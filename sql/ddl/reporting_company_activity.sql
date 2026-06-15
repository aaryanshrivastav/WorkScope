-- ============================================================================
-- Table: workspace.reporting.reporting_company_activity
-- Layer: REPORTING
-- Description: Company hiring activity metrics by sector
-- ============================================================================
-- Purpose: Physical table definition for gold_company_activity
-- Dependencies: workspace.gold.fact_job_postings, workspace.gold.dim_company, workspace.gold.dim_sector
-- Expected Output: Table created with 6 columns
-- ============================================================================

CREATE OR REPLACE TABLE workspace.reporting.reporting_company_activity (
  sector_sk BIGINT NOT NULL COMMENT 'Sector foreign key',
  company_sk BIGINT NOT NULL COMMENT 'Company key',
  active_jobs BIGINT COMMENT 'Current active jobs',
  total_jobs_30d BIGINT COMMENT 'Jobs last 30 days',
  top_role STRING COMMENT 'Most hired role',
  updated_at TIMESTAMP NOT NULL COMMENT 'Last refresh',
  PRIMARY KEY (sector_sk, company_sk)
)
COMMENT 'Company hiring activity metrics by sector'
PARTITIONED BY (sector_sk)
USING DELTA
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);

-- End of DDL
