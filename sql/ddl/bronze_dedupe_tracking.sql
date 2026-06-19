-- ============================================================================
-- Table: workspace.bronze.dedupe_tracking
-- Layer: BRONZE
-- Description: Tracks duplicate payload occurrences in Bronze tables without deleting data
-- ============================================================================
-- Purpose: Physical table definition for dedupe_tracking
-- Dependencies: workspace.bronze.bronze_job_snapshot
-- Consumers: workspace.audit.audit_dq_results
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.bronze.dedupe_tracking (
  dedupe_id STRING NOT NULL COMMENT 'Unique deduplication record ID',
  source_table STRING NOT NULL COMMENT 'Source table being deduplicated',
  batch_id STRING NOT NULL COMMENT 'Batch identifier',
  dedupe_key_hash STRING NOT NULL COMMENT 'Hash of deduplication key columns',
  first_seen_record_id STRING COMMENT 'First occurrence record ID',
  first_seen_batch_id STRING COMMENT 'Batch where first seen',
  duplicate_count INT NOT NULL COMMENT 'Number of duplicate occurrences',
  first_seen_timestamp TIMESTAMP COMMENT 'First occurrence timestamp',
  last_seen_timestamp TIMESTAMP COMMENT 'Last occurrence timestamp',

  batch_status STRING NOT NULL COMMENT 'Batch processing status: PROCESSED, ROLLED_BACK',

  tracking_timestamp TIMESTAMP NOT NULL COMMENT 'When dedupe was tracked',

  -- Partition column required to avoid high-cardinality TIMESTAMP partitioning
  tracking_date DATE NOT NULL COMMENT 'Derived partition date from tracking_timestamp'

  -- PRIMARY KEY removed for Databricks Delta compatibility
  -- Enforced through ingestion and reconciliation pipelines

  -- DEFAULT value removed for Databricks portability
  -- Ingestion pipelines should populate PROCESSED when no explicit status is supplied
)
USING DELTA
PARTITIONED BY (tracking_date)
COMMENT 'Tracks duplicate payload occurrences in Bronze tables without deleting data'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);