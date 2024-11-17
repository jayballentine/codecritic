"""
Module for generating final comprehensive code reviews.
"""
from pathlib import Path
import json
from typing import Dict, Any
from app.models.model_manager import ModelManager

class FinalReviewer:
    """Handles generation of final comprehensive reviews."""
    
    def __init__(self):
        """Initialize the final reviewer."""
        config_path = str(Path("app/models/config/model_config.yml"))
        self.model_manager = ModelManager(config_path)
        self.prompt_template = self._load_prompt_template()
        
    def _load_prompt_template(self) -> str:
        """
        Load the final review prompt template.
        
        Returns:
            str: Content of the final review prompt template
        """
        prompt_path = Path("app/prompts/final_review.txt")
        with open(prompt_path, 'r') as f:
            return f.read()
            
    def generate_final_review(self, merged_review: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate final review from merged review results.
        
        Args:
            merged_review: Results from merged batch review
            
        Returns:
            dict: Final review results following the format specified in the prompt
            
        Raises:
            ValueError: If merged review is invalid
        """
        if not merged_review:
            raise ValueError("Invalid merged review")
            
        # Validate merged review format
        self._validate_merged_review(merged_review)
        
        # Prepare prompt with merged review data
        prompt = self._prepare_final_prompt(merged_review)
        
        # Get final review from model
        try:
            review_result = self.model_manager.generate_review(prompt)
            parsed_result = json.loads(review_result)
            
            # Validate review format
            self._validate_review_format(parsed_result)
            
            return parsed_result
            
        except json.JSONDecodeError:
            raise ValueError("Invalid review format received from model")
            
    def _prepare_final_prompt(self, merged_review: Dict[str, Any]) -> str:
        """
        Prepare the review prompt for final analysis.
        
        Args:
            merged_review: Merged review results to analyze
            
        Returns:
            str: Formatted prompt for the model
        """
        analysis = merged_review["merged_analysis"]
        findings = analysis["key_findings"]
        recommendations = merged_review["recommendations"]
        
        review_summary = (
            f"Overall Quality Score: {analysis['overall_quality_score']}\n"
            f"Architectural Alignment: {analysis['architectural_alignment_score']}\n"
            f"Integration Impact: {analysis['integration_impact_score']}\n\n"
            f"Key Findings:\n"
            f"Strengths:\n{json.dumps(findings['strengths'], indent=2)}\n"
            f"Concerns:\n{json.dumps(findings['concerns'], indent=2)}\n"
            f"Risks:\n{json.dumps(findings['risks'], indent=2)}\n\n"
            f"Recommendations:\n"
            f"Architectural: {json.dumps(recommendations['architectural_improvements'], indent=2)}\n"
            f"Integration: {json.dumps(recommendations['integration_considerations'], indent=2)}\n"
            f"Priority: {json.dumps(recommendations['priority_actions'], indent=2)}"
        )
        
        return f"""
{self.prompt_template}

MERGED REVIEW TO ANALYZE:
{review_summary}
"""
        
    def _validate_merged_review(self, review: Dict[str, Any]):
        """
        Validate that the merged review follows the expected format.
        
        Args:
            review: Merged review dictionary to validate
            
        Raises:
            ValueError: If review format is invalid
        """
        if "merged_analysis" not in review:
            raise ValueError("Invalid merged review format: missing merged_analysis")
            
        analysis = review["merged_analysis"]
        required_fields = {
            "overall_quality_score",
            "architectural_alignment_score",
            "integration_impact_score",
            "key_findings"
        }
        
        if not all(field in analysis for field in required_fields):
            raise ValueError("Invalid merged review format: missing required fields")
            
    def _validate_review_format(self, review: Dict[str, Any]):
        """
        Validate that the review follows the expected format.
        
        Args:
            review: Review dictionary to validate
            
        Raises:
            ValueError: If review format is invalid
        """
        # Check top-level structure
        required_keys = {"final_assessment", "action_plan", "summary"}
        if not all(key in review for key in required_keys):
            raise ValueError("Invalid review format: missing required sections")
            
        # Check final assessment
        assessment = review["final_assessment"]
        required_assessment = {
            "final_score",
            "quality_breakdown",
            "recommendations",
            "risk_analysis"
        }
        if not all(key in assessment for key in required_assessment):
            raise ValueError("Invalid review format: missing assessment sections")
            
        # Check quality breakdown
        breakdown = assessment["quality_breakdown"]
        required_metrics = {
            "code_quality",
            "architecture",
            "maintainability",
            "scalability"
        }
        if not all(metric in breakdown for metric in required_metrics):
            raise ValueError("Invalid review format: missing quality metrics")
            
        # Check risk analysis
        risks = assessment["risk_analysis"]
        required_risks = {
            "high_priority",
            "medium_priority",
            "low_priority"
        }
        if not all(level in risks for level in required_risks):
            raise ValueError("Invalid review format: missing risk levels")
            
        # Check action plan
        plan = review["action_plan"]
        required_plan = {
            "immediate_actions",
            "short_term_goals",
            "long_term_improvements"
        }
        if not all(key in plan for key in required_plan):
            raise ValueError("Invalid review format: missing action plan sections")
