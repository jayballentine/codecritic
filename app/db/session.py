from contextlib import contextmanager
from typing import Generator, Optional, Dict, Any
from supabase import Client

from app.db.base import get_database_client
from app.utils.logger import get_logger

logger = get_logger(__name__)

class MockSupabaseClient:
    """Mock Supabase client for testing subscription operations."""
    _subscriptions: Dict[str, Any] = {}

    @classmethod
    def create_subscription(cls, subscription):
        """Create a subscription in the mock database."""
        cls._subscriptions[subscription.user_id] = subscription
        return subscription

    @classmethod
    def get_subscription(cls, user_id: str):
        """Retrieve a subscription by user ID."""
        return cls._subscriptions.get(user_id)

    @classmethod
    def update_subscription(cls, subscription):
        """Update an existing subscription."""
        cls._subscriptions[subscription.user_id] = subscription
        return subscription

class SessionLocal:
    """Local session class for database operations."""
    def __init__(self):
        self._db_client = get_database_client()
        self.client = self._db_client.client
        self._in_transaction = False

    def __enter__(self):
        self.begin()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is not None:
                self.rollback()
            else:
                self.commit()
        finally:
            self.close()

    def begin(self):
        """Begin a transaction."""
        self._in_transaction = True

    def commit(self):
        """Commit the current transaction."""
        if self._in_transaction:
            # Supabase doesn't have explicit commit
            self._in_transaction = False

    def rollback(self):
        """Rollback the current transaction."""
        if self._in_transaction:
            # Supabase doesn't have explicit rollback
            self._in_transaction = False

    def close(self):
        """Close the session."""
        self._in_transaction = False
        # Supabase doesn't require explicit connection closing
        pass

    def execute(self, query: str, *args, **kwargs):
        """Execute a query."""
        if not self._in_transaction:
            raise RuntimeError("Transaction not started")
        # Implementation would depend on specific needs
        pass

class Session:
    def __init__(self):
        """Initialize the Session class."""
        self._db_client = get_database_client()

    @contextmanager
    def begin(self) -> Generator[SessionLocal, None, None]:
        """
        Context manager for database operations.
        Provides a session for database interactions.

        Usage:
            with session.begin() as db_session:
                db_session.execute("SOME SQL COMMAND")

        Yields:
            SessionLocal: Active database session
        """
        session = SessionLocal()
        try:
            session.begin()
            yield session
        except Exception as e:
            session.rollback()
            logger.error(f"Database operation failed: {str(e)}")
            raise
        finally:
            try:
                session.commit()
            finally:
                session.close()

def get_session() -> Session:
    """
    Get a new database session.

    Returns:
        Session: Configured database session
    """
    return Session()

def get_supabase_client() -> Client:
    """
    Get a Supabase client for direct database interactions.

    Returns:
        Client: Supabase client instance
    """
    return get_database_client().client

# For testing purposes, use the mock Supabase client
supabase = MockSupabaseClient()
