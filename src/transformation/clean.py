import re

import pandas as pd
import spacy

from .config.tech_constants import EXCLUDED, TECH_ALIASES


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


def standardize_companies(data: pd.DataFrame, llm) -> pd.DataFrame:
    """
    Nettoie et normalise les noms d'entreprises.

    Les noms distincts sont d'abord nettoyés avec des expressions régulières,
    puis analysés avec spaCy pour identifier les cas suspects.
    Seuls ces noms sont ensuite envoyés au LLM pour normalisation.

    Args:
        data (pd.DataFrame): DataFrame contenant les offres d'emploi.
        llm (LLMExtractor): Instance du modèle utilisée pour la normalisation.

    Returns:
        pd.DataFrame: DataFrame contenant les noms d'entreprises normalisés.
    """
    data = data.copy()

    unique_companies = data["entreprise"].drop_duplicates()

    nlp = spacy.load("fr_core_news_md")

    def clean_and_flag_company(name):
        """
        Nettoie un nom d'entreprise et détermine s'il nécessite
        une normalisation supplémentaire par le LLM.

        Args:
            name (str): Nom brut de l'entreprise.

        Returns:
            tuple: Nom nettoyé et booléen indiquant si le LLM est nécessaire.
        """
        name = re.sub(r"\s+", " ", str(name)).strip()
        name = re.sub(r"[\s-]+$", "", name)
        name = re.sub(r"\s+super recruteur$", "", name, flags=re.IGNORECASE)

        doc = nlp(name)

        # Détecter 
        # la présence d'un nom de personne après le début du texte.
        has_person_suffix = any(ent.label_ == "PER" and ent.start_char > 0 for ent in doc.ents)

        # Considérer les noms de trois mots ou plus comme potentiellement suspects.
        is_long_name = len(name.split()) >= 3

        # Détecter du texte supplémentaire autour d'une entité reconnue.
        has_extra_text = (len(doc.ents) == 1 and doc.ents[0].text.strip().casefold() != name.casefold())

        needs_llm = (has_person_suffix or has_extra_text or len(doc.ents) > 1 or is_long_name)

        return name, needs_llm

    # Analyser chaque nom distinct une seule fois.
    results = {name: clean_and_flag_company(name) for name in unique_companies}

    # Réassocier les résultats à toutes les offres, y compris les doublons.
    normalized = data["entreprise"].map(results)

    # Séparer le nom nettoyé et l'indicateur de traitement par LLM.
    data["company_normalized"] = normalized.map(lambda x: x[0])
    data["company_needs_llm"] = normalized.map(lambda x: x[1])

    # Utiliser le nom nettoyé comme valeur finale par défaut.
    data["company_name"] = data["company_normalized"]

    # Sélectionner uniquement les noms suspects distincts.
    companies_to_process = (data.loc[data["company_needs_llm"],["company_normalized"]].drop_duplicates())

    if not companies_to_process.empty:

        # Normaliser les noms suspects avec le LLM.
        predictions = llm.extract_entities("Company", companies_to_process)

        # Associer chaque nom nettoyé à sa prédiction LLM.
        corrections = predictions.set_index("company_normalized")["company_name_llm"]

        # Appliquer les corrections à toutes les offres concernées.
        # Conserver le nom nettoyé en l'absence de correction.
        data["company_name"] = (data["company_normalized"].map(corrections).fillna(data["company_normalized"]))

    # Créer une clé de rapprochement sans modifier le nom affiché. Pour rapprocher les entreprises même lorsqu'il y a une différence d'accents ou de ponctuation
    data["company_key"] = (data["company_name"].str.casefold()
                           .str.normalize("NFKD") # Decompose les accents
                           .str.replace(r"[\u0300-\u036f]", "", regex=True) # remplace les accents
                           .str.replace(r"[^\w\s]", " ", regex=True) # remplace la ponctuation par un espace
                           .str.replace(r"\s+", " ", regex=True)
                           .str.strip()
                           )
    
    return data

def clean_df(df: pd.DataFrame, llm) -> pd.DataFrame:
    """
    Nettoie les données extraites et prépare le DataFrame pour la couche Silver.

    Args:
        df (pd.DataFrame): DataFrame contenant les offres enrichies.
        llm (LLMExtractor): Instance du LLM utilisée pour normaliser les entreprises.

    Returns:
        pd.DataFrame: DataFrame nettoyé et renommé.
    """
    df = df.copy()

    # Normaliser les technologies extraites par le LLM.
    df["stack_required"] = df["stack_required"].apply(to_set).apply(clean_stack)
    df["stack_desired"] = df["stack_desired"].apply(to_set).apply(clean_stack)

    # Regrouper les technologies requises et souhaitées.
    df["all_technologies"] = [required | desired for required, desired in zip(df["stack_required"],df["stack_desired"])]

    # Remplacer les valeurs manquantes.
    df["entreprise"] = df["entreprise"].fillna("Non renseignée")
    df["location"] = df["location"].fillna("Non renseignée")

    # Nettoyer et normaliser les noms d'entreprises.
    df = standardize_companies(df, llm)

    # Regrouper les années d'expérience en catégories.
    def categorize_exp(x):
        if pd.isna(x):
            return "Non renseignée"
        elif x < 1:
            return "0"
        elif x < 2:
            return "1"
        elif x < 3:
            return "2"
        elif x < 4:
            return "3"
        elif x < 5:
            return "4"
        elif x < 6:
            return "5"
        else:
            return "5+"

    df["experience_min"] = df["experience_min"].apply(categorize_exp)

    # Supprimer les colonnes utilisées uniquement pour l'analyse des prédictions LLM.
    df = df.drop(columns=["experience_max","experience_type","level_title",
                          "level_description","is_internship","reason_job",
                          "company_normalized","company_needs_llm","entreprise"
                          ],
                 errors="ignore"
                 )

    # Harmoniser les noms de colonnes pour la couche Silver.
    df = df.rename(columns={
        "domain": "platform_name",
        "date": "scraping_month",
        "url": "offer_url",
        "poste": "job_title",
        "description": "job_description",
        "location": "job_location",
        "experience": "experience_description",
        "job_predicted": "job_category",
        "experience_min": "experience_category",
        "stack_required": "required_technologies",
        "stack_desired": "desired_technologies",
        "seniority_llm": "seniority_level",
        "_id": "offer_id"
    })

    return df
