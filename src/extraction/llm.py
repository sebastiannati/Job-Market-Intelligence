from path import Path
import json
import pandas as pd
import ollama
from tqdm import tqdm
from constant_llm import *
from utility_llm import *
from sklearn.metrics import accuracy_score, f1_score

""" 
Ce fichier contient la classe qui permet d'extraire des informations via un model local.
"""

class LLM_Extractor:
    
    def __init__(self):
        """Par défaut, crée une instance qui charge le prompt général d'extraction."""
        # Loads all instructions
        self.instructions = self._load_instructions()
        
        # LLM's configuration
        self.extraction_entity = None
        self.active_version = None
        self.version = None
        self.model = None
        self.model_params = None
        self.prompt = None
        self.schema = None

        # Gets global extraction prompt
        self._set_prompt("global_extraction_prompt")
    
        # Data for evaluation 
        self.X_val = pd.DataFrame()
        self.X_test = pd.DataFrame()
        
        self._load_data()
    
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
    
    def _set_prompt(self, entity_to_extract):
        """Sélectionne l'entité et charge la configuration du LLM."""

        def _load_classifier():
            """Met à jour la configuration selon la version active."""
            self.active_version = self.extraction_entity["active_version"]
            self.version = self.extraction_entity[self.active_version]

            self.model = self.version["model"]
            self.model_params = self.version["params"]
            self.prompt = self.version["system_prompt"]
            self.schema = self.version["schema"]

        if entity_to_extract not in self.instructions:
            raise ValueError(f"Entité inconnue : {entity_to_extract}")

        self.extraction_entity = self.instructions[entity_to_extract]
        _load_classifier()

    def _load_data(self):
        val_path = Path("src/extraction/data_llm/data_val.xlsx")
        test_path = Path("src/extraction/data_llm/data_test.xlsx")
        
        self.X_val = pd.read_excel(val_path).reset_index(drop=True)
        self.X_test = pd.read_excel(test_path).reset_index(drop=True)
        
    def extract(self,mode: str,data:pd.DataFrame):
        """Fonction qui utilise le prompt général capable d'extraire la seniorité, le nom du job et la stack.
        Sinon elle traite chaque version
        """

        prompts = {
            "Seniority": "seniority_classifier",
            "Job": "job_classifier_prompt",
            "Stack": "stack_extraction_prompt",
        }

        if mode not in prompts:
            raise ValueError(f"Mode inconnu : {mode}")

        self._set_prompt(prompts[mode])

        data = data.copy()

        colonnes = ["poste", "experience", "description"]
        data[colonnes] = data[colonnes].fillna("not provided")

        return self._run_llm(data)
            
    def _run_llm(self,data:pd.DataFrame):
        """Utilise la configuration du LLM_Extractor pour parcourir les données et inférer"""
        
        results = []
        total_tokens = []

        for _, row in tqdm(data.iterrows(), total=len(data)):

            user_prompt = (
                f"Title: {row['poste']}\n"
                f"Raw experience: {row['experience']}\n"
                f"Description:\n{row['description']}"
            )

            try:
                response = ollama.chat(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    format=self.schema,
                    options=self.model_params,
                    think=False,
                    keep_alive="30m",
                )

                res_data = json.loads(response.message.content)

                total_tokens.append(
                    (response.prompt_eval_count or 0)
                    + (response.eval_count or 0)
                )

            except Exception as error:
                res_data = {"erreur": str(error)}

            results.append(res_data)

        print("Max tokens :", max(total_tokens))

        return pd.concat([data.reset_index(drop=True), pd.DataFrame(results)],axis=1)

    def evaluate(self, mode: str, dataset: str = "val"):
        """Évalue les prédictions du LLM sur un jeu de données annoté."""

        datasets = {
            "val": self.X_val,
            "test": self.X_test
        }
        
        if dataset not in datasets:
            raise ValueError(f"Dataset inconnu : {dataset}")

        if mode not in ["Job", "Seniority", "Stack"]:
            raise ValueError(f"Mode inconnu : {mode}")

        data = datasets[dataset].reset_index(drop=True).copy()

        # Ne pas transmettre les annotations manuelles au LLM
        X = data.drop(
            columns=["Job_cat", "Seniority", "Stack required", "Stack desired"],
            errors="ignore"
        )

        # Inférence
        res = self.extract(mode, X).reset_index(drop=True)

        if mode in ["Job", "Seniority"]:

            columns = {
                "Job": ("Job_cat", "categorie"),
                "Seniority": ("Seniority", "seniority_llm"),
            }

            true_col, pred_col = columns[mode]

            y_true = data[true_col].astype(str).str.strip()
            y_pred = res[pred_col].fillna("ERREUR").astype(str).str.strip()

            scores = {
                "accuracy": accuracy_score(y_true, y_pred),
                "macro_f1": f1_score(
                    y_true,
                    y_pred,
                    labels=y_true.unique(),
                    average="macro",
                    zero_division=0
                ),
                "nb_erreurs": int((y_true != y_pred).sum())
            }

            res[f"{true_col}_vrai"] = y_true
            res["correct"] = y_true == y_pred

        else:

            y_req = data["Stack required"].apply(to_set).apply(clean_stack)
            y_des = data["Stack desired"].apply(to_set).apply(clean_stack)

            pred_req = res["stack_requise_extraite"].apply(to_set).apply(clean_stack)
            pred_des = res["stack_souhaitee_extraite"].apply(to_set).apply(clean_stack)

            scores = {
                "requise": eval_stack(y_req, pred_req),
                "souhaitee": eval_stack(y_des, pred_des),
                "globale": eval_stack(
                    [r | s for r, s in zip(y_req, y_des)],
                    [r | s for r, s in zip(pred_req, pred_des)]
                )
            }

            res["requis_manquants"] = [
                sorted(v - p) for v, p in zip(y_req, pred_req)
            ]
            res["requis_en_trop"] = [
                sorted(p - v) for v, p in zip(y_req, pred_req)
            ]
            res["souhaites_manquants"] = [
                sorted(v - p) for v, p in zip(y_des, pred_des)
            ]
            res["souhaites_en_trop"] = [
                sorted(p - v) for v, p in zip(y_des, pred_des)
            ]

        return scores, res

    def print(self):
        print("="*30,"LLM Extractor", "="*30)
        
        for nom,valeur in vars(self).items():
            print(f"{nom} :\t{valeur}")
            
            
        print("="*75)
    
if __name__ == "__main__":

    llm = LLM_Extractor()

    scores_job, res_job = llm.evaluate("Job", dataset="val")

    print(scores_job)
    print(res_job.head())