import pandas as pd
import glob


# --------------------------------------------------------------------------- #
# Loading and merging data files
# --------------------------------------------------------------------------- #

def load_data():
    
    fichiers_xlsx = glob.glob("scraping_results/*.xlsx")

    liste_dataframes = []


    for fichier in fichiers_xlsx:
        df_temp = pd.read_excel(fichier)

        # Merge all columns to experience
        if 'profil_recherche' in df_temp.columns: 
            df_temp = df_temp.rename(columns={'profil_recherche':'experience'})

        liste_dataframes.append(df_temp)

    df_global = pd.concat(liste_dataframes, ignore_index=True)

    # Dropping useless data columns
    df_global = df_global.drop(columns = ["config_name","currency",
                                          "France","start_url",
                                          "start_url_formatted","country"])

    df_global.head()
    
    return df_global

# --------------------------------------------------------------------------- #
# Pipeline
# --------------------------------------------------------------------------- #

def classify_seniority(df: pd.DataFrame) -> pd.DataFrame:
    """Classe la séniorité : regex d'abord, puis LLM pour les offres restantes.

    Ajoute les colonnes `seniority_level`, `needs_llm` et `reason`.
    """
    tqdm.pandas(desc="Séniorité (regex)")
    results = df.progress_apply(classify_regex, axis=1).tolist()
    df["seniority_level"] = [label for label, _ in results]
    df["needs_llm"] = [source == "needs_llm" for _, source in results]

    if "reason" not in df.columns:
        df["reason"] = None

    llm_mask = df["needs_llm"]
    if not llm_mask.any():
        print("Aucune offre à classer avec le LLM")
        return df

    tqdm.pandas(desc="Séniorité (LLM)")
    df.loc[llm_mask, ["seniority_level", "reason"]] = df.loc[llm_mask].progress_apply(
        lambda row: pd.Series(classify_llm(row)), axis=1, result_type="expand"
    )
    return df