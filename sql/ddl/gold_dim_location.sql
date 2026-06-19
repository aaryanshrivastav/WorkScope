-- ============================================================================
-- Table: workspace.gold.dim_location
-- Layer: GOLD
-- Description: Location dimension with geographic hierarchy
-- ============================================================================
-- Purpose: Physical table definition for dim_location
-- Dependencies: workspace.silver.silver_jobs_current
-- Consumers: workspace.gold.dim_job, workspace.gold.fact_job_postings
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.gold.dim_location (
  location_sk BIGINT NOT NULL COMMENT 'Surrogate key',
  location_name STRING NOT NULL COMMENT 'Full location string',
  city STRING COMMENT 'City name',
  state_province STRING COMMENT 'State or province',
  country STRING COMMENT 'Country name',
  country_code STRING COMMENT 'ISO country code',
  region STRING COMMENT 'Geographic region',
  latitude DECIMAL(10,7) COMMENT 'Latitude coordinate',
  longitude DECIMAL(10,7) COMMENT 'Longitude coordinate',
  is_remote BOOLEAN NOT NULL COMMENT 'Remote location flag',
  created_at TIMESTAMP NOT NULL COMMENT 'Creation timestamp'

  -- PRIMARY KEY removed for Databricks Delta compatibility
  -- Uniqueness of location_sk must be enforced through
  -- dimensional loading and validation processes
)
USING DELTA
COMMENT 'Location dimension with geographic hierarchy'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);