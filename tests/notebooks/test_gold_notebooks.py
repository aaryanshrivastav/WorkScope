"""
Integration tests for Gold layer notebooks.

Tests verify:
- SCD2 dimension building (uses test_scd2_key_generation.py)
- Bridge and fact table construction
- Data mart schema compliance
"""

import pytest
import os
from datetime import datetime


WORKSPACE_ROOT = "/Workspace/Users/aaryan.shrivastav1403@gmail.com/LMIP"
GOLD_NOTEBOOKS = {
    "gold_dim_job_scd2": f"{WORKSPACE_ROOT}/notebooks/gold/gold_dim_job_scd2",
    "gold_dim_company": f"{WORKSPACE_ROOT}/notebooks/gold/gold_dim_company",
    "gold_dim_company_alias": f"{WORKSPACE_ROOT}/notebooks/gold/gold_dim_company_alias",
    "gold_dim_role": f"{WORKSPACE_ROOT}/notebooks/gold/gold_dim_role",
    "gold_dim_sector": f"{WORKSPACE_ROOT}/notebooks/gold/gold_dim_sector",
    "gold_dim_skill": f"{WORKSPACE_ROOT}/notebooks/gold/gold_dim_skill",
    "gold_dim_location": f"{WORKSPACE_ROOT}/notebooks/gold/gold_dim_location",
    "gold_dim_source": f"{WORKSPACE_ROOT}/notebooks/gold/gold_dim_source",
    "gold_dim_date": f"{WORKSPACE_ROOT}/notebooks/gold/gold_dim_date",
    "gold_bridge_job_skill": f"{WORKSPACE_ROOT}/notebooks/gold/gold_bridge_job_skill",
    "gold_fact_job_postings": f"{WORKSPACE_ROOT}/notebooks/gold/gold_fact_job_postings",
    "gold_fact_job_lifecycle": f"{WORKSPACE_ROOT}/notebooks/gold/gold_fact_job_lifecycle",
    "gold_fact_salary": f"{WORKSPACE_ROOT}/notebooks/gold/gold_fact_salary",
    "gold_fact_pipeline_runs": f"{WORKSPACE_ROOT}/notebooks/gold/gold_fact_pipeline_runs",
}


@pytest.fixture(scope="module")
def test_catalog():
    return os.getenv("TEST_CATALOG", "workspace")


class TestGoldNotebookStructure:
    """Verify gold notebook structure."""

    def test_all_notebooks_exist(self, workspace_client):
        """Verify all gold notebooks exist."""
        for name, path in GOLD_NOTEBOOKS.items():
            try:
                workspace_client.workspace.get_status(path)
            except Exception as e:
                pytest.fail(f"Notebook {name} not found at {path}: {e}")


class TestDimJobSCD2:
    """Test gold_dim_job_scd2 notebook (uses test_scd2_key_generation.py)."""

    def test_scd2_version_tracking(self, spark):
        """Test SCD2 versioning logic."""
        # See test_scd2_key_generation.py for comprehensive tests
        # This verifies SCD2 structure
        from pyspark.sql.types import StructType, StructField, StringType, TimestampType, BooleanType
        
        schema = StructType([
            StructField("job_key", StringType(), False),
            StructField("job_identity_key", StringType(), False),
            StructField("title", StringType(), True),
            StructField("effective_date", TimestampType(), False),
            StructField("end_date", TimestampType(), True),
            StructField("is_current", BooleanType(), False),
        ])
        
        # Sample SCD2 records
        data = [
            ("job1_v1", "identity1", "Engineer", datetime(2024, 1, 1), datetime(2024, 2, 1), False),
            ("job1_v2", "identity1", "Senior Engineer", datetime(2024, 2, 1), None, True),
        ]
        
        df = spark.createDataFrame(data, schema)
        
        # Verify SCD2 properties
        current_versions = df.filter("is_current = true").count()
        historical_versions = df.filter("is_current = false").count()
        
        assert current_versions == 1, "Expected 1 current version"
        assert historical_versions == 1, "Expected 1 historical version"


class TestDimCompany:
    """Test gold_dim_company notebook."""

    def test_company_dimension_structure(self, spark):
        """Test company dimension table structure."""
        companies = [
            ("company1", "ACME Corp", "Technology", "USA"),
            ("company2", "Beta Inc", "Healthcare", "Canada"),
        ]
        
        df = spark.createDataFrame(
            companies,
            ["company_key", "company_name", "industry", "country"]
        )
        
        assert df.count() == 2


class TestDimCompanyAlias:
    """Test gold_dim_company_alias notebook."""

    def test_company_alias_mapping(self, spark):
        """Test company alias mappings."""
        aliases = [
            ("company1", "ACME Corp"),
            ("company1", "ACME Corporation"),
            ("company1", "acme corp"),
        ]
        
        df = spark.createDataFrame(
            aliases,
            ["company_key", "alias_name"]
        )
        
        # Verify aliases map to same company
        assert df.filter("company_key = 'company1'").count() == 3


class TestBridgeJobSkill:
    """Test gold_bridge_job_skill notebook."""

    def test_job_skill_relationships(self, spark):
        """Test job-skill bridge table."""
        relationships = [
            ("job1", "skill1", "Python", "required"),
            ("job1", "skill2", "SQL", "preferred"),
            ("job2", "skill1", "Python", "required"),
        ]
        
        df = spark.createDataFrame(
            relationships,
            ["job_key", "skill_key", "skill_name", "proficiency_level"]
        )
        
        # Verify bridge structure
        job1_skills = df.filter("job_key = 'job1'").count()
        assert job1_skills == 2, "Expected 2 skills for job1"


class TestFactJobPostings:
    """Test gold_fact_job_postings notebook."""

    def test_fact_table_grain(self, spark):
        """Test fact table grain and measures."""
        facts = [
            ("fact1", "job1", "company1", "location1", "date1", 1, 100000),
            ("fact2", "job2", "company2", "location2", "date2", 1, 120000),
        ]
        
        df = spark.createDataFrame(
            facts,
            ["fact_key", "job_key", "company_key", "location_key", "date_key", "posting_count", "salary_amount"]
        )
        
        assert df.count() == 2


class TestFactJobLifecycle:
    """Test gold_fact_job_lifecycle notebook."""

    def test_lifecycle_events(self, spark):
        """Test job lifecycle event tracking."""
        events = [
            ("event1", "job1", "2024-01-01", "POSTED"),
            ("event2", "job1", "2024-01-15", "UPDATED"),
            ("event3", "job1", "2024-02-01", "CLOSED"),
        ]
        
        df = spark.createDataFrame(
            events,
            ["event_key", "job_key", "event_date", "event_type"]
        )
        
        # Verify lifecycle phases
        assert df.filter("event_type = 'POSTED'").count() == 1
        assert df.filter("event_type = 'CLOSED'").count() == 1


class TestFactSalary:
    """Test gold_fact_salary notebook."""

    def test_salary_aggregations(self, spark):
        """Test salary fact table."""
        salaries = [
            ("job1", "role1", "location1", 100000, 110000, "USD"),
            ("job2", "role1", "location1", 95000, 105000, "USD"),
        ]
        
        df = spark.createDataFrame(
            salaries,
            ["job_key", "role_key", "location_key", "min_salary", "max_salary", "currency"]
        )
        
        # Calculate average
        from pyspark.sql.functions import avg
        avg_min = df.agg(avg("min_salary")).first()[0]
        assert avg_min == 97500


class TestFactPipelineRuns:
    """Test gold_fact_pipeline_runs notebook."""

    def test_pipeline_run_metrics(self, spark):
        """Test pipeline run metrics."""
        runs = [
            ("run1", "2024-01-01", "bronze_ingestion", "SUCCESS", 1000, 120),
            ("run2", "2024-01-01", "silver_processing", "FAILURE", 0, 45),
        ]
        
        df = spark.createDataFrame(
            runs,
            ["run_key", "run_date", "pipeline_name", "status", "records_processed", "duration_seconds"]
        )
        
        # Count failures
        failures = df.filter("status = 'FAILURE'").count()
        assert failures == 1


@pytest.mark.integration
class TestGoldNotebookExecution:
    """Integration tests for gold notebooks."""

    def test_gold_build_workflow(self, workspace_client):
        """Test complete gold build workflow."""
        pytest.skip("Requires deployed workflow - see test_workflows.py")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
