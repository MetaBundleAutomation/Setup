#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Google Search module to find relevant news articles for stock tickers.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional, Union

# Add the project root to path if running this file directly
if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.utils.logger import get_logger

logger = get_logger(__name__)


class GoogleSearch:
    """
    Class to handle Google Custom Search API operations.
    """
    
    def __init__(self, api_key: str, engine_id: str):
        """
        Initialize the GoogleSearch client.
        
        Args:
            api_key: Google API key
            engine_id: Google Custom Search Engine ID
        """
        self.api_key = api_key
        self.engine_id = engine_id
        logger.debug(f"GoogleSearch client initialized with engine ID: {engine_id[:6]}...")
    
    async def search_ticker_news(
        self, 
        ticker: str, 
        max_results: int = 10,
        days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Search for news about a ticker symbol.
        
        Args:
            ticker: Stock ticker symbol
            max_results: Maximum number of results to return
            days_back: How many days back to search
            
        Returns:
            List of search result dictionaries
        """
        # Prepare date restriction (Google format: dN where N is number of days back)
        date_restrict = f"d{days_back}"
        
        # Prepare search query
        query = f"{ticker} stock news"
        
        logger.info(f"Searching for: {query} within past {days_back} days")
        
        try:
            # Validate credentials before proceeding
            if not self.api_key or not self.engine_id:
                logger.error("Missing Google Search API credentials. API Key or Engine ID is empty.")
                return []

            # Log the actual values we're using (truncated for security)
            logger.debug(f"Using API key: {self.api_key[:6]}... and Engine ID: {self.engine_id}")
            
            # Using run_in_executor to make the synchronous Google API call in a thread pool
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                self._execute_search,
                query,
                date_restrict,
                max_results
            )
            return results
        except Exception as e:
            logger.error(f"Error searching for {ticker}: {str(e)}")
            return []
    
    async def search_with_date_range(
        self,
        query: str,
        from_date: Union[date, datetime, str],
        to_date: Union[date, datetime, str],
        max_results: int = 10,
        news_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search for articles with custom query and date range.
        
        Args:
            query: Search query string
            from_date: Start date (inclusive) in the format YYYY-MM-DD
            to_date: End date (inclusive) in the format YYYY-MM-DD
            max_results: Maximum number of results to return
            news_only: If True, limit search to news sites only
            
        Returns:
            List of search result dictionaries
        """
        # Format dates if needed
        if isinstance(from_date, str):
            from_date = datetime.strptime(from_date, "%Y-%m-%d").date()
        elif isinstance(from_date, datetime):
            from_date = from_date.date()
            
        if isinstance(to_date, str):
            to_date = datetime.strptime(to_date, "%Y-%m-%d").date()
        elif isinstance(to_date, datetime):
            to_date = to_date.date()
            
        # Convert date range to Google's format
        # Google uses YYYYMMDD:YYYYMMDD format for sort=date
        date_range = f"{from_date.strftime('%Y%m%d')}:{to_date.strftime('%Y%m%d')}"
        
        # Adjust the query for news sources if requested
        actual_query = query
        if news_only:
            # Add terms that target news articles
            actual_query = f"{query} site:news.google.com OR site:reuters.com OR site:bloomberg.com OR site:wsj.com OR site:nytimes.com OR site:ft.com OR site:cnbc.com OR site:bbc.com OR site:theguardian.com OR inurl:news OR inurl:article"
            
        logger.info(f"Searching for: '{actual_query}' between {from_date} and {to_date}")
        
        try:
            # Validate credentials before proceeding
            if not self.api_key or not self.engine_id:
                logger.error("Missing Google Search API credentials. API Key or Engine ID is empty.")
                return []
                
            # Using run_in_executor to make the synchronous Google API call in a thread pool
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                self._execute_search_with_date_range,
                actual_query,
                date_range,
                max_results,
                news_only
            )
            return results
        except Exception as e:
            logger.error(f"Error searching for '{query}': {str(e)}")
            return []

    def _execute_search(self, query: str, date_restrict: str, max_results: int) -> List[Dict[str, Any]]:
        """
        Execute the Google search (synchronous).
        
        Args:
            query: Search query string
            date_restrict: Date restriction in Google format (e.g. 'd30' for 30 days)
            max_results: Maximum number of results
            
        Returns:
            List of search result dictionaries
        """
        try:
            service = build("customsearch", "v1", developerKey=self.api_key)
            
            # Split the search into multiple calls if more than 10 results needed
            # (Google API limit is 10 per request)
            all_results = []
            for i in range(0, min(max_results, 100), 10):
                response = service.cse().list(
                    q=query,
                    cx=self.engine_id,
                    dateRestrict=date_restrict,
                    num=min(10, max_results - i),
                    start=i + 1
                ).execute()
                
                if "items" in response:
                    all_results.extend(response["items"])
                
                if len(all_results) >= max_results or "items" not in response:
                    break
            
            # Extract relevant information
            formatted_results = []
            for item in all_results:
                # Try multiple ways to extract the date
                published_time = None
                if "pagemap" in item and "metatags" in item["pagemap"] and item["pagemap"]["metatags"]:
                    tags = item["pagemap"]["metatags"][0]
                    published_time = (
                        tags.get("article:published_time") or 
                        tags.get("og:article:published_time") or 
                        tags.get("datePublished")
                    )
                
                formatted_results.append({
                    "title": item.get("title"),
                    "link": item.get("link"),
                    "snippet": item.get("snippet"),
                    "source": item.get("displayLink"),
                    "published_time": published_time
                })
            
            logger.info(f"Google Search returned {len(formatted_results)} results")
            return formatted_results[:max_results]
            
        except HttpError as e:
            logger.error(f"Google API error: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in Google Search: {str(e)}")
            return []

    def _execute_search_with_date_range(self, query: str, date_range: str, max_results: int, news_only: bool = True) -> List[Dict[str, Any]]:
        """
        Execute Google search with specific date range (synchronous).
        
        Args:
            query: Search query string
            date_range: Date range in format YYYYMMDD:YYYYMMDD
            max_results: Maximum number of results
            news_only: If True, focus on news sources
            
        Returns:
            List of search result dictionaries
        """
        try:
            service = build("customsearch", "v1", developerKey=self.api_key)
            
            # Split the search into multiple calls if more than 10 results needed
            # (Google API limit is 10 per request)
            all_results = []
            for i in range(0, min(max_results, 100), 10):
                logger.debug(f"Executing Google search for '{query}' with date range {date_range}")
                
                # For date range search, we need to use specific parameters
                from_date, to_date = date_range.split(":")
                
                # First try with the date range parameter
                params = {
                    "q": query,
                    "cx": self.engine_id,
                    "num": min(10, max_results - i),
                    "start": i + 1,
                }
                
                # For news searches
                if news_only:
                    # Use the news search type if available in your engine configuration
                    params["searchType"] = "news"
                    # Sort by date for news
                    params["sort"] = "date"
                
                # Google API doesn't directly support date range in the way we're trying to use it
                # Instead, we'll use a combination of dateRestrict
                # Calculate days back from today to from_date
                from_date_obj = datetime.strptime(from_date, "%Y%m%d").date()
                to_date_obj = datetime.strptime(to_date, "%Y%m%d").date()
                today = datetime.now().date()
                
                # Use the more recent date as our date restrict
                days_back = (today - from_date_obj).days
                
                if days_back > 0:
                    params["dateRestrict"] = f"d{days_back}"
                    logger.debug(f"Using dateRestrict: d{days_back}")
                
                try:
                    response = service.cse().list(**params).execute()
                    
                    if "items" in response:
                        # Process each result
                        for item in response["items"]:
                            # Skip corporate domains if news_only is True
                            if news_only:
                                # Extract the domain
                                domain = item.get("displayLink", "").lower()
                                # Skip corporate and non-news domains
                                if any(x in domain for x in ["nvidia.com", "amd.com", "intel.com", "microsoft.com", "apple.com", "github.com", "stackoverflow.com"]):
                                    logger.debug(f"Skipping corporate domain: {domain}")
                                    continue
                            
                            # Add to results
                            all_results.append(item)
                    
                    if len(all_results) >= max_results or "items" not in response:
                        break
                        
                except HttpError as e:
                    logger.warning(f"Google search error: {str(e)}")
                    # Don't immediately return, try with different parameters
                    
            # Extract relevant information and filter for articles with published dates
            formatted_results = []
            for item in all_results:
                # Try multiple ways to extract the date
                published_time = None
                has_date = False
                
                # Look for date in metatags first
                if "pagemap" in item and "metatags" in item["pagemap"] and item["pagemap"]["metatags"]:
                    tags = item["pagemap"]["metatags"][0]
                    published_time = (
                        tags.get("article:published_time") or 
                        tags.get("og:article:published_time") or 
                        tags.get("datePublished")
                    )
                    
                # Also check for date in other areas of the pagemap
                if not published_time and "pagemap" in item:
                    # Check in article or newsarticle sections
                    for section_name in ["article", "newsarticle"]:
                        if section_name in item["pagemap"] and item["pagemap"][section_name]:
                            published_time = item["pagemap"][section_name][0].get("datepublished")
                            if published_time:
                                break
                    
                    # Check in creativework section
                    if not published_time and "creativework" in item["pagemap"] and item["pagemap"]["creativework"]:
                        published_time = item["pagemap"]["creativework"][0].get("datepublished")
                
                # If we found a date, add the result
                has_date = published_time is not None
                
                # Only include if it's a genuine news article with a date (if news_only is True)
                if not news_only or has_date:
                    formatted_results.append({
                        "title": item.get("title"),
                        "link": item.get("link"),
                        "snippet": item.get("snippet"),
                        "source": item.get("displayLink"),
                        "published_time": published_time
                    })
            
            logger.info(f"Google Search returned {len(formatted_results)} news results for date range search")
            return formatted_results[:max_results]
            
        except HttpError as e:
            logger.error(f"Google API error in date range search: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in Google Search with date range: {str(e)}")
            return []
