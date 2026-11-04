# Transformation et enrichissement des données

Les offres stockées dans MongoDB Atlas sont préparées avec **Pandas**, enrichies par un **LLM local**, puis normalisées pour leur exploitation analytique.

## 1. Chargement et préparation

La fonction `load_data_mongodb()`, dans [`src/load/mongodb.py`](../src/load/mongodb.py), charge les documents de `JobOffers.raw_offers` dans un DataFrame.

La fonction `load_data()`, dans [`pipeline.py`](../pipeline.py), applique ensuite les traitements suivants :

| Traitement | Règle |
|---|---|
| Harmonisation du profil | Compléter les valeurs nulles de `experience` avec `profil_recherche` via `combine_first()` |
| Sélection des colonnes | Retirer les métadonnées du scraper et les champs non exploités, notamment `date_de_publication` et `nb_candidats` |
| Normalisation temporelle | Convertir la date de collecte au format `YYYY-MM` |
| Déduplication | Conserver une ligne par combinaison de `poste`, `experience` et `description` |
| Filtrage | Écarter les offres dont la description et le profil sont tous les deux manquants |

Les valeurs nulles, les chaînes vides et la mention `not provided` sont considérées comme manquantes, indépendamment de la casse et des espaces périphériques. Les textes d'origine sont conservés.

`combine_first()` complète les valeurs nulles sans concaténer les textes : si les deux champs sont renseignés, `experience` est prioritaire.

La référence temporelle représente le **mois de collecte**, et non le mois de publication. La déduplication actuelle ne tient pas compte de cette période et devra être adaptée pour une analyse historique.

## 2. Enrichissement par le LLM

La classe `LLMExtractor`, dans [`src/transformation/llm.py`](../src/transformation/llm.py), utilise **Qwen3 14B via Ollama**, exécuté localement.

Les prompts sont versionnés dans [`instructions_llm.json`](../src/transformation/instructions_llm.json). Chaque version définit les instructions système, les paramètres du modèle et le schéma JSON attendu.

La fonction `extract_best_models()` sélectionne explicitement deux configurations :

| Configuration | Informations utilisées |
|---|---|
| `Full v5` | Métier, technologies requises et souhaitées, informations d'expérience |
| `Seniority v2` | Niveau de séniorité final |

Ces configurations utilisent une température de `0`, un contexte de `12 000` tokens et une limite de génération de `2 048` tokens.

La méthode `extract_entities()` sélectionne le prompt et prépare les champs d'entrée. `_predict_dataframe()` transmet ensuite chaque offre à `ollama.chat()`, à partir du titre, du profil recherché et de la description.

Les réponses sont structurées selon un schéma JSON, décodées avec `json.loads()`, puis ajoutées au DataFrame initial. Les exceptions sont enregistrées dans une colonne `erreur`.

Pour `Seniority v2`, `_seniority_from_levels()` retient le niveau le plus élevé parmi les classifications issues du titre, de l'expérience et de la description. Ce résultat remplace la séniorité produite par `Full v5`.

Les métriques et les comparaisons sont présentées dans [Évaluation des prompts du LLM](llm_evaluation.md).

## 3. Normalisation après enrichissement

La fonction `clean_df()`, dans [`src/transformation/clean.py`](../src/transformation/clean.py), prépare les résultats pour la couche Silver.

| Traitement | Implémentation |
|---|---|
| Technologies | `to_set()` et `clean_stack()` harmonisent les valeurs à l'aide des alias et exclusions |
| Regroupement des technologies | Union des technologies requises et souhaitées dans `all_technologies` |
| Données manquantes | Remplacement des entreprises et localisations nulles par `Non renseignée` |
| Entreprises | Nettoyage textuel, détection des noms suspects et correction ciblée par le LLM |
| Clé entreprise | Création de `company_key`, sans distinction de casse, d'accents ou de ponctuation |
| Expérience | Regroupement en catégories `0`, `1`, `2`, `3`, `4`, `5` et `5+` |
| Schéma de sortie | Suppression des champs intermédiaires et renommage des colonnes en anglais au format `snake_case` |

Les alias et exclusions des technologies sont définis dans [`tech_constants.py`](../src/transformation/config/tech_constants.py).

### Normalisation des entreprises

La fonction `standardize_companies()` traite chaque nom distinct une seule fois :

1. Nettoyage des espaces et des suffixes identifiables, comme `Super recruteur`.
2. Analyse avec le modèle spaCy `fr_core_news_md`.
3. Sélection des noms suspects : plusieurs entités, nom de personne en suffixe, texte autour d'une entité ou nom contenant au moins trois mots.
4. Envoi des seuls noms suspects au LLM avec le mode `Company`.
5. Réassociation des corrections aux offres et création de `company_key`.

La clé de rapprochement est séparée du nom affiché pour conserver une présentation lisible tout en harmonisant les variations typographiques.

## 4. Approches expérimentées et choix retenus

### Classification par expressions régulières

Une première approche reposait sur des règles et des expressions régulières pour classer les offres, notamment à partir des intitulés et des mentions d'expérience.

Cette méthode est rapide, mais interprète difficilement le contexte : une mention de stagiaires dans les missions ne signifie pas nécessairement que le poste est un stage. Les intitulés génériques et les exigences implicites limitent également la couverture des règles.

Les regex ont servi de point de comparaison. Le LLM a été retenu pour exploiter conjointement le titre, le profil et la description. Les annotations manuelles constituent la référence d'évaluation.

### Extraction spécialisée ou combinée

Plusieurs stratégies de prompts ont été comparées :

| Approche | Enseignement | Décision |
|---|---|---|
| Prompts spécialisés `Job`, `Seniority`, `Stack` | Permettent d'évaluer chaque tâche séparément, mais nécessitent plusieurs requêtes pour enrichir une offre |
| Prompt `Job_Stack` | Testé pour combiner métier et technologies ; performances insuffisantes sur le jeu de test |
| Prompt combiné `Full` | Regroupe plusieurs extractions dans une requête, mais sa séniorité est moins performante que celle du prompt spécialisé retenu |
| `Full v5` + `Seniority v2` | Combine extraction générale et classification dédiée de la séniorité | Configuration retenue |

`Stack v2` obtient un meilleur F1 global d'extraction des technologies que `Full v5` sur le test. Le choix de `Full v5` constitue un compromis : il fournit aussi le métier et les informations d'expérience sans requête spécialisée supplémentaire.

Les résultats détaillés et les limites de sélection sont documentés dans [Évaluation des prompts](llm_evaluation.md).

### Normalisation des entreprises

Plusieurs méthodes ont été explorées pour retirer le bruit et rapprocher les variantes de noms.

| Approche | Limite observée | Décision |
|---|---|---|
| Expressions régulières seules | Adaptées aux suffixes connus, mais insuffisantes pour distinguer systématiquement entreprise, recruteur et texte supplémentaire | Conservées pour le nettoyage simple |
| Fuzzy matching avec RapidFuzz | Des noms similaires pouvaient désigner des entreprises différentes et provoquer des rapprochements incorrects | Fusion automatique non retenue |
| NER seule | Les noms courts offrent trop peu de contexte pour identifier systématiquement l'entreprise pertinente | Non retenue comme méthode unique |
| Nettoyage + NER comme filtre + LLM ciblé | Permet de réserver l'interprétation des cas suspects au LLM | Approche retenue |

La similarité textuelle n'est donc pas utilisée seule pour fusionner des entreprises. La clé `company_key` harmonise la forme des noms, sans constituer une preuve que deux entreprises sont identiques.

## 5. Export

La fonction `save_data()`, dans [`pipeline.py`](../pipeline.py), enregistre les données au format **Parquet**, localement ou dans **Azure Data Lake Storage Gen2**.

Le jeu obtenu constitue la couche Silver : des offres structurées et enrichies, prêtes pour la modélisation analytique.

## 6. Limites et travaux reportés

- **Localisations :** le nettoyage géographique approfondi a été reporté. La collecte initiale ciblant l'Île-de-France, l'harmonisation des villes, départements, régions, localisations multiples et mentions de télétravail n'a pas été priorisée.
- **Historisation :** le mois de collecte devra être intégré à la déduplication pour préserver les observations d'une même annonce sur plusieurs périodes.
- **Entreprises :** le filtre NER repose sur des heuristiques ; certains noms ambigus peuvent ne pas être détectés.
- **Qualité des données :** la présence d'un texte ne garantit pas sa pertinence, et une réponse JSON structurée ne garantit pas l'exactitude des informations extraites.