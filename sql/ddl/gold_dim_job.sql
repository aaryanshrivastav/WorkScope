-- ============================================================================
-- Table: workspace.gold.dim_job
-- Layer: GOLD
-- Description: Job dimension with SCD Type 2 for tracking job posting changes over time
-- ============================================================================
-- Purpose: Physical table definition for dim_job
-- Dependencies: workspace.silver.silver_jobs_current, workspace.silver.silver_job_identity_map
-- Consumers: workspace.gold.fact_job_postings, workspace.gold.fact_job_lifecycle
-- Expected Output: Table created with 16 columns
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.gold.dim_job (
  job_sk BIGINT NOT NULL COMMENT 'Surrogate key (version-specific)',
  enterprise_job_id STRING NOT NULL COMMENT 'Durable job identifier',
  canonical_role_id STRING COMMENT 'Canonical role ID',
  company_sk BIGINT COMMENT 'FK to dim_company',
  location_sk BIGINT COMMENT 'FK to dim_location',
  sector_sk BIGINT COMMENT 'FK to dim_sector',
  title_normalized STRING COMMENT 'Standardized job title',
  salary_min DECIMAL(15,2) COMMENT 'Minimum salary',
  salary_max DECIMAL(15,2) COMMENT 'Maximum salary',
  salary_currency STRING COMMENT 'Salary currency',
  remote_type STRING COMMENT 'REMOTE, HYBRID, ONSITE',
  employment_type_normalized STRING COMMENT 'Employment type',
  effective_from TIMESTAMP NOT NULL COMMENT 'Version valid from',
  effective_to TIMESTAMP COMMENT 'Version valid to',
  is_current BOOLEAN NOT NULL COMMENT 'Current version flag',
  record_hash STRING NOT NULL COMMENT 'Content hash for change detection'
,
  PRIMARY KEY (job_sk)
)
COMMENT 'Job dimension with SCD Type 2 for tracking job posting changes over time'
PARTITIONED BY (effective_from)
USING DELTA
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);

-- End of DDL
