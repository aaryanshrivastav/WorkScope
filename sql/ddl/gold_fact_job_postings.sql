-- ============================================================================
-- Table: workspace.gold.fact_job_postings
-- Layer: GOLD
-- Description: Core fact table for job posting events with foreign keys to all dimensions
-- ============================================================================
-- Purpose: Physical table definition for fact_job_postings
-- Dependencies: workspace.silver.silver_jobs_current, workspace.silver.silver_job_changes
-- Consumers: workspace.gold.gold_hiring_trends, workspace.gold.gold_location_trends
-- Expected Output: Table created with 14 columns
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.gold.fact_job_postings (
  fact_job_posting_sk BIGINT NOT NULL COMMENT 'Fact surrogate key',
  job_sk BIGINT NOT NULL COMMENT 'FK to dim_job (SCD2-aware)',
  company_sk BIGINT NOT NULL COMMENT 'FK to dim_company',
  location_sk BIGINT NOT NULL COMMENT 'FK to dim_location',
  role_sk BIGINT NOT NULL COMMENT 'FK to dim_role',
  sector_sk BIGINT NOT NULL COMMENT 'FK to dim_sector',
  source_sk BIGINT NOT NULL COMMENT 'FK to dim_source',
  posting_date_sk INT NOT NULL COMMENT 'FK to dim_date (YYYYMMDD)',
  posting_timestamp TIMESTAMP NOT NULL COMMENT 'Degenerate dimension: posting time',
  active_flag BOOLEAN NOT NULL COMMENT 'Currently active job',
  is_new_job BOOLEAN NOT NULL COMMENT 'First occurrence flag',
  is_update BOOLEAN NOT NULL COMMENT 'Update event flag',
  is_soft_delete BOOLEAN NOT NULL COMMENT 'Deletion event flag',
  is_restore BOOLEAN NOT NULL COMMENT 'Restoration event flag'
,
  PRIMARY KEY (fact_job_posting_sk)
)
COMMENT 'Core fact table for job posting events with foreign keys to all dimensions'
PARTITIONED BY (posting_timestamp)
USING DELTA
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);

-- End of DDL
