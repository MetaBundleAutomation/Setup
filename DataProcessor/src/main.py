#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Main entry point for DataProcessor application.
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports to work correctly
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.config import settings
from src.search.google_search import GoogleSearch
from src.scrape.async_scraper import AsyncScraper
from src.utils.logger import get_logger
from src.models.data_schema import RawArticle

logger = get_logger(__name__)

# Output directory for storing articles
OUTPUT_DIR = Path(project_root) / "output"

async def process_ticker(ticker: str, days_back: int = 30) -> List[Dict[str, Any]]:
    """
    Process a single stock ticker by searching for news,
    scraping articles, and storing the results.
    
    Args:
        ticker: Stock symbol to search for
        days_back: Number of days to look back
        
    Returns:
        List of processed article data
    """
    logger.info(f"Processing ticker {ticker} for the past {days_back} days")
    
    # Initialize Google search
    google_search = GoogleSearch(
        api_key=settings.GOOGLE_SEARCH_API_KEY,
        engine_id=settings.GOOGLE_SEARCH_ENGINE_ID
    )
    
    # Search for news articles
    search_results = await google_search.search_ticker_news(
        ticker=ticker,
        days_back=days_back,
        max_results=settings.MAX_SEARCH_RESULTS
    )
    
    logger.info(f"Found {len(search_results)} search results for {ticker}")
    
    if not search_results:
        return []
    
    # Extract URLs - note the change from result.link to result["link"]
    urls = [result["link"] for result in search_results]
    
    # Scrape article content
    async_scraper = AsyncScraper(
        max_concurrent=settings.MAX_CONCURRENT_SCRAPES,
        timeout=30
    )
    articles = await async_scraper.scrape_urls(urls)
    
    logger.info(f"Successfully scraped {len(articles)} articles for {ticker}")
    
    if not articles:
        return []
    
    # Process articles into structured output
    processed_articles = []
    for article in articles:
        if not article or not article.content:
            continue
            
        article_data = {
            "url": article.url,
            "title": article.title or "Untitled",
            "source": article.source,
            "publish_date": str(article.publish_date) if article.publish_date else None,
            "authors": article.authors,
            "content_snippet": article.content[:200] + "..." if article.content and len(article.content) > 200 else article.content,
            "keywords": list(article.keywords) if article.keywords else [],
            "images": list(article.images)[:3] if article.images else [],
            "ticker": ticker,
            "extracted_at": datetime.now().isoformat(),
        }
        processed_articles.append(article_data)
    
    logger.info(f"Processed {len(processed_articles)} articles for {ticker}")
    
    # Create output directory if it doesn't exist
    output_dir = OUTPUT_DIR / ticker
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the processed articles to a JSON file
    output_file = output_dir / f"{ticker}_articles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(processed_articles, f, indent=2)
    
    logger.info(f"Saved article data to {output_file}")
    
    # Print article summaries
    print(f"\n{'='*80}\nARTICLES FOR {ticker}\n{'='*80}")
    
    for idx, article in enumerate(processed_articles, 1):
        print(f"\nARTICLE {idx}")
        print(f"URL: {article['url']}")
        print(f"TITLE: {article['title']}")
        print(f"SOURCE: {article['source']}")
        print(f"PUBLISH DATE: {article['publish_date']}")
        print(f"AUTHORS: {', '.join(article['authors']) if article['authors'] else 'Unknown'}")
        print(f"CONTENT SNIPPET: {article['content_snippet']}")
        print(f"KEYWORDS: {', '.join(article['keywords']) if article['keywords'] else 'None'}")
        print(f"IMAGES: {len(article['images'])} images")
        print("-" * 80)
    
    return processed_articles

async def main():
    """
    Main entry point for the application.
    """
    logger.info("Starting DataProcessor")
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # List of stock tickers to process
    tickers = ["AAPL"]
    
    # Process each ticker
    all_articles = []
    for ticker in tickers:
        try:
            ticker_articles = await process_ticker(ticker)
            all_articles.extend(ticker_articles)
        except Exception as e:
            logger.error(f"Error processing ticker {ticker}: {str(e)}")
    
    logger.info(f"Total processed articles: {len(all_articles)}")
    
    # Save the combined results to a JSON file
    output_file = OUTPUT_DIR / f"all_articles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_articles, f, indent=2)
    
    print(f"\nAll article data saved to {output_file}")

if __name__ == "__main__":
    asyncio.run(main())
