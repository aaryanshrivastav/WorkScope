"""
LMIP Initialization Script

Consolidates all init notebooks into a single Python script that:
1. Creates Unity Catalog schemas
2. Executes DDL files to create tables
3. Seeds metadata tables from CSV files
4. Validates the environment

This script replaces the 5-notebook init workflow and can be called
from deployment scripts or run standalone.

Usage:
    from deployment.init import LMIPInitializer
    
    initializer = LMIPInitializer(catalog="workspace")
    success = initializer.initialize()
    
Or run directly:
    python deployment/init.py --catalog workspace
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timezone
import csv
import requests

from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import NotFound, ResourceConflict
from rich.console import Console
from rich.table import Table
from rich.panel import Panel


console = Console()


class LMIPInitializer:
    """Initialize LMIP environment: schemas, tables, and metadata"""
    
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
    
    # Metadata CSV files to seed
    METADATA_CSV_FILES = [
        ("canonical_roles.csv", "metadata", "taxonomy_role_canonical"),
        ("role_families.csv", "metadata", "taxonomy_role_families"),
        ("sectors.csv", "metadata", "taxonomy_sectors"),
        ("canonical_skills.csv", "metadata", "taxonomy_skill_catalog"),
    ]
    
    # API endpoints to validate
    API_ENDPOINTS = [
        "https://remotive.com/api/remote-jobs",
        "https://www.arbeitnow.com/api/job-board-api"
    ]
    
    def __init__(self, catalog: str = "workspace", project_root: Optional[Path] = None):
        """
        Initialize the LMIP initializer.
        
        Args:
            catalog: Unity Catalog name (default: workspace)
            project_root: Project root directory (default: auto-detect from script location)
        """
        self.catalog = catalog
        self.client = WorkspaceClient()
        
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
            "metadata": {"seeded": [], "skipped": [], "failed": []},
            "validation": {"passed": [], "warned": [], "failed": []}
        }
    
    def print_banner(self):
        """Print initialization banner"""
        banner = """
[bold cyan]╔══════════════════════════════════════════════════════════╗
║                                                          ║
║           LMIP ENVIRONMENT INITIALIZATION                ║
║                                                          ║
║  Labor Market Intelligence Platform - Setup & Validate  ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝[/bold cyan]
"""
        console.print(banner)
        console.print(f"[bold]Target Catalog:[/bold] {self.catalog}")
        console.print(f"[bold]Project Root:[/bold] {self.project_root}")
        console.print(f"[bold]Timestamp:[/bold] {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
    
    def create_schemas(self) -> bool:
        """Create Unity Catalog schemas"""
        console.print("\n" + "="*60)
        console.print("[bold magenta]📦 STEP 1: Creating Schemas[/bold magenta]")
        console.print("="*60 + "\n")
        
        success = True
        
        for schema_name, description in self.SCHEMAS:
            try:
                # Try to create schema
                sql = f"CREATE SCHEMA IF NOT EXISTS {self.catalog}.{schema_name} COMMENT '{description}'"
                
                # Execute via SQL statement API
                result = self.client.statement_execution.execute_statement(
                    warehouse_id=self._get_warehouse_id(),
                    statement=sql,
                    catalog=self.catalog,
                    wait_timeout="30s"
                )
                
                if result.status.state.value == "SUCCEEDED":
                    # Check if it was created or already existed
                    # Since we use IF NOT EXISTS, we need to verify
                    verify_sql = f"DESCRIBE SCHEMA {self.catalog}.{schema_name}"
                    verify_result = self.client.statement_execution.execute_statement(
                        warehouse_id=self._get_warehouse_id(),
                        statement=verify_sql,
                        catalog=self.catalog,
                        wait_timeout="10s"
                    )
                    
                    if verify_result.status.state.value == "SUCCEEDED":
                        self.results["schemas"]["created"].append(schema_name)
                        console.print(f"[green]✓[/green] {schema_name:20} - Created")
                    else:
                        self.results["schemas"]["skipped"].append(schema_name)
                        console.print(f"[yellow]⚠[/yellow] {schema_name:20} - Already exists")
                else:
                    raise Exception(f"Statement execution failed: {result.status.state}")
                    
            except Exception as e:
                self.results["schemas"]["failed"].append((schema_name, str(e)))
                console.print(f"[red]✗[/red] {schema_name:20} - Failed: {str(e)[:50]}")
                success = False
        
        # Summary
        console.print(f"\n[bold]Schemas Summary:[/bold]")
        console.print(f"  Created: {len(self.results['schemas']['created'])}")
        console.print(f"  Skipped: {len(self.results['schemas']['skipped'])}")
        console.print(f"  Failed:  {len(self.results['schemas']['failed'])}")
        
        return success
    
    def execute_ddl_files(self) -> bool:
        """Execute DDL files to create tables"""
        console.print("\n" + "="*60)
        console.print("[bold magenta]🏗️  STEP 2: Creating Tables (DDL Execution)[/bold magenta]")
        console.print("="*60 + "\n")
        
        if not self.ddl_dir.exists():
            console.print(f"[red]✗ DDL directory not found: {self.ddl_dir}[/red]")
            return False
        
        success = True
        
        for ddl_file in self.DDL_EXECUTION_ORDER:
            ddl_path = self.ddl_dir / ddl_file
            
            if not ddl_path.exists():
                console.print(f"[yellow]⚠[/yellow] {ddl_file:50} - File not found, skipping")
                self.results["ddl"]["skipped"].append(ddl_file)
                continue
            
            try:
                # Read DDL file
                with open(ddl_path, 'r') as f:
                    ddl_sql = f.read()
                
                # Execute DDL
                result = self.client.statement_execution.execute_statement(
                    warehouse_id=self._get_warehouse_id(),
                    statement=ddl_sql,
                    catalog=self.catalog,
                    wait_timeout="60s"
                )
                
                if result.status.state.value == "SUCCEEDED":
                    self.results["ddl"]["created"].append(ddl_file)
                    console.print(f"[green]✓[/green] {ddl_file:50} - Created")
                else:
                    raise Exception(f"Statement execution failed: {result.status.state}")
                    
            except Exception as e:
                self.results["ddl"]["failed"].append((ddl_file, str(e)))
                console.print(f"[red]✗[/red] {ddl_file:50} - Failed: {str(e)[:50]}")
                success = False
        
        # Summary
        console.print(f"\n[bold]DDL Execution Summary:[/bold]")
        console.print(f"  Created: {len(self.results['ddl']['created'])}")
        console.print(f"  Skipped: {len(self.results['ddl']['skipped'])}")
        console.print(f"  Failed:  {len(self.results['ddl']['failed'])}")
        
        return success
    
    def seed_metadata(self) -> bool:
        """Seed metadata tables from CSV files"""
        console.print("\n" + "="*60)
        console.print("[bold magenta]🌱 STEP 3: Seeding Metadata Tables[/bold magenta]")
        console.print("="*60 + "\n")
        
        if not self.metadata_dir.exists():
            console.print(f"[red]✗ Metadata directory not found: {self.metadata_dir}[/red]")
            return False
        
        success = True
        
        for csv_file, schema, table in self.METADATA_CSV_FILES:
            csv_path = self.metadata_dir / csv_file
            
            if not csv_path.exists():
                console.print(f"[yellow]⚠[/yellow] {csv_file:40} - File not found, skipping")
                self.results["metadata"]["skipped"].append(csv_file)
                continue
            
            try:
                # Read CSV file
                with open(csv_path, 'r') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                
                if not rows:
                    console.print(f"[yellow]⚠[/yellow] {csv_file:40} - Empty file, skipping")
                    self.results["metadata"]["skipped"].append(csv_file)
                    continue
                
                # Build INSERT statement
                columns = list(rows[0].keys())
                full_table = f"{self.catalog}.{schema}.{table}"
                
                # Add created_at/updated_at if not present
                if 'created_at' not in columns:
                    for row in rows:
                        row['created_at'] = datetime.now(timezone.utc).isoformat()
                    columns.append('created_at')
                
                if 'updated_at' not in columns:
                    for row in rows:
                        row['updated_at'] = datetime.now(timezone.utc).isoformat()
                    columns.append('updated_at')
                
                # Build VALUES clause
                values_list = []
                for row in rows:
                    values = []
                    for col in columns:
                        value = row.get(col, '')
                        # Escape quotes and wrap strings
                        if value is None or value == '':
                            values.append('NULL')
                        else:
                            # Escape single quotes
                            escaped_value = str(value).replace("'", "''")
                            values.append(f"'{escaped_value}'")
                    values_list.append(f"({', '.join(values)})")
                
                values_str = ',\\n  '.join(values_list)
                
                # Use MERGE to make it idempotent (upsert)
                # First, try to create a temp view and merge
                insert_sql = f"""
                INSERT INTO {full_table} ({', '.join(columns)})
                VALUES
                  {values_str}
                """
                
                result = self.client.statement_execution.execute_statement(
                    warehouse_id=self._get_warehouse_id(),
                    statement=insert_sql,
                    catalog=self.catalog,
                    wait_timeout="60s"
                )
                
                if result.status.state.value == "SUCCEEDED":
                    self.results["metadata"]["seeded"].append((csv_file, len(rows)))
                    console.print(f"[green]✓[/green] {csv_file:40} - Seeded {len(rows)} records")
                else:
                    raise Exception(f"Statement execution failed: {result.status.state}")
                    
            except Exception as e:
                self.results["metadata"]["failed"].append((csv_file, str(e)))
                console.print(f"[red]✗[/red] {csv_file:40} - Failed: {str(e)[:50]}")
                success = False
        
        # Summary
        console.print(f"\n[bold]Metadata Seeding Summary:[/bold]")
        console.print(f"  Seeded: {len(self.results['metadata']['seeded'])}")
        console.print(f"  Skipped: {len(self.results['metadata']['skipped'])}")
        console.print(f"  Failed:  {len(self.results['metadata']['failed'])}")
        
        return success
    
    def validate_environment(self) -> Tuple[bool, str]:
        """
        Validate the environment setup.
        
        Returns:
            Tuple of (success, status) where status is SUCCESS, WARNINGS, or FAILED
        """
        console.print("\n" + "="*60)
        console.print("[bold magenta]🔍 STEP 4: Environment Validation[/bold magenta]")
        console.print("="*60 + "\n")
        
        # Python version check
        console.print("[bold]Python Environment[/bold]")
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        if sys.version_info >= (3, 10):
            self.results["validation"]["passed"].append(("Python Version", python_version))
            console.print(f"[green]✓[/green] Python {python_version}")
        else:
            self.results["validation"]["warned"].append(("Python Version", f"{python_version} (recommended >= 3.10)"))
            console.print(f"[yellow]⚠[/yellow] Python {python_version} (recommended >= 3.10)")
        
        # Required packages
        required_packages = ["databricks.sdk", "requests", "rich"]
        for package in required_packages:
            try:
                __import__(package.replace(".sdk", ""))
                self.results["validation"]["passed"].append((f"Package: {package}", "Installed"))
                console.print(f"[green]✓[/green] {package} - Installed")
            except ImportError:
                self.results["validation"]["failed"].append((f"Package: {package}", "Not installed"))
                console.print(f"[red]✗[/red] {package} - Not installed")
        
        # Catalog validation
        console.print(f"\n[bold]Catalog and Schemas[/bold]")
        try:
            # Verify schemas exist
            for schema_name, _ in self.SCHEMAS:
                try:
                    verify_sql = f"DESCRIBE SCHEMA {self.catalog}.{schema_name}"
                    result = self.client.statement_execution.execute_statement(
                        warehouse_id=self._get_warehouse_id(),
                        statement=verify_sql,
                        catalog=self.catalog,
                        wait_timeout="10s"
                    )
                    
                    if result.status.state.value == "SUCCEEDED":
                        self.results["validation"]["passed"].append((f"Schema: {schema_name}", "Exists"))
                        console.print(f"[green]✓[/green] Schema: {schema_name}")
                    else:
                        self.results["validation"]["failed"].append((f"Schema: {schema_name}", "Does not exist"))
                        console.print(f"[red]✗[/red] Schema: {schema_name} - Does not exist")
                        
                except Exception as e:
                    self.results["validation"]["failed"].append((f"Schema: {schema_name}", str(e)))
                    console.print(f"[red]✗[/red] Schema: {schema_name} - {str(e)[:50]}")
        
        except Exception as e:
            self.results["validation"]["failed"].append(("Schema Validation", str(e)))
            console.print(f"[red]✗[/red] Schema validation failed: {str(e)[:50]}")
        
        # Network connectivity
        console.print(f"\n[bold]Network Connectivity[/bold]")
        for endpoint in self.API_ENDPOINTS:
            try:
                response = requests.get(endpoint, timeout=10)
                if response.status_code == 200:
                    self.results["validation"]["passed"].append((f"API: {endpoint}", f"Reachable (HTTP {response.status_code})"))
                    console.print(f"[green]✓[/green] {endpoint} - Reachable")
                else:
                    self.results["validation"]["warned"].append((f"API: {endpoint}", f"HTTP {response.status_code}"))
                    console.print(f"[yellow]⚠[/yellow] {endpoint} - HTTP {response.status_code}")
            except requests.exceptions.Timeout:
                self.results["validation"]["warned"].append((f"API: {endpoint}", "Timeout"))
                console.print(f"[yellow]⚠[/yellow] {endpoint} - Timeout")
            except Exception as e:
                self.results["validation"]["warned"].append((f"API: {endpoint}", str(e)[:50]))
                console.print(f"[yellow]⚠[/yellow] {endpoint} - {str(e)[:50]}")
        
        # Determine overall status
        passed = len(self.results["validation"]["passed"])
        warned = len(self.results["validation"]["warned"])
        failed = len(self.results["validation"]["failed"])
        
        console.print(f"\n[bold]Validation Summary:[/bold]")
        console.print(f"  Passed:   {passed}")
        console.print(f"  Warnings: {warned}")
        console.print(f"  Failed:   {failed}")
        
        if failed > 0:
            return False, "FAILED"
        elif warned > 0:
            return True, "WARNINGS"
        else:
            return True, "SUCCESS"
    
    def initialize(self) -> bool:
        """
        Execute complete initialization workflow.
        
        Returns:
            True if all steps succeeded, False otherwise
        """
        self.print_banner()
        
        # Track overall success
        all_success = True
        
        # Step 1: Create schemas
        if not self.create_schemas():
            console.print("[yellow]⚠️  Schema creation completed with errors[/yellow]")
            all_success = False
        
        # Step 2: Execute DDL files
        if not self.execute_ddl_files():
            console.print("[yellow]⚠️  DDL execution completed with errors[/yellow]")
            all_success = False
        
        # Step 3: Seed metadata
        if not self.seed_metadata():
            console.print("[yellow]⚠️  Metadata seeding completed with errors[/yellow]")
            all_success = False
        
        # Step 4: Validate environment
        validation_success, validation_status = self.validate_environment()
        if not validation_success:
            console.print("[yellow]⚠️  Environment validation completed with errors[/yellow]")
            all_success = False
        
        # Final summary
        console.print("\n" + "="*60)
        console.print("[bold]🏁 INITIALIZATION COMPLETE[/bold]")
        console.print("="*60)
        
        if all_success and validation_status == "SUCCESS":
            console.print(Panel(
                "[bold green]🎉 LMIP environment initialized successfully![/bold green]\\n"
                "All schemas, tables, and metadata are ready.",
                border_style="green"
            ))
        elif all_success and validation_status == "WARNINGS":
            console.print(Panel(
                "[bold yellow]⚠️  LMIP environment initialized with warnings.[/bold yellow]\\n"
                "Review the validation warnings above.",
                border_style="yellow"
            ))
        else:
            console.print(Panel(
                "[bold red]❌ LMIP environment initialization encountered errors.[/bold red]\\n"
                "Review the logs above for details.",
                border_style="red"
            ))
        
        console.print("="*60)
        
        return all_success
    
    def _get_warehouse_id(self) -> str:
        """
        Get SQL warehouse ID for executing statements.
        Uses the first available serverless warehouse, or falls back to any warehouse.
        """
        # Try to get from environment variable first
        import os
        if warehouse_id := os.getenv("DATABRICKS_WAREHOUSE_ID"):
            return warehouse_id
        
        # Otherwise, find a warehouse
        warehouses = list(self.client.warehouses.list())
        
        if not warehouses:
            raise Exception("No SQL warehouses found. Please create one first.")
        
        # Prefer serverless warehouses
        for wh in warehouses:
            if wh.enable_serverless_compute:
                return wh.id
        
        # Fall back to first warehouse
        return warehouses[0].id


def main():
    """Main entry point for standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Initialize LMIP environment: schemas, tables, and metadata",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize with default catalog (workspace)
  python deployment/init.py
  
  # Initialize with custom catalog
  python deployment/init.py --catalog my_catalog
  
  # Initialize with custom project root
  python deployment/init.py --project-root /path/to/LMIP
"""
    )
    parser.add_argument("--catalog", default="workspace",
                       help="Unity Catalog name (default: workspace)")
    parser.add_argument("--project-root", type=Path, default=None,
                       help="Project root directory (default: auto-detect)")
    
    args = parser.parse_args()
    
    # Create initializer and run
    initializer = LMIPInitializer(
        catalog=args.catalog,
        project_root=args.project_root
    )
    success = initializer.initialize()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
