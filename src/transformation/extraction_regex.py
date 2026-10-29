"""Classification d'offres d'emploi par expressions régulières.

Deux approches indépendantes :
- Métier : classement à partir du titre uniquement.
- Séniorité : stage/alternance, années d'expérience explicites puis titre.

Ce module est conservé comme trace d'une approche déterministe exploratoire.
Il n'est pas utilisé pour les inférences finales du pipeline, j'ai privilégié le LLM.

Limites : les regex ne comprennent ni le sens des missions, ni les nuances des
critères d'expérience. Elles peuvent produire des faux positifs et des faux
négatifs. Les sorties ne doivent pas être interprétées comme une vérité terrain.
"""

from __future__ import annotations
import re
import unicodedata
from collections.abc import Callable


# -----------------------------------------------------------------------------
# 1. Classification du métier à partir du titre
# -----------------------------------------------------------------------------


def normalize_title(value: object) -> str:
    """Normalise un titre pour faciliter les correspondances regex."""
    text = unicodedata.normalize("NFKD", str(value or ""))
    return "".join(char for char in text if not unicodedata.combining(char)).lower()


DATA_TERMS = (
    r"data|donnee|\bia\b|\bai\b|\bbi\b|analytics|power ?bi|talend|"
    r"dataiku|teradata|snowflake|machine learning|\bml\b|genai|llm"
)
ENGINEERING_TERMS = r"engineer|ingenieur|developpeu|research|scientist|\bops\b|mlops"

# Ordre de priorité conservé : Consultant > Data Science > Data Engineer >
# ML / IA Engineer > Data Analyst > Autre.
JOB_RULES: list[tuple[str, Callable[[str], bool]]] = [
    (
        "Consultant Data / IA",
        lambda title: bool(
            re.search(r"consult|conseil|advisor|advisory", title)
            and re.search(DATA_TERMS, title)
        ),
    ),
    (
        "Data Science",  # Libellé historique, différent de "Data Scientist".
        lambda title: bool(re.search(r"data ?scien|datascien|statisticien", title)),
    ),
    (
        "Data Engineer",
        lambda title: bool(
            re.search(
                r"data engineer|data ingenieur|ingenieur (de )?(donnees|data)|"
                r"big data|analytics engineer|data platform|databricks|snowflake|"
                r"dataops|\betl\b|talend|data architect|architecte data|"
                r"bi engineer|developpeu\w* (bi|data|talend|databricks)",
                title,
            )
        ),
    ),
    (
        "ML / IA Engineer",
        lambda title: bool(
            re.search(
                r"machine learning|\bml\b|mlops|ml ops|\bai\b|\bia\b|genai|"
                r"llm|intelligence artificielle|agentic|agentique|deep learning|"
                r"computer vision",
                title,
            )
            and re.search(ENGINEERING_TERMS, title)
        ),
    ),
    (
        "Data Analyst",
        lambda title: bool(
            re.search(
                r"data.*analy|analy.*(data|donnees)|power ?bi|\bbi\b|"
                r"business intelligence|web ?analy|reporting",
                title,
            )
        ),
    ),
]


def categorize(title: object) -> str:
    """Classe un titre dans la première catégorie regex correspondante."""
    normalized = normalize_title(title)
    for label, matches in JOB_RULES:
        if matches(normalized):
            return label
    return "Autre"


# -----------------------------------------------------------------------------
# 2. Préclassification de la séniorité
# -----------------------------------------------------------------------------

INTERNSHIP_PATTERN = re.compile(
    r"\b(stages?|stagiaires?|alternances?|alternants?|"
    r"apprenti(?:e|es|s)?|apprentissages?|interns?|internships?)\b",
    re.IGNORECASE,
)

# Extraction indicative de l'expérience : N années ou N à M années, dans un
# voisinage immédiat de la notion d'expérience. Les durées sont ambiguës hors
# contexte (historique d'entreprise, projet, compétence spécifique, etc.).
YEAR_TOKEN = r"(?<!\d)(\d{1,2})\s*\+?"
YEAR_UNIT = r"(?:ans?|ann[ée]es?|years?|yrs?)\b"
EXPERIENCE_PATTERN = re.compile(
    rf"{YEAR_TOKEN}\s*(?:(?:à|to|-|–)\s*\d{{1,2}}\s*\+?\s*)?{YEAR_UNIT}"
    rf"(?=[^.\n]{{0,30}}?exp[ée]rience|[^.\n]{{0,12}}?exp\b)"
    rf"|exp[ée]rience[^.\n]{{0,30}}?{YEAR_TOKEN}\s*{YEAR_UNIT}",
    re.IGNORECASE,
)

# Cas courant "N+ years of experience" : la locution 'of experience' constitue
# une preuve plus directe que l'expression plus générale ci-dessus.
EXPERIENCE_OF_PATTERN = re.compile(
    rf"{YEAR_TOKEN}\s*(?:(?:à|to|-|–)\s*\d{{1,2}}\s*\+?\s*)?"
    rf"(?:years?|yrs?)\s+of\s+experience\b",
    re.IGNORECASE,
)

SINCE_PATTERN = re.compile(r"(?:depuis|since)\s*$", re.IGNORECASE)
MAX_YEARS = 15  # Filtre heuristique historique, non une garantie de pertinence.

SENIOR_PATTERN = re.compile(
    r"\b(senior|sénior|sr\.?|lead|principal|staff|head\s+of)\b", re.IGNORECASE
)
JUNIOR_PATTERN = re.compile(
    r"\b(junior|jr\.?|graduate|entry[- ]level|débutante?)\b", re.IGNORECASE
)
CHIEF_OF_STAFF_PATTERN = re.compile(r"chief\s+of\s+staff", re.IGNORECASE)


def normalize_text(value: object) -> str:
    """Convertit les valeurs absentes en texte vide et normalise l'Unicode."""
    if value is None or (isinstance(value, float) and value != value):
        return ""
    return unicodedata.normalize("NFKC", str(value)).replace("’", "'")


def years_to_level(years: int) -> str:
    """Transforme un indicateur d'années en niveau (règles historiques)."""
    if years <= 2:
        return "Junior"
    if years <= 4:
        return "Intermédiaire"
    return "Senior"


def classify_regex_row(
    title: object, experience_field: object, description: object
) -> tuple[str | None, str, str | None]:
    """Retourne (niveau, source, indice), ou (None, 'needs_llm', None)."""