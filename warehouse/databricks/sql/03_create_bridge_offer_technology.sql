CREATE TABLE IF NOT EXISTS jobmarketdatabricks.gold.bridge_offer_technology (
    offer_id VARCHAR(255) NOT NULL,
    technology_id BIGINT NOT NULL,
    requirement_type VARCHAR(30) NOT NULL,

    CONSTRAINT pk_offer_technology
        PRIMARY KEY (offer_id, technology_id, requirement_type),

    CONSTRAINT fk_offer 
        FOREIGN KEY (offer_id)
        REFERENCES jobmarketdatabricks.gold.fact_offers(offer_id),

    CONSTRAINT fk_technology
        FOREIGN KEY (technology_id)
        REFERENCES jobmarketdatabricks.gold.dim_technology(technology_id)
)

TBLPROPERTIES ('delta.feature.catalogManaged' = 'supported');

ALTER TABLE jobmarketdatabricks.gold.bridge_offer_technology
DROP CONSTRAINT IF EXISTS chk_requirement_type;

ALTER TABLE jobmarketdatabricks.gold.bridge_offer_technology
ADD CONSTRAINT chk_requirement_type
CHECK (requirement_type IN ('required', 'desired'));

-- Vues pour récupérer les offres et les technos desired et required

CREATE OR REPLACE VIEW jobmarketdatabricks.gold.v_offer_technology_source AS

SELECT
    offer_id,
    EXPLODE(required_technologies) AS technology_name, -- Ne produit pas de NULL dans Spark
    'required' AS requirement_type
FROM jobmarketdatabricks.silver.job_offers

UNION ALL

SELECT
    offer_id,
    EXPLODE(desired_technologies) AS technology_name,
    'desired' AS requirement_type
FROM jobmarketdatabricks.silver.job_offers;