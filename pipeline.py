from pathlib import Path

import pandas as pd

from src.extraction.llm import LLMExtractor
from src.MongoDB.mongodb import *

# --------------------------------------------------------------------------- #
# Loading and merging data files
# --------------------------------------------------------------------------- #

def load_data():
    """Loads data from MongoDB and normalize it according  

    Returns:
        pd.DataFrame: Clean dataframe from MongoDB raw data (no duplicates, columns normalized and dropped) 
    """
    print("-"*30,"Loading Data","-"*30)
    try :
        df = load_data_mongodb()
    except Exception as e:
        raise(f"Can't load data from MongoDB : {e}")
    
    # Both columns represent the same information and are mutually exclusive.
    # Merge them by keeping the non-null value.
    df["experience"] = df["experience"].combine_first(df["profil_recherche"])

    df.drop(columns=["profil_recherche"], inplace=True)

    # Dropping useless data columns
    df = df.drop(columns = ["config_name","currency",
                            "start_url","start_url_formatted",
                            "country", "brand","date_de_publication","nb_candidats"])

    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m")

    before = len(df)
    df = df.drop_duplicates(subset=["poste","experience","description"],keep="first")
    
    print(f"{before} offers imported from MongoDB, dropped {before - len(df)} duplicates.")
    
    # Drop rows with neither a job description nor experience information.
    # Without either, the LLM and I cannot classify the role neither seniority and extract the stack.

    # Normaliser les valeurs pour la comparaison
    missing = (df[["description", "experience"]].fillna("")
        .apply(lambda col: col.str.strip().str.casefold())
        .isin(["not provided", ""])
    )
    
    before = len(df)

    # Supprimer les offres où les deux informations manquent
    df = df.loc[~missing.all(axis=1)].copy()  
    
    print(f"{before} offers, dropped {before - len(df)} empty rows.")
    
    print("-"*74)
    return df

def extract_best_models(data: pd.DataFrame,extractor: LLMExtractor,skip=False) -> pd.DataFrame:
    """Combine les prédictions des meilleurs prompts sélectionnés."""
    print("-"*30,"Infering job offers","-"*30)
    
    if skip:
        print("LLM inference skipped.")
        print("-"*81)
        return None
    
    # Skip the infering, for testing for exemple

    try :
        # Job + Stack
        full_predictions = extractor.extract_entities(mode="Full",data=data,version="v5")

        # Seniority
        seniority_predictions = extractor.extract_entities(mode="Seniority",data=data,version="v2")

        seniority_predictions["seniority_llm"] = (extractor._seniority_from_levels(seniority_predictions))

        result = full_predictions.drop(columns=["seniority_llm","reason_seniority"],errors="ignore").reset_index(drop=True)

        result["seniority_llm"] = (seniority_predictions["seniority_llm"].reset_index(drop=True))
        
    except Exception as e:
        raise(f"LLM inference failed: {e}") 
    
    return result

def clean_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Entreprises manquantes
    df["entreprise"] = df["entreprise"].fillna("Non renseignée")

    # Transformer les années d'expérience en catégories string
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

    # Drop all columns that serves only to analyse llm's predictions
    df = df.drop(columns=["experience_max","experience_type","level_title","level_description","is_internship","reason_job"])
    
    df = df.rename(columns={
        "domain": "platform_name",
        "date": "scraping_month",
        "url": "offer_url",
        "entreprise": "company_name",
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

if __name__ == "__main__":
    
    data = load_data()
    
    llm = LLMExtractor()
    
    data = extract_best_models(data=data,extractor=llm,skip=True)
    
    data = clean_df(data)
    
    data.to_parquet(Path("data/job_offers.parquet"),index=False)