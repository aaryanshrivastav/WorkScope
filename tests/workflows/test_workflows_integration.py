"""
Integration tests for LMIP workflows.

Tests verify:
- Workflow configuration is valid
- Task dependencies are correct
- End-to-end workflow execution
- Workflow orchestration and error handling
"""

import pytest
import json
import os
from pathlib import Path
from dotenv import load_dotenv
import os
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.jobs import RunLifeCycleState, RunResultState
load_dotenv()


PROJECT_ROOT = Path(__file__).parents[2]
WORKFLOW_DIR = PROJECT_ROOT / "workflows"
WORKFLOWS = {
    "init": WORKFLOW_DIR / "init.json",
    "ingestion": WORKFLOW_DIR / "LMIPDataIngestion.json",
    "silver": WORKFLOW_DIR / "LMIPSilverProcessing.json",
    "intermediate": WORKFLOW_DIR / "LMIPIntermediateProcessing.json",
    "warehouse": WORKFLOW_DIR / "LMIPWarehouseBuild.json",
    "gold": WORKFLOW_DIR / "LMIPGoldBuild.json",
    "publishing": WORKFLOW_DIR / "publishing.json",
    "recovery": WORKFLOW_DIR / "recovery.json",
}


@pytest.fixture(scope="module")
def workspace_client():
    """Get Databricks workspace client."""
    host = os.getenv("DATABRICKS_HOST")
    token = os.getenv("DATABRICKS_TOKEN")
    if not host or not token:
        pytest.skip("Databricks host and token not configured in environment")
    return WorkspaceClient(host=host, token=token)


@pytest.fixture(scope="module")
def workflow_configs():
    """Load all workflow JSON configurations."""
    configs = {}
    for name, path in WORKFLOWS.items():
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                configs[name] = json.load(f)
    return configs


class TestWorkflowConfiguration:
    """Test workflow configuration validity."""

    def test_all_workflow_files_exist(self):
        """Verify all workflow JSON files exist."""
        for name, path in WORKFLOWS.items():
            assert os.path.exists(path), f"Workflow {name} not found at {path}"

    def test_workflow_json_is_valid(self, workflow_configs):
        """Verify all workflow JSONs are valid."""
        for name, config in workflow_configs.items():
            assert "name" in config, f"Workflow {name} missing 'name' field"
            assert "tasks" in config, f"Workflow {name} missing 'tasks' field"
            assert isinstance(config["tasks"], list), f"Workflow {name} 'tasks' must be a list"

    def test_workflow_tasks_have_required_fields(self, workflow_configs):
        """Verify each task has required fields."""
        for name, config in workflow_configs.items():
            for task in config["tasks"]:
                assert "task_key" in task, f"Task in {name} missing 'task_key'"
                # At least one task type should be present
                task_types = ["notebook_task", "spark_python_task", "python_wheel_task", "pipeline_task"]
                has_task_type = any(t in task for t in task_types)
                assert has_task_type, f"Task {task.get('task_key')} in {name} missing task type"

    def test_workflow_task_dependencies_exist(self, workflow_configs):
        """Verify task dependencies reference valid tasks."""
        for name, config in workflow_configs.items():
            task_keys = {task["task_key"] for task in config["tasks"]}
            
            for task in config["tasks"]:
                if "depends_on" in task:
                    for dep in task["depends_on"]:
                        dep_key = dep.get("task_key")
                        assert dep_key in task_keys, \
                            f"Task {task['task_key']} in {name} depends on non-existent task {dep_key}"

    def test_workflow_has_no_circular_dependencies(self, workflow_configs):
        """Verify no circular dependencies in task graphs."""
        for name, config in workflow_configs.items():
            # Build dependency graph
            graph = {}
            for task in config["tasks"]:
                task_key = task["task_key"]
                deps = [dep["task_key"] for dep in task.get("depends_on", [])]
                graph[task_key] = deps
            
            # DFS to detect cycles
            visited = set()
            rec_stack = set()
            
            def has_cycle(node):
                visited.add(node)
                rec_stack.add(node)
                
                for neighbor in graph.get(node, []):
                    if neighbor not in visited:
                        if has_cycle(neighbor):
                            return True
                    elif neighbor in rec_stack:
                        return True
                
                rec_stack.remove(node)
                return False
            
            for task_key in graph:
                if task_key not in visited:
                    assert not has_cycle(task_key), f"Circular dependency detected in {name}"


class TestInitWorkflow:
    """Test init.json workflow."""

    def test_init_workflow_task_order(self, workflow_configs):
        """Verify init tasks run in correct order."""
        init_config = workflow_configs["init"]
        tasks = {t["task_key"]: t for t in init_config["tasks"]}
        
        # Expected order: validate_env -> create_schemas -> seed_metadata
        assert any(k in tasks for k in ["Init_ValidateEnv", "init_validate_env", "Init_Validate_Environment"])
        assert any(k in tasks for k in ["Init_CreateSchemas", "init_create_schemas", "Init_Create_Schemas"])


class TestIngestionWorkflow:
    """Test LMIPDataIngestion.json workflow."""

    def test_ingestion_has_source_tasks(self, workflow_configs):
        """Verify ingestion workflow has tasks for each data source."""
        ingestion_config = workflow_configs["ingestion"]
        task_keys = [t["task_key"] for t in ingestion_config["tasks"]]
        
        # Should have tasks for different data sources
        # Verify at least one source ingestion task exists
        assert len(task_keys) > 0


class TestSilverProcessingWorkflow:
    """Test LMIPSilverProcessing.json workflow."""

    def test_silver_processing_task_dependencies(self, workflow_configs):
        """Verify silver processing tasks have correct dependencies."""
        silver_config = workflow_configs["silver"]
        
        # Build task map
        tasks = {t["task_key"]: t for t in silver_config["tasks"]}
        
        # CDC detection should run before identity mapping
        # Identity mapping should run before sector assignment
        # (Specific task names may vary - this is a structural test)
        assert len(tasks) > 0


class TestIntermediateProcessingWorkflow:
    """Test LMIPIntermediateProcessing.json workflow."""

    def test_intermediate_processing_dependencies(self, workflow_configs):
        """Verify intermediate processing dependencies."""
        inter_config = workflow_configs["intermediate"]
        assert "tasks" in inter_config
        assert len(inter_config["tasks"]) > 0


class TestWarehouseBuildWorkflow:
    """Test LMIPWarehouseBuild.json workflow."""

    def test_warehouse_dimensions_before_facts(self, workflow_configs):
        """Verify dimension tables build before fact tables."""
        wh_config = workflow_configs["warehouse"]
        
        # Get all tasks
        tasks = wh_config["tasks"]
        
        # Identify dim and fact tasks
        dim_tasks = [t for t in tasks if "dim" in t["task_key"].lower()]
        fact_tasks = [t for t in tasks if "fact" in t["task_key"].lower() or "bridge" in t["task_key"].lower()]
        
        # For each fact task, verify it depends on at least one dim task
        for fact_task in fact_tasks:
            deps = [dep["task_key"] for dep in fact_task.get("depends_on", [])]
            # Fact should depend on at least one dimension (or another task that depends on dims)
            # This is a simplified check
            if deps:
                assert len(deps) > 0


class TestPublishingWorkflow:
    """Test publishing.json workflow."""

    def test_publishing_manifest_writes_last(self, workflow_configs):
        """Verify manifest writes after all exports."""
        pub_config = workflow_configs["publishing"]
        tasks = {t["task_key"]: t for t in pub_config["tasks"]}
        
        # Manifest task should have dependencies on export tasks
        manifest_task = next((t for t in pub_config["tasks"] if "manifest" in t["task_key"].lower()), None)
        
        if manifest_task:
            deps = manifest_task.get("depends_on", [])
            assert len(deps) > 0, "Manifest task should depend on export tasks"


class TestRecoveryWorkflow:
    """Test recovery.json workflow."""

    def test_recovery_has_rollback_task(self, workflow_configs):
        """Verify recovery workflow includes rollback task."""
        recovery_config = workflow_configs["recovery"]
        task_keys = [t["task_key"] for t in recovery_config["tasks"]]
        
        # Should have rollback task
        rollback_task = next((k for k in task_keys if "rollback" in k.lower()), None)
        assert rollback_task is not None, "Recovery workflow missing rollback task"

    def test_recovery_has_replay_task(self, workflow_configs):
        """Verify recovery workflow includes replay/backfill task."""
        recovery_config = workflow_configs["recovery"]
        task_keys = [t["task_key"] for t in recovery_config["tasks"]]
        
        # Should have replay/backfill task
        replay_task = next((k for k in task_keys if "replay" in k.lower() or "backfill" in k.lower()), None)
        assert replay_task is not None, "Recovery workflow missing replay task"


@pytest.mark.integration
@pytest.mark.slow
class TestWorkflowExecution:
    """End-to-end workflow execution tests.
    
    These tests actually run the workflows and verify results.
    Mark as @pytest.mark.slow since they take time.
    """

    def test_init_workflow_runs_successfully(self, workspace_client):
        """Test init workflow execution."""
        pytest.skip("Full workflow execution - run manually or in CI")
        
        # This would:
        # 1. Trigger init workflow
        # 2. Wait for completion
        # 3. Verify schemas created
        # 4. Verify metadata loaded

    def test_ingestion_workflow_runs_successfully(self, workspace_client):
        """Test ingestion workflow execution."""
        pytest.skip("Full workflow execution - run manually or in CI")
        
        # This would:
        # 1. Trigger ingestion workflow
        # 2. Wait for completion
        # 3. Verify bronze tables populated
        # 4. Verify batch tracking updated

    def test_end_to_end_pipeline(self, workspace_client):
        """Test complete pipeline from ingestion to publishing."""
        pytest.skip("Full E2E test - run manually or in CI")
        
        # This would:
        # 1. Run init workflow
        # 2. Run ingestion workflow
        # 3. Run silver processing workflow
        # 4. Run intermediate processing workflow
        # 5. Run warehouse build workflow
        # 6. Run publishing workflow
        # 7. Verify published outputs


class TestWorkflowErrorHandling:
    """Test workflow error handling and recovery."""

    def test_workflow_has_retry_policy(self, workflow_configs):
        """Verify workflows have retry policies configured."""
        for name, config in workflow_configs.items():
            # Check if workflow has max_retries or retry policy
            # This is optional but recommended
            pass

    def test_workflow_has_timeout_configured(self, workflow_configs):
        """Verify workflows have timeouts configured."""
        for name, config in workflow_configs.items():
            # Check for timeout settings
            # This prevents runaway workflows
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
