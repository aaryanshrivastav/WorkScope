-- ============================================================================
-- Table: workspace.audit.audit_access_events
-- Layer: AUDIT
-- Description: Audit log of data access events for security and compliance
-- ============================================================================
-- Purpose: Physical table definition for audit_access_events
-- Dependencies: None
-- Consumers: None (audit/compliance use)
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.audit.audit_access_events (
  access_event_id STRING NOT NULL COMMENT 'Access event ID',
  user_id STRING NOT NULL COMMENT 'User identifier',
  user_email STRING COMMENT 'User email',
  access_timestamp TIMESTAMP NOT NULL COMMENT 'Access time',

  -- Partition column required because Databricks does not support
  -- expression-based partitioning such as DATE(access_timestamp)
  access_date DATE NOT NULL COMMENT 'Derived partition date from access_timestamp',

  resource_type STRING NOT NULL COMMENT 'TABLE, VIEW, NOTEBOOK',
  resource_name STRING NOT NULL COMMENT 'Resource accessed',
  action STRING NOT NULL COMMENT 'SELECT, INSERT, UPDATE, DELETE',
  rows_affected BIGINT COMMENT 'Rows read/modified',
  status STRING NOT NULL COMMENT 'SUCCESS, DENIED, ERROR'

  -- PRIMARY KEY removed for Databricks Delta compatibility
  -- Enforced through ingestion and audit validation pipelines

  -- CHECK CONSTRAINT removed for Databricks Delta compatibility
  -- Enforced through audit data quality validation rules
)
USING DELTA
PARTITIONED BY (access_date)
COMMENT 'Audit log of data access events for security and compliance'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);