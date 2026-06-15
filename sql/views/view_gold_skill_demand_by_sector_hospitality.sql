-- ============================================================================
-- View: workspace.gold.gold_hospitality_skills
-- Layer: GOLD
-- Description: Backward compatibility view for hospitality skill demand
-- ============================================================================
-- Purpose: Maps old table name to new multi-sector table, filtered to Hospitality
-- Source Table: workspace.gold.gold_skill_demand_by_sector
-- Filter: Hospitality sector only
-- Migration: Created as part of sector generalization migration (Phase 6)
-- ============================================================================

CREATE VIEW workspace.gold.gold_hospitality_skills AS
SELECT
  gsds.skill_sk,
  gsds.trend_date_sk,
  gsds.job_count,
  gsds.demand_rank,
  gsds.growth_rate,
  gsds.updated_at
FROM workspace.gold.gold_skill_demand_by_sector gsds
INNER JOIN workspace.gold.dim_sector s ON gsds.sector_sk = s.sector_sk
WHERE s.sector_name IN ('Hospitality', 'Hotels & Resorts', 'Restaurants', 'Food & Beverage')
   OR s.sector_family = 'Hospitality';

-- End of VIEW definition
-- Note: This view provides backward compatibility for applications expecting
-- the old gold_hospitality_skills table structure.
