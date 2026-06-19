-- ============================================================================
-- Table: workspace.reporting.reporting_location_trends
-- Layer: REPORTING
-- Description: Geographic hiring trends and location-based analytics
-- ============================================================================
-- Purpose: Physical table definition for reporting_location_trends
-- Dependencies:
--   workspace.gold.fact_job_postings
--   workspace.gold.dim_location
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.reporting.reporting_location_trends (
  location_sk BIGINT NOT NULL COMMENT 'Location key',
  trend_date_sk INT NOT NULL COMMENT 'Date key',
  total_jobs BIGINT COMMENT 'Total jobs in location',
  remote_jobs BIGINT COMMENT 'Remote job count',
  onsite_jobs BIGINT COMMENT 'Onsite job count',
  avg_salary_usd DECIMAL(15,2) COMMENT 'Average salary',
  top_sector STRING COMMENT 'Dominant sector',
  updated_at TIMESTAMP NOT NULL COMMENT 'Last refresh'

  -- PRIMARY KEY removed for Databricks Delta compatibility
  -- Composite uniqueness of (location_sk, trend_date_sk)
  -- must be enforced through reporting refresh validation
)
USING DELTA
COMMENT 'Geographic hiring trends and location-based analytics'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);