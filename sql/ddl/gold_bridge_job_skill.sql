-- ============================================================================
-- Table: workspace.gold.bridge_job_skill
-- Layer: GOLD
-- Description: Bridge table linking jobs to skills (many-to-many relationship)
-- ============================================================================
-- Purpose: Physical table definition for bridge_job_skill
-- Dependencies: workspace.intermediate.inter_job_skill_evidence
-- Consumers: workspace.gold.gold_skill_demand,
--            workspace.gold.gold_hospitality_skills
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.gold.bridge_job_skill (
  job_skill_bridge_sk BIGINT NOT NULL COMMENT 'Bridge surrogate key',
  job_sk BIGINT NOT NULL COMMENT 'FK to dim_job',
  skill_sk BIGINT NOT NULL COMMENT 'FK to dim_skill',
  skill_importance STRING COMMENT 'REQUIRED, PREFERRED, NICE_TO_HAVE',
  extraction_confidence DECIMAL(5,4) NOT NULL COMMENT 'Extraction confidence score',
  created_at TIMESTAMP NOT NULL COMMENT 'Creation timestamp'

  -- PRIMARY KEY removed for Databricks Delta compatibility
  -- Uniqueness of job_skill_bridge_sk must be enforced through
  -- dimensional loading and bridge-table validation processes

  -- Foreign key relationships are not enforced by Delta Lake
  -- Referential integrity must be validated during ETL/ELT processing
)
USING DELTA
COMMENT 'Bridge table linking jobs to skills (many-to-many relationship)'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);