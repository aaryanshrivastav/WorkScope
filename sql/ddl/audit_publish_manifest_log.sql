-- ============================================================================
-- Table: workspace.audit.publish_manifest_log
-- Layer: AUDIT
-- Description: Audit log for manifest generation operations
-- ============================================================================
-- Purpose: Physical table definition for publish_manifest_log
-- Dependencies: None
-- Consumers: None (audit/monitoring use)
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.audit.publish_manifest_log (
  operation STRING COMMENT 'Type of manifest operation performed (e.g., manifest_generation)',
  master_manifest_path STRING COMMENT 'Path to the master manifest file in UC Volumes',
  snapshot_count INT COMMENT 'Number of snapshots documented in the manifest',
  table_count INT COMMENT 'Number of tables included in the manifest',
  manifest_version STRING COMMENT 'Version of the manifest format (e.g., 1.0)',
  generated_at TIMESTAMP COMMENT 'Timestamp when the manifest was generated (ISO 8601 format)'
)
USING DELTA
COMMENT 'Audit log for manifest generation. Records manifest creation events with snapshot and table counts.'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);