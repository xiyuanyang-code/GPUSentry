"""Logging module for GPUSentry with both file and console output."""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler


def setup_logger(name: str, log_file: str = None, level: int = logging.INFO) -> logging.Logger:
    """Set up a logger with both console and file handlers.
    
    Args:
        name: Name of the logger
        log_file: Path to log file. If None, uses default location
        level: Logging level (default: INFO)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Prevent adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Create formatters
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if log_file is None:
        home_dir = os.path.expanduser("~")
        gpusentry_dir = os.path.join(home_dir, ".gpusentry", "logs")
        os.makedirs(gpusentry_dir, exist_ok=True)
        log_file = os.path.join(gpusentry_dir, f"gpusentry_{datetime.now().strftime('%Y%m%d')}.log")
    
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=100*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    return logger


# Global logger instance for the application
app_logger = setup_logger("gpusentry")