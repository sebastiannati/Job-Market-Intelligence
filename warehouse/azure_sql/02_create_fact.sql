IF OBJECT_ID(N'dbo.fact_offers', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.fact_offers (
        offer_id NVARCHAR(255) NOT NULL,
        seniority_id BIGINT NOT NULL,
        experience_id BIGINT NOT NULL,
        company_id NVARCHAR(255) NOT NULL,
        mois_id INT NOT NULL,
        job_category_id BIGINT NOT NULL,
        platform_id BIGINT NOT NULL,

        CONSTRAINT pk_fact_offers PRIMARY KEY (offer_id),

        CONSTRAINT fk_seniority FOREIGN KEY (seniority_id)
            REFERENCES dbo.dim_seniority(seniority_id),

        CONSTRAINT fk_experience FOREIGN KEY (experience_id)
            REFERENCES dbo.dim_experience(experience_id),

        CONSTRAINT fk_company FOREIGN KEY (company_id)
            REFERENCES dbo.dim_company(company_key),

        CONSTRAINT fk_mois FOREIGN KEY (mois_id)
            REFERENCES dbo.dim_date(mois_id),

        CONSTRAINT fk_job_category FOREIGN KEY (job_category_id)
            REFERENCES dbo.dim_job_category(job_category_id),

        CONSTRAINT fk_platform FOREIGN KEY (platform_id)
            REFERENCES dbo.dim_platform(platform_id)
    );
END;
