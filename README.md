# Job-Market-Intelligence

Ce projet propose une analyse approfondie de l'état du marché de l'emploi en **Data & IA** au mois d'avril 2026. 

Dans un second temps, il implémente un système **RAG (Retrieval-Augmented Generation)** alimenté par mes expériences, projets et cursus. Cet assistant sert à la fois d'outil d'aide à la rédaction (CV, lettres de motivation) et de support pour répondre précisément aux questions des recruteurs sur mon parcours et mes compétences.

---

## Récolte des données

La collecte repose sur un scraper sur mesure, inspiré de l'architecture et du fonctionnement développés lors de mon stage de fin d'études. 

Les données ont été récoltées sur plusieurs plateformes majeures (**LinkedIn, Indeed, France Travail, StationF et HelloWork**). Le dataset consolidé regroupe **2 472 offres d'emploi** et intègre les informations clés suivantes :

| Champ | Description |
| :--- | :--- |
| `entreprise` | Nom de l'entreprise qui recrute |
| `poste` | Intitulé du poste |
| `description` | Descriptif complet de l'offre | 
| `location` | Localisation géographique | 
| `date_de_publication` | Date de publication de l'annonce |
| `experience` | Niveau d'expérience requis (brut) | 
| `nb_candidats` | Nombre de candidats (si indiqué) | 
| `profil_recherche` | Détails sur le profil recherché | 

--- 

## Nettoyage et traitement des données

Les données étant brutes, certaines peuvent manquer et d'autres prendre des formes variées. Par exemple :
* **Expérience :** Les données sur l'expérience requise combinent des indications d'années d'expérience et des descriptions textuelles nécessitant une analyse des compétences attendues.
* **Date de publication :** Le format est hétérogène et peut correspondre soit à une date classique, soit à une phrase relative (ex: "il y a 3 jours", "publié hier").

Enfin, d'autres informations clés doivent être extraites de ces offres, notamment **la stack technique** (langages, frameworks, outils cloud, etc.).

Pour transformer ce corpus brut en un jeu de données exploitable pour l'analyse, plusieurs étapes de traitement ont été mises en place :

1. **Nettoyage et normalisation textuelle :**
   * Standardisation des dates de publication pour unifier les formats.

2. **Extraction et classification intelligente par LLM local (via Ollama) :**
   * Utilisation d'un modèle local tournant sur GPU (RX 6900 XT) pour classifier automatiquement le niveau de séniorité requis selon 4 catégories : **Stage/Alternance, Jeune diplômé(0), Junior(0-2 ans), Intermédiaire (2-5 ans) et Senior(5+ ans)**. Cette classification croise intelligemment le titre du poste, l'expérience brute et la description.
   * Identification automatisée des compétences clés, des langages de programmation, des frameworks et des outils cloud (ex: Python, SQL, Azure, Docker, etc.) mentionnés dans les offres.
   * **Évaluation des performances :** Test et validation des performances du modèle en comparant ses prédictions à un corpus d'offres labellisé à la main pour garantir la fiabilité de la classification.

3. **Consolidation finale :**
   * Fusion des données nettoyées et enrichies dans un format unifié (`.parquet` / `.csv`) prêt à alimenter la brique d'analyse du marché de l'emploi.