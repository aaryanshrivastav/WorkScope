-- ============================================================================
-- Table: workspace.reporting.reporting_skill_demand
-- Layer: REPORTING
-- Description: Skill demand analytics showing most requested skills and trends
-- ============================================================================
-- Purpose: Physical table definition for reporting_skill_demand
-- Dependencies:
--   workspace.gold.bridge_job_skill
--   workspace.gold.fact_job_postings
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.reporting.reporting_skill_demand (
  skill_sk BIGINT NOT NULL COMMENT 'Skill key',
  demand_date_sk INT NOT NULL COMMENT 'Date key',
  job_count BIGINT COMMENT 'Jobs requiring skill',
  company_count BIGINT COMMENT 'Companies requiring skill',
  avg_salary_usd DECIMAL(15,2) COMMENT 'Average salary for skill',
  growth_rate_30d DECIMAL(10,2) COMMENT '30-day growth rate',
  top_sector STRING COMMENT 'Primary sector demanding skill',
  updated_at TIMESTAMP NOT NULL COMMENT 'Last refresh'

  -- PRIMARY KEY removed for Databricks Delta compatibility
  -- Composite uniqueness of (skill_sk, demand_date_sk)
  -- must be enforced through reporting refresh validation
)
USING DELTA
COMMENT 'Skill demand analytics showing most requested skills and trends'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);