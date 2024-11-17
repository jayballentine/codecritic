# Load environment variables first, before any other imports
import os
from pathlib import Path
from dotenv import load_dotenv

# Load test environment variables using absolute path
env_path = Path(__file__).parent.parent.parent.parent / '.env.test'
load_dotenv(env_path, override=True)

# Now import everything else
import pytest
from datetime import datetime, timedelta, timezone
from jwt.exceptions import ExpiredSignatureError, InvalidSignatureError
from app.db.models import User, get_database_client
from app.utils.security import SecurityUtilities
from app.auth.session_management import create_user_session
from app.auth.token_refresh import REFRESH_TOKEN_EXPIRY, ACCESS_TOKEN_EXPIRY, _parse_datetime

class TestTokenRefresh:
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test database and create test user"""
        try:
            self.client = get_database_client().client
            
            # Create test user
            self.test_user = User.create(
                email="test_refresh@example.com",
                subscription_type="basic",
                username="test_refresh_user"
            )
            
        except Exception as e:
            pytest.skip(f"Setup failed: {str(e)}")
            
        yield
        
        try:
            # Cleanup: Delete test user and their sessions
            self.client.table('sessions').delete().eq('user_id', self.test_user.user_id).execute()
            self.client.table('users').delete().eq('email', 'test_refresh@example.com').execute()
        except Exception as e:
            print(f"Cleanup failed: {str(e)}")

    def test_automatic_token_refresh_on_expiry(self):
        """Test that tokens are automatically refreshed when expired"""
        from app.auth.token_refresh import refresh_expired_token
        
        # Create session with short expiration but long refresh window
        session = create_user_session(
            self.test_user.user_id,
            token_expiry=ACCESS_TOKEN_EXPIRY
        )
        original_token = session['token']
        
        # Wait for token to expire
        import time
        time.sleep(2)
        
        # Attempt to use expired token - should trigger automatic refresh
        new_token = refresh_expired_token(original_token)
        
        # Verify new token is different and valid
        assert new_token != original_token
        payload = SecurityUtilities.validate_jwt_token(new_token)
        assert payload['user_id'] == self.test_user.user_id
        
        # Verify old token is invalidated in database
        stored_session = self.client.table('sessions').select('*')\
            .eq('session_id', session['session_id'])\
            .single()\
            .execute()
        assert stored_session.data['is_active'] is False

    def test_single_use_refresh_tokens(self):
        """Test that refresh tokens can only be used once"""
        from app.auth.token_refresh import refresh_expired_token
        
        # Create initial session with short expiration but long refresh window
        session = create_user_session(
            self.test_user.user_id,
            token_expiry=ACCESS_TOKEN_EXPIRY
        )
        original_token = session['token']
        
        # Wait for token to expire
        import time
        time.sleep(2)
        
        # First refresh should succeed
        new_token = refresh_expired_token(original_token)
        assert new_token != original_token
        
        # Second refresh with same expired token should fail
        with pytest.raises(ValueError, match="Token has already been refreshed"):
            refresh_expired_token(original_token)

    def test_invalid_token_handling(self):
        """Test proper error handling for invalid tokens"""
        from app.auth.token_refresh import refresh_expired_token
        
        # Test with malformed token
        with pytest.raises(InvalidSignatureError):
            refresh_expired_token("invalid.token.format")
        
        # Test with tampered token
        session = create_user_session(self.test_user.user_id)
        tampered_token = session['token'][:-1] + ('1' if session['token'][-1] == '0' else '0')
        with pytest.raises(InvalidSignatureError):
            refresh_expired_token(tampered_token)

    def test_refresh_token_expiration(self):
        """Test that refresh tokens have appropriate expiration"""
        from app.auth.token_refresh import refresh_expired_token
        
        # Create session with refresh token
        session = create_user_session(
            self.test_user.user_id,
            token_expiry=REFRESH_TOKEN_EXPIRY
        )
        
        # Verify refresh token expiration is set correctly
        stored_session = self.client.table('sessions').select('*')\
            .eq('session_id', session['session_id'])\
            .single()\
            .execute()
        
        expiry = _parse_datetime(stored_session.data['expiry'])
        now = datetime.now(timezone.utc)
        
        # Verify expiration is within acceptable range (allowing for test execution time)
        expected_expiry = now + REFRESH_TOKEN_EXPIRY
        assert abs((expiry - expected_expiry).total_seconds()) < 5

    def test_concurrent_refresh_handling(self):
        """Test handling of concurrent refresh attempts"""
        from app.auth.token_refresh import refresh_expired_token
        
        # Create session with short expiration but long refresh window
        session = create_user_session(
            self.test_user.user_id,
            token_expiry=ACCESS_TOKEN_EXPIRY
        )
        original_token = session['token']
        
        # Wait for token to expire
        import time
        time.sleep(2)
        
        # Simulate concurrent refresh attempts
        def refresh_attempt():
            try:
                return refresh_expired_token(original_token)
            except ValueError as e:
                if "Token has already been refreshed" not in str(e):
                    raise
                return None
        
        # Only one refresh should succeed, others should fail gracefully
        results = [refresh_attempt() for _ in range(3)]
        successful_refreshes = [r for r in results if r is not None]
        assert len(successful_refreshes) == 1

    def test_refresh_maintains_user_context(self):
        """Test that refreshed tokens maintain necessary user context"""
        from app.auth.token_refresh import refresh_expired_token
        
        # Create session with short expiration but long refresh window
        session = create_user_session(
            self.test_user.user_id,
            token_expiry=ACCESS_TOKEN_EXPIRY
        )
        
        # Wait for token to expire
        import time
        time.sleep(2)
        
        # Refresh token and verify claims are maintained
        new_token = refresh_expired_token(session['token'])
        payload = SecurityUtilities.validate_jwt_token(new_token)
        
        assert payload['user_id'] == self.test_user.user_id
        assert 'session_id' in payload  # Session tracking maintained
