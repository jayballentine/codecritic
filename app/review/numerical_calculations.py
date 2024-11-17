"""
Numerical calculations module for code review metrics processing.

Handles batch and merged batch calculations of review metrics,
ensuring consistent and accurate metric aggregation.
"""
from typing import List, Dict, Any, Union
from statistics import mean
from dataclasses import dataclass, asdict

@dataclass
class ReviewMetrics:
    """
    Standardized structure for review metrics across different review stages.
    
    Supports flexible metric tracking with type-safe calculations.
    """
    readability: float = 0.0
    maintainability: float = 0.0
    complexity: float = 0.0
    coding_standards: float = 0.0
    documentation: float = 0.0
    security: float = 0.0
    performance: float = 0.0
    reusability: float = 0.0
    error_handling: float = 0.0
    test_coverage: float = 0.0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Union[int, float]]):
        """
        Create ReviewMetrics from a dictionary, handling missing keys gracefully.
        
        Args:
            data: Dictionary of metrics
        
        Returns:
            ReviewMetrics instance
        """
        return cls(**{
            k: float(data.get(k, 0.0))
            for k in cls.__annotations__
        })
    
    def to_dict(self) -> Dict[str, float]:
        """Convert metrics to dictionary."""
        return asdict(self)

class NumericalProcessor:
    """
    Processes numerical metrics for code reviews across different stages.
    
    Handles:
    - Individual file metric calculations
    - Batch metric aggregation
    - Merged batch metric consolidation
    """
    
    @staticmethod
    def calculate_batch_averages(reviews: List[Dict[str, Any]]) -> ReviewMetrics:
        """
        Calculate average metrics for a batch of reviews.
        
        Args:
            reviews: List of individual review dictionaries
        
        Returns:
            Aggregated ReviewMetrics
        """
        if not reviews:
            raise ValueError("Cannot process empty batch of reviews")
            
        # For batch reviews, use consistency and pattern quality scores
        if all('batch_analysis' in review for review in reviews):
            metrics = {
                'readability': mean(review['batch_analysis'].get('consistency_score', 0) for review in reviews),
                'maintainability': mean(review['batch_analysis'].get('pattern_quality', 0) for review in reviews),
                'complexity': mean(review['batch_analysis'].get('cohesion_rating', 0) for review in reviews),
                'coding_standards': mean(review['batch_analysis'].get('consistency_score', 0) for review in reviews),
                'documentation': mean(review['batch_analysis'].get('pattern_quality', 0) for review in reviews),
                'security': 0.0,  # Not applicable for batch reviews
                'performance': 0.0,  # Not applicable for batch reviews
                'reusability': mean(review['batch_analysis'].get('cohesion_rating', 0) for review in reviews),
                'error_handling': 0.0,  # Not applicable for batch reviews
                'test_coverage': 0.0  # Not applicable for batch reviews
            }
            return ReviewMetrics(**metrics)
            
        # For individual file reviews, use file scores
        batch_metrics = []
        for review in reviews:
            file_scores = review.get('file_scores', {})
            for scores in file_scores.values():
                batch_metrics.append(ReviewMetrics.from_dict(scores))
        
        if not batch_metrics:
            raise ValueError("No valid metrics found in reviews")
        
        # Calculate averages
        avg_metrics = {
            metric: mean(getattr(m, metric) for m in batch_metrics)
            for metric in ReviewMetrics.__annotations__
        }
        
        return ReviewMetrics(**avg_metrics)
    
    @staticmethod
    def calculate_merged_batch_averages(batches: List[List[Dict[str, Any]]]) -> ReviewMetrics:
        """
        Calculate average metrics across multiple batches.
        
        Args:
            batches: List of review batches
        
        Returns:
            Consolidated ReviewMetrics
        """
        if not batches:
            raise ValueError("Cannot process empty list of batches")
        
        # Flatten all reviews
        all_reviews = [review for batch in batches for review in batch]
        
        return NumericalProcessor.calculate_batch_averages(all_reviews)
    
    @staticmethod
    def extract_qualitative_data(reviews: List[Dict[str, Any]]) -> List[str]:
        """
        Extract only qualitative data from reviews.
        
        Args:
            reviews: List of review dictionaries
        
        Returns:
            List of qualitative data strings
        """
        qualitative_data = []
        for review in reviews:
            # Handle batch reviews
            if 'batch_analysis' in review:
                findings = review['batch_analysis'].get('findings', {})
                for category in ['patterns_identified', 'consistency_issues', 'cohesion_concerns']:
                    qualitative_data.extend(findings.get(category, []))
                continue
                
            # Handle individual file reviews
            overall_review = review.get('overall_review', {})
            if not any(
                isinstance(val, (int, float)) or 
                (isinstance(val, str) and val.replace('.', '').isdigit())
                for val in overall_review.values()
            ):
                summary = overall_review.get('summary', '')
                if summary:
                    qualitative_data.append(summary)
        
        return qualitative_data
