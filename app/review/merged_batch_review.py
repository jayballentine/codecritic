"""
Module for merging and analyzing multiple batch reviews.
"""
from pathlib import Path
import json
from typing import List, Dict, Any
from app.models.model_manager import ModelManager
from app.review.numerical_calculations import NumericalProcessor, ReviewMetrics

class MergedBatchReviewer:
    """Handles merging and analysis of multiple batch reviews."""
    
    def __init__(self):
        """Initialize the merged batch reviewer."""
        config_path = str(Path("app/models/config/model_config.yml"))
        self.model_manager = ModelManager(config_path)
        self.prompt_template = self._load_prompt_template()
        
    def _load_prompt_template(self) -> str:
        """
        Load the merged batch review prompt template.
        
        Returns:
            str: Content of the merged batch review prompt template
        """
        prompt_path = Path("app/prompts/merged_batch_review.txt")
        with open(prompt_path, 'r') as f:
            return f.read()
            
    def merge_reviews(self, batch_reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge multiple batch reviews into a comprehensive analysis.
        
        Args:
            batch_reviews: List of batch review results to merge
            
        Returns:
            dict: Merged review results following the format specified in the prompt
            
        Raises:
            ValueError: If no reviews provided or only one batch review
        """
        if not batch_reviews:
            raise ValueError("No batch reviews provided")
        if len(batch_reviews) < 2:
            raise ValueError("At least two batch reviews required")
            
        # Calculate aggregate metrics
        metrics = NumericalProcessor.calculate_batch_averages(batch_reviews)
        
        # Prepare prompt with batch reviews
        prompt = self._prepare_merged_prompt(batch_reviews, metrics)
        
        # Get merged analysis from model
        try:
            review_result = self.model_manager.generate_review(prompt)
            parsed_result = json.loads(review_result)
            
            # Validate review format
            self._validate_review_format(parsed_result)
            
            return parsed_result
            
        except json.JSONDecodeError:
            raise ValueError("Invalid review format received from model")
            
    def _prepare_merged_prompt(self, batch_reviews: List[Dict[str, Any]], metrics: ReviewMetrics) -> str:
        """
        Prepare the review prompt for merged analysis.
        
        Args:
            batch_reviews: List of batch reviews to analyze
            metrics: Aggregated metrics across all reviews
            
        Returns:
            str: Formatted prompt for the model
        """
        reviews_summary = "\n\n".join([
            f"Batch {i+1}:\n"
            f"Files: {len(review.get('batch_analysis', {}).get('files_reviewed', []))}\n"
            f"Consistency Score: {review.get('batch_analysis', {}).get('consistency_score')}\n"
            f"Pattern Quality: {review.get('batch_analysis', {}).get('pattern_quality')}\n"
            f"Cohesion Rating: {review.get('batch_analysis', {}).get('cohesion_rating')}\n"
            f"Findings: {json.dumps(review.get('batch_analysis', {}).get('findings', {}), indent=2)}"
            for i, review in enumerate(batch_reviews)
        ])
        
        metrics_summary = (
            f"Aggregate Metrics:\n"
            f"Readability: {metrics.readability:.2f}\n"
            f"Maintainability: {metrics.maintainability:.2f}\n"
            f"Complexity: {metrics.complexity:.2f}\n"
            f"Coding Standards: {metrics.coding_standards:.2f}\n"
            f"Documentation: {metrics.documentation:.2f}\n"
            f"Security: {metrics.security:.2f}\n"
            f"Performance: {metrics.performance:.2f}\n"
            f"Reusability: {metrics.reusability:.2f}\n"
            f"Error Handling: {metrics.error_handling:.2f}\n"
            f"Test Coverage: {metrics.test_coverage:.2f}"
        )
        
        return f"""
{self.prompt_template}

BATCH REVIEWS TO MERGE:
{reviews_summary}

AGGREGATE METRICS:
{metrics_summary}
"""
        
    def _validate_review_format(self, review: Dict[str, Any]):
        """
        Validate that the review follows the expected format.
        
        Args:
            review: Review dictionary to validate
            
        Raises:
            ValueError: If review format is invalid
        """
        # Check top-level structure
        required_keys = {"merged_analysis", "recommendations"}
        if not all(key in review for key in required_keys):
            raise ValueError("Invalid review format: missing required sections")
            
        # Check merged analysis
        analysis = review["merged_analysis"]
        required_analysis = {
            "overall_quality_score",
            "architectural_alignment_score",
            "integration_impact_score",
            "key_findings"
        }
        if not all(key in analysis for key in required_analysis):
            raise ValueError("Invalid review format: missing analysis metrics")
            
        # Check findings
        findings = analysis["key_findings"]
        required_findings = {"strengths", "concerns", "risks"}
        if not all(key in findings for key in required_findings):
            raise ValueError("Invalid review format: missing findings sections")
            
        # Check recommendations
        recommendations = review["recommendations"]
        required_recommendations = {
            "architectural_improvements",
            "integration_considerations",
            "priority_actions"
        }
        if not all(key in recommendations for key in required_recommendations):
            raise ValueError("Invalid review format: missing recommendations")
