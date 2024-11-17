import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from cryptography.fernet import Fernet
from app.db.models import get_database_client
from app.utils.security import SecurityUtilities
from postgrest.exceptions import APIError

class SessionManager:
    def __init__(self):
        self.client = get_database_client().client
        # Initialize encryption key
        self.encryption_key = os.getenv('SESSION_ENCRYPTION_KEY', Fernet.generate_key())
        self.fernet = Fernet(self.encryption_key)

    def _encrypt_token(self, token: str) -> str:
        """Encrypt a token before storage"""
        return self.fernet.encrypt(token.encode()).decode()

    def _decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt a stored token"""
        return self.fernet.decrypt(encrypted_token.encode()).decode()

    def _is_valid_uuid(self, val: str) -> bool:
        """Check if a string is a valid UUID"""
        try:
            uuid.UUID(str(val))
            return True
        except ValueError:
            return False

    def create_session(self, user_id: int, token_expiry: timedelta = None) -> Dict:
        """Create a new session for a user"""
        if token_expiry is None:
            token_expiry = timedelta(hours=24)

        # Generate session ID
        session_id = str(uuid.uuid4())

        # Create JWT token
        payload = {
            'user_id': user_id,
            'session_id': session_id
        }
        token = SecurityUtilities.generate_jwt_token(payload, token_expiry)

        # Encrypt token for storage
        encrypted_token = self._encrypt_token(token)

        # Store session in database with UTC timezone
        now = datetime.now(timezone.utc)
        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'token': encrypted_token,
            'created_at': now.isoformat(),
            'expiry': (now + token_expiry).isoformat(),
            'is_active': True
        }

        self.client.table('sessions').insert(session_data).execute()

        return {
            'session_id': session_id,
            'token': token,
            'expiry': now + token_expiry
        }

    def validate_session(self, session_id: str) -> bool:
        """Validate if a session is active and not expired"""
        if not self._is_valid_uuid(session_id):
            return False

        try:
            result = self.client.table('sessions')\
                .select('*')\
                .eq('session_id', session_id)\
                .eq('is_active', True)\
                .single()\
                .execute()

            if not result.data:
                return False

            session = result.data
            expiry = datetime.fromisoformat(session['expiry'])
            now = datetime.now(timezone.utc)

            return expiry > now
        except APIError:
            return False

    def refresh_session(self, session_id: str) -> Dict:
        """Refresh an expired session with a new token"""
        if not self._is_valid_uuid(session_id):
            raise ValueError("Invalid session ID format")

        result = self.client.table('sessions')\
            .select('*')\
            .eq('session_id', session_id)\
            .single()\
            .execute()

        if not result.data:
            raise ValueError("Session not found")

        session = result.data
        
        # Invalidate old session
        self.client.table('sessions')\
            .update({'is_active': False})\
            .eq('session_id', session_id)\
            .execute()

        # Create new session
        return self.create_session(session['user_id'])

    def get_active_sessions(self, user_id: int) -> List[Dict]:
        """Get all active sessions for a user"""
        result = self.client.table('sessions')\
            .select('*')\
            .eq('user_id', user_id)\
            .eq('is_active', True)\
            .execute()

        return result.data if result.data else []

    def logout_session(self, user_id: int) -> None:
        """Invalidate all active sessions for a user"""
        self.client.table('sessions')\
            .update({'is_active': False})\
            .eq('user_id', user_id)\
            .eq('is_active', True)\
            .execute()

    def get_encrypted_token(self, session_id: str) -> Optional[str]:
        """Get the encrypted token for a session"""
        if not self._is_valid_uuid(session_id):
            return None

        result = self.client.table('sessions')\
            .select('token')\
            .eq('session_id', session_id)\
            .single()\
            .execute()

        return result.data['token'] if result.data else None

# Initialize global session manager
_session_manager = SessionManager()

# Public interface functions
def create_user_session(user_id: int, token_expiry: timedelta = None) -> Dict:
    return _session_manager.create_session(user_id, token_expiry)

def validate_session(session_id: str) -> bool:
    return _session_manager.validate_session(session_id)

def refresh_session(session_id: str) -> Dict:
    return _session_manager.refresh_session(session_id)

def get_active_sessions(user_id: int) -> List[Dict]:
    return _session_manager.get_active_sessions(user_id)

def logout_user(user_id: int) -> None:
    return _session_manager.logout_session(user_id)

def get_encrypted_token(session_id: str) -> Optional[str]:
    return _session_manager.get_encrypted_token(session_id)
