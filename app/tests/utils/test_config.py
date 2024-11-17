import os
import pytest
from dotenv import load_dotenv

from app.utils.config import get_environment, get_config

def test_load_environment_variables():
    """Test that environment variables can be loaded from .env.example"""
    # Load .env.example
    load_dotenv('.env.example')
    
    # Check specific environment variables
    assert get_config('SUPABASE_URL') is not None, "SUPABASE_URL should be set"
    assert get_config('SUPABASE_KEY') is not None, "SUPABASE_KEY should be set"
    assert get_config('GITHUB_CLIENT_ID') is not None, "GITHUB_CLIENT_ID should be set"
    assert get_config('GITHUB_CLIENT_SECRET') is not None, "GITHUB_CLIENT_SECRET should be set"
    assert get_config('SENDGRID_API_KEY') is not None, "SENDGRID_API_KEY should be set"

def test_missing_variables():
    """Test handling of missing environment variables"""
    # Store original values
    original_vars = {
        'SUPABASE_URL': os.environ.get('SUPABASE_URL'),
        'GITHUB_CLIENT_ID': os.environ.get('GITHUB_CLIENT_ID')
    }
    
    try:
        # Remove variables temporarily
        for var in original_vars:
            if var in os.environ:
                del os.environ[var]
        
        # Test missing variables return None
        assert get_config('SUPABASE_URL') is None, "Missing variable should return None"
        assert get_config('GITHUB_CLIENT_ID') is None, "Missing variable should return None"
        
        # Test default values
        assert get_config('SUPABASE_URL', 'default') == 'default', "Should return default value"
        assert get_config('GITHUB_CLIENT_ID', 'default') == 'default', "Should return default value"
    
    finally:
        # Restore original values
        for var, value in original_vars.items():
            if value is not None:
                os.environ[var] = value

def test_environment_detection():
    """Test environment detection"""
    # Store original environment
    original_env = os.environ.get('ENVIRONMENT')
    
    try:
        # Test default environment
        if 'ENVIRONMENT' in os.environ:
            del os.environ['ENVIRONMENT']
        assert get_environment() == 'development', "Default environment should be development"
        
        # Test explicit environments
        test_envs = ['development', 'production', 'staging']
        for env in test_envs:
            os.environ['ENVIRONMENT'] = env
            assert get_environment() == env, f"Should detect {env} environment"
    
    finally:
        # Restore original environment
        if original_env is not None:
            os.environ['ENVIRONMENT'] = original_env
        elif 'ENVIRONMENT' in os.environ:
            del os.environ['ENVIRONMENT']
