-- ============================================================================
-- Table: workspace.reporting.reporting_hiring_activity
-- Layer: REPORTING
-- Description: Hiring trends and analysis across sectors
-- ============================================================================
-- Purpose: Physical table definition for reporting_hiring_activity
-- Dependencies:
--   workspace.gold.fact_job_postings
--   workspace.gold.dim_sector
-- ============================================================================

CREATE OR REPLACE TABLE workspace.reporting.reporting_hiring_activity (
  sector_sk BIGINT NOT NULL COMMENT 'Sector foreign key',
  hiring_date_sk INT NOT NULL COMMENT 'Date key',
  total_jobs BIGINT COMMENT 'Total jobs in sector',
  new_jobs BIGINT COMMENT 'New postings',
  top_role STRING COMMENT 'Most hired role',
  avg_salary DECIMAL(15,2) COMMENT 'Average salary',
  updated_at TIMESTAMP NOT NULL COMMENT 'Last refresh'
)
USING DELTA
COMMENT 'Hiring trends and analysis across sectors'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);