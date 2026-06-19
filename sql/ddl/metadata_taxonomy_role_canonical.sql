-- =============================================================================
-- LMIP Metadata: Canonical Role Taxonomy
-- =============================================================================
-- Purpose: Master canonical role taxonomy for job title normalization and mapping
-- Source: Seeded from metadata/canonical_roles.csv
-- Layer: Metadata (governance and reference data)
-- =============================================================================

CREATE TABLE IF NOT EXISTS ${catalog}.metadata.taxonomy_role_canonical (
  role_key STRING NOT NULL COMMENT 'Unique canonical role identifier (e.g., ENG_SWE, DATA_DS)',
  canonical_role STRING NOT NULL COMMENT 'Standard role name (e.g., Software Engineer, Data Scientist)',
  family_key STRING NOT NULL COMMENT 'Parent role family key (FK to taxonomy_role_families)',
  sector_key STRING NOT NULL COMMENT 'Parent sector key (FK to taxonomy_sectors)',
  seniority STRING COMMENT 'Seniority level: junior, mid, senior, executive',
  aliases STRING COMMENT 'Pipe-delimited role aliases for fuzzy matching',
  created_at TIMESTAMP NOT NULL COMMENT 'Record creation timestamp',
  updated_at TIMESTAMP NOT NULL COMMENT 'Record last update timestamp'
)
USING DELTA
COMMENT 'Master canonical role taxonomy for job title normalization. Maps raw job titles to standardized canonical roles with seniority levels and sector/family classification.'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'quality.expectation.role_key_not_null' = 'role_key IS NOT NULL',
  'quality.expectation.canonical_role_not_null' = 'canonical_role IS NOT NULL',
  'quality.expectation.family_key_not_null' = 'family_key IS NOT NULL',
  'quality.expectation.sector_key_not_null' = 'sector_key IS NOT NULL',
  'lmip.layer' = 'metadata',
  'lmip.table_type' = 'taxonomy',
  'lmip.governance' = 'controlled',
  'lmip.seed_source' = 'metadata/canonical_roles.csv'
);
