-- ============================================================================
-- Table: workspace.reporting.reporting_salary_trends
-- Layer: REPORTING
-- Description: Salary trends and compensation analytics by role and location
-- ============================================================================
-- Purpose: Physical table definition for reporting_salary_trends
-- Dependencies: workspace.gold.fact_salary
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.reporting.reporting_salary_trends (
  role_sk BIGINT NOT NULL COMMENT 'Role key',
  location_sk BIGINT NOT NULL COMMENT 'Location key',
  trend_date_sk INT NOT NULL COMMENT 'Date key',
  avg_salary_min DECIMAL(15,2) COMMENT 'Average minimum salary',
  avg_salary_max DECIMAL(15,2) COMMENT 'Average maximum salary',
  median_salary DECIMAL(15,2) COMMENT 'Median salary',
  p25_salary DECIMAL(15,2) COMMENT '25th percentile',
  p75_salary DECIMAL(15,2) COMMENT '75th percentile',
  sample_size BIGINT COMMENT 'Number of job postings',
  updated_at TIMESTAMP NOT NULL COMMENT 'Last refresh'

  -- PRIMARY KEY removed for Databricks Delta compatibility
  -- Composite uniqueness of (role_sk, location_sk, trend_date_sk)
  -- must be enforced through reporting refresh validation
)
USING DELTA
COMMENT 'Salary trends and compensation analytics by role and location'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);