from datetime import datetime
from pydantic import BaseModel, EmailStr, validator, constr
from typing import List, Optional, Dict, Any
from app.db.base import get_database_client
from app.utils.logger import get_logger

logger = get_logger(__name__)

class User(BaseModel):
    user_id: int
    email: EmailStr
    subscription_type: str
    created_at: datetime = datetime.now()

    @validator('subscription_type')
    def validate_subscription_type(cls, v):
        valid_types = ['basic', 'premium', 'enterprise']
        if v not in valid_types:
            raise ValueError(f"Subscription type must be one of {valid_types}")
        return v

    @classmethod
    async def create(cls, email: str, subscription_type: str) -> 'User':
        """Create a new user in Supabase."""
        try:
            client = get_database_client().client
            # Check for existing user
            existing = client.table('users').select('*').eq('email', email).execute()
            if existing.data:
                raise ValueError("Email already exists")

            data = {
                'email': email,
                'subscription_type': subscription_type,
                'created_at': datetime.now().isoformat()
            }
            result = client.table('users').insert(data).execute()
            
            if result.data:
                return cls(**result.data[0])
            raise ValueError("Failed to create user")
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise

    @classmethod
    async def get_by_email(cls, email: str) -> Optional['User']:
        """Fetch user by email."""
        try:
            client = get_database_client().client
            result = client.table('users').select('*').eq('email', email).execute()
            return cls(**result.data[0]) if result.data else None
        except Exception as e:
            logger.error(f"Error fetching user: {str(e)}")
            raise

class Repository(BaseModel):
    repo_id: int
    owner: str
    submission_date: datetime
    status: str

    @validator('owner')
    def validate_owner(cls, v):
        if not v or not v.strip():
            raise ValueError("Owner cannot be empty")
        return v

    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ['active', 'inactive']
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return v

    @classmethod
    async def create(cls, owner: str, status: str = 'active') -> 'Repository':
        """Create a new repository submission."""
        try:
            client = get_database_client().client
            data = {
                'owner': owner,
                'submission_date': datetime.now().isoformat(),
                'status': status
            }
            result = client.table('repositories').insert(data).execute()
            
            if result.data:
                return cls(**result.data[0])
            raise ValueError("Failed to create repository")
        except Exception as e:
            logger.error(f"Error creating repository: {str(e)}")
            raise

    @classmethod
    async def get_by_owner(cls, owner: str) -> List['Repository']:
        """Fetch repositories by owner."""
        try:
            client = get_database_client().client
            result = client.table('repositories').select('*').eq('owner', owner).execute()
            return [cls(**repo) for repo in result.data]
        except Exception as e:
            logger.error(f"Error fetching repositories: {str(e)}")
            raise

    async def update_status(self, new_status: str) -> 'Repository':
        """Update repository status."""
        try:
            client = get_database_client().client
            result = client.table('repositories').update(
                {'status': new_status}
            ).eq('repo_id', self.repo_id).execute()
            
            if result.data:
                return self.__class__(**result.data[0])
            raise ValueError("Failed to update repository status")
        except Exception as e:
            logger.error(f"Error updating repository status: {str(e)}")
            raise

class Review(BaseModel):
    review_id: int
    repo_id: int
    file_reviews: str
    batch_reviews: str
    final_review: str

    @validator('file_reviews', 'batch_reviews', 'final_review')
    def validate_reviews(cls, v):
        if not v or not v.strip():
            raise ValueError("Review content cannot be empty")
        return v

    @classmethod
    async def create(cls, repo_id: int, file_reviews: str, batch_reviews: str, final_review: str) -> 'Review':
        """Create a new review."""
        try:
            client = get_database_client().client
            # Verify repository exists
            repo = client.table('repositories').select('*').eq('repo_id', repo_id).execute()
            if not repo.data:
                raise ValueError("Repository not found")

            data = {
                'repo_id': repo_id,
                'file_reviews': file_reviews,
                'batch_reviews': batch_reviews,
                'final_review': final_review
            }
            result = client.table('reviews').insert(data).execute()
            
            if result.data:
                return cls(**result.data[0])
            raise ValueError("Failed to create review")
        except Exception as e:
            logger.error(f"Error creating review: {str(e)}")
            raise

    @classmethod
    async def get_by_repo_id(cls, repo_id: int) -> List['Review']:
        """Fetch all reviews for a repository."""
        try:
            client = get_database_client().client
            result = client.table('reviews').select('*').eq('repo_id', repo_id).execute()
            return [cls(**review) for review in result.data]
        except Exception as e:
            logger.error(f"Error fetching reviews: {str(e)}")
            raise

    async def update_review(self, updates: Dict[str, str]) -> 'Review':
        """Update review content."""
        try:
            client = get_database_client().client
            result = client.table('reviews').update(updates).eq(
                'review_id', self.review_id
            ).execute()
            
            if result.data:
                return self.__class__(**result.data[0])
            raise ValueError("Failed to update review")
        except Exception as e:
            logger.error(f"Error updating review: {str(e)}")
            raise
from supabase import create_client, Client
from typing import Dict, List, Optional
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime
import uuid

class SupabaseManager:
    def __init__(self, supabase_url: str, supabase_key: str):
        """
        Initialize Supabase client with provided credentials
        
        Args:
            supabase_url (str): Supabase project URL
            supabase_key (str): Supabase API key
        """
        self.supabase: Client = create_client(supabase_url, supabase_key)

class User(BaseModel):
    """
    User model with validation and Supabase integration
    """
    id: Optional[str] = None
    email: EmailStr
    username: str
    created_at: Optional[datetime] = None

    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        return v

class UserManager(SupabaseManager):
    def create_user(self, user: User) -> Dict:
        """
        Create a new user in Supabase
        
        Args:
            user (User): User model with registration details
        
        Returns:
            Dict: Created user details
        """
        try:
            # Check for existing user
            existing_user = self.supabase.table('users').select('*').eq('email', user.email).execute()
            if existing_user.data:
                raise ValueError('User with this email already exists')

            # Generate unique ID if not provided
            user.id = user.id or str(uuid.uuid4())
            user.created_at = datetime.utcnow()

            result = self.supabase.table('users').insert(user.dict()).execute()
            return result.data[0]
        except Exception as e:
            raise ValueError(f"User creation failed: {str(e)}")

class Repository(BaseModel):
    """
    Repository model with validation
    """
    id: Optional[str] = None
    name: str
    url: str
    user_id: str
    status: str = 'pending'
    created_at: Optional[datetime] = None

    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ['pending', 'approved', 'rejected']
        if v not in valid_statuses:
            raise ValueError(f'Invalid status. Must be one of {valid_statuses}')
        return v

class RepositoryManager(SupabaseManager):
    def submit_repository(self, repo: Repository) -> Dict:
        """
        Submit a new repository for review
        
        Args:
            repo (Repository): Repository submission details
        
        Returns:
            Dict: Submitted repository details
        """
        try:
            repo.id = repo.id or str(uuid.uuid4())
            repo.created_at = datetime.utcnow()
            repo.status = 'pending'

            result = self.supabase.table('repositories').insert(repo.dict()).execute()
            return result.data[0]
        except Exception as e:
            raise ValueError(f"Repository submission failed: {str(e)}")

    def get_user_repositories(self, user_id: str) -> List[Dict]:
        """
        Fetch repositories for a specific user
        
        Args:
            user_id (str): User's unique identifier
        
        Returns:
            List[Dict]: List of user's repositories
        """
        try:
            result = self.supabase.table('repositories').select('*').eq('user_id', user_id).execute()
            return result.data
        except Exception as e:
            raise ValueError(f"Failed to fetch repositories: {str(e)}")

class Review(BaseModel):
    """
    Review model for repository submissions
    """
    id: Optional[str] = None
    repository_id: str
    reviewer_id: str
    status: str
    comments: Optional[str] = None
    created_at: Optional[datetime] = None

class ReviewManager(SupabaseManager):
    def create_review(self, review: Review) -> Dict:
        """
        Create a review for a repository submission
        
        Args:
            review (Review): Review details
        
        Returns:
            Dict: Created review details
        """
        try:
            review.id = review.id or str(uuid.uuid4())
            review.created_at = datetime.utcnow()

            result = self.supabase.table('reviews').insert(review.dict()).execute()
            
            # Update repository status based on review
            self.supabase.table('repositories').update({'status': review.status}).eq('id', review.repository_id).execute()
            
            return result.data[0]
        except Exception as e:
            raise ValueError(f"Review creation failed: {str(e)}")

    def get_repository_reviews(self, repository_id: str) -> List[Dict]:
        """
        Fetch reviews for a specific repository
        
        Args:
            repository_id (str): Repository's unique identifier
        
        Returns:
            List[Dict]: List of repository reviews
        """
        try:
            result = self.supabase.table('reviews').select('*').eq('repository_id', repository_id).execute()
            return result.data
        except Exception as e:
            raise ValueError(f"Failed to fetch reviews: {str(e)}")
