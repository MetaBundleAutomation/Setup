#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Launch script for the DataProcessor API server.
"""

import os
import sys
import uvicorn
from pathlib import Path

# Add project root to path for imports to work correctly
project_root = str(Path(__file__).parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils.logger import get_logger

logger = get_logger(__name__)

if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Run the DataProcessor API server')
    parser.add_argument('-p', '--port', type=int, default=8000, help='Port to run the server on')
    parser.add_argument('--host', type=str, default="0.0.0.0", help='Host to run the server on')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload for development')
    args = parser.parse_args()
    
    logger.info(f"Starting DataProcessor API server on {args.host}:{args.port}")
    
    # Run the server
    uvicorn.run(
        "src.api.app:app", 
        host=args.host, 
        port=args.port, 
        reload=args.reload
    )
