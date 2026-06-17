"""
LMIP Bootstrap Script

One-time infrastructure provisioning for the Labor Market Intelligence Platform.

This script creates the foundational Unity Catalog infrastructure:
1. Creates Unity Catalog schemas (9 schemas)
2. Executes DDL files to create tables (40+ tables)
3. Seeds baseline metadata from CSV files (canonical roles, skills, sectors)

This script is IDEMPOTENT - safe to run multiple times.

Usage:
    python deployment/bootstrap.py [--catalog workspace] [--dry-run]
    
Examples:
    # Bootstrap with default catalog
    python deployment/bootstrap.py
    
    # Bootstrap with custom catalog
    python deployment/bootstrap.py --catalog my_catalog
    
    # Dry run (preview changes)
    python deployment/bootstrap.py --dry-run
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone
import csv
from dotenv import load_dotenv
import os
load_dotenv()

from core import DatabricksClientWrapper, SQLExecutor, DeploymentLogger


class LMIPBootstrapper:
    """Bootstrap LMIP infrastructure: schemas, tables, and metadata"""
    
    # Schema definitions
    SCHEMAS = [
        ("metadata", "Source configurations, DQ rules, taxonomy mappings, and pipeline run control"),
        ("bronze", "Raw ingestion layer - API snapshots and response logs"),
        ("silver", "Cleansed and deduplicated job postings with change tracking"),
        ("intermediate", "Intermediate enrichment - role mapping, skill catalog, company canonicalization"),
        ("gold", "Dimensional warehouse - star schema with conformed dimensions and facts"),
        ("reporting", "Pre-aggregated business metrics, KPIs, and trend analyses"),
        ("audit", "Pipeline runs, DQ results, access logs, and compliance tracking"),
        ("publish", "Consumer-ready datasets, reports, and external integrations"),
        ("quarantine", "Failed records, DQ violations, and rejected data for investigation")
    ]
    
    # DDL execution order (dependencies matter)
    DDL_EXECUTION_ORDER = [
        # Metadata layer first
        "metadata_source_config.sql",
        "metadata_pipeline_run_control.sql",
        "metadata_staging_to_current_batches.sql",
        
        # Audit and quarantine
        "audit_audit_pipeline_runs.sql",
        "audit_audit_dq_results.sql",
        "audit_audit_access_events.sql",
        "audit_publish_export_log.sql",
        "audit_publish_manifest_log.sql",
        "quarantine_quarantine_jobs.sql",
        
        # Bronze layer
        "bronze_bronze_job_snapshot.sql",
        "bronze_bronze_api_response_log.sql",
        
        # Silver layer
        "silver_silver_jobs_staging.sql",
        "silver_silver_jobs_current.sql",
        "silver_silver_jobs_history.sql",
        "silver_silver_skill_mapping.sql",
        
        # Intermediate layer
        "intermediate_inter_company_canonical.sql",
        "intermediate_inter_company_map.sql",
        "intermediate_inter_job_role_map.sql",
        "intermediate_inter_job_skill_evidence.sql",
        "intermediate_inter_sector_map.sql",
        "intermediate_inter_skill_catalog.sql",
        
        # Gold layer dimensions
        "gold_dim_date.sql",
        "gold_dim_company.sql",
        "gold_dim_company_alias.sql",
        "gold_dim_role.sql",
        "gold_dim_sector.sql",
        "gold_dim_skill.sql",
        "gold_dim_job.sql",
        "gold_dim_location.sql",
        "gold_dim_source.sql",
        
        # Gold layer bridges and facts
        "gold_bridge_job_skill.sql",
        "gold_fact_job_postings.sql",
        "gold_fact_job_lifecycle.sql",
        "gold_fact_salary.sql",
        "gold_fact_pipeline_runs.sql",
        
        # Reporting layer (aggregates and KPIs)
        "reporting_role_review_queue.sql",
        "reporting_skill_demand.sql",
        "reporting_skill_demand_by_sector.sql",
        "reporting_company_activity.sql",
        "reporting_company_hiring.sql",
        "reporting_hiring_activity.sql",
        "reporting_hiring_trends.sql",
        "reporting_location_trends.sql",
        "reporting_salary_trends.sql",
        "reporting_sector_overview.sql",
        "reporting_pipeline_health.sql",
        
        # Publish layer
        "publish_publish_manifest.sql",
        "publish_publish_bundle_log.sql",
    ]
    
    # Metadata CSV files to seed (file, schema, table)
    METADATA_CSV_FILES = [
        ("canonical_roles.csv", "metadata", "taxonomy_role_canonical"),
        ("role_families.csv", "metadata", "taxonomy_role_families"),
        ("sectors.csv", "metadata", "taxonomy_sectors"),
        ("canonical_skills.csv", "metadata", "taxonomy_skill_catalog"),
    ]
    
    def __init__(
        self, 
        catalog: str = "workspace", 
        project_root: Optional[Path] = None,
        dry_run: bool = False
    ):
        """
        Initialize the LMIP bootstrapper.
        
        Args:
            catalog: Unity Catalog name (default: workspace)
            project_root: Project root directory (default: auto-detect)
            dry_run: If True, preview changes without executing
        """
        self.catalog = catalog
        self.dry_run = dry_run
        
        # Initialize core utilities
        self.db = DatabricksClientWrapper()
        self.executor = SQLExecutor(
            client=self.db.client,
            warehouse_id=self.db.warehouse_id,
            catalog=catalog
        )
        self.logger = DeploymentLogger()
        
        # Auto-detect project root (deployment/ is a subdirectory)
        if project_root is None:
            self.project_root = Path(__file__).parent.parent
        else:
            self.project_root = Path(project_root)
        
        self.ddl_dir = self.project_root / "sql" / "ddl"
        self.metadata_dir = self.project_root / "metadata"
        
        # Track results
        self.results = {
            "schemas": {"created": [], "skipped": [], "failed": []},
            "ddl": {"created": [], "skipped": [], "failed": []},
            "metadata": {"seeded": [], "skipped": [], "failed": []}
        }
    
    def print_banner(self):
        """Print bootstrap banner"""
        self.logger.banner("LMIP INFRASTRUCTURE BOOTSTRAP")
        self.logger.info(f"Target Catalog: {self.catalog}")
        self.logger.info(f"Project Root: {self.project_root}")
        self.logger.info(f"Dry Run: {self.dry_run}")
        self.logger.info(f"Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
    
    def create_schemas(self) -> bool:
        """Create Unity Catalog schemas"""
        self.logger.section("STEP 1: Creating Schemas")
        
        success = True
        
        for schema_name, description in self.SCHEMAS:
            try:
                if self.dry_run:
                    self.logger.info(f"🔍 {schema_name:20} - Would create")
                    self.results["schemas"]["skipped"].append(schema_name)
                    continue
                
                # Use SQLExecutor to create schema
                result=self.executor.create_schema(
                    schema=schema_name,
                    comment=description,
                    if_not_exists=True
                )
                if result["success"]:
                    self.results["schemas"]["created"].append(schema_name)
                    self.logger.item_success(f"{schema_name:20}", "Created")
                else :  
                    e=result["error"]
                    self.results["schemas"]["failed"].append((schema_name, str(e)))
                    self.logger.item_error(f"{schema_name:20}", f"Failed: {str(e)[:50]}")
                    success = False
                    
            except Exception as e:
                self.results["schemas"]["failed"].append((schema_name, str(e)))
                self.logger.item_error(f"{schema_name:20}", f"Failed: {str(e)[:50]}")
                success = False
        
        # Summary
        self.logger.info(f"\nSchemas Summary:")
        self.logger.info(f"  Created: {len(self.results['schemas']['created'])}")
        self.logger.info(f"  Skipped: {len(self.results['schemas']['skipped'])}")
        self.logger.info(f"  Failed:  {len(self.results['schemas']['failed'])}")
        
        return success
    
    def execute_ddl_files(self) -> bool:
        """Execute DDL files to create tables"""
        self.logger.section("STEP 2: Creating Tables (DDL Execution)")
        
        if not self.ddl_dir.exists():
            self.logger.error(f"DDL directory not found: {self.ddl_dir}")
            return False
        
        success = True
        
        for ddl_file in self.DDL_EXECUTION_ORDER:
            ddl_path = self.ddl_dir / ddl_file
            
            if not ddl_path.exists():
                self.logger.item_warning(f"{ddl_file:50}", "File not found: skipping")
                self.results["ddl"]["skipped"].append(ddl_file)
                continue
            
            try:
                if self.dry_run:
                    self.logger.info(f"🔍 {ddl_file:50} - Would execute")
                    self.results["ddl"]["skipped"].append(ddl_file)
                    continue
                
                # Use SQLExecutor to execute DDL file
                result=self.executor.execute_ddl(ddl_path)
                if result["success"]:
                    self.results["ddl"]["created"].append(ddl_file)
                    self.logger.item_success(f"{ddl_file:50}", "Created")
                else:
                    e=result["error"]
                    self.results["ddl"]["failed"].append((ddl_file, str(e)))
                    self.logger.item_error(f"{ddl_file:50}", f"Failed: {str(e)}")
                    success = False
                    print("\nFULL ERROR:")
                    print(e)
                    
            except Exception as e:
                self.results["ddl"]["failed"].append((ddl_file, str(e)))
                self.logger.item_error(f"{ddl_file:50}", f"Failed: {str(e)}")
                success = False
                print("\nFULL ERROR:")
                print(e)
        
        # Summary
        self.logger.info(f"\nDDL Execution Summary:")
        self.logger.info(f"  Created: {len(self.results['ddl']['created'])}")
        self.logger.info(f"  Skipped: {len(self.results['ddl']['skipped'])}")
        self.logger.info(f"  Failed:  {len(self.results['ddl']['failed'])}")
        
        return success
     
    def bootstrap(self) -> bool:
        """
        Execute complete bootstrap workflow.
        
        Returns:
            True if all steps succeeded, False otherwise
        """
        self.print_banner()
        
        # Track overall success
        all_success = True
        
        # Step 1: Create schemas
        if not self.create_schemas():
            self.logger.warning("Schema creation completed with errors")
            all_success = False
        
        # Step 2: Execute DDL files
        if not self.execute_ddl_files():
            self.logger.warning("DDL execution completed with errors")
            all_success = False
        
        # Step 3: Seed metadata
        if not self.seed_metadata():
            self.logger.warning("Metadata seeding completed with errors")
            all_success = False
        
        # Final summary
        self.logger.section("BOOTSTRAP COMPLETE")
        
        if all_success:
            self.logger.panel(
                "🎉 LMIP infrastructure bootstrapped successfully!\n"
                "All schemas, tables, and metadata are ready.\n\n"
                "Next steps:\n"
                "  1. Run: python deployment/deploy_workspace.py\n"
                "  2. Run: python deployment/deploy_jobs.py\n"
                "  3. Run: python deployment/validate_deployment.py",
                title="SUCCESS",
                style="green"
            )
        else:
            self.logger.panel(
                "⚠️  LMIP bootstrap completed with errors.\n"
                "Review the logs above for details.",
                title="WARNING",
                style="yellow"
            )
        
        return all_success


def main():
    """Main entry point for standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Bootstrap LMIP infrastructure: schemas, tables, and metadata",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Bootstrap with default catalog (workspace)
  python deployment/bootstrap.py
  
  # Bootstrap with custom catalog
  python deployment/bootstrap.py --catalog my_catalog
  
  # Dry run (preview changes)
  python deployment/bootstrap.py --dry-run
  
  # Bootstrap with custom project root
  python deployment/bootstrap.py --project-root /path/to/LMIP
"""
    )
    parser.add_argument("--catalog", default="workspace",
                       help="Unity Catalog name (default: workspace)")
    parser.add_argument("--project-root", type=Path, default=None,
                       help="Project root directory (default: auto-detect)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Preview changes without executing")
    
    args = parser.parse_args()
    
    # Create bootstrapper and run
    bootstrapper = LMIPBootstrapper(
        catalog=args.catalog,
        project_root=args.project_root,
        dry_run=args.dry_run
    )
    success = bootstrapper.bootstrap()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
