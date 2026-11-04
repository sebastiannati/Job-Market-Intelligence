# Job Market Intelligence

**Analyse du marché de l'emploi Data & IA en France.**

Ce projet personnel consiste à développer un pipeline Data de bout en bout pour collecter, nettoyer, classifier et analyser des offres d'emploi.

L'objectif est de transformer des données non structurées en informations exploitables dans **Power BI**, afin d'étudier les métiers, les niveaux d'expérience et les compétences techniques recherchées.

La collecte initiale porte sur **avril 2026**, avec un ciblage géographique de l'Île-de-France. Les résultats ne représentent donc pas l'ensemble du marché français.

## Architecture

Le projet repose sur une **architecture médaillon** :

1. **Collecte — Python et Playwright :** extraction des offres depuis plusieurs plateformes.
2. **MongoDB Atlas — Bronze :** stockage des offres brutes.
3. **Python et LLM local :** nettoyage, classification et extraction d'informations avec Qwen3 14B.
4. **Azure Data Lake Storage Gen2 — Silver :** stockage des données préparées au format Parquet.
5. **Databricks SQL — Silver → Gold :** création et alimentation du modèle dimensionnel.
6. **Azure SQL — Gold :** stockage du Data Warehouse — *en cours*.
7. **Power BI :** analyse et visualisation — *en cours*.

![Architecture du pipeline](docs/images/pipeline_illustration.png)

Les choix de modélisation sont détaillés dans [Architecture et modèle dimensionnel](docs/architecture.md).

## Préparation et enrichissement

Les offres proviennent de **LinkedIn, Indeed, France Travail, Station F et HelloWork**.

Après leur chargement depuis MongoDB, les données sont harmonisées et dédupliquées avec Pandas. Le LLM identifie ensuite le métier, la séniorité et les technologies requises ou souhaitées.

Les résultats sont normalisés avant leur export vers la couche Silver.

Voir [Transformation et enrichissement des données](docs/data_transformation.md) pour les règles appliquées et les approches expérimentées.

## Résultats

- **2 472 offres** collectées.
- **1 970 offres** conservées après nettoyage et déduplication.
- **Modèle dimensionnel :** dimensions, table de faits et table de pont des technologies.
- **Azure SQL et Power BI :** intégration en cours.

### Évaluation du LLM

Les versions de prompts utilisant **Qwen3 14B** sont comparées à des annotations de référence préannotées par des LLM, puis revues et corrigées manuellement.

| Tâche | Configuration retenue | Résultat sur le test |
|---|---|---:|
| Classification du métier | `Full v5` | Macro-F1 : **89,9 %** |
| Classification de la séniorité | `Seniority v2` | Macro-F1 : **86,5 %** |
| Extraction des technologies | `Full v5` | F1 micro global : **76,1 %** |
| Normalisation des entreprises | `Company v1` | Accuracy : **100 %** sur 35 noms renseignés |

Les trois premières tâches sont évaluées sur **39 offres de test**. Ces résultats restent à interpréter au regard de la taille des échantillons et de la démarche de sélection des prompts.

Voir [Évaluation des prompts du LLM](docs/llm_evaluation.md) pour les jeux utilisés, les graphiques et les limites méthodologiques.

## Stack technique

| Domaine | Technologies |
|---|---|
| Extraction | Python, Playwright |
| Stockage | MongoDB Atlas, Azure Data Lake Storage Gen2 |
| Traitement | Pandas, SQL, Databricks |
| IA générative | Ollama, Qwen3 14B |
| Normalisation des entreprises | spaCy, expressions régulières, LLM |
| Évaluation | scikit-learn |
| Data Warehouse | Databricks SQL, Azure SQL |
| Visualisation | Power BI |

## Automatisation prévue

L'objectif est d'automatiser le cycle complet :

1. Lancement planifié des scrapers.
2. Ingestion des observations dans MongoDB.
3. Nettoyage, inférence locale et normalisation.
4. Export des données Silver dans Azure Data Lake.
5. Alimentation du modèle Gold.
6. Actualisation du modèle sémantique Power BI après validation du chargement.

L'orchestration devra gérer les dépendances, les journaux d'exécution, les alertes et la reprise sans duplication.

L'inférence locale nécessitera que la machine hébergeant Ollama soit disponible. L'outil d'orchestration reste à sélectionner.

**Statut : automatisation prévue, non encore implémentée.**

## Autres perspectives

- Étendre les collectes à de nouvelles périodes et zones géographiques.
- Finaliser les tableaux de bord Power BI.
- Développer un assistant RAG de candidature, alimenté par mon parcours, mes expériences et mes projets.

## Documentation technique

| Document | Contenu |
|---|---|
| [Transformation des données](docs/data_transformation.md) | Nettoyage, inférence, normalisation et approches expérimentées |
| [Évaluation du LLM](docs/llm_evaluation.md) | Jeux annotés, métriques, graphiques et choix des prompts |
| [Architecture et modèle dimensionnel](docs/architecture.md) | Schéma étoile, table de faits, table de pont et alimentation |

### Code source

- [Pipeline principal](pipeline.py)
- [Chargement et stockage](src/load/)
- [Transformations et inférence](src/transformation/)
- [Configuration des prompts](src/transformation/instructions_llm.json)
- [Scripts du Data Warehouse](warehouse/)

---

*Projet personnel en cours de développement.*