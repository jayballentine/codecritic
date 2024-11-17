"""
Test suite for the LLM model manager.
"""
import pytest
import os
from unittest.mock import patch, Mock
import yaml
from pathlib import Path

class TestModelManager:
    """
    Test suite for ModelManager class.
    
    Tests the basic model configuration and fallback behavior.
    """
    
    @pytest.fixture
    def mock_config(self, tmp_path):
        """Create a temporary config file."""
        config = {
            "models": {
                "primary": {
                    "name": "gpt-4",
                    "provider": "openai"
                },
                "backup": {
                    "name": "gpt-3.5-turbo",
                    "provider": "openai"
                }
            }
        }
        config_path = tmp_path / "model_config.yml"
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        return str(config_path)

    @pytest.fixture
    def mock_env(self):
        """Mock environment variables."""
        return {
            "OPENAI_API_KEY": "test-key-123",
            "ANTHROPIC_API_KEY": "test-key-456"
        }

    def test_model_initialization(self, mock_config, mock_env):
        """Test basic model manager initialization."""
        with patch.dict(os.environ, mock_env):
            from app.models.model_manager import ModelManager
            manager = ModelManager(mock_config)
            
            assert manager.current_model == "gpt-4"
            assert manager.current_provider == "openai"
            assert manager.api_key == mock_env["OPENAI_API_KEY"]

    def test_fallback_on_error(self, mock_config, mock_env):
        """Test fallback to backup model on error."""
        with patch.dict(os.environ, mock_env):
            from app.models.model_manager import ModelManager
            manager = ModelManager(mock_config)
            
            # Simulate error with primary model
            manager.handle_model_error()
            
            assert manager.current_model == "gpt-3.5-turbo"
            assert manager.current_provider == "openai"
            assert manager.api_key == mock_env["OPENAI_API_KEY"]

    def test_reset_to_primary(self, mock_config, mock_env):
        """Test resetting back to primary model."""
        with patch.dict(os.environ, mock_env):
            from app.models.model_manager import ModelManager
            manager = ModelManager(mock_config)
            
            # Switch to backup and then reset
            manager.handle_model_error()
            manager.reset_to_primary()
            
            assert manager.current_model == "gpt-4"
            assert manager.current_provider == "openai"

    def test_api_key_handling(self, mock_config, mock_env):
        """Test API key access and validation."""
        with patch.dict(os.environ, mock_env):
            from app.models.model_manager import ModelManager
            manager = ModelManager(mock_config)
            
            assert manager.api_key == mock_env["OPENAI_API_KEY"]
            
            # Test missing API key
            with patch.dict(os.environ, {}, clear=True):
                with pytest.raises(ValueError):
                    ModelManager(mock_config)
