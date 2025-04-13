#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Configuration module for the DataProcessor application.
Loads settings from environment variables and provides them to the application.
"""

import os
import sys
from typing import Optional

# For Pydantic v2, BaseSettings is now in pydantic_settings
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

# Add the project root to the Python path for direct imports if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    GOOGLE_SEARCH_API_KEY: str = Field(default="", env="GOOGLE_SEARCH_API_KEY")
    GOOGLE_SEARCH_ENGINE_ID: str = Field(default="", env="GOOGLE_SEARCH_ENGINE_ID")
    
    # LLM Configuration
    LLM_HOST: str = Field(default="localhost", env="LLM_HOST")
    LLM_PORT: int = Field(default=8080, env="LLM_PORT")
    LLM_MODEL: str = Field(default="deepseek-v1", env="LLM_MODEL")
    
    # Application Settings
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    MAX_CONCURRENT_SCRAPES: int = Field(default=10, env="MAX_CONCURRENT_SCRAPES")
    MAX_SEARCH_RESULTS: int = Field(default=20, env="MAX_SEARCH_RESULTS")
    SUMMARY_MAX_LENGTH: int = Field(default=200, env="SUMMARY_MAX_LENGTH")
    
    class Config:
        """Pydantic config for Settings."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Create a singleton instance to be imported by other modules
settings = Settings()
