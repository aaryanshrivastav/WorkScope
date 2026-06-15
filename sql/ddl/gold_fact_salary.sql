-- ============================================================================
-- Table: workspace.gold.fact_salary
-- Layer: GOLD
-- Description: Salary fact table for compensation analysis
-- ============================================================================
-- Purpose: Physical table definition for fact_salary
-- Dependencies: workspace.gold.dim_job
-- Consumers: workspace.gold.gold_salary_trends
-- Expected Output: Table created with 11 columns
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.gold.fact_salary (
  fact_salary_sk BIGINT NOT NULL COMMENT 'Fact surrogate key',
  job_sk BIGINT NOT NULL COMMENT 'FK to dim_job',
  role_sk BIGINT NOT NULL COMMENT 'FK to dim_role',
  location_sk BIGINT NOT NULL COMMENT 'FK to dim_location',
  source_sk BIGINT NOT NULL COMMENT 'FK to dim_source',
  posted_date_sk INT NOT NULL COMMENT 'FK to dim_date',
  salary_min DECIMAL(15,2) COMMENT 'Minimum salary',
  salary_max DECIMAL(15,2) COMMENT 'Maximum salary',
  salary_midpoint DECIMAL(15,2) COMMENT 'Midpoint salary',
  salary_currency STRING NOT NULL COMMENT 'Currency code',
  salary_normalized_usd DECIMAL(15,2) COMMENT 'USD-normalized salary'
,
  PRIMARY KEY (fact_salary_sk)
)
COMMENT 'Salary fact table for compensation analysis'
USING DELTA
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);

-- End of DDL
