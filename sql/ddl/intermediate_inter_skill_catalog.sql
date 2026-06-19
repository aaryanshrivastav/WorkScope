-- ============================================================================
-- Table: workspace.intermediate.inter_skill_catalog
-- Layer: INTERMEDIATE
-- Description: Canonical skill catalog with taxonomy and metadata
-- ============================================================================
-- Purpose: Physical table definition for inter_skill_catalog
-- Dependencies: workspace.silver.silver_skill_mapping
-- Consumers: workspace.gold.dim_skill
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.intermediate.inter_skill_catalog (
  skill_id STRING NOT NULL COMMENT 'Unique skill identifier',
  skill_name_canonical STRING NOT NULL COMMENT 'Canonical skill name',
  skill_category STRING COMMENT 'Skill category',
  skill_type STRING COMMENT 'Technical, Soft, Domain',
  skill_description STRING COMMENT 'Skill description',
  skill_aliases ARRAY<STRING> COMMENT 'Alternative skill names',
  is_active BOOLEAN NOT NULL COMMENT 'Active flag',
  created_at TIMESTAMP NOT NULL COMMENT 'Creation timestamp'

  -- PRIMARY KEY removed for Databricks Delta compatibility
  -- Uniqueness of skill_id must be enforced through
  -- taxonomy governance and pipeline validation
)
USING DELTA
COMMENT 'Canonical skill catalog with taxonomy and metadata'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);