"""Logging configuration module for the FastAPI application.

This module provides a consistent logging format that matches Uvicorn's style.
"""

__author__ = "Nikolai Alexander"
__email__ = "njalexander93@gmail.com"
__version__ = "1.0.0"
__date__ = "2025-02-28"
__license__ = "Proprietary"
__copyright__ = "Copyright (c) 2025 MartyChat"

import logging
import sys
from typing import ClassVar


class UvicornStyleFormatter(logging.Formatter):
    """Formatter that mimics Uvicorn's log formatting."""

    level_name_colors: ClassVar[dict[str, str]] = {
        "DEBUG": "\x1b[36m",  # Cyan
        "INFO": "\x1b[32m",  # Green
        "WARNING": "\x1b[33m",  # Yellow
        "ERROR": "\x1b[31m",  # Red
        "CRITICAL": "\x1b[31m\x1b[1m",  # Bold Red
    }
    reset_color = "\x1b[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with Uvicorn-style formatting.

        This method adds a colored level name with a colon to the log record. The level name is colored based on the
        log level.

        Args:
            record: The log record to format.

        Returns:
            str: The formatted log record
        """
        # Create a colored level name with colon
        if record.levelname in self.level_name_colors:
            color = self.level_name_colors[record.levelname]
            level_colon = f"{color}{record.levelname}:{self.reset_color}"
        else:
            level_colon = f"{record.levelname}:"

        # Set it as a custom attribute on the record
        record.level_colon = f"{level_colon:<8}"

        # Format the record
        return super().format(record)


def setup_logger(
    name: str = "martychat",
    level: str = "INFO",
) -> logging.Logger:
    """
    Sets up a logger with Uvicorn-style formatting.

    Args:
        name: The name of the logger (default: "martychat")
        level: The logging level (default: "INFO")

    Returns:
        logging.Logger: Configured logger instance
    """
    # Get the logger
    logger = logging.getLogger(name)

    # Clear any existing handlers to prevent duplicate logging
    logger.handlers.clear()

    # Prevent logging from propagating to the root logger
    logger.propagate = False

    # Set the log level
    logger.setLevel(getattr(logging, level.upper()))

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)

    # Create formatter
    formatter = UvicornStyleFormatter("%(level_colon)s     %(message)s")

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


# Configure root logger to prevent duplicate logging
root_logger = logging.getLogger()
root_logger.handlers.clear()

# Create default logger instance
logger = setup_logger()
