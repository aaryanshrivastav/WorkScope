-- ============================================================================
-- Table: workspace.reporting.reporting_company_hiring
-- Layer: REPORTING
-- Description: Company-level hiring activity and metrics
-- ============================================================================
-- Purpose: Physical table definition for gold_company_hiring
-- Dependencies: workspace.gold.fact_job_postings, workspace.gold.dim_company
-- Expected Output: Table created with 8 columns
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.reporting.reporting_company_hiring (
  company_sk BIGINT NOT NULL COMMENT 'Company key',
  hiring_date_sk INT NOT NULL COMMENT 'Date key',
  active_jobs BIGINT COMMENT 'Active job count',
  new_jobs_30d BIGINT COMMENT 'New jobs last 30 days',
  top_role STRING COMMENT 'Most hired role',
  top_location STRING COMMENT 'Primary hiring location',
  remote_ratio DECIMAL(5,4) COMMENT 'Ratio of remote jobs',
  updated_at TIMESTAMP NOT NULL COMMENT 'Last refresh'
,
  PRIMARY KEY (company_sk, hiring_date_sk)
)
COMMENT 'Company-level hiring activity and metrics'
USING DELTA
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);

-- End of DDL
