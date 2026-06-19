-- ============================================================================
-- Table: workspace.intermediate.inter_company_map
-- Layer: INTERMEDIATE
-- Description: Company to sector mapping and company enrichment data
-- ============================================================================
-- Purpose: Physical table definition for inter_company_map
-- Dependencies: workspace.intermediate.inter_company_canonical
-- Consumers: workspace.gold.dim_company
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.intermediate.inter_company_map (
  canonical_company_name STRING NOT NULL COMMENT 'Canonical company name',
  sector_name STRING COMMENT 'Assigned sector',
  sector_assignment_method STRING COMMENT 'How sector was assigned',
  sector_confidence DECIMAL(5,4) COMMENT 'Sector assignment confidence',
  updated_at TIMESTAMP NOT NULL COMMENT 'Last update timestamp'

  -- PRIMARY KEY removed for Databricks Delta compatibility
  -- Uniqueness of canonical_company_name must be enforced
  -- through enrichment pipeline validation and MERGE logic
)
USING DELTA
COMMENT 'Company to sector mapping and company enrichment data'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);