-- ============================================================================
-- Table: workspace.quarantine.quarantine_jobs
-- Layer: QUARANTINE
-- Description: Records that failed data quality validation and require human review
-- ============================================================================
-- Purpose: Physical table definition for quarantine_jobs
-- Dependencies: workspace.silver.silver_jobs_current
-- Consumers: workspace.gold.gold_pipeline_health,
--            workspace.audit.audit_dq_results
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.quarantine.quarantine_jobs (
  quarantine_id STRING NOT NULL COMMENT 'Unique identifier for this quarantine entry (UUID)',
  enterprise_job_id STRING NOT NULL COMMENT 'Foreign key to silver.silver_jobs_current',
  source_name STRING NOT NULL COMMENT 'Data source that originated this record',
  source_job_id STRING COMMENT 'Original job ID from the source system',
  job_title STRING COMMENT 'Job title from the record for reference',
  title_raw STRING COMMENT 'Raw job title before standardization',
  company_name STRING COMMENT 'Company name from the record for reference',
  company_name_raw STRING COMMENT 'Raw company name before standardization',
  quarantine_reason STRING NOT NULL COMMENT 'Human-readable reason for quarantine',
  failed_rule_name STRING NOT NULL COMMENT 'Specific DQ rule that failed',
  failure_stage STRING NOT NULL COMMENT 'Pipeline stage where failure occurred',
  severity STRING NOT NULL COMMENT 'ERROR (blocks downstream), WARN (flagged for review)',
  quarantine_severity STRING COMMENT 'Duplicate/alias of severity for backward compatibility',
  raw_payload STRING COMMENT 'Original JSON payload for root cause analysis',
  reprocess_status STRING NOT NULL COMMENT 'Current lifecycle status: PENDING, REPROCESS, REPROCESSED, DISCARDED, REPROCESS_FAILED, RESOLVED',
  reprocess_reason STRING COMMENT 'Human reviewer''s documented reason for decision',
  reprocess_batch_id STRING COMMENT 'Batch identifier for tracking bulk operations',
  reviewed_by STRING COMMENT 'Email address of reviewer who made decision',
  reviewed_at TIMESTAMP COMMENT 'Timestamp when human review decision was made',
  quarantined_at TIMESTAMP NOT NULL COMMENT 'Timestamp when record was first routed to quarantine',
  reprocessed_at TIMESTAMP COMMENT 'Timestamp when record was reprocessed',
  resolved_at TIMESTAMP COMMENT 'Timestamp when record lifecycle completed',

  -- Partition column required because Databricks does not support
  -- expression-based partitioning in PARTITIONED BY clauses
  quarantined_date DATE NOT NULL COMMENT 'Derived partition date from quarantined_at'

  -- PRIMARY KEY removed for Databricks Delta compatibility
  -- Enforced through quarantine routing and validation pipelines

  -- CHECK constraints removed for Databricks Delta compatibility
  -- Enforced through DQ and workflow validation rules
)
USING DELTA
PARTITIONED BY (quarantined_date)
COMMENT 'Records that failed data quality validation and require human review'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);