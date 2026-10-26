from pathlib import Path
import pandas as pd
import io

from azure.core.exceptions import ClientAuthenticationError
from azure.identity import AzureCliCredential
from azure.storage.filedatalake import DataLakeServiceClient


class AzureDataLake:

    def __init__(self):
        
        
        self.storage_account = "jobmarketstorage"
        self.container = "joboffers"

        try:
            credential = AzureCliCredential()

            # forces the connection
            token = credential.get_token("https://storage.azure.com/.default")

            print("Authentification Azure réussie !")

        except ClientAuthenticationError as e:
            print("Échec de l'authentification Azure.")
            print("Vérifie ton compte avec : az login")
            raise

        # Connexion au compte de stockage
        self.service_client = DataLakeServiceClient(
            account_url=f"https://{self.storage_account}.dfs.core.windows.net",
            credential=credential
        )

        # Sélectionner le conteneur
        self.container = self.service_client.get_file_system_client(
            file_system=self.container
        )

    def upload_dataframe(self,df:pd.DataFrame,azure_path:str):
        """Prends un dataframe en entrée et le convertir en parquet pour le sauvegarder sur la base Azure

        Args:
            df (pd.DataFrame): Jeu de données propres et alimentées via LLM.
        """

        # Buffer to save in memory
        buffer = io.BytesIO()
        
        df.to_parquet(buffer,engine="pyarrow",index=False)
        
        # Reinitialize head to begin 
        buffer.seek(0)
    
        file_client = self.container.get_file_client(azure_path)
        file_client.upload_data(buffer,overwrite=True)
       
    def upload_local_file(self, local_path: str, azure_path: str):

        # Vérifier que le fichier local existe
        local_file = Path(local_path)

        if not local_file.is_file():
            raise FileNotFoundError(
                f"Fichier introuvable : {local_path}"
            )

        # Sélectionner le fichier distant
        file_client = self.container.get_file_client(azure_path)

        # Transférer les données
        with local_file.open("rb") as data:
            file_client.upload_data(
                data=data,
                overwrite=True
            )

        print(f"File uploaded : {azure_path}")
    
    def file_exists(self, azure_path: str) -> bool:

        file_client = self.container.get_file_client(azure_path)

        return file_client.exists()

if __name__ == "__main__":
    
    data_lake = AzureDataLake()