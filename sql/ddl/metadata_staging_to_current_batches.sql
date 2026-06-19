-- ============================================================================
-- Table: workspace.metadata.staging_to_current_batches
-- Layer: METADATA
-- Description: Tracks which staging batches have been processed through CDC to current
-- ============================================================================
-- Purpose: Physical table definition for staging_to_current_batches
-- Dependencies: workspace.silver.silver_jobs_staging
-- Consumers: workspace.silver.silver_jobs_current (CDC idempotency control)
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.metadata.staging_to_current_batches (
  batch_id STRING COMMENT 'Staging batch identifier that was processed through CDC',
  source_name STRING COMMENT 'Data source name (e.g., remotive, arbeitnow)',
  inserts INT COMMENT 'Number of INSERT operations performed for this batch',
  updates INT COMMENT 'Number of UPDATE operations performed for this batch',
  deletes INT COMMENT 'Number of DELETE operations performed for this batch',
  processed_at TIMESTAMP COMMENT 'Timestamp when the batch was processed through CDC',
  run_id STRING COMMENT 'Workflow run identifier (format: YYYYMMDD_HHMMSS)',
  status STRING COMMENT 'Processing status: success or failed'

  -- PRIMARY KEY removed for Databricks Delta compatibility
  -- Composite uniqueness of (batch_id, source_name)
  -- must be enforced by CDC orchestration logic

  -- CHECK constraint removed for Databricks Delta compatibility
  -- Status validation must be enforced by pipeline DQ controls
)
USING DELTA
COMMENT 'Tracks which staging batches have been processed through CDC to current. Used by silver_detect_cdc to ensure idempotent batch processing.'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);