from path import Path
import json
import pandas as pd
import ollama
from tqdm import tqdm
from constant_llm import *

""" 
Ce fichier contient la classe qui permet d'extraire des informations via un model local.
"""

class LLM_Extractor:
    
    def __init__(self):
        """Par défaut, crée une instance qui charge le prompt général d'extraction."""
        # Loads all instructions
        self.instructions = self._load_instructions()
        # Gets global extraction prompt
        self.extraction_entity = self.instructions.get("global_extraction_prompt")
        # Gets active version of the prompt
        self.active_version = self.extraction_entity.get("active_version")
        # Gets the version of the prompt
        self.version = self.extraction_entity.get(self.active_version)
        # Gets the model
        self.model = self.version.get("model")
        # Gets the parameters of the model
        self.model_params = self.version.get("params")
        # Gets the prompt of the version
        self.prompt = self.version.get("system_prompt")
        # Gets the schema output of the version
        self.schema = self.version.get("schema")
        self.X_val = pd.DataFrame()
        self.X_test = pd.DataFrame()
        
    def _load_instructions(self):
        """Charge toutes les configurations du fichiers `instructions_llm.json` pour manipuler les versions plus facilement.

        Returns:
            dict: Dictionnaire qui contient toutes les version de chaque instructions 
            (global, seniority, job, stack) pour extraire les informations des offres d'emplois.
        """
        # Path
        instructions_path = Path("src/extraction/instructions_llm.json") 
        
        instructions = {}
        
        with open(instructions_path,encoding="utf-8") as f:
            instructions = json.load(f)
        
        return instructions
    
    def _load_data(self):
        val_path = Path("src/extraction/data_llm/data_val.xlsx")
        test_path = Path("src/extraction/data_llm/data_test.xlsx")
        
        self.X_val = pd.read_excel(val_path).reset_index(drop=True)
        self.X_test = pd.read_excel(test_path).reset_index(drop=True)
        
        print("Data Loaded")
        
        
    def extract(self,mode: str,data:pd.DataFrame):
        """Fonction qui utilise le prompt général capable d'extraire la seniorité, le nom du job et la stack.
        Sinon elle traite chaque version
        """
        def _val(value) -> str:
            if pd.isna(value):
                return "not provided"
            return str(value)
        if mode == "Seniority":
            self.extract_seniority()
        elif mode == "Job":
            self.extract_job()
        elif mode == "Stack":
            self.extract_stack()
        else:
            pass
            
            
    def extract_seniority(self):
        """Utilise la version active des prompts pour extraire la seniorité"""
        
        print("="*30,"Seniority Prompt", "="*30)
        
        self.extraction_entity = self.instructions.get("seniority_classifier_prompt")
        self.active_version = self.extraction_entity.get("active_version")
        self.version = self.extraction_entity.get(self.active_version)
        self.model = self.version.get("model")
        self.model_params = self.version.get("params")
        self.prompt = self.version.get("system_prompt")
        self.schema = self.version.get("schema")
        print("="*78)
        
    def extract_job(self,df):
        """Utilise la version active des prompts pour extraire la catégorie du job"""
        
        self.extraction_entity = self.instructions.get("job_classifier_prompt")
        
        self.active_version = self.extraction_entity.get("active_version")
        self.version = self.extraction_entity.get(self.active_version)
        self.model = self.version.get("model")
        self.model_params = self.version.get("params")
        self.prompt = self.version.get("system_prompt")
        self.schema = self.version.get("schema")
        
        results = []
        
        total_tokens = []
        
        for _, row in tqdm(df.iterrows(), total=len(df)):
    
            title = "not provided" if not row["poste"] else row["poste"]

            user_prompt = (
                f"Title: {title}\n"
                f"Raw experience: {(row['experience'])}\n"
                f"Description:\n{(row['description'])}"
            )

            try:
                response = ollama.chat(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    format=self.schema,
                    options=self.model_params
                    ,
                    think=False,
                    keep_alive="30m",
                )

                results = json.loads(response.message.content)
                
                total_tokens.append(response.prompt_eval_count + response.eval_count)

            except Exception as error:
                return {
                    "categorie": None,
                    "categorie_alternative": None,
                    "justification": None,
                    "categorie_code": None,
                    "stack_requise": [],
                    "stack_souhaitee": [],
                    "erreur": str(error),
                }

        # Concatenated df with predictions
        return pd.concat([df.reset_index(drop=True), pd.DataFrame(results)],axis=1,)
        
    def extract_stack():
        """Utilise la version active des prompts pour extraire la stack"""
    
    def evaluate_llm():
        """Il va chercher les jeux de validations et de tests et test tout les prompts dessus.
        Met à jour automatiquement la version activement en fonction des résultats et enregistre les erreurs.
        """
    
    def print(self):
        print("="*30,"LLM Extractor", "="*30)
        
        for nom,valeur in vars(self).items():
            print(f"{nom} :\t{valeur}")
            
            
        print("="*75)
    
    def evaluate_extraction():
        pass
    
if __name__ == "__main__":
    
    llm = LLM_Extractor()
    llm._load_data()
    