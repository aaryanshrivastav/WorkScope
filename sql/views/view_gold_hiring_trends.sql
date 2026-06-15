-- ============================================================================
-- View: workspace.gold.gold_hiring_trends
-- Layer: GOLD
-- Description: Aggregated hiring trends by date and sector
-- ============================================================================
-- Purpose: Time-series analysis of hiring patterns across sectors
-- Dependencies: workspace.gold.fact_job_postings, workspace.gold.dim_sector, workspace.gold.dim_date
-- Expected Output: Daily/weekly/monthly hiring metrics by sector
-- ============================================================================

CREATE OR REPLACE VIEW workspace.gold.gold_hiring_trends AS
SELECT
  d.date_sk AS hiring_date_sk,
  s.sector_sk,
  s.sector_name,
  COUNT(DISTINCT CASE WHEN f.is_new_job = TRUE THEN f.job_sk END) AS total_new_jobs,
  COUNT(DISTINCT CASE WHEN f.active_flag = TRUE THEN f.job_sk END) AS total_active_jobs,
  COUNT(DISTINCT CASE WHEN f.is_soft_delete = TRUE THEN f.job_sk END) AS total_closed_jobs,
  COUNT(DISTINCT f.company_sk) AS unique_companies,
  AVG(DATEDIFF(DAY, f.posting_timestamp, CURRENT_TIMESTAMP())) AS avg_days_to_fill,
  CURRENT_TIMESTAMP() AS updated_at
FROM workspace.gold.fact_job_postings f
JOIN workspace.gold.dim_date d ON f.posting_date_sk = d.date_sk
JOIN workspace.gold.dim_sector s ON f.sector_sk = s.sector_sk
GROUP BY d.date_sk, s.sector_sk, s.sector_name;

-- End of VIEW definition
