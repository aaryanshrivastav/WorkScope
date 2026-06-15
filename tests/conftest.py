"""
LMIP Test Configuration and Shared Fixtures

Provides reusable fixtures for unit and integration tests.
Uses pytest-spark for Spark session management.
"""

import pytest
from datetime import datetime, timedelta
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, TimestampType, BooleanType, IntegerType, DoubleType
import hashlib


@pytest.fixture(scope="session")
def spark():
    """
    Create a Spark session for testing.
    Session-scoped to reuse across all tests.
    """
    spark = (
        SparkSession.builder
        .appName("LMIP_Unit_Tests")
        .master("local[2]")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.default.parallelism", "2")
        .config("spark.sql.warehouse.dir", "/tmp/spark-warehouse")
        .config("spark.driver.memory", "2g")
        .getOrCreate()
    )
    
    # Set log level to WARN to reduce noise
    spark.sparkContext.setLogLevel("WARN")
    
    yield spark
    
    spark.stop()


@pytest.fixture(scope="function")
def clean_spark(spark):
    """
    Provide a clean Spark session for each test by dropping test tables.
    Function-scoped to ensure test isolation.
    """
    # Clean up any test tables before test
    test_databases = ["test_bronze", "test_silver", "test_warehouse", "test_metadata"]
    for db in test_databases:
        try:
            spark.sql(f"DROP DATABASE IF EXISTS {db} CASCADE")
        except:
            pass
    
    yield spark
    
    # Clean up after test
    for db in test_databases:
        try:
            spark.sql(f"DROP DATABASE IF EXISTS {db} CASCADE")
        except:
            pass


@pytest.fixture
def sample_bronze_jobs(spark):
    """
    Create sample bronze job records for testing.
    Returns a DataFrame with typical raw job postings.
    """
    data = [
        {
            "source_name": "remotive",
            "source_job_id": "rem_001",
            "source_job_key": "remotive_rem_001",
            "company_name": "Acme Corp",
            "title": "Senior Python Developer",
            "description": "Looking for experienced Python developer with Django and FastAPI",
            "location": "Remote, USA",
            "remote_type": "REMOTE",
            "source_url": "https://remotive.com/job/rem_001",
            "posted_at": datetime(2026, 6, 1, 10, 0, 0),
            "last_seen": datetime(2026, 6, 7, 10, 0, 0),
            "batch_id": "batch_20260607_001",
            "ingested_at": datetime(2026, 6, 7, 10, 5, 0)
        },
        {
            "source_name": "arbeitnow",
            "source_job_id": "arb_002",
            "source_job_key": "arbeitnow_arb_002",
            "company_name": "TechStart Inc.",
            "title": "Data Engineer - AWS",
            "description": "Data engineering role working with AWS, Spark, and Python",
            "location": "Berlin, Germany",
            "remote_type": "HYBRID",
            "source_url": "https://arbeitnow.com/job/arb_002",
            "posted_at": datetime(2026, 6, 2, 14, 30, 0),
            "last_seen": datetime(2026, 6, 7, 10, 0, 0),
            "batch_id": "batch_20260607_001",
            "ingested_at": datetime(2026, 6, 7, 10, 5, 0)
        },
        {
            "source_name": "remotive",
            "source_job_id": "rem_003",
            "source_job_key": "remotive_rem_003",
            "company_name": "Finance Solutions Ltd",
            "title": "Backend Engineer",
            "description": "Backend development for fintech platform using Java and Spring",
            "location": "London, UK",
            "remote_type": "ONSITE",
            "source_url": "https://remotive.com/job/rem_003",
            "posted_at": datetime(2026, 6, 3, 9, 0, 0),
            "last_seen": datetime(2026, 6, 7, 10, 0, 0),
            "batch_id": "batch_20260607_001",
            "ingested_at": datetime(2026, 6, 7, 10, 5, 0)
        }
    ]
    
    schema = StructType([
        StructField("source_name", StringType(), False),
        StructField("source_job_id", StringType(), False),
        StructField("source_job_key", StringType(), False),
        StructField("company_name", StringType(), True),
        StructField("title", StringType(), True),
        StructField("description", StringType(), True),
        StructField("location", StringType(), True),
        StructField("remote_type", StringType(), True),
        StructField("source_url", StringType(), True),
        StructField("posted_at", TimestampType(), True),
        StructField("last_seen", TimestampType(), True),
        StructField("batch_id", StringType(), False),
        StructField("ingested_at", TimestampType(), False)
    ])
    
    return spark.createDataFrame(data, schema)


@pytest.fixture
def sample_silver_jobs(spark):
    """
    Create sample silver job records with normalized fields.
    """
    data = [
        {
            "enterprise_job_id": "job_001",
            "source_name": "remotive",
            "source_job_id": "rem_001",
            "source_job_key": "remotive_rem_001",
            "company_name_raw": "Acme Corp",
            "company_name_norm": "acme corp",
            "title_raw": "Senior Python Developer",
            "title_normalized": "senior python developer",
            "description_raw": "Looking for experienced Python developer",
            "location_raw": "Remote, USA",
            "location_norm": "remote usa",
            "remote_type": "REMOTE",
            "source_url": "https://remotive.com/job/rem_001",
            "posted_at": datetime(2026, 6, 1, 10, 0, 0),
            "last_seen": datetime(2026, 6, 7, 10, 0, 0),
            "is_active": True,
            "soft_delete_flag": False,
            "soft_delete_reason": None,
            "record_hash": "abc123",
            "current_batch_id": "batch_20260607_001",
            "created_at": datetime(2026, 6, 7, 10, 5, 0),
            "updated_at": datetime(2026, 6, 7, 10, 5, 0)
        },
        {
            "enterprise_job_id": "job_002",
            "source_name": "arbeitnow",
            "source_job_id": "arb_002",
            "source_job_key": "arbeitnow_arb_002",
            "company_name_raw": "TechStart Inc.",
            "company_name_norm": "techstart inc",
            "title_raw": "Data Engineer - AWS",
            "title_normalized": "data engineer aws",
            "description_raw": "Data engineering role with AWS",
            "location_raw": "Berlin, Germany",
            "location_norm": "berlin germany",
            "remote_type": "HYBRID",
            "source_url": "https://arbeitnow.com/job/arb_002",
            "posted_at": datetime(2026, 6, 2, 14, 30, 0),
            "last_seen": datetime(2026, 6, 7, 10, 0, 0),
            "is_active": True,
            "soft_delete_flag": False,
            "soft_delete_reason": None,
            "record_hash": "def456",
            "current_batch_id": "batch_20260607_001",
            "created_at": datetime(2026, 6, 7, 10, 5, 0),
            "updated_at": datetime(2026, 6, 7, 10, 5, 0)
        }
    ]
    
    schema = StructType([
        StructField("enterprise_job_id", StringType(), False),
        StructField("source_name", StringType(), True),
        StructField("source_job_id", StringType(), True),
        StructField("source_job_key", StringType(), True),
        StructField("company_name_raw", StringType(), True),
        StructField("company_name_norm", StringType(), True),
        StructField("title_raw", StringType(), True),
        StructField("title_normalized", StringType(), True),
        StructField("description_raw", StringType(), True),
        StructField("location_raw", StringType(), True),
        StructField("location_norm", StringType(), True),
        StructField("remote_type", StringType(), True),
        StructField("source_url", StringType(), True),
        StructField("posted_at", TimestampType(), True),
        StructField("last_seen", TimestampType(), True),
        StructField("is_active", BooleanType(), True),
        StructField("soft_delete_flag", BooleanType(), True),
        StructField("soft_delete_reason", StringType(), True),
        StructField("record_hash", StringType(), True),
        StructField("current_batch_id", StringType(), True),
        StructField("created_at", TimestampType(), True),
        StructField("updated_at", TimestampType(), True)
    ])
    
    return spark.createDataFrame(data, schema)


def compute_record_hash(*fields):
    """
    Helper function to compute record hash from fields.
    Used for CDC change detection.
    
    Args:
        *fields: Variable number of field values
    
    Returns:
        str: MD5 hash of concatenated fields
    """
    content = "|".join([str(f) if f is not None else "" for f in fields])
    return hashlib.md5(content.encode()).hexdigest()


@pytest.fixture
def record_hash_function():
    """Provide the record hash function as a fixture"""
    return compute_record_hash


@pytest.fixture
def sample_sector_keywords():
    """Sample sector keywords for classification testing"""
    return {
        1: ["software", "developer", "engineer", "tech", "python", "java", "data"],
        2: ["finance", "banking", "fintech", "trading", "accountant"],
        3: ["healthcare", "medical", "nurse", "doctor", "clinical"],
        4: ["sales", "marketing", "account manager", "business development"],
        -1: ["unknown"]
    }


@pytest.fixture
def sample_dim_jobs(spark):
    """
    Create sample dimension job records for SCD2 testing.
    """
    data = [
        {
            "job_sk": 1,
            "enterprise_job_id": "job_001",
            "source_name": "remotive",
            "source_job_id": "rem_001",
            "canonical_role_id": "role_001",
            "company_sk": 100,
            "location_sk": 200,
            "sector_sk": 1,
            "role_sk": 300,
            "title_raw": "Senior Python Developer",
            "title_normalized": "senior python developer",
            "description_raw": "Looking for experienced Python developer",
            "location_raw": "Remote, USA",
            "remote_type": "REMOTE",
            "salary_min": None,
            "salary_max": None,
            "salary_currency": None,
            "posted_at": datetime(2026, 6, 1, 10, 0, 0),
            "record_hash": "abc123",
            "effective_from": datetime(2026, 6, 1, 10, 0, 0),
            "effective_to": None,
            "is_current": True,
            "created_at": datetime(2026, 6, 1, 10, 5, 0),
            "updated_at": datetime(2026, 6, 1, 10, 5, 0)
        }
    ]
    
    schema = StructType([
        StructField("job_sk", IntegerType(), False),
        StructField("enterprise_job_id", StringType(), False),
        StructField("source_name", StringType(), True),
        StructField("source_job_id", StringType(), True),
        StructField("canonical_role_id", StringType(), True),
        StructField("company_sk", IntegerType(), True),
        StructField("location_sk", IntegerType(), True),
        StructField("sector_sk", IntegerType(), True),
        StructField("role_sk", IntegerType(), True),
        StructField("title_raw", StringType(), True),
        StructField("title_normalized", StringType(), True),
        StructField("description_raw", StringType(), True),
        StructField("location_raw", StringType(), True),
        StructField("remote_type", StringType(), True),
        StructField("salary_min", DoubleType(), True),
        StructField("salary_max", DoubleType(), True),
        StructField("salary_currency", StringType(), True),
        StructField("posted_at", TimestampType(), True),
        StructField("record_hash", StringType(), True),
        StructField("effective_from", TimestampType(), True),
        StructField("effective_to", TimestampType(), True),
        StructField("is_current", BooleanType(), True),
        StructField("created_at", TimestampType(), True),
        StructField("updated_at", TimestampType(), True)
    ])
    
    return spark.createDataFrame(data, schema)


@pytest.fixture
def scd2_update_function():
    """
    Provide SCD2 update function that properly enforces 'only one current version' constraint.
    
    This function handles the complete SCD2 Type 2 update logic:
    1. Expires old versions by setting is_current=False and effective_to=change_date
    2. Inserts new versions with is_current=True and effective_from=change_date
    3. Ensures only ONE current version per business key
    
    Args:
        current_df: Current dimension table DataFrame
        staging_df: Staging data with new/changed records
        business_key: Column name for business key (e.g., 'enterprise_job_id')
        change_date: Timestamp for the change
        
    Returns:
        Updated DataFrame with old versions expired and new versions added
    """
    from pyspark.sql import functions as F
    
    def update_scd2(current_df, staging_df, business_key, change_date):
        """
        Apply SCD2 logic: expire old versions, add new versions.
        """
        # Get list of changed business keys
        changed_keys = [row[business_key] for row in staging_df.select(business_key).distinct().collect()]
        
        # Step 1: Expire old versions for changed keys
        # Mark all versions of changed keys as not current
        expired_df = current_df.withColumn(
            "is_current",
            F.when(
                F.col(business_key).isin(changed_keys),
                F.lit(False)
            ).otherwise(F.col("is_current"))
        ).withColumn(
            "effective_to",
            F.when(
                (F.col(business_key).isin(changed_keys)) & (F.col("is_current") == True),
                F.lit(change_date)
            ).otherwise(F.col("effective_to"))
        )
        
        # Reapply the is_current=False to ensure it takes effect
        expired_df = expired_df.withColumn(
            "is_current",
            F.when(
                F.col(business_key).isin(changed_keys),
                F.lit(False)
            ).otherwise(F.col("is_current"))
        )
        
        # Step 2: Prepare new versions from staging
        # Add SCD2 metadata columns to staging data
        new_versions_df = staging_df.withColumn("effective_from", F.lit(change_date)) \
            .withColumn("effective_to", F.lit(None).cast("timestamp")) \
            .withColumn("is_current", F.lit(True))
        
        # Step 3: Union expired old versions with new current versions
        result_df = expired_df.union(new_versions_df)
        
        return result_df
    
    return update_scd2


@pytest.fixture
def quarantine_routing_function():
    """
    Provide quarantine routing function with suspicious content pattern detection.
    
    Implements data quality rules to flag jobs for quarantine:
    1. Missing required fields (NULL values)
    2. Empty strings in required fields
    3. Suspicious content patterns (spam indicators)
    4. Invalid data formats
    
    Args:
        df: Input DataFrame with job data
        required_fields: List of field names that cannot be NULL or empty
        
    Returns:
        DataFrame with is_quarantined and quarantine_reason columns
    """
    from pyspark.sql import functions as F
    
    def route_to_quarantine(df, required_fields=None):
        """
        Apply quarantine routing rules.
        """
        if required_fields is None:
            required_fields = ["company", "title", "description"]
        
        # Start with no quarantine
        result_df = df.withColumn("is_quarantined", F.lit(False)) \
                      .withColumn("quarantine_reason", F.lit(None).cast("string"))
        
        # Rule 1: Missing required fields (NULL or empty)
        for field in required_fields:
            if field in df.columns:
                result_df = result_df.withColumn(
                    "is_quarantined",
                    F.when(
                        F.col(field).isNull() | (F.trim(F.col(field)) == ""),
                        F.lit(True)
                    ).otherwise(F.col("is_quarantined"))
                ).withColumn(
                    "quarantine_reason",
                    F.when(
                        (F.col(field).isNull() | (F.trim(F.col(field)) == "")) & F.col("quarantine_reason").isNull(),
                        F.lit("MISSING_REQUIRED_FIELD")
                    ).otherwise(F.col("quarantine_reason"))
                )
        
        # Rule 2: Suspicious content patterns
        if "title" in df.columns:
            # Excessive exclamation marks in title (more than 2)
            result_df = result_df.withColumn(
                "is_quarantined",
                F.when(
                    F.length(F.regexp_replace(F.col("title"), "[^!]", "")) > 2,
                    F.lit(True)
                ).otherwise(F.col("is_quarantined"))
            ).withColumn(
                "quarantine_reason",
                F.when(
                    (F.length(F.regexp_replace(F.col("title"), "[^!]", "")) > 2) & F.col("quarantine_reason").isNull(),
                    F.lit("SUSPICIOUS_CONTENT")
                ).otherwise(F.col("quarantine_reason"))
            )
        
        if "description" in df.columns:
            # Excessive exclamation marks in description (more than 5)
            result_df = result_df.withColumn(
                "is_quarantined",
                F.when(
                    F.length(F.regexp_replace(F.col("description"), "[^!]", "")) > 5,
                    F.lit(True)
                ).otherwise(F.col("is_quarantined"))
            ).withColumn(
                "quarantine_reason",
                F.when(
                    (F.length(F.regexp_replace(F.col("description"), "[^!]", "")) > 5) & F.col("quarantine_reason").isNull(),
                    F.lit("SUSPICIOUS_CONTENT")
                ).otherwise(F.col("quarantine_reason"))
            )
            
            # Excessive dollar signs (more than 3)
            result_df = result_df.withColumn(
                "is_quarantined",
                F.when(
                    F.length(F.regexp_replace(F.col("description"), "[^$]", "")) > 3,
                    F.lit(True)
                ).otherwise(F.col("is_quarantined"))
            ).withColumn(
                "quarantine_reason",
                F.when(
                    (F.length(F.regexp_replace(F.col("description"), "[^$]", "")) > 3) & F.col("quarantine_reason").isNull(),
                    F.lit("SUSPICIOUS_CONTENT")
                ).otherwise(F.col("quarantine_reason"))
            )
            
            # Description too long (more than 5000 characters)
            result_df = result_df.withColumn(
                "is_quarantined",
                F.when(
                    F.length(F.col("description")) > 5000,
                    F.lit(True)
                ).otherwise(F.col("is_quarantined"))
            ).withColumn(
                "quarantine_reason",
                F.when(
                    (F.length(F.col("description")) > 5000) & F.col("quarantine_reason").isNull(),
                    F.lit("SUSPICIOUS_CONTENT")
                ).otherwise(F.col("quarantine_reason"))
            )
        
        return result_df
    
    return route_to_quarantine
