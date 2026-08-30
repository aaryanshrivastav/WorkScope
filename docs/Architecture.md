# LMIP Architecture Reference

**Last Updated**: 2026-06-20  
**Target**: Solo Maintainer Reference  
*(Full legacy architecture doc preserved at [archive/Architecture_legacy.md](archive/Architecture_legacy.md))*

---

## High-Level Architecture Overview

LMIP (Labor Market Intelligence Platform) is a Databricks-first data platform that ingests, cleanses, enriches, models, and publishes job posting data from external REST APIs (Remotive, Arbeitnow).

```
┌──────────────┐     ┌──────────────┐     ┌──────────────────┐     ┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│ External APIs│ ──► │ Bronze Layer │ ──► │   Silver Layer   │ ──► │ Intermediate │ ──► │    Gold Layer    │ ──► │  Reporting   │
│ (Remotive/   │     │ (Immutable   │     │   (Cleansed,     │     │ (Taxonomies &│     │ (Kimball Star    │     │  (Pre-agg    │
│  Arbeitnow)  │     │  Snapshots)  │     │    CDC, DQ)      │     │  Entity Map) │     │     Schema)      │     │   BI Marts)  │
└──────────────┘     └──────────────┘     └──────────────────┘     └──────────────┘     └──────────────────┘     └──────────────┘
                                                                                                                        │
                                                                                                                        ▼
                                                                                                                 ┌──────────────┐
                                                                                                                 │Publish/Export│
                                                                                                                 │(CSV & Supabase)
                                                                                                                 └──────────────┘
```

---

## 9-Schema Unity Catalog Structure

All schemas reside in the `workspace` Unity Catalog catalog:

| Schema | Purpose | Key Tables |
|--------|---------|------------|
| **`metadata`** | Control configurations & governed taxonomies | `source_config`, `pipeline_run_control`, `taxonomy_sectors`, `taxonomy_role_canonical`, `taxonomy_skill_catalog` |
| **`bronze`** | Raw immutable API response payloads | `bronze_job_snapshot`, `bronze_api_response_log` |
| **`silver`** | Cleansed, deduplicated job postings & audit log | `silver_jobs_current`, `silver_job_changes`, `silver_skill_mapping` |
| **`intermediate`** | Canonical mapping tables & entity resolution | `inter_job_role_map`, `inter_company_canonical`, `inter_skill_catalog` |
| **`gold`** | Star schema dimensional model (Kimball) | `dim_job`, `dim_company`, `dim_role`, `dim_skill`, `dim_sector`, `fact_job_postings`, `fact_salary` |
| **`reporting`** | Pre-aggregated business KPIs & analytics marts | `reporting_salary_trends`, `reporting_skill_demand`, `reporting_hiring_trends`, `reporting_sector_overview` |
| **`audit`** | Operational logs & compliance audits | `audit_pipeline_runs`, `audit_dq_results`, `audit_access_events` |
| **`publish`** | Published export metadata & tracking | `publish_manifest`, `publish_export_log` |
| **`quarantine`** | Rejected/invalid data for investigation | `quarantine_jobs` |

---

## Compute & Deployment Strategy

- **Compute Platform**: Databricks Serverless Compute / Single-Node SQL Warehouse.
- **Infrastructure Provisioning**: Single-command bootstrapping via `python deployment/bootstrap.py --catalog workspace`.
- **Orchestration Workflows**: 5 Databricks Workflows (`LMIPDataIngestion`, `LMIPSilverProcessing`, `LMIPIntermediateProcessing`, `LMIPGoldBuild`, `publishing`).
- **Data Validation & Quality**: Delta expectation checks + `quarantine_jobs` quarantine routing.
