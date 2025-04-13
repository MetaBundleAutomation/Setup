#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Custom logger module for DataProcessor.
"""

import os
import sys
from typing import Optional

from loguru import logger as loguru_logger

# Get log level from environment or use INFO as default
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Configure loguru logger
loguru_logger.remove()  # Remove default handler
loguru_logger.add(
    sys.stderr,
    level=LOG_LEVEL,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)
loguru_logger.add(
    "logs/dataprocessor.log",
    rotation="10 MB",
    retention="1 week",
    level=LOG_LEVEL,
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}"
)


def get_logger(name: Optional[str] = None) -> loguru_logger.__class__:
    """
    Get a configured logger instance with the given name.
    
    Args:
        name: Logger name (module name)
        
    Returns:
        Configured logger instance
    """
    return loguru_logger.bind(name=name)
