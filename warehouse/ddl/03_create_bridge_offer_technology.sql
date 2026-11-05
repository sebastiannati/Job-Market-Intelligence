CREATE TABLE IF NOT EXISTS bridge_offer_technology (
    offer_id VARCHAR(255) NOT NULL,
    technology_id INT NOT NULL,
    requirement_type VARCHAR(30) NOT NULL,

    CONSTRAINT pk_offer_technology PRIMARY KEY (offer_id, technology_id),

    CONSTRAINT fk_offer FOREIGN KEY (offer_id) REFERENCES fact_offers(offer_id),

    CONSTRAINT fk_technology FOREIGN KEY (technology_id) REFERENCES dim_technology(technology_id)
);
ALTER TABLE workspace.default.bridge_offer_technology
SET TBLPROPERTIES ('delta.feature.catalogManaged' = 'supported');