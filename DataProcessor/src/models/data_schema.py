#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Data models for the DataProcessor application.
Uses Pydantic for validation and serialization.
"""

from datetime import datetime
from typing import List, Dict, Optional, Set, Union, Any
from pydantic import BaseModel, Field, HttpUrl


class RawArticle(BaseModel):
    """Raw article data as scraped from the web."""
    
    url: str
    title: Optional[str] = None
    content: Optional[str] = None
    html: Optional[str] = None
    publish_date: Optional[datetime] = None
    authors: List[str] = Field(default_factory=list)
    source: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    summary: Optional[str] = None
    images: Set[str] = Field(default_factory=set)


class CleanedArticle(BaseModel):
    """Article after cleaning and content extraction."""
    
    url: str
    title: Optional[str] = None
    content: str
    publish_date: Optional[datetime] = None
    authors: List[str] = Field(default_factory=list)
    source: Optional[str] = None
    
    @classmethod
    def from_raw_article(cls, raw: RawArticle, cleaned_content: str) -> 'CleanedArticle':
        """Create a CleanedArticle from a RawArticle and cleaned content."""
        return cls(
            url=raw.url,
            title=raw.title,
            content=cleaned_content,
            publish_date=raw.publish_date,
            authors=raw.authors,
            source=raw.source
        )


class ArticleSummary(BaseModel):
    """Summary of an article produced by the LLM."""
    
    title: str
    content: str
    sentiment: Optional[float] = None  # -1.0 to 1.0, negative to positive
    keywords: List[str] = Field(default_factory=list)
    
    
class TimelineEvent(BaseModel):
    """A timeline event for a stock ticker."""
    
    id: str = Field(...)
    ticker: str
    date: datetime
    title: str
    summary: str
    url: str
    source: str
    sentiment: Optional[float] = None
    importance: Optional[float] = None  # 0.0 to 1.0, low to high importance
    
    
class ProcessingResult(BaseModel):
    """Complete result of processing a ticker's news."""
    
    ticker: str
    query_date: datetime = Field(default_factory=datetime.now)
    days_processed: int
    events: List[TimelineEvent] = Field(default_factory=list)
    
    @property
    def event_count(self) -> int:
        """Get the number of events."""
        return len(self.events)
