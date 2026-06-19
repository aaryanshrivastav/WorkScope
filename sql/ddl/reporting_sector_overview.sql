-- ============================================================================
-- Table: workspace.reporting.reporting_sector_overview
-- Layer: REPORTING
-- Description: Sector-level overview with key metrics and trends
-- ============================================================================
-- Purpose: Physical table definition for reporting_sector_overview
-- Dependencies:
--   workspace.gold.fact_job_postings
--   workspace.gold.fact_salary
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

  -- PRIMARY KEY removed for Databricks Delta compatibility
  -- Composite uniqueness of (sector_sk, overview_date_sk)
  -- must be enforced through reporting refresh validation
)
USING DELTA
COMMENT 'Sector-level overview with key metrics and trends'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);