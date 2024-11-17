from typing import Optional
import re
from app.db.session import get_supabase_client

class Repository:
    VALID_STATUSES = ["Pending", "In Progress", "Completed"]
    VALID_SUBMISSION_METHODS = ["github_url", "zip_file"]
    STATUS_TRANSITIONS = {
        "Pending": ["In Progress"],
        "In Progress": ["Completed"],
        "Completed": []
    }

    def __init__(
        self,
        repo_id: str,
        submission_method: str,
        github_url: Optional[str] = None,
        file_path: Optional[str] = None,
        status: str = "Pending"
    ):
        self.repo_id = repo_id
        self._status = "Pending"  # Initialize privately
        self.submission_method = submission_method
        self.github_url = github_url
        self.file_path = file_path
        
        # Validate submission method and related fields
        self._validate_submission_method()
        
        # Set status last to ensure proper initialization
        self.status = status

    @property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, new_status: str) -> None:
        if new_status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(self.VALID_STATUSES)}")
        
        # If this is an initialization (current status is Pending and hasn't been saved)
        if self._status == "Pending" and not hasattr(self, '_saved'):
            self._status = new_status
            return
            
        # Check if the transition is valid
        if new_status not in self.STATUS_TRANSITIONS.get(self._status, []):
            raise ValueError(f"Invalid status transition from {self._status} to {new_status}")
        
        self._status = new_status

    def _validate_submission_method(self) -> None:
        if self.submission_method not in self.VALID_SUBMISSION_METHODS:
            raise ValueError("Invalid submission method")

        if self.submission_method == "github_url":
            if not self.github_url:
                raise ValueError("GitHub URL required")
            self._validate_github_url()
        elif self.submission_method == "zip_file":
            if self.file_path is None:  # Check for None specifically
                raise ValueError("File path required")
            self._validate_zip_file()

    def _validate_github_url(self) -> None:
        if not self.github_url:
            return
            
        # Basic URL format validation
        github_pattern = r'^https://github\.com/[\w-]+/[\w.-]+/?$'
        if not re.match(github_pattern, self.github_url):
            # Check if it's a valid URL format first
            if not self.github_url.startswith('https://'):
                raise ValueError("Invalid github url format")
            # Then check if it's actually GitHub
            if not self.github_url.startswith('https://github.com/'):
                raise ValueError("Must be a github.com URL")
            # If both checks pass but pattern doesn't match, it's an invalid format
            raise ValueError("Invalid github url format")

    def _validate_zip_file(self) -> None:
        # Removed the guard clause to handle empty strings
        if not self.file_path.strip():
            raise ValueError("File path cannot be empty")
        if not self.file_path.lower().endswith('.zip'):
            raise ValueError("Must be a zip file")

    def save(self) -> None:
        supabase = get_supabase_client()
        data = {
            "repo_id": self.repo_id,
            "status": self.status,
            "submission_method": self.submission_method,
        }
        
        if self.submission_method == "github_url":
            data["github_url"] = self.github_url
        else:
            data["file_path"] = self.file_path

        try:
            if not hasattr(self, '_saved'):
                # Insert new record
                result = supabase.table("repositories").insert(data).execute()
                self._saved = True
            else:
                # Update existing record
                result = supabase.table("repositories").update(data).eq("repo_id", self.repo_id).execute()
        except Exception as e:
            if "unique constraint" in str(e).lower():
                raise Exception("unique constraint")
            raise e
