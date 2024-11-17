import os
import pytest
from pathlib import Path
from dotenv import load_dotenv

from app.auth.github_oauth import GitHubOAuthService, User

def load_test_env():
    """Load test environment variables."""
    env_path = Path(__file__).parent.parent.parent.parent / '.env.test'
    if not env_path.exists():
        raise FileNotFoundError(f".env.test file not found at {env_path}")
    load_dotenv(env_path)

# Load environment variables before running tests
load_test_env()

@pytest.fixture(scope="session", autouse=True)
def print_oauth_url():
    """Print OAuth URL before running any tests (once per session)."""
    oauth_service = GitHubOAuthService()
    redirect_url = oauth_service.generate_oauth_redirect_url()
    print("\n=== GitHub OAuth Authorization ===")
    print("\nTo complete the OAuth flow test:")
    print("1. Visit this URL in your browser:")
    print(f"\n{redirect_url}\n")
    print("2. Authorize the application")
    print("3. Copy the 'code' parameter from the redirect URL")
    print("4. Update GITHUB_TEST_CODE in .env.test with this code")
    print("5. Run the tests again\n")
    print("Note: The authorization code expires quickly, so you'll need to")
    print("      generate a new one for each test run.")
    print("\n================================")
    yield

class TestGitHubOAuth:
    def setup_method(self):
        """Setup method to initialize GitHubOAuthService."""
        self.oauth_service = GitHubOAuthService()

    def test_github_oauth_redirect(self):
        """Test GitHub OAuth redirect URL generation."""
        redirect_url = self.oauth_service.generate_oauth_redirect_url()
        
        assert redirect_url is not None
        assert 'https://github.com/login/oauth/authorize' in redirect_url
        assert f'client_id={self.oauth_service.client_id}' in redirect_url
        assert 'scope=user%3Aemail' in redirect_url

    def test_missing_credentials(self):
        """Test error handling for missing OAuth credentials."""
        # Temporarily unset environment variables
        client_id = os.environ.pop('GITHUB_CLIENT_ID', None)
        client_secret = os.environ.pop('GITHUB_CLIENT_SECRET', None)
        redirect_uri = os.environ.pop('GITHUB_REDIRECT_URI', None)

        try:
            with pytest.raises(ValueError, match="GitHub OAuth credentials must be set"):
                GitHubOAuthService()
        finally:
            # Restore environment variables
            if client_id:
                os.environ['GITHUB_CLIENT_ID'] = client_id
            if client_secret:
                os.environ['GITHUB_CLIENT_SECRET'] = client_secret
            if redirect_uri:
                os.environ['GITHUB_REDIRECT_URI'] = redirect_uri

    def test_invalid_code_error(self):
        """Test error handling for invalid authorization code."""
        with pytest.raises(ValueError):
            self.oauth_service.exchange_code_for_token('')

    def test_invalid_token_error(self):
        """Test error handling for invalid access token."""
        with pytest.raises(ValueError, match="Access token is required"):
            self.oauth_service.get_user_details('')

    def test_invalid_user_details_error(self):
        """Test error handling for invalid user details."""
        with pytest.raises(ValueError, match="Invalid user details"):
            self.oauth_service.create_or_update_user({})

    def test_oauth_error_handling(self):
        """Test standardized OAuth error handling."""
        error_data = {
            'error': 'access_denied',
            'description': 'The user denied access to the application'
        }
        error_response = self.oauth_service.handle_oauth_error(error_data)
        
        assert error_response['error'] == 'access_denied'
        assert error_response['error_description'] == 'The user denied access to the application'

    def test_github_oauth_flow(self):
        """
        Test complete GitHub OAuth authentication flow.
        Uses actual GitHub credentials from environment variables.
        """
        # Get authorization code from environment
        code = os.getenv('GITHUB_TEST_CODE')
        if not code:
            pytest.skip("No GitHub test authorization code provided. See the instructions above to get one.")

        try:
            # Exchange code for token
            token_response = self.oauth_service.exchange_code_for_token(code)
        except ValueError as e:
            if "incorrect or expired" in str(e):
                pytest.skip("GitHub authorization code has expired. Please generate a new one.")
            raise

        assert 'access_token' in token_response
        
        # Get user details
        user_details = self.oauth_service.get_user_details(token_response['access_token'])
        assert user_details.get('username')
        assert user_details.get('email')
        
        # Create user
        user = self.oauth_service.create_or_update_user(user_details)
        assert isinstance(user, User)
        assert user.username == user_details['username']
        assert user.email == user_details['email']
