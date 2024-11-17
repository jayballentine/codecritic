"""
Tests for individual file review functionality.
"""
import os
import pytest
from pathlib import Path
from app.review.individual_file_review import FileReviewer
from app.intake.code_extraction import ExtractedFile

class TestFileReviewer:
    @pytest.fixture(autouse=True)
    def setup_env(self, monkeypatch):
        """Setup environment variables for testing."""
        monkeypatch.setenv('OPENAI_API_KEY', 'test-key')
        monkeypatch.setenv('ANTHROPIC_API_KEY', 'test-key')
        
    @pytest.fixture
    def sample_python_file(self):
        """Create a sample Python file for testing."""
        return ExtractedFile(
            path="test.py",
            content="def hello():\n    return 'world'",
            language="Python",
            size=28
        )
        
    @pytest.fixture
    def sample_js_file(self):
        """Create a sample JavaScript file for testing."""
        return ExtractedFile(
            path="app.js",
            content="function add(a,b) { return a + b; }",
            language="JavaScript",
            size=35
        )
        
    def test_review_initialization(self):
        """Test reviewer initialization with prompt template."""
        reviewer = FileReviewer()
        assert reviewer.prompt_template is not None
        assert "OBJECTIVE" in reviewer.prompt_template
        assert "METRICS" in reviewer.prompt_template
        
    def test_review_python_file(self, sample_python_file):
        """Test reviewing a Python file."""
        reviewer = FileReviewer()
        result = reviewer.review_file(sample_python_file)
        
        # Check structure
        assert "file_scores" in result
        assert sample_python_file.path in result["file_scores"]
        scores = result["file_scores"][sample_python_file.path]
        
        # Check all required metrics exist
        required_metrics = [
            "readability", "maintainability", "complexity",
            "coding_standards", "documentation", "security",
            "performance", "reusability", "error_handling",
            "test_coverage"
        ]
        for metric in required_metrics:
            assert metric in scores
            assert isinstance(scores[metric], (int, float))
            assert 0 <= scores[metric] <= 10  # Scores should be 0-10
            
        # Check qualitative feedback
        assert "notes" in scores
        assert isinstance(scores["notes"], str)
        assert len(scores["notes"]) > 0
        
        # Check overall review
        assert "overall_review" in result
        assert "total_score" in result["overall_review"]
        assert "strengths" in result["overall_review"]
        assert "concerns" in result["overall_review"]
        assert "hiring_confidence" in result["overall_review"]
        assert "risks" in result["overall_review"]
        assert "summary" in result["overall_review"]
        
    def test_review_js_file(self, sample_js_file):
        """Test reviewing a JavaScript file."""
        reviewer = FileReviewer()
        result = reviewer.review_file(sample_js_file)
        
        assert "file_scores" in result
        assert sample_js_file.path in result["file_scores"]
        
    def test_invalid_file(self):
        """Test reviewing an invalid file."""
        reviewer = FileReviewer()
        invalid_file = ExtractedFile(
            path="test.xyz",
            content="invalid content",
            language="Unknown",
            size=14
        )
        
        with pytest.raises(ValueError, match="Unsupported file type"):
            reviewer.review_file(invalid_file)
            
    def test_empty_file(self):
        """Test reviewing an empty file."""
        reviewer = FileReviewer()
        empty_file = ExtractedFile(
            path="empty.py",
            content="",
            language="Python",
            size=0
        )
        
        with pytest.raises(ValueError, match="Empty file"):
            reviewer.review_file(empty_file)
            
    def test_review_consistency(self, sample_python_file):
        """Test that reviews are consistent for the same file."""
        reviewer = FileReviewer()
        result1 = reviewer.review_file(sample_python_file)
        result2 = reviewer.review_file(sample_python_file)
        
        # Same file should get similar scores (within reasonable margin)
        scores1 = result1["file_scores"][sample_python_file.path]
        scores2 = result2["file_scores"][sample_python_file.path]
        
        for metric in scores1:
            if isinstance(scores1[metric], (int, float)):
                assert abs(scores1[metric] - scores2[metric]) <= 2  # Allow small variance
