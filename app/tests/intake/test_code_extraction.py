"""
Tests for code extraction functionality from validated inputs.
"""
import os
import pytest
import tempfile
import zipfile
from pathlib import Path
from app.intake.code_extraction import CodeExtractor

class TestCodeExtraction:
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdirname:
            yield tmpdirname
            
    @pytest.fixture
    def sample_zip(self, temp_dir):
        """Create a sample ZIP file with test code files."""
        zip_path = os.path.join(temp_dir, "test_code.zip")
        with zipfile.ZipFile(zip_path, 'w') as zf:
            # Add a Python file
            zf.writestr("test.py", "def hello(): return 'world'")
            # Add a nested JavaScript file
            zf.writestr("src/app.js", "function add(a,b) { return a + b; }")
            # Add a CSS file
            zf.writestr("styles/main.css", "body { color: blue; }")
        return zip_path
        
    def test_extract_from_zip(self, sample_zip):
        """Test extracting code files from a ZIP archive."""
        extractor = CodeExtractor()
        files = extractor.extract_from_zip(sample_zip)
        
        assert len(files) == 3
        assert any(f.path == "test.py" for f in files)
        assert any(f.path == "src/app.js" for f in files)
        assert any(f.path == "styles/main.css" for f in files)
        
        # Verify content extraction
        python_file = next(f for f in files if f.path == "test.py")
        assert python_file.content == "def hello(): return 'world'"
        
    def test_extract_from_github(self):
        """Test extracting code files from a GitHub repository."""
        extractor = CodeExtractor()
        repo_url = "https://github.com/test/repo"
        
        with pytest.raises(NotImplementedError):
            # This will be implemented later when we add GitHub API integration
            extractor.extract_from_github(repo_url)
            
    def test_file_metadata(self, sample_zip):
        """Test that extracted files include necessary metadata."""
        extractor = CodeExtractor()
        files = extractor.extract_from_zip(sample_zip)
        
        file = next(f for f in files if f.path == "test.py")
        assert hasattr(file, 'path')
        assert hasattr(file, 'content')
        assert hasattr(file, 'language')
        assert hasattr(file, 'size')
        
    def test_invalid_zip(self, temp_dir):
        """Test handling of invalid ZIP files."""
        invalid_zip = os.path.join(temp_dir, "invalid.zip")
        with open(invalid_zip, 'w') as f:
            f.write("Not a ZIP file")
            
        extractor = CodeExtractor()
        with pytest.raises(ValueError, match="Invalid ZIP file"):
            extractor.extract_from_zip(invalid_zip)
            
    def test_empty_zip(self, temp_dir):
        """Test handling of empty ZIP files."""
        empty_zip = os.path.join(temp_dir, "empty.zip")
        with zipfile.ZipFile(empty_zip, 'w'):
            pass
            
        extractor = CodeExtractor()
        with pytest.raises(ValueError, match="No files found in ZIP"):
            extractor.extract_from_zip(empty_zip)
            
    def test_file_filtering(self, temp_dir):
        """Test filtering of non-code files."""
        zip_path = os.path.join(temp_dir, "mixed_content.zip")
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("code.py", "print('hello')")
            zf.writestr("image.jpg", "binary content")
            zf.writestr("doc.pdf", "pdf content")
            
        extractor = CodeExtractor()
        files = extractor.extract_from_zip(zip_path)
        
        assert len(files) == 1
        assert files[0].path == "code.py"
