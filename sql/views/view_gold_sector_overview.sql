-- ============================================================================
-- View: workspace.gold.gold_sector_overview
-- Layer: GOLD
-- Description: Sector-level overview with key metrics and trends
-- ============================================================================
-- Purpose: Gold analytical view for gold_sector_overview
-- Dependencies: workspace.gold.fact_job_postings, workspace.gold.fact_salary
-- Expected Output: Aggregated metrics with 8 columns
-- ============================================================================

CREATE OR REPLACE VIEW workspace.gold.gold_sector_overview AS
WITH sector_jobs AS (
  SELECT
    f.sector_sk,
    f.posting_date_sk AS overview_date_sk,
    COUNT(DISTINCT f.job_sk) AS total_jobs,
    COUNT(DISTINCT f.company_sk) AS total_companies
  FROM workspace.gold.fact_job_postings f
  WHERE f.active_flag = TRUE
  GROUP BY f.sector_sk, f.posting_date_sk
),
sector_salaries AS (
  SELECT
    fs.sector_sk,
    AVG(fs.salary_max) AS avg_salary_usd
  FROM workspace.gold.fact_salary fs
  WHERE fs.is_current = TRUE
  GROUP BY fs.sector_sk
),
top_skills_by_sector AS (
  SELECT
    f.sector_sk,
    sk.skill_name,
    COUNT(*) AS skill_count,
    ROW_NUMBER() OVER (PARTITION BY f.sector_sk ORDER BY COUNT(*) DESC) AS rn
  FROM workspace.gold.fact_job_postings f
  JOIN workspace.gold.bridge_job_skill bjs ON f.job_sk = bjs.job_sk
  JOIN workspace.gold.dim_skill sk ON bjs.skill_sk = sk.skill_sk
  WHERE f.active_flag = TRUE
  GROUP BY f.sector_sk, sk.skill_name
),
skills_array AS (
  SELECT
    sector_sk,
    COLLECT_LIST(skill_name) AS top_skills
  FROM top_skills_by_sector
  WHERE rn <= 10
  GROUP BY sector_sk
),
growth_calc AS (
  SELECT
    sector_sk,
    posting_date_sk,
    total_jobs,
    LAG(total_jobs, 30) OVER (PARTITION BY sector_sk ORDER BY posting_date_sk) AS jobs_30d_ago
  FROM sector_jobs
)
SELECT
  sj.sector_sk,
  sj.overview_date_sk,
  sj.total_jobs,
  sj.total_companies,
  ss.avg_salary_usd,
  sa.top_skills,
  CASE 
    WHEN gc.jobs_30d_ago > 0 
    THEN ((gc.total_jobs - gc.jobs_30d_ago) * 100.0 / gc.jobs_30d_ago)
    ELSE NULL
  END AS growth_rate_30d,
  CURRENT_TIMESTAMP() AS updated_at
FROM sector_jobs sj
LEFT JOIN sector_salaries ss ON sj.sector_sk = ss.sector_sk
LEFT JOIN skills_array sa ON sj.sector_sk = sa.sector_sk
LEFT JOIN growth_calc gc ON sj.sector_sk = gc.sector_sk AND sj.overview_date_sk = gc.posting_date_sk

-- End of VIEW definition
