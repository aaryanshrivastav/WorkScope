-- ============================================================================
-- Table: workspace.silver.silver_job_identity_map
-- Layer: SILVER
-- Description: Cross-source job identity linking. Maps duplicate jobs across
--              different data sources.
-- ============================================================================
-- Purpose: Physical table definition for silver_job_identity_map
-- Dependencies: workspace.silver.silver_jobs_current
-- Consumers: workspace.warehouse.dim_job
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.silver.silver_job_identity_map (
  job_identity_map_sk BIGINT NOT NULL COMMENT 'Surrogate key',
  job_id_1 STRING NOT NULL COMMENT 'First job ID',
  job_id_2 STRING NOT NULL COMMENT 'Second job ID (linked)',
  source_1 STRING NOT NULL COMMENT 'Source of job 1',
  source_2 STRING NOT NULL COMMENT 'Source of job 2',
  match_rule STRING NOT NULL COMMENT 'EXACT, FUZZY_COMPANY, COMPOSITE_HASH',
  match_score DECIMAL(5,4) NOT NULL COMMENT 'Match confidence 0-1',
  assigned_at TIMESTAMP NOT NULL COMMENT 'When linkage was created',
  batch_id STRING NOT NULL COMMENT 'Processing batch ID'

  -- PRIMARY KEY removed for Databricks Delta compatibility
  -- Uniqueness of job_identity_map_sk must be enforced
  -- through Silver-layer validation and merge logic
)
USING DELTA
COMMENT 'Cross-source job identity linking. Maps duplicate jobs across different data sources.'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);