import logging
import sys
from datetime import datetime
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors and emojis for different log levels"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    
    EMOJIS = {
        'DEBUG': '🔍',
        'INFO': '📋',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '🚨',
    }
    
    RESET = '\033[0m'
    
    def format(self, record):
        # Get color and emoji for log level
        color = self.COLORS.get(record.levelname, '')
        emoji = self.EMOJIS.get(record.levelname, '📋')
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Create formatted message
        formatted_msg = f"{color}{emoji} [{timestamp}] {record.levelname}: {record.getMessage()}{self.RESET}"
        
        return formatted_msg


def setup_logger(name: str = "vidsnatch", level: int = logging.INFO) -> logging.Logger:
    """Setup and configure logger with colored output and timestamps"""
    
    logger = logging.getLogger(name)
    
    # Avoid adding multiple handlers if logger already exists
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Set custom formatter
    formatter = ColoredFormatter()
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    # Prevent propagation to root logger to avoid duplicate messages
    logger.propagate = False
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get logger instance"""
    if name is None:
        name = "vidsnatch"
    return logging.getLogger(name)
