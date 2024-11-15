from datetime import datetime
from pydantic import BaseModel, EmailStr, validator, constr
from typing import List, Optional, Dict, Any
from app.db.base import get_database_client
from app.utils.logger import get_logger

logger = get_logger(__name__)

class User(BaseModel):
    user_id: Optional[int] = None
    email: EmailStr
    subscription_type: str
    created_at: datetime = datetime.now()

    @validator('email')
    def validate_email_format(cls, v):
        import re
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, v):
            raise ValueError("Invalid email format")
        return v

    @validator('subscription_type')
    def validate_subscription_type(cls, v):
        valid_types = ['basic', 'premium', 'enterprise']
        if v not in valid_types:
            raise ValueError(f"Subscription type must be one of {valid_types}")
        return v

    @classmethod
    async def create(cls, email: str, subscription_type: str, user_id: Optional[int] = None) -> 'User':
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
            if user_id is not None:
                data['user_id'] = user_id

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
    repo_id: Optional[int] = None
    user_id: int
    name: str
    owner: str
    submission_date: datetime = datetime.now()
    status: str = 'active'

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
    async def create(cls, user_id: int, name: str, owner: str, status: str = 'active') -> 'Repository':
        """Create a new repository submission."""
        try:
            client = get_database_client().client
            data = {
                'user_id': user_id,
                'name': name,
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
    review_id: Optional[int] = None
    repo_id: int
    user_id: int
    rating: int
    comment: str
    file_reviews: Optional[str] = None
    batch_reviews: Optional[str] = None
    final_review: Optional[str] = None

    @validator('file_reviews', 'batch_reviews', 'final_review')
    def validate_reviews(cls, v):
        if not v or not v.strip():
            raise ValueError("Review content cannot be empty")
        return v

    @classmethod
    async def create(cls, repo_id: int, user_id: int, rating: int, comment: str, 
                     file_reviews: Optional[str] = None, 
                     batch_reviews: Optional[str] = None, 
                     final_review: Optional[str] = None) -> 'Review':
        """Create a new review."""
        try:
            client = get_database_client().client
            # Verify repository exists
            repo = client.table('repositories').select('*').eq('repo_id', repo_id).execute()
            if not repo.data:
                raise ValueError("Repository not found")

            data = {
                'repo_id': repo_id,
                'user_id': user_id,
                'rating': rating,
                'comment': comment,
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
