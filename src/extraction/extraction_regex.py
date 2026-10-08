import re

import re, unicodedata
import pandas as pd

def norm(s):
    # NFKD : retire les accents et convertit les caractères "gras" Unicode
    s = unicodedata.normalize("NFKD", str(s))
    return "".join(c for c in s if not unicodedata.combining(c)).lower()

# --- Briques réutilisables ---
DATA = (r"data|donnee|\bia\b|\bai\b|\bbi\b|analytics|power ?bi|talend|dataiku|teradata|"
        r"snowflake|machine learning|\bml\b|genai|llm")
ENG  = r"engineer|ingenieur|developpeu|research|scientist|\bops\b|mlops"

# --- Règles, par ordre de priorité ---
RULES = [
    # 1. Consultant : prioritaire, à condition d'avoir un mot data/IA/ML dans le titre
    ("Consultant Data / IA",
     lambda t: re.search(r"consult|conseil|advisor|advisory", t) and re.search(DATA, t)),

    # 2. Data Science
    ("Data Science",
     lambda t: re.search(r"data ?scien|datascien|statisticien", t)),

    # 3. Data Engineer
    ("Data Engineer",
     lambda t: re.search(
         r"data engineer|data ingenieur|ingenieur (de )?(donnees|data)|big data|analytics engineer|"
         r"data platform|databricks|snowflake|dataops|\betl\b|talend|data architect|architecte data|"
         r"bi engineer|developpeu\w* (bi|data|talend|databricks)", t)),

    # 4. ML / IA Engineer (il faut un mot "engineer/ingénieur/..." pour éviter AI Trainer, AI Product Manager...)
    ("ML / IA Engineer",
     lambda t: re.search(
         r"machine learning|\bml\b|mlops|ml ops|\bai\b|\bia\b|genai|llm|intelligence artificielle|"
         r"agentic|agentique|deep learning|computer vision", t) and re.search(ENG, t)),

    # 5. Data Analyst / BI
    ("Data Analyst",
     lambda t: re.search(
         r"data.*analy|analy.*(data|donnees)|power ?bi|\bbi\b|business intelligence|web ?analy|reporting", t)),
]

def categorize(titre):
    t = norm(titre)
    for label, test in RULES:
        if test(t):
            return label
    return "Autre"

# --- Colonne optionnelle : type de contrat ---
def contrat(titre):
    t = norm(titre)
    if re.search(r"alternan|apprenti|apprentissage|apprenticeship", t): return "Alternance"
    if re.search(r"\bstage|stagiaire|\bintern\b|internship|\bpfe\b", t): return "Stage"
    if "freelance" in t: return "Freelance"
    return "CDI / autre"

# --- Application ---
counts = df["poste"].value_counts().rename_axis("poste").reset_index(name="n")
counts["categorie"] = counts["poste"].apply(categorize)
counts["contrat"]   = counts["poste"].apply(contrat)

print(counts.groupby("categorie")["n"].sum().sort_values(ascending=False))
# --------------------------------------------------------------------------- #
# 1. Pré-classification par regex
# --------------------------------------------------------------------------- #

# Stage / alternance : titre uniquement
INTERN = re.compile(
    r"\b(stages?|stagiaires?|alternances?|alternants?|apprenti(?:e|es|s)?|apprentissages?|"
    r"interns?|internships?)\b",
    re.I,
)

# "N ans d'expérience" / "N+ years of experience" (chiffres uniquement, contexte obligatoire)
YEARS = re.compile(
    r"(?<!\d)(\d{1,2})\s*\+?\s*(?:(?:à|to|-|–)\s*\d{1,2}\s*\+?\s*)?(?:ans?|ann[ée]es?|years?|yrs?)\b"
    r"(?=[^.\n]{0,30}?exp[ée]rience|[^.\n]{0,12}exp\b)"
    r"|exp[ée]rience[^.\n]{0,30}?(?<!\d)(\d{1,2})\s*\+?\s*(?:ans?|years?)\b",
    re.I,
)
SINCE = re.compile(r"(?:depuis|since)\s*$", re.I)
MAX_YEARS = 15  # au-delà, c'est probablement l'ancienneté de l'entreprise

# Niveau explicite dans le titre
SENIOR = re.compile(r"\b(senior|sénior|sr\.?|lead|principal|staff|head\s+of)\b", re.I)
JUNIOR = re.compile(r"\b(junior|jr\.?|graduate|entry[- ]level|débutante?)\b", re.I)
CHIEF_OF_STAFF = re.compile(r"chief\s+of\s+staff", re.I)


def _norm(x) -> str:
    """Normalise une valeur en texte (NaN/None -> chaîne vide)."""
    if x is None or (isinstance(x, float) and x != x):
        return ""
    return unicodedata.normalize("NFKC", str(x)).replace("’", "'")


def years_to_level(years: int) -> str:
    if years <= 2:
        return "Junior"
    if years <= 4:
        return "Intermédiaire"
    return "Senior"


def classify_regex_row(title, experience_field, description):
    """Retourne (label, source, evidence).

    source : title_intern | years | title | needs_llm
    Si aucune règle sûre ne s'applique : (None, "needs_llm", None).
    """
    title = _norm(title)
    text = f"{_norm(experience_field)}\n{_norm(description)}"

    # 1. Stage / alternance (titre uniquement)
    m = INTERN.search(title)
    if m:
        return "Stage/Alternance", "title_intern", m.group(0)

    # 2. Années d'expérience explicites
    found = []
    for m in YEARS.finditer(text):
        if SINCE.search(text[max(0, m.start() - 15):m.start()]):
            continue
        years = int(m.group(1) or m.group(2))
        if years < MAX_YEARS:
            found.append((years, m.group(0)))
    if found:
        years, evidence = max(found)
        return years_to_level(years), "years", evidence

    # 3. Niveau explicite dans le titre
    clean_title = CHIEF_OF_STAFF.sub("", title)
    for rx, label in ((SENIOR, "Senior"), (JUNIOR, "Junior")):
        m = rx.search(clean_title)
        if m:
            return label, "title", m.group(0)

    return None, "needs_llm", None


def classify_regex(row):
    """Version DataFrame : retourne (label, source)."""
    label, source, _ = classify_regex_row(row["poste"], row["experience"], row["description"])
    return label, source

# --------------------------------------------------------------------------- #
# Tests rapides de la partie regex
# --------------------------------------------------------------------------- #
REGEX_TESTS = [
    # (titre, champ expérience, description, label attendu)
    ("2 Alternances - BI (H/F)", "", "", "Stage/Alternance"),
    ("Analytics Engineer", "", "3+ years as an Analytics Engineer with experience", None),
    ("Analytics Engineer", "", "3+ years of experience in analytics", "Intermédiaire"),
    ("Staff ML Engineer", "", "7+ years of experience in ML", "Senior"),
    ("Staff Engineer", "", "5 à 7 ans d'expérience en backend", "Senior"),
    ("Data Engineer", "", "Expérience : 2 ans minimum", "Junior"),
    ("Consultant", "", "Depuis 20 ans d'expérience, nous... ", None),
    ("Data Engineer Senior", "", "Spark, Airflow", "Senior"),
    ("Jr Developer", "", "", "Junior"),
    ("Chief of Staff", "", "", None),
    ("Data Engineer", "", "Pipelines Spark", None),
]


def run_regex_tests() -> int:
    failures = 0
    for title, field, desc, expected in REGEX_TESTS:
        got = classify_regex_row(title, field, desc)
        ok = got[0] == expected
        failures += not ok
        print("OK " if ok else "KO ", title, "->", got, "" if ok else f"(attendu {expected})")
    print("Regex: TOUT OK" if not failures else f"{failures} ECHEC(S)")
    return failures


if __name__ == "__main__":
    run_regex_tests()