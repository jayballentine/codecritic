"""
Module for extracting code from various sources (ZIP, GitHub) into a consistent format.
Enhanced with streaming and concurrent processing capabilities.
"""
from dataclasses import dataclass, field
from pathlib import Path
import zipfile
from typing import List, Optional, Set, Generator, Dict, Any
import requests
import os
import base64
import logging
import re
import concurrent.futures
import queue
import threading
from functools import partial

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ExtractedFile:
    """Represents a code file extracted from a source."""
    path: str
    content: str
    language: str
    size: int
    priority: str = 'Medium'
    repository_hierarchy: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def detect_language(file_path: str) -> str:
        """
        Detect programming language from file extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            str: Detected programming language
        """
        extension = Path(file_path).suffix.lower()
        language_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.go': 'Go',
            '.rs': 'Rust',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.scala': 'Scala',
            '.html': 'HTML',
            '.css': 'CSS',
            '.sql': 'SQL',
            '.sh': 'Shell',
            '.yaml': 'YAML',
            '.yml': 'YAML',
            '.json': 'JSON',
            '.xml': 'XML',
            '.md': 'Markdown'
        }
        return language_map.get(extension, 'Unknown')

class CodeExtractor:
    """Handles extraction of code from various sources with enhanced processing."""
    
    def __init__(self, max_workers: int = 5):
        """
        Initialize the code extractor with concurrent processing capabilities.
        
        Args:
            max_workers: Maximum number of concurrent workers for file processing
        """
        # Existing initialization
        self.code_extensions = {
            '.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs',
            '.rb', '.php', '.go', '.rs', '.swift', '.kt', '.scala',
            '.html', '.css', '.sql', '.sh', '.yaml', '.yml',
            '.json', '.xml', '.md'
        }

        self.critical_names = {'main.py', 'index.js', 'app.py', 'server.py'}
        
        self.skip_patterns = {
            r'\.gitignore$', r'\.dockerignore$', r'LICENSE.*', r'CHANGELOG.*',
            r'README.*', r'CONTRIBUTING.*', r'node_modules/.*', r'dist/.*',
            r'build/.*', r'\.pyc$', r'__pycache__/.*', r'\.egg-info/.*',
            r'\.tox/.*', r'\.pytest_cache/.*', r'\.coverage$', r'coverage\.xml$',
            r'\.DS_Store$', r'tests?/fixtures/.*', r'tests?/data/.*',
            r'tests?/resources/.*', r'\.env\..*', r'\.vscode/.*', r'\.idea/.*',
            r'\.settings/.*', 
            # Enhanced test file filtering
            r'tests?/.*', r'.*_test\..*', r'test_.*', r'.*_spec\..*'
        }

        self.skip_regex = re.compile('|'.join(self.skip_patterns))
        
        # Concurrent processing configuration
        self.max_workers = max_workers
        self.file_queue = queue.Queue()
        self.batch_queue = queue.Queue()
        
    def is_critical_file(self, file_path: str) -> bool:
        """
        Check if a file is critical based on its name.
        
        Args:
            file_path: Path to the file
            
        Returns:
            bool: True if file is critical, False otherwise
        """
        return Path(file_path).name in self.critical_names

    def should_skip_file(self, file_path: str) -> bool:
        """
        Check if a file should be skipped based on skip rules.
        
        Args:
            file_path: Path to the file
            
        Returns:
            bool: True if file should be skipped, False otherwise
        """
        # Never skip critical files
        if self.is_critical_file(file_path):
            return False
        
        # Check against skip patterns
        if self.skip_regex.search(file_path):
            return True
        
        # Additional test file filtering
        filename = Path(file_path).name.lower()
        test_indicators = ['test_', '_test', 'spec_', '_spec']
        if any(indicator in filename for indicator in test_indicators):
            return True
        
        return False

    def extract_from_github(self, repo_url: str) -> List[ExtractedFile]:
        """
        Extract files from a GitHub repository.
        
        Args:
            repo_url: URL of the GitHub repository
            
        Returns:
            List[ExtractedFile]: List of extracted files
        """
        return list(self.stream_github_files(repo_url))

    def stream_github_files(self, repo_url: str) -> Generator[ExtractedFile, None, None]:
        """
        Stream files from a GitHub repository with enhanced processing.
        
        Args:
            repo_url: URL of the GitHub repository
            
        Yields:
            ExtractedFile: Extracted and processed files
        """
        # Parse owner/repo from URL
        _, _, _, owner, repo = repo_url.rstrip('/').split('/')
        
        # GitHub API headers
        token = os.getenv('GITHUB_PAT')
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        logger.info(f"Streaming repository: {owner}/{repo}")
        api_url = f'https://api.github.com/repos/{owner}/{repo}/git/trees/main?recursive=1'
        
        try:
            response = requests.get(api_url, headers=headers)
            response.raise_for_status()
            tree = response.json()['tree']
            
            # Concurrent file processing
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                file_futures = []
                for item in tree:
                    if item['type'] == 'blob':
                        path = item['path']
                        if Path(path).suffix.lower() in self.code_extensions and not self.should_skip_file(path):
                            future = executor.submit(self._process_github_file, item, headers, owner, repo)
                            file_futures.append(future)
                
                for future in concurrent.futures.as_completed(file_futures):
                    extracted_file = future.result()
                    if extracted_file:
                        yield extracted_file
                        
        except requests.RequestException as e:
            logger.error(f"Error streaming repository: {str(e)}")
            raise
    
    def _process_github_file(self, item: Dict[str, Any], headers: Dict[str, str], owner: str, repo: str) -> Optional[ExtractedFile]:
        """
        Process a single GitHub file with detailed metadata.
        
        Args:
            item: GitHub API file item
            headers: API request headers
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Optional[ExtractedFile]: Processed file or None if skipped
        """
        try:
            path = item['path']
            
            # Fetch file content
            content_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/{path}"
            content_response = requests.get(content_url, headers=headers)
            content_response.raise_for_status()
            content = content_response.text
            
            # Determine priority and language
            priority = self.determine_priority(path)
            language = ExtractedFile.detect_language(path)
            
            # Create extracted file with repository hierarchy
            extracted_file = ExtractedFile(
                path=path,
                content=content,
                language=language,
                size=len(content),
                priority=priority,
                repository_hierarchy={
                    'owner': owner,
                    'repo': repo,
                    'branch': 'main',
                    'full_path': path
                }
            )
            
            return extracted_file
        
        except requests.RequestException as e:
            logger.error(f"Error processing file {path}: {str(e)}")
            return None
    
    def determine_priority(self, file_path: str) -> str:
        """
        Determine the priority level of a file based on its path and name.
        
        Args:
            file_path: Path to the file
            
        Returns:
            str: Priority level (Critical, High, Medium, Low, Skip)
        """
        # Get just the filename without the path
        filename = Path(file_path).name
        logger.info(f"Determining priority for file: {filename} (full path: {file_path})")

        # Critical files - these take absolute precedence regardless of location
        if self.is_critical_file(file_path):
            logger.info(f"{filename} is Critical (entry point)")
            return 'Critical'

        # Skip check happens after critical file check
        if self.should_skip_file(file_path):
            logger.info(f"{file_path} is Skip (matches skip pattern)")
            return 'Skip'

        # Convert path to lowercase for case-insensitive comparisons
        path_lower = file_path.lower()
        name_lower = filename.lower()
        
        # Test files - only check the filename itself
        if name_lower.startswith('test_') or name_lower.endswith('_test.py'):
            logger.info(f"{filename} is Low (test file)")
            return 'Low'
            
        # Source files in main directories
        source_dirs = {'src/', 'lib/', 'core/'}
        if any(path_lower.startswith(d) for d in source_dirs):
            logger.info(f"{filename} is High (source file)")
            return 'High'
        
        # Documentation
        if path_lower.endswith(('.md', '.txt')):
            logger.info(f"{filename} is Low (documentation)")
            return 'Low'
        
        # Configuration files
        if path_lower.endswith(('.json', '.yml', '.yaml', '.xml')):
            logger.info(f"{filename} is Medium (config file)")
            return 'Medium'
        
        # Default to Medium for other code files
        logger.info(f"{filename} is Medium (default)")
        return 'Medium'
    
    def form_review_batches(self, files: List[ExtractedFile], batch_size: int = 10) -> List[List[ExtractedFile]]:
        """
        Form review batches based on file priority.
        
        Args:
            files: List of extracted files
            batch_size: Number of files per batch
            
        Returns:
            List of file batches
        """
        # Sort files by priority: Critical first, then High, Medium, Low
        priority_order = {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3}
        sorted_files = sorted(files, key=lambda f: priority_order.get(f.priority, 3))
        
        batches = []
        current_batch = []
        
        for file in sorted_files:
            current_batch.append(file)
            
            if len(current_batch) == batch_size:
                batches.append(current_batch)
                current_batch = []
        
        # Add remaining files if any
        if current_batch:
            batches.append(current_batch)
        
        return batches
