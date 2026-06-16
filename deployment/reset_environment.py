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
from rich.prompt import Confirm

from core import DatabricksClientWrapper, SQLExecutor, DeploymentLogger

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
        self.dry_run = dry_run
        
        # Initialize core utilities
        self.db = DatabricksClientWrapper()
        self.executor = SQLExecutor(
            client=self.db.client,
            warehouse_id=self.db.warehouse_id,
            catalog=catalog
        )
        self.logger = DeploymentLogger()
        
        # Track results
        self.results = {
            "schemas_dropped": [],
            "tables_dropped": [],
            "failed": []
        }
    
    def print_banner(self):
        """Print warning banner"""
        self.logger.panel(
            "⚠️  WARNING: This operation DELETES data permanently!",
            title="ENVIRONMENT RESET UTILITY",
            style="error"
        )
        self.logger.info(f"Target Catalog: {self.catalog}")
        self.logger.info(f"Dry Run: {self.dry_run}")
        self.logger.info(f"Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
    
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
    
    def drop_tables_in_schema(self, schema: str) -> bool:
        """Drop all tables in a schema (keep the schema)"""
        self.logger.warning(f"\nDropping tables in {schema}...")
        
        if not self.db.schema_exists(self.catalog, schema):
            self.logger.item_warning(f"Schema {schema} does not exist, skipping")
            return True
        
        tables = self.db.list_tables(self.catalog, schema)
        
        if not tables:
            self.logger.info(f"  No tables found in {schema}")
            return True
        
        success = True
        for table in tables:
            full_table_name = f"{self.catalog}.{schema}.{table}"
            
            try:
                if self.dry_run:
                    self.logger.info(f"🔍   Would drop: {full_table_name}")
                    continue
                
                # Use SQLExecutor to drop table
                self.executor.drop_table(schema, table)
                
                self.results["tables_dropped"].append(full_table_name)
                self.logger.item_success(f"Dropped: {full_table_name}")
                    
            except Exception as e:
                self.results["failed"].append((full_table_name, str(e)))
                self.logger.item_error(f"Failed to drop {full_table_name}: {str(e)[:50]}")
                success = False
        
        return success
    
    def drop_schema(self, schema: str, cascade: bool = True) -> bool:
        """Drop a schema (with or without CASCADE)"""
        full_schema_name = f"{self.catalog}.{schema}"
        
        if not self.db.schema_exists(self.catalog, schema):
            self.logger.item_warning(f"Schema {schema} does not exist, skipping")
            return True
        
        try:
            if self.dry_run:
                self.logger.info(f"🔍 Would drop schema: {full_schema_name} {'CASCADE' if cascade else 'RESTRICT'}")
                return True
            
            # Use SQLExecutor to drop schema
            self.executor.drop_schema(schema, cascade=cascade)
            
            self.results["schemas_dropped"].append(schema)
            self.logger.item_success(f"Dropped schema: {full_schema_name}")
            return True
                
        except Exception as e:
            self.results["failed"].append((full_schema_name, str(e)))
            self.logger.item_error(f"Failed to drop schema {full_schema_name}: {str(e)[:50]}")
            return False
    
    def reset_full(self, skip_confirmation: bool = False) -> bool:
        """Drop all LMIP schemas"""
        self.logger.section("🔥 FULL ENVIRONMENT RESET")
        
        if not self.dry_run and not skip_confirmation:
            self.logger.panel(
                f"⚠️  WARNING ⚠️\n\n"
                f"This will PERMANENTLY DELETE all LMIP data in catalog: {self.catalog}\n\n"
                f"The following schemas will be dropped:\n"
                f"  • {', '.join(self.SCHEMA_DROP_ORDER)}\n\n"
                f"This action cannot be undone.",
                title="DANGER",
                style="error"
            )
            
            if not Confirm.ask("\n[bold red]Are you absolutely sure?[/bold red]", default=False):
                self.logger.warning("\nReset cancelled by user.")
                return False
            
            # Double confirmation
            self.logger.error("\nFinal confirmation required.")
            from rich.console import Console
            console = Console()
            response = console.input("Type 'DELETE ALL' to proceed: ")
            if response != "DELETE ALL":
                self.logger.warning("\nReset cancelled. Confirmation text did not match.")
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
        
        self.logger.section("📦 PARTIAL ENVIRONMENT RESET")
        self.logger.info(f"Target schemas: {', '.join(sorted(schemas))}\n")
        
        if not self.dry_run:
            self.logger.panel(
                f"⚠️  WARNING ⚠️\n\n"
                f"This will DROP the following schemas in catalog: {self.catalog}\n"
                f"  • {', '.join(sorted(schemas))}\n\n"
                f"All data in these schemas will be permanently deleted.",
                title="CAUTION",
                style="warning"
            )
            
            if not Confirm.ask("\n[bold yellow]Proceed with layer reset?[/bold yellow]", default=False):
                self.logger.warning("\nReset cancelled by user.")
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
        
        self.logger.section("🗑️  TABLES-ONLY RESET")
        self.logger.info(f"Target schemas: {', '.join(sorted(schemas))}")
        self.logger.info("Action: Drop tables, keep schemas\n")
        
        if not self.dry_run:
            if not Confirm.ask("[bold cyan]Proceed with tables-only reset?[/bold cyan]", default=False):
                self.logger.warning("\nReset cancelled by user.")
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
        self.logger.section("RESET SUMMARY")
        
        # Build table data
        headers = ["Category", "Count"]
        rows = [
            ["Schemas Dropped", str(len(self.results["schemas_dropped"]))],
            ["Tables Dropped", str(len(self.results["tables_dropped"]))],
            ["Failed Operations", str(len(self.results["failed"]))]
        ]
        
        self.logger.table(headers, rows)
        
        if self.results["schemas_dropped"]:
            self.logger.info(f"\nDropped schemas: {', '.join(self.results['schemas_dropped'])}")
        
        if self.results["failed"]:
            self.logger.error("\nFailed operations:")
            for item, error in self.results["failed"]:
                self.logger.item_error(f"{item}: {error[:50]}")


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
    logger = DeploymentLogger()
    if success:
        logger.panel(
            "✅ Reset completed successfully\n\n"
            "Next steps:\n"
            "  • Run: python deployment/bootstrap.py (to recreate infrastructure)\n"
            "  • Run: python deployment/deploy_all.py (full redeployment)",
            title="SUCCESS",
            style="success"
        )
    else:
        logger.panel(
            "⚠️  Reset completed with errors\n\n"
            "Review the logs above for details.",
            title="WARNING",
            style="warning"
        )
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
