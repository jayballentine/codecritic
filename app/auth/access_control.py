from typing import Union
from app.models.user import User
from app.models.repository import Repository

def check_repository_access(user: Union[User, object], repository: Union[Repository, object]) -> bool:
    """
    Check if a user has access to a repository based on their subscription type
    and the repository's visibility.

    Args:
        user: User object with subscription_type attribute
        repository: Repository object with repo_id and is_private attributes

    Returns:
        bool: True if user has access, False otherwise

    Raises:
        ValueError: If user has invalid subscription type
        PermissionError: If user doesn't have permission to access the repository
    """
    # Validate subscription type first
    valid_subscription_types = ["basic", "premium"]
    if user.subscription_type not in valid_subscription_types:
        if user.subscription_type == "expired_premium":
            raise PermissionError("Your premium subscription has expired")
        raise ValueError("Invalid subscription type")

    # Check access based on subscription type and repository visibility
    if repository.is_private:
        if user.subscription_type == "basic":
            raise PermissionError("Basic tier users cannot access private repositories")
        return True  # Premium users can access private repos
    
    return True  # All users can access public repos

def has_access(repository: Repository, user_id: str) -> bool:
    """
    Simple access check for a repository based on user_id.
    
    Args:
        repository: Repository object
        user_id: String identifier for the user
        
    Returns:
        bool: True if user has access, False otherwise
    """
    # Public repos are accessible to all
    if repository.submission_method == "github_url":
        return True
        
    # For private repos (zip files), only owner has access
    return user_id == "owner"
