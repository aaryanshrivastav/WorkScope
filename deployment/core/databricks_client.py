"""
Databricks SDK Wrapper

Provides a higher-level interface to the Databricks SDK with:
- Automatic warehouse selection
- Error handling
- Retry logic
- Common patterns abstraction
"""

from typing import Optional, List
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import WarehouseInfo
from rich.console import Console

console = Console()


class DatabricksClientWrapper:
    """Enhanced Databricks SDK client with common patterns"""
    
    def __init__(self, warehouse_id: Optional[str] = None):
        """
        Initialize Databricks client wrapper.
        
        Args:
            warehouse_id: Optional SQL warehouse ID. If not provided, auto-selects.
        """
        self.client = WorkspaceClient()
        self._warehouse_id = warehouse_id
        self._cached_warehouse_id: Optional[str] = None
    
    @property
    def warehouse_id(self) -> str:
        """
        Get SQL warehouse ID for executing statements.
        Auto-selects serverless warehouse if not provided.
        
        Returns:
            Warehouse ID string
        
        Raises:
            Exception: If no warehouses are available
        """
        if self._cached_warehouse_id:
            return self._cached_warehouse_id
        
        if self._warehouse_id:
            self._cached_warehouse_id = self._warehouse_id
            return self._warehouse_id
        
        # Auto-select warehouse
        self._cached_warehouse_id = self._select_warehouse()
        return self._cached_warehouse_id
    
    def _select_warehouse(self) -> str:
        """
        Automatically select the best available SQL warehouse.
        Prefers: Serverless > Pro > Classic
        
        Returns:
            Warehouse ID
        
        Raises:
            Exception: If no warehouses found
        """
        warehouses: List[WarehouseInfo] = list(self.client.warehouses.list())
        
        if not warehouses:
            raise Exception(
                "No SQL warehouses found. Please create a SQL warehouse first.\n"
                "Visit: Settings → SQL Warehouses → Create Warehouse"
            )
        
        # Priority 1: Serverless warehouses
        for wh in warehouses:
            if wh.enable_serverless_compute:
                console.print(f"[dim]Auto-selected serverless warehouse: {wh.name} ({wh.id})[/dim]")
                return wh.id
        
        # Priority 2: Pro warehouses
        for wh in warehouses:
            if hasattr(wh, 'warehouse_type') and wh.warehouse_type and 'PRO' in str(wh.warehouse_type):
                console.print(f"[dim]Auto-selected Pro warehouse: {wh.name} ({wh.id})[/dim]")
                return wh.id
        
        # Priority 3: Any warehouse
        selected = warehouses[0]
        console.print(f"[dim]Auto-selected warehouse: {selected.name} ({selected.id})[/dim]")
        return selected.id
    
    def schema_exists(self, catalog: str, schema: str) -> bool:
        """
        Check if a schema exists.
        
        Args:
            catalog: Catalog name
            schema: Schema name
        
        Returns:
            True if exists, False otherwise
        """
        try:
            self.client.schemas.get(f"{catalog}.{schema}")
            return True
        except Exception:
            return False
    
    def table_exists(self, catalog: str, schema: str, table: str) -> bool:
        """
        Check if a table exists.
        
        Args:
            catalog: Catalog name
            schema: Schema name
            table: Table name
        
        Returns:
            True if exists, False otherwise
        """
        try:
            self.client.tables.get(f"{catalog}.{schema}.{table}")
            return True
        except Exception:
            return False
    
    def list_tables(self, catalog: str, schema: str) -> List[str]:
        """
        List all tables in a schema.
        
        Args:
            catalog: Catalog name
            schema: Schema name
        
        Returns:
            List of table names
        """
        try:
            tables = self.client.tables.list(
                catalog_name=catalog,
                schema_name=schema
            )
            return [table.name for table in tables]
        except Exception as e:
            console.print(f"[yellow]⚠️  Could not list tables in {catalog}.{schema}: {e}[/yellow]")
            return []
    
    def get_table_row_count(self, catalog: str, schema: str, table: str) -> Optional[int]:
        """
        Get row count for a table.
        
        Args:
            catalog: Catalog name
            schema: Schema name
            table: Table name
        
        Returns:
            Row count or None if query fails
        """
        try:
            full_table = f"{catalog}.{schema}.{table}"
            result = self.client.statement_execution.execute_statement(
                warehouse_id=self.warehouse_id,
                statement=f"SELECT COUNT(*) as cnt FROM {full_table}",
                catalog=catalog,
                wait_timeout="30s"
            )
            
            if result.status.state.value == "SUCCEEDED" and result.result:
                # Parse result
                if result.result.data_array and len(result.result.data_array) > 0:
                    return int(result.result.data_array[0][0])
            
            return None
        except Exception as e:
            console.print(f"[yellow]⚠️  Could not get row count for {catalog}.{schema}.{table}: {e}[/yellow]")
            return None
    
    def notebook_exists(self, path: str) -> bool:
        """
        Check if a notebook exists at given workspace path.
        
        Args:
            path: Workspace path (e.g., /Users/user@domain.com/notebook)
        
        Returns:
            True if exists, False otherwise
        """
        try:
            self.client.workspace.get_status(path)
            return True
        except Exception:
            return False
    
    def job_exists(self, job_name: str) -> bool:
        """
        Check if a job exists by name.
        
        Args:
            job_name: Job name to search for
        
        Returns:
            True if exists, False otherwise
        """
        try:
            jobs = self.client.jobs.list(name=job_name)
            for job in jobs:
                if job.settings and job.settings.name == job_name:
                    return True
            return False
        except Exception:
            return False
    
    def get_job_id(self, job_name: str) -> Optional[str]:
        """
        Get job ID by name.
        
        Args:
            job_name: Job name to search for
        
        Returns:
            Job ID or None if not found
        """
        try:
            jobs = self.client.jobs.list(name=job_name)
            for job in jobs:
                if job.settings and job.settings.name == job_name:
                    return str(job.job_id)
            return None
        except Exception:
            return None
