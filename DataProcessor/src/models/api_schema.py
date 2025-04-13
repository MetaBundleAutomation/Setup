#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
API request/response models for the DataProcessor FastAPI application.
"""

from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """
    Search request model for the /search endpoint.
    """
    search_term: str = Field(..., description="Term to search for (e.g., 'climate change', 'artificial intelligence')")
    from_date: date = Field(..., description="Start date for the search (format: YYYY-MM-DD)")
    to_date: date = Field(..., description="End date for the search (format: YYYY-MM-DD)")
    max_results: int = Field(10, description="Maximum number of results to return (default: 10)")
    topic: Optional[str] = Field(None, description="Optional topic filter (business, technology, health, science, entertainment, sports, world, nation)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "search_term": "climate change",
                "from_date": "2025-03-01",
                "to_date": "2025-04-01",
                "max_results": 10,
                "topic": "business"
            }
        }


class ArticleResponse(BaseModel):
    """
    Model for a scraped article in the response.
    Simplified to include only the essential fields requested by the user.
    """
    title: str = Field(..., description="Article title")
    link: str = Field(..., description="URL to the article")
    source: str = Field(..., description="Publication source name")
    publish_date: str = Field(..., description="Article publication date")


class SearchResponse(BaseModel):
    """
    Search response model for the /search endpoint.
    """
    search_term: str
    from_date: date
    to_date: date
    total_results: int
    articles: List[ArticleResponse]
    processing_time: float
