-- ============================================================================
-- Table: workspace.gold.dim_skill
-- Layer: GOLD
-- Description: Skill dimension with canonical skill taxonomy
-- ============================================================================
-- Purpose: Physical table definition for dim_skill
-- Dependencies: workspace.intermediate.inter_skill_catalog
-- Consumers: workspace.warehouse.bridge_job_skill
-- Expected Output: Table created with 8 columns
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.gold.dim_skill (
  skill_sk BIGINT NOT NULL COMMENT 'Surrogate key',
  skill_id STRING NOT NULL COMMENT 'Skill identifier',
  skill_name STRING NOT NULL COMMENT 'Canonical skill name',
  skill_category STRING COMMENT 'Skill category',
  skill_type STRING COMMENT 'Technical, Soft, Domain',
  skill_description STRING COMMENT 'Skill description',
  is_active BOOLEAN NOT NULL COMMENT 'Active flag',
  created_at TIMESTAMP NOT NULL COMMENT 'Creation timestamp'
,
  PRIMARY KEY (skill_sk)
)
COMMENT 'Skill dimension with canonical skill taxonomy'
USING DELTA
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);

-- End of DDL
