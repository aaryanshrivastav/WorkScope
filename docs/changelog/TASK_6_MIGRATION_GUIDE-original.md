# Task 6 Migration Guide: Gold Dimension Tables & Sector Taxonomy

**Migration Date**: June 2026  
**Status**: ✅ DDL FILES COMPLETE | 🔄 NOTEBOOKS IN PROGRESS  

## Summary

Updated gold layer dimension tables (dim_sector, dim_role, dim_skill) to reflect the governed sector taxonomy from workspace.metadata tables.

### Files Modified
- ✅ gold_dim_sector.sql - Added taxonomy columns
- ✅ gold_dim_role.sql - Added taxonomy columns
- ✅ gold_dim_skill.sql - Added taxonomy columns
- 🔄 gold_dim_sector.ipynb - Updating loader (IN PROGRESS)
- ⏳ gold_dim_role.ipynb - Pending
- ⏳ gold_dim_skill.ipynb - Pending

### Key Schema Changes
All three dimensions now include:
- Natural keys from taxonomy (sector_key, role_key, skill_key)
- Cross-references to taxonomy hierarchy
- Audit timestamps (updated_at, taxonomy_updated_at)

See full details in README sections below.
