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
from dotenv import load_dotenv
import os
import time

console = Console()
load_dotenv()

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
        timeout: str = "0s",
        catalog: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a SQL statement.
        
        Args:
            sql: SQL statement to execute
            timeout: Wait timeout (default: 0s)
            catalog: Optional catalog override
        
        Returns:
            Dict with 'success' (bool), 'state' (str), 'error' (Optional[str]), 'result' (Any)
        """
        result = self.client.statement_execution.execute_statement(
            warehouse_id=self.warehouse_id,
            statement=sql,
            catalog=catalog or self.catalog,
            wait_timeout=timeout
        )

        statement_id = result.statement_id

        while True:

            state = result.status.state
            print(f"DEBUG STATE: {state}")

            if state == StatementState.SUCCEEDED:
                return {
                    "success": True,
                    "state": "SUCCEEDED",
                    "error": None,
                    "result": result.result
                }

            if state in (
                StatementState.FAILED,
                StatementState.CANCELED,
                StatementState.CLOSED
            ):
                error_msg = (
                    result.status.error.message
                    if result.status.error
                    else str(state)
                )

                return {
                    "success": False,
                    "state": state.value,
                    "error": error_msg,
                    "result": None
                }

            # PENDING or RUNNING
            time.sleep(2)

            result = self.client.statement_execution.get_statement(
                statement_id
            )
    
    def execute_ddl(self, ddl_file: Path, timeout: str = "0s") -> Dict[str, Any]:
        """
        Execute a DDL file.
        
        Args:
            ddl_file: Path to DDL SQL file
            timeout: Wait timeout (default: 0s for DDL)
        
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
        return self.execute(sql, timeout="0s")
    
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
        return self.execute(sql, timeout="0s")
    
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
        return self.execute(sql, timeout="0s")
    
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
        result = self.execute(f"SELECT COUNT(*) as cnt FROM {full_table}", timeout="0s")
        
        if result["success"] and result["result"] and result["result"].data_array:
            try:
                return int(result["result"].data_array[0][0])
            except (IndexError, ValueError, TypeError):
                return None
        
        return None
    
    def execute_insert(
        self,
        target_table: str,
        source_data: List[Dict[str, Any]],
        timeout: str = "0s"
    ):
        if not source_data:
            return {
                "success": False,
                "state": "EMPTY_DATA",
                "error": "No data provided",
                "result": None
            }

        columns = list(source_data[0].keys())

        values = []

        for row in source_data:
            row_values = []

            for col in columns:
                value = row.get(col)

                if value is None:
                    row_values.append("NULL")
                else:
                    escaped = str(value).replace("'", "''")
                    row_values.append(f"'{escaped}'")

            values.append(f"({', '.join(row_values)})")

        sql = f"""
        INSERT INTO {target_table}
        ({', '.join(columns)})
        VALUES
        {', '.join(values)}
        """

        return self.execute(sql, timeout=timeout)