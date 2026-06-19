-- ============================================================================
-- Table: workspace.audit.audit_dq_results
-- Layer: AUDIT
-- Description: Data quality check results and violations log
-- ============================================================================
-- Purpose: Physical table definition for audit_dq_results
-- Dependencies: None
-- Consumers: workspace.warehouse.fact_pipeline_runs
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.audit.audit_dq_results (
  dq_result_id STRING NOT NULL COMMENT 'DQ result ID',
  table_name STRING NOT NULL COMMENT 'Table checked',
  rule_name STRING NOT NULL COMMENT 'DQ rule applied',
  rule_type STRING NOT NULL COMMENT 'NOT_NULL, UNIQUE, RANGE, etc.',
  check_timestamp TIMESTAMP NOT NULL COMMENT 'When check ran',

  -- Partition column required because Databricks does not support
  -- expression-based partitioning in PARTITIONED BY clauses
  check_date DATE NOT NULL COMMENT 'Derived partition date from check_timestamp',

  status STRING NOT NULL COMMENT 'PASSED, FAILED, WARNING',
  rows_checked BIGINT COMMENT 'Rows evaluated',
  rows_failed BIGINT COMMENT 'Rows failing rule',
  failure_rate DECIMAL(5,4) COMMENT 'Failure percentage',
  details STRING COMMENT 'Additional details/samples'

  -- PRIMARY KEY removed for Databricks Delta compatibility
  -- Enforced through audit and pipeline validation processes

  -- CHECK CONSTRAINT removed for Databricks Delta compatibility
  -- Enforced through DQ orchestration and validation framework
)
USING DELTA
PARTITIONED BY (check_date)
COMMENT 'Data quality check results and violations log'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);