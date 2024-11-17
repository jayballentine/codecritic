import os
import requests
from typing import Dict, Any
from urllib.parse import urlencode
from datetime import datetime

class User:
    """Simple User class for testing purposes"""
    def __init__(self, username: str, email: str, name: str = None):
        self.username = username
        self.email = email
        self.name = name

class GitHubOAuthService:
    def __init__(self):
        self.client_id = os.getenv('GITHUB_CLIENT_ID')
        self.client_secret = os.getenv('GITHUB_CLIENT_SECRET')
        self.redirect_uri = os.getenv('GITHUB_REDIRECT_URI')
        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            raise ValueError("GitHub OAuth credentials must be set in environment variables")

    def generate_oauth_redirect_url(self) -> str:
        """Generate the GitHub OAuth redirect URL for authorization."""
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': 'user:email',
            'response_type': 'code'
        }
        return f'https://github.com/login/oauth/authorize?{urlencode(params)}'

    def exchange_code_for_token(self, code: str) -> Dict[str, str]:
        """Exchange the authorization code for an access token."""
        if not code:
            raise ValueError("Authorization code is required")

        try:
            response = requests.post(
                'https://github.com/login/oauth/access_token',
                data={
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'code': code,
                    'redirect_uri': self.redirect_uri
                },
                headers={'Accept': 'application/json'},
                timeout=10
            )

            if response.status_code != 200:
                error_data = response.json() if response.text else {'error': 'Unknown error'}
                raise ValueError(f"Token exchange failed: {error_data}")

            token_data = response.json()
            if 'error' in token_data:
                raise ValueError(f"OAuth Error: {token_data.get('error_description', 'Unknown error')}")

            return token_data

        except requests.RequestException as e:
            raise ValueError(f"Failed to exchange code for token: {str(e)}")

    def get_user_details(self, access_token: str) -> Dict[str, Any]:
        """Fetch user details from GitHub using the access token."""
        if not access_token:
            raise ValueError("Access token is required")

        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/vnd.github.v3+json'
            }

            # Get user profile
            user_response = requests.get(
                'https://api.github.com/user',
                headers=headers,
                timeout=10
            )
            user_response.raise_for_status()
            user_data = user_response.json()

            # Get user emails
            email_response = requests.get(
                'https://api.github.com/user/emails',
                headers=headers,
                timeout=10
            )
            email_response.raise_for_status()
            emails = email_response.json()
            primary_email = next((email['email'] for email in emails if email['primary']), None)

            return {
                'username': user_data.get('login'),
                'email': primary_email or user_data.get('email'),
                'name': user_data.get('name')
            }

        except requests.RequestException as e:
            raise ValueError(f"Failed to fetch user details: {str(e)}")

    def create_or_update_user(self, user_details: Dict[str, Any]) -> User:
        """Create or update user with GitHub details."""
        if not user_details or not user_details.get('username'):
            raise ValueError("Invalid user details")

        return User(
            username=user_details['username'],
            email=user_details['email'],
            name=user_details.get('name')
        )

    def handle_oauth_error(self, error_data: Dict[str, str]) -> Dict[str, str]:
        """Handle and standardize OAuth error responses."""
        return {
            'error': error_data.get('error', 'unknown_error'),
            'error_description': error_data.get('description', 'An unknown OAuth error occurred')
        }
