import unittest
from datetime import datetime
from app.services.report_generation_service import ReportGenerationService
from app.models.subscription import Subscription
from app.models.review import Review

class MockReview:
    def __init__(self, repository_name='test_repo', timestamp=None):
        self.repository_name = repository_name
        self.timestamp = timestamp or datetime.utcnow()
        self.overall_quality_score = 85
        self.file_reviews = [
            {
                'filename': 'test.py',
                'critical_issues': 1,
                'improvement_suggestions': ['Use type hints', 'Reduce complexity']
            },
            {
                'filename': 'utils.py',
                'critical_issues': 0,
                'improvement_suggestions': ['Add docstrings']
            }
        ]
        self.code_quality_metrics = {
            'cyclomatic_complexity': 3.5,
            'maintainability_index': 80
        }

class TestReportGenerationService(unittest.TestCase):
    def setUp(self):
        self.mock_review = MockReview()

    def test_free_tier_report_generation(self):
        """Test report generation for free tier subscription"""
        free_subscription = Subscription(user_id=1, plan_type='Free')
        report = ReportGenerationService.generate_report(self.mock_review, free_subscription)
        
        # Verify metadata
        self.assertEqual(report['metadata']['repository'], 'test_repo')
        self.assertEqual(report['metadata']['subscription_tier'], 'Free')
        
        # Verify summary for free tier
        self.assertEqual(report['summary']['overall_quality_score'], 85)
        self.assertEqual(report['summary']['total_files_analyzed'], 2)
        self.assertEqual(report['summary']['critical_issues_count'], 1)
        
        # Verify limited details for free tier
        self.assertIsNotNone(report['summary']['improvement_areas'])
        self.assertEqual(len(report['detailed_findings']['file_reviews']), 0)

    def test_pro_tier_report_generation(self):
        """Test report generation for pro tier subscription"""
        pro_subscription = Subscription(user_id=1, plan_type='Pro')
        report = ReportGenerationService.generate_report(self.mock_review, pro_subscription)
        
        # Verify metadata
        self.assertEqual(report['metadata']['repository'], 'test_repo')
        self.assertEqual(report['metadata']['subscription_tier'], 'Pro')
        
        # Verify summary
        self.assertEqual(report['summary']['overall_quality_score'], 85)
        self.assertEqual(report['summary']['total_files_analyzed'], 2)
        self.assertEqual(report['summary']['critical_issues_count'], 1)
        
        # Verify comprehensive details for pro tier
        self.assertIsNotNone(report['summary']['improvement_areas'])
        self.assertEqual(len(report['detailed_findings']['file_reviews']), 2)
        self.assertIn('code_quality_metrics', report['detailed_findings'])

    def test_report_validation(self):
        """Test report validation mechanism"""
        pro_subscription = Subscription(user_id=1, plan_type='Pro')
        report = ReportGenerationService.generate_report(self.mock_review, pro_subscription)
        
        # Validate report structure
        is_valid = ReportGenerationService.validate_report(report)
        self.assertTrue(is_valid)

    def test_report_export(self):
        """Test report export to JSON"""
        pro_subscription = Subscription(user_id=1, plan_type='Pro')
        report = ReportGenerationService.generate_report(self.mock_review, pro_subscription)
        
        # Export report
        exported_report = ReportGenerationService.export_report(report)
        
        # Verify export
        self.assertIsInstance(exported_report, str)
        self.assertTrue(exported_report.startswith('{'))
        self.assertTrue(exported_report.endswith('}'))

if __name__ == '__main__':
    unittest.main()
