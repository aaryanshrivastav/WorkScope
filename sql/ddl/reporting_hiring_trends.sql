-- ============================================================================
-- Table: workspace.reporting.reporting_hiring_trends
-- Layer: REPORTING
-- Description: Aggregated hiring trends by date and sector for time-series analysis
-- ============================================================================
-- Purpose: Physical table definition for reporting_hiring_trends
-- Dependencies:
--   workspace.gold.fact_job_postings
--   workspace.gold.dim_sector
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.reporting.reporting_hiring_trends (
  hiring_date_sk BIGINT NOT NULL COMMENT 'Date key',
  sector_sk BIGINT NOT NULL COMMENT 'Sector key',
  total_new_jobs BIGINT COMMENT 'New jobs posted',
  total_active_jobs BIGINT COMMENT 'Active job count',
  total_closed_jobs BIGINT COMMENT 'Closed job count',
  unique_companies BIGINT COMMENT 'Companies hiring',
  avg_days_to_fill DECIMAL(10,2) COMMENT 'Average time to fill',
  updated_at TIMESTAMP NOT NULL COMMENT 'Last refresh'

  -- PRIMARY KEY removed for Databricks Delta compatibility
  -- Composite uniqueness of (hiring_date_sk, sector_sk)
  -- must be enforced through reporting refresh validation
)
USING DELTA
COMMENT 'Aggregated hiring trends by date and sector for time-series analysis'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);