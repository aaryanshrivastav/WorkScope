"""
SQL Execution Utilities

Helper class for executing SQL statements via Databricks SDK with:
- Error handling
- Result parsing
- DDL execution patterns
- Idempotent operations
"""

from typing import Optional, Dict, Any, List
from pathlib import Path
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
from rich.console import Console

console = Console()


class SQLExecutor:
    """Helper for executing SQL statements via Databricks SDK"""
    
    def __init__(self, client: WorkspaceClient, warehouse_id: str, catalog: str):
        """
        Initialize SQL executor.
        
        Args:
            client: Databricks WorkspaceClient instance
            warehouse_id: SQL warehouse ID to use
            catalog: Default catalog name
        """
        self.client = client
        self.warehouse_id = warehouse_id
        self.catalog = catalog
    
    def execute(
        self, 
        sql: str, 
        timeout: str = "60s",
        catalog: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a SQL statement.
        
        Args:
            sql: SQL statement to execute
            timeout: Wait timeout (default: 60s)
            catalog: Optional catalog override
        
        Returns:
            Dict with 'success' (bool), 'state' (str), 'error' (Optional[str]), 'result' (Any)
        """
        try:
            result = self.client.statement_execution.execute_statement(
                warehouse_id=self.warehouse_id,
                statement=sql,
                catalog=catalog or self.catalog,
                wait_timeout=timeout
            )
            
            if result.status.state.value == "SUCCEEDED":
                return {
                    "success": True,
                    "state": "SUCCEEDED",
                    "error": None,
                    "result": result.result
                }
            else:
                error_msg = result.status.error.message if result.status.error else str(result.status.state)
                return {
                    "success": False,
                    "state": result.status.state.value,
                    "error": error_msg,
                    "result": None
                }
                
        except Exception as e:
            return {
                "success": False,
                "state": "ERROR",
                "error": str(e),
                "result": None
            }
    
    def execute_ddl(self, ddl_file: Path, timeout: str = "120s") -> Dict[str, Any]:
        """
        Execute a DDL file.
        
        Args:
            ddl_file: Path to DDL SQL file
            timeout: Wait timeout (default: 120s for DDL)
        
        Returns:
            Dict with execution result
        """
        if not ddl_file.exists():
            return {
                "success": False,
                "state": "FILE_NOT_FOUND",
                "error": f"DDL file not found: {ddl_file}",
                "result": None
            }
        
        try:
            with open(ddl_file, 'r') as f:
                sql = f.read()
            
            return self.execute(sql, timeout=timeout)
            
        except Exception as e:
            return {
                "success": False,
                "state": "READ_ERROR",
                "error": f"Failed to read DDL file: {e}",
                "result": None
            }
    
    def create_schema(
        self, 
        schema: str, 
        comment: Optional[str] = None,
        if_not_exists: bool = True
    ) -> Dict[str, Any]:
        """
        Create a Unity Catalog schema.
        
        Args:
            schema: Schema name
            comment: Optional schema comment
            if_not_exists: Use IF NOT EXISTS clause (idempotent)
        
        Returns:
            Dict with execution result
        """
        if_clause = "IF NOT EXISTS" if if_not_exists else ""
        comment_clause = f"COMMENT '{comment}'" if comment else ""
        
        sql = f"CREATE SCHEMA {if_clause} {self.catalog}.{schema} {comment_clause}"
        return self.execute(sql, timeout="30s")
    
    def drop_schema(
        self, 
        schema: str, 
        cascade: bool = True,
        if_exists: bool = True
    ) -> Dict[str, Any]:
        """
        Drop a Unity Catalog schema.
        
        Args:
            schema: Schema name
            cascade: Drop with CASCADE (drop all tables)
            if_exists: Use IF EXISTS clause
        
        Returns:
            Dict with execution result
        """
        if_clause = "IF EXISTS" if if_exists else ""
        cascade_clause = "CASCADE" if cascade else "RESTRICT"
        
        sql = f"DROP SCHEMA {if_clause} {self.catalog}.{schema} {cascade_clause}"
        return self.execute(sql, timeout="60s")
    
    def drop_table(
        self, 
        schema: str, 
        table: str,
        if_exists: bool = True
    ) -> Dict[str, Any]:
        """
        Drop a table.
        
        Args:
            schema: Schema name
            table: Table name
            if_exists: Use IF EXISTS clause
        
        Returns:
            Dict with execution result
        """
        if_clause = "IF EXISTS" if if_exists else ""
        full_table = f"{self.catalog}.{schema}.{table}"
        
        sql = f"DROP TABLE {if_clause} {full_table}"
        return self.execute(sql, timeout="30s")
    
    def get_row_count(self, schema: str, table: str) -> Optional[int]:
        """
        Get row count for a table.
        
        Args:
            schema: Schema name
            table: Table name
        
        Returns:
            Row count or None if query fails
        """
        full_table = f"{self.catalog}.{schema}.{table}"
        result = self.execute(f"SELECT COUNT(*) as cnt FROM {full_table}", timeout="30s")
        
        if result["success"] and result["result"] and result["result"].data_array:
            try:
                return int(result["result"].data_array[0][0])
            except (IndexError, ValueError, TypeError):
                return None
        
        return None
    
    def execute_merge(
        self,
        target_table: str,
        source_data: List[Dict[str, Any]],
        merge_key: str,
        timeout: str = "60s"
    ) -> Dict[str, Any]:
        """
        Execute a MERGE statement (idempotent upsert).
        
        Args:
            target_table: Full table name (catalog.schema.table)
            source_data: List of dicts representing rows
            merge_key: Column name to use for matching (e.g., 'id')
            timeout: Wait timeout
        
        Returns:
            Dict with execution result
        """
        if not source_data:
            return {
                "success": False,
                "state": "EMPTY_DATA",
                "error": "No data provided for merge",
                "result": None
            }
        
        # Build VALUES clause
        columns = list(source_data[0].keys())
        values_list = []
        
        for row in source_data:
            values = []
            for col in columns:
                value = row.get(col)
                if value is None:
                    values.append("NULL")
                else:
                    # Escape quotes
                    escaped = str(value).replace("'", "''")
                    values.append(f"'{escaped}'")
            values_list.append(f"({', '.join(values)})")
        
        values_str = ',\n  '.join(values_list)
        
        # Build MERGE statement
        merge_sql = f"""
MERGE INTO {target_table} AS target
USING (
  SELECT * FROM VALUES
    {values_str}
) AS source({', '.join(columns)})
ON target.{merge_key} = source.{merge_key}
WHEN MATCHED THEN
  UPDATE SET *
WHEN NOT MATCHED THEN
  INSERT *
"""
        
        return self.execute(merge_sql, timeout=timeout)
