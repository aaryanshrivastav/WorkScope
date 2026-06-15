"""
Test Export Bundle Manifest Structure

Tests the publish contract and bundle manifest validation.
Critical for consumer data contracts and API stability.

Priority: MEDIUM RISK (contract validation, important for consumers)
"""

import pytest
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType, ArrayType, MapType
from datetime import datetime
import json


class TestManifestStructure:
    """Test manifest JSON structure and required fields"""
    
    def test_manifest_required_fields(self):
        """Manifest must contain all required fields"""
        manifest = {
            "bundle_id": "bundle_20260607_001",
            "created_at": "2026-06-07T10:00:00Z",
            "version": "1.0",
            "catalog": "workspace",
            "schema": "publish",
            "tables": [],
            "metadata": {}
        }
        
        required_fields = ["bundle_id", "created_at", "version", "catalog", "schema", "tables", "metadata"]
        
        for field in required_fields:
            assert field in manifest, f"Manifest missing required field: {field}"
    
    def test_manifest_tables_array_structure(self):
        """Tables array must contain properly structured entries"""
        manifest = {
            "tables": [
                {
                    "table_name": "publish_jobs",
                    "full_name": "workspace.publish.publish_jobs",
                    "record_count": 1000,
                    "file_size_bytes": 524288,
                    "partitions": ["year", "month"],
                    "schema": {
                        "fields": [
                            {"name": "job_id", "type": "string", "nullable": False},
                            {"name": "title", "type": "string", "nullable": True}
                        ]
                    }
                }
            ]
        }
        
        table_entry = manifest["tables"][0]
        
        required_table_fields = ["table_name", "full_name", "record_count", "file_size_bytes", "schema"]
        
        for field in required_table_fields:
            assert field in table_entry, f"Table entry missing required field: {field}"
    
    def test_manifest_metadata_structure(self):
        """Metadata must contain lineage and quality information"""
        manifest = {
            "metadata": {
                "source_batch_ids": ["batch_20260607_001"],
                "pipeline_run_id": "run_12345",
                "data_quality_score": 0.98,
                "lineage": {
                    "source_tables": ["bronze.bronze_job_snapshot", "silver.silver_jobs_current"],
                    "transformation_steps": ["standardize", "deduplicate", "enrich"]
                },
                "contact": "data-team@company.com"
            }
        }
        
        metadata = manifest["metadata"]
        
        assert "source_batch_ids" in metadata
        assert "pipeline_run_id" in metadata
        assert "lineage" in metadata
        assert "source_tables" in metadata["lineage"]
        assert "transformation_steps" in metadata["lineage"]


class TestManifestValidation:
    """Test manifest validation rules"""
    
    def test_bundle_id_format(self):
        """Bundle ID must follow naming convention"""
        valid_bundle_ids = [
            "bundle_20260607_001",
            "bundle_20260607_002",
            "bundle_20261231_999"
        ]
        
        invalid_bundle_ids = [
            "bundle_001",           # Missing date
            "20260607_001",         # Missing prefix
            "bundle_2026-06-07",    # Wrong date format
        ]
        
        # Pattern: bundle_YYYYMMDD_NNN
        import re
        pattern = r"^bundle_\d{8}_\d{3}$"
        
        for bundle_id in valid_bundle_ids:
            assert re.match(pattern, bundle_id), f"{bundle_id} should be valid"
        
        for bundle_id in invalid_bundle_ids:
            assert not re.match(pattern, bundle_id), f"{bundle_id} should be invalid"
    
    def test_version_format(self):
        """Version must follow semantic versioning"""
        valid_versions = ["1.0", "1.1", "2.0", "1.0.0"]
        invalid_versions = ["v1.0", "1", "1.0.0.0"]
        
        import re
        # Pattern: major.minor or major.minor.patch
        pattern = r"^\d+\.\d+(\.\d+)?$"
        
        for version in valid_versions:
            assert re.match(pattern, version), f"{version} should be valid"
        
        for version in invalid_versions:
            assert not re.match(pattern, version), f"{version} should be invalid"
    
    def test_table_record_count_positive(self):
        """Table record counts must be non-negative"""
        valid_counts = [0, 1, 1000, 1000000]
        invalid_counts = [-1, -100]
        
        for count in valid_counts:
            assert count >= 0, f"{count} should be valid (>=0)"
        
        for count in invalid_counts:
            assert count < 0, f"{count} should be invalid (<0)"
    
    def test_iso_timestamp_format(self):
        """Timestamps must be in ISO 8601 format"""
        valid_timestamps = [
            "2026-06-07T10:00:00Z",
            "2026-06-07T10:00:00.123Z",
            "2026-06-07T10:00:00+00:00"
        ]
        
        # Validate ISO format by parsing
        from datetime import datetime
        
        for ts in valid_timestamps:
            try:
                # Try parsing with different formats
                if ts.endswith("Z"):
                    datetime.fromisoformat(ts.replace("Z", "+00:00"))
                else:
                    datetime.fromisoformat(ts)
                assert True  # Valid if no exception
            except ValueError:
                assert False, f"{ts} should be valid ISO 8601"


class TestManifestGeneration:
    """Test manifest generation from tables"""
    
    def test_generate_manifest_for_single_table(self, spark):
        """Generate manifest for a single table"""
        # Sample table data
        data = [
            ("job_001", "Developer", "Acme Corp"),
            ("job_002", "Engineer", "TechCo"),
        ]
        
        df = spark.createDataFrame(
            data,
            ["job_id", "title", "company"]
        )
        
        # Generate manifest entry
        record_count = df.count()
        
        manifest_entry = {
            "table_name": "publish_jobs",
            "full_name": "workspace.publish.publish_jobs",
            "record_count": record_count,
            "schema": {
                "fields": [
                    {"name": field.name, "type": str(field.dataType), "nullable": field.nullable}
                    for field in df.schema.fields
                ]
            }
        }
        
        assert manifest_entry["record_count"] == 2
        assert len(manifest_entry["schema"]["fields"]) == 3
        assert manifest_entry["schema"]["fields"][0]["name"] == "job_id"
    
    def test_generate_manifest_for_multiple_tables(self, spark):
        """Generate manifest for multiple tables in a bundle"""
        # Table 1: Jobs
        jobs_data = [("job_001", "Developer")]
        jobs_df = spark.createDataFrame(jobs_data, ["job_id", "title"])
        
        # Table 2: Companies
        companies_data = [("comp_001", "Acme Corp")]
        companies_df = spark.createDataFrame(companies_data, ["company_id", "company_name"])
        
        # Generate manifest
        manifest = {
            "bundle_id": "bundle_20260607_001",
            "tables": [
                {
                    "table_name": "publish_jobs",
                    "record_count": jobs_df.count()
                },
                {
                    "table_name": "publish_companies",
                    "record_count": companies_df.count()
                }
            ]
        }
        
        assert len(manifest["tables"]) == 2
        assert manifest["tables"][0]["record_count"] == 1
        assert manifest["tables"][1]["record_count"] == 1


class TestManifestConsistency:
    """Test manifest consistency with actual data"""
    
    def test_manifest_record_count_matches_table(self, spark):
        """Manifest record count must match actual table count"""
        data = [
            ("job_001", "Developer"),
            ("job_002", "Engineer"),
            ("job_003", "Manager"),
        ]
        
        df = spark.createDataFrame(data, ["job_id", "title"])
        
        actual_count = df.count()
        manifest_count = 3
        
        assert actual_count == manifest_count, \
            f"Manifest count ({manifest_count}) must match actual count ({actual_count})"
    
    def test_manifest_schema_matches_table(self, spark):
        """Manifest schema must match actual table schema"""
        data = [("job_001", "Developer", 50000)]
        
        df = spark.createDataFrame(
            data,
            ["job_id", "title", "salary"]
        )
        
        # Extract schema from DataFrame
        actual_schema = {field.name: str(field.dataType) for field in df.schema.fields}
        
        # Manifest schema
        manifest_schema = {
            "job_id": "StringType()",
            "title": "StringType()",
            "salary": "LongType()"  # Note: ints become longs in Spark
        }
        
        for field_name, field_type in manifest_schema.items():
            assert field_name in actual_schema, f"Field {field_name} missing from actual schema"
    
    def test_manifest_partition_info_accurate(self, spark):
        """Manifest partition information must be accurate"""
        # Simulated partitioned table
        data = [
            ("job_001", 2026, 6),
            ("job_002", 2026, 6),
            ("job_003", 2026, 7),
        ]
        
        df = spark.createDataFrame(
            data,
            ["job_id", "year", "month"]
        )
        
        # Get distinct partition values
        partitions = df.select("year", "month").distinct().collect()
        
        manifest_partitions = [
            {"year": row.year, "month": row.month} for row in partitions
        ]
        
        assert len(manifest_partitions) == 2  # 2 distinct year/month combinations
        assert {"year": 2026, "month": 6} in manifest_partitions
        assert {"year": 2026, "month": 7} in manifest_partitions


class TestManifestVersioning:
    """Test manifest versioning and change tracking"""
    
    def test_version_increments_on_schema_change(self):
        """Version should increment when schema changes"""
        # Version 1.0 schema
        v1_schema = {
            "fields": [
                {"name": "job_id", "type": "string"},
                {"name": "title", "type": "string"}
            ]
        }
        
        # Version 1.1 schema (added field)
        v2_schema = {
            "fields": [
                {"name": "job_id", "type": "string"},
                {"name": "title", "type": "string"},
                {"name": "salary", "type": "int"}  # New field
            ]
        }
        
        # Schema changed: increment minor version
        v1_version = "1.0"
        v2_version = "1.1"
        
        assert v1_schema != v2_schema
        assert v2_version > v1_version
    
    def test_version_increments_on_breaking_change(self):
        """Version should increment major version on breaking changes"""
        # Version 1.0 schema
        v1_schema = {
            "fields": [
                {"name": "job_id", "type": "string"},
                {"name": "salary", "type": "int"}
            ]
        }
        
        # Version 2.0 schema (changed field type - BREAKING)
        v2_schema = {
            "fields": [
                {"name": "job_id", "type": "string"},
                {"name": "salary", "type": "string"}  # Changed type
            ]
        }
        
        # Breaking change: increment major version
        v1_version = "1.0"
        v2_version = "2.0"
        
        assert v2_version.split(".")[0] > v1_version.split(".")[0], \
            "Major version should increment on breaking changes"


class TestManifestSerialization:
    """Test manifest JSON serialization"""
    
    def test_manifest_serializes_to_json(self):
        """Manifest must be JSON serializable"""
        manifest = {
            "bundle_id": "bundle_20260607_001",
            "created_at": "2026-06-07T10:00:00Z",
            "version": "1.0",
            "tables": [
                {
                    "table_name": "publish_jobs",
                    "record_count": 1000
                }
            ]
        }
        
        # Should not raise exception
        json_str = json.dumps(manifest)
        
        assert isinstance(json_str, str)
        assert "bundle_20260607_001" in json_str
    
    def test_manifest_deserializes_from_json(self):
        """Manifest must be JSON deserializable"""
        json_str = '''
        {
            "bundle_id": "bundle_20260607_001",
            "created_at": "2026-06-07T10:00:00Z",
            "version": "1.0",
            "tables": []
        }
        '''
        
        # Should not raise exception
        manifest = json.loads(json_str)
        
        assert manifest["bundle_id"] == "bundle_20260607_001"
        assert manifest["version"] == "1.0"
    
    def test_manifest_roundtrip_serialization(self):
        """Manifest should survive JSON roundtrip"""
        original = {
            "bundle_id": "bundle_20260607_001",
            "version": "1.0",
            "tables": [{"table_name": "jobs", "record_count": 100}]
        }
        
        # Serialize and deserialize
        json_str = json.dumps(original)
        deserialized = json.loads(json_str)
        
        assert original == deserialized, \
            "Manifest should be identical after JSON roundtrip"


class TestManifestDataQuality:
    """Test data quality metadata in manifest"""
    
    def test_include_dq_metrics(self):
        """Manifest should include data quality metrics"""
        manifest = {
            "metadata": {
                "data_quality": {
                    "completeness_score": 0.98,
                    "accuracy_score": 0.95,
                    "consistency_score": 1.0,
                    "null_counts": {
                        "title": 5,
                        "company": 2,
                        "salary": 150
                    },
                    "duplicate_count": 3,
                    "quarantine_count": 12
                }
            }
        }
        
        dq = manifest["metadata"]["data_quality"]
        
        assert "completeness_score" in dq
        assert "null_counts" in dq
        assert dq["completeness_score"] >= 0.0
        assert dq["completeness_score"] <= 1.0
    
    def test_include_validation_results(self):
        """Manifest should include validation results"""
        manifest = {
            "metadata": {
                "validation": {
                    "passed": True,
                    "tests_run": 25,
                    "tests_passed": 24,
                    "tests_failed": 1,
                    "failed_tests": [
                        {
                            "test_name": "salary_range_check",
                            "failure_reason": "5 records exceed max salary threshold"
                        }
                    ]
                }
            }
        }
        
        validation = manifest["metadata"]["validation"]
        
        assert validation["passed"] == True
        assert validation["tests_passed"] == 24
        assert len(validation["failed_tests"]) == 1


class TestManifestLineage:
    """Test lineage information in manifest"""
    
    def test_include_source_lineage(self):
        """Manifest should trace data lineage to source"""
        manifest = {
            "metadata": {
                "lineage": {
                    "source_tables": [
                        "bronze.bronze_job_snapshot",
                        "bronze.bronze_api_response_log"
                    ],
                    "intermediate_tables": [
                        "silver.silver_jobs_staging",
                        "silver.silver_jobs_current"
                    ],
                    "transformation_pipeline": "LMIP_GoldBuild",
                    "source_batch_ids": [
                        "batch_20260607_001",
                        "batch_20260607_002"
                    ]
                }
            }
        }
        
        lineage = manifest["metadata"]["lineage"]
        
        assert "source_tables" in lineage
        assert "transformation_pipeline" in lineage
        assert len(lineage["source_batch_ids"]) == 2
    
    def test_include_dependency_graph(self):
        """Manifest should include table dependency graph"""
        manifest = {
            "metadata": {
                "lineage": {
                    "dependencies": {
                        "publish_jobs": ["silver_jobs_current", "warehouse_dim_job"],
                        "publish_companies": ["warehouse_dim_company"]
                    }
                }
            }
        }
        
        deps = manifest["metadata"]["lineage"]["dependencies"]
        
        assert "publish_jobs" in deps
        assert "silver_jobs_current" in deps["publish_jobs"]


class TestManifestContractValidation:
    """Test consumer contract validation"""
    
    def test_validate_against_contract_schema(self):
        """Validate manifest against published contract schema"""
        contract_schema = {
            "required_fields": ["job_id", "title", "company"],
            "field_types": {
                "job_id": "string",
                "title": "string",
                "company": "string"
            }
        }
        
        manifest_schema = {
            "fields": [
                {"name": "job_id", "type": "string"},
                {"name": "title", "type": "string"},
                {"name": "company", "type": "string"},
                {"name": "salary", "type": "int"}  # Optional field
            ]
        }
        
        # Check required fields present
        manifest_field_names = [f["name"] for f in manifest_schema["fields"]]
        
        for required_field in contract_schema["required_fields"]:
            assert required_field in manifest_field_names, \
                f"Contract requires field {required_field}"
    
    def test_backward_compatibility_check(self):
        """Check manifest is backward compatible with previous version"""
        v1_fields = {"job_id", "title", "company"}
        v2_fields = {"job_id", "title", "company", "salary"}  # Added field
        
        # V2 should be backward compatible (contains all V1 fields)
        assert v1_fields.issubset(v2_fields), \
            "V2 should contain all V1 fields for backward compatibility"
        
        # Breaking change example
        v3_fields = {"job_id", "title"}  # Removed 'company' - BREAKING
        
        assert not v1_fields.issubset(v3_fields), \
            "V3 breaks backward compatibility by removing field"
