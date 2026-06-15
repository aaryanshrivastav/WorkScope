-- ============================================================================
-- Table: workspace.reporting.reporting_skill_demand_by_sector
-- Layer: REPORTING
-- Description: Skill demand analysis by sector
-- ============================================================================
-- Purpose: Physical table definition for gold_skill_demand_by_sector
-- Dependencies: workspace.gold.bridge_job_skill, workspace.gold.dim_sector
-- Expected Output: Table created with 7 columns
-- ============================================================================

CREATE OR REPLACE TABLE workspace.reporting.reporting_skill_demand_by_sector (
  sector_sk BIGINT NOT NULL COMMENT 'Sector foreign key',
  skill_sk BIGINT NOT NULL COMMENT 'Skill key',
  trend_date_sk INT NOT NULL COMMENT 'Date key',
  job_count BIGINT COMMENT 'Jobs requiring skill',
  demand_rank INT COMMENT 'Skill demand rank',
  growth_rate DECIMAL(10,2) COMMENT 'Growth rate',
  updated_at TIMESTAMP NOT NULL COMMENT 'Last refresh'
)
USING DELTA
PARTITIONED BY (sector_sk)
COMMENT 'Skill demand analysis by sector'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);

-- End of DDL
