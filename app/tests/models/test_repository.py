import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.models.repository import Repository
from app.db.session import get_supabase_client

@pytest.fixture
def mock_supabase():
    """Fixture to provide a mocked Supabase client."""
    with patch('app.models.repository.get_supabase_client') as mock:
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

def test_repo_id_uniqueness(mock_supabase):
    """Test that repo_id is unique across repositories."""
    # Configure mock for first successful insert
    mock_supabase.table.return_value.insert.return_value.execute.return_value = {
        "data": [{
            "repo_id": "unique_repo_1",
            "status": "Pending",
            "submission_method": "github_url",
            "github_url": "https://github.com/user/repo1"
        }]
    }
    
    # Create first repository successfully
    first_repo = Repository(
        repo_id="unique_repo_1",
        submission_method="github_url",
        github_url="https://github.com/user/repo1"
    )
    first_repo.save()
    
    # Configure mock to raise exception for duplicate repo_id
    mock_supabase.table.return_value.insert.return_value.execute.side_effect = Exception("unique constraint")
    
    # Attempt to create another repository with same repo_id
    with pytest.raises(Exception) as excinfo:
        second_repo = Repository(
            repo_id="unique_repo_1",
            submission_method="github_url",
            github_url="https://github.com/user/repo2"
        )
        second_repo.save()
    
    assert "unique constraint" in str(excinfo.value).lower()

def test_status_lifecycle(mock_supabase):
    """Test that repository status transitions correctly through its lifecycle."""
    # Configure mock for initial creation
    mock_supabase.table.return_value.insert.return_value.execute.return_value = {
        "data": [{
            "repo_id": "lifecycle_test",
            "status": "Pending",
            "submission_method": "github_url",
            "github_url": "https://github.com/user/repo"
        }]
    }
    
    # Create repository (should start as Pending)
    repo = Repository(
        repo_id="lifecycle_test",
        submission_method="github_url",
        github_url="https://github.com/user/repo"
    )
    repo.save()
    assert repo.status == "Pending"
    
    # Configure mock for first status update (Pending -> In Progress)
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = {
        "data": [{
            "repo_id": "lifecycle_test",
            "status": "In Progress",
            "submission_method": "github_url",
            "github_url": "https://github.com/user/repo"
        }]
    }
    
    # Update to In Progress
    repo.status = "In Progress"
    repo.save()
    
    # Configure mock for second status update (In Progress -> Completed)
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = {
        "data": [{
            "repo_id": "lifecycle_test",
            "status": "Completed",
            "submission_method": "github_url",
            "github_url": "https://github.com/user/repo"
        }]
    }
    
    # Update to Completed
    repo.status = "Completed"
    repo.save()
    
    # Test invalid status transition (Completed -> Pending)
    with pytest.raises(ValueError) as excinfo:
        repo.status = "Pending"
        repo.save()
    
    assert "invalid status transition" in str(excinfo.value).lower()
    
    # Test invalid status value
    with pytest.raises(ValueError) as excinfo:
        repo.status = "Invalid Status"
        repo.save()
    
    assert "invalid status" in str(excinfo.value).lower()

def test_submission_method_validation(mock_supabase):
    """Test that only valid submission methods are accepted."""
    # Test valid GitHub URL submission
    mock_supabase.table.return_value.insert.return_value.execute.return_value = {
        "data": [{
            "repo_id": "github_test",
            "status": "Pending",
            "submission_method": "github_url",
            "github_url": "https://github.com/user/repo"
        }]
    }
    
    github_repo = Repository(
        repo_id="github_test",
        submission_method="github_url",
        github_url="https://github.com/user/repo"
    )
    github_repo.save()
    
    # Test valid zip file submission
    mock_supabase.table.return_value.insert.return_value.execute.return_value = {
        "data": [{
            "repo_id": "zip_test",
            "status": "Pending",
            "submission_method": "zip_file",
            "file_path": "path/to/repo.zip"
        }]
    }
    
    zip_repo = Repository(
        repo_id="zip_test",
        submission_method="zip_file",
        file_path="path/to/repo.zip"
    )
    zip_repo.save()
    
    # Test invalid submission method
    with pytest.raises(ValueError) as excinfo:
        invalid_repo = Repository(
            repo_id="invalid_test",
            submission_method="invalid_method"
        )
        invalid_repo.save()
    
    assert "invalid submission method" in str(excinfo.value).lower()
    
    # Test GitHub URL submission without URL
    with pytest.raises(ValueError) as excinfo:
        missing_url_repo = Repository(
            repo_id="missing_url_test",
            submission_method="github_url"
        )
        missing_url_repo.save()
    
    assert "github url required" in str(excinfo.value).lower()
    
    # Test zip file submission without file path
    with pytest.raises(ValueError) as excinfo:
        missing_file_repo = Repository(
            repo_id="missing_file_test",
            submission_method="zip_file"
        )
        missing_file_repo.save()
    
    assert "file path required" in str(excinfo.value).lower()

def test_github_url_validation(mock_supabase):
    """Test that GitHub URLs are properly validated."""
    # Test invalid GitHub URL format
    with pytest.raises(ValueError) as excinfo:
        repo = Repository(
            repo_id="invalid_url_test",
            submission_method="github_url",
            github_url="not_a_github_url"
        )
        repo.save()
    
    assert "invalid github url format" in str(excinfo.value).lower()
    
    # Test non-GitHub URL
    with pytest.raises(ValueError) as excinfo:
        repo = Repository(
            repo_id="wrong_domain_test",
            submission_method="github_url",
            github_url="https://gitlab.com/user/repo"
        )
        repo.save()
    
    assert "must be a github.com url" in str(excinfo.value).lower()

def test_zip_file_validation(mock_supabase):
    """Test that zip file submissions are properly validated."""
    # Test invalid file extension
    with pytest.raises(ValueError) as excinfo:
        repo = Repository(
            repo_id="invalid_ext_test",
            submission_method="zip_file",
            file_path="path/to/repo.rar"
        )
        repo.save()
    
    assert "must be a zip file" in str(excinfo.value).lower()
    
    # Test empty file path
    with pytest.raises(ValueError) as excinfo:
        repo = Repository(
            repo_id="empty_path_test",
            submission_method="zip_file",
            file_path=""
        )
        repo.save()
    
    assert "file path cannot be empty" in str(excinfo.value).lower()
