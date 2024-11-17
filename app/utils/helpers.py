import re

def validate_email(email: str) -> bool:
    """
    Validate an email address format.
    
    Args:
        email (str): Email address to validate
    
    Returns:
        bool: True if email is valid, False otherwise
    """
    if not isinstance(email, str):
        return False
    
    # Regex pattern for email validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    return bool(re.match(email_pattern, email))

def format_api_response(success: bool = False, data: dict = None, error: str = None) -> dict:
    """
    Format a standardized API response.
    
    Args:
        success (bool, optional): Indicates if the API call was successful. Defaults to False.
        data (dict, optional): Response data payload. Defaults to None.
        error (str, optional): Error message if the call was unsuccessful. Defaults to None.
    
    Returns:
        dict: Standardized API response dictionary
    """
    return {
        "success": success,
        "data": data,
        "error": error
    }
