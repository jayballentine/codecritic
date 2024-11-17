import os
from datetime import datetime, timedelta
import bcrypt
import jwt
from jwt.exceptions import PyJWTError, ExpiredSignatureError, InvalidSignatureError

class SecurityUtilities:
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password (str): Plain text password to hash
        
        Returns:
            str: Hashed password
        """
        # Generate a salt and hash the password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def validate_password(plain_password: str, hashed_password: str) -> bool:
        """
        Validate a password against its hash.
        
        Args:
            plain_password (str): Plain text password to validate
            hashed_password (str): Stored hashed password
        
        Returns:
            bool: True if password is correct, False otherwise
        """
        return bcrypt.checkpw(
            plain_password.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )

    @staticmethod
    def generate_jwt_token(payload: dict, expires_delta: timedelta = None) -> str:
        """
        Generate a JWT token.
        
        Args:
            payload (dict): Data to encode in the token
            expires_delta (timedelta, optional): Token expiration time
        
        Returns:
            str: JWT token
        """
        # Get JWT secret from environment variable, with a fallback for testing
        jwt_secret = os.getenv('JWT_SECRET_KEY', 'fallback_secret_for_testing')
        
        # Set default expiration to 1 hour if not provided
        if expires_delta is None:
            expires_delta = timedelta(hours=1)
        
        # Add expiration to payload
        to_encode = payload.copy()
        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire})
        
        # Encode token
        encoded_jwt = jwt.encode(
            to_encode, 
            jwt_secret, 
            algorithm="HS256"
        )
        
        return encoded_jwt

    @staticmethod
    def validate_jwt_token(token: str) -> dict:
        """
        Validate a JWT token and return its payload.
        
        Args:
            token (str): JWT token to validate
        
        Returns:
            dict: Decoded token payload
        
        Raises:
            ExpiredSignatureError: If the token has expired
            InvalidSignatureError: If the token signature is invalid
            PyJWTError: For other JWT-related errors
        """
        # Get JWT secret from environment variable, with a fallback for testing
        jwt_secret = os.getenv('JWT_SECRET_KEY', 'fallback_secret_for_testing')
        
        try:
            # Decode and validate the token
            payload = jwt.decode(
                token, 
                jwt_secret, 
                algorithms=["HS256"]
            )
            return payload
        except ExpiredSignatureError:
            # Specific handling for expired tokens
            raise
        except InvalidSignatureError:
            # Specific handling for invalid signatures
            raise
        except PyJWTError as e:
            # Catch-all for other JWT-related errors
            raise
