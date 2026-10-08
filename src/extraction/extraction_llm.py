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



# --------------------------------------------------------------------------- #
# 2. Classification par LLM local
# --------------------------------------------------------------------------- #
SYSTEM_SENIORITY = """You are an expert recruiter in the data/IT/business job market in France. You classify job offers (French or English) by required seniority.

LEVELS (use these exact labels):
- "Stage/Alternance": internship, work-study, apprenticeship.
- "Junior": 0 to 2 years of experience, beginners and recent graduates (not an internship).
- "Intermédiaire": 3 to 4 years of experience.
- "Senior": 5+ years, or a high-seniority role.

INPUT FIELDS: Title, Raw experience, Description. Any of them may be "not provided".
"Raw experience" and "Profile sought" often contain the candidate requirements as free text: read them TOGETHER as the EXPERIENCE source.

Assess THREE sources separately:
1. level_title: from the TITLE only.
2. level_experience: from the explicit years in Raw experience + Profile sought only (no explicit years at all -> "Junior").
3. level_description: from the DESCRIPTION, following the ordered steps below.
The final level is computed OUTSIDE the model as the highest of the three. Report each one honestly: never inflate one source to compensate for another.

YEARS -> LEVEL TABLE (apply it literally, in every field):
- 0, 1 or 2 years -> Junior (also "2+", "at least 2", "minimum 2", "au moins 2 ans", "plus de 2 ans", "more than 2")
- 3 or 4 years -> Intermédiaire (also "3+", "at least 3")
- 5 years or more -> Senior
- A range uses its LOWER bound: 1-3 -> Junior; 3-5 -> Intermédiaire; 4-7 -> Intermédiaire; 5-8 -> Senior; "3 à 8+" -> Intermédiaire.
- Count only the GLOBAL professional-experience requirement. IGNORE years about one specific tool when a global number exists ("4 to 5 years, of which 2 on Databricks" -> 4), company age or size, contract or alternance duration ("CDD 1 an", "alternance 2 ans").

TITLE:
- "Senior", "Lead", "Tech Lead", "Principal", "Architect", "Head of", "Director" -> Senior. "Confirmé"/"Confirmed" -> Intermédiaire. "Junior" -> Junior.
- Years written in the title follow the table (e.g. "4/7 ans" -> Intermédiaire).
- "Expert", "Manager", "Chef de projet", "Responsable" alone carry no seniority information -> "Junior".

DESCRIPTION: apply the steps in order and stop at the first one that matches.
 a. Explicit years of experience in the description -> use the table. Explicit years ALWAYS beat adjectives such as expert, experienced, autonomous, mid-senior, "senior stakeholders", "to lead a workstream".
 b. The role itself is announced as senior: "we are looking for a Senior / Lead / Tech Lead / Architect / Director ..." -> Senior; "profil confirmé / experienced profile" -> Intermédiaire. A verb ("to lead") or "senior stakeholders" is NOT a seniority signal.
 c. Otherwise judge the responsibilities. DEFAULT = Junior.
    - Senior ONLY if the person leads a team, defines the architecture or the technical strategy, or is THE technical referent.
    - Intermédiaire ONLY if the person explicitly owns a whole scope end to end ("own", "responsible for", "de A à Z", "garant") of a platform, product or program, not just a part of it.
    - Junior for everything else: participate, contribute, support, assist, build, maintain, analyse, report, collaborate, design pieces within a team.
    Technologies, tools, cloud, MLOps, "autonomous", "rigorous", "complex data", company prestige and description length are NOT signals.
 d. CAP: if the experience source gives 0-2 years and the description has no explicit years (step a) and no step b match, level_description can be Junior, or Senior (only for leadership/architecture/technical referent). Never Intermédiaire.

INTERNSHIP:
- is_internship = true ONLY when the offer is explicitly a stage, internship, alternance, apprenticeship ("contrat d'apprentissage", "contrat de professionnalisation", "alternant(e)", "apprenti(e)") in the title or as the contract. It overrides everything: set all three levels to "Stage/Alternance".
- is_internship = false when the text only says the candidate is studying or preparing a degree, or when "stage/alternance compris" appears inside a requirement about PREVIOUS experience ("first experience, internship included").

EXAMPLES (generic):
- Raw experience "2 An(s)", description "contribuer à la conception des pipelines", no years -> experience Junior, description Junior.
- Description "au moins 2 ans d'expérience" or "1 à 3 ans" -> Junior.
- Profile sought "4 to 7 years of experience", description "we need a manager to lead GRC" -> experience Intermédiaire (lower bound 4), description Intermédiaire ("to lead" is a verb).
- Title "Data Engineer (Junior)", Raw experience "1 An(s)" -> all three Junior.
- Description "5 ans d'expérience minimum" while Raw experience says "1 An(s)" -> experience Junior, description Senior.

Answer only with the requested JSON. "reason" is one short sentence that quotes the decisive words and the level they map to (for example: "'minimum 2 ans' -> Junior"). A number must never be described with a level that contradicts the table."""

_LEVEL_FIELD = {"type": "string", "enum": LEVELS}
SCHEMA_SENIORITY = {
    "type": "object",
    "properties": {
        "reason": {"type": "string"},
        "is_internship": {"type": "boolean"},
        "level_title": _LEVEL_FIELD,
        "level_experience": _LEVEL_FIELD,
        "level_description": _LEVEL_FIELD,
    },
    "required": ["reason", "is_internship", "level_title", "level_experience", "level_description"],
}


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



