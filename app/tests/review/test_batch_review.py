"""
Tests for batch code review functionality.
"""
import pytest
from pathlib import Path
from app.review.batch_review import BatchReviewer
from app.intake.code_extraction import ExtractedFile

class TestBatchReviewer:
    @pytest.fixture(autouse=True)
    def setup_env(self, monkeypatch):
        """Setup environment variables for testing."""
        monkeypatch.setenv('OPENAI_API_KEY', 'test-key')
        monkeypatch.setenv('ANTHROPIC_API_KEY', 'test-key')
        
    @pytest.fixture
    def sample_files(self):
        """Create a sample batch of files for testing."""
        return [
            ExtractedFile(
                path="src/main.py",
                content="def main():\n    print('hello')",
                language="Python",
                size=30
            ),
            ExtractedFile(
                path="src/utils.py",
                content="def helper():\n    return True",
                language="Python",
                size=28
            ),
            ExtractedFile(
                path="src/app.js",
                content="function init() { console.log('ready'); }",
                language="JavaScript",
                size=40
            )
        ]
        
    def test_batch_initialization(self):
        """Test batch reviewer initialization."""
        reviewer = BatchReviewer()
        assert reviewer.prompt_template is not None
        assert "OBJECTIVE" in reviewer.prompt_template
        assert "METRICS" in reviewer.prompt_template
        
    def test_batch_review(self, sample_files):
        """Test reviewing a batch of files."""
        reviewer = BatchReviewer()
        result = reviewer.review_batch(sample_files)
        
        # Check structure
        assert "batch_analysis" in result
        assert "files_reviewed" in result["batch_analysis"]
        assert len(result["batch_analysis"]["files_reviewed"]) == 3
        
        # Check metrics
        metrics = ["consistency_score", "pattern_quality", "cohesion_rating"]
        for metric in metrics:
            assert metric in result["batch_analysis"]
            assert isinstance(result["batch_analysis"][metric], (int, float))
            assert 0 <= result["batch_analysis"][metric] <= 10
            
        # Check findings
        findings = result["batch_analysis"]["findings"]
        assert "patterns_identified" in findings
        assert "consistency_issues" in findings
        assert "cohesion_concerns" in findings
        
        # Check recommendations
        assert "recommendations" in result
        assert "pattern_improvements" in result["recommendations"]
        assert "consistency_fixes" in result["recommendations"]
        assert "cohesion_enhancements" in result["recommendations"]
        
    def test_empty_batch(self):
        """Test handling empty batch."""
        reviewer = BatchReviewer()
        with pytest.raises(ValueError, match="Empty batch"):
            reviewer.review_batch([])
            
    def test_single_file_batch(self):
        """Test reviewing batch with single file."""
        reviewer = BatchReviewer()
        single_file = ExtractedFile(
            path="test.py",
            content="print('test')",
            language="Python",
            size=12
        )
        
        with pytest.raises(ValueError, match="Batch must contain at least 2 files"):
            reviewer.review_batch([single_file])
            
    def test_mixed_language_analysis(self, sample_files):
        """Test analysis of files with different languages."""
        reviewer = BatchReviewer()
        result = reviewer.review_batch(sample_files)
        
        # Should identify language mixing in patterns
        patterns = result["batch_analysis"]["findings"]["patterns_identified"]
        assert any("mixed language" in pattern.lower() for pattern in patterns)
        
    def test_consistency_across_files(self):
        """Test consistency analysis across similar files."""
        files = [
            ExtractedFile(
                path="test1.py",
                content="def func1():\n    pass",
                language="Python",
                size=20
            ),
            ExtractedFile(
                path="test2.py",
                content="def func2():\n    return None",
                language="Python",
                size=28
            )
        ]
        
        reviewer = BatchReviewer()
        result = reviewer.review_batch(files)
        
        # Should have high consistency score for similar files
        assert result["batch_analysis"]["consistency_score"] >= 8.0
