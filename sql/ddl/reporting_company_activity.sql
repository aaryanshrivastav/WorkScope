-- ============================================================================
-- Table: workspace.reporting.reporting_company_activity
-- Layer: REPORTING
-- Description: Company hiring activity metrics by sector
-- ============================================================================
-- Purpose: Physical table definition for reporting_company_activity
-- Dependencies:
--   workspace.gold.fact_job_postings
--   workspace.gold.dim_company
--   workspace.gold.dim_sector
-- ============================================================================

CREATE OR REPLACE TABLE workspace.reporting.reporting_company_activity (
  sector_sk BIGINT NOT NULL COMMENT 'Sector foreign key',
  company_sk BIGINT NOT NULL COMMENT 'Company key',
  active_jobs BIGINT COMMENT 'Current active jobs',
  total_jobs_30d BIGINT COMMENT 'Jobs last 30 days',
  top_role STRING COMMENT 'Most hired role',
  updated_at TIMESTAMP NOT NULL COMMENT 'Last refresh'

  -- PRIMARY KEY removed for Databricks Delta compatibility
  -- Composite uniqueness of (sector_sk, company_sk)
  -- must be enforced through reporting build validation
)
USING DELTA
COMMENT 'Company hiring activity metrics by sector'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);