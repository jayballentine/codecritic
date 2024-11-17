import pytest
from app.models.repository import Repository
from app.auth.access_control import has_access

@pytest.fixture
def public_repo():
    return Repository(repo_id="public_repo", submission_method="github_url", github_url="https://github.com/public/repo")

@pytest.fixture
def private_repo():
    return Repository(repo_id="private_repo", submission_method="zip_file", file_path="/path/to/private_repo.zip")

def test_has_access_public_repo(public_repo):
    assert has_access(public_repo, "user1") == True

def test_has_access_private_repo(private_repo):
    assert has_access(private_repo, "user1") == False

def test_has_access_private_repo_owner(private_repo):
    assert has_access(private_repo, "owner") == True

def test_has_access_private_repo_non_owner(private_repo):
    assert has_access(private_repo, "non_owner") == False
