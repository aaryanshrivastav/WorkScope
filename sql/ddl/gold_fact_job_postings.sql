-- ============================================================================
-- Table: workspace.gold.fact_job_postings
-- Layer: GOLD
-- Description: Core fact table for job posting events with foreign keys to all dimensions
-- ============================================================================
-- Purpose: Physical table definition for fact_job_postings
-- Dependencies: workspace.silver.silver_jobs_current,
--               workspace.silver.silver_job_changes
-- Consumers: workspace.gold.gold_hiring_trends,
--            workspace.gold.gold_location_trends
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
  is_restore BOOLEAN NOT NULL COMMENT 'Restoration event flag',

  -- Databricks partition column
  posting_date DATE NOT NULL COMMENT 'Derived partition date from posting_timestamp'

  -- PRIMARY KEY removed for Databricks Delta compatibility
  -- Uniqueness of fact_job_posting_sk must be enforced through
  -- fact loading and validation processes

  -- Foreign key relationships are not enforced by Delta Lake
  -- Referential integrity must be validated during ETL/ELT processing
)
USING DELTA
PARTITIONED BY (posting_date)
COMMENT 'Core fact table for job posting events with foreign keys to all dimensions'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);