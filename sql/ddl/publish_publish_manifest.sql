-- ============================================================================
-- Table: workspace.publish.publish_manifest
-- Layer: PUBLISH
-- Description: Manifest tracking for published data bundles
-- ============================================================================
-- Purpose: Physical table definition for publish_manifest
-- Dependencies: workspace.gold.* tables
-- Consumers: workspace.publish.publish_bundle_log
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.publish.publish_manifest (
  manifest_id STRING NOT NULL COMMENT 'Unique manifest identifier',
  bundle_name STRING NOT NULL COMMENT 'Name of data bundle',
  contract_version STRING NOT NULL COMMENT 'Data contract version',
  snapshot_timestamp TIMESTAMP NOT NULL COMMENT 'Data snapshot timestamp',
  checksum_json STRING COMMENT 'Checksums for all files in bundle (JSON)',
  rowcount_json STRING COMMENT 'Row counts for all tables (JSON)',
  access_mode STRING NOT NULL COMMENT 'Access mode: PUBLIC, RESTRICTED, PRIVATE',
  created_at TIMESTAMP NOT NULL COMMENT 'When manifest was created',

  -- Partition column required because Databricks does not support
  -- expression-based partitioning in PARTITIONED BY clauses
  created_date DATE NOT NULL COMMENT 'Derived partition date from created_at'

  -- PRIMARY KEY removed for Databricks Delta compatibility
  -- Enforced through publish orchestration and validation pipelines

  -- CHECK constraint removed for Databricks Delta compatibility
  -- Enforced through publish governance validation rules
)
USING DELTA
PARTITIONED BY (created_date)
COMMENT 'Manifest tracking for published data bundles'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);