"""
Test Quarantine Routing Logic

Tests the data quality failure routing and quarantine management.
Boolean logic with clear rules - easy to unit test thoroughly.

Priority: MEDIUM RISK (clear logic but critical for data quality)
"""

import pytest
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, BooleanType, TimestampType
from datetime import datetime, timedelta


class TestQuarantineRules:
    """Test quarantine rule evaluation"""
    
    def test_missing_required_field_quarantine(self, spark):
        """Jobs missing required fields should be quarantined"""
        data = [
            ("job_001", "Acme Corp", "Developer", "Good job", False),  # Valid
            ("job_002", None, "Developer", "Good job", True),          # Missing company
            ("job_003", "Acme Corp", None, "Good job", True),          # Missing title
            ("job_004", "Acme Corp", "Developer", None, True),         # Missing description
        ]
        
        schema = StructType([
            StructField("job_id", StringType(), True),
            StructField("company", StringType(), True),
            StructField("title", StringType(), True),
            StructField("description", StringType(), True),
            StructField("should_quarantine", BooleanType(), True)
        ])
        df = spark.createDataFrame(data, schema)
        
        # Apply quarantine rule: flag if any required field is NULL
        df_flagged = df.withColumn(
            "is_quarantined",
            F.when(
                F.col("company").isNull() | 
                F.col("title").isNull() | 
                F.col("description").isNull(),
                True
            ).otherwise(False)
        )
        
        results = df_flagged.collect()
        
        for row in results:
            assert row.is_quarantined == row.should_quarantine, \
                f"{row.job_id}: Expected quarantine={row.should_quarantine}, got {row.is_quarantined}"
    
    def test_empty_string_vs_null(self, spark):
        """Empty strings should also trigger quarantine for required fields"""
        data = [
            ("job_001", "Acme", "Dev", "Desc", False),  # Valid
            ("job_002", "", "Dev", "Desc", True),       # Empty company
            ("job_003", "Acme", "", "Desc", True),      # Empty title
        ]
        
        schema = StructType([
            StructField("job_id", StringType(), True),
            StructField("company", StringType(), True),
            StructField("title", StringType(), True),
            StructField("description", StringType(), True),
            StructField("should_quarantine", BooleanType(), True)
        ])
        df = spark.createDataFrame(data, schema)
        
        # Flag if NULL OR empty string
        df_flagged = df.withColumn(
            "is_quarantined",
            F.when(
                (F.col("company").isNull() | (F.trim(F.col("company")) == "")) |
                (F.col("title").isNull() | (F.trim(F.col("title")) == "")) |
                (F.col("description").isNull() | (F.trim(F.col("description")) == "")),
                True
            ).otherwise(False)
        )
        
        results = df_flagged.collect()
        
        for row in results:
            assert row.is_quarantined == row.should_quarantine, \
                f"{row.job_id}: Empty strings should trigger quarantine"
    
    def test_invalid_date_quarantine(self, spark):
        """Jobs with invalid dates should be quarantined"""
        future_date = datetime.now() + timedelta(days=365)
        past_date = datetime(2000, 1, 1)
        valid_date = datetime(2026, 6, 1)
        
        data = [
            ("job_001", valid_date, False),    # Valid
            ("job_002", future_date, True),    # Future date (invalid)
            ("job_003", past_date, True),      # Too old (>1 year)
        ]
        
        schema = StructType([
            StructField("job_id", StringType(), True),
            StructField("posted_at", TimestampType(), True),
            StructField("should_quarantine", BooleanType(), True)
        ])
        df = spark.createDataFrame(data, schema)
        
        current_date = datetime(2026, 6, 7)
        min_valid_date = datetime(2025, 6, 7)  # 1 year ago
        
        # Flag if posted_at is in future OR too old
        df_flagged = df.withColumn(
            "is_quarantined",
            F.when(
                (F.col("posted_at") > F.lit(current_date)) |
                (F.col("posted_at") < F.lit(min_valid_date)),
                True
            ).otherwise(False)
        )
        
        results = df_flagged.collect()
        
        for row in results:
            assert row.is_quarantined == row.should_quarantine, \
                f"{row.job_id}: Invalid date should trigger quarantine"
    
    def test_suspicious_content_patterns(self, spark):
        """Jobs with suspicious content should be quarantined"""
        data = [
            ("job_001", "Software Developer", "Great opportunity", False),          # Valid
            ("job_002", "Easy money!!!", "Click here now!!!", True),                # Spam
            ("job_003", "Win $1000", "Amazing opportunity $$$", True),              # Spam
            ("job_004", "Developer", "a" * 10000, True),                            # Too long
        ]
        
        schema = StructType([
            StructField("job_id", StringType(), True),
            StructField("title", StringType(), True),
            StructField("description", StringType(), True),
            StructField("should_quarantine", BooleanType(), True)
        ])
        df = spark.createDataFrame(data, schema)
        
        # Flag spam patterns
        df_flagged = df.withColumn(
            "is_quarantined",
            F.when(
                # Excessive exclamation marks
                (F.length(F.regexp_replace(F.col("title"), "[^!]", "")) > 2) |
                (F.length(F.regexp_replace(F.col("description"), "[^!]", "")) > 5) |
                # Excessive dollar signs
                (F.length(F.regexp_replace(F.col("description"), "[^$]", "")) > 3) |
                # Description too long
                (F.length(F.col("description")) > 5000),
                True
            ).otherwise(False)
        )
        
        results = df_flagged.collect()
        
        for row in results:
            assert row.is_quarantined == row.should_quarantine, \
                f"{row.job_id}: Suspicious content should trigger quarantine"


class TestQuarantineCategories:
    """Test quarantine categorization by failure type"""
    
    def test_categorize_by_failure_reason(self, spark):
        """Quarantined jobs should be categorized by failure reason"""
        data = [
            ("job_001", None, "Dev", "Desc", "MISSING_REQUIRED_FIELD"),
            ("job_002", "Acme", "Dev", "Spam!!!", "SUSPICIOUS_CONTENT"),
            ("job_003", "Acme", "Dev", "Desc", None),  # Valid - no quarantine
        ]
        
        schema = StructType([
            StructField("job_id", StringType(), True),
            StructField("company", StringType(), True),
            StructField("title", StringType(), True),
            StructField("description", StringType(), True),
            StructField("expected_reason", StringType(), True)
        ])
        df = spark.createDataFrame(data, schema)
        
        # Determine quarantine reason
        df_categorized = df.withColumn(
            "quarantine_reason",
            F.when(F.col("company").isNull(), "MISSING_REQUIRED_FIELD")
            .when(F.col("description").contains("!!!"), "SUSPICIOUS_CONTENT")
            .otherwise(None)
        )
        
        results = df_categorized.collect()
        
        for row in results:
            assert row.quarantine_reason == row.expected_reason, \
                f"{row.job_id}: Expected reason {row.expected_reason}, got {row.quarantine_reason}"
    
    def test_multiple_failures_priority(self, spark):
        """When multiple rules fail, use priority to determine primary reason"""
        data = [
            ("job_001", None, "Spam!!!", "Both missing company and spam title"),
        ]
        
        schema = StructType([
            StructField("job_id", StringType(), True),
            StructField("company", StringType(), True),
            StructField("title", StringType(), True),
            StructField("description", StringType(), True)
        ])
        df = spark.createDataFrame(data, schema)
        
        # Priority: MISSING_REQUIRED_FIELD > SUSPICIOUS_CONTENT
        df_categorized = df.withColumn(
            "quarantine_reason",
            F.when(F.col("company").isNull(), "MISSING_REQUIRED_FIELD")  # Priority 1
            .when(F.col("title").contains("!!!"), "SUSPICIOUS_CONTENT")   # Priority 2
            .otherwise(None)
        )
        
        result = df_categorized.collect()[0]
        
        assert result.quarantine_reason == "MISSING_REQUIRED_FIELD", \
            "Higher priority rule should take precedence"


class TestQuarantineActions:
    """Test quarantine management actions"""
    
    def test_quarantine_job_sets_flags(self, spark):
        """Quarantining a job should set appropriate flags"""
        data = [
            ("job_001", "Acme", "Dev", "Desc", False, None, None),
        ]
        
        schema = StructType([
            StructField("job_id", StringType(), True),
            StructField("company", StringType(), True),
            StructField("title", StringType(), True),
            StructField("description", StringType(), True),
            StructField("is_quarantined", BooleanType(), True),
            StructField("quarantine_reason", StringType(), True),
            StructField("quarantined_at", TimestampType(), True)
        ])
        df = spark.createDataFrame(data, schema)
        
        # Simulate quarantine action
        current_time = datetime(2026, 6, 7, 10, 0, 0)
        
        df_quarantined = df.withColumn("is_quarantined", F.lit(True)) \
            .withColumn("quarantine_reason", F.lit("MISSING_REQUIRED_FIELD")) \
            .withColumn("quarantined_at", F.lit(current_time))
        
        result = df_quarantined.collect()[0]
        
        assert result.is_quarantined == True
        assert result.quarantine_reason == "MISSING_REQUIRED_FIELD"
        assert result.quarantined_at == current_time
    
    def test_release_from_quarantine(self, spark):
        """Releasing a job from quarantine should clear flags"""
        data = [
            ("job_001", True, "MISSING_REQUIRED_FIELD", datetime(2026, 6, 7)),
        ]
        
        schema = StructType([
            StructField("job_id", StringType(), True),
            StructField("is_quarantined", BooleanType(), True),
            StructField("quarantine_reason", StringType(), True),
            StructField("quarantined_at", TimestampType(), True)
        ])
        df = spark.createDataFrame(data, schema)
        
        # Release from quarantine
        df_released = df.withColumn("is_quarantined", F.lit(False)) \
            .withColumn("quarantine_reason", F.lit(None)) \
            .withColumn("released_at", F.lit(datetime(2026, 6, 8)))
        
        result = df_released.collect()[0]
        
        assert result.is_quarantined == False
        assert result.quarantine_reason is None
        assert result.released_at == datetime(2026, 6, 8)
    
    def test_quarantine_retry_after_fix(self, spark):
        """Fixed jobs should be retried and released if valid"""
        data = [
            ("job_001", None, "Developer", True, "MISSING_REQUIRED_FIELD"),  # Original: missing company
        ]
        
        schema = StructType([
            StructField("job_id", StringType(), True),
            StructField("company", StringType(), True),
            StructField("title", StringType(), True),
            StructField("is_quarantined", BooleanType(), True),
            StructField("quarantine_reason", StringType(), True)
        ])
        df_quarantined = spark.createDataFrame(data, schema)
        
        # Simulate fix: company name added
        df_fixed = df_quarantined.withColumn("company", F.lit("Acme Corp"))
        
        # Re-evaluate quarantine rules
        df_reeval = df_fixed.withColumn(
            "still_invalid",
            F.col("company").isNull()
        )
        
        result = df_reeval.collect()[0]
        
        assert result.company == "Acme Corp", "Company should be fixed"
        assert result.still_invalid == False, "Should pass validation after fix"


class TestQuarantineReporting:
    """Test quarantine reporting and metrics"""
    
    def test_count_by_quarantine_reason(self, spark):
        """Count quarantined jobs by reason"""
        data = [
            ("job_001", "MISSING_REQUIRED_FIELD"),
            ("job_002", "MISSING_REQUIRED_FIELD"),
            ("job_003", "SUSPICIOUS_CONTENT"),
            ("job_004", "INVALID_DATE"),
        ]
        
        schema = StructType([
            StructField("job_id", StringType(), True),
            StructField("quarantine_reason", StringType(), True)
        ])
        df = spark.createDataFrame(data, schema)
        
        counts = df.groupBy("quarantine_reason").count().collect()
        
        reason_counts = {row.quarantine_reason: row['count'] for row in counts}
        
        assert reason_counts["MISSING_REQUIRED_FIELD"] == 2
        assert reason_counts["SUSPICIOUS_CONTENT"] == 1
        assert reason_counts["INVALID_DATE"] == 1
    
    def test_quarantine_age_calculation(self, spark):
        """Calculate how long jobs have been in quarantine"""
        current_date = datetime(2026, 6, 7)
        
        data = [
            ("job_001", datetime(2026, 6, 1), 6),   # 6 days old
            ("job_002", datetime(2026, 6, 6), 1),   # 1 day old
            ("job_003", datetime(2026, 5, 1), 37),  # 37 days old
        ]
        
        schema = StructType([
            StructField("job_id", StringType(), True),
            StructField("quarantined_at", TimestampType(), True),
            StructField("expected_age_days", IntegerType(), True)
        ])
        df = spark.createDataFrame(data, schema)
        
        df_with_age = df.withColumn(
            "age_days",
            F.datediff(F.lit(current_date), F.col("quarantined_at"))
        )
        
        results = df_with_age.collect()
        
        for row in results:
            assert row.age_days == row.expected_age_days, \
                f"{row.job_id}: Expected age {row.expected_age_days}, got {row.age_days}"
    
    def test_quarantine_retention_policy(self, spark):
        """Old quarantined jobs should be marked for deletion"""
        retention_days = 30
        current_date = datetime(2026, 6, 7)
        
        data = [
            ("job_001", datetime(2026, 6, 1), False),   # 6 days - keep
            ("job_002", datetime(2026, 5, 1), True),    # 37 days - delete
            ("job_003", datetime(2025, 12, 1), True),   # 6 months - delete
        ]
        
        schema = StructType([
            StructField("job_id", StringType(), True),
            StructField("quarantined_at", TimestampType(), True),
            StructField("should_delete", BooleanType(), True)
        ])
        df = spark.createDataFrame(data, schema)
        
        df_with_deletion = df.withColumn(
            "mark_for_deletion",
            F.datediff(F.lit(current_date), F.col("quarantined_at")) > retention_days
        )
        
        results = df_with_deletion.collect()
        
        for row in results:
            assert row.mark_for_deletion == row.should_delete, \
                f"{row.job_id}: Deletion policy mismatch"


class TestQuarantineWorkflow:
    """Test complete quarantine workflow"""
    
    def test_ingestion_to_quarantine_flow(self, spark):
        """End-to-end: ingest -> validate -> quarantine if invalid"""
        # Simulated ingestion batch
        raw_data = [
            ("job_001", "Acme Corp", "Developer", "Great job"),      # Valid
            ("job_002", None, "Developer", "Missing company"),       # Invalid
            ("job_003", "TechCo", "Spam!!!", "Click now!!!"),        # Invalid
        ]
        
        schema = StructType([
            StructField("job_id", StringType(), True),
            StructField("company", StringType(), True),
            StructField("title", StringType(), True),
            StructField("description", StringType(), True)
        ])
        df_raw = spark.createDataFrame(raw_data, schema)
        
        # Validate and route
        df_validated = df_raw.withColumn(
            "is_valid",
            F.when(
                F.col("company").isNull() |
                F.col("title").contains("!!!") |
                F.col("description").contains("!!!"),
                False
            ).otherwise(True)
        )
        
        # Split into valid and quarantine
        valid_df = df_validated.filter(F.col("is_valid") == True)
        quarantine_df = df_validated.filter(F.col("is_valid") == False)
        
        assert valid_df.count() == 1, "Should have 1 valid job"
        assert quarantine_df.count() == 2, "Should have 2 quarantined jobs"
        
        valid_ids = [row.job_id for row in valid_df.collect()]
        quarantine_ids = [row.job_id for row in quarantine_df.collect()]
        
        assert "job_001" in valid_ids
        assert "job_002" in quarantine_ids
        assert "job_003" in quarantine_ids
    
    def test_review_and_release_workflow(self, spark):
        """Workflow: manual review -> fix -> release"""
        # Quarantined job
        data = [
            ("job_001", None, "Developer", True, "MISSING_REQUIRED_FIELD", 
             "pending_review"),
        ]
        
        schema = StructType([
            StructField("job_id", StringType(), True),
            StructField("company", StringType(), True),
            StructField("title", StringType(), True),
            StructField("is_quarantined", BooleanType(), True),
            StructField("quarantine_reason", StringType(), True),
            StructField("review_status", StringType(), True)
        ])
        df_quarantine = spark.createDataFrame(data, schema)
        
        # Step 1: Mark as under review
        df_reviewing = df_quarantine.withColumn("review_status", F.lit("under_review"))
        
        # Step 2: Fix applied (company added)
        df_fixed = df_reviewing.withColumn("company", F.lit("Acme Corp"))
        
        # Step 3: Re-validate
        df_revalidated = df_fixed.withColumn(
            "is_now_valid",
            F.col("company").isNotNull()
        )
        
        # Step 4: Release if valid
        df_final = df_revalidated.withColumn(
            "is_quarantined",
            F.when(F.col("is_now_valid"), False).otherwise(True)
        ).withColumn(
            "review_status",
            F.when(F.col("is_now_valid"), "released").otherwise("failed_review")
        )
        
        result = df_final.collect()[0]
        
        assert result.company == "Acme Corp"
        assert result.is_quarantined == False
        assert result.review_status == "released"


class TestQuarantineEdgeCases:
    """Test edge cases"""
    
    def test_already_quarantined_job_revalidation(self, spark):
        """Re-quarantine a job that's already in quarantine (no duplicate)"""
        data = [
            ("job_001", True, "MISSING_REQUIRED_FIELD", datetime(2026, 6, 1)),
        ]
        
        schema = StructType([
            StructField("job_id", StringType(), True),
            StructField("is_quarantined", BooleanType(), True),
            StructField("quarantine_reason", StringType(), True),
            StructField("quarantined_at", TimestampType(), True)
        ])
        df = spark.createDataFrame(data, schema)
        
        # Check if already quarantined before re-quarantine
        df_check = df.withColumn(
            "already_quarantined",
            F.col("is_quarantined") == True
        )
        
        result = df_check.collect()[0]
        
        assert result.already_quarantined == True, \
            "Should detect job is already quarantined"
    
    def test_valid_job_does_not_get_quarantined(self, spark):
        """Ensure valid jobs are NOT quarantined"""
        data = [
            ("job_001", "Acme Corp", "Python Developer", 
             "Looking for experienced Python developer", datetime(2026, 6, 1)),
        ]
        
        schema = StructType([
            StructField("job_id", StringType(), True),
            StructField("company", StringType(), True),
            StructField("title", StringType(), True),
            StructField("description", StringType(), True),
            StructField("posted_at", TimestampType(), True)
        ])
        df = spark.createDataFrame(data, schema)
        
        # Apply all quarantine rules
        df_evaluated = df.withColumn(
            "should_quarantine",
            F.when(
                F.col("company").isNull() |
                F.col("title").isNull() |
                F.col("description").isNull() |
                F.col("title").contains("!!!") |
                F.col("description").contains("!!!"),
                True
            ).otherwise(False)
        )
        
        result = df_evaluated.collect()[0]
        
        assert result.should_quarantine == False, \
            "Valid job should NOT be quarantined"
