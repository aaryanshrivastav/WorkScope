# LMIP - Labor Market Information Platform

**Version:** 1.0.0  
**Status:** Active  
**Last Updated:** 2026-06-12

---

## Overview

LMIP is a comprehensive data pipeline that ingests, transforms, and publishes labor market intelligence. The platform processes job postings, salary data, skill trends, and hiring patterns from multiple sources into a curated analytics layer.

**Key Features:**
* Multi-source data ingestion (Bronze layer)
* Standardized transformations (Silver layer)
* Business-ready analytics (Gold layer)
* Automated data quality monitoring
* Multi-channel publishing (CSV, Supabase)
* Reproducible consumer deployments

---

## Architecture

```
Sources (APIs, Scraping)  
       ↓  
Bronze Layer (Raw ingestion)  
       ↓  
Silver Layer (Standardization + Deduplication)  
       ↓  
Intermediate Layer (Enrichment + Canonicalization)
       ↓  
Gold Layer (Star schema with dimensions)  
       ↓  
Reporting Layer (Aggregated analytics)  
       ↓  
Publishing (CSV bundles + Supabase)
```

**See:** [docs/Architecture.md](./docs/Architecture.md) for detailed architecture

---

## Quick Links

### For Data Engineers

* **[docs/Pipeline_Flow.md](./docs/Pipeline_Flow.md)** - End-to-end pipeline flow
* **[docs/Publishing.md](./docs/Publishing.md)** - Internal publishing workflow
* **[docs/Data_Quality_Framework.md](./docs/Data_Quality_Framework.md)** - DQ checks and monitoring
* **[docs/Monitoring_Runbook.md](./docs/Monitoring_Runbook.md)** - Operations and monitoring
* **[docs/Recovery_Runbook.md](./docs/Recovery_Runbook.md)** - Disaster recovery

### For Data Consumers

* **[docs/Publishing_Index.md](./docs/Publishing_Index.md)** - ⭐ Start here: Guide to all publishing docs
* **[docs/Consumer_Bootstrap.md](./docs/Consumer_Bootstrap.md)** - Quick start guide
* **[docs/Publishing_Contracts.md](./docs/Publishing_Contracts.md)** - Formal specification
* **[publish/README.md](./publish/README.md)** - Implementation scripts

### For Data Analysts

* **[docs/Data_Model.md](./docs/Data_Model.md)** - Star schema and table relationships
* **[docs/knowledge_graph_ontology.md](./docs/knowledge_graph_ontology.md)** - Knowledge graph ontology (sector-agnostic labor market model)
* **[docs/Consumer_Bootstrap.md](./docs/Consumer_Bootstrap.md)** - Query examples and patterns

---

## Project Structure

```
LMIP/
├── README.md (this file)
├── docs/
│   ├── Architecture.md
│   ├── Data_Model.md
│   ├── knowledge_graph_ontology.md  (Knowledge graph ontology)
│   ├── Pipeline_Flow.md
│   ├── Data_Quality_Framework.md
│   ├── Publishing_Index.md         (⭐ Publishing docs index)
│   ├── Publishing.md                (Internal workflow)
│   ├── Publishing_Contracts.md      (External spec)
│   ├── Consumer_Bootstrap.md        (Quick start)
│   ├── Monitoring_Runbook.md
│   └── Recovery_Runbook.md
├── contracts/
│   ├── bronze/               (Bronze layer contracts)
│   ├── silver/               (Silver layer contracts)
│   ├── intermediate/         (Intermediate layer contracts)
│   ├── gold/                (Gold layer dimension contracts)
│   ├── reporting/            (Reporting layer contracts)
│   ├── metadata/             (Metadata contracts)
│   ├── audit/                (Audit table contracts)
│   ├── quarantine/           (Quarantine contracts)
│   └── dq/                   (Data quality contracts)
├── notebooks/
│   └── (Pipeline notebooks - TBD)
├── publish/
│   ├── README.md             (Publishing implementation guide)
│   └── scripts/
│       ├── export_bundle.py      (Databricks export)
│       ├── load_bundle.py        (Consumer import)
│       ├── load_dimensions.sql   (Consumer DDL)
│       ├── load_facts.sql        (Consumer DDL)
│       └── validate_import.sql   (Consumer validation)
├── sql/
│   └── (Ad-hoc queries - TBD)
├── workflows/
│   └── (Job definitions - TBD)
├── tests/
│   └── (Test suites - TBD)
└── deployment/
    └── (Deployment configs - TBD)
```

---

## Data Layers

### Bronze Layer
**Purpose:** Raw data ingestion  
**Schema:** `workspace.bronze`  
**Format:** JSON-like structures, minimal transformation

### Silver Layer
**Purpose:** Standardization and deduplication  
**Schema:** `workspace.silver`  
**Format:** Canonical schemas, type-safe

### Intermediate Layer
**Purpose:** Enrichment and canonicalization  
**Schema:** `workspace.intermediate`  
**Format:** Canonical entities and mappings

### Reporting Layer
**Purpose:** Star schema with dimension tables  
**Schema:** `workspace.reporting`  
**Tables:**
* dim_sector
* dim_company
* dim_location
* dim_role
* dim_skill
* dim_source

### Gold Layer
**Purpose:** Business-ready aggregates  
**Schema:** `workspace.gold`  
**Tables:**
* reporting_company_hiring
* reporting_hospitality_companies
* reporting_salary_trends
* reporting_skill_demand
* reporting_location_trends

---

## Publishing

LMIP publishes data through multiple channels:

1. **CSV Bundles** - Versioned, portable archives
2. **Supabase Postgres** - Real-time queryable database
3. **Unity Catalog Volumes** - Internal snapshots

**Start Here:** [docs/Publishing_Index.md](./docs/Publishing_Index.md)

**Versioning:** Semantic versioning (YYYY.WW.PATCH)  
**Schedule:**
* Daily incremental: Monday-Saturday, 02:00 UTC
* Weekly full refresh: Sunday, 04:00 UTC
* Monthly archive: First Sunday, 06:00 UTC

---

## Data Quality

**Framework:** [docs/Data_Quality_Framework.md](./docs/Data_Quality_Framework.md)

**Quality Checks:**
* Completeness (NULL checks, row counts)
* Validity (foreign keys, data types)
* Consistency (cross-table validation)
* Timeliness (freshness checks)

**Quarantine:** Failed records isolated in `workspace.quarantine` schema

---

## Getting Started

### As a Data Consumer

1. Read [docs/Publishing_Index.md](./docs/Publishing_Index.md)
2. Follow [docs/Consumer_Bootstrap.md](./docs/Consumer_Bootstrap.md)
3. Review [docs/Data_Model.md](./docs/Data_Model.md)
4. Download latest bundle or connect to Supabase

### As a Data Engineer

1. Read [docs/Architecture.md](./docs/Architecture.md)
2. Review [docs/Pipeline_Flow.md](./docs/Pipeline_Flow.md)
3. Study layer contracts in `contracts/` directory
4. Set up monitoring per [docs/Monitoring_Runbook.md](./docs/Monitoring_Runbook.md)

### As a Platform Architect

1. Review [docs/Architecture.md](./docs/Architecture.md)
2. Study [docs/Publishing_Contracts.md](./docs/Publishing_Contracts.md)
3. Examine implementation scripts in `publish/scripts/`
4. Design integration following formal specifications

---

## Support

**Data Team:** data-engineering@lmip.org  
**Issues:** GitHub (TBD)  
**Documentation:** Quarterly review cycle  
**On-call:** See [docs/Monitoring_Runbook.md](./docs/Monitoring_Runbook.md)

---

## License

See [LICENSE](./LICENSE)

---

**Last Updated:** 2026-06-12  
**Document Owner:** LMIP Platform Engineering Team