-- ============================================================================
-- View: workspace.gold.role_review_queue
-- Layer: GOLD
-- Description: Queue of job roles requiring manual review and validation
-- ============================================================================
-- Purpose: Gold analytical view for role_review_queue
-- Dependencies: workspace.intermediate.sem_job_role_map
-- Expected Output: Aggregated metrics with 7 columns
-- ============================================================================

CREATE OR REPLACE VIEW workspace.gold.role_review_queue AS
SELECT
  CONCAT('RVW_', j.enterprise_job_id, '_', CAST(UNIX_TIMESTAMP(rm.created_at) AS STRING)) AS review_id,
  j.enterprise_job_id,
  j.title_raw,
  rm.canonical_role_name AS suggested_role,
  rm.mapping_confidence AS confidence,
  CASE 
    WHEN rm.mapping_confidence < 0.7 THEN 'PENDING'
    WHEN rm.mapping_confidence >= 0.9 THEN 'APPROVED'
    ELSE 'PENDING'
  END AS review_status,
  rm.created_at
FROM workspace.silver.silver_jobs_current j
JOIN workspace.intermediate.sem_job_role_map rm ON j.title_normalized = rm.title_normalized
WHERE rm.mapping_confidence < 0.9
  AND j.is_active = TRUE
  AND j.soft_delete_flag = FALSE

-- End of VIEW definition
