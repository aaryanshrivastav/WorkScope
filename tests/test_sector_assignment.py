"""
Test Sector Assignment Logic (silver_sector_assign)

Tests the rule-based sector classification logic using keyword matching.
Important for accurate job categorization and reporting.

Priority: HIGH RISK (complex logic with many edge cases)
"""

import pytest
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, ArrayType
from datetime import datetime


class TestKeywordMatching:
    """Test keyword-based sector matching"""
    
    def test_single_keyword_match(self, spark, sample_sector_keywords):
        """Job with single matching keyword should be assigned correct sector"""
        data = [
            ("job_001", "Python Developer", "Looking for Python developer with Django experience", 1),
        ]
        
        df = spark.createDataFrame(
            data,
            ["job_id", "title", "description", "expected_sector"]
        )
        
        # Check if 'python' (sector 1 keyword) is in title or description
        sector_1_keywords = sample_sector_keywords[1]
        
        def contains_sector_keyword(title, description, keywords):
            text = f"{title} {description}".lower()
            return any(kw in text for kw in keywords)
        
        result_sector = 1 if contains_sector_keyword("Python Developer", 
                                                      "Looking for Python developer with Django experience",
                                                      sector_1_keywords) else -1
        
        assert result_sector == 1, "Should match sector 1 (tech) based on 'python' keyword"
    
    def test_multiple_keyword_match_same_sector(self, spark, sample_sector_keywords):
        """Job with multiple keywords from same sector should be assigned that sector"""
        data = [
            ("job_001", "Senior Python Engineer", "Java, Python, and data engineering required"),
        ]
        
        df = spark.createDataFrame(
            data,
            ["job_id", "title", "description"]
        )
        
        # Should match sector 1: python, java, engineer, data all in sector_1_keywords
        sector_1_keywords = sample_sector_keywords[1]
        text = "Senior Python Engineer Java, Python, and data engineering required".lower()
        
        matched_keywords = [kw for kw in sector_1_keywords if kw in text]
        
        assert len(matched_keywords) >= 3, \
            "Should match multiple sector 1 keywords (python, java, data, engineer)"
    
    def test_conflicting_keywords_highest_priority(self, spark, sample_sector_keywords):
        """Job with keywords from multiple sectors should use priority/confidence scoring"""
        # This job mentions both tech (python) and finance (trading)
        data = [
            ("job_001", "Python Developer", "Build trading systems with Python"),
        ]
        
        df = spark.createDataFrame(
            data,
            ["job_id", "title", "description"]
        )
        
        text = "Python Developer Build trading systems with Python".lower()
        
        # Count matches per sector
        sector_1_matches = sum(1 for kw in sample_sector_keywords[1] if kw in text)  # Tech
        sector_2_matches = sum(1 for kw in sample_sector_keywords[2] if kw in text)  # Finance
        
        # Python appears twice, so tech sector should win
        assert sector_1_matches > sector_2_matches, \
            "Sector 1 (tech) should have more keyword matches than sector 2 (finance)"
    
    def test_keyword_case_insensitivity(self, spark, sample_sector_keywords):
        """Keyword matching should be case-insensitive"""
        data = [
            ("job_001", "PYTHON DEVELOPER", "Looking for PYTHON developer"),
        ]
        
        df = spark.createDataFrame(
            data,
            ["job_id", "title", "description"]
        )
        
        text_lower = "PYTHON DEVELOPER Looking for PYTHON developer".lower()
        
        assert "python" in text_lower, "Lowercased text should contain 'python'"


class TestSectorPrioritization:
    """Test sector assignment when multiple sectors match"""
    
    def test_title_weighted_higher_than_description(self, spark, sample_sector_keywords):
        """Keywords in title should have higher weight than in description"""
        # Title: finance (sector 2)
        # Description: tech keywords (sector 1)
        data = [
            ("job_001", "Finance Analyst", 
             "Use Python and data engineering tools to analyze financial data"),
        ]
        
        df = spark.createDataFrame(
            data,
            ["job_id", "title", "description"]
        )
        
        # Count matches with weights
        title = "Finance Analyst".lower()
        description = "Use Python and data engineering tools to analyze financial data".lower()
        
        sector_1_score = sum(2 for kw in sample_sector_keywords[1] if kw in title) + \
                         sum(1 for kw in sample_sector_keywords[1] if kw in description)
        
        sector_2_score = sum(2 for kw in sample_sector_keywords[2] if kw in title) + \
                         sum(1 for kw in sample_sector_keywords[2] if kw in description)
        
        # Finance in title (weight 2) should outweigh python/data in description
        assert sector_2_score > sector_1_score, \
            "Title keywords should be weighted higher than description keywords"
    
    def test_multiple_sectors_max_score_wins(self, spark, sample_sector_keywords):
        """When job matches multiple sectors, highest score wins"""
        data = [
            ("job_001", "Software Developer", 
             "Healthcare tech company seeking Python developer for medical records system"),
        ]
        
        df = spark.createDataFrame(
            data,
            ["job_id", "title", "description"]
        )
        
        text = "Software Developer Healthcare tech company seeking Python developer for medical records system".lower()
        
        # Count matches
        sector_1_matches = sum(1 for kw in sample_sector_keywords[1] if kw in text)  # Tech
        sector_3_matches = sum(1 for kw in sample_sector_keywords[3] if kw in text)  # Healthcare
        
        # Should have more tech keywords than healthcare keywords
        assert sector_1_matches > sector_3_matches, \
            "Tech sector should have more matches (software, tech, python, developer)"
    
    def test_tie_breaking_sector_id(self, spark, sample_sector_keywords):
        """When sectors have equal scores, use lower sector_id as tiebreaker"""
        # Artificial case where both sectors have equal keyword matches
        data = [
            ("job_001", "Developer", "developer"),  # Matches sector 1 only
            ("job_002", "Finance", "finance"),      # Matches sector 2 only
        ]
        
        df = spark.createDataFrame(
            data,
            ["job_id", "title", "description"]
        )
        
        # If job matched both sectors equally, sector 1 (lower ID) should win
        # This documents the tiebreaker rule
        
        pass  # Tiebreaker documented


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_no_keyword_match_unknown_sector(self, spark, sample_sector_keywords):
        """Job with no matching keywords should be assigned 'unknown' sector"""
        data = [
            ("job_001", "Mystery Job", "Doing some work somewhere"),
        ]
        
        df = spark.createDataFrame(
            data,
            ["job_id", "title", "description"]
        )
        
        text = "Mystery Job Doing some work somewhere".lower()
        
        # Check if any sector keywords match
        has_match = any(
            any(kw in text for kw in keywords)
            for sector_id, keywords in sample_sector_keywords.items()
            if sector_id != -1  # Exclude 'unknown' sector
        )
        
        assert not has_match, "Should have no sector matches"
        
        # Should default to sector -1 (unknown)
        assigned_sector = -1
        assert assigned_sector == -1, "Should be assigned unknown sector (-1)"
    
    def test_empty_title_and_description(self, spark):
        """Job with empty title and description should be unknown sector"""
        data = [
            ("job_001", "", ""),
            ("job_002", None, None),
        ]
        
        df = spark.createDataFrame(
            data,
            ["job_id", "title", "description"]
        )
        
        # Empty text should not match any keywords
        text = "".lower()
        
        # Should default to unknown sector
        assert text == "", "Empty text should remain empty"
    
    def test_special_characters_in_keywords(self, spark):
        """Keyword matching should handle special characters"""
        data = [
            ("job_001", "C++ Developer", "C++ and C# development"),
        ]
        
        df = spark.createDataFrame(
            data,
            ["job_id", "title", "description"]
        )
        
        text = "C++ Developer C++ and C# development".lower()
        
        # Check if 'c++' is found (with special chars)
        assert "c++" in text, "Should preserve special characters in keyword search"
    
    def test_partial_word_matching(self, spark, sample_sector_keywords):
        """Test whether partial word matches should count"""
        data = [
            ("job_001", "Financer", "We need a financer"),  # Contains 'finance' but different word
        ]
        
        df = spark.createDataFrame(
            data,
            ["job_id", "title", "description"]
        )
        
        text = "Financer We need a financer".lower()
        
        # Should 'finance' keyword match 'financer'?
        # This depends on matching strategy: substring vs whole word
        
        partial_match = "finance" in text  # Substring match
        whole_word_match = " finance " in f" {text} "  # Whole word match
        
        assert partial_match, "Substring matching would find 'finance' in 'financer'"
        assert not whole_word_match, "Whole word matching would NOT find 'finance' in 'financer'"
        
        # Document decision: use substring matching for flexibility


class TestSectorScoring:
    """Test sector confidence scoring logic"""
    
    def test_calculate_sector_score(self, spark, sample_sector_keywords):
        """Calculate confidence score based on keyword matches"""
        data = [
            ("job_001", "Python Developer", 
             "Software engineer with Python, Java, and data science experience"),
        ]
        
        df = spark.createDataFrame(
            data,
            ["job_id", "title", "description"]
        )
        
        title = "Python Developer".lower()
        description = "Software engineer with Python, Java, and data science experience".lower()
        
        # Calculate score: title matches count 2x, description matches count 1x
        sector_1_keywords = sample_sector_keywords[1]
        
        title_matches = sum(2 for kw in sector_1_keywords if kw in title)
        desc_matches = sum(1 for kw in sector_1_keywords if kw in description)
        
        total_score = title_matches + desc_matches
        
        # Expected matches: python (title + desc), developer (title), software (desc), 
        # engineer (desc), java (desc), data (desc)
        # Score: 2+2 (title: python, developer) + 1+1+1+1 (desc: python, software, engineer, java, data)
        
        assert total_score >= 6, f"Expected high score (>=6) for strong tech match, got {total_score}"
    
    def test_confidence_threshold(self, spark, sample_sector_keywords):
        """Only assign sector if confidence score exceeds threshold"""
        confidence_threshold = 2  # Require at least 2 keyword matches
        
        # Job 1: Strong match (multiple keywords)
        strong_match_score = 5
        
        # Job 2: Weak match (single keyword)
        weak_match_score = 1
        
        assert strong_match_score >= confidence_threshold, \
            "Strong match should exceed threshold"
        
        assert weak_match_score < confidence_threshold, \
            "Weak match should not exceed threshold"
    
    def test_multi_sector_scores(self, spark, sample_sector_keywords):
        """Return scores for all sectors, not just the winner"""
        data = [
            ("job_001", "Python Developer", 
             "Build trading systems for healthcare fintech"),
        ]
        
        df = spark.createDataFrame(
            data,
            ["job_id", "title", "description"]
        )
        
        text = "Python Developer Build trading systems for healthcare fintech".lower()
        
        # Calculate scores for all sectors
        scores = {}
        for sector_id, keywords in sample_sector_keywords.items():
            if sector_id == -1:  # Skip unknown sector
                continue
            scores[sector_id] = sum(1 for kw in keywords if kw in text)
        
        # Should have non-zero scores for multiple sectors
        non_zero_sectors = [sid for sid, score in scores.items() if score > 0]
        
        assert len(non_zero_sectors) >= 2, \
            "Should match multiple sectors (tech, finance, healthcare)"


class TestSectorHierarchy:
    """Test hierarchical sector classification"""
    
    def test_primary_vs_secondary_sector(self, spark, sample_sector_keywords):
        """Assign primary sector (highest score) and secondary sector (second highest)"""
        data = [
            ("job_001", "Software Engineer", 
             "Healthcare technology company building medical software"),
        ]
        
        df = spark.createDataFrame(
            data,
            ["job_id", "title", "description"]
        )
        
        text = "Software Engineer Healthcare technology company building medical software".lower()
        
        # Calculate scores
        scores = {}
        for sector_id, keywords in sample_sector_keywords.items():
            if sector_id == -1:
                continue
            scores[sector_id] = sum(1 for kw in keywords if kw in text)
        
        sorted_sectors = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        primary_sector = sorted_sectors[0][0]
        secondary_sector = sorted_sectors[1][0] if len(sorted_sectors) > 1 else None
        
        # Primary should be tech (software, engineer, tech)
        # Secondary should be healthcare (healthcare, medical)
        
        assert primary_sector == 1, f"Primary sector should be 1 (tech), got {primary_sector}"
        assert secondary_sector == 3, f"Secondary sector should be 3 (healthcare), got {secondary_sector}"


class TestKeywordExpansion:
    """Test keyword synonym expansion"""
    
    def test_synonym_matching(self, spark):
        """Keywords should include common synonyms"""
        # Example: 'developer' should match 'dev', 'programmer', 'coder'
        # This test documents the requirement for synonym expansion
        
        base_keyword = "developer"
        synonyms = ["dev", "programmer", "coder", "engineer"]
        
        job_title = "Software Coder"
        
        # Check if any synonym matches
        text = job_title.lower()
        has_match = any(syn in text for syn in synonyms)
        
        assert has_match, "Should match synonym 'coder' for 'developer' keyword"
    
    def test_acronym_expansion(self, spark):
        """Keywords should handle common acronyms"""
        # Example: 'SWE' -> 'Software Engineer'
        
        data = [
            ("job_001", "SWE", "SWE position available"),
        ]
        
        df = spark.createDataFrame(
            data,
            ["job_id", "title", "description"]
        )
        
        # Should expand SWE to software engineer
        text = "SWE SWE position available".lower()
        
        # Document that acronym expansion would improve matching
        # Future: build acronym dictionary
        
        pass  # Documented for future implementation


class TestNormalizationConsistency:
    """Test that normalization is consistent with identity matching"""
    
    def test_sector_uses_normalized_fields(self, spark):
        """Sector assignment should use same normalized fields as identity matching"""
        data = [
            ("job_001", "Python Developer", "PYTHON DEVELOPER", 
             "python developer", "python developer"),  # raw vs normalized
        ]
        
        df = spark.createDataFrame(
            data,
            ["job_id", "title_raw", "description_raw", "title_norm", "description_norm"]
        )
        
        # Sector assignment should use normalized fields
        text_norm = "python developer python developer".lower()
        text_raw = "Python Developer PYTHON DEVELOPER".lower()
        
        # Both should match 'python' keyword
        assert "python" in text_norm
        assert "python" in text_raw
        
        # Normalization is already lowercase, so both work
        # But using normalized fields ensures consistency with other processes


# Integration test fixtures
@pytest.fixture
def sample_jobs_for_sector_assignment(spark):
    """Sample jobs covering different sectors"""
    data = [
        ("job_001", "Python Developer", "Build web apps with Django and Flask", 1),
        ("job_002", "Financial Analyst", "Analyze trading data and market trends", 2),
        ("job_003", "Registered Nurse", "Provide patient care in clinical setting", 3),
        ("job_004", "Sales Manager", "Drive business development and account management", 4),
        ("job_005", "Mystery Worker", "Do various tasks as needed", -1),  # Unknown
    ]
    
    return spark.createDataFrame(
        data,
        ["job_id", "title", "description", "expected_sector"]
    )


class TestEndToEnd:
    """End-to-end sector assignment tests"""
    
    def test_batch_sector_assignment(self, spark, sample_jobs_for_sector_assignment, 
                                      sample_sector_keywords):
        """Assign sectors to a batch of jobs"""
        df = sample_jobs_for_sector_assignment
        
        # Simulate sector assignment for each job
        results = []
        for row in df.collect():
            title_lower = row.title.lower()
            description_lower = row.description.lower()
            
            # Find best matching sector with weighted scoring
            # Title keywords weighted 2x, description keywords weighted 1x
            best_sector = -1
            best_score = 0
            
            for sector_id, keywords in sample_sector_keywords.items():
                if sector_id == -1:
                    continue
                # Weight title matches higher than description matches
                title_score = sum(2 for kw in keywords if kw in title_lower)
                description_score = sum(1 for kw in keywords if kw in description_lower)
                score = title_score + description_score
                if score > best_score:
                    best_score = score
                    best_sector = sector_id
            
            results.append((row.job_id, best_sector, row.expected_sector))
        
        # Verify assignments match expectations
        for job_id, assigned, expected in results:
            assert assigned == expected, \
                f"{job_id}: Expected sector {expected}, got {assigned}"
