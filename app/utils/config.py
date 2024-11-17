import os
from typing import Optional, Dict, Any

def validate_config():
    """
    Validate critical environment variables.
    Raises ValueError if any critical variables are missing.
    """
    critical_vars = [
        'SUPABASE_URL', 
        'SUPABASE_KEY', 
        'GITHUB_CLIENT_ID', 
        'GITHUB_CLIENT_SECRET', 
        'SENDGRID_API_KEY'
    ]
    
    for var in critical_vars:
        if not os.getenv(var):
            raise ValueError(f"Missing required environment variable: {var}")

def get_environment() -> str:
    """
    Detect and return the current environment.
    Defaults to 'development' if not specified.
    """
    return os.getenv('ENVIRONMENT', 'development')

def get_config(key: Optional[str] = None, default: Optional[str] = None) -> Any:
    """
    Retrieve a configuration value from environment variables.
    Supports both Supabase and traditional PostgreSQL configurations.
    
    :param key: Optional environment variable key to retrieve
    :param default: Optional default value if the key is not found
    :return: The value of the environment variable, default, or a config dictionary
    """
    # Check if Supabase configuration is preferred
    if os.getenv('USE_SUPABASE', 'true').lower() == 'true':
        if key is None:
            return {
                'SUPABASE_URL': os.getenv('SUPABASE_URL'),
                'SUPABASE_KEY': os.getenv('SUPABASE_KEY')
            }
        elif key in ['SUPABASE_URL', 'SUPABASE_KEY']:
            return os.getenv(key, default)
    
    # Fallback to traditional PostgreSQL configuration
    if key is None:
        return {
            'DB_HOST': os.getenv('DB_HOST', 'localhost'),
            'DB_PORT': os.getenv('DB_PORT', '5432'),
            'DB_USERNAME': os.getenv('DB_USERNAME', 'testuser'),
            'DB_PASSWORD': os.getenv('DB_PASSWORD', 'testpass'),
            'DB_NAME': os.getenv('DB_NAME', 'testdb')
        }
    
    return os.getenv(key, default)

def is_supabase_enabled() -> bool:
    """
    Check if Supabase is the preferred database configuration.
    
    :return: Boolean indicating Supabase usage
    """
    return os.getenv('USE_SUPABASE', 'true').lower() == 'true'
