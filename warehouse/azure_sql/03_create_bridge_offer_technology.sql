IF OBJECT_ID(N'dbo.bridge_offer_technology', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.bridge_offer_technology (
        offer_id NVARCHAR(255) NOT NULL,
        technology_id BIGINT NOT NULL,
        requirement_type NVARCHAR(30) NOT NULL,

        CONSTRAINT pk_offer_technology
            PRIMARY KEY (offer_id, technology_id, requirement_type),

        CONSTRAINT fk_offer
            FOREIGN KEY (offer_id)
            REFERENCES dbo.fact_offers(offer_id),

        CONSTRAINT fk_technology
            FOREIGN KEY (technology_id)
            REFERENCES dbo.dim_technology(technology_id),

        CONSTRAINT chk_requirement_type
            CHECK (requirement_type IN ('required', 'desired'))
    );
END;
