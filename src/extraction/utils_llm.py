import pandas as pd

from src.extraction.config.tech_constants import *

# Extraction methods
EXTRACTION_ENTITIES = [
    "global_extraction_prompt",
    "job_classifier_prompt",
    "stack_extraction_prompt",
    "seniority_classifier",
]

def _bullets(missions: list) -> str:
    """Formate une mission par ligne."""
    return "\n".join(f"- {mission}" for mission in missions)

def to_set(value):

    if isinstance(value, list):
        outils = value
    elif isinstance(value, str):
        outils = value.split(";")
    elif pd.isna(value):
        return set()
    else:
        return set()

    return {outil.strip().lower() for outil in outils if outil.strip()}


def clean_stack(tools):
    return {
        TECH_ALIASES.get(t.strip().casefold(),t.strip())
        for t in tools
        if isinstance(t, str)
        and t.strip()
        and t.strip().casefold() not in EXCLUDED
    }
    
def eval_stack(y_true, y_pred):
    """Calcule les métriques micro sur toutes les technologies."""

    tp = fn = fp = 0

    for true, pred in zip(y_true, y_pred):
        tp += len(true & pred) # len des bonnes extractions
        fp += len(pred - true) # len des extractions en trop
        fn += len(true - pred) # len des extractions en moins

    precision = tp/(tp+fp) # mesures les techno en trop (si fp (techno en trop) petit alors fp/fp =1)
    recall = tp/(fn+tp)  # mesures les techno en moins (si fn petit (techno qui manquent) alors tp/tp)
    f1 = 2*(precision*recall)/(precision+recall)#moyenne harmonique des deux

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1
    }