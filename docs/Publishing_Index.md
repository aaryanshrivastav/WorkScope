# LMIP Publishing Documentation Index

**Last Updated:** 2026-06-12

---

## Overview

LMIP distributes labor market data through multiple channels to serve different consumer needs. This index guides you to the right documentation for your role and use case.

---

## Documentation by Audience

### For Data Engineers (Internal)

**[Publishing.md](./Publishing.md)** - Internal Publishing Workflow
* Unity Catalog Volume exports
* Supabase synchronization
* CSV compression and checksums
* Monitoring and troubleshooting
* Infrastructure and secrets

**Use this when:**
* Operating the publishing pipeline
* Debugging export failures
* Modifying the sync workflow
* Setting up monitoring

---

### For Data Consumers (External)

**[Consumer_Bootstrap.md](./Consumer_Bootstrap.md)** - Quick Start Guide
* CSV file access patterns
* Supabase connection examples
* Schema reference
* Code examples (Python, SQL, JavaScript, R)

**Use this when:**
* First-time setup
* Learning available tables
* Writing consumer applications
* Quick queries and analysis

---

### For Platform Architects & Integration Teams

**[Publishing_Contracts.md](./Publishing_Contracts.md)** - Formal Specification
* Export order and dependency graph
* Versioning strategy (YYYY.WW.PATCH)
* Manifest schema specification
* CSV bundle structure
* Incremental publishing strategy
* Disaster recovery procedures
* Quality gates and validation

**Use this when:**
* Designing downstream systems
* Planning integrations
* Implementing consumer loaders
* Setting up automated ingestion
* Building reproducible deployments

---

## Implementation Artifacts

### Producer Side (Databricks)

**[../publish/scripts/export_bundle.py](../publish/scripts/export_bundle.py)**
* Full and incremental export modes
* Manifest generation
* Checksum calculation
* PySpark-based CSV export

**Usage:**
```bash
python export_bundle.py \
  --catalog workspace \
  --gold-schema gold \
  --gold-schema gold \
  --output /dbfs/mnt/lmip-exports \
  --mode full
```

---

### Consumer Side (PostgreSQL/Supabase)

**[../publish/scripts/load_bundle.py](../publish/scripts/load_bundle.py)**
* Bundle validation (checksums, row counts)
* Full refresh mode (truncate + reload)
* Incremental mode (upsert + append)
* Transaction safety

**[../publish/scripts/load_dimensions.sql](../publish/scripts/load_dimensions.sql)**
* DDL for 6 dimension tables
* Primary keys, indexes, constraints

**[../publish/scripts/load_facts.sql](../publish/scripts/load_facts.sql)**
* DDL for 5 gold fact tables
* Foreign keys, indexes
* version_history tracking table

**[../publish/scripts/validate_import.sql](../publish/scripts/validate_import.sql)**
* Referential integrity checks
* NULL constraint validation
* Date range validation
* Data quality checks

**Usage:**
```bash
# Validate bundle
python scripts/load_bundle.py --validate-only --manifest manifest.json

# Create schema (first time)
psql $DATABASE_URL -f scripts/load_dimensions.sql
psql $DATABASE_URL -f scripts/load_facts.sql

# Load data
python scripts/load_bundle.py \
  --database-url $DATABASE_URL \
  --manifest manifest.json \
  --mode full

# Validate import
psql $DATABASE_URL -f scripts/validate_import.sql
```

---

## Quick Reference

### Publishing Architecture Comparison

| Aspect | Internal (Publishing.md) | External (Publishing_Contracts.md) |
|--------|-------------------------|------------------------------------|
| **Target** | Unity Catalog Volumes + Supabase | Portable CSV bundles |
| **Versioning** | Timestamp filenames | Semantic versioning (YYYY.WW.PATCH) |
| **Checksums** | MD5 | SHA256 |
| **Consumer Access** | Requires Databricks or Supabase | Fully reproducible offline |
| **Manifest** | Per-table JSON | Comprehensive bundle manifest |
| **Incremental** | Full upsert only | UPSERT dimensions + append facts |
| **Recovery** | Troubleshooting guide | Disaster recovery procedures |

---

### Data Tables Overview

**Dimensions (6 tables)**
* dim_sector - Industry sectors
* dim_company - Companies
* dim_location - Geographic locations
* dim_role - Job roles
* dim_skill - Skills
* dim_source - Data sources

**Gold Facts (5 tables)**
* gold_company_hiring - Company hiring activity
* gold_company_activity - Company activity metrics by sector
* gold_salary_trends - Salary analytics
* gold_skill_demand - Skill demand trends
* gold_location_trends - Geographic job market trends

---

## Decision Tree: Which Doc Do I Need?

```
Start here:
└─ Are you operating the LMIP platform?
    ├─ YES → Publishing.md (internal workflow)
    └─ NO → Are you consuming data for analysis/dashboards?
        ├─ YES → Consumer_Bootstrap.md (quick start)
        └─ NO → Are you building an integration or downstream system?
            ├─ YES → Publishing_Contracts.md (formal spec)
            └─ NO → Start with Consumer_Bootstrap.md
```

---

## Related Documentation

* [Architecture.md](./Architecture.md) - Overall LMIP system architecture
* [Data_Model.md](./Data_Model.md) - Star schema and table relationships
* [Recovery_Runbook.md](./Recovery_Runbook.md) - General disaster recovery procedures
* [Monitoring_Runbook.md](./Monitoring_Runbook.md) - Monitoring and alerting

---

## Support

**Issues:** GitHub (TBD)  
**Contact:** data-engineering@lmip.org  
**Documentation Updates:** Quarterly review cycle

---

**Document Owner:** LMIP Platform Engineering Team