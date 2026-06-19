-- ============================================================================
-- Table: workspace.bronze.bronze_api_response_log
-- Layer: BRONZE
-- Description: Immutable log of all API request/response pairs for audit and replay capability
-- ============================================================================
-- Purpose: Physical table definition for bronze_api_response_log
-- Dependencies: external_api
-- Consumers: workspace.audit.audit_access_events
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.bronze.bronze_api_response_log (
  response_log_id STRING NOT NULL COMMENT 'Unique log identifier',
  source_name STRING NOT NULL COMMENT 'API source name',
  batch_id STRING NOT NULL COMMENT 'Batch identifier',
  request_url STRING NOT NULL COMMENT 'API endpoint URL',
  http_status_code INT NOT NULL COMMENT 'HTTP response status code',
  retry_count INT COMMENT 'Number of retries attempted',
  rate_limit_hit BOOLEAN COMMENT 'Whether rate limit was hit',
  response_time_ms INT COMMENT 'Response time in milliseconds',
  logged_at TIMESTAMP NOT NULL COMMENT 'Log timestamp',

  -- Partition column required to avoid high-cardinality TIMESTAMP partitioning
  logged_date DATE NOT NULL COMMENT 'Derived partition date from logged_at'

  -- PRIMARY KEY removed for Databricks Delta compatibility
  -- Enforced through ingestion and reconciliation pipelines
)
USING DELTA
PARTITIONED BY (logged_date)
COMMENT 'Immutable log of all API request/response pairs for audit and replay capability'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);