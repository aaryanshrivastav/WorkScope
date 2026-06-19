-- ============================================================================
-- Table: workspace.silver.silver_jobs_staging
-- Layer: SILVER
-- Description: Staging area for standardized jobs before CDC detection.
--              Temporary holding area for batch processing.
-- ============================================================================
-- Purpose: Physical table definition for silver_jobs_staging
-- Dependencies: workspace.bronze.bronze_job_snapshot
-- Consumers: workspace.silver.silver_jobs_current
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.silver.silver_jobs_staging (
  source_name STRING NOT NULL COMMENT 'Source system name',
  source_job_id STRING NOT NULL COMMENT 'Job ID from source system',
  source_job_key STRING NOT NULL COMMENT 'Composite key: source_name|source_job_id',
  company_name_raw STRING COMMENT 'Raw company name from source',
  company_name_norm STRING COMMENT 'Normalized company name',
  title_raw STRING COMMENT 'Raw job title from source',
  title_normalized STRING COMMENT 'Standardized job title',
  description_raw STRING COMMENT 'Raw job description',
  location_raw STRING COMMENT 'Raw location string',
  location_norm STRING COMMENT 'Normalized location',
  remote_type STRING COMMENT 'REMOTE, HYBRID, ONSITE',
  source_url STRING COMMENT 'Source URL for job posting',
  posted_at TIMESTAMP COMMENT 'Job posting timestamp',
  last_seen TIMESTAMP NOT NULL COMMENT 'Last observation timestamp',
  batch_id STRING NOT NULL COMMENT 'Processing batch ID',
  processed_at TIMESTAMP NOT NULL COMMENT 'Processing timestamp',
  record_hash STRING NOT NULL COMMENT 'Hash for change detection',
  is_active BOOLEAN NOT NULL COMMENT 'Active flag',
  soft_delete_flag BOOLEAN NOT NULL COMMENT 'Soft delete marker',
  soft_delete_reason STRING COMMENT 'Reason for soft delete'

  -- PRIMARY KEY removed for Databricks Delta compatibility
  -- Uniqueness of source_job_key must be enforced through
  -- staging validation and CDC processing logic
)
USING DELTA
COMMENT 'Staging area for standardized jobs before CDC detection. Temporary holding area for batch processing.'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);