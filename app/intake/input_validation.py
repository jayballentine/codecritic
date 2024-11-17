import os
import re
import zipfile
from urllib.parse import urlparse
import requests
import time

class ValidationError(Exception):
    """Custom exception for validation errors"""
    def __init__(self, error_type, message, details=None):
        self.error_type = error_type
        self.message = message
        self.details = details
        super().__init__(message)

class InputValidator:
    """Unified validator for all input types"""
    
    # Constants for validation
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    MAX_FREE_TIER_FILES = 50
    MAX_PAID_TIER_FILES = 200
    GITHUB_API_BASE = "https://api.github.com"
    
    def __init__(self, subscription_tier):
        """Initialize validator with subscription tier"""
        self.subscription_tier = subscription_tier
        self.max_files = (self.MAX_PAID_TIER_FILES if subscription_tier == "paid" 
                         else self.MAX_FREE_TIER_FILES)
    
    def validate_input(self, input_data):
        """
        Single entry point for all input validation
        
        Args:
            input_data: Either a GitHub URL or path to ZIP file
            
        Returns:
            dict: Validation result containing status and metadata
            
        Raises:
            ValidationError: If validation fails
        """
        if not input_data:
            raise ValidationError("invalid_input", "Invalid input: Input data cannot be empty")
            
        if self._is_github_url(input_data):
            return self._validate_github_submission(input_data)
        elif self._is_zip_file(input_data):
            return self._validate_zip_submission(input_data)
        else:
            raise ValidationError("invalid_input", "Invalid input: Must be a GitHub URL or ZIP file")
    
    def _is_github_url(self, input_data):
        """Check if input is a GitHub URL"""
        if not isinstance(input_data, str):
            return False
        
        try:
            parsed = urlparse(input_data.lower().rstrip('/'))
            return parsed.netloc in ['github.com', 'www.github.com']
        except:
            return False
    
    def _is_zip_file(self, input_data):
        """Check if input is a ZIP file"""
        if not isinstance(input_data, str):
            return False
        
        return os.path.isfile(input_data) and input_data.lower().endswith('.zip')
    
    def _validate_github_submission(self, url):
        """
        Validate GitHub repository URL and check access
        
        Args:
            url: GitHub repository URL
            
        Returns:
            dict: Validation result
            
        Raises:
            ValidationError: If validation fails
        """
        # Basic URL validation
        parsed_url = urlparse(url)
        path_parts = [part for part in parsed_url.path.strip('/').split('/') if part]
        
        if len(path_parts) < 2:
            raise ValidationError("invalid_github_url", 
                                "Invalid input: Invalid GitHub repository URL format")
        
        # Convert URL to API endpoint
        owner, repo = path_parts[:2]
        api_url = f"{self.GITHUB_API_BASE}/repos/{owner}/{repo}"
        
        # Check repository access
        try:
            # First try without authentication to check if repo exists and is public
            response = requests.get(api_url)
            
            # Handle rate limiting
            if response.status_code == 403 and 'X-RateLimit-Remaining' in response.headers:
                if response.headers['X-RateLimit-Remaining'] == '0':
                    reset_time = int(response.headers['X-RateLimit-Reset'])
                    wait_time = max(reset_time - int(time.time()), 0)
                    raise ValidationError("rate_limit", 
                                       f"Rate limit exceeded. Reset in {wait_time} seconds")
            
            # If repo is not found with unauthenticated request, it might be private
            if response.status_code == 404:
                # For free tier, we don't even try to access private repos
                if self.subscription_tier != "paid":
                    raise ValidationError("subscription_required", 
                                       "Subscription required: Private repositories require paid subscription")
                
                # For paid tier, we would try with authentication here
                # For now, just raise not found error
                raise ValidationError("repo_not_found", 
                                   "Invalid input: Repository not found or access denied")
            
            # If we get here, the repo exists and is public
            repo_data = response.json()
            is_private = repo_data.get('private', False)
            
            # Double check subscription for private repos
            if is_private and self.subscription_tier != "paid":
                raise ValidationError("subscription_required", 
                                   "Subscription required: Private repositories require paid subscription")
            
            return {
                'is_valid': True,
                'type': 'github',
                'is_private': is_private,
                'owner': owner,
                'repo': repo
            }
            
        except requests.RequestException as e:
            raise ValidationError("github_api_error", 
                               f"Invalid input: Error accessing GitHub API: {str(e)}")
    
    def _validate_zip_submission(self, zip_path):
        """
        Validate ZIP file submission
        
        Args:
            zip_path: Path to ZIP file
            
        Returns:
            dict: Validation result
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # Check ZIP integrity
                bad_file = zf.testzip()
                if bad_file:
                    raise ValidationError("corrupt_zip", 
                                       f"Invalid input: Corrupted ZIP file: {bad_file}")
                
                # Get file list
                files = [f for f in zf.namelist() if not f.endswith('/')]
                
                # Check number of files
                if len(files) > self.max_files:
                    raise ValidationError("too_many_files",
                                       f"Invalid input: ZIP contains too many files (max {self.max_files})")
                
                # Check for path traversal
                for file_path in files:
                    if os.path.isabs(file_path) or '..' in file_path:
                        raise ValidationError("path_traversal",
                                           "Invalid input: Detected potential path traversal attempt")
                
                # Check file sizes
                for file_info in zf.infolist():
                    if file_info.file_size > self.MAX_FILE_SIZE:
                        raise ValidationError("file_size_exceeded",
                                           f"File size exceeded: {file_info.filename} exceeds size limit")
                
                return {
                    'is_valid': True,
                    'type': 'zip',
                    'files': files,
                    'total_size': sum(f.file_size for f in zf.infolist())
                }
                
        except zipfile.BadZipFile:
            raise ValidationError("invalid_zip", "Invalid input: Invalid or corrupted ZIP file")
        except Exception as e:
            if not isinstance(e, ValidationError):
                raise ValidationError("zip_processing_error", 
                                   f"Invalid input: Error processing ZIP file: {str(e)}")
            raise
