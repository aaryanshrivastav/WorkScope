-- ============================================================================
-- Table: workspace.reporting.reporting_pipeline_health
-- Layer: REPORTING
-- Description: Data pipeline health metrics and monitoring dashboard data
-- ============================================================================
-- Purpose: Physical table definition for gold_pipeline_health
-- Dependencies: workspace.gold.fact_pipeline_runs, workspace.gold.fact_job_lifecycle
-- Expected Output: Table created with 9 columns
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.reporting.reporting_pipeline_health (
  health_date_sk INT NOT NULL COMMENT 'Date key',
  pipeline_name STRING NOT NULL COMMENT 'Pipeline identifier',
  total_runs BIGINT COMMENT 'Total pipeline runs',
  successful_runs BIGINT COMMENT 'Successful runs',
  failed_runs BIGINT COMMENT 'Failed runs',
  avg_duration_seconds DECIMAL(10,2) COMMENT 'Average run duration',
  total_records_processed BIGINT COMMENT 'Total records processed',
  success_rate DECIMAL(5,4) COMMENT 'Success rate %',
  updated_at TIMESTAMP NOT NULL COMMENT 'Last refresh'
,
  PRIMARY KEY (health_date_sk, pipeline_name)
)
COMMENT 'Data pipeline health metrics and monitoring dashboard data'
USING DELTA
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);

-- End of DDL
