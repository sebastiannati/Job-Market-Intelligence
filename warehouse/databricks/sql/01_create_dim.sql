CREATE TABLE IF NOT EXISTS jobmarketdatabricks.gold.dim_job_category(
    job_category_id BIGINT GENERATED ALWAYS AS IDENTITY,
    job_category VARCHAR(255) NOT NULL,
    CONSTRAINT pk_job_category PRIMARY KEY(job_category_id)
)
TBLPROPERTIES('delta.feature.catalogManaged' = 'supported');

create table if not exists jobmarketdatabricks.gold.dim_company (
    company_name STRING Not NULL,
    company_key STRING NOT NULL,
    constraint pk_company PRIMARY KEY (company_key)
)
TBLPROPERTIES('delta.feature.catalogManaged' = 'supported');

CREATE TABLE IF NOT EXISTS jobmarketdatabricks.gold.dim_date(
    mois_id int not null,
    annee int not null,
    mois int not null,
    CONSTRAINT pk_mois PRIMARY KEY (mois_id)
)
TBLPROPERTIES('delta.feature.catalogManaged' = 'supported');

CREATE TABLE IF NOT EXISTS jobmarketdatabricks.gold.dim_experience (
    experience_id BIGINT GENERATED ALWAYS AS IDENTITY,
    experience_min STRING NOT NULL,
    CONSTRAINT pk_experience PRIMARY KEY (experience_id)
)
TBLPROPERTIES('delta.feature.catalogManaged' = 'supported');

CREATE TABLE IF NOT EXISTS jobmarketdatabricks.gold.dim_platform (
    platform_id  BIGINT GENERATED ALWAYS AS IDENTITY,
    platform_name VARCHAR(255) NOT NULL,
    CONSTRAINT platform_pk PRIMARY KEY (platform_id)
)
TBLPROPERTIES('delta.feature.catalogManaged' = 'supported');

CREATE TABLE IF NOT EXISTS jobmarketdatabricks.gold.dim_seniority(
    seniority_id BIGINT GENERATED ALWAYS AS IDENTITY,
    seniority_level VARCHAR(20) Not NULL,
    CONSTRAINT pk_seniority PRIMARY KEY (seniority_id)
)
TBLPROPERTIES('delta.feature.catalogManaged' = 'supported');

CREATE TABLE IF NOT EXISTS jobmarketdatabricks.gold.dim_technology(
    technology_id BIGINT GENERATED ALWAYS AS IDENTITY,
    technology_name STRING NOT NULL,
    CONSTRAINT pk_technology PRIMARY KEY (technology_id)
)
TBLPROPERTIES('delta.feature.catalogManaged' = 'supported');