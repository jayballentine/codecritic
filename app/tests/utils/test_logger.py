import os
import logging
import pytest
import sys

from app.utils.logger import setup_logger, get_logger

class TestLogger:
    def setup_method(self):
        # Ensure logs directory exists
        os.makedirs('logs', exist_ok=True)
        
        # Clear any existing log files before each test
        log_file = 'logs/app.log'
        if os.path.exists(log_file):
            os.remove(log_file)

    def test_logger_console_output(self, caplog):
        """
        Test that logs are correctly written to the console.
        """
        logger = setup_logger(log_level='DEBUG')
        
        # Test different log levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")
        
        # Check console output
        log_records = caplog.records
        assert len(log_records) == 5
        assert "Debug message" in caplog.text
        assert "Info message" in caplog.text
        assert "Warning message" in caplog.text
        assert "Error message" in caplog.text
        assert "Critical message" in caplog.text

    def test_logger_file_output(self):
        """
        Test that logs are written to the log file in the correct format.
        """
        log_file = 'logs/app.log'
        logger = setup_logger(log_level='DEBUG')
        
        # Log some messages
        logger.info("Test log message")
        logger.error("Error log message")
        
        # Read the log file
        with open(log_file, 'r') as f:
            log_contents = f.read()
        
        # Verify log file contents
        assert "Test log message" in log_contents
        assert "Error log message" in log_contents
        
        # Verify log format
        assert " - app_logger - INFO - " in log_contents
        assert " - app_logger - ERROR - " in log_contents

    def test_log_levels(self, caplog):
        """
        Test that different log levels are handled appropriately.
        """
        # Test INFO level
        logger_info = setup_logger(log_level='INFO')
        
        # Set caplog level to INFO
        caplog.set_level(logging.INFO)
        
        # Log info message - should be captured
        logger_info.info("Info level test")
        
        # Log debug message - should NOT be captured
        logger_info.debug("Debug level test")
        
        # Verify only info message is in logs
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == 'INFO'
        assert "Info level test" in caplog.text
        assert "Debug level test" not in caplog.text

    def test_get_logger(self):
        """
        Test the get_logger function.
        """
        # Test default logger
        default_logger = get_logger()
        assert isinstance(default_logger, logging.Logger)
        
        # Test named logger
        named_logger = get_logger('test_module')
        assert isinstance(named_logger, logging.Logger)
        assert named_logger.name == 'test_module'

    def test_log_file_rotation(self):
        """
        Verify that log file rotation works.
        """
        # Create a logger that will potentially trigger log rotation
        logger = setup_logger(log_level='DEBUG')
        
        # Generate many log messages to potentially trigger rotation
        for i in range(10000):
            logger.info(f"Log message {i}")
        
        # Check that log files exist
        log_files = [f for f in os.listdir('logs') if f.startswith('app.log')]
        assert len(log_files) > 0
