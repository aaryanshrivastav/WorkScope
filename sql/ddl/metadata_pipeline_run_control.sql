-- ============================================================================
-- Table: workspace.metadata.pipeline_run_control
-- Layer: METADATA
-- Description: Pipeline execution control and orchestration metadata
-- ============================================================================
-- Purpose: Physical table definition for pipeline_run_control
-- Dependencies: None
-- Consumers: workspace.audit.audit_pipeline_runs
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.metadata.pipeline_run_control (
  run_control_sk BIGINT NOT NULL COMMENT 'Surrogate key',
  pipeline_name STRING NOT NULL COMMENT 'Name of the pipeline',
  batch_id STRING NOT NULL COMMENT 'Unique batch identifier',
  source_name STRING COMMENT 'Source being processed',
  trigger_type STRING NOT NULL COMMENT 'Trigger type: SCHEDULED, MANUAL, EVENT',
  scheduled_at TIMESTAMP COMMENT 'Scheduled execution time',
  started_at TIMESTAMP COMMENT 'Actual start time',
  ended_at TIMESTAMP COMMENT 'Completion time',
  status STRING NOT NULL COMMENT 'Execution status: PENDING, RUNNING, SUCCESS, FAILED',
  operator_user STRING COMMENT 'User who triggered manual runs'

  -- PRIMARY KEY removed for Databricks Delta compatibility
  -- Enforced through orchestration and metadata validation pipelines

  -- UNIQUE constraint removed for Databricks Delta compatibility
  -- batch_id uniqueness must be enforced before MERGE/INSERT operations

  -- CHECK constraints removed for Databricks Delta compatibility
  -- Enforced through orchestration and data quality validation rules
)
USING DELTA
COMMENT 'Pipeline execution control and orchestration metadata'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);