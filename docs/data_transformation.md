# Transformation et enrichissement des données

Les offres stockées dans MongoDB Atlas sont préparées avec **Pandas**, enrichies par un **LLM local**, puis normalisées pour leur exploitation analytique.

## 1. Chargement et préparation

La fonction `load_data_mongodb()`, dans [`src/load/mongodb.py`](../src/load/mongodb.py), charge les documents de `JobOffers.raw_offers` dans un DataFrame.

À l'ingestion, `generate_offer_id()` génère un identifiant SHA-256 à partir de l'URL et de la date de collecte. Cet identifiant est utilisé comme `_id` pour éviter l'insertion répétée d'une même observation.

La fonction `load_data()`, dans [`pipeline.py`](../pipeline.py), applique ensuite les transformations suivantes :

| Traitement | Règle |
|---|---|
| Harmonisation du profil | Compléter les valeurs nulles de `experience` avec `profil_recherche` via `combine_first()` |
| Sélection des colonnes | Retirer les métadonnées du scraper et les champs non exploités, notamment `date_de_publication` et `nb_candidats` |
| Normalisation temporelle | Convertir la date de collecte au format `YYYY-MM` |
| Déduplication | Conserver une ligne par combinaison de `poste`, `experience` et `description` |
| Filtrage | Écarter les offres dont la description et le profil sont tous les deux manquants |

Les valeurs nulles, les chaînes vides et la mention `not provided` sont considérées comme manquantes, indépendamment de la casse et des espaces périphériques. Les textes d'origine sont conservés.

`combine_first()` complète les valeurs nulles sans concaténer les textes : si les deux champs sont renseignés, `experience` est prioritaire.

Les dates de publication relatives n'étant pas normalisées, le **mois de collecte** constitue la référence temporelle de l'analyse.

## 2. Enrichissement par le LLM

La classe `LLMExtractor`, dans [`src/transformation/llm.py`](../src/transformation/llm.py), utilise **Qwen3 14B via Ollama**.

Le modèle est exécuté localement sur une machine équipée d'un GPU **AMD Radeon RX 6900 XT**, afin de maîtriser les coûts d'inférence sur plusieurs milliers d'offres.

Les prompts sont versionnés dans [`instructions_llm.json`](../src/transformation/instructions_llm.json). Chaque version définit les instructions système, les paramètres du modèle et le schéma JSON attendu.

### Configurations retenues

La fonction `extract_best_models()` sélectionne explicitement :

| Configuration | Informations utilisées |
|---|---|
| `Full v5` | Métier, technologies requises et souhaitées, informations d'expérience |
| `Seniority v2` | Niveau de séniorité final |

Ces configurations utilisent une température de `0`, un contexte de `12 000` tokens et une limite de génération de `2 048` tokens.

La stratégie repose sur **deux appels au modèle par offre**.

### Traitement des entrées et sorties

`extract_entities()` sélectionne le prompt et prépare les champs d'entrée. `_predict_dataframe()` transmet chaque offre à `ollama.chat()`, à partir du titre, du profil recherché et de la description.

Les réponses sont structurées selon un schéma JSON, décodées avec `json.loads()`, puis ajoutées au DataFrame initial. Les exceptions sont enregistrées dans une colonne `erreur`.

Pour `Seniority v2`, `_seniority_from_levels()` retient le niveau le plus élevé parmi les classifications issues du titre, de l'expérience et de la description. Ce résultat remplace la séniorité produite par `Full v5`.

Les résultats et les limites de sélection sont détaillés dans [Évaluation des prompts du LLM](llm_evaluation.md).

## 3. Normalisation après enrichissement

La fonction `clean_df()`, dans [`src/transformation/clean.py`](../src/transformation/clean.py), prépare les résultats pour la couche Silver.

| Traitement | Implémentation |
|---|---|
| Technologies | `to_set()` et `clean_stack()` harmonisent les valeurs à l'aide d'alias et d'exclusions |
| Regroupement des technologies | Union des technologies requises et souhaitées dans `all_technologies` |
| Données manquantes | Remplacement des entreprises et localisations nulles par `Non renseignée` |
| Entreprises | Nettoyage textuel, détection des noms suspects et correction ciblée par le LLM |
| Clé entreprise | Création de `company_key`, sans distinction de casse, d'accents ou de ponctuation |
| Expérience | Regroupement en catégories `0`, `1`, `2`, `3`, `4`, `5` et `5+` |
| Schéma de sortie | Suppression des champs intermédiaires et renommage des colonnes en anglais au format `snake_case` |

Les alias et exclusions sont définis dans [`tech_constants.py`](../src/transformation/config/tech_constants.py). Ils permettent notamment de regrouper plusieurs écritures d'une même technologie sous une appellation commune.

### Normalisation des entreprises

`standardize_companies()` traite chaque nom distinct une seule fois :

1. Nettoyage des espaces et des suffixes identifiables, comme `Super recruteur`.
2. Analyse avec le modèle spaCy `fr_core_news_md`.
3. Sélection des noms suspects : plusieurs entités, nom de personne en suffixe, texte autour d'une entité ou nom contenant au moins trois mots.
4. Envoi des seuls noms suspects au LLM avec le mode `Company`.
5. Réassociation des corrections aux offres et création de `company_key`.

La clé de rapprochement est séparée du nom affiché pour conserver une présentation lisible tout en harmonisant les variations typographiques.

## 4. Approches expérimentées

### Classification par expressions régulières

Une première approche utilisait des règles et des expressions régulières pour classer les offres.

Cette méthode est rapide, mais interprète difficilement le contexte. Une mention de stagiaires dans les missions ne signifie pas nécessairement que le poste proposé est un stage. Les intitulés génériques et les exigences implicites limitent également la couverture des règles.

Les regex ont servi de point de comparaison. Le LLM a été retenu pour exploiter conjointement le titre, le profil et la description.

### Extraction spécialisée ou combinée

| Approche | Enseignement | Décision |
|---|---|---|
| Prompts spécialisés `Job`, `Seniority`, `Stack` | Évaluation indépendante des tâches, mais plusieurs requêtes pour enrichir une offre | Conservés pour les comparaisons |
| Prompt `Job_Stack` | Extraction combinée du métier et des technologies ; résultats insuffisants sur le test | Non retenu |
| Prompt `Full` | Extraction de plusieurs informations dans une requête, mais séniorité moins performante que le prompt spécialisé retenu | Retenu pour le métier, les technologies et l'expérience |
| `Full v5` + `Seniority v2` | Compromis entre qualité et nombre de requêtes | Configuration retenue |

`Stack v2` obtient un meilleur F1 global d'extraction des technologies que `Full v5` sur le test. Le choix de `Full v5` évite toutefois une requête spécialisée supplémentaire, puisqu'il fournit également le métier et les informations d'expérience.

### Normalisation des entreprises

| Approche | Limite observée | Décision |
|---|---|---|
| Expressions régulières seules | Insuffisantes pour distinguer systématiquement entreprise, recruteur et texte supplémentaire | Conservées pour le nettoyage simple |
| Fuzzy matching avec RapidFuzz | Des noms similaires pouvaient désigner des entreprises différentes et provoquer des rapprochements incorrects | Fusion automatique non retenue |
| NER seule | Les champs courts offrent trop peu de contexte pour identifier systématiquement l'entreprise pertinente | Non retenue comme méthode unique |
| Nettoyage + NER comme filtre + LLM ciblé | Réserve l'interprétation des cas suspects au LLM | Approche retenue |

La similarité textuelle n'est pas utilisée seule pour fusionner des entreprises. `company_key` harmonise la forme des noms sans constituer une preuve d'identité entre deux entreprises.

## 5. Export et automatisation prévue

`save_data()`, dans [`pipeline.py`](../pipeline.py), enregistre les données au format **Parquet**, localement ou dans **Azure Data Lake Storage Gen2**.

Le jeu obtenu constitue la couche Silver, utilisée pour la [modélisation analytique](architecture.md).

À terme, ces traitements seront déclenchés automatiquement après chaque collecte. L'orchestration devra assurer la disponibilité d'Ollama, conserver les journaux d'exécution et permettre de reprendre les traitements en échec sans dupliquer les observations.

**Statut : automatisation prévue, non encore implémentée.**

## 6. Limites et travaux reportés

- **Historisation :** la déduplication actuelle ne tient pas compte du mois de collecte. Elle devra être adaptée pour conserver les observations d'une même annonce sur plusieurs périodes.
- **Localisations :** le nettoyage géographique approfondi a été reporté. La collecte initiale ciblant l'Île-de-France, l'harmonisation des villes, départements, régions, localisations multiples et mentions de télétravail n'a pas été priorisée.
- **Entreprises :** le filtre NER repose sur des heuristiques ; certains noms ambigus peuvent ne pas être détectés.
- **Fiabilité :** une réponse JSON structurée ne garantit pas l'exactitude des informations extraites.