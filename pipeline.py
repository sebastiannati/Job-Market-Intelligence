import pandas as pd
import glob
from src.extraction.llm import LLMExtractor
from pathlib import Path

# --------------------------------------------------------------------------- #
# Loading and merging data files
# --------------------------------------------------------------------------- #

def load_data():
    
    fichiers_xlsx = glob.glob("scraping_results/*.xlsx")

    liste_dataframes = []


    for fichier in fichiers_xlsx:
        df_temp = pd.read_excel(fichier)
        
        df_temp = df_temp.rename(columns={'profil_recherche':'experience'})

        liste_dataframes.append(df_temp)
        
        df_global = pd.concat(liste_dataframes, ignore_index=True)

        # Dropping useless data columns
        df_global = df_global.drop(columns = ["config_name","currency",
                                            "start_url","start_url_formatted",
                                            "country", "brand"])

    df_global["date"] = pd.to_datetime(df_global["date"]).dt.strftime("%Y-%m")

    before = len(df_global)
    df_global = df_global.drop_duplicates(subset=["poste","experience","description"],keep="first")
    print("Nombre de doublons supprimé : ", before - len(df_global))
    
    return df_global

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