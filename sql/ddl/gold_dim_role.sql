-- ============================================================================
-- Table: workspace.gold.dim_role
-- Layer: GOLD
-- Description: Job role dimension with canonical role definitions
-- ============================================================================
-- Purpose: Physical table definition for dim_role
-- Dependencies: workspace.intermediate.inter_job_role_map
-- Consumers: workspace.gold.dim_job, workspace.gold.fact_job_postings
-- Expected Output: Table created with 8 columns
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.gold.dim_role (
  role_sk BIGINT NOT NULL COMMENT 'Surrogate key',
  canonical_role_id STRING NOT NULL COMMENT 'Canonical role identifier',
  role_name STRING NOT NULL COMMENT 'Role name',
  role_category STRING COMMENT 'Role category',
  role_level STRING COMMENT 'Seniority level',
  role_description STRING COMMENT 'Role description',
  is_active BOOLEAN NOT NULL COMMENT 'Active flag',
  created_at TIMESTAMP NOT NULL COMMENT 'Creation timestamp'
,
  PRIMARY KEY (role_sk)
)
COMMENT 'Job role dimension with canonical role definitions'
USING DELTA
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);

-- End of DDL
