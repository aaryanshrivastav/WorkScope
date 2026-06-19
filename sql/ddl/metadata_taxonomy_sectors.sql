-- =============================================================================
-- LMIP Metadata: Sector Taxonomy
-- =============================================================================
-- Purpose: Master sector taxonomy with hierarchical structure and NAICS mapping
-- Source: Seeded from metadata/sectors.csv
-- Layer: Metadata (governance and reference data)
-- =============================================================================

CREATE TABLE IF NOT EXISTS ${catalog}.metadata.taxonomy_sectors (
  sector_key STRING NOT NULL COMMENT 'Unique sector identifier (e.g., TECH, HOSP, HEAL)',
  sector_name STRING NOT NULL COMMENT 'Display name for the sector',
  parent_sector STRING COMMENT 'Parent sector key for hierarchical rollup (NULL for top-level)',
  naics_code STRING COMMENT 'NAICS industry classification code',
  keywords STRING COMMENT 'Pipe-delimited keywords for sector classification matching',
  created_at TIMESTAMP NOT NULL COMMENT 'Record creation timestamp',
  updated_at TIMESTAMP NOT NULL COMMENT 'Record last update timestamp'
)
USING DELTA
COMMENT 'Master sector taxonomy with hierarchical structure. Supports multi-sector labor market analysis with NAICS code mapping and keyword-based classification.'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'quality.expectation.sector_key_not_null' = 'sector_key IS NOT NULL',
  'quality.expectation.sector_name_not_null' = 'sector_name IS NOT NULL',
  'lmip.layer' = 'metadata',
  'lmip.table_type' = 'taxonomy',
  'lmip.governance' = 'controlled',
  'lmip.seed_source' = 'metadata/sectors.csv'
);
