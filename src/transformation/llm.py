import json

import ollama
import pandas as pd
from path import Path
from sklearn.metrics import accuracy_score, f1_score
from tqdm import tqdm

from src.transformation.clean import clean_stack, to_set
from src.transformation.config.job_constants import *

""" 
Ce fichier contient la classe qui permet d'extraire des informations via un model local.
"""
class LLMExtractor:
    
    def __init__(self):
        """Par défaut, crée une instance qui charge le prompt général d'extraction."""
        # Loads all instructions
        self.instructions = self._load_prompt_configs()
        
        # LLM's configuration
        self.extraction_entity = None
        self.entity_name = None
        self.active_version = None
        self.version = None
        self.model = None
        self.model_params = None
        self.prompt = None
        self.schema = None

        # Gets full extraction prompt
        self._configure_model("full_extraction")
    
        # Data for evaluation 
        self.X_val = pd.DataFrame()
        self.X_test = pd.DataFrame()
        
        self._load_evaluation_datasets()
    
    def _load_prompt_configs(self):
        """Charge toutes les configurations du fichiers `instructions_llm.json` pour manipuler les versions plus facilement.

        Returns:
            dict: Dictionnaire qui contient toutes les version de chaque instructions 
            (full, seniority, job, stack) pour extraire les informations des offres d'emplois.
        """
        # Path
        instructions_path = Path("src/transformation/instructions_llm.json") 
        
        instructions = {}
        
        with open(instructions_path,encoding="utf-8") as f:
            instructions = json.load(f)
        
        return instructions
    
    def _configure_model(self, entity_to_extract, version="active_version"):
        """Sélectionne l'entité et charge sa configuration LLM."""

        if entity_to_extract not in self.instructions:
            raise ValueError(f"Entité inconnue : {entity_to_extract}")
        self.entity_name = entity_to_extract
        self.extraction_entity = self.instructions[entity_to_extract]

        def _load_classifier():
            self.active_version = (
                self.extraction_entity["active_version"]
                if version == "active_version"
                else version
            )

            if self.active_version not in self.extraction_entity:
                raise ValueError(f"Version inconnue : {self.active_version}")

            self.version = self.extraction_entity[self.active_version]

            self.model = self.version["model"]
            self.model_params = self.version["params"]
            self.prompt = self.version["system_prompt"]
            self.schema = self.version["schema"]

        _load_classifier()

    def _load_evaluation_datasets(self):
        val_path = Path("src/transformation/data_llm/data_val.xlsx")
        test_path = Path("src/transformation/data_llm/data_test.xlsx")
        
        self.X_val = pd.read_excel(val_path).reset_index(drop=True)
        self.X_test = pd.read_excel(test_path).reset_index(drop=True)
        
    def extract_entities(self,mode: str,data:pd.DataFrame, version = "active_version"):
        """Fonction qui utilise le prompt général capable d'extraire la seniorité, le nom du job et la stack.
        Sinon elle traite chaque version
        """

        prompts = {
            "Job_Stack" : "job_and_stack",
            "Seniority": "seniority_classification",
            "Job": "job_classification",
            "Stack": "stack_extraction",
            "Full": "full_extraction",
            "Company": "company_extraction"
        }

        if mode not in prompts:
            raise ValueError(f"Mode inconnu : {mode}")

        self._configure_model(prompts[mode],version=version)

        data = data.copy()
        
        if mode != "Company":
            colonnes = ["poste", "experience", "description"]
            data[colonnes] = data[colonnes].fillna("not provided")

        return self._predict_dataframe(data)
            
    def _predict_dataframe(self,data:pd.DataFrame):
        """Utilise la configuration du LLM_Extractor pour parcourir les données et inférer"""
        
        results = []
        total_tokens = []

        for _, row in tqdm(data.iterrows(), total=len(data)):
            
            if self.entity_name == "company_extraction": 
                user_prompt = f"Company name: {row['company_normalized']}"
            
            else : 
                user_prompt = (f"Title: {row['poste']}\n" 
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
        
        df = pd.concat([data.reset_index(drop=True), pd.DataFrame(results)],axis=1)
        
        return df

    def _seniority_from_levels(self, df: pd.DataFrame) -> pd.Series:
        """Calcule la séniorité maximale à partir des trois niveaux prédits pour les prompts v1 à v3 de classification de séniorité"""

        seniority_order = {
            "Stage/Alternance": 0,
            "Junior": 1,
            "Intermédiaire": 2,
            "Senior": 3,
        }

        columns = ["level_title", "level_experience", "level_description"]

        return df[columns].apply(
            lambda row: max(
                (level for level in row if level in seniority_order),
                key=seniority_order.get,
                default=None
            ),
            axis=1
        )

    def _eval_stack(self,y_true, y_pred):
        """Calcule les métriques micro sur toutes les technologies."""

        tp = fn = fp = 0

        for true, pred in zip(y_true, y_pred):
            tp += len(true & pred) # len des bonnes extractions
            fp += len(pred - true) # len des extractions en trop
            fn += len(true - pred) # len des extractions en moins

        precision = tp/(tp+fp) # mesures les techno en trop (si fp (techno en trop) petit alors fp/fp =1)
        recall = tp/(fn+tp)  # mesures les techno en moins (si fn petit (techno qui manquent) alors tp/tp)
        f1 = 2*(precision*recall)/(precision+recall)#moyenne harmonique des deux

        return {
            "precision": precision,
            "recall": recall,
            "f1": f1
        }

    def evaluate_prompt(self, mode: str, dataset: str = "val", version: str = "active_version"):
        """Évalue les prédictions du LLM selon le mode sélectionné."""

        datasets = {
            "val": self.X_val,
            "test": self.X_test,
        }

        if dataset not in datasets:
            raise ValueError(f"Dataset inconnu : {dataset}")

        if mode not in ["Job", "Seniority", "Stack", "Full", "Job_Stack", "Company"]:
            raise ValueError(f"Mode inconnu : {mode}")

        data = datasets[dataset].copy()
        
        # Ne pas prendre les lignes qui ne contiennent pas de valeurs pour l'entreprise        
        if mode == "Company":
            # Exclure les offres sans nom d'entreprise.
            data = data.dropna(subset=["entreprise"])

            # Exclure également les noms vides.
            data = data[data["entreprise"].astype(str).str.strip().ne("")]
            data["company_normalized"] = data["entreprise"] # colonne attendue par le llm

        data = data.reset_index(drop=True)
        
        X = data.drop(columns=["Job_cat", "Seniority", "Stack required", "Stack desired","company_true"],errors="ignore")
        
        # Une seule inférence pour tous les modes
        res = self.extract_entities(mode, X, version=version).reset_index(drop=True)

        scores = {}

        classifications = {
            "Job": ("Job_cat", "job_predicted"),
            "Seniority": ("Seniority", "seniority_llm"),
        }

        for task, (true_col, pred_col) in classifications.items():

            # Job_Stack évalue uniquement Job
            if mode not in [task, "Full"] and not (mode == "Job_Stack" and task == "Job"):
                continue

            # Compatibilité Seniority v1-v3
            if task == "Seniority" and pred_col not in res.columns:
                res[pred_col] = self._seniority_from_levels(res)

            y_true = data[true_col].astype(str).str.strip()
            y_pred = res[pred_col].fillna("ERREUR").astype(str).str.strip()

            # Préfixes pour les modes multi-tâches
            prefix = (f"{task.lower()}_" if mode in ["Full", "Job_Stack"] else "")

            scores[f"{prefix}accuracy"] = accuracy_score(y_true, y_pred)

            scores[f"{prefix}macro_f1"] = f1_score(y_true,y_pred,labels=y_true.unique(),average="macro",zero_division=0)

            scores[f"{prefix}nb_erreurs"] = int((y_true != y_pred).sum())

            # Colonnes pour analyser les erreurs
            res[f"{true_col}_vrai"] = y_true

            correct_col = (f"{task.lower()}_correct" if mode in ["Full", "Job_Stack"] else "correct")

            res[correct_col] = y_true == y_pred

        # Stacks
        if mode in ["Stack", "Full", "Job_Stack"]:

            y_req = data["Stack required"].apply(to_set).apply(clean_stack)
            y_des = data["Stack desired"].apply(to_set).apply(clean_stack)
            y_global = [required | desired for required, desired in zip(y_req, y_des)]

            pred_req = res["stack_required"].apply(to_set).apply(clean_stack)
            pred_des = res["stack_desired"].apply(to_set).apply(clean_stack)
            pred_global = [required | desired for required, desired in zip(pred_req, pred_des)]
            
            res["all_technologies"] = [sorted(stack) for stack in pred_global]
            res["all_technologies"] = res["all_technologies"].apply(to_set).apply(clean_stack)

            scores.update({
                "required": self.eval_stack(y_req, pred_req),
                "desired": self.eval_stack(y_des, pred_des),
                "globale": self.eval_stack(y_global, pred_global)
            })

            # Vérité terrain
            res["Stack required_vrai"] = data["Stack required"]
            res["Stack desired_vrai"] = data["Stack desired"]

            # Analyse des erreurs
            res["required_missing"] = [sorted(true - pred) for true, pred in zip(y_req, pred_req)]
            res["required_extra"] = [sorted(pred - true) for true, pred in zip(y_req, pred_req)]
            res["desired_missing"] = [sorted(true - pred) for true, pred in zip(y_des, pred_des)]
            res["desired_extra"] = [sorted(pred - true) for true, pred in zip(y_des, pred_des)]

        if mode == "Company":
            # Pour clean les nom des entreprises
            y_true = data["company_true"].astype(str).str.strip().str.casefold()
            y_pred = res["company_name_llm"].fillna("ERREUR").astype(str).str.strip().str.casefold()

            scores["accuracy"] = accuracy_score(y_true, y_pred)
            scores["nb_erreurs"] = int((y_true != y_pred).sum())
            scores["nb_total"] = len(y_true)

            # Comparaison des résultats pour analyser les erreurs
            res["company_true"] = y_true
            res["correct"] = y_true == y_pred

        return scores, res
    
    def evaluate_prompt_versions(self,mode: str = "All",dataset: str = "val",versions: list | None = None):
        """Évalue les versions des prompts et sauvegarde scores et prédictions."""

        modes = {
            "Job_Stack": "job_and_stack",
            "Job": "job_classification",
            "Seniority": "seniority_classification",
            "Stack": "stack_extraction",
            "Full": "full_extraction",
            "Company": "company_extraction"
        }

        if mode != "All" and mode not in modes:
            raise ValueError(f"Mode inconnu : {mode}")

        datasets = {"val": self.X_val,"test": self.X_test,}

        if dataset not in datasets:
            raise ValueError(f"Dataset inconnu : {dataset}")

        # Tous les modes ou un seul
        selected_modes = modes if mode == "All" else {mode: modes[mode]}

        # Dossier de sauvegarde
        output_dir = Path(f"src/transformation/evaluation_llm/{dataset}")

        ground_truth = datasets[dataset].reset_index(drop=True)

        # Colonnes de vérité terrain à conserver avec les prédictions
        truth_columns = {
            "Job": ["Job_cat"],
            "Seniority": ["Seniority"],
            "Stack": ["Stack required", "Stack desired"],
            "Full": ["Job_cat","Seniority","Stack required","Stack desired"],
            "Job_Stack": ["Job_cat","Stack required","Stack desired"],
            "Company": ["company_true"]
        }

        all_results = []

        for current_mode, entity in selected_modes.items():

            # Récupérer les versions propres à chaque prompt
            if versions is None:
                current_versions = [
                    key for key in self.instructions[entity]
                    if key.startswith("v") and key[1:].isdigit()
                ]
            else:
                current_versions = versions

            current_versions = sorted(current_versions,key=lambda v: int(v[1:]))
            
            if current_mode == "Company":
                        # Appliquer le même filtre que dans evaluate_prompt().
                        ground_truth = ground_truth.dropna(subset=["entreprise"])
                        ground_truth = ground_truth.loc[ground_truth["entreprise"].astype(str).str.strip().ne("")]
                        
            ground_truth = ground_truth.reset_index(drop=True)

            for version in current_versions:

                print(f"\nÉvaluation : {current_mode} - {version}")

                result = {"mode": current_mode,"version": version,}

                try:
                    
                    scores, predictions = self.evaluate_prompt(mode=current_mode,dataset=dataset,version=version)

                    # Conserver la vérité terrain avec les prédictions
                    predictions = predictions.reset_index(drop=True).copy()

                    if len(predictions) != len(ground_truth):
                        raise ValueError("Nombre de prédictions différent du dataset "f"({len(predictions)} vs {len(ground_truth)})")

                    for col in truth_columns[current_mode]:
                        predictions[f"{col}_true"] = ground_truth[col]

                    # Sauvegarder les prédictions de cette version
                    predictions_path = output_dir / (f"predictions_{dataset}_"f"{current_mode.lower()}_{version}.parquet")

                    predictions.to_parquet(predictions_path,index=False)

                    # Ajouter les métriques
                    result.update(pd.json_normalize(scores, sep="_").iloc[0].to_dict())

                    result["status"] = "OK"

                except Exception as error:
                    result["status"] = "ERREUR"
                    result["erreur"] = str(error)

                    print(f"Erreur : {error}")

                # Fichier des scores du mode courant
                scores_path = output_dir / (f"results_{dataset}_{current_mode.lower()}.csv")

                # Conserver les autres versions déjà évaluées
                if scores_path.exists():
                    results = pd.read_csv(scores_path)

                    results = results[results["version"] != version]
                else:
                    results = pd.DataFrame()

                # Ajouter les résultats de la version courante
                results = pd.concat([results, pd.DataFrame([result])],ignore_index=True)

                # Trier les versions
                results = results.sort_values("version",key=lambda s: s.str.extract(r"v(\d+)")[0].astype(int))

                # Sauvegarder les métriques
                results.to_csv(scores_path, index=False)

                all_results.append(result)

        return pd.DataFrame(all_results)
    
    def print_config(self):
        print("="*30,"LLM Extractor", "="*30)
        
        for nom,valeur in vars(self).items():
            print(f"{nom} :\t{valeur}")
            
        print("="*75)
    
if __name__ == "__main__":

    llm = LLMExtractor()
    llm.evaluate_prompt_versions(mode="Company",dataset="val",versions = ["v1"])
    llm.evaluate_prompt_versions(mode="Company",dataset="test",versions = ["v1"])