CREATE TABLE IF NOT EXISTS dim_job_category(
    job_category_id INT NOT NULL,
    job_category VARCHAR(255) NOT NULL,
    CONSTRAINT pk_job_category PRIMARY KEY(job_category_id)
);

create table if not exists dim_company (
    company_name STRING Not NULL,
    company_key STRING NOT NULL,
    constraint pk_company PRIMARY KEY (company_key)
);

CREATE TABLE IF NOT EXISTS dim_date(
    mois_id int not null,
    annee int not null,
    mois int not null,
    CONSTRAINT pk_mois PRIMARY KEY (mois_id)
);

CREATE TABLE IF NOT EXISTS dim_experience(
    experience_id INT NOT NULL,
    experience_min STRING NOT NULL,
    CONSTRAINT pk_experience PRIMARY KEY (experience_id)
);

CREATE TABLE IF NOT EXISTS dim_plateforme (
    plateforme_id INT NOT NULL,
    plateforme_name VARCHAR(255) NOT NULL,
    CONSTRAINT plateforme_pk PRIMARY KEY (plateforme_id)
);

CREATE TABLE IF NOT EXISTS dim_seniority(
    seniority_id INT Not NULL,
    seniority_level VARCHAR(20) Not NULL,
    CONSTRAINT pk_seniority PRIMARY KEY (seniority_id)
);

CREATE TABLE IF NOT EXISTS dim_technology(
    technology_id INT NOT NULL,
    technology_name STRING NOT NULL,
    CONSTRAINT pk_technology PRIMARY KEY (technology_id)
);