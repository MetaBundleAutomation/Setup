#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script for the news feed RSS search.
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import json

# Add project root to path for imports to work correctly
project_root = str(Path(__file__).parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.search.news_feed_search import NewsFeedSearch
from src.utils.logger import get_logger

logger = get_logger(__name__)

async def test_news_search(query="NVIDIA", days_back=30, max_results=10, topic=None):
    """
    Test the RSS news search with a query.
    
    Args:
        query: Search query
        days_back: Number of days to look back
        max_results: Maximum number of results to return
        topic: Optional topic filter
    """
    logger.info(f"Testing RSS news search for: {query}")
    
    # Calculate date range
    to_date = datetime.now().date()
    from_date = to_date - timedelta(days=days_back)
    
    # Initialize feed searcher
    searcher = NewsFeedSearch()
    
    try:
        # Search for news
        results = await searcher.search_news(
            query=query,
            from_date=from_date,
            to_date=to_date,
            max_results=max_results,
            topic=topic
        )
        
        await searcher.close()
        
        logger.info(f"Found {len(results)} news articles")
        
        # Print results
        for i, article in enumerate(results, 1):
            print(f"\nARTICLE {i}:")
            print(f"Title: {article.get('title')}")
            print(f"Source: {article.get('source')}")
            print(f"Date: {article.get('publish_date')}")
            print(f"Link: {article.get('link')}")
            print(f"Authors: {', '.join(article.get('authors', []))}")
            print("-" * 80)
        
        # Save results to file
        output_dir = Path(project_root) / "output" / "rss_test"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"{query.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
            
        logger.info(f"Saved results to {output_file}")
        
        return results
    
    except Exception as e:
        logger.error(f"Error in RSS test: {str(e)}")
        return []

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the RSS news search")
    parser.add_argument("-q", "--query", type=str, default="NVIDIA", help="Search query")
    parser.add_argument("-d", "--days", type=int, default=30, help="Days to look back")
    parser.add_argument("-m", "--max", type=int, default=10, help="Maximum number of results")
    parser.add_argument("-t", "--topic", type=str, help="Topic filter (business, technology, etc.)")
    
    args = parser.parse_args()
    
    asyncio.run(test_news_search(
        query=args.query,
        days_back=args.days,
        max_results=args.max,
        topic=args.topic
    ))
