# Évaluation des prompts du LLM

L'évaluation compare plusieurs versions de prompts utilisant **Qwen3 14B** pour trois tâches : classification du métier, classification de la séniorité et extraction des technologies.

Le modèle n'est pas réentraîné : les expérimentations portent sur les instructions et les stratégies d'extraction, par tâche ou combinées.

## 1. Jeux annotés

Les prédictions sont comparées à des annotations manuelles enregistrées dans deux fichiers :

| Jeu | Taille | Fichier | Utilisation |
|---|---:|---|---|
| Validation | 42 offres | [`data_val.xlsx`](../src/transformation/data_llm/data_val.xlsx) | Comparaison des prompts et analyse des erreurs |
| Test | 39 offres | [`data_test.xlsx`](../src/transformation/data_llm/data_test.xlsx) | Comparaison des performances sur un jeu distinct |

Les annotations comprennent le métier, la séniorité et les technologies requises ou souhaitées. Elles sont retirées des données envoyées au LLM afin de ne pas lui fournir les réponses attendues.

Les erreurs observées permettent d'examiner les ambiguïtés des offres et d'ajuster les consignes. Les versions des prompts sont conservées dans [`instructions_llm.json`](../src/transformation/instructions_llm.json).

## 2. Méthode et métriques

La classe `LLMExtractor`, dans [`src/transformation/llm.py`](../src/transformation/llm.py), centralise l'évaluation :

- `evaluate_prompt()` compare les prédictions aux annotations.
- `evaluate_prompt_versions()` exécute plusieurs versions et sauvegarde leurs résultats.

| Tâche | Métriques |
|---|---|
| Métier et séniorité | Accuracy, macro-F1 et nombre d'erreurs |
| Technologies | Précision, rappel et F1 micro, calculés séparément pour les technologies requises, souhaitées et leur union |

Le macro-F1 donne le même poids à chaque classe évaluée. Pour les technologies, la précision mesure la justesse des éléments extraits et le rappel leur couverture.

Les technologies annotées et prédites sont normalisées avec les mêmes fonctions, `to_set()` et `clean_stack()`, avant comparaison. Les éléments manquants et ceux extraits en trop sont conservés pour analyser les erreurs.

## 3. Résultats sur le jeu de test

### Classification du métier

![Accuracy et macro-F1 des prompts de classification du métier sur le jeu de test](../src/transformation/evaluation_llm/assets/job_results.png)

Les configurations `Full v1` à `Full v5` obtiennent les mêmes résultats : **89,7 % d'accuracy**, un **macro-F1 de 0,899** et **4 erreurs sur 39 offres**.

`Full v5` permet de conserver ce niveau de classification tout en extrayant les technologies et les informations d'expérience dans une même requête.

### Classification de la séniorité

![Accuracy et macro-F1 des prompts de classification de la séniorité sur le jeu de test](../src/transformation/evaluation_llm/assets/seniortity_results.png)

`Seniority v2` obtient les meilleurs résultats sur ce jeu : **89,7 % d'accuracy**, un **macro-F1 de 0,865** et **4 erreurs sur 39 offres**.

La séniorité est donc traitée par un prompt dédié dans la configuration retenue.

### Extraction des technologies

![F1 des technologies requises, souhaitées et globales sur le jeu de test](../src/transformation/evaluation_llm/assets/stack_results.png)

| Configuration | F1 requises | F1 souhaitées | F1 global |
|---|---:|---:|---:|
| `Stack v2` | 0,799 | 0,577 | 0,777 |
| `Full v5` | 0,766 | 0,494 | 0,761 |

`Stack v2` obtient un meilleur F1 global. `Full v5` est néanmoins retenu comme compromis entre qualité d'extraction et nombre de requêtes, puisqu'il fournit également la catégorie du métier et les informations d'expérience.

La distinction entre technologies requises et souhaitées reste plus difficile que l'identification de leur présence dans l'offre.

## 4. Configuration retenue

La fonction `extract_best_models()`, dans [`pipeline.py`](../pipeline.py), combine :

- **`Full v5`** pour le métier, les technologies et les informations d'expérience.
- **`Seniority v2`** pour le niveau de séniorité final.

Cette configuration associe une extraction combinée à un traitement spécialisé de la séniorité.

## 5. Traçabilité des résultats

Les résultats sont enregistrés dans [`evaluation_llm/`](../src/transformation/evaluation_llm/), avec un sous-dossier par jeu :

- `val/` : résultats de validation.
- `test/` : résultats de test.
- `assets/` : graphiques de comparaison.

Les fichiers CSV contiennent les métriques par version. Les fichiers Parquet conservent les prédictions, les annotations de référence et les informations utiles à l'analyse des erreurs.

## 6. Limites et interprétation

Les jeux évalués sont de petite taille : sur 39 offres, une seule erreur représente environ **2,6 points d'accuracy**. Ces résultats décrivent donc les échantillons étudiés et ne garantissent pas les mêmes performances sur l'ensemble du marché.

Le classement des prompts varie selon le jeu. Par exemple, `Seniority v4` obtient un macro-F1 de **0,863 en validation**, contre **0,704 pour v2**, alors que `v2` arrive en tête sur le test.

Les résultats de test présentés constituent une comparaison expérimentale. Si ce classement a servi à sélectionner les prompts retenus, un nouvel échantillon indépendant sera nécessaire pour mesurer leur performance finale sans biais de sélection.