-- 1. Entreprises
BEGIN TRANSACTION;

MERGE INTO jobmarketdatabricks.gold.dim_company AS target
USING (
    SELECT
        company_key,
        MIN(company_name) AS company_name
    FROM jobmarketdatabricks.silver.job_offers
    GROUP BY company_key
) AS source
ON target.company_key = source.company_key

WHEN NOT MATCHED THEN
    INSERT (company_key, company_name)
    VALUES (source.company_key, source.company_name);

COMMIT;


-- 2. Dates
BEGIN TRANSACTION;

MERGE INTO jobmarketdatabricks.gold.dim_date AS target
USING (
    SELECT DISTINCT
        CAST(REPLACE(scraping_month, '-', '') AS INT) AS mois_id,
        CAST(SUBSTRING(scraping_month, 1, 4) AS INT) AS annee,
        CAST(SUBSTRING(scraping_month, 6, 2) AS INT) AS mois
    FROM jobmarketdatabricks.silver.job_offers
    WHERE scraping_month IS NOT NULL
) AS source
ON target.mois_id = source.mois_id

WHEN NOT MATCHED THEN
    INSERT (mois_id, annee, mois)
    VALUES (source.mois_id, source.annee, source.mois);

COMMIT;


-- 3. Catégories d’expérience
BEGIN TRANSACTION;

MERGE INTO jobmarketdatabricks.gold.dim_experience AS target
USING (
    SELECT DISTINCT
        CASE
            WHEN experience_category IN ('5', '5+') THEN '5+'
            ELSE experience_category
        END AS experience_min
    FROM jobmarketdatabricks.silver.job_offers
    WHERE experience_category IS NOT NULL
) AS source
ON target.experience_min = source.experience_min

WHEN NOT MATCHED THEN
    INSERT (experience_min)
    VALUES (source.experience_min);

COMMIT;


-- 4. Catégories de postes
BEGIN TRANSACTION;

MERGE INTO jobmarketdatabricks.gold.dim_job_category AS target
USING (
    SELECT DISTINCT job_category
    FROM jobmarketdatabricks.silver.job_offers
    WHERE job_category IS NOT NULL
) AS source
ON target.job_category = source.job_category

WHEN NOT MATCHED THEN
    INSERT (job_category)
    VALUES (source.job_category);

COMMIT;


-- 5. Plateformes
BEGIN TRANSACTION;

MERGE INTO jobmarketdatabricks.gold.dim_platform AS target
USING (
    SELECT DISTINCT platform_name
    FROM jobmarketdatabricks.silver.job_offers
    WHERE platform_name IS NOT NULL
) AS source
ON target.platform_name = source.platform_name

WHEN NOT MATCHED THEN
    INSERT (platform_name)
    VALUES (source.platform_name);

COMMIT;

-- 6. Seniorité

BEGIN TRANSACTION;

MERGE INTO jobmarketdatabricks.gold.dim_seniority as target
USING(
    SELECT DISTINCT seniority_level
    FROM jobmarketdatabricks.silver.job_offers
) AS source

ON target.seniority_level = source.seniority_level

WHEN NOT MATCHED
    THEN INSERT (seniority_level)
    VALUES (source.seniority_level);

COMMIT;

-- 7. Stack technique
BEGIN TRANSACTION;

MERGE INTO jobmarketdatabricks.gold.dim_technology AS target
USING (
    SELECT DISTINCT technology_name
    FROM (
        SELECT EXPLODE(all_technologies) AS technology_name
        FROM jobmarketdatabricks.silver.job_offers
    ) AS technologies
    WHERE technology_name IS NOT NULL
      AND TRIM(technology_name) <> ''
) AS source

ON target.technology_name = source.technology_name

WHEN NOT MATCHED THEN
    INSERT (technology_name)
    VALUES (source.technology_name);

COMMIT;