import pytest

class TestHelpers:
    def test_validate_email_valid_formats(self):
        """
        Test various valid email formats to ensure they pass validation.
        """
        from app.utils.helpers import validate_email  # Assumed function

        valid_emails = [
            'user@example.com',
            'firstname.lastname@example.com',
            'user+tag@example.com',
            'user123@example.co.uk',
            'user-name@example.org',
            'user_name@example.net',
            'user@subdomain.example.com',
        ]

        for email in valid_emails:
            assert validate_email(email) is True, f"Failed to validate valid email: {email}"

    def test_validate_email_invalid_formats(self):
        """
        Test various invalid email formats to ensure they fail validation.
        """
        from app.utils.helpers import validate_email  # Assumed function

        invalid_emails = [
            'invalid.email',
            'invalid@email',
            '@invalid.com',
            'user@.com',
            'user@example.',
            'user@example,com',
            'user name@example.com',
            'user@example com',
            '',
            None,
        ]

        for email in invalid_emails:
            assert validate_email(email) is False, f"Incorrectly validated invalid email: {email}"

    def test_format_api_response_success(self):
        """
        Test JSON response formatting for successful API responses.
        """
        from app.utils.helpers import format_api_response  # Assumed function

        # Test successful response with data
        data = {"user_id": 1, "username": "testuser"}
        response = format_api_response(success=True, data=data)
        
        assert response == {
            "success": True,
            "data": data,
            "error": None
        }

    def test_format_api_response_failure(self):
        """
        Test JSON response formatting for failed API responses.
        """
        from app.utils.helpers import format_api_response  # Assumed function

        # Test failed response with error message
        error_msg = "Authentication failed"
        response = format_api_response(success=False, error=error_msg)
        
        assert response == {
            "success": False,
            "data": None,
            "error": error_msg
        }

    def test_format_api_response_default_values(self):
        """
        Test JSON response formatting with default/empty values.
        """
        from app.utils.helpers import format_api_response  # Assumed function

        # Test response with default values
        response = format_api_response()
        
        assert response == {
            "success": False,
            "data": None,
            "error": None
        }
