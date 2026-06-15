# LMIP Architecture Documentation

**Document Version**: 1.0  
**Last Updated**: 2026-06-12  
**Target Audience**: Engineering teams, architects, platform operators

---

## Executive Summary

**LMIP (Labor Market Intelligence Platform)** is a Databricks-first data platform that ingests, transforms, and publishes labor market data from multiple external job posting APIs. The platform implements a **medallion architecture** with semantic enrichment, dimensional modeling, and pre-aggregated analytics marts.

### Key Characteristics

* **Cloud-Native**: 100% Databricks serverless compute
* **Medallion Pattern**: Bronze → Silver → Intermediate → Gold → Reporting
* **Data Sources**: External job APIs (Remotive, Arbeitnow)
* **Target Catalog**: `workspace` (Unity Catalog)
* **Orchestration**: Databricks Workflows with file-arrival triggers
* **Data Volume**: ~100-150 job postings per hour, ~2,500-3,000 per day
* **Latency**: End-to-end pipeline completes in 6-8 hours

---

## System Architecture

### High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  EXTERNAL SOURCES                                               │
│  • Remotive API (remotive.com)                                  │
│  • Arbeitnow API (arbeitnow.com)                                │
└──────────────────────┬──────────────────────────────────────────┘
                       │ HTTP/REST APIs
                       │ Hourly Ingestion
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  BRONZE LAYER (Raw Ingestion)                                   │
│  • Immutable snapshot storage                                   │
│  • JSON payload preservation                                    │
│  Tables: bronze_job_snapshot, bronze_api_response_log           │
└──────────────────────┬──────────────────────────────────────────┘
                       │ Standardization
                       │ Change Data Capture
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  SILVER LAYER (Cleansed & Validated)                            │
│  • Schema enforcement                                           │
│  • Data quality validation                                      │
│  • Skill extraction, sector assignment                          │
│  Tables: silver_jobs_current, silver_job_changes                │
└──────────────────────┬──────────────────────────────────────────┘
                       │ Canonicalization
                       │ Entity Resolution
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  INTERMEDIATE LAYER (Enriched)                                      │
│  • Role taxonomy mapping                                        │
│  • Company canonicalization                                     │
│  • Sector normalization                                         │
│  • Skill graph construction                                     │
│  Tables: sem_job_role_map, sem_company_map, sem_skill_catalog   │
└──────────────────────┬──────────────────────────────────────────┘
                       │ Dimensional Modeling
                       │ Star Schema
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  GOLD LAYER (Star Schema)                                  │
│  • Kimball dimensional model                                    │
│  • SCD Type 2 for job dimension                                 │
│  • 9 dimensions, 4 facts, 1 bridge                             │
│  Tables: dim_*, fact_*, bridge_*                                │
└──────────────────────┬──────────────────────────────────────────┘
                       │ Aggregation
                       │ BI Marts
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  REPORTING LAYER (Analytics Marts)                                   │
│  • Pre-aggregated metrics                                       │
│  • Dashboard-ready tables                                       │
│  • Time-series trends                                           │
│  Tables: reporting_salary_trends, reporting_skill_demand, reporting_hiring_*   │
└──────────────────────┬──────────────────────────────────────────┘
                       │ Export
                       │ Publishing
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  PUBLISHING LAYER                                               │
│  • CSV snapshots                                                │
│  • External databases (Supabase Postgres)                       │
│  • API endpoints                                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Architectural Layers

### 1. Bronze Layer: Raw Ingestion

**Purpose**: Capture complete, unmodified API responses as immutable snapshots

**Key Principles**:
* **Append-Only**: Never update or delete records
* **Schema-on-Read**: Store flexible JSON payloads
* **Full Lineage**: Track every snapshot to its ingestion batch
* **Payload Preservation**: Store complete API response for reprocessing

**Tables**:
* `workspace.bronze.bronze_job_snapshot` - Raw API responses with metadata
* `workspace.bronze.bronze_api_response_log` - API telemetry (status, timing, rate limits)
* `workspace.bronze.dedupe_tracking` - Duplicate detection records
* `workspace.bronze.batch_metadata` - Batch completion metadata

**Key Operations**:
1. API ingestion from multiple sources (parallel)
2. Payload hashing (SHA-256) for deduplication
3. Batch ID generation and tracking
4. API response logging
5. Deduplication tracking (non-blocking)

**Failure Modes**:
* API unavailable/timeout: Retry with exponential backoff
* Rate limiting: Respect API quotas, queue requests
* Partial data: Capture what's available, log failures

---

### 2. Silver Layer: Standardization & Quality Control

**Purpose**: Transform raw bronze data into clean, validated, standardized job postings

**Key Principles**:
* **Idempotency**: All notebooks can be re-run safely
* **Change Data Capture (CDC)**: Track INSERTs, UPDATEs, DELETEs, RESTOREs
* **Data Quality Validation**: Route failures to quarantine
* **Graceful Degradation**: Low-confidence items queue for review

**Tables**:
* `workspace.silver.silver_jobs_staging` - Staging area for batch processing
* `workspace.silver.silver_jobs_current` - Current snapshot of all job postings
* `workspace.silver.silver_job_changes` - Audit trail of all job changes
* `workspace.silver.silver_skill_mapping` - Skills extracted from job descriptions
* `workspace.silver.silver_job_identity_map` - Canonical job identity mapping
* `workspace.silver.silver_intermediate_review_queue` - Low-confidence records for review

**Key Operations**:
1. **Standardization**: Normalize company names, titles, locations
2. **CDC Detection**: Hash-based change detection
3. **Soft Delete/Restore**: Handle job expiration and reappearance
4. **Data Quality Validation**: Completeness, uniqueness, referential integrity
5. **Skill Extraction**: Keyword-based and NLP extraction
6. **Sector Assignment**: Rule-based and ML-based classification
7. **Identity Mapping**: Cross-source job deduplication

**Failure Modes**:
* Schema violations: Quarantine records for manual review
* DQ failures: Route to quarantine with remediation instructions
* Skill extraction failures: Continue with NULL values, flag for review

---

### 3. Intermediate Layer: Enrichment & Canonicalization

**Purpose**: Map raw values to canonical business entities using hybrid matching (rules + ML)

**Key Principles**:
* **Hybrid Matching**: Dictionary → Regex → Optional LLM fallback
* **Confidence Scoring**: Route low-confidence matches to review queue
* **Human-in-the-Loop**: Review resolver applies human feedback
* **Deterministic-First**: Prefer rules over ML for predictability

**Tables**:
* `workspace.intermediate.sem_job_role_map` - Job title → canonical role
* `workspace.intermediate.sem_company_map` - Company name → canonical entity
* `workspace.intermediate.sem_sector_map` - Industry sector normalization
* `workspace.intermediate.sem_skill_catalog` - Canonical skill taxonomy
* `workspace.intermediate.sem_skill_graph` - Skill relationships (co-occurrence, prerequisite)

**Key Operations**:
1. **Role Mapping**: Dictionary → Regex → LLM fallback (optional)
2. **Company Canonicalization**: Exact → Alias → Fuzzy match (Levenshtein)
3. **Sector Normalization**: Map to NAICS/GICS/SIC taxonomies
4. **Skill Catalog Sync**: Update canonical skill taxonomy
5. **Skill Graph Build**: Co-occurrence, prerequisite, similarity edges
6. **Review Resolution**: Apply human feedback to improve future matches

**Failure Modes**:
* Low-confidence matches: Route to review queue
* LLM timeout: Fallback to NULL value, flag for review
* Ambiguous mappings: Route to review with context

---

### 4. Gold Layer: Dimensional Model (Star Schema)

**Purpose**: Implement Kimball-style star schema for BI and analytics

**Key Principles**:
* **Conformed Dimensions**: Shared across all facts
* **SCD Type 2**: Historical tracking for job dimension
* **Surrogate Keys**: Stable integer keys decoupled from business keys
* **Time Travel Joins**: SCD2 effective date windows

**Dimensions (9)**:
* `dim_date` (Type 1) - Calendar attributes, fiscal periods
* `dim_source` (Type 1) - Data source systems
* `dim_company` (Type 1) - Canonical company entities
* `dim_company_alias` (Type 1) - Company name variations
* `dim_location` (Type 1) - Geographic hierarchy
* `dim_sector` (Type 1) - Industry sectors
* `dim_skill` (Type 1) - Skills catalog
* `dim_role` (Type 1) - Canonical job roles
* `dim_job` (Type 2) - Job postings with history (SCD2)

**Facts (4)**:
* `fact_job_postings` - Core transactional facts (one row per job posting event)
* `fact_job_lifecycle` - Job state changes (one row per transition)
* `fact_salary` - Salary observations (one row per job with salary)
* `fact_pipeline_runs` - ETL operational metrics

**Bridge (1)**:
* `bridge_job_skill` - Many-to-many job-skill relationships with confidence scores

**Execution Order**:
1. **Phase 1**: Load conformed dimensions (parallel, no dependencies)
2. **Phase 2**: Load company dimensions (sequential: company → alias)
3. **Phase 3**: Load SCD2 job dimension (requires all Phase 1 & 2)
4. **Phase 4**: Load bridge tables (requires dim_job, dim_skill)
5. **Phase 5**: Load fact tables (parallel, requires respective dimensions)

**Failure Modes**:
* Dimension load failures: Block downstream fact loading
* Foreign key resolution failures: Use -1 placeholder for unknown
* SCD2 history corruption: Rebuild from silver layer

---

### 5. Reporting Layer: Analytics Marts

**Purpose**: Pre-aggregated, dashboard-ready business metrics

**Key Principles**:
* **Denormalized for Performance**: Dimensional attributes embedded
* **Pre-Aggregated**: Rollups computed at ingestion, not query time
* **Temporal Optimization**: Window functions for trending
* **Multiple Grain Levels**: Drill-down capability (total → sector → role → location)

**Tables**:
* `reporting_salary_trends` - Salary analytics with percentile distributions
* `reporting_skill_demand` - Skill demand trends and co-occurrence
* `reporting_hiring_trends` - Job posting velocity and hiring activity
* `gold_company_hiring` - Company-level hiring metrics
* `gold_location_trends` - Geographic hiring trends
* `gold_sector_overview` - Sector-level aggregations
* `gold_pipeline_health` - Operational monitoring
* `gold_company_activity` - Company hiring activity by sector
* `reporting_hiring_activity` - Sector-aware hiring trends
* `reporting_skill_demand_by_sector` - Skill demand analysis by sector

**Key Metrics**:
* Salary percentiles (P25, P50, P75, P90)
* Month-over-month and quarter-over-quarter changes
* Skill co-occurrence rankings
* Hiring velocity indicators
* Data quality and pipeline health metrics

**Failure Modes**:
* Aggregation failures: Retry or fallback to gold layer queries
* Empty rollup groups: Filter for minimum observation counts
* Performance degradation: Optimize/ZORDER tables

---

### 6. Publishing Layer

**Purpose**: Export data to external consumers and systems

**Key Principles**:
* **Consumer-Specific Formats**: CSV snapshots, Postgres tables, APIs
* **Incremental Publishing**: Only export changed data
* **Manifest Tracking**: Log all published datasets
* **Error Recovery**: Retry failed exports with exponential backoff

**Outputs**:
* CSV snapshots in Unity Catalog Volumes
* Supabase Postgres tables (external database)
* REST API endpoints (future)

**Tables**:
* `workspace.publish.publish_manifest` - Published dataset manifest
* `workspace.publish.publish_export_log` - Export execution log

**Failure Modes**:
* Export failures: Retry with backoff, alert on repeated failures
* Data format errors: Validate before export, quarantine invalid records
* External system unavailable: Queue exports, retry when available

---

## Cross-Cutting Concerns

### 7. Quarantine Layer

**Purpose**: Non-blocking data quality isolation and human review workflow

**Key Principles**:
* **Non-Blocking**: Main pipeline continues, quarantined records processed separately
* **Human-in-the-Loop**: Manual review and remediation
* **Reprocessing**: Re-inject corrected records into pipeline
* **Retention Policies**: Auto-expire old quarantined records

**Tables**:
* `workspace.quarantine.quarantine_jobs` - Isolated DQ failures
* `workspace.quarantine.quarantine_batches` - Batch-level quarantine operation tracking

**Operations**:
1. **Route Records**: Automatically quarantine DQ failures
2. **Review & Remediate**: Human review with UI (future)
3. **Reprocess Batch**: Re-inject corrected records
4. **Retention Cleanup**: Auto-expire records after 90 days

---

### 8. Audit Layer

**Purpose**: Comprehensive observability and compliance tracking

**Key Principles**:
* **Complete Lineage**: Track all data transformations
* **Performance Metrics**: Runtime, row counts, error rates
* **Access Logging**: Track data access for compliance
* **Alerting**: Automated notifications on failures

**Tables**:
* `workspace.audit.audit_pipeline_runs` - Pipeline execution history
* `workspace.audit.audit_dq_results` - Data quality test results
* `workspace.audit.audit_access_events` - Data access logs

**Operations**:
1. **Pipeline Run Logging**: Automatic logging via metadata layer
2. **DQ Result Tracking**: Validation outcomes per batch
3. **Access Event Logging**: Unity Catalog access logs
4. **Daily Summary**: Aggregated metrics for monitoring
5. **Notification Dispatch**: Email/Slack alerts on failures

---

## Technology Stack

### Compute
* **Databricks Serverless**: Auto-scaling, no cluster management
* **Supported Languages**: Python, SQL (R and Scala not supported on serverless)

### Storage
* **Unity Catalog**: `workspace` catalog (single-catalog architecture)
* **Delta Lake**: All tables stored as Delta for ACID transactions
* **Partitioning**: By date and source for query performance

### Orchestration
* **Databricks Workflows**: Multi-task workflows with file-arrival triggers
* **Retry Logic**: Configurable retry counts and intervals per task
* **Concurrency**: Max 1 concurrent run to prevent overlaps

### Security
* **Databricks Secrets**: API keys stored in secret scopes (`lmip-api`)
* **Unity Catalog Governance**: Table-level access control
* **Audit Logging**: All data access tracked in `audit` schema

### External Integrations
* **Remotive API**: Job posting source (remotive.com)
* **Arbeitnow API**: Job posting source (arbeitnow.com)
* **Supabase**: External Postgres for publishing

---

## Design Decisions & Rationale

### Why Medallion Architecture?
* **Reprocessing**: Bronze immutability enables schema evolution and reprocessing
* **Layer Isolation**: Each layer can evolve independently
* **Quality Control**: Progressive refinement from raw to analytics-ready

### Why Single Catalog?
* **Simplicity**: Single `workspace` catalog reduces complexity
* **Schema Isolation**: Layers separated by schema (bronze, silver, intermediate, gold, reporting)
* **Access Control**: Simplified governance with schema-level permissions

### Why SCD Type 2 for Jobs Only?
* **Historical Analysis**: Job postings change over time (salary, requirements)
* **Performance**: Type 1 for static dimensions (company, sector) avoids unnecessary history
* **Lineage**: SCD2 enables time-travel analysis of job evolution

### Why Hybrid Semantic Matching?
* **Accuracy**: Rules provide deterministic matching for common cases
* **Coverage**: ML fallback handles edge cases
* **Cost Control**: LLM calls optional and timeout-protected
* **Human Feedback**: Review queue improves matching over time

### Why Pre-Aggregated Gold Layer?
* **Dashboard Performance**: Sub-second queries for BI tools
* **Denormalization**: Embed dimensional attributes to avoid expensive joins
* **Temporal Metrics**: Pre-compute MoM/QoQ changes for trending

---

## Scalability & Performance

### Current Scale
* **Daily Ingestion**: ~2,500-3,000 job postings
* **Total Jobs**: ~50,000-100,000 active jobs
* **Pipeline Duration**: 6-8 hours end-to-end
* **Storage**: ~50-100 GB (including history)

### Performance Optimizations
* **Partitioning**: Date and source partitions for query pruning
* **Z-Ordering**: Optimize Delta tables on common filter columns
* **Compact**: Regularly compact Delta tables to merge small files
* **Caching**: Avoid caching; Delta tables are already optimized
* **Parallel Processing**: Skill extraction and sector assignment run in parallel

### Scaling Considerations
* **Horizontal Scaling**: Databricks serverless auto-scales compute
* **Data Growth**: Bronze layer grows linearly with ingestion volume
* **Query Performance**: Gold layer pre-aggregations remain fast
* **Bottlenecks**: Intermediate layer (LLM calls) and gold build (SCD2)

---

## Security & Compliance

### Data Access Control
* **Unity Catalog ACLs**: Schema-level permissions
* **Secret Management**: Databricks Secrets for API keys
* **Audit Logging**: All data access tracked in `audit` schema

### Data Privacy
* **No PII**: Job postings contain public data only
* **Retention Policies**: Bronze layer retains 365 days, gold layer indefinitely
* **Right to Erasure**: Not applicable (public data)

### Compliance
* **Data Lineage**: Complete end-to-end tracking via `batch_id`
* **Change Tracking**: All updates logged in `silver_job_changes`
* **Audit Trail**: Pipeline runs logged in `audit_pipeline_runs`

---

## Future Enhancements

### Near-Term (Q2 2026)
* Contract validation and enforcement
* Schema drift detection
* Great Expectations integration for DQ rules
* Real-time streaming ingestion

### Medium-Term (Q3-Q4 2026)
* Additional data sources (LinkedIn, Indeed, Glassdoor)
* Real-time API endpoints for consumers
* Advanced ML models for skill extraction
* Interactive review UI for quarantine and intermediate queues

### Long-Term (2027+)
* Multi-catalog architecture (dev, staging, prod)
* Federated contract governance
* Cost allocation per data product
* Graph database for skill relationships

---

## Related Documentation

* **Data Model**: See `Data_Model.md` for detailed schema documentation
* **Pipeline Flow**: See `Pipeline_Flow.md` for workflow orchestration details
* **Publishing**: See `Publishing.md` for export and consumer integration
* **Consumer Bootstrap**: See `Consumer_Bootstrap.md` for getting started as a consumer
* **Recovery**: See `Recovery_Runbook.md` for failure recovery procedures
* **Monitoring**: See `Monitoring_Runbook.md` for observability and alerting

---

## Contact & Support

**Platform Owner**: LMIP Data Platform Engineering  
**Documentation**: `/Workspace/Users/aaryan.shrivastav1403@gmail.com/LMIP/docs/`  
**Source Repository**: `/Workspace/Users/aaryan.shrivastav1403@gmail.com/LMIP/`
