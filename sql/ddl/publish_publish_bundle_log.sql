-- ============================================================================
-- Table: workspace.publish.publish_bundle_log
-- Layer: PUBLISH
-- Description: Log of bundle delivery attempts to external systems
-- ============================================================================
-- Purpose: Physical table definition for publish_bundle_log
-- Dependencies: workspace.publish.publish_manifest
-- Consumers: None (audit/monitoring use)
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.publish.publish_bundle_log (
  bundle_log_id STRING NOT NULL COMMENT 'Unique log entry identifier',
  manifest_id STRING NOT NULL COMMENT 'FK to publish_manifest',
  target_system STRING NOT NULL COMMENT 'Destination system identifier',
  target_location STRING COMMENT 'Destination path or endpoint',
  status STRING NOT NULL COMMENT 'Delivery status: PENDING, IN_PROGRESS, DELIVERED, FAILED',
  created_at TIMESTAMP NOT NULL COMMENT 'When delivery was initiated',

  -- Partition column required because Databricks does not support
  -- expression-based partitioning in PARTITIONED BY clauses
  created_date DATE NOT NULL COMMENT 'Derived partition date from created_at'

  -- PRIMARY KEY removed for Databricks Delta compatibility
  -- Enforced through publish pipeline validation

  -- CHECK constraint removed for Databricks Delta compatibility
  -- Enforced through publish workflow validation rules
)
USING DELTA
PARTITIONED BY (created_date)
COMMENT 'Log of bundle delivery attempts to external systems'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);