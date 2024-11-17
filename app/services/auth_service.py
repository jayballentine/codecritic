from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from app.db.base import get_database_client
from app.utils.logger import get_logger
from app.models.user import UserCreate, UserResponse

logger = get_logger(__name__)

class AuthService:
    """
    Service for handling authentication using Supabase.
    """
    @staticmethod
    async def sign_up(user_data: UserCreate) -> Dict[str, Any]:
        """
        Register a new user using Supabase authentication.

        Args:
            user_data: User registration data

        Returns:
            Dict containing user data and session
        """
        try:
            client = get_database_client().client
            auth_response = client.auth.sign_up({
                "email": user_data.email,
                "password": user_data.password,
                "options": {
                    "data": {
                        "full_name": user_data.full_name
                    }
                }
            })
            
            if auth_response.user:
                return {
                    "user": auth_response.user,
                    "session": auth_response.session
                }
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user"
            )
        except Exception as e:
            logger.error(f"Sign up failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    @staticmethod
    async def sign_in(email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate a user using Supabase authentication.

        Args:
            email: User's email
            password: User's password

        Returns:
            Dict containing user data and session
        """
        try:
            client = get_database_client().client
            auth_response = client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if auth_response.user and auth_response.session:
                return {
                    "user": auth_response.user,
                    "session": auth_response.session
                }
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        except Exception as e:
            logger.error(f"Sign in failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )

    @staticmethod
    async def sign_out(access_token: str) -> None:
        """
        Sign out a user using Supabase authentication.

        Args:
            access_token: User's access token
        """
        try:
            client = get_database_client().client
            client.auth.sign_out()
        except Exception as e:
            logger.error(f"Sign out failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to sign out"
            )

    @staticmethod
    async def get_current_user(access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get the current authenticated user using Supabase.

        Args:
            access_token: User's access token

        Returns:
            Optional[Dict] containing user data
        """
        try:
            client = get_database_client().client
            user = client.auth.get_user(access_token)
            return user.dict() if user else None
        except Exception as e:
            logger.error(f"Failed to get current user: {str(e)}")
            return None

    @staticmethod
    async def reset_password(email: str) -> None:
        """
        Send a password reset email using Supabase.

        Args:
            email: User's email address
        """
        try:
            client = get_database_client().client
            client.auth.reset_password_email(email)
        except Exception as e:
            logger.error(f"Password reset failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to send password reset email"
            )
