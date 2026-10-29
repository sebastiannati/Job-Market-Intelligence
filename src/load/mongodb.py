import pandas as pd
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import BulkWriteError
import glob
import json
from tqdm import tqdm
import hashlib
from urllib.parse import urlsplit, urlunsplit
from datetime import datetime

def load_data_mongodb():
    client = connect_mongodb()

    db = client["JobOffers"]
    collection = db["raw_offers"]
    
    try:
        
        documents = list(collection.find())
        df = pd.DataFrame(documents)
        
        return df

    finally:
        client.close()

def connect_mongodb():
    try : 
        load_dotenv("atlas-credentials.env")
        MONGO_URI = os.getenv("MONGODB_URI")
    
    except FileNotFoundError as e:
        raise(f"Can't load MongoDB Credentials : {e}")
    
    try :
        client = MongoClient(MONGO_URI)
        client.admin.command("ping")
        print("Connected to MongoDB Atlas !")
        return client
    except Exception as e :
        raise(f"Can't connect to MongoDB Atlas : {e}")

def generate_offer_id(url, scraping_date):

    key = f"{url}|{scraping_date}"

    # Hash déterministe
    return hashlib.sha256(key.encode("utf-8")).hexdigest()

def insert_mongodb(df=None):
    """
    Pour chaque offre, un index unique est crée en fonction de la date de scraping 
    et de l'url de l'offre. Insère les offres d'emploi dans MongoDB Atlas.

    Si df est fourni :
        Insère directement le DataFrame du scraper.

    Sinon :
        Lit tous les fichiers Excel de scraping_results,
        les concatène et les insère.
    """
    
    if df is None:
        
        list_df = []
        
        fichiers = glob.glob("scraping_results/*.xlsx")
        
        for fichier in tqdm(fichiers,desc='Laoding data from excel files : '):
            try:
                df_temp = pd.read_excel(fichier)
                list_df.append(df_temp)

            except Exception as e:
                raise RuntimeError(f"Erreur lors de la lecture de {fichier} : {e}")
        
        df = pd.concat(list_df,ignore_index=True)
    
    tqdm.pandas(desc="Generating offers ids")
    
    # Générer l'identifiant de chaque offre
    df["_id"] = df.progress_apply(lambda row: generate_offer_id(row["url"],row["date"]),axis=1)
    
    # Drop duplicates in case we scrape the same offer on different 
    # websites and they share url and scraping_date 
    df = df.drop_duplicates(subset=["_id"],keep="first") 
    
    documents = json.loads(df.to_json(orient="records",date_format="iso"))

    client = connect_mongodb()    
    db =  client.JobOffers
    collection = db["raw_offers"]
    
    try: 
        result = collection.insert_many(documents,ordered=False)
        
        nb_insertions = len(result.inserted_ids)

        print(f"{nb_insertions} offers inserted in MongoDB")
    
    except BulkWriteError as e:
        details = e.details
  
        errors = details["writeErrors"] # Errors BulkWrite
        
        for error in errors:
            if error["code"] != 11000:
                raise(f"Not a duplicate error : {e}")

        print("Offers inserted :", details.get("nInserted", 0))
        print("Duplicates ignored :", len(errors))
        
    except Exception as e :
        raise(f"Can't insert job offers from {fichiers} in database : {e}")
    
    finally:
        client.close()


if __name__ == "__main__":
    # To Test if needed
    pass