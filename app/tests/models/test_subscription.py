import pytest
from datetime import datetime, timedelta
from app.models.subscription import Subscription
from app.tests.utils.test_utils import mock_supabase

class TestSubscription:
    def test_valid_plan_types(self):
        """Test that only valid plan types are accepted."""
        valid_plans = ['Free', 'Pro', 'Enterprise']
        invalid_plans = ['Basic', 'Premium', '']

        for plan in valid_plans:
            subscription = Subscription(user_id='test_user', plan_type=plan)
            assert subscription.plan_type == plan

        for plan in invalid_plans:
            with pytest.raises(ValueError, match="Invalid plan type"):
                Subscription(user_id='test_user', plan_type=plan)

    def test_free_plan_no_expiry(self):
        """Test that Free plan has no expiry date."""
        free_subscription = Subscription(user_id='test_user', plan_type='Free')
        assert free_subscription.expiry_date is None

    def test_paid_plan_expiry(self):
        """Test that paid plans have an expiry date."""
        pro_subscription = Subscription(user_id='test_user', plan_type='Pro')
        assert pro_subscription.expiry_date is not None
        assert pro_subscription.expiry_date > datetime.utcnow()

    def test_subscription_expiration(self):
        """Test subscription expiration logic."""
        # Create a subscription that's already expired
        past_date = datetime.utcnow() - timedelta(days=30)
        expired_subscription = Subscription(
            user_id='test_user', 
            plan_type='Pro', 
            expiry_date=past_date
        )
        assert expired_subscription.is_expired is True

        # Create a current subscription
        current_subscription = Subscription(
            user_id='test_user', 
            plan_type='Pro', 
            expiry_date=datetime.utcnow() + timedelta(days=30)
        )
        assert current_subscription.is_expired is False

    def test_plan_upgrade_downgrade(self):
        """Test plan type changes."""
        subscription = Subscription(user_id='test_user', plan_type='Free')
        
        # Upgrade to Pro
        subscription.upgrade_plan('Pro')
        assert subscription.plan_type == 'Pro'
        assert subscription.expiry_date is not None

        # Downgrade to Free
        subscription.upgrade_plan('Free')
        assert subscription.plan_type == 'Free'
        assert subscription.expiry_date is None

    def test_supabase_integration(self):
        """Test Supabase integration for subscription operations."""
        # Create a new subscription
        subscription = Subscription(user_id='test_user', plan_type='Pro')
        
        # Test creating subscription in Supabase
        created_subscription = mock_supabase.create_subscription(subscription)
        assert created_subscription is not None
        assert created_subscription.user_id == 'test_user'
        assert created_subscription.plan_type == 'Pro'

        # Test retrieving subscription
        retrieved_subscription = mock_supabase.get_subscription('test_user')
        assert retrieved_subscription is not None
        assert retrieved_subscription.plan_type == 'Pro'

        # Test updating subscription
        retrieved_subscription.upgrade_plan('Enterprise')
        updated_subscription = mock_supabase.update_subscription(retrieved_subscription)
        assert updated_subscription.plan_type == 'Enterprise'
