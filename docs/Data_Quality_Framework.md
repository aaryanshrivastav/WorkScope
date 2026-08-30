# LMIP Data Quality Framework Reference

**Last Updated**: 2026-06-20  
**Target**: Maintainer DQ Reference  
*(Full legacy DQ framework doc preserved at [archive/Data_Quality_Framework_legacy.md](archive/Data_Quality_Framework_legacy.md))*

---

## 1. Core Principles

LMIP enforces automated data quality (DQ) checks at every processing stage using Delta Lake expectations and quarantine routing:

1. **Non-Blocking Bronze Ingestion**: Raw API payloads are stored immutably regardless of quality issues.
2. **Silver Quality Gates**: Critical fields (title, company, source key) are validated during Silver processing.
3. **Quarantine Routing**: Invalid records are diverted to `quarantine.quarantine_jobs` with failure tags instead of dropping data or halting pipelines.
4. **Audit Logging**: DQ checks log results to `audit.audit_dq_results`.

---

## 2. Key Expectations & Rules

| Layer | Rule | Expectation / Condition | Action on Failure |
|-------|------|------------------------|-------------------|
| **Bronze** | `valid_json` | `payload IS NOT NULL AND is_valid_json(payload)` | Telemetry warning in `bronze_api_response_log` |
| **Silver** | `title_not_null` | `title IS NOT NULL AND length(trim(title)) > 0` | Route to `quarantine.quarantine_jobs` (`reason='MISSING_TITLE'`) |
| **Silver** | `company_not_null` | `company_name IS NOT NULL` | Route to `quarantine.quarantine_jobs` (`reason='MISSING_COMPANY'`) |
| **Silver** | `valid_date` | `posted_at <= current_timestamp()` | Route to `quarantine.quarantine_jobs` (`reason='FUTURE_POSTED_DATE'`) |
| **Gold** | `valid_fk` | Foreign keys reference existing dimension SKs | Default surrogate key (`-1` / `"UNKNOWN"`) assignment |

---

## 3. Quarantine Routing & Recovery Flow

```
Raw Postings ──► Silver Validation Check
                        │
             ┌──────────┴──────────┐
             ▼                     ▼
       Valid Records        Invalid Records
             │                     │
             ▼                     ▼
   silver_jobs_current   quarantine.quarantine_jobs
                                   │
                                   ▼
                         Manual / Automated Review
                                   │
                                   ▼
                         Release & Re-ingest
```

### Manual Quarantine Release Query
To inspect quarantined records:
```sql
SELECT quarantine_reason, COUNT(*) 
FROM workspace.quarantine.quarantine_jobs 
GROUP BY quarantine_reason;
```

---

## 4. DQ Verification Commands

Run data quality validation queries and unit tests locally:
```bash
# Run quarantine routing unit tests
python -m pytest tests/test_quarantine_routing.py

# Run validation SQL scripts against Databricks workspace
python deployment/validate_deployment.py
```
