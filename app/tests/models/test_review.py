import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from app.models.review import Review
from app.models.repository import Repository

class TestReviewModel:
    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client for testing."""
        with patch('app.models.review.get_supabase_client') as mock_client:
            mock_client_instance = Mock()
            mock_client.return_value = mock_client_instance
            yield mock_client_instance

    @pytest.fixture
    def sample_repository(self):
        """Create a sample repository for testing reviews."""
        return Mock(id=1, name="test-repo")

    def test_review_creation(self, sample_repository):
        """Test creating a new review for a repository."""
        review = Review.create(
            repo_id=sample_repository.id,
            file_reviews=[
                {
                    "file_path": "src/main.py",
                    "score": 8.5,
                    "comments": ["Good structure"]
                },
                {
                    "file_path": "src/utils.py", 
                    "score": 7.0,
                    "comments": ["Could improve error handling"]
                }
            ]
        )
        
        assert review is not None
        assert review.repo_id == sample_repository.id
        assert len(review.file_reviews) == 2

    def test_batch_review_aggregation(self, sample_repository):
        """Test aggregation of file reviews into batch reviews."""
        review = Review.create(
            repo_id=sample_repository.id,
            file_reviews=[
                {
                    "file_path": "src/main.py",
                    "score": 8.5,
                    "comments": ["Good structure"]
                },
                {
                    "file_path": "src/utils.py", 
                    "score": 7.0,
                    "comments": ["Could improve error handling"]
                },
                {
                    "file_path": "tests/test_main.py",
                    "score": 9.0,
                    "comments": ["Comprehensive tests"]
                }
            ]
        )
        
        # Trigger batch review aggregation
        review.aggregate_batch_reviews()
        
        assert len(review.batch_reviews) > 0
        assert all(batch_review.get('score') is not None for batch_review in review.batch_reviews)
        
        # Check that batch reviews are grouped correctly
        batch_names = [batch['batch_name'] for batch in review.batch_reviews]
        assert 'src' in batch_names
        assert 'tests' in batch_names

    def test_final_review_computation(self, sample_repository):
        """Test computation of final review from batch reviews."""
        review = Review.create(
            repo_id=sample_repository.id,
            file_reviews=[
                {
                    "file_path": "src/main.py",
                    "score": 8.5,
                    "comments": ["Good structure"]
                },
                {
                    "file_path": "src/utils.py", 
                    "score": 7.0,
                    "comments": ["Could improve error handling"]
                },
                {
                    "file_path": "tests/test_main.py",
                    "score": 9.0,
                    "comments": ["Comprehensive tests"]
                }
            ]
        )
        
        # Trigger batch review aggregation and final review computation
        review.aggregate_batch_reviews()
        review.compute_final_review()
        
        assert review.final_review is not None
        assert review.final_review.get('overall_score') is not None
        assert review.final_review.get('summary') is not None
        assert 'batch_reviews' in review.final_review

    def test_review_persistence(self, mock_supabase_client, sample_repository):
        """Test that review data can be saved and retrieved."""
        review = Review.create(
            repo_id=sample_repository.id,
            file_reviews=[
                {
                    "file_path": "src/main.py",
                    "score": 8.5,
                    "comments": ["Good structure"]
                }
            ]
        )
        
        # Mock the Supabase table methods
        mock_table = Mock()
        mock_supabase_client.table.return_value = mock_table
        
        # Create mock data that matches the structure from Supabase
        mock_data = {
            'review_id': review.review_id,
            'repo_id': review.repo_id,
            'repository_name': review.repository_name,
            'file_reviews': review.file_reviews,
            'batch_reviews': review.batch_reviews,
            'final_review': review.final_review,
            'timestamp': review.timestamp.isoformat(),  # Convert datetime to ISO string
            'code_quality_metrics': review.code_quality_metrics
        }
        
        mock_table.upsert.return_value = Mock(execute=Mock(return_value=Mock(data=[mock_data])))
        mock_table.select.return_value = Mock(eq=Mock(return_value=Mock(execute=Mock(return_value=Mock(data=[mock_data])))))
        
        # Save the review
        result = review.save()
        
        # Retrieve the review
        retrieved_review = Review.get(review.review_id)
        
        # Assertions
        assert result is not None
        assert retrieved_review is not None
        assert retrieved_review.review_id == review.review_id
        assert retrieved_review.repo_id == sample_repository.id
        assert isinstance(retrieved_review.timestamp, datetime)  # Verify timestamp is properly parsed
