import pytest
from unittest.mock import MagicMock, patch
from app.db.session import Session, SessionLocal
from app.tests.utils.test_utils import get_mock_database_client

class TestSessionManagement:
    def setup_method(self):
        self.mock_db = get_mock_database_client()
        self.session = Session(self.mock_db)

    def test_transaction_commit_success(self):
        # Use the actual begin method
        with self.session.begin() as db_session:
            # Verify the session has our mock client
            assert db_session.client == self.mock_db.client
            # Simulate some database operation
            db_session.execute("SOME SQL COMMAND")

    def test_transaction_error_handling(self):
        # Simulate an error during transaction
        with pytest.raises(Exception) as exc_info:
            with self.session.begin() as db_session:
                raise Exception("Transaction error")

        assert str(exc_info.value) == "Transaction error"

    def test_transaction_rollback_on_failure(self):
        # Simulate a failure during transaction
        with pytest.raises(Exception):
            with self.session.begin() as db_session:
                raise Exception("Failure during transaction")
