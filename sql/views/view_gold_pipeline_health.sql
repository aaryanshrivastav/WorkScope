-- ============================================================================
-- View: workspace.gold.gold_pipeline_health
-- Layer: GOLD
-- Description: Data pipeline health metrics and monitoring dashboard data
-- ============================================================================
-- Purpose: Gold analytical view for gold_pipeline_health
-- Dependencies: workspace.gold.fact_pipeline_runs, workspace.gold.fact_job_lifecycle
-- Expected Output: Aggregated metrics with 9 columns
-- ============================================================================

CREATE OR REPLACE VIEW workspace.gold.gold_pipeline_health AS
SELECT
  pr.run_date_sk AS health_date_sk,
  pr.pipeline_name,
  COUNT(*) AS total_runs,
  COUNT(CASE WHEN pr.run_status = 'SUCCESS' THEN 1 END) AS successful_runs,
  COUNT(CASE WHEN pr.run_status = 'FAILED' THEN 1 END) AS failed_runs,
  AVG(pr.duration_seconds) AS avg_duration_seconds,
  SUM(pr.records_processed) AS total_records_processed,
  CAST(COUNT(CASE WHEN pr.run_status = 'SUCCESS' THEN 1 END) AS DECIMAL(10,4)) / NULLIF(COUNT(*), 0) AS success_rate,
  CURRENT_TIMESTAMP() AS updated_at
FROM workspace.gold.fact_pipeline_runs pr
GROUP BY pr.run_date_sk, pr.pipeline_name

-- End of VIEW definition
