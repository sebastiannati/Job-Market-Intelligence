import pandas as pd

TECH_ALIASES = {
    # ========================================
    # BI / Reporting / Bureautique
    # ========================================
    "powerbi": "Power BI",
    "power bi": "Power BI",
    "excel": "Excel",
    "excel avancé": "Excel",
    "microsoft excel": "Excel",
    "powerpoint": "PowerPoint",
    "microsoft powerpoint": "PowerPoint",
    "office": "Microsoft Office",
    "microsoft office": "Microsoft Office",
    "tableau": "Tableau",
    "looker": "Looker",
    "looker studio": "Looker Studio",
    "google data studio": "Looker Studio",
    "metabase": "Metabase",
    "microstrategy": "MicroStrategy",
    "zendesk explore": "Zendesk Explore",

    # ========================================
    # Cloud / Services Cloud
    # ========================================
    "aws": "AWS",
    "amazon web services": "AWS",
    "azure": "Microsoft Azure",
    "microsoft azure": "Microsoft Azure",
    "gcp": "Google Cloud Platform",
    "google cloud": "Google Cloud Platform",
    "google cloud platform": "Google Cloud Platform",
    "sagemaker": "Amazon SageMaker",
    "aws sagemaker": "Amazon SageMaker",
    "amazon sagemaker": "Amazon SageMaker",
    "aws bedrock": "Amazon Bedrock",
    "amazon bedrock": "Amazon Bedrock",
    "azure ml": "Azure Machine Learning",
    "azure machine learning": "Azure Machine Learning",
    "vertex ai": "Vertex AI",
    "gcp vertex ai": "Vertex AI",
    "google vertex ai": "Vertex AI",
    "bigquery": "BigQuery",
    "google bigquery": "BigQuery",
    "azure stream analytics": "Azure Stream Analytics",
    "azure log analytics": "Azure Log Analytics",
    "ibm cloud": "IBM Cloud",
    "dataflow": "Dataflow",

    # ========================================
    # Langages / Développement
    # ========================================
    "python": "Python",
    "sql": "SQL",
    "r": "R",
    "java": "Java",
    "scala": "Scala",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "c#": "C#",
    "c++": "C++",
    "vba": "VBA",
    "shell unix": "Unix Shell",
    "unix shell": "Unix Shell",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "react": "React",
    "reactjs": "React",
    "angular": "Angular",
    "fastapi": "FastAPI",

    # ========================================
    # Data Engineering / Big Data
    # ========================================
    "spark": "Apache Spark",
    "apache spark": "Apache Spark",
    "pyspark": "PySpark",
    "hadoop": "Hadoop",
    "apache hadoop": "Hadoop",
    "sqoop": "Apache Sqoop",
    "apache sqoop": "Apache Sqoop",
    "airflow": "Apache Airflow",
    "apache airflow": "Apache Airflow",
    "dbt": "dbt",
    "dataform": "Dataform",
    "snowflake": "Snowflake",
    "databricks": "Databricks",
    "dataiku": "Dataiku",
    "delta lake": "Delta Lake",
    "talend": "Talend",
    "informatica": "Informatica",
    "ssis": "SSIS",
    "control-m": "Control-M",

    # ========================================
    # Bases de données / Moteurs
    # ========================================
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "oracle": "Oracle",
    "oracle database": "Oracle",
    "teradata": "Teradata",
    "elasticsearch": "Elasticsearch",
    "chromadb": "ChromaDB",
    "faiss": "FAISS",
    "mongodb": "MongoDB",
    "mysql": "MySQL",

    # ========================================
    # Machine Learning / IA
    # ========================================
    "scikit learn": "scikit-learn",
    "scikit-learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "tensorflow": "TensorFlow",
    "pytorch": "PyTorch",
    "huggingface": "Hugging Face",
    "hugging face": "Hugging Face",
    "langchain": "LangChain",
    "langgraph": "LangGraph",
    "mlflow": "MLflow",
    "agno": "Agno",
    "numpy": "NumPy",
    "pandas": "pandas",
    "seaborn": "Seaborn",
    "matplotlib": "Matplotlib",
    "plotly": "Plotly",
    "streamlit": "Streamlit",
    "dash": "Dash",
    "xgboost": "XGBoost",
    "ragas": "Ragas",
    "deepeval": "DeepEval",
    "tensorboard": "TensorBoard",
    "tensorrt": "TensorRT",

    # ========================================
    # DevOps / Infrastructure / Code
    # ========================================
    "docker": "Docker",
    "docker compose": "Docker Compose",
    "kubernetes": "Kubernetes",
    "terraform": "Terraform",
    "terragrunt": "Terragrunt",
    "bicep": "Bicep",
    "jenkins": "Jenkins",
    "git": "Git",
    "github": "GitHub",
    "github actions": "GitHub Actions",
    "gitlab": "GitLab",
    "azure devops": "Azure DevOps",
    "grafana": "Grafana",
    "argo cd": "Argo CD",
    "argocd": "Argo CD",
    "postman": "Postman",
    "cursor": "Cursor",
    "claude code": "Claude Code",

    # ========================================
    # Gouvernance / Qualité des données
    # ========================================
    "collibra": "Collibra",
    "atlan": "Atlan",
    "unity catalog": "Unity Catalog",
    "great expectations": "Great Expectations",
    "soda": "Soda",
    "datahub": "DataHub",

    # ========================================
    # Logiciels métier / Entreprise
    # ========================================
    "sas": "SAS",
    "alteryx": "Alteryx",
    "unica": "Unica",
    "adobe campaign": "Adobe Campaign",
    "zendesk": "Zendesk",
    "jira": "Jira",
    "confluence": "Confluence",
    "miro": "Miro",
    "aveva braincube": "AVEVA Braincube",
    "aveva connect": "AVEVA Connect",
    "aveva teamwork": "AVEVA Teamwork",
    "aveva advanced analytics": "AVEVA Advanced Analytics",
    "aveva system platform": "AVEVA System Platform",

    # ========================================
    # Protocoles / Standards
    # ========================================
    "api rest": "REST",
    "rest api": "REST",
    "rest": "REST",
    "graphql": "GraphQL",
    "openapi": "OpenAPI",
    "oauth": "OAuth",
    "mcp": "MCP",
    "mcp serveur": "MCP",
}

EXCLUDED = {
    # ========================================
    # Concepts Data / IA
    # ========================================
    "machine learning",
    "deep learning",
    "generative ai",
    "generative ia",
    "genai",
    "ia générative",
    "llm",
    "vlm",
    "nlp",
    "rag",
    "mlops",
    "devops",
    "dataops",
    "etl",
    "elt",
    "etl/elt",
    "ci/cd",
    "data lake",
    "data warehouse",
    "datawarehouse",
    "lakehouse",
    "mdm",
    "esb",
    "feature store",
    "data governance",
    "data visualization",
    "data visualisation",
    "dataviz",
    "data manipulation",
    "data management",
    "orchestration",
    "monitoring",
    "fine-tuning",
    "pipelines",
    "data quality",

    # ========================================
    # Familles génériques de technologies
    # ========================================
    "cloud",
    "infrastructures cloud",
    "cloud computing",
    "api",
    "api management",
    "api back-end",
    "base de données",
    "bases de données",
    "base sql",
    "bases vectorielles",
    "vector databases",
    "nosql",
    "outils bi",
    "outils de bi",
    "outils de big data",
    "outils de restitution",
    "outils d'orchestration",
    "data visualization tools",
    "frameworks ia",
    "frameworks de deep learning",
    "librairies spécialisées nlp",
    "compétences front-end",
    "large datasets / event-based data",

    # ========================================
    # Compétences / Activités générales
    # ========================================
    "cybersecurity",
    "automated testing",
    "data-driven content (reports, blog posts, etc.)",
    "connaissance des environnements digitaux",
    "connaissance finance de marché / assurance",
    "analyse statistique",
    "gestion de projet",
    "développement d'api",
    "agile",
    "scrum",
    "kanban",

    # ========================================
    # Réglementations / Référentiels
    # ========================================
    "rgpd",
    "gdpr",
    "gdpr compliance",
    "data act",
    "ai act",
    "itil",
    "sla",
    "itil/sla",
    "dcam",
    "dama",

    # ========================================
    # Certifications / Qualifications
    # ========================================
    "pspo",
    "certifications cloud",
    "anglais",
}

# Extraction methods
EXTRACTION_ENTITIES = [
    "global_extraction_prompt",
    "job_classifier_prompt",
    "stack_extraction_prompt",
    "seniority_classifier",
]

def to_set(value):

    if isinstance(value, list):
        outils = value
    elif isinstance(value, str):
        outils = value.split(";")
    elif pd.isna(value):
        return set()
    else:
        return set()

    return {outil.strip().lower() for outil in outils if outil.strip()}


def clean_stack(tools):
    return {
        TECH_ALIASES.get(t.strip().casefold(), t.strip())
        for t in tools
        if isinstance(t, str)
        and t.strip().casefold() not in EXCLUDED
        and t.strip()
    }
    
def eval_stack(y_true, y_pred):
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