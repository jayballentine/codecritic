"""
Module for handling batch code reviews of multiple files.
"""
from pathlib import Path
import json
from typing import List, Dict, Any
from app.intake.code_extraction import ExtractedFile
from app.models.model_manager import ModelManager

class BatchReviewer:
    """Handles batch code reviews across multiple files."""
    
    def __init__(self):
        """Initialize the batch reviewer with necessary components."""
        config_path = str(Path("app/models/config/model_config.yml"))
        self.model_manager = ModelManager(config_path)
        self.prompt_template = self._load_prompt_template()
        
    def _load_prompt_template(self) -> str:
        """
        Load the batch review prompt template.
        
        Returns:
            str: Content of the batch review prompt template
        """
        prompt_path = Path("app/prompts/batch_review.txt")
        with open(prompt_path, 'r') as f:
            return f.read()
            
    def review_batch(self, files: List[ExtractedFile]) -> Dict[str, Any]:
        """
        Review multiple files as a batch and analyze patterns.
        
        Args:
            files: List of ExtractedFile objects to review
            
        Returns:
            dict: Batch review results following the format specified in the prompt
            
        Raises:
            ValueError: If batch is empty or contains only one file
        """
        if not files:
            raise ValueError("Empty batch")
        if len(files) < 2:
            raise ValueError("Batch must contain at least 2 files")
            
        # Prepare prompt with all file contents
        prompt = self._prepare_batch_prompt(files)
        
        # Get review from model
        try:
            review_result = self.model_manager.generate_review(prompt)
            parsed_result = json.loads(review_result)
            
            # Validate review format
            self._validate_review_format(parsed_result, files)
            
            return parsed_result
            
        except json.JSONDecodeError:
            raise ValueError("Invalid review format received from model")
            
    def _prepare_batch_prompt(self, files: List[ExtractedFile]) -> str:
        """
        Prepare the review prompt for a batch of files.
        
        Args:
            files: List of ExtractedFile objects to review
            
        Returns:
            str: Formatted prompt for the model
        """
        files_content = "\n\n".join([
            f"File: {file.path}\n"
            f"Language: {file.language}\n"
            f"Size: {file.size} bytes\n"
            f"Content:\n{file.content}"
            for file in files
        ])
        
        return f"""
{self.prompt_template}

FILES TO REVIEW:
{files_content}
"""
        
    def _validate_review_format(self, review: Dict[str, Any], files: List[ExtractedFile]):
        """
        Validate that the review follows the expected format.
        
        Args:
            review: Review dictionary to validate
            files: List of files that were reviewed
            
        Raises:
            ValueError: If review format is invalid
        """
        # Check top-level structure
        required_keys = {"batch_analysis", "recommendations"}
        if not all(key in review for key in required_keys):
            raise ValueError("Invalid review format: missing required sections")
            
        # Check batch analysis
        analysis = review["batch_analysis"]
        required_analysis = {
            "files_reviewed", "consistency_score", "pattern_quality",
            "cohesion_rating", "findings"
        }
        if not all(key in analysis for key in required_analysis):
            raise ValueError("Invalid review format: missing analysis metrics")
            
        # Check findings
        findings = analysis["findings"]
        required_findings = {
            "patterns_identified", "consistency_issues", "cohesion_concerns"
        }
        if not all(key in findings for key in required_findings):
            raise ValueError("Invalid review format: missing findings sections")
            
        # Check recommendations
        recommendations = review["recommendations"]
        required_recommendations = {
            "pattern_improvements", "consistency_fixes", "cohesion_enhancements"
        }
        if not all(key in recommendations for key in required_recommendations):
            raise ValueError("Invalid review format: missing recommendations")
            
        # Validate file list
        if len(analysis["files_reviewed"]) != len(files):
            raise ValueError("Invalid review format: file count mismatch")
