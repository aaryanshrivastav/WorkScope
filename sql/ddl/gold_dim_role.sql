-- ============================================================================
-- Table: workspace.gold.dim_role
-- Layer: GOLD
-- Description: Job role dimension with canonical role definitions
-- ============================================================================
-- Purpose: Physical table definition for dim_role with taxonomy integration
-- Dependencies: workspace.metadata.taxonomy_role_canonical, taxonomy_role_families
-- Consumers: workspace.gold.dim_job, workspace.gold.fact_job_postings
-- Expected Output: Table created with 12 columns including taxonomy references
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.gold.dim_role (
  role_sk BIGINT NOT NULL COMMENT 'Surrogate key',
  role_key STRING NOT NULL COMMENT 'Natural key from taxonomy (e.g., ENG_SWE, HOSP_MANAGER)',
  canonical_role STRING NOT NULL COMMENT 'Canonical role name',
  family_key STRING COMMENT 'Role family key (e.g., ENG, HOSP_OPS, CLIN_CARE)',
  family_name STRING COMMENT 'Role family name (e.g., Engineering, Hospitality Operations)',
  sector_key STRING COMMENT 'Sector key (e.g., TECH, HOSP, HEAL)',
  seniority STRING COMMENT 'Seniority level (junior|mid|senior|executive)',
  role_description STRING COMMENT 'Role description',
  is_active BOOLEAN NOT NULL COMMENT 'Active flag',
  created_at TIMESTAMP NOT NULL COMMENT 'Record creation timestamp',
  updated_at TIMESTAMP COMMENT 'Last update timestamp',
  taxonomy_updated_at TIMESTAMP COMMENT 'Last taxonomy sync timestamp'
,
  PRIMARY KEY (role_sk)
)
USING DELTA
COMMENT 'Job role dimension with canonical role definitions'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);