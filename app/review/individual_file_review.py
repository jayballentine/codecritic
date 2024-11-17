"""
Module for handling individual file code reviews.
"""
from pathlib import Path
import json
from typing import Dict, Any
from app.intake.code_extraction import ExtractedFile
from app.models.model_manager import ModelManager

class FileReviewer:
    """Handles individual file code reviews."""
    
    def __init__(self):
        """Initialize the file reviewer with necessary components."""
        config_path = str(Path("app/models/config/model_config.yml"))
        self.model_manager = ModelManager(config_path)
        self.prompt_template = self._load_prompt_template()
        self.supported_languages = {
            'Python', 'JavaScript', 'TypeScript', 'Java', 'C++', 'C',
            'C#', 'Ruby', 'PHP', 'Go', 'Rust', 'Swift', 'Kotlin',
            'Scala', 'HTML', 'CSS', 'SQL', 'Shell', 'YAML', 'JSON',
            'XML', 'Markdown'
        }
        
    def _load_prompt_template(self) -> str:
        """
        Load the initial review prompt template.
        
        Returns:
            str: Content of the initial review prompt template
        """
        prompt_path = Path("app/prompts/initial_review.txt")
        with open(prompt_path, 'r') as f:
            return f.read()
            
    def review_file(self, file: ExtractedFile) -> Dict[str, Any]:
        """
        Review an individual file and provide detailed analysis.
        
        Args:
            file: ExtractedFile object containing the code to review
            
        Returns:
            dict: Review results following the format specified in the prompt
            
        Raises:
            ValueError: If file is invalid or empty
        """
        # Validate file
        if file.language not in self.supported_languages:
            raise ValueError(f"Unsupported file type: {file.language}")
        if not file.content.strip():
            raise ValueError("Empty file")
            
        # Prepare prompt with file content
        prompt = self._prepare_review_prompt(file)
        
        # Get review from model
        try:
            review_result = self.model_manager.generate_review(prompt)
            parsed_result = json.loads(review_result)
            
            # Validate review format
            self._validate_review_format(parsed_result, file.path)
            
            return parsed_result
            
        except json.JSONDecodeError:
            raise ValueError("Invalid review format received from model")
            
    def _prepare_review_prompt(self, file: ExtractedFile) -> str:
        """
        Prepare the review prompt for a specific file.
        
        Args:
            file: ExtractedFile object to review
            
        Returns:
            str: Formatted prompt for the model
        """
        return f"""
{self.prompt_template}

FILE TO REVIEW:
Path: {file.path}
Language: {file.language}
Size: {file.size} bytes

CODE:
{file.content}
"""
        
    def _validate_review_format(self, review: Dict[str, Any], file_path: str):
        """
        Validate that the review follows the expected format.
        
        Args:
            review: Review dictionary to validate
            file_path: Path of the reviewed file
            
        Raises:
            ValueError: If review format is invalid
        """
        # Check top-level structure
        required_keys = {"file_scores", "overall_review"}
        if not all(key in review for key in required_keys):
            raise ValueError("Invalid review format: missing required sections")
            
        # Check file scores
        if file_path not in review["file_scores"]:
            raise ValueError("Invalid review format: file path not in scores")
            
        scores = review["file_scores"][file_path]
        required_metrics = {
            "readability", "maintainability", "complexity",
            "coding_standards", "documentation", "security",
            "performance", "reusability", "error_handling",
            "test_coverage", "notes"
        }
        
        if not all(metric in scores for metric in required_metrics):
            raise ValueError("Invalid review format: missing required metrics")
            
        # Check overall review
        overall = review["overall_review"]
        required_overall = {
            "total_score", "strengths", "concerns",
            "hiring_confidence", "risks", "summary"
        }
        
        if not all(key in overall for key in required_overall):
            raise ValueError("Invalid review format: missing overall review sections")
