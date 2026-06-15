-- ============================================================================
-- Table: workspace.intermediate.inter_sector_map
-- Layer: INTERMEDIATE
-- Description: Sector taxonomy and hierarchical sector mapping
-- ============================================================================
-- Purpose: Physical table definition for inter_sector_map
-- Dependencies: None (source table)
-- Consumers: workspace.gold.dim_sector
-- Expected Output: Table created with 5 columns
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.intermediate.inter_sector_map (
  sector_name STRING NOT NULL COMMENT 'Sector name',
  sector_category STRING COMMENT 'Broader sector category',
  sector_description STRING COMMENT 'Sector description',
  is_active BOOLEAN NOT NULL COMMENT 'Active sector flag',
  created_at TIMESTAMP NOT NULL COMMENT 'Creation timestamp'
,
  PRIMARY KEY (sector_name)
)
COMMENT 'Sector taxonomy and hierarchical sector mapping'
USING DELTA
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);

-- End of DDL
