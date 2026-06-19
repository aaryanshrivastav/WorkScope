-- ============================================================================
-- Table: workspace.bronze.bronze_job_snapshot
-- Layer: BRONZE
-- Description: Immutable snapshots of Bronze ingestion job executions.
--              Captures job metadata for audit trail.
-- ============================================================================
-- Purpose: Physical table definition for bronze_job_snapshot
-- Dependencies: None (source table)
-- Consumers: workspace.audit.audit_pipeline_runs
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.bronze.bronze_job_snapshot (
  snapshot_id STRING NOT NULL COMMENT 'Unique snapshot identifier',
  job_id STRING NOT NULL COMMENT 'Job identifier',
  job_name STRING COMMENT 'Job name',
  batch_id STRING NOT NULL COMMENT 'Batch processing identifier',
  run_id STRING COMMENT 'Job run identifier',
  status STRING NOT NULL COMMENT 'Job status: running, success, failed, partial',
  config_json STRING COMMENT 'Job configuration as JSON',
  snapshot_timestamp TIMESTAMP NOT NULL COMMENT 'When snapshot was taken',
  ingestion_timestamp TIMESTAMP NOT NULL COMMENT 'When record was ingested',

  -- Partition column required to avoid high-cardinality TIMESTAMP partitioning
  ingestion_date DATE NOT NULL COMMENT 'Derived partition date from ingestion_timestamp'

  -- PRIMARY KEY removed for Databricks Delta compatibility
  -- Enforced through ingestion and reconciliation pipelines
)
USING DELTA
PARTITIONED BY (ingestion_date)
COMMENT 'Immutable snapshots of Bronze ingestion job executions. Captures job metadata for audit trail.'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);