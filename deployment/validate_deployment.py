"""
Validate LMIP deployment

This module validates that all necessary components are properly deployed:
- Unity Catalog schemas
- Workspace notebooks
- Databricks Jobs
- Required tables
- Metadata seeding (row counts)
"""

from typing import Dict, List, Tuple, Optional
import os
from dotenv import load_dotenv

from core import get_config, DeploymentConfig, DatabricksClientWrapper, DeploymentLogger
load_dotenv()


class DeploymentValidator:
    """Validate LMIP deployment"""
    
    # Metadata tables with minimum expected row counts
    METADATA_TABLES = [
        ("metadata", "taxonomy_role_canonical", 50),       # At least 50 roles
        ("metadata", "taxonomy_skill_catalog", 100),       # At least 100 skills
        ("metadata", "taxonomy_sectors", 10),              # At least 10 sectors
        ("metadata", "taxonomy_role_families", 10),        # At least 10 families
    ]
    
    def __init__(self, config: DeploymentConfig):
        self.config = config
        self.db = DatabricksClientWrapper()
        self.logger = DeploymentLogger()
        self.validation_results = []
    
    def add_result(self, category: str, item: str, status: str, message: str = ""):
        """Add a validation result"""
        self.validation_results.append({
            "category": category,
            "item": item,
            "status": status,
            "message": message
        })
    
    def validate_schema(self, schema_name: str) -> bool:
        """Validate that a schema exists"""
        if self.db.schema_exists(self.config.catalog, schema_name):
            self.add_result("Schema", schema_name, "✅", "Exists")
            return True
        else:
            self.add_result("Schema", schema_name, "❌", "Not found")
            return False
    
    def validate_schemas(self) -> Dict:
        """Validate all required schemas"""
        self.logger.info("\n🗄️  Validating Unity Catalog Schemas")
        
        required_schemas = [
            self.config.bronze_schema,
            self.config.silver_schema,
            self.config.intermediate_schema,
            self.config.gold_schema,
            self.config.reporting_schema,
            self.config.metadata_schema,
            self.config.audit_schema,
            self.config.quarantine_schema,
            self.config.publish_schema
        ]
        
        results = []
        for schema in required_schemas:
            result = self.validate_schema(schema)
            results.append(result)
        
        passed = sum(results)
        self.logger.info(f"  Schemas validated: {passed}/{len(results)}")
        
        return {
            "total": len(results),
            "passed": passed,
            "failed": len(results) - passed
        }
    
    def validate_table(self, schema: str, table: str) -> bool:
        """Validate that a table exists"""
        if self.db.table_exists(self.config.catalog, schema, table):
            self.add_result("Table", table, "✅", f"Exists in {schema}")
            return True
        else:
            self.add_result("Table", table, "❌", f"Not found in {schema}")
            return False
    
    def validate_tables(self) -> Dict:
        """Validate critical tables"""
        self.logger.info("\n📊 Validating Critical Tables")
        
        critical_tables = [
            (self.config.bronze_schema, "bronze_job_snapshot"),
            (self.config.bronze_schema, "bronze_api_response_log"),
            (self.config.audit_schema, "audit_pipeline_runs"),
            (self.config.metadata_schema, "pipeline_run_control"),
        ]
        
        results = []
        for schema, table in critical_tables:
            result = self.validate_table(schema, table)
            results.append(result)
        
        passed = sum(results)
        self.logger.info(f"  Tables validated: {passed}/{len(results)}")
        
        return {
            "total": len(results),
            "passed": passed,
            "failed": len(results) - passed
        }
    
    def validate_metadata_seeded(self) -> Dict:
        """Validate metadata tables have been seeded with baseline data"""
        self.logger.info("\n🌱 Validating Metadata Seeding")
        
        results = []
        for schema, table, min_rows in self.METADATA_TABLES:
            try:
                row_count = self.db.get_table_row_count(self.config.catalog, schema, table)
                
                if row_count is None:
                    self.add_result("Metadata", table, "❌", "Could not query row count")
                    results.append(False)
                elif row_count == 0:
                    self.add_result("Metadata", table, "❌", f"Empty table (expected ≥{min_rows} rows)")
                    results.append(False)
                elif row_count < min_rows:
                    self.add_result("Metadata", table, "⚠️", f"Only {row_count} rows (expected ≥{min_rows})")
                    self.logger.item_warning(f"{table:40} - {row_count} rows (expected ≥{min_rows})")
                    results.append(True)  # Warning, but not a failure
                else:
                    self.add_result("Metadata", table, "✅", f"{row_count} rows (≥{min_rows} expected)")
                    self.logger.item_success(f"{table:40} - {row_count} rows")
                    results.append(True)
                    
            except Exception as e:
                self.add_result("Metadata", table, "❌", f"Error: {str(e)[:50]}")
                self.logger.item_error(f"{table:40} - Failed: {str(e)[:50]}")
                results.append(False)
        
        passed = sum(results)
        self.logger.info(f"\n  Metadata tables validated: {passed}/{len(results)}")
        
        return {
            "total": len(results),
            "passed": passed,
            "failed": len(results) - passed
        }
    
    def validate_notebook(self, notebook_path: str) -> bool:
        """Validate that a notebook exists"""
        try:
            full_path = self.config.get_full_path(notebook_path)
            if self.db.notebook_exists(full_path):
                self.add_result("Notebook", notebook_path, "✅", "Exists")
                return True
            else:
                self.add_result("Notebook", notebook_path, "❌", "Not found")
                return False
        except Exception as e:
            self.add_result("Notebook", notebook_path, "❌", "Not found")
            return False
    
    def validate_notebooks(self) -> Dict:
        """Validate critical notebooks"""
        self.logger.info("\n📓 Validating Critical Notebooks")
        
        critical_notebooks = [
            "notebooks/ingestion/ingest_remotive",
            "notebooks/ingestion/ingest_arbeitnow",
            "notebooks/ingestion/ingest_usajobs",
            "notebooks/ingestion/ingest_adzuna",
            "notebooks/ingestion/ingest_common_helpers",
            "notebooks/ingestion/ingest_manifest_writer",
            "notebooks/init/init_create_schemas",
        ]
        
        results = []
        for notebook in critical_notebooks:
            result = self.validate_notebook(notebook)
            results.append(result)
        
        passed = sum(results)
        self.logger.info(f"  Notebooks validated: {passed}/{len(results)}")
        
        return {
            "total": len(results),
            "passed": passed,
            "failed": len(results) - passed
        }
    
    def validate_job(self, job_name: str) -> bool:
        """Validate that a job exists"""
        try:
            job_id = self.db.get_job_id(job_name)
            if job_id:
                self.add_result("Job", job_name, "✅", f"ID: {job_id}")
                return True
            else:
                self.add_result("Job", job_name, "❌", "Not found")
                return False
        except Exception as e:
            self.add_result("Job", job_name, "❌", f"Error: {e}")
            return False
    
    def validate_jobs(self) -> Dict:
        """Validate deployed jobs"""
        self.logger.info("\n⚙️  Validating Databricks Jobs")
        
        expected_jobs = [
            "LMIP_Initialization",
            "LMIP_Daily_Ingestion",
        ]
        
        results = []
        for job_name in expected_jobs:
            result = self.validate_job(job_name)
            results.append(result)
        
        passed = sum(results)
        self.logger.info(f"  Jobs validated: {passed}/{len(results)}")
        
        return {
            "total": len(results),
            "passed": passed,
            "failed": len(results) - passed
        }
    
    def validate_all(self) -> Dict:
        """Run all validations"""
        self.logger.banner("LMIP DEPLOYMENT VALIDATION")
        self.logger.info(f"Catalog: {self.config.catalog}")
        self.logger.info(f"Workspace Root: {self.config.workspace_root}\n")
        
        # Run all validations
        schemas = self.validate_schemas()
        tables = self.validate_tables()
        metadata = self.validate_metadata_seeded()
        notebooks = self.validate_notebooks()
        jobs = self.validate_jobs()
        
        # Calculate overall results
        total = (schemas["total"] + tables["total"] + metadata["total"] +
                notebooks["total"] + jobs["total"])
        passed = (schemas["passed"] + tables["passed"] + metadata["passed"] +
                 notebooks["passed"] + jobs["passed"])
        failed = total - passed
        
        # Print detailed results table
        self._print_results_table()
        
        # Print overall summary
        self.logger.section("VALIDATION SUMMARY")
        
        # Category breakdown
        self.logger.info("\nBy Category:")
        self.logger.info(f"  Schemas:   {schemas['passed']}/{schemas['total']}")
        self.logger.info(f"  Tables:    {tables['passed']}/{tables['total']}")
        self.logger.info(f"  Metadata:  {metadata['passed']}/{metadata['total']}")
        self.logger.info(f"  Notebooks: {notebooks['passed']}/{notebooks['total']}")
        self.logger.info(f"  Jobs:      {jobs['passed']}/{jobs['total']}")
        
        # Overall stats
        self.logger.info("\nOverall:")
        self.logger.info(f"  Total checks:     {total}")
        self.logger.success(f"  Passed:           {passed}")
        self.logger.error(f"  Failed:           {failed}")
        self.logger.info(f"  Success rate:     {passed/total*100:.1f}%")
        
        if failed == 0:
            self.logger.panel(
                "🎉 All validations passed!\n"
                "Your LMIP deployment is ready for use.",
                title="SUCCESS",
                style="green"
            )
        else:
            self.logger.panel(
                "⚠️  Some validations failed. Review the details above.\n"
                "Hint: Check error messages and re-run specific deployment steps.",
                title="WARNING",
                style="yellow"
            )
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "categories": {
                "schemas": schemas,
                "tables": tables,
                "metadata": metadata,
                "notebooks": notebooks,
                "jobs": jobs
            }
        }
    
    def _print_results_table(self):
        """Print validation results as a table"""
        self.logger.info("\n")
        
        # Build table data
        headers = ["Category", "Item", "Status", "Message"]
        rows = []
        for result in self.validation_results:
            rows.append([
                result["category"],
                result["item"],
                result["status"],
                result["message"]
            ])
        
        self.logger.table(headers, rows, title="🔍 VALIDATION DETAILS")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Validate LMIP deployment",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Show detailed validation output")
    
    args = parser.parse_args()
    
    # Load configuration
    config = get_config()
    
    # Validate configuration
    if not config.validate():
        return 1
    
    # Create validator and run
    validator = DeploymentValidator(config)
    result = validator.validate_all()
    
    # Exit code based on results
    if result["failed"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
