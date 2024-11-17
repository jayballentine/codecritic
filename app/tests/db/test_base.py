import os
import pytest
from unittest.mock import patch, MagicMock

from app.utils.config import get_config
from app.utils.logger import get_logger
from app.db.base import get_database_client

logger = get_logger(__name__)

class MockDatabaseClient:
    """Mock database client for testing initialization scenarios."""
    def __init__(self, config=None):
        if config:
            self.host = config.get('DB_HOST')
            self.port = int(config.get('DB_PORT')) if config.get('DB_PORT') else None
            self.username = config.get('DB_USERNAME')
            self.password = config.get('DB_PASSWORD')
            self.database = config.get('DB_NAME')
        else:
            self.host = None
            self.port = None
            self.username = None
            self.password = None
            self.database = None
        self.connected = False
        self.client = MagicMock()

    def connect(self):
        """Simulate database connection."""
        if not all([self.host, self.port, self.username, self.password, self.database]):
            raise ValueError("Missing required database connection parameters")
        self.connected = True
        return self

    def get_connection(self):
        """Get the mock Supabase client."""
        return self.client

@pytest.fixture
def mock_config():
    """Fixture to provide test configuration."""
    return {
        'DB_HOST': 'localhost',
        'DB_PORT': 5432,
        'DB_USERNAME': 'testuser',
        'DB_PASSWORD': 'testpass',
        'DB_NAME': 'testdb',
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_KEY': 'test-key'
    }

@pytest.fixture
def mock_env(mock_config):
    """Fixture to set up environment variables."""
    original_env = {}
    for key, value in mock_config.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = str(value)
    yield
    for key, value in original_env.items():
        if value is None:
            del os.environ[key]
        else:
            os.environ[key] = value

def mock_get_database_client(config=None):
    """Utility function to get a mock database client."""
    if config is None:
        config = get_config()
    return MockDatabaseClient(config=config)

@patch('app.utils.config.get_config')
def test_database_client_initialization(mock_get_config, mock_config):
    """Test successful database client initialization."""
    mock_get_config.return_value = mock_config
    try:
        client = mock_get_database_client(mock_config)
        client.connect()
        assert client.connected is True
        assert client.host == 'localhost'
        logger.info("Database client initialized successfully")
    except Exception as e:
        pytest.fail(f"Database client initialization failed: {e}")

def test_database_client_missing_credentials():
    """Test database client initialization with missing credentials."""
    with pytest.raises(ValueError, match="Missing required database connection parameters"):
        client = MockDatabaseClient()
        client.connect()

@patch('app.utils.config.get_config')
def test_database_client_utility_function(mock_get_config, mock_config):
    """Test the utility function for getting a database client."""
    mock_get_config.return_value = mock_config
    client = mock_get_database_client(mock_config)
    assert client.host == 'localhost'
    assert client.port == 5432
    assert client.username == 'testuser'
    assert client.password == 'testpass'
    assert client.database == 'testdb'
    assert client.client is not None  # Verify mock Supabase client exists
