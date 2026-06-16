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
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.catalog import SchemaInfo
from rich.console import Console
from rich.table import Table

from config import get_config, DeploymentConfig
load_dotenv()

console = Console()


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
        self.w = WorkspaceClient(
            host=os.getenv("DATABRICKS_HOST"),
            token=os.getenv("DATABRICKS_TOKEN")
        )
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
        try:
            schema_full_name = f"{self.config.catalog}.{schema_name}"
            schema = self.w.schemas.get(schema_full_name)
            self.add_result("Schema", schema_name, "✅", "Exists")
            return True
        except Exception as e:
            self.add_result("Schema", schema_name, "❌", f"Not found: {e}")
            return False
    
    def validate_schemas(self) -> Dict:
        """Validate all required schemas"""
        console.print("\n[bold cyan]🗄️  Validating Unity Catalog Schemas[/bold cyan]")
        
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
        console.print(f"  Schemas validated: [green]{passed}[/green]/[bold]{len(results)}[/bold]")
        
        return {
            "total": len(results),
            "passed": passed,
            "failed": len(results) - passed
        }
    
    def validate_table(self, schema: str, table: str) -> bool:
        """Validate that a table exists"""
        try:
            table_full_name = f"{self.config.catalog}.{schema}.{table}"
            table_info = self.w.tables.get(table_full_name)
            self.add_result("Table", table, "✅", f"Exists in {schema}")
            return True
        except Exception as e:
            self.add_result("Table", table, "❌", f"Not found in {schema}")
            return False
    
    def validate_tables(self) -> Dict:
        """Validate critical tables"""
        console.print("\n[bold cyan]📊 Validating Critical Tables[/bold cyan]")
        
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
        console.print(f"  Tables validated: [green]{passed}[/green]/[bold]{len(results)}[/bold]")
        
        return {
            "total": len(results),
            "passed": passed,
            "failed": len(results) - passed
        }
    
    def get_table_row_count(self, schema: str, table: str) -> Optional[int]:
        """Get row count for a table"""
        try:
            full_table = f"{self.config.catalog}.{schema}.{table}"
            result = self.w.statement_execution.execute_statement(
                warehouse_id=self._get_warehouse_id(),
                statement=f"SELECT COUNT(*) as cnt FROM {full_table}",
                catalog=self.config.catalog,
                wait_timeout="0s"
            )
            
            if result.status.state.value == "SUCCEEDED" and result.result:
                if result.result.data_array and len(result.result.data_array) > 0:
                    return int(result.result.data_array[0][0])
            
            return None
        except Exception as e:
            console.print(f"[yellow]⚠️  Could not get row count for {schema}.{table}: {e}[/yellow]")
            return None
    
    def validate_metadata_seeded(self) -> Dict:
        """Validate metadata tables have been seeded with baseline data"""
        console.print("\n[bold cyan]🌱 Validating Metadata Seeding[/bold cyan]")
        
        results = []
        for schema, table, min_rows in self.METADATA_TABLES:
            try:
                row_count = self.get_table_row_count(schema, table)
                
                if row_count is None:
                    self.add_result("Metadata", table, "❌", "Could not query row count")
                    results.append(False)
                elif row_count == 0:
                    self.add_result("Metadata", table, "❌", f"Empty table (expected ≥{min_rows} rows)")
                    results.append(False)
                elif row_count < min_rows:
                    self.add_result("Metadata", table, "⚠️", f"Only {row_count} rows (expected ≥{min_rows})")
                    console.print(f"  [yellow]⚠️[/yellow]  {table:40} - {row_count} rows (expected ≥{min_rows})")
                    results.append(True)  # Warning, but not a failure
                else:
                    self.add_result("Metadata", table, "✅", f"{row_count} rows (≥{min_rows} expected)")
                    console.print(f"  [green]✓[/green]  {table:40} - {row_count} rows")
                    results.append(True)
                    
            except Exception as e:
                self.add_result("Metadata", table, "❌", f"Error: {str(e)[:50]}")
                console.print(f"  [red]✗[/red]  {table:40} - Failed: {str(e)[:50]}")
                results.append(False)
        
        passed = sum(results)
        console.print(f"\n  Metadata tables validated: [green]{passed}[/green]/[bold]{len(results)}[/bold]")
        
        return {
            "total": len(results),
            "passed": passed,
            "failed": len(results) - passed
        }
    
    def validate_notebook(self, notebook_path: str) -> bool:
        """Validate that a notebook exists"""
        try:
            full_path = self.config.get_full_path(notebook_path)
            obj = self.w.workspace.get_status(full_path)
            self.add_result("Notebook", notebook_path, "✅", "Exists")
            return True
        except Exception as e:
            self.add_result("Notebook", notebook_path, "❌", "Not found")
            return False
    
    def validate_notebooks(self) -> Dict:
        """Validate critical notebooks"""
        console.print("\n[bold cyan]📓 Validating Critical Notebooks[/bold cyan]")
        
        critical_notebooks = [
            "notebooks/ingestion/ingest_remotive",
            "notebooks/ingestion/ingest_arbeitnow",
            "notebooks/ingestion/ingest_common_helpers",
            "notebooks/ingestion/ingest_manifest_writer",
            "notebooks/init/init_create_schemas",
        ]
        
        results = []
        for notebook in critical_notebooks:
            result = self.validate_notebook(notebook)
            results.append(result)
        
        passed = sum(results)
        console.print(f"  Notebooks validated: [green]{passed}[/green]/[bold]{len(results)}[/bold]")
        
        return {
            "total": len(results),
            "passed": passed,
            "failed": len(results) - passed
        }
    
    def validate_job(self, job_name: str) -> bool:
        """Validate that a job exists"""
        try:
            jobs = self.w.jobs.list(name=job_name)
            for job in jobs:
                if job.settings.name == job_name:
                    self.add_result("Job", job_name, "✅", f"ID: {job.job_id}")
                    return True
            self.add_result("Job", job_name, "❌", "Not found")
            return False
        except Exception as e:
            self.add_result("Job", job_name, "❌", f"Error: {e}")
            return False
    
    def validate_jobs(self) -> Dict:
        """Validate deployed jobs"""
        console.print("\n[bold cyan]⚙️  Validating Databricks Jobs[/bold cyan]")
        
        expected_jobs = [
            "LMIP_Initialization",
            "LMIP_Daily_Ingestion",
        ]
        
        results = []
        for job_name in expected_jobs:
            result = self.validate_job(job_name)
            results.append(result)
        
        passed = sum(results)
        console.print(f"  Jobs validated: [green]{passed}[/green]/[bold]{len(results)}[/bold]")
        
        return {
            "total": len(results),
            "passed": passed,
            "failed": len(results) - passed
        }
    
    def validate_all(self) -> Dict:
        """Run all validations"""
        console.print("\n[bold magenta]🔍 Starting LMIP Deployment Validation[/bold magenta]")
        console.print(f"[dim]Catalog: {self.config.catalog}[/dim]")
        console.print(f"[dim]Workspace Root: {self.config.workspace_root}[/dim]\n")
        
        # Run all validations
        schemas = self.validate_schemas()
        tables = self.validate_tables()
        metadata = self.validate_metadata_seeded()  # NEW: Row count validation
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
        console.print("\n" + "="*60)
        console.print("[bold]📊 VALIDATION SUMMARY[/bold]")
        console.print("="*60)
        
        # Category breakdown
        console.print(f"\n[bold]By Category:[/bold]")
        console.print(f"  Schemas:   {schemas['passed']}/{schemas['total']}")
        console.print(f"  Tables:    {tables['passed']}/{tables['total']}")
        console.print(f"  Metadata:  {metadata['passed']}/{metadata['total']}")
        console.print(f"  Notebooks: {notebooks['passed']}/{notebooks['total']}")
        console.print(f"  Jobs:      {jobs['passed']}/{jobs['total']}")
        
        # Overall stats
        console.print(f"\n[bold]Overall:[/bold]")
        console.print(f"  Total checks:     {total}")
        console.print(f"  [green]✅ Passed:[/green]        {passed}")
        console.print(f"  [red]❌ Failed:[/red]        {failed}")
        console.print(f"  [bold]Success rate:[/bold]   {passed/total*100:.1f}%")
        console.print("="*60)
        
        if failed == 0:
            console.print("\n[bold green]🎉 All validations passed![/bold green]")
            console.print("[dim]Your LMIP deployment is ready for use.[/dim]")
        else:
            console.print("\n[bold red]⚠️  Some validations failed. Review the details above.[/bold red]")
            console.print("[dim]Hint: Check error messages and re-run specific deployment steps.[/dim]")
        
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
        console.print("\n")
        
        table = Table(title="🔍 VALIDATION DETAILS", show_header=True, header_style="bold cyan")
        table.add_column("Category", style="cyan")
        table.add_column("Item", style="white")
        table.add_column("Status", style="white")
        table.add_column("Message", style="dim")
        
        for result in self.validation_results:
            status_color = "green" if result["status"] == "✅" else ("yellow" if result["status"] == "⚠️" else "red")
            table.add_row(
                result["category"],
                result["item"],
                f"[{status_color}]{result['status']}[/{status_color}]",
                result["message"]
            )
        
        console.print(table)
    
    def _get_warehouse_id(self) -> str:
        """Get SQL warehouse ID for executing statements"""
        import os
        if warehouse_id := os.getenv("DATABRICKS_WAREHOUSE_ID"):
            return warehouse_id
        
        warehouses = list(self.w.warehouses.list())
        
        if not warehouses:
            raise Exception("No SQL warehouses found. Please create one first.")
        
        # Prefer serverless warehouses
        for wh in warehouses:
            if wh.enable_serverless_compute:
                return wh.id
        
        # Fall back to first warehouse
        return warehouses[0].id


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
