# LMIP Documentation TODO

## High Priority

### 1. Taxonomy Table Schema Contracts

**Status**: ⏳ PENDING  
**Priority**: HIGH  
**Owner**: Data Engineering Team

**Description**: Create formal schema contracts (YAML) for the four taxonomy tables in the metadata layer.

**Missing Contracts**:
* `contracts/metadata/taxonomy_sectors.yaml`
* `contracts/metadata/taxonomy_role_families.yaml`
* `contracts/metadata/taxonomy_role_canonical.yaml`
* `contracts/metadata/taxonomy_skill_catalog.yaml`

**Current State**:
* Tables are implemented and in production (56 DDL files total)
* Schemas are defined in DDL files (`sql/ddl/metadata_taxonomy_*.sql`)
* Data is seeded from CSV files (`metadata/*.csv`) during bootstrap
* Interim schema documentation exists in migration guide

**Action Items**:
- [ ] Create YAML contract for taxonomy_sectors (19 records)
  - [ ] Document sector hierarchy (parent_sector relationship)
  - [ ] Document NAICS code mappings
  - [ ] Document keyword search patterns
  - [ ] Add data quality rules (required fields, format validations)

- [ ] Create YAML contract for taxonomy_role_families (13 records)
  - [ ] Document sector linkage (sector_key foreign key)
  - [ ] Document family-role relationship
  - [ ] Add description field guidelines

- [ ] Create YAML contract for taxonomy_role_canonical (22 records)
  - [ ] Document role hierarchy (family_key, sector_key foreign keys)
  - [ ] Document seniority enum values
  - [ ] Document alias pipe-delimiter format
  - [ ] Add title normalization rules

- [ ] Create YAML contract for taxonomy_skill_catalog (26 records)
  - [ ] Document skill categories (Technical, Operations, Soft Skill)
  - [ ] Document sector linkage (optional for cross-sector skills)
  - [ ] Document alias pipe-delimiter format
  - [ ] Add skill extraction patterns

- [ ] Update Data_Model.md with contract references
- [ ] Update sql/README.md with contract references
- [ ] Remove contract pending warnings once complete

**References**:
* Current DDL: `sql/ddl/metadata_taxonomy_*.sql`
* CSV Source: `metadata/*.csv`
* Migration Guide: `docs/changelog/2026-06-17-taxonomy-tables-migration.md`
* Existing Contract Template: Use other metadata contracts as reference

**Acceptance Criteria**:
* All four YAML contracts exist in `contracts/metadata/`
* Contracts follow existing LMIP contract format
* Contracts include column definitions, data types, constraints, descriptions
* Contracts include data quality rules
* Contracts document hierarchical relationships
* Contract pending warnings removed from documentation

---

## Medium Priority

### 2. Testing Coverage Validation

**Status**: ⏳ IN PROGRESS  
**Priority**: MEDIUM

**Description**: Measure and document actual test coverage percentages for all modules.

**Action Items**:
- [ ] Run coverage report: `pytest --cov=LMIP --cov-report=html`
- [ ] Update tests/README.md with actual coverage metrics
- [ ] Identify gaps below 70% threshold
- [ ] Add tests for uncovered critical paths

**Target Metrics** (from tests/README.md):
* CDC Hash Logic: 95%+
* Identity Matching: 95%+
* Sector Assignment: 90%+
* SCD2 Key Generation: 90%+
* Quarantine Routing: 85%+
* Export Manifest: 85%+
* Notebooks: 70%+
* Workflows: 70%+

---

## Low Priority

### 3. Architecture Diagram Updates

**Status**: ⏳ PENDING  
**Priority**: LOW

**Description**: Create visual architecture diagrams for the 6-layer pipeline.

**Action Items**:
- [ ] Create layer flow diagram (Bronze → Silver → Intermediate → Warehouse → Gold → Publish)
- [ ] Create taxonomy data flow diagram (CSV → metadata.taxonomy_* → intermediate → gold dimensions)
- [ ] Create SCD2 versioning diagram (dim_job temporal logic)
- [ ] Add diagrams to README.md and docs/Data_Model.md

**Tools**: Mermaid, Draw.io, or similar

---

## Completed

### ✅ Documentation Consolidation (2026-06-20)

* Consolidated 4 test documentation files into tests/README.md
* Archived 3 root-level migration guides to docs/changelog/
* Created CONTRIBUTING.md and CHANGELOG.md
* Added .pytest_cache to .gitignore (already present)
* Flagged missing taxonomy contracts in sql/README.md and Data_Model.md

---

**Last Updated**: 2026-06-20  
**Maintained By**: Data Engineering Team
