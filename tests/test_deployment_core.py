"""
Unit tests for deployment core modules.

Tests cover:
- DeploymentConfig loading, environment parsing, and path formatting
- DeploymentLogger console outputs and formatting
- DatabricksClientWrapper auto-selection and offline fallback handling
- SQLExecutor statement execution and error parsing
"""

import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from deployment.core.config import DeploymentConfig
from deployment.core.logger import DeploymentLogger
from deployment.core.databricks_client import DatabricksClientWrapper
from deployment.core.sql_executor import SQLExecutor


class TestDeploymentConfig:
    """Test DeploymentConfig functionality."""

    def test_default_config(self):
        """Test default values of DeploymentConfig."""
        config = DeploymentConfig(databricks_host="https://test.databricks.com")
        assert config.databricks_host == "https://test.databricks.com"
        assert config.catalog == "workspace"
        assert config.bronze_schema == "bronze"
        assert config.silver_schema == "silver"
        assert config.gold_schema == "gold"
        assert config.dry_run is False

    def test_get_full_path(self):
        """Test get_full_path helper method."""
        config = DeploymentConfig(
            databricks_host="https://test.databricks.com",
            workspace_root="/Users/test@example.com/LMIP"
        )
        path = config.get_full_path("notebooks/ingest")
        assert path == "/Users/test@example.com/LMIP/notebooks/ingest"

    def test_get_table_name(self):
        """Test get_table_name helper method."""
        config = DeploymentConfig(
            databricks_host="https://test.databricks.com",
            catalog="my_catalog"
        )
        table_name = config.get_table_name("gold", "dim_job")
        assert table_name == "my_catalog.gold.dim_job"

    def test_from_env(self, monkeypatch):
        """Test loading config from environment variables."""
        monkeypatch.setenv("DATABRICKS_HOST", "https://env.cloud.databricks.com")
        monkeypatch.setenv("CATALOG", "env_catalog")
        monkeypatch.setenv("DRY_RUN", "true")

        config = DeploymentConfig.from_env()
        assert config.databricks_host == "https://env.cloud.databricks.com"
        assert config.catalog == "env_catalog"
        assert config.dry_run is True


class TestDeploymentLogger:
    """Test DeploymentLogger methods."""

    def test_logger_initialization(self):
        """Test logger init with verbose modes."""
        logger = DeploymentLogger(verbose=True)
        assert logger.verbose is True

    def test_logger_methods_no_raise(self):
        """Verify logging calls execute without exceptions."""
        logger = DeploymentLogger(verbose=True)
        logger.banner("TEST BANNER")
        logger.section("Test Section")
        logger.info("Test Info")
        logger.success("Test Success")
        logger.warning("Test Warning")
        logger.error("Test Error")
        logger.debug("Test Debug")
        logger.dry_run("Test Dry Run")
        logger.item_success("item1", "ok")
        logger.item_error("item2", "fail")
        logger.item_warning("item3", "warn")
        logger.item_skip("item4", "skip")
        logger.summary("Summary", {"Created": 1, "Failed": 0})


class TestDatabricksClientWrapper:
    """Test DatabricksClientWrapper."""

    def test_client_wrapper_offline_fallback(self):
        """Verify client wrapper handles missing credentials without crashing."""
        with patch.dict(os.environ, {"DATABRICKS_HOST": "", "DATABRICKS_TOKEN": ""}, clear=True):
            wrapper = DatabricksClientWrapper()
            assert wrapper.client is None
            assert wrapper.warehouse_id == "dry-run-warehouse-id"

    def test_client_wrapper_warehouse_id_override(self):
        """Verify explicit warehouse ID is preserved."""
        wrapper = DatabricksClientWrapper(warehouse_id="custom-wh-123")
        assert wrapper.warehouse_id == "custom-wh-123"


class TestSQLExecutor:
    """Test SQLExecutor."""

    def test_sql_executor_init(self):
        """Test SQLExecutor initialization."""
        mock_client = MagicMock()
        executor = SQLExecutor(client=mock_client, warehouse_id="wh-1", catalog="test_cat")
        assert executor.warehouse_id == "wh-1"
        assert executor.catalog == "test_cat"

    def test_config_methods(self):
        """Test DeploymentConfig helper methods and validation."""
        import dataclasses
        config = DeploymentConfig(
            databricks_host="https://test.databricks.com",
            databricks_token="test_token"
        )
        assert config.get_schema_name("bronze") == "workspace.bronze"
        assert dataclasses.asdict(config)["databricks_host"] == "https://test.databricks.com"
        
        # Test validation
        errors = config.validate()
        assert len(errors) == 0
        assert config.validate() is True

        invalid_config = DeploymentConfig(databricks_host="")
        invalid_errors = invalid_config.validate()
        assert len(invalid_errors) > 0
        assert invalid_config.validate() is False


class TestDeploymentLoggerExpanded:
    """Expanded tests for DeploymentLogger methods."""

    def test_logger_tables_and_panels(self):
        """Test rich panels and stats formatting in logger."""
        logger = DeploymentLogger(verbose=True)
        logger.panel("Panel Message", title="Panel Title")
        logger.summary("Execution Summary", {"Passed": 10, "Failed": 0})


class TestDatabricksClientWrapperExpanded:
    """Expanded tests for DatabricksClientWrapper."""

    def test_wrapper_schema_and_catalog_checks(self):
        """Test schema_exists, create_schema, and get_job_id methods."""
        wrapper = DatabricksClientWrapper()
        wrapper.client = MagicMock()

        # Mock schema_exists
        wrapper.client.schemas.get.return_value = MagicMock()
        assert wrapper.schema_exists("cat", "sch") is True

        # Mock schema_exists exception
        wrapper.client.schemas.get.side_effect = Exception("Not found")
        assert wrapper.schema_exists("cat", "sch") is False

        # Mock get_job_id
        mock_job = MagicMock()
        mock_job.job_id = 456
        mock_job.settings.name = "my_job"
        wrapper.client.jobs.list.return_value = [mock_job]
        assert wrapper.get_job_id("my_job") == "456"
        assert wrapper.get_job_id("non_existent") is None


class TestSQLExecutorExpanded:
    """Expanded tests for SQLExecutor methods."""

    def test_sql_executor_file_and_ddl(self, tmp_path):
        """Test execute_ddl and create_schema."""
        mock_client = MagicMock()
        from databricks.sdk.service.sql import StatementState

        mock_statement = MagicMock()
        mock_statement.statement_id = "stmt-1"
        mock_statement.status.state = StatementState.SUCCEEDED
        mock_statement.result = {}

        mock_client.statement_execution.execute_statement.return_value = mock_statement
        mock_client.statement_execution.get_statement.return_value = mock_statement

        executor = SQLExecutor(client=mock_client, warehouse_id="wh-1", catalog="test_cat")

        # Test create_schema
        schema_res = executor.create_schema("bronze", comment="Bronze schema")
        assert schema_res["success"] is True

        # Test execute_ddl with temp file
        sql_file = tmp_path / "test.sql"
        sql_file.write_text("CREATE TABLE ${catalog}.test.tbl (id INT);")
        file_res = executor.execute_ddl(sql_file)
        assert file_res["success"] is True

    def test_sql_executor_failed_statement(self):
        """Test SQLExecutor handling of statement failures."""
        mock_client = MagicMock()
        from databricks.sdk.service.sql import StatementState

        mock_statement = MagicMock()
        mock_statement.statement_id = "stmt-fail"
        mock_statement.status.state = StatementState.FAILED
        mock_statement.status.error.message = "Table not found"

        mock_client.statement_execution.execute_statement.return_value = mock_statement
        mock_client.statement_execution.get_statement.return_value = mock_statement

        executor = SQLExecutor(client=mock_client, warehouse_id="wh-1", catalog="test_cat")
        res = executor.execute("SELECT * FROM invalid_table")
        assert res["success"] is False
        assert "Table not found" in res["error"]

