-- ============================================================================
-- Table: workspace.reporting.role_review_queue
-- Layer: REPORTING
-- Description: Queue of job roles requiring manual review and validation
-- ============================================================================
-- Purpose: Physical table definition for role_review_queue
-- Dependencies: workspace.intermediate.inter_job_role_map
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.reporting.role_review_queue (
  review_id STRING NOT NULL COMMENT 'Review queue entry ID',
  enterprise_job_id STRING NOT NULL COMMENT 'Job identifier',
  title_raw STRING NOT NULL COMMENT 'Raw job title',
  suggested_role STRING COMMENT 'AI-suggested role',
  confidence DECIMAL(5,4) COMMENT 'Suggestion confidence',
  review_status STRING NOT NULL COMMENT 'PENDING, APPROVED, REJECTED',
  created_at TIMESTAMP NOT NULL COMMENT 'Queue entry timestamp'

  -- PRIMARY KEY removed for Databricks Delta compatibility
  -- Uniqueness of review_id must be enforced through
  -- workflow validation and review queue processing
)
USING DELTA
COMMENT 'Queue of job roles requiring manual review and validation'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);