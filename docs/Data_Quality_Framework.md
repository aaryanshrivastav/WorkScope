# LMIP Data Quality Framework

**Version:** 1.0  
**Last Updated:** June 12, 2026  
**Owner:** Data Quality Lead  
**Status:** Active

---

## Executive Summary

This document defines the comprehensive Data Quality (DQ) Framework for the Labor Market Intelligence Platform (LMIP). The framework covers **55 datasets** across **7 data layers** with **80+ validation rules** organized into **8 categories**.

### Framework Scope

* **Bronze Layer:** 5 tables - Raw ingestion validation
* **Silver Layer:** 6 tables - Cleansed data validation
* **Intermediate Layer: Entity resolution validation
* **Gold Layer:** 14 tables - Dimensional model validation
* **Gold Layer:** 19 tables - Business metric validation
* **Quarantine Layer:** 1 table - Failed record management
* **Audit Layer:** 3 tables - DQ monitoring

### Key Metrics

* **Total Validation Rules:** 80+
* **Critical (ERROR) Rules:** 45
* **Warning Rules:** 30
* **Informational Rules:** 5
* **Automated Actions:** 10 types
* **Coverage:** 100% of critical data flows

---

## Table of Contents

1. [Framework Architecture](#framework-architecture)
2. [Validation Rule Categories](#validation-rule-categories)
3. [Severity Levels](#severity-levels)
4. [Response Actions](#response-actions)
5. [Data Layer Contracts](#data-layer-contracts)
6. [Rule Catalog](#rule-catalog)
7. [Implementation Guide](#implementation-guide)
8. [Monitoring & Alerting](#monitoring--alerting)
9. [Appendices](#appendices)

---

## 1. Framework Architecture

### 1.1 Design Principles

1. **Prevention Over Cure:** Catch data quality issues as early as possible in the pipeline
2. **Automated Response:** Automate remediation actions wherever possible
3. **Layered Validation:** Apply appropriate validations at each data layer
4. **Business-Driven:** Align DQ rules with business requirements and SLAs
5. **Auditable:** Maintain complete audit trail of all DQ checks and actions

### 1.2 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     LMIP Data Quality Framework                  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Validation Rule Engine                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Completeness │  │  Uniqueness  │  │  Freshness   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Referential  │  │   Business   │  │    Sector    │         │
│  │  Integrity   │  │    Logic     │  │Classification│         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│  ┌──────────────┐  ┌──────────────┐                            │
│  │    Salary    │  │   Location   │                            │
│  │  Validation  │  │Normalization │                            │
│  └──────────────┘  └──────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Response Action Engine                       │
│  QUARANTINE │ ALERT │ AUTO_FIX │ FLAG │ LOG │ QUEUE            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Audit & Monitoring                          │
│  audit.audit_dq_results │ quarantine.quarantine_jobs            │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 Data Flow

1. **Ingestion:** Data arrives in Bronze layer from external sources
2. **Bronze Validation:** Completeness, uniqueness, freshness checks
3. **Silver Transformation:** Cleansing, normalization, deduplication
4. **Silver Validation:** Business rules, referential integrity
5. **Intermediate Enrichment:** Entity resolution, classification
6. **Intermediate Validation:** Sector assignment, confidence scores
7. **Gold Load:** Dimensional modeling
8. **Gold Validation:** FK relationships, dimension integrity
9. **Gold Aggregation:** Business metrics calculation
10. **Gold Validation:** Metric consistency, completeness

---

## 2. Validation Rule Categories

### 2.1 Completeness Rules

**Purpose:** Ensure critical fields are populated

* **Rule Count:** 15
* **Severity:** ERROR for critical fields, WARNING for optional fields
* **Action:** QUARANTINE or FLAG_FOR_REVIEW

**Key Rules:**
* BR_COMPL_001: Bronze job snapshot required fields
* SV_COMPL_001: Silver jobs critical fields
* SM_COMPL_001: Intermediate sector map completeness
* WH_COMPL_001-005: Gold dimension/fact completeness
* GD_COMPL_001-002: Gold aggregation completeness

### 2.2 Uniqueness Rules

**Purpose:** Validate primary and natural key uniqueness

* **Rule Count:** 12
* **Severity:** ERROR for PK violations, WARNING for NK duplicates
* **Action:** QUARANTINE

**Key Rules:**
* BR_UNIQ_001-002: Bronze snapshot uniqueness
* SV_UNIQ_001-003: Silver enterprise_job_id and mapping uniqueness
* SM_UNIQ_001-003: Intermediate canonical ID uniqueness
* WH_UNIQ_001-005: Gold surrogate key uniqueness
* GD_UNIQ_001: Gold mapping uniqueness

### 2.3 Freshness Rules

**Purpose:** Monitor data timeliness and pipeline health

* **Rule Count:** 7
* **Severity:** WARNING for delays, ERROR for critical staleness
* **Action:** ALERT

**Key Rules:**
* BR_FRESH_001: Bronze ingestion within 24 hours
* SV_FRESH_001-002: Silver updates within 48 hours / 7 days
* SM_FRESH_001: Intermediate mapping recency
* WH_FRESH_001: Gold load recency
* GD_FRESH_001: Gold aggregation recency
* AUDIT_FRESH_001: DQ validation execution recency

### 2.4 Referential Integrity Rules

**Purpose:** Validate foreign key relationships

* **Rule Count:** 9
* **Severity:** ERROR
* **Action:** QUARANTINE

**Key Rules:**
* SV_REF_001: Silver to Bronze FK integrity
* SM_REF_001-002: Intermediate to Silver FK integrity
* WH_REF_001-006: Gold fact-to-dimension FK integrity
* QUAR_REF_001: Quarantine FK integrity check

### 2.5 Business Logic Rules

**Purpose:** Enforce business rules and data logic

* **Rule Count:** 11
* **Severity:** ERROR for violations, WARNING for anomalies
* **Action:** QUARANTINE, AUTO_FIX, or FLAG_FOR_REVIEW

**Key Rules:**
* BIZ_001: Posted date not in future
* BIZ_002: Active flag consistency
* BIZ_003: Posted date before last seen
* BIZ_004: Created before updated
* BIZ_005: Confidence scores in valid range (0-1)
* BIZ_006-007: Valid enumeration values
* BIZ_008: Salary observation type validation
* BIZ_009-011: Dimension and quarantine status validation

### 2.6 Sector Classification Rules

**Purpose:** Validate sector assignments and classifications

* **Rule Count:** 9
* **Severity:** ERROR for invalid codes, WARNING for missing/low confidence
* **Action:** QUEUE_FOR_INTERMEDIATE_REVIEW or QUARANTINE

**Key Rules:**
* SECT_001: Missing sector assignment
* SECT_002: Low confidence sector assignment (<0.6)
* SECT_003: Sector assignment without intermediate mapping
* SECT_004: Invalid sector code
* SECT_005: Missing assignment method
* SECT_006-007: Valid normalization/taxonomy types
* SECT_008: Sector family consistency
* SECT_009: Hospitality sector coverage

### 2.7 Salary Validation Rules

**Purpose:** Validate salary data quality

* **Rule Count:** 11
* **Severity:** ERROR for invalid data, WARNING for outliers
* **Action:** QUARANTINE or FLAG_FOR_REVIEW

**Key Rules:**
* SAL_001: Salary min < max
* SAL_002: Positive salary values
* SAL_003: Valid ISO currency codes
* SAL_004: Valid salary period (ANNUAL, MONTHLY, HOURLY)
* SAL_005: Confidence score range (0-1)
* SAL_006-007: Reasonable salary ranges by period
* SAL_008: Low confidence salary flagging
* SAL_009: Sector salary data coverage
* SAL_010: Salary trend consistency
* SAL_011: Missing salary data tracking

### 2.8 Location Normalization Rules

**Purpose:** Validate location data quality and normalization

* **Rule Count:** 12
* **Severity:** ERROR for invalid data, WARNING for missing normalization
* **Action:** QUARANTINE, QUEUE_FOR_NORMALIZATION, or QUEUE_FOR_GEOCODING

**Key Rules:**
* LOC_001: Missing location normalization
* LOC_002: Valid ISO country codes
* LOC_003-004: Valid latitude/longitude ranges
* LOC_005: Location hierarchy consistency
* LOC_006: Geocoding completeness
* LOC_007: Remote type consistency
* LOC_008: Location natural key uniqueness
* LOC_009: ISO region code format
* LOC_010: Location trends data quality
* LOC_011: Consistent location names
* LOC_012: Inactive location usage

---

## 3. Severity Levels

### 3.1 ERROR

**Definition:** Critical data quality issue that prevents data from being used

* **Impact:** HIGH
* **Response Time:** Immediate
* **Action Required:** Yes
* **Examples:**
  * Missing required fields
  * Duplicate primary keys
  * Orphaned foreign keys
  * Invalid salary ranges
  * Date logic violations

**SLA:** ERROR conditions must be resolved within 4 hours of detection

### 3.2 WARNING

**Definition:** Data quality issue that may impact analytics or downstream processes

* **Impact:** MEDIUM
* **Response Time:** Within 24 hours
* **Action Required:** Review and prioritize
* **Examples:**
  * Missing normalized values
  * Low confidence scores
  * Stale data (>48 hours)
  * Outlier values
  * Missing optional enrichments

**SLA:** WARNING conditions should be reviewed daily and resolved within 48 hours

### 3.3 INFO

**Definition:** Informational data quality metric for monitoring

* **Impact:** LOW
* **Response Time:** Periodic review
* **Action Required:** No immediate action
* **Examples:**
  * Coverage metrics
  * Completeness percentages
  * Data volume trends

**SLA:** INFO metrics reviewed weekly in DQ dashboard

---

## 4. Response Actions

### 4.1 QUARANTINE

**Description:** Move records to quarantine table for manual review

* **Target:** `workspace.quarantine.quarantine_jobs`
* **Automated:** Yes
* **Approval Required:** No
* **Process:**
  1. Record fails validation
  2. Full record payload copied to quarantine table
  3. Quarantine metadata added (rule_name, severity, timestamp)
  4. Alert sent to DQ team
  5. Original record soft-deleted or marked

**Usage:** Critical errors that prevent processing (45 rules)

### 4.2 ALERT

**Description:** Send alert to data quality team

* **Channels:** Email, Slack
* **Automated:** Yes
* **Process:**
  1. Rule violation detected
  2. Alert message generated with details
  3. Notification sent to configured channels
  4. Record logged to audit table

**Usage:** Freshness violations, pipeline health issues (7 rules)

### 4.3 AUTO_FIX

**Description:** Automatically fix the data quality issue

* **Automated:** Yes
* **Approval Required:** No
* **Process:**
  1. Issue detected
  2. Correction logic applied
  3. Original value logged for audit
  4. Record updated with corrected value

**Usage:** Simple logic corrections (1 rule - BIZ_002)

### 4.4 FLAG_FOR_REVIEW

**Description:** Flag records for manual review

* **Target:** `workspace.silver.silver_intermediate_review_queue`
* **Automated:** Yes
* **Process:**
  1. Record flagged
  2. Added to review queue with issue details
  3. Analyst notified
  4. Record continues through pipeline

**Usage:** Suspicious but not invalid data (5 rules)

### 4.5 QUEUE_FOR_INTERMEDIATE_REVIEW

**Description:** Queue for intermediate layer review

* **Target:** `workspace.silver.silver_intermediate_review_queue`
* **Automated:** Yes
* **Process:**
  1. Missing or low-confidence intermediate mapping detected
  2. Job added to intermediate review queue
  3. ML/manual review triggered
  4. Mapping created/updated

**Usage:** Sector classification issues (3 rules)

### 4.6 QUEUE_FOR_NORMALIZATION

**Description:** Queue for normalization processing

* **Automated:** Yes
* **Process:**
  1. Missing normalized value detected
  2. Record queued for normalization service
  3. Normalization logic applied
  4. Record updated

**Usage:** Location/company name normalization (1 rule)

### 4.7 QUEUE_FOR_GEOCODING

**Description:** Queue for geocoding processing

* **Automated:** Yes
* **Process:**
  1. Missing lat/long detected
  2. Location queued for geocoding service
  3. Geocoding API called
  4. Coordinates added to dimension

**Usage:** Location geocoding (1 rule)

### 4.8 LOG_WARNING

**Description:** Log warning to audit table

* **Target:** `workspace.audit.audit_dq_results`
* **Automated:** Yes
* **Process:**
  1. Warning condition detected
  2. Details logged to audit table
  3. Daily summary report generated

**Usage:** Non-critical warnings (15 rules)

### 4.9 LOG_INFO

**Description:** Log informational message

* **Target:** `workspace.audit.audit_dq_results`
* **Automated:** Yes
* **Process:**
  1. Metric calculated
  2. Value logged to audit table
  3. Available in DQ dashboard

**Usage:** Monitoring metrics (1 rule)

### 4.10 CREATE_INTERMEDIATE_MAPPING

**Description:** Trigger intermediate mapping creation

* **Automated:** Yes
* **Process:**
  1. Missing intermediate mapping detected
  2. Mapping creation pipeline triggered
  3. Entity resolution performed
  4. Mapping record created

**Usage:** Missing intermediate mappings (1 rule)

---

## 5. Data Layer Contracts

### 5.1 Bronze Layer Contract

**Schema:** `workspace.bronze`

**Purpose:** Immutable raw data capture

**Tables:**

#### bronze_job_snapshot
* **Description:** Raw job posting snapshots from external sources
* **Critical Columns:** snapshot_id, source_name, source_job_id, payload_json, ingestion_timestamp
* **Validation Rules:** 4 (BR_COMPL_001, BR_UNIQ_001, BR_UNIQ_002, BR_FRESH_001)
* **SLA:** Freshness < 24h, Completeness > 99.5%

#### batch_metadata
* **Description:** Ingestion batch metadata
* **Critical Columns:** batch_id, source_name, started_at
* **Validation Rules:** 1 (BR_COMPL_002)
* **SLA:** Freshness < 1h, Completeness = 100%

#### bronze_api_response_log
* **Description:** API response logging
* **Validation Rules:** 0

#### dedupe_tracking
* **Description:** Deduplication tracking
* **Validation Rules:** 0

#### watermarks
* **Description:** Incremental load watermarks
* **Validation Rules:** 0

### 5.2 Silver Layer Contract

**Schema:** `workspace.silver`

**Purpose:** Cleansed and conformed data

**Tables:**

#### silver_jobs_current
* **Description:** Current state of all job postings
* **Critical Columns:** enterprise_job_id, source_name, source_job_id, title_raw, posted_at, is_active
* **Validation Rules:** 19 rules across all categories
* **SLA:** Freshness < 24h, Completeness > 98%, Uniqueness = 100%
* **Most Comprehensive Coverage**

#### silver_job_changes
* **Description:** Job posting change events (CDC)
* **Validation Rules:** 0

#### silver_job_identity_map
* **Description:** Job identity resolution
* **Validation Rules:** 1 (SV_UNIQ_003)

#### silver_jobs_staging
* **Description:** Processing staging area
* **Validation Rules:** 0

#### silver_intermediate_review_queue
* **Description:** Intermediate review queue
* **Validation Rules:** 0

#### silver_skill_mapping
* **Description:** Skill extraction results
* **Validation Rules:** 1 (SV_COMPL_003)

### 5.3 Intermediate Layer Contract

**Schema:** `workspace.intermediate`

**Purpose:** Entity resolution and canonical mappings

**Tables:**

#### sem_company_canonical
* **Description:** Canonical company master
* **Critical Columns:** canonical_company_id, canonical_company_name
* **Validation Rules:** 2 (SM_COMPL_002, SM_UNIQ_001)
* **SLA:** Completeness = 100%, Uniqueness = 100%

#### sem_company_map
* **Description:** Company name to canonical mapping
* **Validation Rules:** 1 (SM_REF_002)

#### sem_job_role_map
* **Description:** Job title to role mapping
* **Validation Rules:** 0

#### sem_job_skill_evidence
* **Description:** Skill evidence extraction
* **Validation Rules:** 0

#### sem_sector_map
* **Description:** Job to sector mapping
* **Critical Columns:** sector_map_id, enterprise_job_id, canonical_sector_code, canonical_sector_name
* **Validation Rules:** 7 rules (completeness, uniqueness, freshness, referential integrity, sector classification)
* **SLA:** Freshness < 48h, Completeness > 95%

#### sem_skill_catalog
* **Description:** Canonical skill catalog
* **Critical Columns:** canonical_skill_id, canonical_skill_name
* **Validation Rules:** 2 (SM_COMPL_003, SM_UNIQ_002)

#### sem_skill_graph_edges
* **Description:** Skill relationship graph
* **Validation Rules:** 0

### 5.4 Gold Layer Contract

**Schema:** `workspace.gold`

**Purpose:** Dimensional model for analytics

**Dimensions:**

#### dim_company
* **Type:** SCD Type 1
* **Critical Columns:** company_sk, company_name
* **Validation Rules:** 2 (WH_COMPL_001, WH_UNIQ_001)
* **SLA:** Completeness = 100%, Uniqueness = 100%

#### dim_location
* **Type:** SCD Type 1
* **Critical Columns:** location_sk, location_name, active_flag
* **Validation Rules:** 11 rules (completeness, uniqueness, location normalization)
* **SLA:** Completeness = 100%, Geocoding > 90%
* **Most Location Rules**

#### dim_sector
* **Type:** SCD Type 1
* **Critical Columns:** sector_sk, sector_name, sector_family, active_flag
* **Validation Rules:** 4 (WH_COMPL_003, WH_UNIQ_003, BIZ_009, SECT_008)

#### dim_skill
* **Type:** SCD Type 1
* **Validation Rules:** 1 (WH_UNIQ_004)

#### dim_role
* **Type:** SCD Type 1
* **Validation Rules:** 0

#### dim_job
* **Type:** SCD Type 2
* **Validation Rules:** 0

#### dim_source
* **Type:** SCD Type 1
* **Validation Rules:** 0

#### dim_company_alias
* **Validation Rules:** 0

**Facts:**

#### fact_job_postings
* **Grain:** One row per job posting per day
* **Critical Columns:** job_sk, company_sk, location_sk, sector_sk, source_sk
* **Validation Rules:** 6 (completeness, freshness, referential integrity)
* **SLA:** Freshness < 24h, Referential Integrity = 100%

#### fact_salary
* **Grain:** One row per salary observation
* **Critical Columns:** fact_salary_sk, job_sk, observation_date_sk, salary_observation_type
* **Validation Rules:** 11 rules (completeness, uniqueness, referential integrity, salary validation)
* **SLA:** Completeness > 95%, Valid Range > 98%
* **Most Salary Rules**

#### fact_job_lifecycle
* **Grain:** One row per lifecycle event
* **Validation Rules:** 0

#### fact_pipeline_runs
* **Grain:** One row per pipeline run
* **Validation Rules:** 0

**Bridges:**

#### bridge_job_skill
* **Description:** Many-to-many job-skill relationship
* **Validation Rules:** 1 (WH_REF_006)

### 5.5 Gold Layer Contract

**Schema:** `workspace.gold`

**Purpose:** Business-level aggregations

**Tables:**

#### gold_hiring_trends
* **Refresh:** Daily
* **Validation Rules:** 2 (GD_COMPL_001, GD_FRESH_001)
* **SLA:** Freshness < 24h

#### gold_salary_trends
* **Refresh:** Daily
* **Validation Rules:** 2 (GD_COMPL_002, SAL_010)
* **SLA:** Freshness < 24h

#### gold_location_trends
* **Refresh:** Daily
* **Validation Rules:** 1 (LOC_010)

#### gold_sector_overview
* **Refresh:** Daily
* **Validation Rules:** 0

#### gold_skill_demand
* **Refresh:** Daily
* **Validation Rules:** 0

#### gold_company_hiring
* **Refresh:** Daily
* **Validation Rules:** 0

#### gold_company_activity
* **Refresh:** Weekly
* **Validation Rules:** 1 (SECT_009)

#### gold_hiring_activity
* **Refresh:** Daily
* **Validation Rules:** 0

#### gold_skill_demand_by_sector
* **Refresh:** Daily
* **Validation Rules:** 0

#### gold_pipeline_health
* **Refresh:** Hourly
* **Validation Rules:** 0

#### canonical_companies_mappings
* **Validation Rules:** 1 (GD_UNIQ_001)

#### canonical_roles
* **Validation Rules:** 0

#### role_dictionary
* **Validation Rules:** 0

#### skill_catalog
* **Validation Rules:** 0

#### skill_aliases
* **Validation Rules:** 0

#### skill_graph
* **Validation Rules:** 0

#### skill_graph_metrics
* **Validation Rules:** 0

#### company_review_queue
* **Validation Rules:** 0

#### role_review_queue
* **Validation Rules:** 0

#### intermediate_review_audit
* **Validation Rules:** 0

### 5.6 Quarantine Layer Contract

**Schema:** `workspace.quarantine`

**Purpose:** Failed validation record storage

#### quarantine_jobs
* **Critical Columns:** quarantine_id, source_name, failure_stage, failed_rule_name, severity
* **Validation Rules:** 3 (BIZ_010, BIZ_011, QUAR_REF_001)

### 5.7 Audit Layer Contract

**Schema:** `workspace.audit`

**Purpose:** DQ monitoring and audit trail

#### audit_dq_results
* **Critical Columns:** audit_dq_sk, run_id, rule_name, target_table, severity
* **Validation Rules:** 1 (AUDIT_FRESH_001)
* **SLA:** Freshness < 24h

#### audit_pipeline_runs
* **Validation Rules:** 0

#### audit_access_events
* **Validation Rules:** 0

---

## 6. Rule Catalog

### 6.1 Complete Rule Index

| Rule ID | Category | Target Table | Severity | Action | Description |
|---------|----------|--------------|----------|--------|-------------|
| **BRONZE LAYER** |
| BR_COMPL_001 | Completeness | bronze_job_snapshot | ERROR | QUARANTINE | Required fields not null |
| BR_COMPL_002 | Completeness | batch_metadata | ERROR | QUARANTINE | Batch metadata complete |
| BR_UNIQ_001 | Uniqueness | bronze_job_snapshot | ERROR | QUARANTINE | Unique snapshot_id |
| BR_UNIQ_002 | Uniqueness | bronze_job_snapshot | WARNING | LOG_WARNING | Unique payload_hash per batch |
| BR_FRESH_001 | Freshness | bronze_job_snapshot | WARNING | ALERT | Source ingested <24h |
| **SILVER LAYER** |
| SV_COMPL_001 | Completeness | silver_jobs_current | ERROR | QUARANTINE | Critical fields not null |
| SV_COMPL_002 | Completeness | silver_jobs_current | WARNING | FLAG_FOR_REVIEW | Normalized fields populated |
| SV_COMPL_003 | Completeness | silver_skill_mapping | ERROR | QUARANTINE | Skill mapping complete |
| SV_UNIQ_001 | Uniqueness | silver_jobs_current | ERROR | QUARANTINE | Unique enterprise_job_id |
| SV_UNIQ_002 | Uniqueness | silver_jobs_current | WARNING | LOG_WARNING | Unique source job |
| SV_UNIQ_003 | Uniqueness | silver_job_identity_map | ERROR | QUARANTINE | Unique mapping_id |
| SV_FRESH_001 | Freshness | silver_jobs_current | WARNING | ALERT | Active jobs updated <48h |
| SV_FRESH_002 | Freshness | silver_jobs_current | ERROR | ALERT | Active jobs seen <7d |
| SV_REF_001 | Referential Integrity | silver_jobs_current | ERROR | QUARANTINE | Valid bronze source reference |
| **INTERMEDIATE LAYER** |
| SM_COMPL_001 | Completeness | sem_sector_map | ERROR | QUARANTINE | Sector map complete |
| SM_COMPL_002 | Completeness | sem_company_canonical | ERROR | QUARANTINE | Canonical company complete |
| SM_COMPL_003 | Completeness | sem_skill_catalog | ERROR | QUARANTINE | Skill catalog complete |
| SM_UNIQ_001 | Uniqueness | sem_company_canonical | ERROR | QUARANTINE | Unique canonical_company_id |
| SM_UNIQ_002 | Uniqueness | sem_skill_catalog | ERROR | QUARANTINE | Unique canonical_skill_id |
| SM_UNIQ_003 | Uniqueness | sem_sector_map | ERROR | QUARANTINE | Unique sector_map_id |
| SM_FRESH_001 | Freshness | sem_sector_map | WARNING | LOG_WARNING | Recent intermediate mappings |
| SM_REF_001 | Referential Integrity | sem_sector_map | ERROR | QUARANTINE | Valid silver job reference |
| SM_REF_002 | Referential Integrity | sem_company_map | ERROR | QUARANTINE | Valid silver job reference |
| **GOLD LAYER** |
| WH_COMPL_001 | Completeness | dim_company | ERROR | QUARANTINE | Company dimension complete |
| WH_COMPL_002 | Completeness | dim_location | ERROR | QUARANTINE | Location dimension complete |
| WH_COMPL_003 | Completeness | dim_sector | ERROR | QUARANTINE | Sector dimension complete |
| WH_COMPL_004 | Completeness | fact_job_postings | ERROR | QUARANTINE | Fact foreign keys not null |
| WH_COMPL_005 | Completeness | fact_salary | ERROR | QUARANTINE | Fact salary complete |
| WH_UNIQ_001 | Uniqueness | dim_company | ERROR | QUARANTINE | Unique company_sk |
| WH_UNIQ_002 | Uniqueness | dim_location | ERROR | QUARANTINE | Unique location_sk |
| WH_UNIQ_003 | Uniqueness | dim_sector | ERROR | QUARANTINE | Unique sector_sk |
| WH_UNIQ_004 | Uniqueness | dim_skill | ERROR | QUARANTINE | Unique skill_sk |
| WH_UNIQ_005 | Uniqueness | fact_salary | ERROR | QUARANTINE | Unique fact_salary_sk |
| WH_FRESH_001 | Freshness | fact_job_postings | WARNING | ALERT | Gold load <24h |
| WH_REF_001 | Referential Integrity | fact_job_postings | ERROR | QUARANTINE | Valid dim_job FK |
| WH_REF_002 | Referential Integrity | fact_job_postings | ERROR | QUARANTINE | Valid dim_company FK |
| WH_REF_003 | Referential Integrity | fact_job_postings | ERROR | QUARANTINE | Valid dim_location FK |
| WH_REF_004 | Referential Integrity | fact_job_postings | ERROR | QUARANTINE | Valid dim_sector FK |
| WH_REF_005 | Referential Integrity | fact_salary | ERROR | QUARANTINE | Valid dimension FKs |
| WH_REF_006 | Referential Integrity | bridge_job_skill | ERROR | QUARANTINE | Valid bridge FKs |
| **GOLD LAYER** |
| GD_COMPL_001 | Completeness | gold_hiring_trends | WARNING | LOG_WARNING | Trend metrics complete |
| GD_COMPL_002 | Completeness | gold_salary_trends | WARNING | LOG_WARNING | Salary metrics complete |
| GD_FRESH_001 | Freshness | gold_hiring_trends | WARNING | ALERT | Trend calculation <24h |
| GD_UNIQ_001 | Uniqueness | canonical_companies_mappings | WARNING | LOG_WARNING | Unique mappings |
| **BUSINESS LOGIC** |
| BIZ_001 | Business Logic | silver_jobs_current | ERROR | QUARANTINE | Posted date not in future |
| BIZ_002 | Business Logic | silver_jobs_current | ERROR | AUTO_FIX | Active flag consistency |
| BIZ_003 | Business Logic | silver_jobs_current | ERROR | QUARANTINE | Posted before last seen |
| BIZ_004 | Business Logic | silver_jobs_current | ERROR | QUARANTINE | Created before updated |
| BIZ_005 | Business Logic | sem_sector_map | ERROR | QUARANTINE | Confidence in range 0-1 |
| BIZ_006 | Business Logic | silver_jobs_current | WARNING | FLAG_FOR_REVIEW | Valid remote_type values |
| BIZ_007 | Business Logic | silver_jobs_current | WARNING | LOG_WARNING | Valid dq_status values |
| BIZ_008 | Business Logic | fact_salary | ERROR | QUARANTINE | Valid observation_type |
| BIZ_009 | Business Logic | dim_sector | WARNING | LOG_WARNING | Inactive sector usage |
| BIZ_010 | Business Logic | quarantine_jobs | ERROR | ALERT | Valid quarantine severity |
| BIZ_011 | Business Logic | quarantine_jobs | ERROR | ALERT | Valid reprocess status |
| **SECTOR CLASSIFICATION** |
| SECT_001 | Sector Classification | silver_jobs_current | WARNING | QUEUE_FOR_INTERMEDIATE_REVIEW | Missing sector assignment |
| SECT_002 | Sector Classification | silver_jobs_current | WARNING | QUEUE_FOR_INTERMEDIATE_REVIEW | Low confidence sector |
| SECT_003 | Sector Classification | silver_jobs_current | ERROR | CREATE_INTERMEDIATE_MAPPING | Sector without mapping |
| SECT_004 | Sector Classification | sem_sector_map | ERROR | QUARANTINE | Invalid sector code |
| SECT_005 | Sector Classification | silver_jobs_current | WARNING | LOG_WARNING | Missing assignment method |
| SECT_006 | Sector Classification | sem_sector_map | WARNING | LOG_WARNING | Valid normalization method |
| SECT_007 | Sector Classification | sem_sector_map | WARNING | LOG_WARNING | Valid taxonomy type |
| SECT_008 | Sector Classification | dim_sector | WARNING | LOG_WARNING | Sector family consistency |
| SECT_009 | Sector Classification | gold_company_activity | WARNING | LOG_WARNING | Hospitality coverage |
| **SALARY VALIDATION** |
| SAL_001 | Salary Validation | fact_salary | ERROR | QUARANTINE | Salary min < max |
| SAL_002 | Salary Validation | fact_salary | ERROR | QUARANTINE | Positive salary values |
| SAL_003 | Salary Validation | fact_salary | ERROR | QUARANTINE | Valid ISO currency codes |
| SAL_004 | Salary Validation | fact_salary | ERROR | QUARANTINE | Valid salary period |
| SAL_005 | Salary Validation | fact_salary | ERROR | QUARANTINE | Confidence in range 0-1 |
| SAL_006 | Salary Validation | fact_salary | WARNING | FLAG_FOR_REVIEW | Reasonable annual range |
| SAL_007 | Salary Validation | fact_salary | WARNING | FLAG_FOR_REVIEW | Reasonable hourly range |
| SAL_008 | Salary Validation | fact_salary | WARNING | FLAG_FOR_REVIEW | Low confidence flagging |
| SAL_009 | Salary Validation | fact_salary | WARNING | LOG_WARNING | Sector salary coverage |
| SAL_010 | Salary Validation | gold_salary_trends | WARNING | LOG_WARNING | Trend consistency |
| SAL_011 | Salary Validation | fact_job_postings | INFO | LOG_INFO | Missing salary tracking |
| **LOCATION NORMALIZATION** |
| LOC_001 | Location Normalization | silver_jobs_current | WARNING | QUEUE_FOR_NORMALIZATION | Missing normalization |
| LOC_002 | Location Normalization | dim_location | ERROR | QUARANTINE | Valid ISO country codes |
| LOC_003 | Location Normalization | dim_location | ERROR | QUARANTINE | Valid latitude range |
| LOC_004 | Location Normalization | dim_location | ERROR | QUARANTINE | Valid longitude range |
| LOC_005 | Location Normalization | dim_location | WARNING | LOG_WARNING | Location hierarchy |
| LOC_006 | Location Normalization | dim_location | WARNING | QUEUE_FOR_GEOCODING | Geocoding completeness |
| LOC_007 | Location Normalization | silver_jobs_current | WARNING | LOG_WARNING | Remote type consistency |
| LOC_008 | Location Normalization | dim_location | ERROR | QUARANTINE | Unique location_nk |
| LOC_009 | Location Normalization | dim_location | WARNING | LOG_WARNING | ISO region code format |
| LOC_010 | Location Normalization | gold_location_trends | WARNING | LOG_WARNING | Trend data quality |
| LOC_011 | Location Normalization | dim_location | WARNING | FLAG_FOR_REVIEW | Consistent location names |
| LOC_012 | Location Normalization | dim_location | WARNING | LOG_WARNING | Inactive location usage |
| **QUARANTINE & AUDIT** |
| QUAR_REF_001 | Referential Integrity | quarantine_jobs | WARNING | LOG_WARNING | Valid job reference |
| AUDIT_FRESH_001 | Freshness | audit_dq_results | ERROR | ALERT | DQ execution <24h |

### 6.2 Rules by Dataset

**Most Validated Tables:**

1. **silver_jobs_current** - 19 rules (most comprehensive)
2. **fact_salary** - 11 rules
3. **dim_location** - 11 rules
4. **sem_sector_map** - 7 rules
5. **fact_job_postings** - 6 rules

**Tables with No Validation:**

17 tables have no explicit rules (primarily staging, audit, and derived aggregations)

---

## 7. Implementation Guide

### 7.1 Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     LMIP SQL Validations                         │
│                 /sql/validations/*.sql (8 files)                 │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Databricks Jobs Scheduler                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   Hourly    │  │    Daily    │  │   Weekly    │            │
│  │  Freshness  │  │ Completeness│  │   Trend     │            │
│  │   Checks    │  │  Uniqueness │  │  Analysis   │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│               Response Action Orchestration                      │
│  - Quarantine records                                            │
│  - Send alerts                                                   │
│  - Trigger fix pipelines                                         │
│  - Log to audit                                                  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                  DQ Dashboard & Reporting                        │
│  workspace.audit.audit_dq_results                                │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Execution Schedule

**Hourly (Critical):**
* BR_FRESH_001: Bronze ingestion freshness
* AUDIT_FRESH_001: DQ execution monitoring

**Every 4 Hours (High Priority):**
* All ERROR-level completeness rules
* All uniqueness rules
* All referential integrity rules

**Daily (Standard):**
* All business logic rules
* Sector classification rules
* Salary validation rules
* Location normalization rules
* Freshness rules (non-critical)

**Weekly (Low Priority):**
* Gold layer aggregation checks
* Trend analysis validation
* Coverage metrics

### 7.3 Integration Points

**1. Pipeline Integration**
* Validation runs after each layer transformation
* Failed ERROR rules block downstream processing
* WARNING rules logged but allow processing to continue

**2. Alerting Integration**
* Databricks SQL Alerts for ERROR conditions
* Slack webhook for immediate notifications
* Email digest for daily WARNING summary

**3. Quarantine Integration**
* Automated quarantine table population
* Quarantine review dashboard
* Reprocessing workflow

**4. Audit Integration**
* All validation results logged to `audit.audit_dq_results`
* Historical trend analysis
* SLA compliance tracking

### 7.4 Setup Instructions

**Step 1: Deploy Validation SQL Files**
```bash
# Copy validation files to Databricks workspace
databricks workspace import-dir \
  LMIP/sql/validations \
  /Workspace/LMIP/sql/validations
```

**Step 2: Create Databricks Jobs**
```python
# Create job for each validation category
from databricks.sdk import WorkspaceClient
w = WorkspaceClient(
    host=os.getenv("DATABRICKS_HOST"),
    token=os.getenv("DATABRICKS_TOKEN")
)

for validation_file in validation_files:
    w.jobs.create(
        name=f"DQ_{validation_file}",
        tasks=[{
            "task_key": "validate",
            "sql_task": {
                "file": {"path": f"/sql/validations/{validation_file}"},
                "gold_warehouse_id": "<warehouse_id>"
            }
        }],
        schedule={"quartz_cron_expression": "0 0 * * * ?"}  # Daily
    )
```

**Step 3: Configure Alerts**
```sql
-- Create SQL alert for ERROR conditions
CREATE ALERT dq_errors
USING CRON '0 * * * *'  -- Hourly
AS
SELECT 
  rule_name,
  target_table,
  failed_records,
  validated_at
FROM workspace.audit.audit_dq_results
WHERE severity = 'ERROR'
  AND validated_at >= CURRENT_TIMESTAMP() - INTERVAL 1 HOUR
  AND failed_records > 0
```

**Step 4: Deploy DQ Contracts**
```bash
# Version control the contracts
git add LMIP/contracts/dq/dq_contracts_catalog.yaml
git commit -m "Deploy DQ contracts v1.0"
git push
```

### 7.5 Testing Strategy

**Unit Testing:**
* Test each validation rule independently
* Use synthetic data with known violations
* Verify correct severity and action assignment

**Integration Testing:**
* Run full validation suite on sample dataset
* Verify quarantine mechanism
* Validate alert delivery
* Check audit logging

**Regression Testing:**
* Maintain test dataset with historical violations
* Run validation suite after any rule changes
* Compare results to baseline

---

## 8. Monitoring & Alerting

### 8.1 DQ Dashboard

**Key Metrics:**

1. **Overall DQ Score**
   * Formula: (Total Rows - Failed Rows) / Total Rows × 100
   * Target: >99%
   * Current: Calculated daily

2. **Rules Pass Rate**
   * Formula: Rules Passed / Total Rules × 100
   * Target: >95%
   * Broken down by layer and category

3. **Quarantine Volume**
   * Daily quarantine additions
   * Aging analysis
   * Resolution rate

4. **Freshness Status**
   * Per-source ingestion lag
   * Pipeline execution delays
   * SLA compliance

5. **Coverage Metrics**
   * % jobs with sector assignment
   * % jobs with salary data
   * % locations geocoded

**Dashboard Queries:**

```sql
-- Overall DQ Health
SELECT 
  DATE_TRUNC('day', evaluated_at) as date,
  COUNT(DISTINCT rule_name) as total_rules,
  COUNT(DISTINCT CASE WHEN failed_records = 0 THEN rule_name END) as passed_rules,
  COUNT(DISTINCT CASE WHEN failed_records > 0 AND severity = 'ERROR' THEN rule_name END) as error_rules,
  COUNT(DISTINCT CASE WHEN failed_records > 0 AND severity = 'WARNING' THEN rule_name END) as warning_rules,
  SUM(failed_records) as total_failures
FROM workspace.audit.audit_dq_results
WHERE evaluated_at >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY DATE_TRUNC('day', evaluated_at)
ORDER BY date DESC
```

```sql
-- Quarantine Analysis
SELECT 
  failure_stage,
  failed_rule_name,
  severity,
  COUNT(*) as quarantined_count,
  COUNT(CASE WHEN reprocess_status = 'RESOLVED' THEN 1 END) as resolved_count,
  COUNT(CASE WHEN reprocess_status = 'PENDING' THEN 1 END) as pending_count
FROM workspace.quarantine.quarantine_jobs
WHERE quarantined_at >= CURRENT_DATE() - INTERVAL 7 DAYS
GROUP BY failure_stage, failed_rule_name, severity
ORDER BY quarantined_count DESC
```

### 8.2 Alert Configuration

**Critical Alerts (Immediate):**
* ERROR rules with >0 failures
* Freshness SLA breach
* Pipeline execution failure
* Quarantine volume spike (>10% daily increase)

**Warning Alerts (Daily Digest):**
* WARNING rules summary
* Coverage metric trends
* Low confidence assignments

**Informational Reports (Weekly):**
* DQ trend analysis
* Rule performance review
* Recommendation summary

### 8.3 SLA Tracking

**Bronze Layer SLA:**
* Freshness: <24 hours - 99% compliance target
* Completeness: >99.5% - Measured daily

**Silver Layer SLA:**
* Freshness: <24 hours for active jobs
* Completeness: >98% for critical fields
* Uniqueness: 100% for enterprise_job_id

**Intermediate Layer SLA:**
* Freshness: <48 hours for new mappings
* Completeness: >95% sector assignment
* Confidence: >80% high-confidence mappings

**Gold Layer SLA:**
* Freshness: <24 hours for fact loads
* Referential Integrity: 100% compliance
* Geocoding: >90% coverage

**Gold Layer SLA:**
* Freshness: <24 hours for daily aggregations
* Completeness: >95% for trend metrics

---

## 9. Appendices

### Appendix A: File Structure

```
LMIP/
├── sql/
│   └── validations/
│       ├── 01_completeness_validations.sql
│       ├── 02_uniqueness_validations.sql
│       ├── 03_freshness_validations.sql
│       ├── 04_referential_integrity_validations.sql
│       ├── 05_business_validations.sql
│       ├── 06_sector_classification_validations.sql
│       ├── 07_salary_validations.sql
│       └── 08_location_normalization_validations.sql
├── contracts/
│   └── dq/
│       └── dq_contracts_catalog.yaml
└── docs/
    └── Data_Quality_Framework.md
```

### Appendix B: Glossary

* **Bronze Layer:** Immutable raw data ingestion layer
* **Silver Layer:** Cleansed and conformed data layer
* **Intermediate Layer: Entity resolution and canonical mapping layer
* **Gold Layer:** Dimensional model for analytics
* **Gold Layer:** Business-level aggregations and metrics
* **Quarantine:** Isolated storage for failed validation records
* **Audit:** Monitoring and tracking layer for DQ results
* **SCD:** Slowly Changing Dimension
* **FK:** Foreign Key
* **PK:** Primary Key
* **NK:** Natural Key
* **SK:** Surrogate Key

### Appendix C: Change Log

| Version | Date | Author | Changes |
|---------|------|--------|----------|
| 1.0 | 2026-06-07 | Data Quality Lead | Initial framework release |

### Appendix D: References

* **SQL Validation Scripts:** `/LMIP/sql/validations/`
* **DQ Contracts:** `/LMIP/contracts/dq/dq_contracts_catalog.yaml`
* **Audit Tables:** `workspace.audit.audit_dq_results`
* **Quarantine Tables:** `workspace.quarantine.quarantine_jobs`

---

**Document End**
