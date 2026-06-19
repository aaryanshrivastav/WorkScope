# LMIP Metadata - Sector-Agnostic Taxonomy

## Purpose

This directory contains **governed taxonomies** for sectors, roles, and skills. These files replace hardcoded dictionaries in intermediate notebooks and enable the platform to be **sector-agnostic** from day one.

## Architecture

```
Sector
  ↓
Role Family
  ↓
Canonical Role
  ↓
Skill Category
  ↓
Canonical Skill
```

## Files

### sectors.csv
Defines the sector hierarchy and keywords for classification.

**Columns**:
* `sector_key`: Unique identifier (e.g., `TECH`, `HOSP`, `HEAL`)
* `sector_name`: Display name (e.g., `Technology`, `Hospitality`, `Healthcare`)
* `parent_sector`: Parent sector key for hierarchical rollup (null for top-level)
* `naics_code`: NAICS code mapping
* `keywords`: Pipe-delimited keywords for sector matching

**Usage**: Load in `inter_sector_normalize` to replace hardcoded NAICS samples.

### role_families.csv
Defines role families within each sector.

**Columns**:
* `family_key`: Unique identifier (e.g., `ENG`, `HOSP_OPS`, `CLIN_CARE`)
* `family_name`: Display name (e.g., `Engineering`, `Hospitality Operations`, `Clinical Care`)
* `sector_key`: Parent sector
* `description`: Family description

**Usage**: Creates the intermediate layer between sectors and roles.

### canonical_roles.csv
Defines canonical role names and their aliases.

**Columns**:
* `role_key`: Unique identifier (e.g., `ENG_SWE`, `HOSP_MANAGER`)
* `canonical_role`: Standard role name (e.g., `Software Engineer`, `Hotel Manager`)
* `family_key`: Parent role family
* `sector_key`: Parent sector
* `seniority`: Seniority level (`junior`, `mid`, `senior`, `executive`)
* `aliases`: Pipe-delimited role aliases for matching

**Usage**: Load in `inter_role_map` to replace hardcoded role dictionary.

### canonical_skills.csv
Defines canonical skill names and their aliases.

**Columns**:
* `skill_key`: Unique identifier (e.g., `TECH_PYTHON`, `HOSP_REV_MGT`)
* `canonical_skill`: Standard skill name (e.g., `Python`, `Revenue Management`)
* `skill_category`: Category (`Technical`, `Operations`, `Clinical`, `Finance`, `Soft Skill`)
* `sector_key`: Primary sector (null for cross-sector soft skills)
* `aliases`: Pipe-delimited skill aliases for matching

**Usage**: Load in `inter_skill_catalog_sync` to replace hardcoded skill lists.

## Current State

**Platform Capacity**:
```
Technology       ██████████  (Fully populated from Remotive/ArbeitNow)
Hospitality      ██░░░░░░░░  (Structurally defined, awaiting data sources)
Healthcare       ██░░░░░░░░  (Structurally defined, awaiting data sources)
Finance          ██░░░░░░░░  (Structurally defined, awaiting data sources)
Retail           ██░░░░░░░░  (Structurally defined, awaiting data sources)
Manufacturing    ██░░░░░░░░  (Structurally defined, awaiting data sources)
Education        ██░░░░░░░░  (Structurally defined, awaiting data sources)
Government       ██░░░░░░░░  (Structurally defined, awaiting data sources)
```

**This is acceptable**. The problem would be designing the platform **only for Technology**.

## How to Extend

### Adding a New Sector

1. Add top-level sector to `sectors.csv`:
   ```csv
   sector_key,sector_name,parent_sector,naics_code,keywords
   LEGAL,Legal,,54,"legal|law|attorney|paralegal"
   ```

2. Add subsectors (optional):
   ```csv
   LEGAL_CORP,Corporate Law,LEGAL,5411,"corporate law|business law|contracts"
   LEGAL_LIT,Litigation,LEGAL,5411,"litigation|trial|courtroom"
   ```

3. Add role families to `role_families.csv`:
   ```csv
   family_key,family_name,sector_key,description
   LEGAL_ATTY,Attorneys,LEGAL,"Licensed legal practitioners"
   LEGAL_PARA,Paralegals,LEGAL,"Legal support and research roles"
   ```

4. Add canonical roles to `canonical_roles.csv`:
   ```csv
   role_key,canonical_role,family_key,sector_key,seniority,aliases
   LEGAL_ATTY_SR,Senior Attorney,LEGAL_ATTY,LEGAL,senior,"senior attorney|partner|counsel"
   ```

5. Add sector-specific skills to `canonical_skills.csv`:
   ```csv
   skill_key,canonical_skill,skill_category,sector_key,aliases
   LEGAL_CONTRACTS,Contract Law,Legal,LEGAL,"contracts|contract law|commercial law"
   ```

### Adding Skills to Existing Sectors

Simply append to `canonical_skills.csv`:
```csv
TECH_RUST,Rust,Technical,TECH,"rust|rust language"
HOSP_OPERA,Opera PMS,Technical,HOSP,"opera|opera pms|property management"
```

## Key Principles

1. **Technology is not special** - it's one sector among many
2. **Metadata-driven** - add sectors/roles/skills via CSV rows, not code changes
3. **Hierarchical** - sectors → families → roles → skills
4. **Alias-aware** - canonical names with multiple aliases for matching
5. **Current data bias is acceptable** - Remotive/ArbeitNow are tech-heavy, that's fine
6. **Platform design must be agnostic** - the ontology supports all sectors equally

## Next Steps

### Before Writing More Intermediate Code

1. ✅ Create metadata files (sectors, roles, skills)
2. ✅ Create metadata loader notebook
3. ✅ Refactor `inter_sector_normalize` to load from `workspace.metadata.taxonomy_sectors` table
4. ✅ Refactor `inter_role_map` to load from `workspace.metadata.taxonomy_role_canonical` table
5. ✅ Refactor `inter_skill_catalog_sync` to load from `workspace.metadata.taxonomy_skill_catalog` table
6. 🔄 Update dim tables in gold layer to reflect sector taxonomy (IN PROGRESS - DDL files complete, notebooks updating)
7. ⬜ Design Knowledge Graph ontology using this taxonomy

### Data Source Strategy

Your current sources (Remotive, ArbeitNow) are tech-heavy. That's fine.

**Do NOT**:
* Redesign the platform around tech
* Remove non-tech sectors from metadata
* Build tech-specific intermediate logic

**DO**:
* Keep the sector-agnostic metadata
* Let Technology be the first fully populated sector
* Plan for future data sources (Indeed, LinkedIn, sector-specific boards)
* Ensure all intermediate logic works for any sector when data arrives

## Benefits

1. **Knowledge Graph ready** - the ontology is already defined
2. **Scalable** - add sectors without refactoring
3. **Governed** - single source of truth for canonical names
