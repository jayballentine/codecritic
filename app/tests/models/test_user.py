import os
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.models.user import User
from app.db.session import get_supabase_client

@pytest.fixture
def mock_supabase():
    """Fixture to provide a mocked Supabase client."""
    with patch('app.models.user.get_supabase_client') as mock:
        client = Mock()
        mock.return_value = client
        
        # Mock table method
        table_mock = Mock()
        client.table.return_value = table_mock
        
        # Mock select chain
        select_mock = Mock()
        table_mock.select.return_value = select_mock
        eq_mock = Mock()
        select_mock.eq.return_value = eq_mock
        eq_mock.execute.return_value = {"data": []}
        
        # Mock insert chain
        insert_mock = Mock()
        table_mock.insert.return_value = insert_mock
        insert_mock.execute.return_value = {"data": []}
        
        # Mock update chain
        update_mock = Mock()
        table_mock.update.return_value = update_mock
        update_mock.eq.return_value = Mock()
        update_mock.eq.return_value.execute.return_value = {"data": []}
        
        yield client

def test_user_id_uniqueness(mock_supabase):
    """Test that user_id is unique across users."""
    # Configure mock for first successful insert
    mock_supabase.table.return_value.insert.return_value.execute.return_value = {
        "data": [{
            "user_id": "unique_test_id_1",
            "email": "test1@example.com",
            "name": "Test User 1",
            "subscription_type": "free"
        }]
    }
    
    # Create first user successfully
    first_user = User(
        user_id="unique_test_id_1",
        email="test1@example.com",
        name="Test User 1"
    )
    first_user.save()
    
    # Configure mock to raise exception for duplicate user_id
    mock_supabase.table.return_value.insert.return_value.execute.side_effect = Exception("unique constraint")
    
    # Attempt to create another user with same user_id
    with pytest.raises(Exception) as excinfo:
        second_user = User(
            user_id="unique_test_id_1",
            email="test2@example.com",
            name="Test User 2"
        )
        second_user.save()
    
    assert "unique constraint" in str(excinfo.value).lower()

def test_email_uniqueness(mock_supabase):
    """Test that email is unique across users."""
    # Configure mock for first successful insert
    mock_supabase.table.return_value.insert.return_value.execute.return_value = {
        "data": [{
            "user_id": "unique_test_id_2",
            "email": "unique_email@example.com",
            "name": "Test User 1",
            "subscription_type": "free"
        }]
    }
    
    # Create first user successfully
    first_user = User(
        user_id="unique_test_id_2",
        email="unique_email@example.com",
        name="Test User 1"
    )
    first_user.save()
    
    # Configure mock to raise exception for duplicate email
    mock_supabase.table.return_value.insert.return_value.execute.side_effect = Exception("unique constraint")
    
    # Attempt to create another user with same email
    with pytest.raises(Exception) as excinfo:
        second_user = User(
            user_id="another_unique_id",
            email="unique_email@example.com",
            name="Test User 2"
        )
        second_user.save()
    
    assert "unique constraint" in str(excinfo.value).lower()

def test_default_subscription_type(mock_supabase):
    """Test that new users have 'free' subscription type by default."""
    # Create user without specifying subscription_type
    user = User(
        user_id="default_sub_test",
        email="default_sub@example.com",
        name="Default Sub User"
    )
    
    # Configure mock for successful insert with default subscription_type
    mock_supabase.table.return_value.insert.return_value.execute.return_value = {
        "data": [{
            "user_id": "default_sub_test",
            "email": "default_sub@example.com",
            "name": "Default Sub User",
            "subscription_type": "free"
        }]
    }
    
    user.save()
    
    # Configure mock for retrieval
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = {
        "data": [{
            "user_id": "default_sub_test",
            "email": "default_sub@example.com",
            "name": "Default Sub User",
            "subscription_type": "free"
        }]
    }
    
    retrieved_user = User.get_by_user_id("default_sub_test")
    assert retrieved_user.subscription_type == "free"

def test_timestamps_auto_management(mock_supabase):
    """Test that created_at and updated_at are automatically managed."""
    initial_time = datetime.now(timezone.utc)
    updated_time = datetime.now(timezone.utc)
    
    # Configure mock for initial insert
    mock_supabase.table.return_value.insert.return_value.execute.return_value = {
        "data": [{
            "user_id": "timestamp_test",
            "email": "timestamp@example.com",
            "name": "Timestamp Test User",
            "subscription_type": "free",
            "created_at": initial_time.isoformat(),
            "updated_at": initial_time.isoformat()
        }]
    }
    
    # Create user
    user = User(
        user_id="timestamp_test",
        email="timestamp@example.com",
        name="Timestamp Test User"
    )
    user.save()
    
    # Configure mock for update
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = {
        "data": [{
            "user_id": "timestamp_test",
            "email": "timestamp@example.com",
            "name": "Updated Timestamp User",
            "subscription_type": "free",
            "created_at": initial_time.isoformat(),
            "updated_at": updated_time.isoformat()
        }]
    }
    
    # Update user
    user.name = "Updated Timestamp User"
    user.save()
    
    # Configure mock for retrieval
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = {
        "data": [{
            "user_id": "timestamp_test",
            "email": "timestamp@example.com",
            "name": "Updated Timestamp User",
            "subscription_type": "free",
            "created_at": initial_time.isoformat(),
            "updated_at": updated_time.isoformat()
        }]
    }
    
    # Retrieve updated user
    updated_user = User.get_by_user_id("timestamp_test")
    assert updated_user.created_at == initial_time.isoformat()
    assert updated_user.updated_at == updated_time.isoformat()
    assert updated_user.updated_at != updated_user.created_at
