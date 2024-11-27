"""
Logging configuration for the application.
"""
import json
import logging
import logging.config
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from app.core.config import settings

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_fields = {
            "app": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT
        }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        # Create the base log entry
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add default fields
        log_entry.update(self.default_fields)
        
        # Add extra fields from the record
        if hasattr(record, "extra"):
            log_entry.update(record.extra)
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
        
        return json.dumps(log_entry)

# Logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": JSONFormatter
        },
        "console": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console",
            "stream": sys.stdout
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "json",
            "filename": "logs/error.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "level": "ERROR"
        },
        "info_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "json",
            "filename": "logs/info.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "level": "INFO"
        }
    },
    "loggers": {
        "": {  # Root logger
            "handlers": ["console", "error_file", "info_file"],
            "level": "INFO",
            "propagate": True
        },
        "app": {  # Application logger
            "handlers": ["console", "error_file", "info_file"],
            "level": "INFO",
            "propagate": False
        }
    }
}

# Initialize logging configuration
logging.config.dictConfig(LOGGING_CONFIG)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Name of the logger, typically __name__
    
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)

# Create default logger
logger = get_logger(__name__)
