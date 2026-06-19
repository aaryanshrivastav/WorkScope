-- ============================================================================
-- Table: workspace.gold.fact_pipeline_runs
-- Layer: GOLD
-- Description: Pipeline execution metrics for monitoring and data quality
-- ============================================================================
-- Purpose: Physical table definition for fact_pipeline_runs
-- Dependencies: workspace.audit.audit_pipeline_runs
-- Consumers: workspace.gold.gold_pipeline_health
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.gold.fact_pipeline_runs (
  fact_pipeline_run_sk BIGINT NOT NULL COMMENT 'Fact surrogate key',
  run_id STRING NOT NULL COMMENT 'Pipeline run identifier',
  pipeline_name STRING NOT NULL COMMENT 'Pipeline name',
  run_date_sk INT NOT NULL COMMENT 'FK to dim_date',
  run_timestamp TIMESTAMP NOT NULL COMMENT 'Run start timestamp',
  run_duration_seconds INT COMMENT 'Total run duration',
  records_processed BIGINT COMMENT 'Records processed',
  records_inserted BIGINT COMMENT 'Records inserted',
  records_updated BIGINT COMMENT 'Records updated',
  records_failed BIGINT COMMENT 'Records failed',
  status STRING NOT NULL COMMENT 'SUCCESS, FAILED, PARTIAL',

  -- Databricks partition column
  run_date DATE NOT NULL COMMENT 'Derived partition date from run_timestamp'

  -- PRIMARY KEY removed for Databricks Delta compatibility
  -- Uniqueness of fact_pipeline_run_sk must be enforced through
  -- pipeline loading and validation processes
)
USING DELTA
PARTITIONED BY (run_date)
COMMENT 'Pipeline execution metrics for monitoring and data quality'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);