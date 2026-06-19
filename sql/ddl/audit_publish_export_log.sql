-- ============================================================================
-- Table: workspace.audit.publish_export_log
-- Layer: AUDIT
-- Description: Audit log for CSV snapshot exports tracking per-table export results
-- ============================================================================
-- Purpose: Physical table definition for publish_export_log
-- Dependencies: None
-- Consumers: None (audit/monitoring use)
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.audit.publish_export_log (
  `table` STRING COMMENT 'Name of the table that was exported',
  status STRING COMMENT 'Export status: success, error, or skipped',
  row_count BIGINT COMMENT 'Number of rows exported from the table',
  file_size_mb DOUBLE COMMENT 'Size of the generated CSV file in megabytes',
  duration_sec DOUBLE COMMENT 'Time taken to export the table in seconds',
  checksum STRING COMMENT 'MD5 checksum of the exported CSV file for integrity verification',
  `file` STRING COMMENT 'Relative path to the exported CSV file (e.g., data/dim_sector.csv.gz)',
  `schema` STRING COMMENT 'Source schema name (e.g., warehouse, gold, audit)',
  sort_columns ARRAY<STRING> COMMENT 'Columns used for deterministic sorting during export',
  error STRING COMMENT 'Error message if status is error',
  reason STRING COMMENT 'Reason for skip if status is skipped (e.g., empty)'

  -- CHECK CONSTRAINT removed for Databricks Delta compatibility
  -- Enforced through export pipeline validation and audit controls
)
USING DELTA
COMMENT 'Audit log for CSV snapshot exports. Records export status, metrics, and file details for each table exported.'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);