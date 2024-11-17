import os
import pytest
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from .env.example
load_dotenv('.env.example')

@pytest.mark.skipif(
    os.getenv('ENVIRONMENT') == 'test',
    reason="Skip Supabase connection test in test environment"
)
def test_supabase_connection():
    """
    Test Supabase connection by validating URL and key
    
    This test will:
    1. Retrieve Supabase URL and key
    2. Verify they are non-empty and follow expected format
    3. Attempt to create a Supabase client
    """
    # Skip if we're in test environment
    if os.getenv('ENVIRONMENT') == 'test':
        pytest.skip("Skipping Supabase connection test in test environment")
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    # Validate Supabase URL
    assert supabase_url, "SUPABASE_URL is not set in environment"
    assert supabase_url.startswith('https://'), "Invalid Supabase URL format"
    assert '.supabase.co' in supabase_url, "Invalid Supabase URL domain"
    
    # Validate Supabase key
    assert supabase_key, "SUPABASE_KEY is not set in environment"
    assert len(supabase_key) > 50, "Supabase key seems too short"
    
    # Attempt to create Supabase client
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Verify client can be created
        assert supabase is not None, "Failed to create Supabase client"
        
        # Note: Actual authentication requires a valid access token or service role
        # This is just a basic connectivity test
    except Exception as e:
        pytest.fail(f"Supabase client creation failed: {str(e)}")
