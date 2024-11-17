import os
import pytest
import tempfile
import zipfile
from app.intake.input_validation import InputValidator, ValidationError

class TestInputValidator:
    def setup_method(self):
        """Setup test environment before each test"""
        self.free_validator = InputValidator("free")
        self.paid_validator = InputValidator("paid")
        
        # Test repositories
        self.public_repo = "https://github.com/torvalds/linux"
        self.private_repo = "https://github.com/private-org/private-repo"
    
    def test_input_type_detection(self):
        """Test correct detection of input types"""
        assert self.free_validator._is_github_url("https://github.com/user/repo")
        assert not self.free_validator._is_github_url("https://gitlab.com/user/repo")
        
        with tempfile.NamedTemporaryFile(suffix='.zip') as tf:
            assert self.free_validator._is_zip_file(tf.name)
        assert not self.free_validator._is_zip_file("not_a_zip.txt")
    
    def test_github_public_repo_validation(self):
        """Test validation of public GitHub repository"""
        result = self.free_validator.validate_input(self.public_repo)
        assert result['is_valid']
        assert result['type'] == 'github'
        assert not result['is_private']
    
    def test_github_rate_limit_handling(self):
        """Test handling of GitHub API rate limits"""
        # Make multiple rapid requests to trigger rate limiting
        results = []
        for _ in range(5):
            try:
                result = self.free_validator.validate_input(self.public_repo)
                results.append(result)
            except ValidationError as e:
                assert 'rate limit' in str(e).lower()
                return
        
        # If we didn't hit rate limit, at least verify all requests were valid
        assert all(r['is_valid'] for r in results)
    
    def test_subscription_tier_restrictions(self):
        """Test subscription tier access restrictions"""
        # Free tier should not access private repos
        with pytest.raises(ValidationError) as exc_info:
            self.free_validator.validate_input(self.private_repo)
        assert 'subscription' in str(exc_info.value).lower()
        
        # Paid tier should access private repos
        try:
            result = self.paid_validator.validate_input(self.private_repo)
            assert result['is_valid']
            assert result['is_private']
        except ValidationError as e:
            if 'rate limit' in str(e).lower():
                pytest.skip("Rate limit reached")
    
    def test_zip_file_validation(self):
        """Test ZIP file validation"""
        # Create a valid test ZIP file
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tf:
            with zipfile.ZipFile(tf.name, 'w') as zf:
                zf.writestr('test.txt', 'test content')
            
            try:
                result = self.free_validator.validate_input(tf.name)
                assert result['is_valid']
                assert result['type'] == 'zip'
                assert len(result['files']) == 1
            finally:
                os.unlink(tf.name)
    
    def test_zip_file_size_limits(self):
        """Test ZIP file size restrictions"""
        # Create a ZIP file that exceeds free tier limits
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tf:
            with zipfile.ZipFile(tf.name, 'w') as zf:
                # Create a large file
                large_content = 'x' * (6 * 1024 * 1024)  # 6MB file
                zf.writestr('large.txt', large_content)
            
            try:
                with pytest.raises(ValidationError) as exc_info:
                    self.free_validator.validate_input(tf.name)
                assert 'file size' in str(exc_info.value).lower()
            finally:
                os.unlink(tf.name)
    
    def test_zip_security_checks(self):
        """Test ZIP security validations"""
        # Test path traversal attempt
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tf:
            with zipfile.ZipFile(tf.name, 'w') as zf:
                zf.writestr('../outside.txt', 'malicious content')
            
            try:
                with pytest.raises(ValidationError) as exc_info:
                    self.free_validator.validate_input(tf.name)
                assert 'path traversal' in str(exc_info.value).lower()
            finally:
                os.unlink(tf.name)
    
    def test_invalid_input_handling(self):
        """Test handling of invalid inputs"""
        invalid_inputs = [
            None,
            "",
            "not_a_url_or_zip",
            "https://not-github.com/user/repo",
            "file.txt"
        ]
        
        for invalid_input in invalid_inputs:
            with pytest.raises(ValidationError) as exc_info:
                self.free_validator.validate_input(invalid_input)
            assert 'invalid input' in str(exc_info.value).lower()
