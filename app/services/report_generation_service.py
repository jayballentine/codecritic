import json
from typing import Dict, Any, List
from app.models.subscription import Subscription
from app.models.review import Review
from app.utils.logger import logger

class ReportGenerationService:
    """
    Service for generating tiered code review reports
    Supports different report depths based on subscription plan
    """

    REPORT_STRUCTURE = {
        "metadata": {
            "repository": None,
            "review_timestamp": None,
            "subscription_tier": None
        },
        "summary": {
            "overall_quality_score": None,
            "total_files_analyzed": 0,
            "critical_issues_count": 0,
            "improvement_areas": []
        },
        "detailed_findings": {
            "file_reviews": [],
            "code_quality_metrics": {}
        }
    }

    @classmethod
    def generate_report(cls, review: Review, subscription: Subscription) -> Dict[str, Any]:
        """
        Generate a report based on subscription tier
        
        Args:
            review (Review): The review object containing analysis results
            subscription (Subscription): User's subscription details
        
        Returns:
            Dict: Standardized JSON report
        """
        report = cls.REPORT_STRUCTURE.copy()
        
        # Populate metadata
        report['metadata']['repository'] = review.repository_name
        report['metadata']['review_timestamp'] = review.timestamp.isoformat()
        report['metadata']['subscription_tier'] = subscription.plan_type

        # Populate summary
        report['summary']['overall_quality_score'] = review.overall_quality_score
        report['summary']['total_files_analyzed'] = len(review.file_reviews)
        report['summary']['critical_issues_count'] = sum(
            1 for file_review in review.file_reviews 
            if file_review.get('critical_issues', 0) > 0
        )
        
        # Tier-based report generation
        if subscription.plan_type == 'Free':
            # Free tier: High-level insights only
            report['summary']['improvement_areas'] = cls._get_top_improvement_areas(review)
        
        elif subscription.plan_type in ['Pro', 'Enterprise']:
            # Paid tiers: Comprehensive analysis
            report['summary']['improvement_areas'] = cls._get_top_improvement_areas(review)
            report['detailed_findings']['file_reviews'] = review.file_reviews
            report['detailed_findings']['code_quality_metrics'] = review.code_quality_metrics

        return report

    @classmethod
    def _get_top_improvement_areas(cls, review: Review, top_n: int = 3) -> List[str]:
        """
        Extract top improvement areas for the report
        
        Args:
            review (Review): The review object
            top_n (int): Number of top improvement areas to return
        
        Returns:
            List[str]: Top improvement areas
        """
        # Placeholder logic - replace with actual improvement area extraction
        improvement_areas = [
            issue for file_review in review.file_reviews 
            for issue in file_review.get('improvement_suggestions', [])
        ]
        return improvement_areas[:top_n]

    @classmethod
    def validate_report(cls, report: Dict[str, Any]) -> bool:
        """
        Validate the generated report for completeness and structure
        
        Args:
            report (Dict): Generated report to validate
        
        Returns:
            bool: Whether the report is valid
        """
        try:
            # Check metadata
            assert report['metadata']['repository'] is not None
            assert report['metadata']['review_timestamp'] is not None
            assert report['metadata']['subscription_tier'] is not None

            # Check summary
            assert 'overall_quality_score' in report['summary']
            assert 'total_files_analyzed' in report['summary']
            assert 'critical_issues_count' in report['summary']
            assert 'improvement_areas' in report['summary']

            return True
        except (KeyError, AssertionError) as e:
            logger.error(f"Report validation failed: {e}")
            return False

    @classmethod
    def export_report(cls, report: Dict[str, Any], format: str = 'json') -> str:
        """
        Export report to specified format
        
        Args:
            report (Dict): Report to export
            format (str): Export format (currently only JSON supported)
        
        Returns:
            str: Exported report content
        """
        if format == 'json':
            return json.dumps(report, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")
