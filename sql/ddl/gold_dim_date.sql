-- ============================================================================
-- Table: workspace.gold.dim_date
-- Layer: GOLD
-- Description: Date dimension with calendar attributes for time-series analysis
-- ============================================================================
-- Purpose: Physical table definition for dim_date
-- Dependencies: None (source table)
-- Consumers: workspace.gold.fact_job_postings,
--            workspace.gold.fact_salary
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.gold.dim_date (
  date_sk INT NOT NULL COMMENT 'Surrogate key (YYYYMMDD format)',
  date_value DATE NOT NULL COMMENT 'Actual date',
  year INT NOT NULL COMMENT 'Year (YYYY)',
  quarter INT NOT NULL COMMENT 'Quarter (1-4)',
  month INT NOT NULL COMMENT 'Month (1-12)',
  month_name STRING NOT NULL COMMENT 'Month name',
  day_of_month INT NOT NULL COMMENT 'Day (1-31)',
  day_of_week INT NOT NULL COMMENT 'Day of week (1-7)',
  day_name STRING NOT NULL COMMENT 'Day name',
  week_of_year INT NOT NULL COMMENT 'ISO week number',
  is_weekend BOOLEAN NOT NULL COMMENT 'Weekend flag',
  is_holiday BOOLEAN NOT NULL COMMENT 'Holiday flag',
  fiscal_year INT COMMENT 'Fiscal year',
  fiscal_quarter INT COMMENT 'Fiscal quarter'

  -- PRIMARY KEY removed for Databricks Delta compatibility
  -- Uniqueness of date_sk must be enforced through
  -- dimension loading and validation processes
)
USING DELTA
COMMENT 'Date dimension with calendar attributes for time-series analysis'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);