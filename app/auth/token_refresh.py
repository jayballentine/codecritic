import os
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidSignatureError
from postgrest.exceptions import APIError
from app.utils.security import SecurityUtilities
from app.auth.session_management import get_session_manager, create_user_session

# Constants for token configuration
REFRESH_TOKEN_EXPIRY = timedelta(days=7)  # Maximum time a token can be refreshed
ACCESS_TOKEN_EXPIRY = timedelta(hours=1)   # New token validity period

def _decode_without_verification(token: str) -> dict:
    """
    Decode a JWT token without verifying expiration.
    
    Args:
        token (str): The JWT token to decode
    
    Returns:
        dict: The decoded token payload
    
    Raises:
        InvalidSignatureError: If the token signature is invalid
    """
    try:
        # Get JWT secret from environment variable
        jwt_secret = os.getenv('JWT_SECRET_KEY', 'fallback_secret_for_testing')
        
        # Decode without verifying expiration
        return jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"],
            options={"verify_exp": False}
        )
    except jwt.InvalidSignatureError:
        raise InvalidSignatureError("Invalid token signature")
    except jwt.DecodeError:
        raise InvalidSignatureError("Invalid token format")

def _parse_datetime(dt_str: str) -> datetime:
    """Parse datetime string from database."""
    try:
        # Remove microseconds to avoid parsing issues
        if '+' in dt_str:
            main_part, tz_part = dt_str.split('+')
            main_part = main_part.split('.')[0]  # Remove microseconds
            dt_str = f"{main_part}+{tz_part}"
        return datetime.fromisoformat(dt_str)
    except ValueError:
        # If that fails, try replacing space with T
        if ' ' in dt_str:
            dt_str = dt_str.replace(' ', 'T')
        if '.' in dt_str:
            dt_str = dt_str.split('.')[0]  # Remove microseconds
        return datetime.fromisoformat(dt_str)

def refresh_expired_token(token: str) -> str:
    """
    Refresh an expired token with security measures.
    
    Args:
        token (str): The expired JWT token to refresh
    
    Returns:
        str: A new valid JWT token
    
    Raises:
        ExpiredSignatureError: If the token has expired
        InvalidSignatureError: If the token signature is invalid
        ValueError: If the token has already been refreshed or is invalid
    """
    # First verify the token format and signature
    if '.' not in token or len(token.split('.')) != 3:
        raise InvalidSignatureError("Invalid token format")

    # Decode token without verification to get payload
    # This will raise InvalidSignatureError if signature is invalid
    payload = _decode_without_verification(token)
    
    if not payload.get('session_id'):
        raise ValueError("Invalid token format - missing session ID")
        
    try:
        # First check if session exists and is active
        session = get_session_manager().client.table('sessions')\
            .select('*')\
            .eq('session_id', payload['session_id'])\
            .eq('is_active', True)\
            .single()\
            .execute()
            
        if not session.data:
            raise ValueError("Token has already been refreshed")
            
    except APIError:
        # No active session found
        raise ValueError("Token has already been refreshed")
        
    # Verify refresh hasn't expired
    expiry = _parse_datetime(session.data['expiry'])
    if datetime.now(timezone.utc) > expiry:
        raise ValueError("Refresh token has expired")
        
    # Invalidate the old session
    get_session_manager().client.table('sessions')\
        .update({'is_active': False})\
        .eq('session_id', payload['session_id'])\
        .execute()
        
    # Create new session with short access token expiry
    # The session expiry will be set to REFRESH_TOKEN_EXPIRY by create_session
    new_session = create_user_session(
        payload['user_id'],
        token_expiry=ACCESS_TOKEN_EXPIRY
    )
    
    return new_session['token']

def validate_refresh_token(token: str) -> bool:
    """
    Validate if a token can be refreshed.
    
    Args:
        token (str): The JWT token to validate
    
    Returns:
        bool: True if token can be refreshed, False otherwise
    """
    try:
        # First try normal validation
        SecurityUtilities.validate_jwt_token(token)
        return False  # Token is still valid, doesn't need refresh
        
    except ExpiredSignatureError:
        try:
            # Token is expired, check if it can be refreshed
            payload = _decode_without_verification(token)
            
            if not payload.get('session_id'):
                return False
                
            try:
                # Check if session is still active
                session = get_session_manager().client.table('sessions')\
                    .select('*')\
                    .eq('session_id', payload['session_id'])\
                    .eq('is_active', True)\
                    .single()\
                    .execute()
                    
                if not session.data:
                    return False
                    
            except APIError:
                return False
                
            # Verify refresh hasn't expired
            expiry = _parse_datetime(session.data['expiry'])
            return datetime.now(timezone.utc) <= expiry
            
        except Exception:
            return False
            
    except Exception:
        return False
