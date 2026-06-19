-- ============================================================================
-- Table: workspace.gold.fact_job_lifecycle
-- Layer: GOLD
-- Description: Job lifecycle metrics tracking job duration, change frequency,
--              and lifecycle events
-- ============================================================================
-- Purpose: Physical table definition for fact_job_lifecycle
-- Dependencies: workspace.silver.silver_jobs_current,
--               workspace.silver.silver_job_changes
-- Consumers: workspace.gold.gold_pipeline_health
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.gold.fact_job_lifecycle (
  fact_job_lifecycle_sk BIGINT NOT NULL COMMENT 'Fact surrogate key',
  job_sk BIGINT NOT NULL COMMENT 'FK to dim_job',
  company_sk BIGINT NOT NULL COMMENT 'FK to dim_company',
  role_sk BIGINT NOT NULL COMMENT 'FK to dim_role',
  first_seen_date_sk INT NOT NULL COMMENT 'FK to dim_date (first seen)',
  last_seen_date_sk INT NOT NULL COMMENT 'FK to dim_date (last seen)',
  days_active INT COMMENT 'Total days job was active',
  update_count INT COMMENT 'Number of updates',
  soft_delete_count INT COMMENT 'Number of soft deletes',
  restore_count INT COMMENT 'Number of restorations',
  is_currently_active BOOLEAN NOT NULL COMMENT 'Current active status'

  -- PRIMARY KEY removed for Databricks Delta compatibility
  -- Uniqueness of fact_job_lifecycle_sk must be enforced through
  -- fact loading and validation processes

  -- Foreign key relationships are not enforced by Delta Lake
  -- Referential integrity must be validated during ETL/ELT processing
)
USING DELTA
COMMENT 'Job lifecycle metrics tracking job duration, change frequency, and lifecycle events'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);