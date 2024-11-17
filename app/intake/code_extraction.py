"""
Module for extracting code from various sources (ZIP, GitHub) into a consistent format.
"""
from dataclasses import dataclass
from pathlib import Path
import zipfile
from typing import List, Optional

@dataclass
class ExtractedFile:
    """Represents a code file extracted from a source."""
    path: str
    content: str
    language: str
    size: int

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
    """Handles extraction of code from various sources."""
    
    def __init__(self):
        """Initialize the code extractor."""
        self.code_extensions = {
            '.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs',
            '.rb', '.php', '.go', '.rs', '.swift', '.kt', '.scala',
            '.html', '.css', '.sql', '.sh', '.yaml', '.yml',
            '.json', '.xml', '.md'
        }
    
    def extract_from_zip(self, zip_path: str) -> List[ExtractedFile]:
        """
        Extract code files from a ZIP archive.
        
        Args:
            zip_path: Path to the ZIP file
            
        Returns:
            List[ExtractedFile]: List of extracted code files
            
        Raises:
            ValueError: If ZIP is invalid or empty
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # Verify ZIP integrity
                if zf.testzip() is not None:
                    raise ValueError("Invalid ZIP file")
                
                # Get list of files
                files = [f for f in zf.namelist() if not f.endswith('/')]
                if not files:
                    raise ValueError("No files found in ZIP")
                
                # Extract code files
                extracted = []
                for file_path in files:
                    if Path(file_path).suffix.lower() in self.code_extensions:
                        content = zf.read(file_path).decode('utf-8', errors='ignore')
                        extracted.append(ExtractedFile(
                            path=file_path,
                            content=content,
                            language=ExtractedFile.detect_language(file_path),
                            size=len(content)
                        ))
                
                return extracted
                
        except zipfile.BadZipFile:
            raise ValueError("Invalid ZIP file")
    
    def extract_from_github(self, repo_url: str) -> List[ExtractedFile]:
        """
        Extract code files from a GitHub repository.
        
        Args:
            repo_url: URL of the GitHub repository
            
        Returns:
            List[ExtractedFile]: List of extracted code files
            
        Raises:
            NotImplementedError: This feature is not yet implemented
        """
        raise NotImplementedError("GitHub extraction not yet implemented")
