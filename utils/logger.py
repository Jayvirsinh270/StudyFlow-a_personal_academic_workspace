"""
Logging Utility
Centralized logging configuration for StudyFlow application
"""

import logging
import os
from pathlib import Path
from datetime import datetime


class StudyFlowLogger:
    """Centralized logger for the application"""
    
    _instance = None
    _logger = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StudyFlowLogger, cls).__new__(cls)
            cls._instance._setup_logger()
        return cls._instance
    
    def _setup_logger(self):
        """Setup the logger with file and console handlers"""
        self._logger = logging.getLogger("StudyFlow")
        self._logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if self._logger.handlers:
            return
        
        # Create logs directory
        logs_dir = Path(__file__).parent.parent.parent / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # File handler - debug level
        log_file = logs_dir / f"studyflow_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self._logger.addHandler(file_handler)
        
        # Console handler - info level
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        self._logger.addHandler(console_handler)
    
    @property
    def logger(self):
        """Get the logger instance"""
        return self._logger
    
    def debug(self, message):
        """Log debug message"""
        self._logger.debug(message)
    
    def info(self, message):
        """Log info message"""
        self._logger.info(message)
    
    def warning(self, message):
        """Log warning message"""
        self._logger.warning(message)
    
    def error(self, message, exc_info=False):
        """Log error message"""
        self._logger.error(message, exc_info=exc_info)
    
    def critical(self, message, exc_info=False):
        """Log critical message"""
        self._logger.critical(message, exc_info=exc_info)


# Global logger instance
logger = StudyFlowLogger().logger


def get_logger():
    """Get the global logger instance"""
    return logger
