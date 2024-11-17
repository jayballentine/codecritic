from typing import Dict, Any, List
from datetime import datetime

class MockSupabaseResult:
    def __init__(self, data=None):
        self.data = data if data is not None else {}

class MockSupabaseQuery:
    def __init__(self, table_data=None):
        self.table_data = table_data if table_data is not None else []
        self.conditions = []
        self.update_data = None
        
    def eq(self, field: str, value: Any):
        self.conditions.append((field, value))
        return self
        
    def execute(self) -> MockSupabaseResult:
        filtered_data = self.table_data
        for field, value in self.conditions:
            filtered_data = [item for item in filtered_data if item.get(field) == value]
            
        # If this is an update operation
        if self.update_data is not None:
            for item in filtered_data:
                item.update(self.update_data)
            return MockSupabaseResult(filtered_data[0] if filtered_data else None)
            
        # Return first item as dict if single() was called, otherwise return list
        if hasattr(self, '_single') and self._single:
            return MockSupabaseResult(filtered_data[0] if filtered_data else None)
        return MockSupabaseResult(filtered_data)

    def single(self):
        self._single = True
        return self

    def update(self, data: Dict[str, Any]):
        self.update_data = data
        return self

class MockSupabaseTable:
    def __init__(self):
        self.data: List[Dict[str, Any]] = []
        
    def insert(self, data: Dict[str, Any]):
        if isinstance(data, dict):
            self.data.append(data)
        return MockSupabaseQuery([data])
        
    def select(self, *args):
        return MockSupabaseQuery(self.data)
        
    def delete(self):
        return MockSupabaseQuery(self.data)
        
    def upsert(self, data: Dict[str, Any]):
        self.data.append(data)
        return MockSupabaseQuery([data])
        
    def update(self, data: Dict[str, Any]):
        return MockSupabaseQuery(self.data).update(data)

class MockSupabaseClient:
    def __init__(self):
        self._tables = {}
        self._subscriptions = {}
        
    def table(self, name: str) -> MockSupabaseTable:
        if name not in self._tables:
            self._tables[name] = MockSupabaseTable()
        return self._tables[name]

    def create_subscription(self, subscription):
        """Create a subscription in the mock database."""
        self._subscriptions[subscription.user_id] = subscription
        return subscription

    def get_subscription(self, user_id: str):
        """Retrieve a subscription by user ID."""
        return self._subscriptions.get(user_id)

    def update_subscription(self, subscription):
        """Update an existing subscription."""
        self._subscriptions[subscription.user_id] = subscription
        return subscription

class MockDatabaseClient:
    """Mock database client for testing."""
    _instance = None
    _client = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(MockDatabaseClient, cls).__new__(cls)
            cls._client = MockSupabaseClient()
        return cls._instance

    @property
    def client(self):
        return self._client

def get_mock_database_client():
    """Get mock database client for testing."""
    return MockDatabaseClient()

# Global mock instance for subscription tests
mock_supabase = MockDatabaseClient().client
