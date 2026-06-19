-- =============================================================================
-- LMIP Metadata: Role Family Taxonomy
-- =============================================================================
-- Purpose: Role family groupings within sectors for role classification
-- Source: Seeded from metadata/role_families.csv
-- Layer: Metadata (governance and reference data)
-- =============================================================================

CREATE TABLE IF NOT EXISTS ${catalog}.metadata.taxonomy_role_families (
  family_key STRING NOT NULL COMMENT 'Unique role family identifier (e.g., ENG, DATA, HOSP_OPS)',
  family_name STRING NOT NULL COMMENT 'Display name for the role family',
  sector_key STRING NOT NULL COMMENT 'Parent sector key (FK to taxonomy_sectors)',
  description STRING COMMENT 'Role family description and scope',
  created_at TIMESTAMP NOT NULL COMMENT 'Record creation timestamp',
  updated_at TIMESTAMP NOT NULL COMMENT 'Record last update timestamp'
)
USING DELTA
COMMENT 'Role family taxonomy providing intermediate grouping between sectors and canonical roles. Enables hierarchical role classification and reporting.'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'quality.expectation.family_key_not_null' = 'family_key IS NOT NULL',
  'quality.expectation.family_name_not_null' = 'family_name IS NOT NULL',
  'quality.expectation.sector_key_not_null' = 'sector_key IS NOT NULL',
  'lmip.layer' = 'metadata',
  'lmip.table_type' = 'taxonomy',
  'lmip.governance' = 'controlled',
  'lmip.seed_source' = 'metadata/role_families.csv'
);
