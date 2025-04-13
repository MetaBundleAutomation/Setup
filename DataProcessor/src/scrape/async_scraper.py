#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Asynchronous web scraper to fetch article content from URLs.
"""

import asyncio
import time
import random
from typing import List, Dict, Any, Optional
import aiohttp
from aiohttp import ClientTimeout, ClientSession
from newspaper import Article
import logging

from src.utils.logger import get_logger
from src.models.data_schema import RawArticle

logger = get_logger(__name__)


class AsyncScraper:
    """
    Asynchronous scraper for fetching article content from URLs.
    """
    
    # Common user agents to rotate through
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/112.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
    ]
    
    def __init__(self, max_concurrent: int = 10, timeout: int = 30, retry_count: int = 2, retry_delay: int = 2):
        """
        Initialize the AsyncScraper.
        
        Args:
            max_concurrent: Maximum number of concurrent requests
            timeout: Timeout for each request in seconds
            retry_count: Number of retries for failed requests
            retry_delay: Delay between retries in seconds
        """
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.semaphore = asyncio.Semaphore(max_concurrent)
        logger.debug(f"AsyncScraper initialized with max_concurrent={max_concurrent}, retry_count={retry_count}")
    
    async def scrape_urls(self, urls: List[str]) -> List[Optional[RawArticle]]:
        """
        Scrape multiple URLs asynchronously.
        
        Args:
            urls: List of URLs to scrape
            
        Returns:
            List of RawArticle objects
        """
        if not urls:
            logger.warning("No URLs provided to scrape")
            return []
            
        logger.info(f"Scraping {len(urls)} URLs with max concurrency of {self.max_concurrent}")
        
        # Create a ClientSession with timeout and custom headers
        session_timeout = ClientTimeout(total=self.timeout)
        conn = aiohttp.TCPConnector(limit=self.max_concurrent, ssl=False)
        
        async with ClientSession(
            timeout=session_timeout, 
            connector=conn, 
            headers=self._get_headers()
        ) as session:
            tasks = [self.scrape_url(session, url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and log them
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error scraping URL {urls[i]}: {str(result)}")
            elif result is not None:
                valid_results.append(result)
        
        logger.info(f"Successfully scraped {len(valid_results)} out of {len(urls)} URLs")
        return valid_results
    
    async def scrape_url(self, session: aiohttp.ClientSession, url: str) -> Optional[RawArticle]:
        """
        Scrape a single URL with retry logic.
        
        Args:
            session: aiohttp ClientSession
            url: URL to scrape
            
        Returns:
            RawArticle object or None if failed
        """
        async with self.semaphore:
            for attempt in range(self.retry_count + 1):
                try:
                    # Add a small random delay to avoid being detected as a bot
                    await asyncio.sleep(random.uniform(0.2, 1.5))
                    
                    logger.debug(f"Scraping URL (attempt {attempt+1}/{self.retry_count+1}): {url}")
                    start_time = time.time()
                    
                    # Use a fresh set of headers for each attempt
                    headers = self._get_headers()
                    
                    # Fetch the HTML
                    async with session.get(url, headers=headers, allow_redirects=True) as response:
                        if response.status != 200:
                            logger.warning(f"Failed to fetch {url} - Status code: {response.status}")
                            if attempt < self.retry_count:
                                retry_delay = self.retry_delay * (attempt + 1)  # Exponential backoff
                                logger.info(f"Retrying in {retry_delay} seconds...")
                                await asyncio.sleep(retry_delay)
                                continue
                            return None
                        
                        html = await response.text()
                    
                    # Parse with newspaper3k in a thread pool to avoid blocking
                    loop = asyncio.get_event_loop()
                    article = await loop.run_in_executor(
                        None,
                        self._parse_with_newspaper,
                        url,
                        html
                    )
                    
                    duration = time.time() - start_time
                    content_length = len(article.content) if article and article.content else 0
                    logger.debug(f"Scraped {url} in {duration:.2f}s - Content length: {content_length}")
                    
                    # If content is too short, it might be a paywall or anti-scraping page
                    if content_length < 200 and attempt < self.retry_count:
                        logger.warning(f"Content too short ({content_length} chars), possible paywall. Retrying...")
                        await asyncio.sleep(self.retry_delay * (attempt + 1))
                        continue
                    
                    return article
                    
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    if attempt < self.retry_count:
                        retry_delay = self.retry_delay * (attempt + 1)
                        logger.warning(f"Connection error for {url}: {str(e)}. Retrying in {retry_delay}s...")
                        await asyncio.sleep(retry_delay)
                    else:
                        logger.error(f"Error scraping {url} after {self.retry_count + 1} attempts: {str(e)}")
                        return None
                except Exception as e:
                    logger.error(f"Unexpected error scraping {url}: {str(e)}")
                    return None
            
            # If we get here, all retries failed
            return None
    
    def _parse_with_newspaper(self, url: str, html: str) -> RawArticle:
        """
        Parse HTML with newspaper3k (synchronous function).
        
        Args:
            url: Source URL
            html: HTML content
            
        Returns:
            RawArticle object with extracted data
        """
        try:
            article = Article(url)
            article.set_html(html)
            article.parse()
            
            # Try to determine the source from the URL
            source = None
            try:
                from urllib.parse import urlparse
                parsed_url = urlparse(url)
                source = parsed_url.netloc.replace('www.', '')
            except Exception:
                source = url.split('/')[2] if len(url.split('/')) > 2 else None
            
            # Extract metadata
            return RawArticle(
                url=url,
                title=article.title,
                content=article.text,
                html=html,
                publish_date=article.publish_date,
                authors=article.authors,
                source=source,
                keywords=article.keywords,
                summary=article.summary,
                images=article.images
            )
        except Exception as e:
            logger.error(f"Error parsing article from {url}: {str(e)}")
            # Return a partial article with what we have
            return RawArticle(
                url=url,
                title=None,
                content=None,
                html=html,
                publish_date=None,
                authors=[],
                source=url.split('/')[2] if len(url.split('/')) > 2 else None,
                keywords=[],
                summary=None,
                images=set()
            )
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Generate random headers to avoid detection.
        
        Returns:
            Dictionary of HTTP headers
        """
        return {
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
        }
