"""
Test suite for numerical calculations in code review processing.

Validates batch and merged batch metric calculations.
"""
import pytest
from app.review.numerical_calculations import NumericalProcessor, ReviewMetrics

class TestNumericalCalculations:
    """
    Comprehensive test suite for numerical metric processing.
    """
    
    @pytest.fixture
    def sample_individual_reviews(self):
        """Generate sample individual review data."""
        return [
            {
                'file_scores': {
                    'actual_filename': {
                        'readability': 7.0,
                        'maintainability': 6.5,
                        'complexity': 5.0,
                        'coding_standards': 8.0,
                        'documentation': 7.5
                    }
                }
            } for _ in range(10)
        ]
    
    @pytest.fixture
    def sample_batches(self):
        """Generate multiple review batches."""
        return [
            [
                {
                    'file_scores': {
                        'actual_filename': {
                            'readability': 7.0,
                            'maintainability': 6.5,
                            'complexity': 5.0
                        }
                    }
                } for _ in range(5)
            ],
            [
                {
                    'file_scores': {
                        'actual_filename': {
                            'readability': 8.0,
                            'maintainability': 7.5,
                            'complexity': 6.0
                        }
                    }
                } for _ in range(5)
            ]
        ]
    
    def test_batch_average_calculation(self, sample_individual_reviews):
        """
        Test batch average calculation for review metrics.
        """
        batch_metrics = NumericalProcessor.calculate_batch_averages(sample_individual_reviews)
        
        # Verify each metric is correctly averaged
        assert batch_metrics.readability == pytest.approx(7.0)
        assert batch_metrics.maintainability == pytest.approx(6.5)
        assert batch_metrics.complexity == pytest.approx(5.0)
        assert batch_metrics.coding_standards == pytest.approx(8.0)
        assert batch_metrics.documentation == pytest.approx(7.5)
    
    def test_merged_batch_average_calculation(self, sample_batches):
        """
        Test merged batch average calculation across multiple batches.
        """
        merged_metrics = NumericalProcessor.calculate_merged_batch_averages(sample_batches)
        
        # Verify merged metrics are correctly calculated
        assert merged_metrics.readability == pytest.approx(7.5)
        assert merged_metrics.maintainability == pytest.approx(7.0)
        assert merged_metrics.complexity == pytest.approx(5.5)
    
    def test_empty_batch_handling(self):
        """
        Test handling of empty batch and merged batch scenarios.
        """
        with pytest.raises(ValueError, match="Cannot process empty batch of reviews"):
            NumericalProcessor.calculate_batch_averages([])
        
        with pytest.raises(ValueError, match="Cannot process empty list of batches"):
            NumericalProcessor.calculate_merged_batch_averages([])
    
    def test_qualitative_data_extraction(self):
        """
        Test extraction of qualitative data from reviews.
        """
        sample_reviews = [
            {
                'overall_review': {
                    'summary': 'Good code quality',
                    'total_score': 8.5,
                    'metrics': {'complexity': 7}
                }
            },
            {
                'overall_review': {
                    'summary': 'Needs improvement',
                    'total_score': 6.5,
                    'risks': ['Complex logic']
                }
            }
        ]
        
        qualitative_data = NumericalProcessor.extract_qualitative_data(sample_reviews)
        
        assert len(qualitative_data) == 0, "No qualitative data should be extracted when numerical values are present"
    
    def test_pure_qualitative_reviews(self):
        """
        Test extraction of qualitative data from reviews with no numerical values.
        """
        sample_reviews = [
            {
                'overall_review': {
                    'summary': 'Good code quality',
                    'strengths': ['Clean architecture']
                }
            },
            {
                'overall_review': {
                    'summary': 'Needs improvement',
                    'risks': ['Complex logic']
                }
            }
        ]
        
        qualitative_data = NumericalProcessor.extract_qualitative_data(sample_reviews)
        
        assert len(qualitative_data) == 2
        assert 'Good code quality' in qualitative_data
        assert 'Needs improvement' in qualitative_data
    
    def test_review_metrics_conversion(self):
        """
        Test conversion between dictionary and ReviewMetrics.
        """
        sample_dict = {
            'readability': 7.5,
            'maintainability': 6.0,
            'complexity': 5.5
        }
        
        metrics = ReviewMetrics.from_dict(sample_dict)
        
        assert metrics.readability == 7.5
        assert metrics.maintainability == 6.0
        assert metrics.complexity == 5.5
        
        # Test to_dict method
        metrics_dict = metrics.to_dict()
        assert metrics_dict['readability'] == 7.5
        assert metrics_dict['maintainability'] == 6.0
        assert metrics_dict['complexity'] == 5.5
