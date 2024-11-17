import pytest
from unittest.mock import MagicMock, patch
from app.db.session import Session, SessionLocal

class TestSessionManagement:
    def setup_method(self):
        self.session = Session()

    @patch('app.db.session.SessionLocal')
    def test_transaction_commit_success(self, mock_session_local):
        # Create a mock session
        mock_db_session = MagicMock()
        mock_session_local.return_value = mock_db_session

        # Use the actual begin method
        with self.session.begin() as db_session:
            # Verify the session is the mocked session
            assert db_session == mock_db_session
            # Simulate some database operation
            db_session.execute("SOME SQL COMMAND")

        # Verify commit was called on the session
        mock_db_session.commit.assert_called_once()
        mock_db_session.close.assert_called_once()

    @patch('app.db.session.SessionLocal')
    def test_transaction_error_handling(self, mock_session_local):
        # Create a mock session
        mock_db_session = MagicMock()
        mock_session_local.return_value = mock_db_session

        # Simulate an error during transaction
        mock_db_session.execute.side_effect = Exception("Transaction error")

        # Verify that an exception is raised and rollback is called
        with pytest.raises(Exception) as exc_info:
            with self.session.begin():
                mock_db_session.execute("SOME SQL COMMAND")

        assert str(exc_info.value) == "Transaction error"
        mock_db_session.rollback.assert_called_once()
        mock_db_session.close.assert_called_once()

    @patch('app.db.session.SessionLocal')
    def test_transaction_rollback_on_failure(self, mock_session_local):
        # Create a mock session
        mock_db_session = MagicMock()
        mock_session_local.return_value = mock_db_session

        # Simulate a failure during transaction
        mock_db_session.execute.side_effect = Exception("Failure during transaction")

        # Verify that an exception is raised and rollback is called
        with pytest.raises(Exception):
            with self.session.begin():
                mock_db_session.execute("SOME SQL COMMAND")

        mock_db_session.rollback.assert_called_once()
        mock_db_session.close.assert_called_once()
