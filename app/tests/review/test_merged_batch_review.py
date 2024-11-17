"""
Tests for merged batch review functionality.
"""
import pytest
from pathlib import Path
from app.review.merged_batch_review import MergedBatchReviewer
from app.review.batch_review import BatchReviewer
from app.intake.code_extraction import ExtractedFile

class TestMergedBatchReviewer:
    @pytest.fixture(autouse=True)
    def setup_env(self, monkeypatch):
        """Setup environment variables for testing."""
        monkeypatch.setenv('OPENAI_API_KEY', 'test-key')
        monkeypatch.setenv('ANTHROPIC_API_KEY', 'test-key')
        
    @pytest.fixture
    def batch_reviews(self):
        """Create sample batch reviews for testing."""
        batch_reviewer = BatchReviewer()
        
        # First batch (Python files)
        batch1 = [
            ExtractedFile(
                path="src/core/main.py",
                content="def main():\n    print('hello')",
                language="Python",
                size=30
            ),
            ExtractedFile(
                path="src/utils/helpers.py",
                content="def helper():\n    return True",
                language="Python",
                size=28
            )
        ]
        
        # Second batch (JavaScript files)
        batch2 = [
            ExtractedFile(
                path="src/frontend/app.js",
                content="function init() { console.log('ready'); }",
                language="JavaScript",
                size=40
            ),
            ExtractedFile(
                path="src/frontend/utils.js",
                content="const helper = () => true;",
                language="JavaScript",
                size=25
            )
        ]
        
        return [
            batch_reviewer.review_batch(batch1),
            batch_reviewer.review_batch(batch2)
        ]
        
    def test_merged_review_initialization(self):
        """Test merged reviewer initialization."""
        reviewer = MergedBatchReviewer()
        assert reviewer.prompt_template is not None
        assert "OBJECTIVE" in reviewer.prompt_template
        assert "METRICS" in reviewer.prompt_template
        
    def test_merge_batch_reviews(self, batch_reviews):
        """Test merging multiple batch reviews."""
        reviewer = MergedBatchReviewer()
        result = reviewer.merge_reviews(batch_reviews)
        
        # Check structure
        assert "merged_analysis" in result
        analysis = result["merged_analysis"]
        
        # Check scores
        assert "overall_quality_score" in analysis
        assert "architectural_alignment_score" in analysis
        assert "integration_impact_score" in analysis
        assert all(0 <= analysis[k] <= 10 for k in analysis if k.endswith('_score'))
        
        # Check findings
        assert "key_findings" in analysis
        findings = analysis["key_findings"]
        assert all(k in findings for k in ["strengths", "concerns", "risks"])
        assert all(isinstance(findings[k], list) for k in findings)
        
        # Check recommendations
        assert "recommendations" in result
        recommendations = result["recommendations"]
        assert "architectural_improvements" in recommendations
        assert "integration_considerations" in recommendations
        assert "priority_actions" in recommendations
        
    def test_empty_reviews(self):
        """Test handling empty review list."""
        reviewer = MergedBatchReviewer()
        with pytest.raises(ValueError, match="No batch reviews provided"):
            reviewer.merge_reviews([])
            
    def test_single_batch_review(self, batch_reviews):
        """Test merging single batch review."""
        reviewer = MergedBatchReviewer()
        with pytest.raises(ValueError, match="At least two batch reviews required"):
            reviewer.merge_reviews([batch_reviews[0]])
            
    def test_cross_language_analysis(self, batch_reviews):
        """Test analysis across different language batches."""
        reviewer = MergedBatchReviewer()
        result = reviewer.merge_reviews(batch_reviews)
        
        # Should identify cross-language patterns
        findings = result["merged_analysis"]["key_findings"]
        assert any("language" in str(item).lower() for items in findings.values() for item in items)
        
    def test_architectural_insights(self, batch_reviews):
        """Test architectural analysis in merged review."""
        reviewer = MergedBatchReviewer()
        result = reviewer.merge_reviews(batch_reviews)
        
        # Should provide architectural insights
        improvements = result["recommendations"]["architectural_improvements"]
        assert len(improvements) > 0
        assert any("architecture" in str(item).lower() for item in improvements)
