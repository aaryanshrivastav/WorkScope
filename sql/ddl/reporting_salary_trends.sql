-- ============================================================================
-- Table: workspace.reporting.reporting_salary_trends
-- Layer: REPORTING
-- Description: Salary trends and compensation analytics by role and location
-- ============================================================================
-- Purpose: Physical table definition for gold_salary_trends
-- Dependencies: workspace.gold.fact_salary
-- Expected Output: Table created with 10 columns
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
,
  PRIMARY KEY (role_sk, location_sk, trend_date_sk)
)
COMMENT 'Salary trends and compensation analytics by role and location'
USING DELTA
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);

-- End of DDL
