import os
import pytest
from unittest.mock import Mock, patch
from app.db.models import User, Repository, Review, get_database_client, DatabaseClient

class TestSupabaseModelIntegration:
    """
    Test suite for Supabase database model integration with mocking.
    """
    
    @pytest.fixture(autouse=True)
    def mock_database_client(self, monkeypatch):
        """
        Mock the DatabaseClient to prevent actual Supabase client creation.
        """
        mock_client = Mock()
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{"user_id": 1, "repo_id": 1}]
        mock_client.table.return_value.insert.return_value.execute.return_value.data = [
            {
                "user_id": 1,
                "email": "test@example.com",
                "subscription_type": "basic",
                "username": "testuser",
                "repo_id": 1,
                "name": "Test Repository",
                "status": "active",
                "rating": 4,
                "comment": "Great repository!"
            }
        ]
        
        def mock_get_database_client():
            mock_db_client = Mock(spec=DatabaseClient)
            mock_db_client.client = mock_client
            return mock_db_client
        
        monkeypatch.setattr('app.db.models.get_database_client', mock_get_database_client)
        return mock_client

    def test_user_creation(self):
        """
        Test user creation with mocked Supabase client.
        """
        user = User.create(
            email="test@example.com", 
            subscription_type="basic", 
            username="testuser"
        )
        
        assert user is not None
        assert user.email == "test@example.com"
        assert user.subscription_type == "basic"

    def test_repository_creation(self):
        """
        Test repository creation with mocked Supabase client.
        """
        repo = Repository.create(
            user_id=1, 
            name="Test Repository", 
            status="active"
        )
        
        assert repo is not None
        assert repo.name == "Test Repository"
        assert repo.status == "active"

    def test_review_creation(self):
        """
        Test review creation with mocked Supabase client.
        """
        review = Review.create(
            repo_id=1, 
            user_id=1, 
            rating=4, 
            comment="Great repository!"
        )
        
        assert review is not None
        assert review.rating == 4
        assert review.comment == "Great repository!"

    def test_user_email_validation(self):
        """
        Test user email validation.
        """
        with pytest.raises(ValueError, match="Invalid email format"):
            User.create(
                email="invalid-email", 
                subscription_type="basic"
            )

    def test_user_subscription_type_validation(self):
        """
        Test user subscription type validation.
        """
        with pytest.raises(ValueError, match="Subscription type must be one of"):
            User.create(
                email="test@example.com", 
                subscription_type="invalid-type"
            )

    def test_repository_status_validation(self):
        """
        Test repository status validation.
        """
        with pytest.raises(ValueError, match="Invalid repository status"):
            Repository.create(
                user_id=1, 
                name="Invalid Repo", 
                status="zombie-status"
            )

    def test_review_rating_validation(self):
        """
        Test review rating validation.
        """
        with pytest.raises(ValueError, match="Rating must be between 1 and 5"):
            Review.create(
                repo_id=1, 
                user_id=1, 
                rating=6, 
                comment="Out of range rating"
            )
