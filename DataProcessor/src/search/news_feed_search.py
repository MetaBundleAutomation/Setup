#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
News feed searcher using Google News RSS and other free news sources.
"""

import sys
import os
import re
import asyncio
import aiohttp
import feedparser
import time
import json
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Union, Optional, Tuple
from pathlib import Path
from urllib.parse import quote, urlparse
from bs4 import BeautifulSoup
import hashlib

# Add project root to path for imports to work correctly
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils.logger import get_logger

logger = get_logger(__name__)

class NewsFeedSearch:
    """
    Class to search for news articles using free RSS feeds.
    """
    
    # Base URLs for different news sources
    GOOGLE_NEWS_URL = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
    GOOGLE_NEWS_SECTION_URL = "https://news.google.com/rss/headlines/section/topic/{topic}?hl=en-US&gl=US&ceid=US:en"
    
    # Topics available in Google News
    TOPICS = {
        "business": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB",
        "technology": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlnQVAB",
        "health": "CAAqIQgKIhtDQkFTRGdvSUwyMHZNR3QwTlRFU0FtVnVLQUFQAQ",
        "science": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp0Y1RJU0FtVnVHZ0pWVXlnQVAB",
        "entertainment": "CAAqJggKIiBDQkFTRWdvSUwyMHZNREpxYW5RU0FtVnVHZ0pWVXlnQVAB",
        "sports": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdvU0FtVnVHZ0pWVXlnQVAB",
        "world": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtVnVHZ0pWVXlnQVAB",
        "nation": "CAAqIggKIhxDQkFTRHdvSUwyMHZNRGxqZHpNd0VnSmxiaWdBUAE"
    }
    
    # Cache directory
    CACHE_DIR = Path(project_root) / "cache" / "rss_feeds"
    
    def __init__(self, user_agent: str = None, cache_expiry: int = 3600):
        """
        Initialize the NewsFeedSearch.
        
        Args:
            user_agent: User agent to use for requests (optional)
            cache_expiry: Cache expiry time in seconds (default: 1 hour)
        """
        self.session = None
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
        self.cache_expiry = cache_expiry
        
        # Create cache directory if it doesn't exist
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        
    async def create_session(self):
        """Create an aiohttp session if one doesn't exist."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={"User-Agent": self.user_agent}
            )
        return self.session
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def search_news(
        self, 
        query: str, 
        from_date: Union[date, datetime, str] = None, 
        to_date: Union[date, datetime, str] = None,
        max_results: int = 10,
        topic: str = None,
        resolve_urls: bool = True,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search for news articles based on query and date range.
        
        Args:
            query: Search query string
            from_date: Start date (optional, default: 7 days ago)
                        Can be a date object, datetime object, or string in YYYY-MM-DD format
            to_date: End date (optional, default: today)
                     Can be a date object, datetime object, or string in YYYY-MM-DD format
            max_results: Maximum number of results to return after filtering
            topic: Specific news topic to search within
            resolve_urls: Whether to resolve Google News redirect URLs
            use_cache: Whether to use cached RSS feed data
            
        Returns:
            List of news article dictionaries
        """
        # Format dates if needed
        if from_date is None:
            from_date = datetime.now().date() - timedelta(days=7)
        elif isinstance(from_date, str):
            try:
                # Handle dates with time components (like 2025-04-13T00:01:00)
                if 'T' in from_date:
                    from_date = datetime.strptime(from_date, "%Y-%m-%dT%H:%M:%S").date()
                else:
                    from_date = datetime.strptime(from_date, "%Y-%m-%d").date()
            except ValueError as e:
                logger.warning(f"Invalid from_date format: {from_date} - {str(e)}")
                from_date = datetime.now().date() - timedelta(days=7)
        elif isinstance(from_date, datetime):
            from_date = from_date.date()
            
        if to_date is None:
            to_date = datetime.now().date()
        elif isinstance(to_date, str):
            try:
                # Handle dates with time components (like 2025-04-13T23:59:59)
                if 'T' in to_date:
                    to_date = datetime.strptime(to_date, "%Y-%m-%dT%H:%M:%S").date()
                else:
                    to_date = datetime.strptime(to_date, "%Y-%m-%d").date()
            except ValueError as e:
                logger.warning(f"Invalid to_date format: {to_date} - {str(e)}")
                to_date = datetime.now().date()
        elif isinstance(to_date, datetime):
            to_date = to_date.date()
        
        logger.info(f"Searching for news: '{query}' between {from_date} and {to_date}")
        
        # Create cache key based on query, topic, and date range
        cache_key = self._generate_cache_key(query, topic, from_date, to_date)
        
        # Try to get from cache
        cached_results = None
        if use_cache:
            cached_results = self._get_from_cache(cache_key)
            if cached_results:
                logger.info(f"Using cached results for '{query}'")
                return cached_results[:max_results]
        
        # Create a session
        await self.create_session()
        
        # Get articles from Google News RSS - JUST ONE API CALL
        google_results = await self._search_google_news(query, topic)
        
        logger.debug(f"RSS feed returned {len(google_results)} results before date filtering")
        
        # Filter by date
        filtered_results = []
        for article in google_results:
            pub_date = article.get("publish_date")
            if pub_date is None:
                # No date, can't filter
                continue
                
            if isinstance(pub_date, str):
                try:
                    # Try to parse the date
                    pub_date = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z").date()
                except (ValueError, TypeError):
                    try:
                        # Try to parse ISO format
                        pub_date = datetime.fromisoformat(pub_date.replace('Z', '+00:00')).date()
                    except (ValueError, TypeError):
                        # If all else fails, keep the article
                        logger.warning(f"Could not parse date: {pub_date}, including article anyway")
                        filtered_results.append(article)
                        continue
            
            # Only include articles within the date range
            # Add debug logging to trace what's happening
            logger.debug(f"Checking date range: article date={pub_date}, from_date={from_date}, to_date={to_date}")
            
            # Fix: Ensure we're comparing dates correctly
            try:
                # Convert dates for comparison if needed
                if isinstance(from_date, datetime):
                    from_date_for_compare = from_date.date()
                else:
                    from_date_for_compare = from_date
                    
                if isinstance(to_date, datetime):
                    to_date_for_compare = to_date.date()
                else:
                    to_date_for_compare = to_date
                    
                if isinstance(pub_date, datetime):
                    pub_date_for_compare = pub_date.date()
                else:
                    pub_date_for_compare = pub_date
                
                # Check if date is within range (inclusive)
                in_range = from_date_for_compare <= pub_date_for_compare <= to_date_for_compare
                logger.debug(f"Date comparison result: in_range={in_range}")
                
                if in_range:
                    filtered_results.append(article)
                    
            except Exception as e:
                logger.warning(f"Error comparing dates: {str(e)}, including article anyway")
                filtered_results.append(article)
        
        logger.debug(f"After date filtering: {len(filtered_results)} results from {len(google_results)} total")
        
        # Sort by date (newest first) and limit to max_results
        sorted_results = sorted(
            filtered_results, 
            key=lambda x: x.get("publish_date", ""), 
            reverse=True
        )[:max_results]
        
        # Resolve Google News redirect URLs in batch if needed
        if resolve_urls:
            # Get all Google News URLs that need resolving
            google_urls = [
                (i, article["link"]) 
                for i, article in enumerate(sorted_results) 
                if "news.google.com" in article["link"]
            ]
            
            if google_urls:
                logger.debug(f"Resolving {len(google_urls)} Google News redirect URLs")
                # Resolve them all in parallel
                resolved_urls = await self._batch_resolve_urls([url for _, url in google_urls])
                
                # Update the articles with resolved URLs
                for (index, _), resolved_url in zip(google_urls, resolved_urls):
                    if resolved_url:
                        sorted_results[index]["link"] = resolved_url
        
        # Cache the results
        if use_cache:
            self._save_to_cache(cache_key, sorted_results)
        
        logger.info(f"Found {len(sorted_results)} news articles for '{query}'")
        return sorted_results
    
    async def _search_google_news(self, query: str, topic: str = None) -> List[Dict[str, Any]]:
        """
        Search Google News RSS for articles.
        
        Args:
            query: Search query string
            topic: Specific news topic to search within
            
        Returns:
            List of news article dictionaries
        """
        try:
            # Determine the URL based on whether we're searching by topic or query
            if topic and topic in self.TOPICS:
                url = self.GOOGLE_NEWS_SECTION_URL.format(topic=self.TOPICS[topic])
                if query:
                    url = f"{url}&q={quote(query)}"
            else:
                url = self.GOOGLE_NEWS_URL.format(query=quote(query))
            
            logger.debug(f"Fetching RSS feed from {url}")
            
            # Important: We only make a single API call to the RSS feed
            # RSS typically returns around 20-30 items by default
            async with self.session.get(url, timeout=30) as response:
                if response.status != 200:
                    logger.error(f"Error fetching Google News RSS: Status {response.status}")
                    return []
                
                content = await response.text()
            
            # Parse the feed
            feed = feedparser.parse(content)
            
            logger.debug(f"RSS feed returned {len(feed.entries)} entries")
            
            results = []
            for entry in feed.entries:
                # Extract information
                title = entry.get("title", "")
                link = entry.get("link", "")
                
                # Publication date 
                pub_date = entry.get("published", "")
                
                # Try to extract source and author
                source = entry.get("source", {}).get("title", "")
                if not source:
                    # Try to extract from title (Google News format: "Title - Source")
                    title_parts = title.split(" - ")
                    if len(title_parts) > 1:
                        source = title_parts[-1]
                        title = " - ".join(title_parts[:-1])
                
                # Extract description/snippet
                description = entry.get("description", "")
                if description:
                    # Clean HTML from description
                    description = BeautifulSoup(description, "html.parser").get_text().strip()
                
                # Try to extract author from various places
                author = entry.get("author", "")
                
                results.append({
                    "title": title,
                    "link": link,
                    "source": source,
                    "publish_date": pub_date,
                    "authors": [author] if author else [],
                    "snippet": description
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching Google News: {str(e)}")
            return []
    
    async def _batch_resolve_urls(self, urls: List[str]) -> List[str]:
        """
        Resolve multiple Google News redirect URLs in parallel.
        
        Args:
            urls: List of Google News redirect URLs
            
        Returns:
            List of resolved real URLs
        """
        if not urls:
            return []
            
        # Set up the tasks
        tasks = [self._extract_real_url(url) for url in urls]
        
        # Run them all in parallel
        return await asyncio.gather(*tasks)
    
    async def _extract_real_url(self, google_url: str) -> str:
        """
        Extract the real URL from a Google News redirect link.
        
        Args:
            google_url: Google News redirect URL
            
        Returns:
            The actual article URL
        """
        try:
            # First try to extract from the URL parameter (faster, no network call)
            parsed = urlparse(google_url)
            if "url=" in parsed.query:
                real_url = parsed.query.split("url=")[1].split("&")[0]
                return real_url
                
            # If that doesn't work, follow the redirect
            async with self.session.get(google_url, allow_redirects=False) as response:
                if response.status in (301, 302):
                    redirect_url = response.headers.get("Location")
                    if redirect_url:
                        return redirect_url
            
            return google_url
        except Exception as e:
            logger.debug(f"Error extracting real URL: {str(e)}")
            return google_url
    
    def _generate_cache_key(self, query: str, topic: str, from_date: date, to_date: date) -> str:
        """
        Generate a cache key based on search parameters.
        
        Args:
            query: Search query
            topic: Topic filter
            from_date: Start date
            to_date: End date
            
        Returns:
            Cache key string
        """
        # Create a unique cache key
        key_str = f"{query}_{topic}_{from_date.isoformat()}_{to_date.isoformat()}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached results if they exist and are not expired.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached results or None
        """
        cache_file = self.CACHE_DIR / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
            
        # Check if cache is expired
        mod_time = cache_file.stat().st_mtime
        if time.time() - mod_time > self.cache_expiry:
            logger.debug(f"Cache expired for key {cache_key}")
            return None
            
        try:
            with open(cache_file, "r") as f:
                data = json.load(f)
                
            logger.debug(f"Loaded {len(data)} results from cache")
            return data
        except Exception as e:
            logger.error(f"Error reading from cache: {str(e)}")
            return None
    
    def _save_to_cache(self, cache_key: str, results: List[Dict[str, Any]]) -> bool:
        """
        Save results to cache.
        
        Args:
            cache_key: Cache key
            results: Search results to cache
            
        Returns:
            Success status
        """
        try:
            cache_file = self.CACHE_DIR / f"{cache_key}.json"
            
            with open(cache_file, "w") as f:
                json.dump(results, f)
                
            logger.debug(f"Saved {len(results)} results to cache")
            return True
        except Exception as e:
            logger.error(f"Error saving to cache: {str(e)}")
            return False
    
    async def get_article_content(self, url: str) -> Dict[str, Any]:
        """
        Get the full content of an article (expensive operation).
        Only call this when a specific article is requested.
        
        Args:
            url: Article URL
            
        Returns:
            Article data with full content
        """
        try:
            # Import newspaper3k only when needed (it's expensive)
            from newspaper import Article
            
            await self.create_session()
            
            # Fetch the article HTML
            async with self.session.get(url, timeout=30) as response:
                if response.status != 200:
                    logger.error(f"Error fetching article: Status {response.status}")
                    return {"url": url, "error": f"HTTP error {response.status}"}
                
                html = await response.text()
            
            # Use newspaper3k to parse the article (CPU intensive)
            loop = asyncio.get_event_loop()
            article = await loop.run_in_executor(None, self._parse_with_newspaper3k, url, html)
            
            return article
            
        except Exception as e:
            logger.error(f"Error getting article content: {str(e)}")
            return {"url": url, "error": str(e)}
    
    def _parse_with_newspaper3k(self, url: str, html: str) -> Dict[str, Any]:
        """
        Parse an article with newspaper3k (CPU intensive).
        
        Args:
            url: Article URL
            html: Article HTML
            
        Returns:
            Parsed article data
        """
        from newspaper import Article
        
        try:
            article = Article(url)
            article.set_html(html)
            article.parse()
            
            # Extract metadata
            return {
                "url": url,
                "title": article.title,
                "authors": article.authors,
                "publish_date": article.publish_date,
                "text": article.text,
                "top_image": article.top_image,
                "images": list(article.images),
                "keywords": article.keywords,
                "summary": article.summary
            }
        except Exception as e:
            logger.error(f"Error parsing article: {str(e)}")
            return {"url": url, "error": str(e)}
