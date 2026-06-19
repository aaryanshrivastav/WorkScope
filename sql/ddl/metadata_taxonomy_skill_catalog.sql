-- =============================================================================
-- LMIP Metadata: Skill Catalog Taxonomy
-- =============================================================================
-- Purpose: Master skill taxonomy for skill extraction and canonicalization
-- Source: Seeded from metadata/canonical_skills.csv
-- Layer: Metadata (governance and reference data)
-- =============================================================================

CREATE TABLE IF NOT EXISTS ${catalog}.metadata.taxonomy_skill_catalog (
  skill_key STRING NOT NULL COMMENT 'Unique skill identifier (e.g., TECH_PYTHON, HOSP_REV_MGT)',
  canonical_skill STRING NOT NULL COMMENT 'Standard skill name (e.g., Python, Revenue Management)',
  skill_category STRING NOT NULL COMMENT 'Skill category: Technical, Operations, Clinical, Finance, Soft Skill',
  sector_key STRING COMMENT 'Primary sector key (NULL for cross-sector soft skills)',
  aliases STRING COMMENT 'Pipe-delimited skill aliases for fuzzy matching',
  created_at TIMESTAMP NOT NULL COMMENT 'Record creation timestamp',
  updated_at TIMESTAMP NOT NULL COMMENT 'Record last update timestamp'
)
USING DELTA
COMMENT 'Master skill taxonomy for skill extraction and canonicalization. Maps raw skill mentions to standardized skill names with sector and category classification.'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'quality.expectation.skill_key_not_null' = 'skill_key IS NOT NULL',
  'quality.expectation.canonical_skill_not_null' = 'canonical_skill IS NOT NULL',
  'quality.expectation.skill_category_not_null' = 'skill_category IS NOT NULL',
  'lmip.layer' = 'metadata',
  'lmip.table_type' = 'taxonomy',
  'lmip.governance' = 'controlled',
  'lmip.seed_source' = 'metadata/canonical_skills.csv'
);
