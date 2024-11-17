import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

def setup_logger(name: str = 'app_logger', log_level: str = 'INFO') -> logging.Logger:
    """
    Set up a logger with console and file logging capabilities.
    
    Args:
        name (str): Name of the logger
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        logging.Logger: Configured logger instance
    """
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.handlers.clear()  # Clear any existing handlers
    logger.setLevel(logging.NOTSET)  # Reset to capture all levels initially
    
    # Set log level
    log_level = log_level.upper()
    numeric_level = getattr(logging, log_level)
    logger.setLevel(numeric_level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File Handler with rotation
    file_handler = RotatingFileHandler(
        'logs/app.log', 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

# Create a default logger
logger = setup_logger()

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance, optionally with a custom name.
    
    Args:
        name (Optional[str]): Custom logger name
    
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name) if name else logger
