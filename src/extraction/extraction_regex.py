import re


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