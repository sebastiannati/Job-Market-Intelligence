# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
# MAGIC %md
# MAGIC # Notebook de construction de la couche Gold de Azure DataLake Storage Gen2 vers Azure SQL

# COMMAND ----------

# MAGIC %md
# MAGIC ## Import des données depuis le Datalake

# COMMAND ----------

scraping_month = "2026-04"
month = scraping_month[5:]
year = scraping_month[:4]

months = {"01":"Janvier", "02":"Février", "03":"Mars", "04":"Avril", "05":"Mai", "06":"Juin", "07":"Juillet", "08":"Août", "09":"Septembre", "10":"Octobre", "11":"Novembre", "12":"Décembre"}

silver_path = f"abfss://joboffers@jobmarketstorage.dfs.core.windows.net/{year}/{months.get(month)}/job_offers.parquet"
print(silver_path)

df = spark.read.parquet(silver_path)

silver_table = "jobmarketdatabricks.silver.job_offers"

spark.sql("CREATE SCHEMA IF NOT EXISTS jobmarketdatabricks.silver")

df_silver = spark.read.parquet(silver_path)

if not df_silver.take(1):
    raise ValueError(f"Parquet vide : {silver_path}")

df_silver.write.format("delta").mode("overwrite").saveAsTable(silver_table)

# COMMAND ----------

spark.sql("USE CATALOG jobmarketdatabricks")
spark.sql("USE SCHEMA gold")

# COMMAND ----------

from pathlib import Path

spark_sql_dir = Path("/Workspace/Users/sebastian.nati.02@gmail.com/Job-Market-Intelligence/warehouse/databricks/sql")

def run_sql_file(path: Path):
    text = path.read_text(encoding="utf-8")
    for stmt in text.split(";"):
        # retire les lignes de commentaires pour détecter les blocs vides
        code = "\n".join(
            l for l in stmt.splitlines() if not l.strip().startswith("--")
        ).strip()
        if not code:
            continue
        print(f"[{path.name}] {code[:70]!r}")
        spark.sql(code)   # une erreur arrête tout le notebook

def run_files(sql_dir: Path) -> None:
    if not sql_dir.is_dir():
        raise NotADirectoryError(f"Dossier SQL introuvable : {sql_dir}")

    sql_files = sorted((path for path in sql_dir.glob("*.sql") if path.is_file()),key=lambda path: path.name,)

    if not sql_files:
        raise FileNotFoundError(f"Aucun fichier .sql dans {sql_dir}")

    for path in sql_files:
        run_sql_file(path)

# COMMAND ----------

print("Création et chargement des dimensions, de la table de faits et de la table de pont dans le Gold :")
run_files(spark_sql_dir)

# COMMAND ----------

gold_schema = "jobmarketdatabricks.gold"
sql_host = "sql-gold-job-market.database.windows.net"
sql_database = "job-market-gold-free"

credentials = {
    "user": dbutils.secrets.get("job-market", "azure-sql-user"),
    "password": dbutils.secrets.get("job-market","azure-sql-password"),
}

jdbc_read_options = {
    **credentials,
    "url": (
        f"jdbc:sqlserver://{sql_host}:1433;"
        f"databaseName={sql_database};"
        "encrypt=true;trustServerCertificate=false;"
    ),
    "driver": "com.microsoft.sqlserver.jdbc.SQLServerDriver",
}

sqlserver_write_options = {
    **credentials,
    "host": sql_host,
    "port": "1433",
    "database": sql_database,
    "authentication": "SqlPassword",
    "encrypt": "true",
    "trustServerCertificate": "false",
    "numPartitions": "1",
}

tables = [
    "dim_company",
    "dim_date",
    "dim_experience",
    "dim_job_category",
    "dim_platform",
    "dim_seniority",
    "dim_technology",
    "fact_offers",
    "bridge_offer_technology",
]


def read_azure_sql(query: str):
    return (
        spark.read.format("jdbc")
        .options(**jdbc_read_options)
        .option("query", query)
        .load()
    )


def azure_row_count(table_name: str) -> int:
    return read_azure_sql(
        f"SELECT COUNT_BIG(*) AS row_count FROM dbo.{table_name}"
    ).first()["row_count"]


# 1. Tester la connexion avant de lire les tables cibles.
print(f"Test de connexion à Azure SQL ({sql_database})")
read_azure_sql("SELECT 1 AS connexion_ok").show()

# 2. Vérifier que toutes les tables cibles sont vides.
non_empty = []
for table_name in tables:
    print(f"Vérification de dbo.{table_name}")
    if azure_row_count(table_name) > 0:
        non_empty.append(table_name)

if non_empty:
    raise ValueError(
        "Le chargement initial exige des tables Azure SQL vides. "
        f"Tables déjà remplies : {', '.join(non_empty)}"
    )

# 3. Copier les dimensions, puis les faits et la table de pont.
for table_name in tables:
    source = spark.table(f"{gold_schema}.{table_name}")
    target = f"dbo.{table_name}"
    expected_count = source.count()

    print(f"Copie de {expected_count} lignes vers {target}")

    (
        source.write.format("sqlserver")
        .options(**sqlserver_write_options)
        .option("dbtable", target)
        .mode("append")
        .save()
    )

    actual_count = azure_row_count(table_name)
    if actual_count != expected_count:
        raise RuntimeError(
            f"{target} : {actual_count} lignes copiées, "
            f"{expected_count} attendues."
        )

    print(f"{target} : {actual_count} lignes vérifiées")

print("Chargement initial terminé.")