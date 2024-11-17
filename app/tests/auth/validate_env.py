import os
from pathlib import Path
from dotenv import load_dotenv

def validate_github_oauth_env():
    """
    Validate GitHub OAuth environment variables.
    Returns a tuple of (is_valid: bool, missing_vars: list, placeholder_vars: list)
    """
    # Load .env.test file
    env_path = Path(__file__).parent.parent.parent.parent / '.env.test'
    if not env_path.exists():
        return False, ['.env.test file not found'], []
    
    load_dotenv(env_path)
    
    # Required variables
    required_vars = [
        'GITHUB_CLIENT_ID',
        'GITHUB_CLIENT_SECRET',
        'GITHUB_REDIRECT_URI'
    ]
    
    # Optional for full test
    optional_vars = ['GITHUB_TEST_CODE']
    
    # Check for missing variables
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    # Check for placeholder values
    placeholder_values = [
        'your_test_client_id',
        'your_test_client_secret',
        'your_test_authorization_code'
    ]
    placeholder_vars = [
        var for var in required_vars + optional_vars
        if os.getenv(var) in placeholder_values
    ]
    
    is_valid = not missing_vars and not placeholder_vars
    return is_valid, missing_vars, placeholder_vars

if __name__ == '__main__':
    is_valid, missing_vars, placeholder_vars = validate_github_oauth_env()
    
    print("\nGitHub OAuth Environment Validation")
    print("==================================")
    
    if is_valid:
        print("✅ All required environment variables are properly set")
    else:
        if missing_vars:
            print("\n❌ Missing required environment variables:")
            for var in missing_vars:
                print(f"   - {var}")
        
        if placeholder_vars:
            print("\n❌ Environment variables with placeholder values:")
            for var in placeholder_vars:
                print(f"   - {var}")
        
        print("\n📝 Instructions:")
        print("1. Open .env.test file")
        print("2. Follow the instructions to create a GitHub OAuth App")
        print("3. Fill in the required credentials")
        print("4. For testing the full OAuth flow:")
        print("   - Run the tests to get the authorization URL")
        print("   - Visit the URL and authorize the app")
        print("   - Copy the 'code' parameter from the redirect URL")
        print("   - Update GITHUB_TEST_CODE in .env.test")
