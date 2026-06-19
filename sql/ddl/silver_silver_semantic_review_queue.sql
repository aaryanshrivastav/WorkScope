-- ============================================================================
-- Table: workspace.silver.silver_semantic_review_queue
-- Layer: SILVER
-- Description: Queue for semantic review of job postings with data quality
--              or classification issues
-- ============================================================================
-- Purpose: Physical table definition for silver_semantic_review_queue
-- Dependencies: workspace.silver.silver_jobs_current
-- Consumers: workspace.audit.audit_dq_results
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.silver.silver_semantic_review_queue (
  review_id STRING NOT NULL COMMENT 'Unique review item identifier',
  enterprise_job_id STRING NOT NULL COMMENT 'FK to silver_jobs_current',
  issue_type STRING NOT NULL COMMENT 'Type of issue: SECTOR_AMBIGUOUS, TITLE_UNCLEAR, etc.',
  issue_detail STRING COMMENT 'Detailed description of the issue',
  confidence DOUBLE COMMENT 'Confidence score that this is an issue (0.0-1.0)',
  queued_at TIMESTAMP NOT NULL COMMENT 'When item was queued for review',
  status STRING NOT NULL COMMENT 'Review status: PENDING, IN_REVIEW, RESOLVED, DISMISSED',
  resolved_at TIMESTAMP COMMENT 'When review was completed',
  resolution_notes STRING COMMENT 'Notes from review resolution',
  batch_id STRING NOT NULL COMMENT 'Batch that identified the issue',
  source_name STRING NOT NULL COMMENT 'Source system identifier',

  queued_date DATE NOT NULL COMMENT 'Derived partition date from queued_at'

  -- PRIMARY KEY removed for Databricks Delta compatibility
  -- Uniqueness of review_id must be enforced through review workflow validation

  -- CHECK constraint removed for Databricks compatibility
  -- status domain must be enforced through DQ validation
)
USING DELTA
PARTITIONED BY (queued_date)
COMMENT 'Queue for semantic review of job postings with data quality or classification issues'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);