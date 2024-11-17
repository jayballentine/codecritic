from datetime import datetime, timezone
from app.db.session import get_supabase_client

class User:
    def __init__(self, user_id, email, name=None, subscription_type="free", created_at=None, updated_at=None):
        """
        Initialize a User instance.
        
        :param user_id: Unique identifier for the user
        :param email: User's email address
        :param name: Optional user name
        :param subscription_type: User's subscription type, defaults to 'free'
        :param created_at: Timestamp when user was created
        :param updated_at: Timestamp when user was last updated
        """
        self.user_id = user_id
        self.email = email
        self.name = name
        self.subscription_type = subscription_type
        self.created_at = created_at
        self.updated_at = updated_at
        self.supabase = get_supabase_client()
    
    def save(self):
        """
        Save or update the user in the database.
        """
        user_data = {
            "user_id": self.user_id,
            "email": self.email,
            "name": self.name,
            "subscription_type": self.subscription_type
        }
        
        # Check if user exists
        existing_user = self.supabase.table("users").select("*").eq("user_id", self.user_id).execute()
        
        if existing_user.get("data", []):
            # Update existing user
            response = self.supabase.table("users").update(user_data).eq("user_id", self.user_id).execute()
        else:
            # Insert new user
            response = self.supabase.table("users").insert(user_data).execute()
        
        # Update instance with response data
        data = response.get("data", [{}])
        if data:
            user_data = data[0]
            self.created_at = user_data.get("created_at")
            self.updated_at = user_data.get("updated_at")
        return self
    
    @classmethod
    def get_by_user_id(cls, user_id):
        """
        Retrieve a user by their user_id.
        
        :param user_id: Unique identifier of the user
        :return: User instance or None
        """
        supabase = get_supabase_client()
        response = supabase.table("users").select("*").eq("user_id", user_id).execute()
        
        data = response.get("data", [])
        if data:
            user_data = data[0]
            return cls(
                user_id=user_data["user_id"],
                email=user_data["email"],
                name=user_data.get("name"),
                subscription_type=user_data.get("subscription_type", "free"),
                created_at=user_data.get("created_at"),
                updated_at=user_data.get("updated_at")
            )
        return None
