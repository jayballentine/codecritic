"""
Tests for enhanced code extraction functionality with streaming and concurrent processing.
"""
import os
import pytest
import tempfile
import zipfile
from unittest.mock import patch, Mock
from pathlib import Path
import logging
from app.intake.code_extraction import CodeExtractor, ExtractedFile

# Set up logging for tests
logging.basicConfig(level=logging.INFO)

class TestEnhancedCodeExtraction:
    @patch('requests.get')
    def test_stream_github_files(self, mock_get):
        """Test streaming files from GitHub with concurrent processing."""
        # Mock GitHub API responses
        mock_tree_response = Mock()
        mock_tree_response.status_code = 200
        mock_tree_response.json.return_value = {
            "tree": [
                {"path": "main.py", "type": "blob", "size": 100},
                {"path": "src/utils.py", "type": "blob", "size": 150},
                {"path": "config.json", "type": "blob", "size": 50},
                {"path": "tests/test_main.py", "type": "blob", "size": 200}
            ]
        }

        # Mock content responses
        def mock_content_response(url):
            response = Mock()
            response.status_code = 200
            response.text = f"Content for {url}"
            response.raise_for_status = lambda: None
            return response

        # Prepare side effects to match the expected calls
        side_effects = [
            mock_tree_response,  # First call for tree
            mock_content_response("https://raw.githubusercontent.com/test/repo/main/main.py"),  # Content for main.py
            mock_content_response("https://raw.githubusercontent.com/test/repo/main/src/utils.py"),  # Content for utils.py
            mock_content_response("https://raw.githubusercontent.com/test/repo/main/config.json")  # Content for config.json
        ]

        # Extend side effects to cover all potential content requests
        side_effects.extend([mock_content_response(f"https://raw.githubusercontent.com/test/repo/main/path{i}") for i in range(10)])

        mock_get.side_effect = side_effects

        extractor = CodeExtractor(max_workers=2)
        repo_url = "https://github.com/test/repo"

        # Collect streamed files
        streamed_files = list(extractor.stream_github_files(repo_url))

        # Assertions
        assert len(streamed_files) == 3  # Excluding test file
        
        # Check file metadata
        for file in streamed_files:
            assert isinstance(file, ExtractedFile)
            assert file.content is not None
            assert file.size > 0
            assert file.language is not None
            assert file.priority in ['Critical', 'High', 'Medium', 'Low']
            assert 'repository_hierarchy' in file.__dict__

    def test_form_review_batches(self):
        """Test dynamic batch formation with priority sorting."""
        extractor = CodeExtractor()
        
        # Create sample files with different priorities
        files = [
            ExtractedFile(path="low1.py", content="", language="Python", size=10, priority="Low"),
            ExtractedFile(path="main.py", content="", language="Python", size=20, priority="Critical"),
            ExtractedFile(path="medium1.py", content="", language="Python", size=15, priority="Medium"),
            ExtractedFile(path="high1.py", content="", language="Python", size=12, priority="High"),
            ExtractedFile(path="low2.py", content="", language="Python", size=8, priority="Low"),
            ExtractedFile(path="critical2.py", content="", language="Python", size=25, priority="Critical")
        ]

        # Form batches
        batches = extractor.form_review_batches(files, batch_size=3)

        # Assertions
        assert len(batches) == 2  # 6 files, batch size 3
        
        # First batch should have critical files first
        first_batch = batches[0]
        assert len(first_batch) == 3
        assert first_batch[0].priority == 'Critical'
        assert first_batch[1].priority == 'Critical'
        assert first_batch[2].priority == 'High'

        # Second batch should have remaining files
        second_batch = batches[1]
        assert len(second_batch) == 3
        assert second_batch[0].priority == 'Medium'
        assert second_batch[1].priority == 'Low'
        assert second_batch[2].priority == 'Low'

    def test_repository_hierarchy(self):
        """Test repository hierarchy metadata in extracted files."""
        extractor = CodeExtractor()
        
        # Create a sample extracted file
        file = ExtractedFile(
            path="src/utils.py", 
            content="def utility():", 
            language="Python", 
            size=20, 
            priority="Medium",
            repository_hierarchy={
                'owner': 'test_owner',
                'repo': 'test_repo',
                'branch': 'main',
                'full_path': 'src/utils.py'
            }
        )

        # Assertions
        assert file.repository_hierarchy['owner'] == 'test_owner'
        assert file.repository_hierarchy['repo'] == 'test_repo'
        assert file.repository_hierarchy['branch'] == 'main'
        assert file.repository_hierarchy['full_path'] == 'src/utils.py'

    @patch('requests.get')
    def test_concurrent_file_processing(self, mock_get):
        """Test concurrent file processing performance characteristics."""
        # Mock GitHub API responses
        mock_tree_response = Mock()
        mock_tree_response.status_code = 200
        mock_tree_response.json.return_value = {
            "tree": [
                {"path": f"src/file{i}.py", "type": "blob", "size": 100} 
                for i in range(20)  # Simulate 20 files
            ]
        }

        # Mock content responses to simulate network delay
        def mock_content_response(url):
            response = Mock()
            response.status_code = 200
            response.text = f"Content for {url}"
            response.raise_for_status = lambda: None
            return response

        # Prepare side effects to match the expected calls
        side_effects = [
            mock_tree_response,  # First call for tree
        ]
        side_effects.extend([
            mock_content_response(f"https://raw.githubusercontent.com/test/repo/main/src/file{i}.py") 
            for i in range(20)
        ])

        mock_get.side_effect = side_effects

        extractor = CodeExtractor(max_workers=5)  # Use 5 workers
        repo_url = "https://github.com/test/repo"

        # Collect streamed files
        streamed_files = list(extractor.stream_github_files(repo_url))

        # Assertions
        assert len(streamed_files) == 20
        for file in streamed_files:
            assert isinstance(file, ExtractedFile)
