import os
import re
import json
import traceback
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import pytest
from app.db.models import User, get_database_client
from app.utils.security import SecurityUtilities
from app.utils.config import get_config

# Load environment variables from .env.test
load_dotenv('.env.test', override=True)

# Ensure Supabase is enabled
os.environ['USE_SUPABASE'] = 'true'

# SQL Schema definitions
USERS_TABLE_SQL = """
create table if not exists users (
    user_id bigint primary key generated always as identity,
    email text unique not null,
    username text,
    subscription_type text not null,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

create index if not exists idx_users_email on users(email);
create index if not exists idx_users_username on users(username);

alter table users
    add constraint check_subscription_type
    check (subscription_type in ('basic', 'premium', 'enterprise'));
"""

SESSIONS_TABLE_SQL = """
create table if not exists sessions (
    session_id uuid primary key,
    user_id bigint references users(user_id) not null,
    token text not null,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    expiry timestamp with time zone not null,
    is_active boolean default true not null
);

create index if not exists idx_sessions_user_id on sessions(user_id);
create index if not exists idx_sessions_active_user on sessions(user_id, is_active);
create index if not exists idx_sessions_expiry on sessions(expiry);

alter table sessions
    add constraint fk_sessions_user
    foreign key (user_id)
    references users(user_id)
    on delete cascade;
"""

class TestSessionManagement:
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test database and create test user"""
        try:
            # Verify Supabase configuration
            supabase_url = get_config('SUPABASE_URL')
            supabase_key = get_config('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                pytest.skip("Supabase configuration not found")
            
            self.client = get_database_client().client
            
            # Create test user
            try:
                # First check if users table exists by attempting to select from it
                try:
                    self.client.table('users').select('*').limit(1).execute()
                    print("Users table exists")
                except Exception as e:
                    print(f"Users table doesn't exist, error: {str(e)}")
                    print_schema_instructions()
                    pytest.skip("Database tables need to be created. See instructions above.")

                # Check if sessions table exists
                try:
                    self.client.table('sessions').select('*').limit(1).execute()
                    print("Sessions table exists")
                except Exception as e:
                    print(f"Sessions table doesn't exist, error: {str(e)}")
                    print_schema_instructions()
                    pytest.skip("Database tables need to be created. See instructions above.")

                self.test_user = User.create(
                    email="test@example.com",
                    subscription_type="basic",
                    username="testuser"
                )
                print("Test user created successfully")
            except Exception as user_error:
                print(f"Failed to create test user: {str(user_error)}")
                traceback.print_exc()
                pytest.skip(f"Failed to create test user: {str(user_error)}")
            
        except Exception as e:
            print(f"Setup failed with error: {str(e)}")
            traceback.print_exc()
            pytest.skip(str(e))
            
        yield
        
        try:
            # Cleanup: Delete test user and their sessions
            self.client.table('sessions').delete().eq('user_id', self.test_user.user_id).execute()
            self.client.table('users').delete().eq('email', 'test@example.com').execute()
        except Exception as e:
            print(f"Cleanup failed: {str(e)}")

    def test_create_session_after_login(self):
        """Test that a session is created after successful login"""
        try:
            from app.auth.session_management import create_user_session
            
            session = create_user_session(self.test_user.user_id)
            
            # Verify session was created
            stored_session = self.client.table('sessions').select('*')\
                .eq('user_id', self.test_user.user_id)\
                .execute()
            
            assert stored_session.data
            assert stored_session.data[0]['user_id'] == self.test_user.user_id
            assert stored_session.data[0]['token'] is not None
            assert stored_session.data[0]['is_active'] is True
        except Exception as e:
            pytest.fail(f"Session creation test failed: {str(e)}")

    def test_token_encryption(self):
        """Test that tokens are properly encrypted when stored"""
        try:
            from app.auth.session_management import create_user_session, get_encrypted_token
            
            session = create_user_session(self.test_user.user_id)
            stored_token = get_encrypted_token(session['session_id'])
            
            # Verify token is encrypted (not plaintext JWT)
            assert not stored_token.startswith('eyJ')  # JWT tokens start with 'eyJ'
            assert len(stored_token) > 0
        except Exception as e:
            pytest.fail(f"Token encryption test failed: {str(e)}")

    def test_token_invalidation_on_logout(self):
        """Test that tokens are properly invalidated on logout"""
        try:
            from app.auth.session_management import create_user_session, logout_user
            
            session = create_user_session(self.test_user.user_id)
            logout_user(self.test_user.user_id)
            
            # Verify session is marked as inactive
            stored_session = self.client.table('sessions').select('*')\
                .eq('user_id', self.test_user.user_id)\
                .execute()
            
            assert stored_session.data[0]['is_active'] is False
        except Exception as e:
            pytest.fail(f"Logout test failed: {str(e)}")

    def test_token_expiration_and_refresh(self):
        """Test token expiration and refresh process"""
        try:
            from app.auth.session_management import create_user_session, refresh_session
            
            # Create session with short expiration
            session = create_user_session(
                self.test_user.user_id,
                token_expiry=timedelta(seconds=1)
            )
            
            # Wait for token to expire
            import time
            time.sleep(2)
            
            # Attempt to refresh expired token
            new_session = refresh_session(session['session_id'])
            
            assert new_session['token'] != session['token']
            assert new_session['expiry'] > datetime.now(timezone.utc)
        except Exception as e:
            pytest.fail(f"Token refresh test failed: {str(e)}")

    def test_multiple_active_sessions(self):
        """Test handling multiple active sessions for same user"""
        try:
            from app.auth.session_management import create_user_session, get_active_sessions
            
            # Create multiple sessions
            session1 = create_user_session(self.test_user.user_id)
            session2 = create_user_session(self.test_user.user_id)
            
            active_sessions = get_active_sessions(self.test_user.user_id)
            
            assert len(active_sessions) == 2
            assert any(s['session_id'] == session1['session_id'] for s in active_sessions)
            assert any(s['session_id'] == session2['session_id'] for s in active_sessions)
        except Exception as e:
            pytest.fail(f"Multiple sessions test failed: {str(e)}")

    def test_session_validation(self):
        """Test session validation logic"""
        try:
            from app.auth.session_management import create_user_session, validate_session
            
            session = create_user_session(self.test_user.user_id)
            
            # Test valid session
            assert validate_session(session['session_id']) is True
            
            # Test invalid session
            assert validate_session('nonexistent-session-id') is False
        except Exception as e:
            pytest.fail(f"Session validation test failed: {str(e)}")

def print_schema_instructions():
    """Print instructions for creating database tables"""
    print("\nTo set up the database, please execute the following SQL in your Supabase SQL editor:")
    print("\n=== First, create the users table ===")
    print(USERS_TABLE_SQL)
    print("\n=== Then, create the sessions table ===")
    print(SESSIONS_TABLE_SQL)
    print("\nAfter creating these tables, run the tests again.")
