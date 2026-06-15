-- ============================================================================
-- View: workspace.gold.gold_location_trends
-- Layer: GOLD
-- Description: Geographic hiring trends and location-based analytics
-- ============================================================================
-- Purpose: Gold analytical view for gold_location_trends
-- Dependencies: workspace.gold.fact_job_postings, workspace.gold.dim_location
-- Expected Output: Aggregated metrics with 8 columns
-- ============================================================================

CREATE OR REPLACE VIEW workspace.gold.gold_location_trends AS
WITH location_metrics AS (
  SELECT
    f.location_sk,
    f.posting_date_sk AS trend_date_sk,
    COUNT(*) AS total_jobs,
    COUNT(CASE WHEN d.remote_type = 'REMOTE' THEN 1 END) AS remote_jobs,
    COUNT(CASE WHEN d.remote_type = 'ONSITE' THEN 1 END) AS onsite_jobs,
    AVG(d.salary_max) AS avg_salary_usd,
    f.sector_sk
  FROM workspace.gold.fact_job_postings f
  JOIN workspace.gold.dim_job d ON f.job_sk = d.job_sk AND d.is_current = TRUE
  WHERE f.active_flag = TRUE
  GROUP BY f.location_sk, f.posting_date_sk, f.sector_sk
),
top_sector_per_location AS (
  SELECT
    location_sk,
    trend_date_sk,
    sector_sk,
    total_jobs,
    ROW_NUMBER() OVER (PARTITION BY location_sk, trend_date_sk ORDER BY total_jobs DESC) AS rn
  FROM location_metrics
)
SELECT
  lm.location_sk,
  lm.trend_date_sk,
  SUM(lm.total_jobs) AS total_jobs,
  SUM(lm.remote_jobs) AS remote_jobs,
  SUM(lm.onsite_jobs) AS onsite_jobs,
  AVG(lm.avg_salary_usd) AS avg_salary_usd,
  s.sector_name AS top_sector,
  CURRENT_TIMESTAMP() AS updated_at
FROM location_metrics lm
LEFT JOIN top_sector_per_location ts 
  ON lm.location_sk = ts.location_sk 
  AND lm.trend_date_sk = ts.trend_date_sk 
  AND ts.rn = 1
LEFT JOIN workspace.gold.dim_sector s ON ts.sector_sk = s.sector_sk
GROUP BY lm.location_sk, lm.trend_date_sk, s.sector_name

-- End of VIEW definition
