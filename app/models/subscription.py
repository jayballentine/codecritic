from datetime import datetime, timedelta

class Subscription:
    VALID_PLAN_TYPES = ['Free', 'Pro', 'Enterprise']

    def __init__(self, user_id, plan_type, expiry_date=None, payment_status='active'):
        self.user_id = user_id
        self.payment_status = payment_status
        self.set_plan_type(plan_type)
        
        # Set expiry date based on plan type
        if plan_type == 'Free':
            self.expiry_date = None
        elif expiry_date is None:
            # Default to 30 days for paid plans
            self.expiry_date = datetime.utcnow() + timedelta(days=30)
        else:
            self.expiry_date = expiry_date

    def set_plan_type(self, plan_type):
        """Validate and set plan type."""
        if plan_type not in self.VALID_PLAN_TYPES:
            raise ValueError(f"Invalid plan type. Must be one of {self.VALID_PLAN_TYPES}")
        self.plan_type = plan_type

    @property
    def is_expired(self):
        """Check if subscription is expired."""
        if self.plan_type == 'Free':
            return False
        return self.expiry_date < datetime.utcnow()

    def upgrade_plan(self, new_plan_type):
        """Upgrade or downgrade subscription plan."""
        # Validate new plan type
        if new_plan_type not in self.VALID_PLAN_TYPES:
            raise ValueError(f"Invalid plan type. Must be one of {self.VALID_PLAN_TYPES}")

        # Set plan type and adjust expiry
        if new_plan_type == 'Free':
            self.plan_type = new_plan_type
            self.expiry_date = None
        else:
            self.plan_type = new_plan_type
            # Reset expiry to 30 days from now for paid plans
            self.expiry_date = datetime.utcnow() + timedelta(days=30)
