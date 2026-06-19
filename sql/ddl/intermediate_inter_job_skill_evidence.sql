-- ============================================================================
-- Table: workspace.intermediate.inter_job_skill_evidence
-- Layer: INTERMEDIATE
-- Description: Evidence snippets for job-skill mappings for review and validation
-- ============================================================================
-- Purpose: Physical table definition for inter_job_skill_evidence
-- Dependencies: workspace.silver.silver_skill_mapping
-- Consumers: workspace.gold.bridge_job_skill
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspace.intermediate.inter_job_skill_evidence (
  evidence_id STRING NOT NULL COMMENT 'Unique evidence ID',
  enterprise_job_id STRING NOT NULL COMMENT 'Job identifier',
  skill_id STRING NOT NULL COMMENT 'Skill identifier',
  evidence_text STRING NOT NULL COMMENT 'Text snippet showing skill',
  context_before STRING COMMENT 'Text before mention',
  context_after STRING COMMENT 'Text after mention',
  confidence DECIMAL(5,4) NOT NULL COMMENT 'Extraction confidence',
  review_status STRING COMMENT 'PENDING, APPROVED, REJECTED',
  extracted_at TIMESTAMP NOT NULL COMMENT 'Extraction timestamp'

  -- PRIMARY KEY removed for Databricks Delta compatibility
  -- Uniqueness of evidence_id must be enforced through
  -- skill extraction and validation pipelines
)
USING DELTA
COMMENT 'Evidence snippets for job-skill mappings for review and validation'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);