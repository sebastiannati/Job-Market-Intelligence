BEGIN TRANSACTION;

MERGE INTO jobmarketdatabricks.gold.fact_offers as target 
USING (
    SELECT 
        job.offer_id,
        dates.mois_id,
        seniority.seniority_id,
        experience.experience_id,
        category.job_category_id,
        platform.platform_id,
        company.company_key AS company_id
    
    FROM jobmarketdatabricks.gold.job_offers_silver AS job

    LEFT JOIN jobmarketdatabricks.gold.dim_date as dates 
        ON CAST(REPLACE(job.scraping_month,'-','') AS INT) = dates.mois_id
    
    LEFT JOIN jobmarketdatabricks.gold.dim_seniority as seniority
        ON job.seniority_level = seniority.seniority_level
    
    -- on doit refaire la transformation 
    LEFT JOIN jobmarketdatabricks.gold.dim_experience as experience
        ON ( 
            CASE WHEN job.experience_category IN ('5','5+') 
                THEN '5+'
                ELSE job.experience_category
            END
        ) = experience.experience_min

    LEFT JOIN jobmarketdatabricks.gold.dim_job_category as category
        ON job.job_category = category.job_category
    
    LEFT JOIN jobmarketdatabricks.gold.dim_platform as platform
        ON job.platform_name = platform.platform_name
    
    LEFT JOIN jobmarketdatabricks.gold.dim_company as company
        ON job.company_key = company.company_key

) AS source

ON target.offer_id = source.offer_id

WHEN NOT MATCHED THEN 
    INSERT(
        offer_id,
        seniority_id,
        experience_id,
        company_id,
        mois_id,
        job_category_id,
        platform_id
    )
    VALUES(
        source.offer_id,
        source.seniority_id,
        source.experience_id,
        source.company_id,
        source.mois_id,
        source.job_category_id,
        source.platform_id
    );

COMMIT;