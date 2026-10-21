import pandas as pd
import glob
from src.extraction.llm import LLMExtractor
from pathlib import Path
from MongoDB.mongodb import *

# --------------------------------------------------------------------------- #
# Loading and merging data files
# --------------------------------------------------------------------------- #

def load_data():
    
    df = load_data_mongodb()
        
    df= df.rename(columns={'profil_recherche':'experience'})

    # Dropping useless data columns
    df = df.drop(columns = ["config_name","currency",
                                        "start_url","start_url_formatted",
                                        "country", "brand"])

    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m")

    before = len(df)
    df= df.drop_duplicates(subset=["poste","experience","description"],keep="first")
    print("Nombre de doublons supprimé : ", before - len(df))
    
    return df

def extract_best_models(data: pd.DataFrame,extractor: LLMExtractor) -> pd.DataFrame:
    """Combine les prédictions des meilleurs prompts sélectionnés."""

    # Job + Stack
    full_predictions = extractor.extract_entities(mode="Full",data=data,version="v5")

    # Seniority
    seniority_predictions = extractor.extract_entities(mode="Seniority",data=data,version="v2")

    # Compute seniority level of job offer
    seniority_predictions["seniority_llm"] = (extractor._seniority_from_levels(seniority_predictions))

    # Dropping seniority inferences of Full v5
    result = full_predictions.drop(columns=["seniority_llm","reason_seniority"],errors="ignore").reset_index(drop=True)

    # Replace by Seniority v2 inference
    result["seniority_llm"] = (seniority_predictions["seniority_llm"].reset_index(drop=True))

    return result

if __name__ == "__main__":
    
    data = load_data()
    
    llm = LLMExtractor()
    
    data = extract_best_models(data=data,extractor=llm)
    
    data.to_parquet(Path("data/job_offers.parquet"),index=False)