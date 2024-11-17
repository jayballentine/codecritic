from typing import List, Dict, Optional
import uuid
import statistics
from datetime import datetime
import json
from pathlib import Path

class Review:
    def __init__(
        self, 
        review_id: Optional[str] = None, 
        repo_id: Optional[int] = None, 
        repository_name: Optional[str] = None,
        file_reviews: Optional[List[Dict]] = None,
        batch_reviews: Optional[List[Dict]] = None,
        final_review: Optional[Dict] = None,
        timestamp: Optional[datetime] = None,
        code_quality_metrics: Optional[Dict] = None
    ):
        self.review_id = review_id or str(uuid.uuid4())
        self.repo_id = repo_id
        self.repository_name = repository_name
        self.file_reviews = file_reviews or []
        self.batch_reviews = batch_reviews or []
        self.final_review = final_review
        self.timestamp = timestamp or datetime.utcnow()
        self.code_quality_metrics = code_quality_metrics or {}

    @property
    def overall_quality_score(self) -> float:
        """
        Compute the overall quality score based on file reviews.
        
        :return: Overall quality score (0-100)
        """
        if not self.file_reviews:
            return 0.0
        
        # Calculate average score from file reviews
        scores = [review.get('score', 0) for review in self.file_reviews]
        return round(statistics.mean(scores), 2)

    @classmethod
    def create(
        cls, 
        repo_id: int, 
        file_reviews: List[Dict], 
        repository_name: Optional[str] = None,
        code_quality_metrics: Optional[Dict] = None
    ) -> 'Review':
        """
        Create a new review instance.
        
        :param repo_id: ID of the repository being reviewed
        :param file_reviews: List of individual file reviews
        :param repository_name: Name of the repository
        :param code_quality_metrics: Additional code quality metrics
        :return: Review instance
        """
        return cls(
            repo_id=repo_id,
            file_reviews=file_reviews,
            repository_name=repository_name,
            code_quality_metrics=code_quality_metrics
        )

    def aggregate_batch_reviews(self):
        """
        Aggregate file reviews into batch reviews.
        Groups files by directory or major components.
        """
        # Simple implementation: group by first directory level
        batch_groups = {}
        for file_review in self.file_reviews:
            # Split file path and use first directory as batch key
            path_parts = file_review['file_path'].split('/')
            batch_key = path_parts[0] if len(path_parts) > 1 else 'root'
            
            if batch_key not in batch_groups:
                batch_groups[batch_key] = {
                    'files': [],
                    'scores': []
                }
            
            batch_groups[batch_key]['files'].append(file_review['file_path'])
            batch_groups[batch_key]['scores'].append(file_review.get('score', 0))
        
        # Convert batch groups to batch reviews
        self.batch_reviews = [
            {
                'batch_name': batch_key,
                'files': batch_info['files'],
                'score': statistics.mean(batch_info['scores']) if batch_info['scores'] else 0,
                'comments': []  # Could be expanded to aggregate comments
            }
            for batch_key, batch_info in batch_groups.items()
        ]

    def compute_final_review(self):
        """
        Compute the final review based on batch reviews.
        """
        if not self.batch_reviews:
            self.aggregate_batch_reviews()
        
        # Compute overall score as mean of batch review scores
        overall_score = statistics.mean([
            batch_review['score'] for batch_review in self.batch_reviews
        ]) if self.batch_reviews else 0
        
        self.final_review = {
            'overall_score': round(overall_score, 2),
            'summary': f"Repository review based on {len(self.file_reviews)} files across {len(self.batch_reviews)} batches",
            'batch_reviews': self.batch_reviews
        }

    def save(self):
        """
        Save the review to a JSON file (for testing).
        """
        # Create reviews directory if it doesn't exist
        output_dir = Path("reviews")
        output_dir.mkdir(exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = output_dir / f"review_{timestamp}.json"
        
        # Prepare review data
        review_data = {
            'review_id': self.review_id,
            'repo_id': self.repo_id,
            'repository_name': self.repository_name,
            'file_reviews': self.file_reviews,
            'batch_reviews': self.batch_reviews,
            'final_review': self.final_review,
            'timestamp': self.timestamp.isoformat(),
            'code_quality_metrics': self.code_quality_metrics
        }
        
        # Save to file
        with open(filename, 'w') as f:
            json.dump(review_data, f, indent=2)
        
        return filename

    @classmethod
    def get(cls, review_id: str) -> 'Review':
        """
        Retrieve a review from file by its ID.
        
        :param review_id: Unique identifier of the review
        :return: Review instance
        """
        reviews_dir = Path("reviews")
        if not reviews_dir.exists():
            return None
        
        # Look for review file with matching ID
        for file in reviews_dir.glob("*.json"):
            with open(file, 'r') as f:
                review_data = json.load(f)
                if review_data['review_id'] == review_id:
                    return cls(
                        review_id=review_data['review_id'],
                        repo_id=review_data['repo_id'],
                        repository_name=review_data.get('repository_name'),
                        file_reviews=review_data.get('file_reviews', []),
                        batch_reviews=review_data.get('batch_reviews', []),
                        final_review=review_data.get('final_review'),
                        timestamp=datetime.fromisoformat(review_data.get('timestamp', datetime.utcnow().isoformat())),
                        code_quality_metrics=review_data.get('code_quality_metrics', {})
                    )
        
        return None
