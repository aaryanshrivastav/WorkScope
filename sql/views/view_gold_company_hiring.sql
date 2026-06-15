-- ============================================================================
-- View: workspace.gold.gold_company_hiring
-- Layer: GOLD
-- Description: Company-level hiring activity and metrics
-- ============================================================================
-- Purpose: Gold analytical view for gold_company_hiring
-- Dependencies: workspace.gold.fact_job_postings, workspace.gold.dim_company
-- Expected Output: Aggregated metrics with 8 columns
-- ============================================================================

CREATE OR REPLACE VIEW workspace.gold.gold_company_hiring AS
WITH company_metrics AS (
  SELECT
    f.company_sk,
    f.posting_date_sk AS hiring_date_sk,
    COUNT(CASE WHEN f.active_flag = TRUE THEN 1 END) AS active_jobs,
    COUNT(CASE WHEN f.is_new_job = TRUE AND DATEDIFF(DAY, f.posting_timestamp, CURRENT_TIMESTAMP()) <= 30 THEN 1 END) AS new_jobs_30d,
    f.role_sk,
    f.location_sk,
    COUNT(CASE WHEN d.remote_type = 'REMOTE' THEN 1 END) AS remote_count,
    COUNT(*) AS total_count
  FROM workspace.gold.fact_job_postings f
  JOIN workspace.gold.dim_job d ON f.job_sk = d.job_sk AND d.is_current = TRUE
  GROUP BY f.company_sk, f.posting_date_sk, f.role_sk, f.location_sk
),
top_role_per_company AS (
  SELECT
    company_sk,
    hiring_date_sk,
    role_sk,
    SUM(active_jobs) AS role_jobs,
    ROW_NUMBER() OVER (PARTITION BY company_sk, hiring_date_sk ORDER BY SUM(active_jobs) DESC) AS rn
  FROM company_metrics
  GROUP BY company_sk, hiring_date_sk, role_sk
),
top_location_per_company AS (
  SELECT
    company_sk,
    hiring_date_sk,
    location_sk,
    SUM(active_jobs) AS location_jobs,
    ROW_NUMBER() OVER (PARTITION BY company_sk, hiring_date_sk ORDER BY SUM(active_jobs) DESC) AS rn
  FROM company_metrics
  GROUP BY company_sk, hiring_date_sk, location_sk
)
SELECT
  cm.company_sk,
  cm.hiring_date_sk,
  SUM(cm.active_jobs) AS active_jobs,
  SUM(cm.new_jobs_30d) AS new_jobs_30d,
  r.role_name AS top_role,
  l.city AS top_location,
  CAST(SUM(cm.remote_count) AS DECIMAL(10,4)) / NULLIF(SUM(cm.total_count), 0) AS remote_ratio,
  CURRENT_TIMESTAMP() AS updated_at
FROM company_metrics cm
LEFT JOIN top_role_per_company tr 
  ON cm.company_sk = tr.company_sk 
  AND cm.hiring_date_sk = tr.hiring_date_sk 
  AND tr.rn = 1
LEFT JOIN workspace.gold.dim_role r ON tr.role_sk = r.role_sk
LEFT JOIN top_location_per_company tl 
  ON cm.company_sk = tl.company_sk 
  AND cm.hiring_date_sk = tl.hiring_date_sk 
  AND tl.rn = 1
LEFT JOIN workspace.gold.dim_location l ON tl.location_sk = l.location_sk
GROUP BY cm.company_sk, cm.hiring_date_sk, r.role_name, l.city

-- End of VIEW definition
