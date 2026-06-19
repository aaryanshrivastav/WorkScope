-- ============================================================================
-- Table: workspace.gold.dim_source
-- Layer: GOLD
-- Description: Data source dimension tracking job posting sources
-- ============================================================================
-- Purpose: Physical table definition for dim_source
-- Dependencies: workspace.silver.silver_jobs_current
-- Consumers: workspace.gold.fact_job_postings
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.gold.dim_source (
  source_sk BIGINT NOT NULL COMMENT 'Surrogate key',
  source_name STRING NOT NULL COMMENT 'Source system name',
  source_type STRING COMMENT 'API, SCRAPER, FEED',
  source_url STRING COMMENT 'Source base URL',
  source_description STRING COMMENT 'Source description',
  is_active BOOLEAN NOT NULL COMMENT 'Active source flag',
  created_at TIMESTAMP NOT NULL COMMENT 'Creation timestamp'

  -- PRIMARY KEY removed for Databricks Delta compatibility
  -- Uniqueness of source_sk must be enforced through
  -- dimension loading and validation processes
)
USING DELTA
COMMENT 'Data source dimension tracking job posting sources'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);