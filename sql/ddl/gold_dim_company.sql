-- ============================================================================
-- Table: workspace.gold.dim_company
-- Layer: GOLD
-- Description: Company dimension with canonical company names and attributes (SCD Type 1)
-- ============================================================================
-- Purpose: Physical table definition for dim_company
-- Dependencies: workspace.intermediate.inter_company_canonical, workspace.intermediate.inter_company_map
-- Consumers: workspace.gold.dim_job, workspace.gold.fact_job_postings
-- Expected Output: Table created with 10 columns
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.gold.dim_company (
  company_sk BIGINT NOT NULL COMMENT 'Surrogate key',
  company_name STRING NOT NULL COMMENT 'Display company name',
  company_name_canonical STRING NOT NULL COMMENT 'Canonical name (business key)',
  company_match_method STRING COMMENT 'Method used for canonicalization',
  match_confidence DECIMAL(5,4) COMMENT 'Canonicalization confidence',
  alias_count INT COMMENT 'Number of name variations',
  sector_sk BIGINT COMMENT 'FK to dim_sector',
  sector_name STRING COMMENT 'Sector name (denormalized)',
  is_active BOOLEAN NOT NULL COMMENT 'Active flag',
  updated_at TIMESTAMP NOT NULL COMMENT 'Last update timestamp'
,
  PRIMARY KEY (company_sk)
)
COMMENT 'Company dimension with canonical company names and attributes (SCD Type 1)'
USING DELTA
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);

-- End of DDL
