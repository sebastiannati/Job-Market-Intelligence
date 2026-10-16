"""Classification du niveau de séniorité des offres d'emploi.

Deux étapes :
1. Pré-classification par regex : uniquement les règles très sûres.
2. Tout le reste (source "needs_llm") est traité par un LLM local via Ollama.

Labels possibles : "Stage/Alternance" | "Junior" | "Intermédiaire" | "Senior".
"""
import json
import re
import unicodedata

import ollama
import pandas as pd
from tqdm import tqdm

# --------------------------------------------------------------------------- #
# Constantes
# --------------------------------------------------------------------------- #
MODEL = "qwen3:14b"
LEVELS = ["Stage/Alternance", "Junior", "Intermédiaire", "Senior"]
RANK = {lvl: i for i, lvl in enumerate(LEVELS)}


def _val(x) -> str:
    return "not provided" if pd.isna(x) else str(x)


def classify_llm(row):
    """Retourne (niveau, raison) ; (None, "erreur: ...") en cas d'échec."""
    user_prompt = (
        f"Title: {_val(row['poste'])}\n"
        f"Raw experience: {_val(row['experience'])}\n"
        f"Description:\n{_val(row['description'])}"
    )
    try:
        response = ollama.chat(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_SENIORITY},
                {"role": "user", "content": user_prompt},
            ],
            format=SCHEMA_SENIORITY,
            options={"temperature": 0, "num_ctx": 12000},
            think=False,
            keep_alive="30m",
        )
        data = json.loads(response.message.content)
    except Exception as e:
        return None, f"erreur: {e}"

    if data["is_internship"]:
        return "Stage/Alternance", data["reason"]

    # Niveau final = le plus élevé des trois sources (hors stage)
    candidates = [data["level_title"], data["level_experience"], data["level_description"]]
    candidates = [c for c in candidates if c != "Stage/Alternance"] or ["Junior"]
    return max(candidates, key=RANK.get), data["reason"]

out = []
for _, row in tqdm(X_test.iterrows(), total=len(X_test)):
    out.append(classify_llm(row))


X_test = X_test.copy()
X_test["pred"], X_test["reason"] = zip(*out)
X_test["true"] = y_true.set_index("offre_id")["seniority_level"].reindex(X_test.index)

# --- évaluation contre les labels annotés ---
from sklearn.metrics import classification_report, confusion_matrix

ev = X_test.dropna(subset=["pred"])
print(f"{len(ev)}/{len(X_test)} offres classées")
print(f"accord exact : {(ev.pred == ev.true).mean():.0%} | à ±1 niveau : "
      f"{((ev.pred.map(RANK) - ev.true.map(RANK)).abs() <= 1).mean():.0%}\n")
print(classification_report(ev.true, ev.pred, labels=LEVELS, zero_division=0))
print(pd.DataFrame(confusion_matrix(ev.true, ev.pred, labels=LEVELS), index=LEVELS, columns=LEVELS))

# désaccords à relire (les cas litigieux sont peut-être des erreurs de ma part)
errors = X_test[X_test.pred != X_test.true][["poste", "experience", "description", "true", "pred", "reason"]]
errors.to_csv("llm_errors.csv")

# Previous = 91% accuracy
# Previous = 81%
#



