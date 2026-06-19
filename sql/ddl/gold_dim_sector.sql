-- ============================================================================
-- Table: workspace.gold.dim_sector
-- Layer: GOLD
-- Description: Industry sector dimension with hierarchical taxonomy
-- ============================================================================
-- Purpose: Physical table definition for dim_sector with taxonomy integration
-- Dependencies: workspace.metadata.taxonomy_sectors
-- Consumers: workspace.gold.dim_company, workspace.gold.dim_job, workspace.gold.dim_role
-- Expected Output: Table created with 12 columns including taxonomy references
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.gold.dim_sector (
  sector_sk BIGINT NOT NULL COMMENT 'Surrogate key',
  sector_key STRING NOT NULL COMMENT 'Natural key from taxonomy (e.g., TECH, HOSP, HEAL)',
  sector_name STRING NOT NULL COMMENT 'Sector display name',
  parent_sector_sk BIGINT COMMENT 'FK to parent sector (NULL for top-level sectors)',
  parent_sector_key STRING COMMENT 'Parent sector natural key from taxonomy',
  naics_code STRING COMMENT 'NAICS classification code',
  sector_level INT COMMENT 'Hierarchy depth (1 = top-level, 2 = sub-sector, etc.)',
  sector_description STRING COMMENT 'Sector description',
  is_active BOOLEAN NOT NULL COMMENT 'Active flag',
  created_at TIMESTAMP NOT NULL COMMENT 'Record creation timestamp',
  updated_at TIMESTAMP COMMENT 'Last update timestamp',
  taxonomy_updated_at TIMESTAMP COMMENT 'Last taxonomy sync timestamp'
,
  PRIMARY KEY (sector_sk)
)
COMMENT 'Industry sector dimension with hierarchical taxonomy - synced from workspace.metadata.taxonomy_sectors'
USING DELTA
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);

-- End of DDL
