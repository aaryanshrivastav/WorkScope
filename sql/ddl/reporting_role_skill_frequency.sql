-- ============================================================================
-- Table: workspace.reporting.reporting_role_skill_frequency
-- Layer: REPORTING
-- Description: Derived mart showing skill frequency and average demand score per canonical role
-- ============================================================================
-- Purpose: Physical table definition for reporting_role_skill_frequency
-- Dependencies:
--   workspace.gold.bridge_job_skill
--   workspace.gold.dim_job
--   workspace.gold.dim_role
--   workspace.gold.dim_skill
-- ============================================================================

CREATE OR REPLACE TABLE ${catalog}.reporting.reporting_role_skill_frequency (
  role_sk BIGINT NOT NULL COMMENT 'Role surrogate key',
  role_key STRING NOT NULL COMMENT 'Natural key for canonical role',
  skill_sk BIGINT NOT NULL COMMENT 'Skill surrogate key',
  skill_key STRING NOT NULL COMMENT 'Natural key for skill',
  postings_count BIGINT COMMENT 'Number of postings for this role that require this skill',
  total_role_postings BIGINT COMMENT 'Total number of postings for this role',
  mention_percentage DECIMAL(5,2) COMMENT 'Percentage of postings for this role that mention this skill',
  avg_extraction_confidence DECIMAL(5,4) COMMENT 'Average extraction confidence for this skill-role pair',
  avg_demand_score DECIMAL(5,2) COMMENT 'Average weighted demand score (REQUIRED=5.0, PREFERRED=3.0, NICE_TO_HAVE=1.0)',
  updated_at TIMESTAMP NOT NULL COMMENT 'Last refresh timestamp'
)
USING DELTA
COMMENT 'Derived analytical mart showing skill requirement frequency and demand score per canonical role'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);

