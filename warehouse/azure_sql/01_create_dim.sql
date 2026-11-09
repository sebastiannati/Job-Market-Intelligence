IF OBJECT_ID(N'dbo.dim_job_category', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.dim_job_category (
        job_category_id BIGINT NOT NULL,
        job_category NVARCHAR(255) NOT NULL,
        CONSTRAINT pk_job_category PRIMARY KEY(job_category_id)
    );
END;

IF OBJECT_ID(N'dbo.dim_company', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.dim_company (
        company_name NVARCHAR(255) Not NULL,
        company_key NVARCHAR(255) NOT NULL,
        constraint pk_company PRIMARY KEY (company_key)
    );
END;

IF OBJECT_ID(N'dbo.dim_date', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.dim_date (
        mois_id int not null,
        annee int not null,
        mois int not null,
        CONSTRAINT pk_mois PRIMARY KEY (mois_id)
    );
END;

IF OBJECT_ID(N'dbo.dim_experience', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.dim_experience (
        experience_id BIGINT NOT NULL,
        experience_min NVARCHAR(255) NOT NULL,
        CONSTRAINT pk_experience PRIMARY KEY (experience_id)
    );
END;

IF OBJECT_ID(N'dbo.dim_platform', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.dim_platform (
        platform_id  BIGINT NOT NULL,
        platform_name NVARCHAR(255) NOT NULL,
        CONSTRAINT platform_pk PRIMARY KEY (platform_id)
    );
END;

IF OBJECT_ID(N'dbo.dim_seniority', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.dim_seniority (
        seniority_id BIGINT NOT NULL,
        seniority_level NVARCHAR(20) Not NULL,
        CONSTRAINT pk_seniority PRIMARY KEY (seniority_id)
    );
END;

IF OBJECT_ID(N'dbo.dim_technology', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.dim_technology (
        technology_id BIGINT NOT NULL,
        technology_name NVARCHAR(255) NOT NULL,
        CONSTRAINT pk_technology PRIMARY KEY (technology_id)
    );
END;
