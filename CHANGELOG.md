# Changelog

All notable changes to the LMIP (Labor Market Intelligence Platform) project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive test suite with 114 unit tests across 6 modules
- Notebook integration tests covering all 47 notebooks
- Workflow integration tests for 8 orchestration workflows
- CI/CD pipeline with GitHub Actions
- Pre-commit test checklist and quality gates

### Changed
- Consolidated test documentation into tests/README.md
- Archived migration guides to docs/changelog/
- Updated deployment/README.md with taxonomy table documentation

### Fixed
- Test documentation organization and deduplication

## [1.1.0] - 2026-06-17

### Added
- Four taxonomy tables in metadata layer (taxonomy_sectors, taxonomy_role_families, taxonomy_role_canonical, taxonomy_skill_catalog)
- CSV-to-table seeding logic in bootstrap.py with idempotent MERGE operations
- Gold dimension tables now reference governed taxonomy (dim_sector, dim_role, dim_skill)
- Taxonomy table migration guide (docs/changelog/2026-06-17-taxonomy-tables-migration.md)

### Changed
- bootstrap.py updated with seed_metadata() function (+108 lines)
- DDL execution order includes 4 new taxonomy DDLs
- Gold dimension schemas updated with taxonomy columns

### Fixed
- TABLE_OR_VIEW_NOT_FOUND errors in bootstrap metadata seeding
- Missing DDL files for taxonomy tables
- Schema alignment between CSV files and taxonomy tables

## [1.0.0] - 2026-06-01

### Added
- Complete 6-layer data pipeline architecture (Bronze → Silver → Intermediate → Warehouse → Gold → Publish)
- 56 Unity Catalog tables across all layers
- 47 production notebooks organized by layer
- 8 orchestration workflows with dependency management
- Deployment automation with bootstrap.py (56 DDL files)
- Metadata layer with pipeline control, source config, and taxonomy tables
- Bronze layer with API response logging and batch management
- Silver layer with CDC detection, identity mapping, and DQ validation
- Intermediate layer with canonicalization and skill graph building
- Warehouse layer with SCD2 dimensions and fact tables
- Gold layer with aggregated metrics and business views
- Publish layer with manifest generation and CSV export

### Infrastructure
- Unity Catalog integration (workspace catalog)
- Delta Lake storage format
- Lakeflow orchestration workflows
- Databricks Serverless Compute support
- GitHub integration for version control

### Documentation
- Project README with architecture overview
- Deployment guide (deployment/README.md)
- SQL layer documentation (sql/README.md)
- Data model documentation (docs/Data_Model.md)
- Testing guide (tests/README.md)
- Rollback mechanism documentation (docs/rollback-mechanism.md)

### Testing
- Unit tests for critical pipeline logic (CDC, identity, sector, SCD2, quarantine, manifest)
- Integration tests for all notebooks by layer
- Workflow validation tests
- Test fixtures and shared configuration (tests/conftest.py)

---

## Version History Format

### Types of Changes

* **Added** — New features, files, or capabilities
* **Changed** — Changes in existing functionality
* **Deprecated** — Soon-to-be removed features
* **Removed** — Removed features or files
* **Fixed** — Bug fixes
* **Security** — Security vulnerability fixes

### Version Numbering

* **MAJOR** (X.0.0) — Breaking changes, major architecture shifts
* **MINOR** (x.X.0) — New features, backward-compatible changes
* **PATCH** (x.x.X) — Bug fixes, documentation updates

---

## Migration Guides

For detailed migration guides and breaking changes, see:

* [docs/changelog/2026-06-17-taxonomy-tables-migration.md](docs/changelog/2026-06-17-taxonomy-tables-migration.md) — Taxonomy tables implementation

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines, including:
* Commit message conventions
* Pull request process
* Testing requirements
* Code standards

---

**Note**: For unreleased changes in development, see the `develop` branch commit history. This changelog tracks only released versions and major milestones.
