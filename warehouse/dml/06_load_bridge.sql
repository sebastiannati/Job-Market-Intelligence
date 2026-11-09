MERGE INTO jobmarketdatabricks.gold.bridge_offer_technology AS target
USING (
    SELECT DISTINCT
        job.offer_id,
        tech.technology_id,
        job.requirement_type
    FROM jobmarketdatabricks.gold.v_offer_technology_source AS job

    -- Récupère l'id de la stack
    INNER JOIN jobmarketdatabricks.gold.dim_technology as tech
        ON job.technology_name = tech.technology_name
    
    -- Récupère l'id de l'offre
    INNER JOIN jobmarketdatabricks.gold.fact_offers as fact
        ON fact.offer_id = job.offer_id
) AS source

ON target.offer_id = source.offer_id
    AND target.technology_id = source.technology_id
    AND target.requirement_type = source.requirement_type

WHEN NOT MATCHED THEN
    INSERT (offer_id, technology_id, requirement_type)
    VALUES (
        source.offer_id,
        source.technology_id,
        source.requirement_type
    );