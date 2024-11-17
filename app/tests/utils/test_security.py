import unittest
from datetime import datetime, timedelta
from app.utils.security import SecurityUtilities

class TestSecurityUtilities(unittest.TestCase):
    def setUp(self):
        """Set up test cases"""
        self.test_password = "secure_password_123!"
        self.test_payload = {
            'user_id': '12345',
            'email': 'test@example.com'
        }

    def test_password_hashing_and_validation(self):
        """Test password hashing and validation"""
        # Hash the password
        hashed_password = SecurityUtilities.hash_password(self.test_password)
        
        # Verify it's a string (decoded from bytes)
        self.assertIsInstance(hashed_password, str)
        
        # Verify correct password validates
        self.assertTrue(
            SecurityUtilities.validate_password(self.test_password, hashed_password),
            "Password validation should succeed for correct password"
        )
        
        # Verify incorrect password fails
        self.assertFalse(
            SecurityUtilities.validate_password("wrong_password", hashed_password),
            "Password validation should fail for incorrect password"
        )

    def test_jwt_token_generation_and_validation(self):
        """Test JWT token generation and validation"""
        # Generate token
        token = SecurityUtilities.generate_jwt_token(self.test_payload)
        
        # Verify token is a string
        self.assertIsInstance(token, str)
        
        # Validate token and verify payload
        decoded_payload = SecurityUtilities.validate_jwt_token(token)
        self.assertEqual(decoded_payload['user_id'], self.test_payload['user_id'])
        self.assertEqual(decoded_payload['email'], self.test_payload['email'])

    def test_jwt_token_expiration(self):
        """Test JWT token expiration"""
        from jwt import ExpiredSignatureError
        
        # Generate a token that expires immediately
        token = SecurityUtilities.generate_jwt_token(
            self.test_payload,
            expires_delta=timedelta(seconds=-1)
        )
        
        # Verify expired token raises ExpiredSignatureError
        with self.assertRaises(
            ExpiredSignatureError,
            msg="Expired token should raise ExpiredSignatureError"
        ):
            SecurityUtilities.validate_jwt_token(token)

if __name__ == '__main__':
    unittest.main()
