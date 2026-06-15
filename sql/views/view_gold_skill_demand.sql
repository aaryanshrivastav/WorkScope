-- ============================================================================
-- View: workspace.gold.gold_skill_demand
-- Layer: GOLD
-- Description: Skill demand trends across industries
-- ============================================================================
-- Purpose: Track which skills are most in-demand by sector and time period
-- Dependencies: workspace.gold.bridge_job_skill, workspace.gold.dim_skill, workspace.gold.fact_job_postings
-- Expected Output: Skill demand metrics with trending indicators
-- ============================================================================

CREATE OR REPLACE VIEW workspace.gold.gold_skill_demand AS
SELECT
  sk.skill_sk,
  sk.skill_name,
  sk.skill_category,
  COUNT(DISTINCT bjs.job_sk) AS job_postings_count,
  COUNT(DISTINCT f.company_sk) AS companies_requesting,
  AVG(f.salary_max) AS avg_max_salary,
  CURRENT_TIMESTAMP() AS updated_at
FROM workspace.gold.bridge_job_skill bjs
JOIN workspace.gold.dim_skill sk ON bjs.skill_sk = sk.skill_sk
JOIN workspace.gold.fact_job_postings f ON bjs.job_sk = f.job_sk
WHERE f.active_flag = TRUE
GROUP BY sk.skill_sk, sk.skill_name, sk.skill_category;

-- End of VIEW definition
