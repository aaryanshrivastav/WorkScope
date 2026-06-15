-- ============================================================================
-- View: workspace.gold.gold_hospitality_hiring
-- Layer: GOLD
-- Description: Backward compatibility view for hospitality hiring trends
-- ============================================================================
-- Purpose: Maps old table name to new multi-sector table, filtered to Hospitality
-- Source Table: workspace.gold.gold_hiring_activity
-- Filter: Hospitality sector only
-- Migration: Created as part of sector generalization migration (Phase 6)
-- ============================================================================

CREATE VIEW workspace.gold.gold_hospitality_hiring AS
SELECT
  gha.hiring_date_sk,
  gha.total_jobs,
  gha.new_jobs,
  gha.top_role,
  gha.avg_salary,
  gha.updated_at
FROM workspace.gold.gold_hiring_activity gha
INNER JOIN workspace.gold.dim_sector s ON gha.sector_sk = s.sector_sk
WHERE s.sector_name IN ('Hospitality', 'Hotels & Resorts', 'Restaurants', 'Food & Beverage')
   OR s.sector_family = 'Hospitality';

-- End of VIEW definition
-- Note: This view provides backward compatibility for applications expecting
-- the old gold_hospitality_hiring table structure.
