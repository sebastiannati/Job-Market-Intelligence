import pandas as pd
import os
from dotenv import load_dotenv
from pymongo import MongoClient
import glob
import json
from tqdm import tqdm

def load_data_mongodb():
    pass

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
    

def insert_mongodb(df=None):
    """
    Insère les offres d'emploi dans MongoDB Atlas.

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

    documents = json.loads(df.to_json(orient="records",date_format="iso"))
    
    client = connect_mongodb()    
    
    try: 
        db =  client.JobOffers
        collection = db["raw_offers"]
        
        result = collection.insert_many(documents)
        
        nb_insertions = len(result.inserted_ids)

        print(f"{nb_insertions} offers inserted in MongoDB")
            
    except Exception as e :
        raise(f"Can't insert job offers from {fichiers} in database : {e}")
    
    finally:
        client.close()

if __name__ == "__main__":
    
    insert_mongodb()