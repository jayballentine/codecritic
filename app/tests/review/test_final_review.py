"""
Tests for final review functionality.
"""
import pytest
from pathlib import Path
from app.review.final_review import FinalReviewer
from app.review.merged_batch_review import MergedBatchReviewer
from app.review.batch_review import BatchReviewer
from app.intake.code_extraction import ExtractedFile

class TestFinalReviewer:
    @pytest.fixture(autouse=True)
    def setup_env(self, monkeypatch):
        """Setup environment variables for testing."""
        monkeypatch.setenv('OPENAI_API_KEY', 'test-key')
        monkeypatch.setenv('ANTHROPIC_API_KEY', 'test-key')
        
    @pytest.fixture
    def merged_review(self):
        """Create a sample merged review result."""
        reviewer = MergedBatchReviewer()
        batch_reviewer = BatchReviewer()
        
        # Create two batches of files
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
        
        batch_reviews = [
            batch_reviewer.review_batch(batch1),
            batch_reviewer.review_batch(batch2)
        ]
        
        return reviewer.merge_reviews(batch_reviews)
        
    def test_final_review_initialization(self):
        """Test final reviewer initialization."""
        reviewer = FinalReviewer()
        assert reviewer.prompt_template is not None
        assert "OBJECTIVE" in reviewer.prompt_template
        assert "METRICS" in reviewer.prompt_template
        
    def test_generate_final_review(self, merged_review):
        """Test generating final review from merged review."""
        reviewer = FinalReviewer()
        result = reviewer.generate_final_review(merged_review)
        
        # Check structure
        assert "final_assessment" in result
        assessment = result["final_assessment"]
        
        # Check scores
        assert "final_score" in assessment
        assert 0 <= assessment["final_score"] <= 10
        
        # Check quality breakdown
        breakdown = assessment["quality_breakdown"]
        metrics = ["code_quality", "architecture", "maintainability", "scalability"]
        for metric in metrics:
            assert metric in breakdown
            assert 0 <= breakdown[metric] <= 10
            
        # Check recommendations and risks
        assert "recommendations" in assessment
        assert len(assessment["recommendations"]) > 0
        
        risk_analysis = assessment["risk_analysis"]
        assert all(k in risk_analysis for k in ["high_priority", "medium_priority", "low_priority"])
        
        # Check action plan
        assert "action_plan" in result
        plan = result["action_plan"]
        assert all(k in plan for k in ["immediate_actions", "short_term_goals", "long_term_improvements"])
        
    def test_empty_merged_review(self):
        """Test handling empty merged review."""
        reviewer = FinalReviewer()
        with pytest.raises(ValueError, match="Invalid merged review"):
            reviewer.generate_final_review({})
            
    def test_invalid_merged_review(self):
        """Test handling invalid merged review format."""
        reviewer = FinalReviewer()
        invalid_review = {
            "merged_analysis": {
                "overall_quality_score": 8.0
            }
        }
        with pytest.raises(ValueError, match="Invalid merged review format"):
            reviewer.generate_final_review(invalid_review)
            
    def test_business_impact_inclusion(self, merged_review):
        """Test that recommendations include business impact."""
        reviewer = FinalReviewer()
        result = reviewer.generate_final_review(merged_review)
        
        # Check recommendations for business impact
        recommendations = result["final_assessment"]["recommendations"]
        assert any("impact" in str(item).lower() for item in recommendations)
        
    def test_timeline_inclusion(self, merged_review):
        """Test that action plan includes timeline considerations."""
        reviewer = FinalReviewer()
        result = reviewer.generate_final_review(merged_review)
        
        # Verify timeline-based organization
        plan = result["action_plan"]
        assert len(plan["immediate_actions"]) > 0
        assert len(plan["short_term_goals"]) > 0
        assert len(plan["long_term_improvements"]) > 0
