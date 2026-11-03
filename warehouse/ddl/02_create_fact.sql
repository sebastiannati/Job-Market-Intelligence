CREATE TABLE IF NOT EXISTS fact_offers(
    offer_id VARCHAR(255) NOT NULL,
    seniority_id INT NOT NULL,
    experience_id INT NOT NULL,
    company_id VARCHAR(255) NOT NULL,
    mois_id INT NOT NULL,
    job_category_id INT NOT NULL,
    plateforme_id INT NOT NULL,

    CONSTRAINT pk_fact_offers PRIMARY KEY (offer_id),

    CONSTRAINT fk_seniority FOREIGN KEY (seniority_id) REFERENCES dim_seniority(seniority_id),

    CONSTRAINT fk_experience FOREIGN KEY (experience_id) REFERENCES dim_experience(experience_id),

    CONSTRAINT fk_company FOREIGN KEY (company_id) REFERENCES dim_company(company_key),

    CONSTRAINT fk_mois FOREIGN KEY (mois_id) REFERENCES dim_date(mois_id),

    CONSTRAINT fk_job_category FOREIGN KEY (job_category_id) REFERENCES dim_job_category(job_category_id),

    CONSTRAINT fk_plateforme FOREIGN KEY (plateforme_id) REFERENCES dim_plateforme(plateforme_id)
);