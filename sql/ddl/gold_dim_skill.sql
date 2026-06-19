-- ============================================================================
-- Table: workspace.gold.dim_skill
-- Layer: GOLD
-- Description: Skill dimension with canonical skill taxonomy
-- ============================================================================
-- Purpose: Physical table definition for dim_skill with taxonomy integration
-- Dependencies: workspace.metadata.taxonomy_skill_catalog
-- Consumers: workspace.gold.bridge_job_skill
-- Expected Output: Table created with 10 columns including taxonomy references
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.gold.dim_skill (
  skill_sk BIGINT NOT NULL COMMENT 'Surrogate key',
  skill_key STRING NOT NULL COMMENT 'Natural key from taxonomy (e.g., TECH_PYTHON, HOSP_REV_MGT)',
  canonical_skill STRING NOT NULL COMMENT 'Canonical skill name',
  skill_category STRING COMMENT 'Skill category (Technical|Operations|Clinical|Finance|Soft Skill)',
  sector_key STRING COMMENT 'Sector key (NULL for cross-sector soft skills)',
  skill_description STRING COMMENT 'Skill description',
  is_active BOOLEAN NOT NULL COMMENT 'Active flag',
  created_at TIMESTAMP NOT NULL COMMENT 'Record creation timestamp',
  updated_at TIMESTAMP COMMENT 'Last update timestamp',
  taxonomy_updated_at TIMESTAMP COMMENT 'Last taxonomy sync timestamp'
,
  PRIMARY KEY (skill_sk)
)
USING DELTA
COMMENT 'Skill dimension with canonical skill taxonomy'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);