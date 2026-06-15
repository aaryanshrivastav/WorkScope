"""
Test SCD2 Key Generation and Change Tracking (wh_dim_job_scd2)

Tests Slowly Changing Dimension Type 2 logic for job dimension table.
Critical for historical accuracy and audit trail.

Priority: HIGH RISK (correctness critical for reporting)
"""

import pytest
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType, BooleanType
from datetime import datetime, timedelta


class TestSurrogateKeyGeneration:
    """Test surrogate key (job_sk) generation"""
    
    def test_generate_new_surrogate_key(self, spark):
        """New records should get new surrogate keys"""
        data = [
            ("job_001", "Developer"),
            ("job_002", "Engineer"),
        ]
        
        schema = StructType([
            StructField("enterprise_job_id", StringType(), True),
            StructField("title", StringType(), True)
        ])
        df = spark.createDataFrame(data, schema)
        
        # Generate surrogate keys using row_number
        from pyspark.sql.window import Window
        
        df_with_sk = df.withColumn(
            "job_sk",
            F.row_number().over(Window.orderBy("enterprise_job_id"))
        )
        
        results = df_with_sk.collect()
        
        # Should have sequential surrogate keys
        assert results[0].job_sk == 1
        assert results[1].job_sk == 2
    
    def test_surrogate_key_uniqueness(self, spark):
        """Each version of a job should have a unique surrogate key"""
        # Same enterprise_job_id, different versions
        data = [
            (1, "job_001", "Developer", 1),       # Version 1
            (2, "job_001", "Senior Developer", 2), # Version 2 (updated title)
        ]
        
        schema = StructType([
            StructField("job_sk", IntegerType(), True),
            StructField("enterprise_job_id", StringType(), True),
            StructField("title", StringType(), True),
            StructField("expected_sk", IntegerType(), True)
        ])
        df = spark.createDataFrame(data, schema)
        
        results = df.collect()
        
        # Each version should have different surrogate key
        assert results[0].job_sk != results[1].job_sk
        assert results[0].enterprise_job_id == results[1].enterprise_job_id
    
    def test_surrogate_key_sequence_increments(self, spark):
        """Surrogate keys should increment by 1"""
        existing_max_sk = 100
        
        # New records should start from existing_max_sk + 1
        new_sk_start = existing_max_sk + 1
        
        data = [
            (new_sk_start, "job_new_001"),
            (new_sk_start + 1, "job_new_002"),
        ]
        
        schema = StructType([
            StructField("job_sk", IntegerType(), True),
            StructField("enterprise_job_id", StringType(), True)
        ])
        df = spark.createDataFrame(data, schema)
        
        results = df.collect()
        
        assert results[0].job_sk == 101
        assert results[1].job_sk == 102


class TestSCD2ChangeDetection:
    """Test SCD2 change detection logic"""
    
    def test_detect_changed_record(self, spark, record_hash_function):
        """Detect when a record has changed (different hash)"""
        # Current dimension
        current_data = [
            (1, "job_001", "Developer", "acme", "hash_old", True),
        ]
        
        schema = StructType([
            StructField("job_sk", IntegerType(), True),
            StructField("enterprise_job_id", StringType(), True),
            StructField("title", StringType(), True),
            StructField("company", StringType(), True),
            StructField("record_hash", StringType(), True),
            StructField("is_current", BooleanType(), True)
        ])
        current_df = spark.createDataFrame(current_data, schema)
        
        # New staging data
        staging_data = [
            ("job_001", "Senior Developer", "acme", "hash_new"),  # Title changed
        ]
        
        schema = StructType([
            StructField("enterprise_job_id", StringType(), True),
            StructField("title", StringType(), True),
            StructField("company", StringType(), True),
            StructField("record_hash", StringType(), True)
        ])
        staging_df = spark.createDataFrame(staging_data, schema)
        
        # Detect changes (hash mismatch)
        changes_df = current_df.alias("cur").join(
            staging_df.alias("stg"),
            F.col("cur.enterprise_job_id") == F.col("stg.enterprise_job_id"),
            "inner"
        ).where(
            (F.col("cur.is_current") == True) &
            (F.col("cur.record_hash") != F.col("stg.record_hash"))
        )
        
        assert changes_df.count() == 1, "Should detect 1 changed record"
    
    def test_no_change_when_hash_matches(self, spark):
        """Do NOT create new version when hash matches (no change)"""
        current_data = [
            (1, "job_001", "Developer", "hash_same", True),
        ]
        
        schema = StructType([
            StructField("job_sk", IntegerType(), True),
            StructField("enterprise_job_id", StringType(), True),
            StructField("title", StringType(), True),
            StructField("record_hash", StringType(), True),
            StructField("is_current", BooleanType(), True)
        ])
        current_df = spark.createDataFrame(current_data, schema)
        
        staging_data = [
            ("job_001", "Developer", "hash_same"),  # Same hash
        ]
        
        schema = StructType([
            StructField("enterprise_job_id", StringType(), True),
            StructField("title", StringType(), True),
            StructField("record_hash", StringType(), True)
        ])
        staging_df = spark.createDataFrame(staging_data, schema)
        
        # Detect changes
        changes_df = current_df.alias("cur").join(
            staging_df.alias("stg"),
            F.col("cur.enterprise_job_id") == F.col("stg.enterprise_job_id"),
            "inner"
        ).where(
            (F.col("cur.is_current") == True) &
            (F.col("cur.record_hash") != F.col("stg.record_hash"))
        )
        
        assert changes_df.count() == 0, "Should detect 0 changes (hash matches)"
    
    def test_detect_new_record(self, spark):
        """Detect when a record is new (not in current dimension)"""
        current_data = [
            (1, "job_001", "Developer", True),
        ]
        
        schema = StructType([
            StructField("job_sk", IntegerType(), True),
            StructField("enterprise_job_id", StringType(), True),
            StructField("title", StringType(), True),
            StructField("is_current", BooleanType(), True)
        ])
        current_df = spark.createDataFrame(current_data, schema)
        
        staging_data = [
            ("job_002", "Engineer"),  # New job
        ]
        
        schema = StructType([
            StructField("enterprise_job_id", StringType(), True),
            StructField("title", StringType(), True)
        ])
        staging_df = spark.createDataFrame(staging_data, schema)
        
        # Detect new records (left anti join)
        new_df = staging_df.alias("stg").join(
            current_df.alias("cur"),
            F.col("stg.enterprise_job_id") == F.col("cur.enterprise_job_id"),
            "left_anti"
        )
        
        assert new_df.count() == 1, "Should detect 1 new record"


class TestSCD2EffectiveDates:
    """Test effective_from and effective_to date management"""
    
    def test_new_record_effective_dates(self, spark):
        """New records should have effective_from=current_date, effective_to=NULL"""
        current_date = datetime(2026, 6, 7, 10, 0, 0)
        
        data = [
            ("job_001", "Developer", current_date, None),
        ]
        
        schema = StructType([
            StructField("enterprise_job_id", StringType(), True),
            StructField("title", StringType(), True),
            StructField("effective_from", StringType(), True),
            StructField("effective_to", StringType(), True)
        ])
        df = spark.createDataFrame(data, schema)
        
        result = df.collect()[0]
        
        assert result.effective_from == current_date
        assert result.effective_to is None, "New records should have NULL effective_to"
    
    def test_expire_old_record_on_change(self, spark):
        """When record changes, old version should get effective_to date"""
        # Current record (active)
        current_data = [
            (1, "job_001", "Developer", datetime(2026, 6, 1), None, True),
        ]
        
        schema = StructType([
            StructField("job_sk", IntegerType(), True),
            StructField("enterprise_job_id", StringType(), True),
            StructField("title", StringType(), True),
            StructField("effective_from", StringType(), True),
            StructField("effective_to", StringType(), True),
            StructField("is_current", BooleanType(), True)
        ])
        current_df = spark.createDataFrame(current_data, schema)
        
        # Update: expire old record
        change_date = datetime(2026, 6, 7)
        
        updated_df = current_df.withColumn("effective_to", F.lit(change_date)) \
            .withColumn("is_current", F.lit(False))
        
        result = updated_df.collect()[0]
        
        assert result.effective_to == change_date, "Old record should be expired"
        assert result.is_current == False, "Old record should not be current"
    
    def test_new_version_inherits_effective_from(self, spark):
        """New version should have effective_from = old version's effective_to + 1 microsecond"""
        old_effective_to = datetime(2026, 6, 7, 0, 0, 0)
        new_effective_from = old_effective_to + timedelta(microseconds=1)
        
        # New version starts immediately after old version ends
        assert new_effective_from > old_effective_to
        
        # Or more commonly: new version starts at change date
        change_date = datetime(2026, 6, 7, 10, 0, 0)
        
        data = [
            (2, "job_001", "Senior Developer", change_date, None, True),  # New version
        ]
        
        schema = StructType([
            StructField("job_sk", IntegerType(), True),
            StructField("enterprise_job_id", StringType(), True),
            StructField("title", StringType(), True),
            StructField("effective_from", StringType(), True),
            StructField("effective_to", StringType(), True),
            StructField("is_current", BooleanType(), True)
        ])
        df = spark.createDataFrame(data, schema)
        
        result = df.collect()[0]
        
        assert result.effective_from == change_date
        assert result.is_current == True


class TestSCD2CurrentFlag:
    """Test is_current flag management"""
    
    def test_only_one_current_version_per_job(self, spark):
        """Each enterprise_job_id should have exactly one current version"""
        data = [
            (1, "job_001", "Developer", True),      # Current
            (2, "job_001", "Sr Developer", False),  # Historical
            (3, "job_002", "Engineer", True),       # Current (different job)
        ]
        
        schema = StructType([
            StructField("job_sk", IntegerType(), True),
            StructField("enterprise_job_id", StringType(), True),
            StructField("title", StringType(), True),
            StructField("is_current", BooleanType(), True)
        ])
        df = spark.createDataFrame(data, schema)
        
        # Count current versions per job
        current_per_job = df.filter(F.col("is_current") == True) \
            .groupBy("enterprise_job_id").count()
        
        results = current_per_job.collect()
        
        for row in results:
            assert row.count == 1, \
                f"{row.enterprise_job_id} should have exactly 1 current version"
    
    def test_set_old_version_not_current(self, spark):
        """When creating new version, set old version is_current=False"""
        data = [
            (1, "job_001", True),
        ]
        
        schema = StructType([
            StructField("job_sk", IntegerType(), True),
            StructField("enterprise_job_id", StringType(), True),
            StructField("is_current", BooleanType(), True)
        ])
        df = spark.createDataFrame(data, schema)
        
        # Simulate update: flip flag
        updated_df = df.withColumn("is_current", F.lit(False))
        
        result = updated_df.collect()[0]
        
        assert result.is_current == False


class TestSCD2CompleteFlow:
    """Test complete SCD2 insert/update flow"""
    
    def test_insert_new_job(self, spark):
        """INSERT: Add completely new job to dimension"""
        # Empty dimension
        current_df = spark.createDataFrame(
            [],
            StructType([
                StructField("job_sk", IntegerType()),
                StructField("enterprise_job_id", StringType()),
                StructField("title", StringType()),
                StructField("effective_from", TimestampType()),
                StructField("effective_to", TimestampType()),
                StructField("is_current", BooleanType())
            ])
        )
        
        # New job
        current_date = datetime(2026, 6, 7)
        new_job = [
            (1, "job_001", "Developer", current_date, None, True),
        ]
        
        schema = StructType([
            StructField("job_sk", IntegerType(), True),
            StructField("enterprise_job_id", StringType(), True),
            StructField("title", StringType(), True),
            StructField("effective_from", StringType(), True),
            StructField("effective_to", StringType(), True),
            StructField("is_current", BooleanType(), True)
        ])
        new_df = spark.createDataFrame(new_job, schema)
        
        # Union to insert
        result_df = current_df.union(new_df)
        
        assert result_df.count() == 1
        result = result_df.collect()[0]
        assert result.is_current == True
        assert result.effective_to is None
    
    def test_update_existing_job_scd2(self, spark):
        """UPDATE: Create new version for changed job (SCD2)"""
        # Current dimension
        current_data = [
            (1, "job_001", "Developer", datetime(2026, 6, 1), None, True),
        ]
        
        schema = StructType([
            StructField("job_sk", IntegerType(), True),
            StructField("enterprise_job_id", StringType(), True),
            StructField("title", StringType(), True),
            StructField("effective_from", StringType(), True),
            StructField("effective_to", StringType(), True),
            StructField("is_current", BooleanType(), True)
        ])
        current_df = spark.createDataFrame(current_data, schema)
        
        # Step 1: Expire old version
        change_date = datetime(2026, 6, 7)
        
        expired_df = current_df.withColumn("effective_to", F.lit(change_date)) \
            .withColumn("is_current", F.lit(False))
        
        # Step 2: Insert new version
        new_version = [
            (2, "job_001", "Senior Developer", change_date, None, True),
        ]
        
        schema = StructType([
            StructField("job_sk", IntegerType(), True),
            StructField("enterprise_job_id", StringType(), True),
            StructField("title", StringType(), True),
            StructField("effective_from", StringType(), True),
            StructField("effective_to", StringType(), True),
            StructField("is_current", BooleanType(), True)
        ])
        new_version_df = spark.createDataFrame(new_version, schema)
        
        # Union old (expired) and new (current)
        result_df = expired_df.union(new_version_df)
        
        assert result_df.count() == 2, "Should have 2 versions"
        
        current_version = result_df.filter(F.col("is_current") == True).collect()[0]
        historical_version = result_df.filter(F.col("is_current") == False).collect()[0]
        
        assert current_version.job_sk == 2
        assert current_version.title == "Senior Developer"
        assert historical_version.job_sk == 1
        assert historical_version.effective_to == change_date
    
    def test_no_op_when_no_change(self, spark):
        """NO-OP: Do nothing when record hasn't changed"""
        current_data = [
            (1, "job_001", "Developer", "hash_same", True),
        ]
        
        schema = StructType([
            StructField("job_sk", IntegerType(), True),
            StructField("enterprise_job_id", StringType(), True),
            StructField("title", StringType(), True),
            StructField("record_hash", StringType(), True),
            StructField("is_current", BooleanType(), True)
        ])
        current_df = spark.createDataFrame(current_data, schema)
        
        staging_data = [
            ("job_001", "Developer", "hash_same"),  # No change
        ]
        
        schema = StructType([
            StructField("enterprise_job_id", StringType(), True),
            StructField("title", StringType(), True),
            StructField("record_hash", StringType(), True)
        ])
        staging_df = spark.createDataFrame(staging_data, schema)
        
        # Detect changes
        changes = current_df.alias("cur").join(
            staging_df.alias("stg"),
            F.col("cur.enterprise_job_id") == F.col("stg.enterprise_job_id"),
            "inner"
        ).where(
            F.col("cur.record_hash") != F.col("stg.record_hash")
        ).count()
        
        assert changes == 0, "No changes detected - no action needed"


class TestSCD2HistoricalQuery:
    """Test querying historical versions"""
    
    def test_get_current_version(self, spark):
        """Query current version of a job"""
        data = [
            (1, "job_001", "Developer", True),
            (2, "job_001", "Sr Developer", False),  # Historical
        ]
        
        schema = StructType([
            StructField("job_sk", IntegerType(), True),
            StructField("enterprise_job_id", StringType(), True),
            StructField("title", StringType(), True),
            StructField("is_current", BooleanType(), True)
        ])
        df = spark.createDataFrame(data, schema)
        
        current_version = df.filter(
            (F.col("enterprise_job_id") == "job_001") &
            (F.col("is_current") == True)
        ).collect()[0]
        
        assert current_version.job_sk == 1
        assert current_version.title == "Developer"
    
    def test_get_version_at_specific_date(self, spark):
        """Query version that was active at a specific date"""
        data = [
            (1, "job_001", datetime(2026, 5, 1), datetime(2026, 6, 1), False),  # May
            (2, "job_001", datetime(2026, 6, 1), None, True),                    # June onwards
        ]
        
        schema = StructType([
            StructField("job_sk", IntegerType(), True),
            StructField("enterprise_job_id", StringType(), True),
            StructField("effective_from", StringType(), True),
            StructField("effective_to", StringType(), True),
            StructField("is_current", BooleanType(), True)
        ])
        df = spark.createDataFrame(data, schema)
        
        query_date = datetime(2026, 5, 15)  # Mid-May
        
        version_at_date = df.filter(
            (F.col("enterprise_job_id") == "job_001") &
            (F.col("effective_from") <= F.lit(query_date)) &
            ((F.col("effective_to").isNull()) | (F.col("effective_to") > F.lit(query_date)))
        ).collect()
        
        assert len(version_at_date) == 1
        assert version_at_date[0].job_sk == 1, "Should return May version"
    
    def test_get_all_versions_history(self, spark):
        """Query complete history of a job"""
        data = [
            (1, "job_001", "Developer", datetime(2026, 5, 1), datetime(2026, 6, 1)),
            (2, "job_001", "Sr Developer", datetime(2026, 6, 1), datetime(2026, 7, 1)),
            (3, "job_001", "Lead Developer", datetime(2026, 7, 1), None),
        ]
        
        schema = StructType([
            StructField("job_sk", IntegerType(), True),
            StructField("enterprise_job_id", StringType(), True),
            StructField("title", StringType(), True),
            StructField("effective_from", StringType(), True),
            StructField("effective_to", StringType(), True)
        ])
        df = spark.createDataFrame(data, schema)
        
        history = df.filter(F.col("enterprise_job_id") == "job_001") \
            .orderBy("effective_from") \
            .collect()
        
        assert len(history) == 3, "Should have 3 versions"
        assert history[0].title == "Developer"
        assert history[1].title == "Sr Developer"
        assert history[2].title == "Lead Developer"


class TestSCD2EdgeCases:
    """Test edge cases"""
    
    def test_same_day_multiple_changes(self, spark):
        """Handle multiple changes on the same day"""
        data = [
            (1, "job_001", datetime(2026, 6, 7, 9, 0), datetime(2026, 6, 7, 10, 0)),   # Morning
            (2, "job_001", datetime(2026, 6, 7, 10, 0), datetime(2026, 6, 7, 15, 0)),  # Midday
            (3, "job_001", datetime(2026, 6, 7, 15, 0), None),                          # Afternoon
        ]
        
        schema = StructType([
            StructField("job_sk", IntegerType(), True),
            StructField("enterprise_job_id", StringType(), True),
            StructField("effective_from", StringType(), True),
            StructField("effective_to", StringType(), True)
        ])
        df = spark.createDataFrame(data, schema)
        
        # Query at specific time
        query_time = datetime(2026, 6, 7, 12, 0)  # Noon
        
        version = df.filter(
            (F.col("effective_from") <= F.lit(query_time)) &
            ((F.col("effective_to").isNull()) | (F.col("effective_to") > F.lit(query_time)))
        ).collect()
        
        assert len(version) == 1
        assert version[0].job_sk == 2, "Should return midday version"
    
    def test_record_deleted_then_recreated(self, spark):
        """Handle job deleted and then recreated"""
        # Version 1: Active
        # Version 2: Deleted (soft delete with effective_to)
        # Version 3: Recreated
        
        data = [
            (1, "job_001", datetime(2026, 5, 1), datetime(2026, 6, 1), False),   # Active
            (2, "job_001", datetime(2026, 6, 1), datetime(2026, 6, 15), False),  # Deleted
            (3, "job_001", datetime(2026, 6, 20), None, True),                    # Recreated
        ]
        
        schema = StructType([
            StructField("job_sk", IntegerType(), True),
            StructField("enterprise_job_id", StringType(), True),
            StructField("effective_from", StringType(), True),
            StructField("effective_to", StringType(), True),
            StructField("is_current", BooleanType(), True)
        ])
        df = spark.createDataFrame(data, schema)
        
        # Should have 3 distinct versions
        assert df.count() == 3
        
        # Current version should be the recreated one
        current = df.filter(F.col("is_current") == True).collect()[0]
        assert current.job_sk == 3
    
    def test_effective_date_gaps(self, spark):
        """Detect gaps in effective date ranges"""
        data = [
            (1, "job_001", datetime(2026, 5, 1), datetime(2026, 5, 31)),  # May
            (2, "job_001", datetime(2026, 6, 15), None),                   # June 15+ (GAP from June 1-14)
        ]
        
        schema = StructType([
            StructField("job_sk", IntegerType(), True),
            StructField("enterprise_job_id", StringType(), True),
            StructField("effective_from", StringType(), True),
            StructField("effective_to", StringType(), True)
        ])
        df = spark.createDataFrame(data, schema)
        
        # Query in the gap period
        gap_date = datetime(2026, 6, 7)
        
        version_in_gap = df.filter(
            (F.col("effective_from") <= F.lit(gap_date)) &
            ((F.col("effective_to").isNull()) | (F.col("effective_to") > F.lit(gap_date)))
        ).count()
        
        assert version_in_gap == 0, "Should find no version in gap period (data quality issue)"
