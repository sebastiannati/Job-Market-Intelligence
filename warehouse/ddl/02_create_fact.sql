CREATE TABLE IF NOT EXISTS workspace.default.fact_offers (
    offer_id VARCHAR(255) NOT NULL,
    seniority_id BIGINT NOT NULL,
    experience_id BIGINT NOT NULL,
    company_id VARCHAR(255) NOT NULL,
    mois_id INT NOT NULL,
    job_category_id BIGINT NOT NULL,
    platform_id BIGINT NOT NULL,

    CONSTRAINT pk_fact_offers PRIMARY KEY (offer_id),

    CONSTRAINT fk_seniority FOREIGN KEY (seniority_id)
        REFERENCES workspace.default.dim_seniority(seniority_id),

    CONSTRAINT fk_experience FOREIGN KEY (experience_id)
        REFERENCES workspace.default.dim_experience(experience_id),

    CONSTRAINT fk_company FOREIGN KEY (company_id)
        REFERENCES workspace.default.dim_company(company_key),

    CONSTRAINT fk_mois FOREIGN KEY (mois_id)
        REFERENCES workspace.default.dim_date(mois_id),

    CONSTRAINT fk_job_category FOREIGN KEY (job_category_id)
        REFERENCES workspace.default.dim_job_category(job_category_id),

    CONSTRAINT fk_platform FOREIGN KEY (platform_id)
        REFERENCES workspace.default.dim_platform(platform_id)
)
TBLPROPERTIES ('delta.feature.catalogManaged' = 'supported');