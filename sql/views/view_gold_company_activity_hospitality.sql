-- ============================================================================
-- View: workspace.gold.gold_hospitality_companies
-- Layer: GOLD
-- Description: Backward compatibility view for hospitality companies
-- ============================================================================
-- Purpose: Maps old table name to new multi-sector table, filtered to Hospitality
-- Source Table: workspace.gold.gold_company_activity
-- Filter: Hospitality sector only
-- Migration: Created as part of sector generalization migration (Phase 6)
-- ============================================================================

CREATE VIEW workspace.gold.gold_hospitality_companies AS
SELECT
  gca.company_sk,
  gca.active_jobs,
  gca.total_jobs_30d,
  gca.top_role,
  gca.updated_at
FROM workspace.gold.gold_company_activity gca
INNER JOIN workspace.gold.dim_sector s ON gca.sector_sk = s.sector_sk
WHERE s.sector_name IN ('Hospitality', 'Hotels & Resorts', 'Restaurants', 'Food & Beverage')
   OR s.sector_family = 'Hospitality';

-- End of VIEW definition
-- Note: This view provides backward compatibility for applications expecting
-- the old gold_hospitality_companies table structure.
