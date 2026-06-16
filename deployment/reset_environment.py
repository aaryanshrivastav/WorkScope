"""
LMIP Environment Reset Script

Safe teardown utility for LMIP Unity Catalog infrastructure.

This script provides controlled environment cleanup:
1. Full reset - Drop all LMIP schemas
2. Partial reset - Drop specific layer(s) (bronze, silver, gold, etc.)
3. Tables-only reset - Drop tables but preserve schemas
4. Schema-only reset - Drop empty schemas

⚠️  WARNING: This script DELETES data. Use with caution.
❌ NEVER drops the Unity Catalog itself - only schemas within it.

Usage:
    python deployment/reset_environment.py --full --confirm
    python deployment/reset_environment.py --layer bronze
    python deployment/reset_environment.py --tables-only
    
Examples:
    # Full reset (requires confirmation)
    python deployment/reset_environment.py --full --confirm
    
    # Drop specific layer
    python deployment/reset_environment.py --layer bronze
    
    # Drop multiple layers
    python deployment/reset_environment.py --layer bronze --layer silver
    
    # Drop tables only (keep schemas)
    python deployment/reset_environment.py --tables-only
    
    # Dry run (preview what would be deleted)
    python deployment/reset_environment.py --full --dry-run
"""

import sys
from pathlib import Path
from typing import List, Optional, Set
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
from databricks.sdk import WorkspaceClient
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm

console = Console()
load_dotenv()


class EnvironmentResetter:
    """Safe teardown utility for LMIP Unity Catalog infrastructure"""
    
    # Schema drop order (reverse of dependencies)
    # Downstream → Upstream to respect foreign keys
    SCHEMA_DROP_ORDER = [
        "publish",      # Publish layer (depends on reporting)
        "reporting",    # Reporting layer (depends on gold)
        "gold",         # Gold layer (depends on intermediate/silver)
        "intermediate", # Intermediate layer (depends on silver)
        "silver",       # Silver layer (depends on bronze)
        "bronze",       # Bronze layer (raw data)
        "quarantine",   # Quarantine (standalone)
        "audit",        # Audit (standalone)
        "metadata"      # Metadata (foundational, drop last)
    ]
    
    # Layer aliases for user-friendly commands
    LAYER_ALIASES = {
        "bronze": ["bronze"],
        "silver": ["silver"],
        "intermediate": ["intermediate"],
        "gold": ["gold"],
        "reporting": ["reporting"],
        "publish": ["publish"],
        "metadata": ["metadata"],
        "audit": ["audit"],
        "quarantine": ["quarantine"],
        # Convenience aliases for multiple schemas
        "medallion": ["bronze", "silver", "gold"],
        "analytics": ["reporting", "publish"],
        "all": SCHEMA_DROP_ORDER
    }
    
    def __init__(
        self, 
        catalog: str = "workspace",
        dry_run: bool = False
    ):
        """
        Initialize the environment resetter.
        
        Args:
            catalog: Unity Catalog name (default: workspace)
            dry_run: If True, preview changes without executing
        """
        self.catalog = catalog
        self.client = WorkspaceClient(
            host=os.getenv("DATABRICKS_HOST"),
            token=os.getenv("DATABRICKS_TOKEN")
        )
        self.dry_run = dry_run
        
        # Track results
        self.results = {
            "schemas_dropped": [],
            "tables_dropped": [],
            "failed": []
        }
    
    def print_banner(self):
        """Print warning banner"""
        banner = """
[bold red]╔══════════════════════════════════════════════════════════╗
║                                                          ║
║           ⚠️  ENVIRONMENT RESET UTILITY                  ║
║                                                          ║
║  WARNING: This operation DELETES data permanently!       ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝[/bold red]
"""
        console.print(banner)
        console.print(f"[bold]Target Catalog:[/bold] {self.catalog}")
        console.print(f"[bold]Dry Run:[/bold] {self.dry_run}")
        console.print(f"[bold]Timestamp:[/bold] {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
    
    def _resolve_layers(self, layers: List[str]) -> Set[str]:
        """Resolve layer names to schema names (supports aliases)"""
        schemas = set()
        for layer in layers:
            layer_lower = layer.lower()
            if layer_lower in self.LAYER_ALIASES:
                schemas.update(self.LAYER_ALIASES[layer_lower])
            else:
                # Direct schema name
                schemas.add(layer_lower)
        return schemas
    
    def _get_schema_tables(self, schema: str) -> List[str]:
        """Get list of tables in a schema"""
        try:
            tables = self.client.tables.list(
                catalog_name=self.catalog,
                schema_name=schema
            )
            return [table.name for table in tables]
        except Exception as e:
            console.print(f"[yellow]⚠️  Could not list tables in {schema}: {e}[/yellow]")
            return []
    
    def _schema_exists(self, schema: str) -> bool:
        """Check if schema exists"""
        try:
            self.client.schemas.get(f"{self.catalog}.{schema}")
            return True
        except Exception:
            return False
    
    def drop_tables_in_schema(self, schema: str) -> bool:
        """Drop all tables in a schema (keep the schema)"""
        console.print(f"\n[bold yellow]Dropping tables in {schema}...[/bold yellow]")
        
        if not self._schema_exists(schema):
            console.print(f"[yellow]⚠️  Schema {schema} does not exist, skipping[/yellow]")
            return True
        
        tables = self._get_schema_tables(schema)
        
        if not tables:
            console.print(f"[dim]  No tables found in {schema}[/dim]")
            return True
        
        success = True
        for table in tables:
            full_table_name = f"{self.catalog}.{schema}.{table}"
            
            try:
                if self.dry_run:
                    console.print(f"[blue]🔍[/blue]   Would drop: {full_table_name}")
                    continue
                
                # Drop table
                result = self.client.statement_execution.execute_statement(
                    warehouse_id=self._get_warehouse_id(),
                    statement=f"DROP TABLE IF EXISTS {full_table_name}",
                    catalog=self.catalog,
                    wait_timeout="0s"
                )
                
                if result.status.state.value == "SUCCEEDED":
                    self.results["tables_dropped"].append(full_table_name)
                    console.print(f"[green]✓[/green]   Dropped: {full_table_name}")
                else:
                    raise Exception(f"Drop failed: {result.status.state}")
                    
            except Exception as e:
                self.results["failed"].append((full_table_name, str(e)))
                console.print(f"[red]✗[/red]   Failed to drop {full_table_name}: {str(e)[:50]}")
                success = False
        
        return success
    
    def drop_schema(self, schema: str, cascade: bool = True) -> bool:
        """Drop a schema (with or without CASCADE)"""
        full_schema_name = f"{self.catalog}.{schema}"
        
        if not self._schema_exists(schema):
            console.print(f"[yellow]⚠️  Schema {schema} does not exist, skipping[/yellow]")
            return True
        
        try:
            cascade_clause = "CASCADE" if cascade else "RESTRICT"
            
            if self.dry_run:
                console.print(f"[blue]🔍[/blue] Would drop schema: {full_schema_name} {cascade_clause}")
                return True
            
            # Drop schema
            result = self.client.statement_execution.execute_statement(
                warehouse_id=self._get_warehouse_id(),
                statement=f"DROP SCHEMA IF EXISTS {full_schema_name} {cascade_clause}",
                catalog=self.catalog,
                wait_timeout="0s"
            )
            
            if result.status.state.value == "SUCCEEDED":
                self.results["schemas_dropped"].append(schema)
                console.print(f"[green]✓[/green] Dropped schema: {full_schema_name}")
                return True
            else:
                raise Exception(f"Drop failed: {result.status.state}")
                
        except Exception as e:
            self.results["failed"].append((full_schema_name, str(e)))
            console.print(f"[red]✗[/red] Failed to drop schema {full_schema_name}: {str(e)[:50]}")
            return False
    
    def reset_full(self, skip_confirmation: bool = False) -> bool:
        """Drop all LMIP schemas"""
        console.print("\n" + "="*60)
        console.print("[bold red]🔥 FULL ENVIRONMENT RESET[/bold red]")
        console.print("="*60 + "\n")
        
        if not self.dry_run and not skip_confirmation:
            console.print(Panel(
                "[bold red]⚠️  WARNING ⚠️[/bold red]\n\n"
                f"This will PERMANENTLY DELETE all LMIP data in catalog: [bold]{self.catalog}[/bold]\n\n"
                "The following schemas will be dropped:\n"
                f"  • {', '.join(self.SCHEMA_DROP_ORDER)}\n\n"
                "[dim]This action cannot be undone.[/dim]",
                border_style="red",
                title="DANGER"
            ))
            
            if not Confirm.ask("\n[bold red]Are you absolutely sure?[/bold red]", default=False):
                console.print("\n[yellow]Reset cancelled by user.[/yellow]")
                return False
            
            # Double confirmation
            console.print("\n[bold red]Final confirmation required.[/bold red]")
            response = console.input("Type 'DELETE ALL' to proceed: ")
            if response != "DELETE ALL":
                console.print("\n[yellow]Reset cancelled. Confirmation text did not match.[/yellow]")
                return False
        
        # Drop schemas in reverse dependency order
        all_success = True
        for schema in self.SCHEMA_DROP_ORDER:
            if not self.drop_schema(schema, cascade=True):
                all_success = False
        
        return all_success
    
    def reset_layers(self, layers: List[str]) -> bool:
        """Drop specific layer(s)"""
        schemas = self._resolve_layers(layers)
        
        console.print("\n" + "="*60)
        console.print("[bold yellow]📦 PARTIAL ENVIRONMENT RESET[/bold yellow]")
        console.print("="*60 + "\n")
        console.print(f"[bold]Target schemas:[/bold] {', '.join(sorted(schemas))}\n")
        
        if not self.dry_run:
            console.print(Panel(
                "[bold yellow]⚠️  WARNING ⚠️[/bold yellow]\n\n"
                f"This will DROP the following schemas in catalog: [bold]{self.catalog}[/bold]\n"
                f"  • {', '.join(sorted(schemas))}\n\n"
                "[dim]All data in these schemas will be permanently deleted.[/dim]",
                border_style="yellow",
                title="CAUTION"
            ))
            
            if not Confirm.ask("\n[bold yellow]Proceed with layer reset?[/bold yellow]", default=False):
                console.print("\n[yellow]Reset cancelled by user.[/yellow]")
                return False
        
        # Drop schemas in dependency order (only those selected)
        all_success = True
        for schema in self.SCHEMA_DROP_ORDER:
            if schema in schemas:
                if not self.drop_schema(schema, cascade=True):
                    all_success = False
        
        return all_success
    
    def reset_tables_only(self, layers: Optional[List[str]] = None) -> bool:
        """Drop tables but preserve schemas"""
        if layers:
            schemas = self._resolve_layers(layers)
        else:
            schemas = set(self.SCHEMA_DROP_ORDER)
        
        console.print("\n" + "="*60)
        console.print("[bold cyan]🗑️  TABLES-ONLY RESET[/bold cyan]")
        console.print("="*60 + "\n")
        console.print(f"[bold]Target schemas:[/bold] {', '.join(sorted(schemas))}")
        console.print("[bold]Action:[/bold] Drop tables, keep schemas\n")
        
        if not self.dry_run:
            if not Confirm.ask("[bold cyan]Proceed with tables-only reset?[/bold cyan]", default=False):
                console.print("\n[yellow]Reset cancelled by user.[/yellow]")
                return False
        
        # Drop tables in each schema (keep schemas)
        all_success = True
        for schema in self.SCHEMA_DROP_ORDER:
            if schema in schemas:
                if not self.drop_tables_in_schema(schema):
                    all_success = False
        
        return all_success
    
    def print_summary(self):
        """Print reset summary"""
        console.print("\n" + "="*60)
        console.print("[bold]📊 RESET SUMMARY[/bold]")
        console.print("="*60)
        
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Category", style="dim")
        table.add_column("Count", justify="right")
        
        table.add_row("Schemas Dropped", str(len(self.results["schemas_dropped"])))
        table.add_row("Tables Dropped", str(len(self.results["tables_dropped"])))
        table.add_row("Failed Operations", str(len(self.results["failed"])), style="red" if self.results["failed"] else "green")
        
        console.print(table)
        
        if self.results["schemas_dropped"]:
            console.print(f"\n[dim]Dropped schemas:[/dim] {', '.join(self.results['schemas_dropped'])}")
        
        if self.results["failed"]:
            console.print("\n[bold red]Failed operations:[/bold red]")
            for item, error in self.results["failed"]:
                console.print(f"  [red]✗[/red] {item}: {error[:50]}")
        
        console.print("="*60)
    
    def _get_warehouse_id(self) -> str:
        """Get SQL warehouse ID for executing statements"""
        import os
        if warehouse_id := os.getenv("DATABRICKS_WAREHOUSE_ID"):
            return warehouse_id
        
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
        description="Reset LMIP environment: safely drop schemas and tables",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full reset (requires confirmation)
  python deployment/reset_environment.py --full --confirm
  
  # Drop specific layer
  python deployment/reset_environment.py --layer bronze
  
  # Drop multiple layers
  python deployment/reset_environment.py --layer bronze --layer silver
  
  # Drop tables only (keep schemas)
  python deployment/reset_environment.py --tables-only
  
  # Drop tables in specific layer
  python deployment/reset_environment.py --tables-only --layer gold
  
  # Dry run (preview what would be deleted)
  python deployment/reset_environment.py --full --dry-run
  
  # Use convenience alias (medallion = bronze + silver + gold)
  python deployment/reset_environment.py --layer medallion

Layer Aliases:
  medallion:  bronze, silver, gold
  analytics:  reporting, publish
  all:        All LMIP schemas
"""
    )
    parser.add_argument("--catalog", default="workspace",
                       help="Unity Catalog name (default: workspace)")
    parser.add_argument("--full", action="store_true",
                       help="Drop all LMIP schemas (requires confirmation)")
    parser.add_argument("--layer", action="append", dest="layers",
                       help="Drop specific layer(s). Can be used multiple times.")
    parser.add_argument("--tables-only", action="store_true",
                       help="Drop tables but preserve schemas")
    parser.add_argument("--confirm", action="store_true",
                       help="Skip confirmation prompts (use with caution)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Preview changes without executing")
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.full and not args.layers and not args.tables_only:
        parser.error("Must specify one of: --full, --layer <name>, or --tables-only")
    
    # Create resetter
    resetter = EnvironmentResetter(
        catalog=args.catalog,
        dry_run=args.dry_run
    )
    
    resetter.print_banner()
    
    # Execute reset operation
    success = True
    
    if args.full:
        success = resetter.reset_full(skip_confirmation=args.confirm)
    elif args.tables_only:
        success = resetter.reset_tables_only(layers=args.layers)
    elif args.layers:
        success = resetter.reset_layers(args.layers)
    
    # Print summary
    resetter.print_summary()
    
    # Final message
    if success:
        console.print(Panel(
            "[bold green]✅ Reset completed successfully[/bold green]\n\n"
            "[dim]Next steps:[/dim]\n"
            "  • Run: python deployment/bootstrap.py (to recreate infrastructure)\n"
            "  • Run: python deployment/deploy_all.py (full redeployment)",
            border_style="green"
        ))
    else:
        console.print(Panel(
            "[bold yellow]⚠️  Reset completed with errors[/bold yellow]\n\n"
            "Review the logs above for details.",
            border_style="yellow"
        ))
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
