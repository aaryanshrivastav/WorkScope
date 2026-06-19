-- ============================================================================
-- Table: workspace.intermediate.inter_job_role_map
-- Layer: INTERMEDIATE
-- Description: Job title to canonical role mapping for role standardization
-- ============================================================================
-- Purpose: Physical table definition for inter_job_role_map
-- Dependencies: workspace.silver.silver_jobs_current
-- Consumers: workspace.gold.dim_role
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.intermediate.inter_job_role_map (
  title_normalized STRING NOT NULL COMMENT 'Normalized job title',
  canonical_role_id STRING NOT NULL COMMENT 'Canonical role identifier',
  canonical_role_name STRING NOT NULL COMMENT 'Canonical role name',
  role_category STRING COMMENT 'Broad role category',
  role_level STRING COMMENT 'Seniority level',
  mapping_method STRING NOT NULL COMMENT 'How mapping was created',
  mapping_confidence DECIMAL(5,4) NOT NULL COMMENT 'Mapping confidence score',
  created_at TIMESTAMP NOT NULL COMMENT 'When mapping was created'

  -- PRIMARY KEY removed for Databricks Delta compatibility
  -- Uniqueness of title_normalized must be enforced through
  -- role-mapping pipeline validation and MERGE logic
)
USING DELTA
COMMENT 'Job title to canonical role mapping for role standardization'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);