import argparse
import re
from pathlib import Path

import pandas as pd
import spacy

from load.azuredb import AzureDataLake

from src.extraction.llm import LLMExtractor
from load.mongodb import *

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

def save_data(output: str, azure: bool = False,data: pd.DataFrame | None = None, input_file: str | None = None):

    if azure:
        lake = AzureDataLake()

        if input_file is not None:
            lake.upload_local_file(
                local_path=input_file,
                azure_path=output
            )

        elif data is not None:
            lake.upload_dataframe(
                df=data,
                azure_path=output,
                format="parquet"
            )

        else:
            raise ValueError("Aucune donnée à envoyer vers Azure.")

    else:
        if data is None:
            raise ValueError(
                "Un DataFrame est nécessaire pour la sauvegarde locale."
            )

        data.to_parquet(Path(output),index=False)

    print(f"Données sauvegardées : {output}")

def run_pipeline(
    output: str,
    azure: bool = False,
    input_file: str | None = None
):
    # Saving data in azure o
    if input_file is not None:
        save_data(output=output,azure=azure,input_file=input_file)
        return


    data = load_data()

    llm = LLMExtractor()

    data = extract_best_models(
        data=data,
        extractor=llm,
        skip=True
    )

    data = clean_df(data)

    # Saving data locally or in cloud 
    save_data(output=output,azure=azure,data=data)

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(
        description="Job Market Intelligence Pipeline"
    )

    parser.add_argument(
        "-o", "--output",
        type=str,
        required=True,
        help="Chemin de sortie local ou Azure"
    )

    parser.add_argument(
        "-i", "--input-file",
        type=str,
        default=None,
        help="Fichier local à envoyer vers Azure"
    )

    parser.add_argument(
        "-a", "--azure",
        action="store_true",
        help="Activer la sauvegarde Azure Data Lake"
    )

    args = parser.parse_args()
    
    run_pipeline(
        output=args.output,
        azure=args.azure,
        input_file=args.input_file
    )