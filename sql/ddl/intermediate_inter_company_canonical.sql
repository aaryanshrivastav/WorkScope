-- ============================================================================
-- Table: workspace.intermediate.inter_company_canonical
-- Layer: INTERMEDIATE
-- Description: Canonical company name mapping. Links company name variations to canonical names.
-- ============================================================================
-- Purpose: Physical table definition for inter_company_canonical
-- Dependencies: workspace.silver.silver_jobs_current
-- Consumers: workspace.gold.dim_company
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.intermediate.inter_company_canonical (
  company_name_norm STRING NOT NULL COMMENT 'Normalized company name variant',
  canonical_company_name STRING NOT NULL COMMENT 'Canonical company name',
  company_match_method STRING NOT NULL COMMENT 'Matching algorithm used',
  company_match_confidence DECIMAL(5,4) NOT NULL COMMENT 'Match confidence score',
  active_flag BOOLEAN NOT NULL COMMENT 'Active company flag',
  assigned_at TIMESTAMP NOT NULL COMMENT 'When mapping was created'

  -- PRIMARY KEY removed for Databricks Delta compatibility
  -- Uniqueness of company_name_norm must be enforced through
  -- matching pipeline validation and MERGE logic
)
USING DELTA
COMMENT 'Canonical company name mapping. Links company name variations to canonical names.'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);