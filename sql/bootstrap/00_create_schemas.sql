-- ============================================================================
-- Bootstrap Script: Create Schemas
-- Purpose: Initialize all schemas required for LMIP data warehouse
-- Expected Output: 9 schemas created (bronze, silver, intermediate, gold, reporting, quarantine, publish, audit, metadata)
-- Dependencies: workspace catalog must exist
-- ============================================================================

-- Create Bronze Layer Schema
CREATE SCHEMA IF NOT EXISTS workspace.bronze
COMMENT 'Bronze layer - raw immutable data from source systems'
MANAGED LOCATION 'dbfs:/lmip/bronze';

-- Create Silver Layer Schema
CREATE SCHEMA IF NOT EXISTS workspace.silver
COMMENT 'Silver layer - cleaned, standardized, and deduplicated data'
MANAGED LOCATION 'dbfs:/lmip/silver';

-- Create Intermediate Layer Schema
CREATE SCHEMA IF NOT EXISTS workspace.intermediate
COMMENT 'Intermediate layer - business logic and canonical mappings'
MANAGED LOCATION 'dbfs:/lmip/intermediate';

-- Create Gold Layer Schema
CREATE SCHEMA IF NOT EXISTS workspace.gold
COMMENT 'Gold layer - dimensional model with facts and dimensions'
MANAGED LOCATION 'dbfs:/lmip/gold';

-- Create Reporting Layer Schema
CREATE SCHEMA IF NOT EXISTS workspace.reporting
COMMENT 'Reporting layer - aggregated analytical marts and views'
MANAGED LOCATION 'dbfs:/lmip/reporting';

-- Create Quarantine Layer Schema
CREATE SCHEMA IF NOT EXISTS workspace.quarantine
COMMENT 'Quarantine layer - records that failed data quality validation'
MANAGED LOCATION 'dbfs:/lmip/quarantine';

-- Create Publish Layer Schema
CREATE SCHEMA IF NOT EXISTS workspace.publish
COMMENT 'Publish layer - consumer-facing exports, manifests, and bundles'
MANAGED LOCATION 'dbfs:/lmip/publish';

-- Create Audit Layer Schema
CREATE SCHEMA IF NOT EXISTS workspace.audit
COMMENT 'Audit layer - pipeline metadata, data quality results, and access logs'
MANAGED LOCATION 'dbfs:/lmip/audit';

-- Create Metadata Layer Schema
CREATE SCHEMA IF NOT EXISTS workspace.metadata
COMMENT 'Metadata layer - pipeline control, source configuration, and batch tracking'
MANAGED LOCATION 'dbfs:/lmip/metadata';

-- Verify schemas were created
SELECT 
  schema_name,
  schema_owner,
  comment
FROM system.information_schema.schemata
WHERE catalog_name = 'workspace'
  AND schema_name IN ('bronze', 'silver', 'intermediate', 'gold', 'reporting', 'quarantine', 'publish', 'audit', 'metadata')
ORDER BY schema_name;

-- End of bootstrap script
