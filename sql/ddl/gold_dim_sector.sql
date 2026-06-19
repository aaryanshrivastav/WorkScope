-- ============================================================================
-- Table: workspace.gold.dim_sector
-- Layer: GOLD
-- Description: Industry sector dimension with hierarchical taxonomy
-- ============================================================================
-- Purpose: Physical table definition for dim_sector
-- Dependencies: workspace.intermediate.inter_sector_map
-- Consumers: workspace.warehouse.dim_company, workspace.warehouse.dim_job
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.gold.dim_sector (
  sector_sk BIGINT NOT NULL COMMENT 'Surrogate key',
  sector_name STRING NOT NULL COMMENT 'Sector name',
  sector_category STRING COMMENT 'Parent sector category',
  sector_family STRING COMMENT 'Sector family grouping (e.g., HOSPITALITY, TECHNOLOGY)',
  sector_description STRING COMMENT 'Sector description',
  is_active BOOLEAN NOT NULL COMMENT 'Active flag',
  created_at TIMESTAMP NOT NULL COMMENT 'Creation timestamp'

  -- PRIMARY KEY removed for Databricks Delta compatibility
  -- Uniqueness of sector_sk must be enforced through
  -- dimension loading and validation processes
)
USING DELTA
COMMENT 'Industry sector dimension with hierarchical taxonomy'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);