# Modélisation analytique en schéma étoile

Les offres nettoyées et enrichies de la couche Silver sont destinées à alimenter un modèle dimensionnel construit avec **Databricks SQL**.

Ce modèle organise les données pour analyser le marché de l'emploi dans **Power BI** : métiers, séniorité, expérience demandée, entreprises et technologies.

Le stockage du Data Warehouse dans **Azure SQL** est en cours de mise en place.

## 1. Schéma du modèle

![Schéma en étoile et table de pont des technologies](images/schema_relationnel.png)

Le modèle comprend une table de faits centrale, des dimensions décrivant les offres et une table de pont reliant les offres à leurs technologies.

Les scripts de création sont disponibles dans [`warehouse/ddl/`](../warehouse/ddl/).

## 2. Pourquoi un schéma étoile ?

Le schéma étoile sépare les observations à analyser des informations qui permettent de les décrire.

La table de faits représente les offres. Les dimensions fournissent les axes d'analyse : métier, entreprise, période, plateforme, séniorité et expérience.

Cette organisation permet de :

- Centraliser les catégories et leurs libellés dans les dimensions.
- Faciliter les regroupements et les filtres dans SQL et Power BI.
- Croiser plusieurs axes, par exemple les technologies demandées pour les postes juniors de Data Engineer.

## 3. Table de faits : `fact_offers`

### Une ligne par observation d'offre

Chaque ligne de `fact_offers` représente une observation conservée après préparation, identifiée par `offer_id`.

La table contient les clés permettant de retrouver ses caractéristiques dans les dimensions :

| Colonne | Dimension associée |
|---|---|
| `job_category_id` | Métier |
| `seniority_id` | Séniorité |
| `experience_id` | Expérience minimale demandée |
| `company_id` | Entreprise, via `company_key` |
| `mois_id` | Mois de collecte |
| `plateforme_id` | Plateforme d'origine |

Cette table ne contient pas de mesure numérique comme un prix ou un chiffre d'affaires. **La présence d'une ligne constitue le fait à compter** : le volume d'offres s'obtient en comptant les observations.

### Analyses possibles

La table de faits permet notamment de calculer :

- Le nombre d'offres par métier, entreprise ou plateforme.
- La répartition des offres par séniorité.
- L'expérience minimale demandée pour chaque niveau de séniorité.
- L'évolution des volumes observés par mois, lorsque plusieurs périodes sont disponibles.

Le mois représente la période de collecte, et non la date de publication. Pour une analyse historique, la préparation doit conserver les observations d'une même annonce sur plusieurs mois.

## 4. Dimensions

| Table | Contenu | Exemple d'utilisation |
|---|---|---|
| `dim_job_category` | Catégories de métiers | Comparer Data Analyst et Data Engineer |
| `dim_seniority` | Niveaux de séniorité | Mesurer la part d'offres juniors |
| `dim_experience` | Catégories d'expérience minimale | Étudier les années demandées aux juniors |
| `dim_company` | Noms normalisés et clés des entreprises | Compter les offres par entreprise |
| `dim_date` | Année et mois de collecte | Suivre les volumes mensuels |
| `dim_plateforme` | Plateformes d'origine | Comparer les sources |
| `dim_technology` | Technologies et type d'exigence | Distinguer compétences requises et souhaitées |

### Pourquoi séparer séniorité et expérience ?

La séniorité et l'expérience minimale apportent deux informations différentes.

Une offre classée « Junior » peut demander zéro, un ou deux ans d'expérience. Les deux dimensions permettent donc de répondre à une question comme :

**Parmi les offres juniors, combien demandent déjà deux ans d'expérience ?**

## 5. Table de pont des technologies

### Pourquoi une table supplémentaire ?

Une offre peut demander plusieurs technologies, et une même technologie peut apparaître dans plusieurs offres. Il s'agit d'une relation **plusieurs-à-plusieurs**.

La table `bridge_offer_technology` représente cette relation en associant chaque offre à ses technologies et en précisant leur type d'exigence :

| offer_id | technology_id | requirement_type |
|---|---:|---|
| Offre A | 1 | required |
| Offre A | 2 | desired |
| Offre B | 1 | desired |

Si `1` correspond à Python et `2` à SQL :

- L'offre A exige Python et souhaite SQL.
- L'offre B souhaite Python.

**La table de pont est simplement la liste des technologies associées à chaque offre, avec leur caractère requis ou souhaité.** Elle ne crée pas un identifiant pour chaque combinaison de technologies.

### Technologies requises et souhaitées

La dimension `dim_technology` contient une seule entrée par technologie. Python conserve donc le même identifiant dans toutes les offres.

Le champ `requirement_type` appartient à la table de pont, car il décrit la relation entre une offre et une technologie :

- `required` : technologie requise.
- `desired` : technologie souhaitée.

La clé composée `(offer_id, technology_id, requirement_type)` évite les associations identiques tout en permettant de conserver une technologie dans les deux catégories pour une même offre.

### Comptage des offres par technologie

Après une jointure avec la table de pont, une offre peut apparaître sur plusieurs lignes. `COUNT(DISTINCT f.offer_id)` permet de compter les offres sans les multiplier.

Un filtre sur `requirement_type` permet de distinguer les technologies requises des technologies souhaitées. Sans ce filtre, le comptage couvre les deux catégories.

## 6. Construction avec Databricks SQL

Les scripts DDL définissent les tables et leurs relations :

| Script | Rôle |
|---|---|
| [`01_create_dim.sql`](../warehouse/ddl/01_create_dim.sql) | Création des dimensions |
| [`02_create_fact.sql`](../warehouse/ddl/02_create_fact.sql) | Création de la table de faits |
| [`03_create_bridge_offer_technology.sql`](../warehouse/ddl/03_create_bridge_offer_technology.sql) | Création de la table de pont |

L'alimentation du modèle suit les dépendances entre les tables :

1. Extraire les valeurs distinctes des données Silver pour alimenter les dimensions.
2. Associer chaque offre aux clés de ses dimensions pour alimenter `fact_offers`.
3. Décomposer les listes de technologies en associations pour alimenter `bridge_offer_technology`.

Les scripts d'alimentation sont regroupés dans [`warehouse/dml/`](../warehouse/dml/).

## 7. Contrôles de cohérence

Les contrôles à appliquer lors du chargement sont :

- Une ligne par `offer_id` dans la table de faits.
- Une clé unique par entrée de dimension.
- Une seule association par couple `(offer_id, technology_id)`.
- Aucune référence à une offre ou à une dimension inexistante.
- Un nombre d'offres cohérent entre les données Silver et la table de faits.

Ces contrôles permettent de préserver des comptages fiables lors des analyses SQL et de la construction des tableaux de bord Power BI.

La préparation des données en amont est décrite dans [Transformation et enrichissement des données](data_transformation.md).