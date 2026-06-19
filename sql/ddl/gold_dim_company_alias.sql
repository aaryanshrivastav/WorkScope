-- ============================================================================
-- Table: workspace.gold.dim_company_alias
-- Layer: GOLD
-- Description: Company name aliases for resolving variations to canonical companies
-- ============================================================================
-- Purpose: Physical table definition for dim_company_alias
-- Dependencies: workspace.intermediate.inter_company_canonical
-- Consumers: workspace.gold.dim_job
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.gold.dim_company_alias (
  company_alias_sk BIGINT NOT NULL COMMENT 'Surrogate key',
  company_sk BIGINT NOT NULL COMMENT 'FK to dim_company',
  alias_name STRING NOT NULL COMMENT 'Company name variation',
  alias_type STRING COMMENT 'LEGAL, TRADE, ABBREVIATION',
  is_primary BOOLEAN NOT NULL COMMENT 'Primary name flag',
  created_at TIMESTAMP NOT NULL COMMENT 'Creation timestamp'

  -- PRIMARY KEY removed for Databricks Delta compatibility
  -- Uniqueness of company_alias_sk must be enforced through
  -- dimensional loading and validation processes

  -- Foreign key relationships are not enforced by Delta Lake
  -- Referential integrity must be validated during ETL/ELT processing
)
USING DELTA
COMMENT 'Company name aliases for resolving variations to canonical companies'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);