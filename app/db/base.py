from typing import Optional
from supabase import create_client, Client
from app.utils.config import get_config
from app.utils.logger import get_logger

logger = get_logger(__name__)

class DatabaseClient:
    """
    Unified database client for managing Supabase connections.
    """
    _instance: Optional['DatabaseClient'] = None
    _supabase_client: Optional[Client] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the DatabaseClient if not already initialized."""
        if self._supabase_client is None:
            self._init_supabase()

    def _init_supabase(self):
        """Initialize Supabase client with configuration."""
        supabase_url = get_config('SUPABASE_URL')
        supabase_key = get_config('SUPABASE_KEY')

        if not supabase_url or not supabase_key:
            raise ValueError("Missing Supabase configuration: URL or Key not found")

        try:
            self._supabase_client = create_client(supabase_url, supabase_key)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}")
            raise

    @property
    def client(self) -> Client:
        """
        Get the Supabase client instance.
        
        Returns:
            Client: Initialized Supabase client
        """
        if self._supabase_client is None:
            self._init_supabase()
        return self._supabase_client

    def get_connection(self) -> Client:
        """
        Get a database connection.
        
        Returns:
            Client: Active Supabase client connection
        """
        return self.client

def get_database_client() -> DatabaseClient:
    """
    Get the singleton database client instance.
    
    Returns:
        DatabaseClient: Configured database client
    """
    return DatabaseClient()
