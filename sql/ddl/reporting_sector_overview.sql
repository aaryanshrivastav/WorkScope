-- ============================================================================
-- Table: workspace.reporting.reporting_sector_overview
-- Layer: REPORTING
-- Description: Sector-level overview with key metrics and trends
-- ============================================================================
-- Purpose: Physical table definition for gold_sector_overview
-- Dependencies: workspace.gold.fact_job_postings, workspace.gold.fact_salary
-- Expected Output: Table created with 8 columns
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.reporting.reporting_sector_overview (
  sector_sk BIGINT NOT NULL COMMENT 'Sector key',
  overview_date_sk INT NOT NULL COMMENT 'Date key',
  total_jobs BIGINT COMMENT 'Total active jobs',
  total_companies BIGINT COMMENT 'Hiring companies',
  avg_salary_usd DECIMAL(15,2) COMMENT 'Average salary',
  top_skills ARRAY<STRING> COMMENT 'Most demanded skills',
  growth_rate_30d DECIMAL(10,2) COMMENT '30-day job growth',
  updated_at TIMESTAMP NOT NULL COMMENT 'Last refresh'
,
  PRIMARY KEY (sector_sk, overview_date_sk)
)
COMMENT 'Sector-level overview with key metrics and trends'
USING DELTA
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);

-- End of DDL
