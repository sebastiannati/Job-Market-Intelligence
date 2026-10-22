"""
Ce fichier contient les principales missions associées à chaque catégorie de métier.
Ces informations sont destinées à être intégrées aux prompts de classification des métiers.
"""

# Liste des missions par catégorie de job pour générer le prompt
MISSIONS_DA = [
    "Traduire un besoin métier en question d’analyse",
    "Extraire et combiner des données",
    "Interroger des bases de données",
    "Nettoyer et préparer des données",
    "Explorer un jeu de données",
    "Réaliser des analyses statistiques descriptives",
    "Définir et calculer des indicateurs",
    "Modéliser des données pour l’analyse",
    "Créer des tableaux de bord",
    "Visualiser des données",
    "Analyser des tendances et des écarts",
    "Segmenter des données",
    "Rechercher les causes d’un problème à partir des données",
    "Réaliser des tests statistiques",
    "Concevoir ou analyser des tests A/B",
    "Produire des prévisions simples",
    "Contrôler la qualité des données",
    "Automatiser des analyses et des rapports",
    "Interpréter et restituer des résultats",
    "Documenter les indicateurs et les règles de calcul",
]

MISSIONS_CONSULTANT = [
    "Recueillir et formaliser les besoins liés aux données",
    "Diagnostiquer la maturité data d’une organisation",
    "Traduire un problème métier en problème data ou IA",
    "Identifier des cas d’usage data et IA",
    "Prioriser les cas d’usage selon leur valeur et leur faisabilité",
    "Évaluer la disponibilité et la qualité des données",
    "Définir une stratégie data ou IA",
    "Définir une feuille de route data",
    "Concevoir une architecture de données cible",
    "Concevoir une solution d’analyse ou d’IA",
    "Rédiger des spécifications fonctionnelles et techniques",
    "Définir des règles de gouvernance des données",
    "Définir des contrôles de qualité des données",
    "Évaluer des solutions et plateformes data",
    "Concevoir et cadrer une preuve de concept",
    "Intégrer une solution data ou IA dans un système existant",
    "Cadrer et suivre la mise en œuvre d’un projet data",
    "Évaluer la conformité et les risques liés aux données et à l’IA",
    "Évaluer les performances d’une solution data ou IA",
    "Mesurer la valeur produite par une solution data ou IA",
]

MISSIONS_DE = [
    "Collecter des données depuis différentes sources",
    "Ingérer des données en traitement par lots",
    "Ingérer des données en flux continu",
    "Concevoir des traitements ETL ou ELT",
    "Transformer et structurer des données",
    "Concevoir des pipelines de données",
    "Orchestrer des traitements de données",
    "Concevoir des modèles pour entrepôts de données",
    "Concevoir des architectures lakehouse ou data lake",
    "Traiter des données distribuées à grande échelle",
    "Optimiser des requêtes et traitements de données",
    "Développer des solutions de traitement de données",
    "Intégrer des API et des sources de données",
    "Tester des pipelines et traitements",
    "Contrôler la qualité des données",
    "Gérer les métadonnées, la traçabilité et la lignée des données",
    "Sécuriser les accès aux données",
    "Déployer et surveiller des pipelines",
    "Diagnostiquer les incidents de traitement de données",
    "Optimiser la performance et le coût des traitements",
]

MISSIONS_DS = [
    "Transformer un problème métier ou scientifique en problème d’analyse",
    "Collecter et préparer des données pour la modélisation",
    "Explorer des jeux de données",
    "Appliquer des méthodes statistiques et probabilistes",
    "Construire des variables explicatives",
    "Entraîner des modèles de classification",
    "Entraîner des modèles de régression",
    "Réaliser des analyses de clustering",
    "Construire des modèles de séries temporelles",
    "Concevoir des expériences et tests",
    "Réaliser des analyses causales",
    "Analyser des données textuelles",
    "Analyser des images ou des données visuelles",
    "Construire des systèmes de recommandation ou de classement",
    "Sélectionner et entraîner des modèles",
    "Évaluer et valider des modèles",
    "Interpréter les résultats d’un modèle",
    "Quantifier l’incertitude des prédictions",
    "Présenter des résultats et recommandations fondés sur les données",
    "Évaluer les biais et limites d’une analyse ou d’un modèle",
]

MISSIONS_MLE = [
    "Concevoir l’architecture d’un système de machine learning ou d’IA",
    "Préparer les données pour l’entraînement et l’inférence",
    "Construire des pipelines de données et de variables pour les modèles",
    "Entraîner ou affiner des modèles",
    "Suivre les expériences et les versions de modèles",
    "Évaluer la qualité des modèles",
    "Déployer des modèles en production",
    "Exposer des modèles via des API",
    "Intégrer des modèles dans des applications",
    "Automatiser l’entraînement et le déploiement des modèles",
    "Surveiller les performances et la dérive des modèles",
    "Optimiser la latence, le débit et le coût d’inférence",
    "Adapter les modèles à une exécution distribuée ou à grande échelle",
    "Mettre en œuvre des systèmes de recherche sémantique",
    "Concevoir des applications fondées sur la génération augmentée par recherche",
    "Concevoir et évaluer des instructions pour des modèles génératifs",
    "Tester la qualité et la sécurité des systèmes d’IA générative",
    "Mettre en place des garde-fous pour les systèmes d’IA",
    "Assurer la reproductibilité et les tests des systèmes de modèles",
    "Gérer le cycle de vie des modèles en production",
]

MISSIONS_AUTRE = [
    # Gestion de produit et de projet
    "Piloter la stratégie, la roadmap et le cycle de vie d’un produit numérique ou data",
    "Définir et prioriser un backlog, rédiger des user stories et arbitrer les fonctionnalités d’un produit",
    "Coordonner un projet informatique ou data principalement sur les délais, budgets, ressources et livrables",

    # Management et gouvernance des données
    "Encadrer une équipe ou un département data principalement sur des responsabilités managériales et organisationnelles",
    "Administrer les référentiels, catalogues et règles de gouvernance des données sans concevoir principalement des solutions analytiques ou techniques",
    "Piloter la qualité, la conformité et la gestion opérationnelle des données sans développer principalement de traitements ou de modèles",
    "Assurer la gestion, la maintenance et l’administration fonctionnelle de bases de données ou de systèmes d’information",

    # Développement logiciel hors Data / IA
    "Développer des applications web frontend ou fullstack sans responsabilité principale liée aux pipelines, analyses ou modèles de données",
    "Développer des applications backend, des API ou des microservices sans responsabilité principale liée aux systèmes de données ou d’IA",
    "Concevoir et maintenir des applications mobiles, des logiciels embarqués ou des applications métier",

    # Infrastructure, cloud et cybersécurité
    "Administrer des systèmes, serveurs, réseaux et infrastructures informatiques",
    "Concevoir et exploiter des infrastructures cloud, des processus DevOps ou des plateformes Kubernetes sans spécialisation principale Data ou MLOps",
    "Assurer la cybersécurité, la détection des intrusions, la gestion des vulnérabilités ou la réponse aux incidents",
    "Réaliser des audits de sécurité informatique, des tests d’intrusion ou des activités de conformité cybersécurité",

    # Autres métiers techniques
    "Tester et valider des applications logicielles principalement dans une démarche d’assurance qualité logicielle",
    "Assurer le support informatique, l’assistance technique et la résolution des incidents utilisateurs",

    # Fonctions métier utilisant des données
    "Piloter des campagnes marketing, CRM ou commerciales principalement sur des objectifs opérationnels plutôt que sur l’analyse de données",
    "Réaliser des activités de finance, comptabilité, contrôle de gestion ou audit principalement métier, même avec des outils de reporting",
    "Concevoir des interfaces, des parcours utilisateurs ou des expériences UX/UI à partir de données d’usage",

    # Métiers scientifiques et industriels
    "Conduire des activités de recherche, d’ingénierie industrielle ou d’expertise scientifique dont la finalité principale n’est pas l’analyse de données ou le développement de systèmes d’IA",
]
