#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Simple test for the RSS search functionality without authors field.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

# Add project root to path
import sys
project_root = str(Path(__file__).parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.search.news_feed_search import NewsFeedSearch
from loguru import logger

# Configure logger
logger.remove()
logger.add(sys.stderr, level="INFO")

async def test_search():
    """Test the RSS search without authors field."""
    query = "NVIDIA"
    
    # Create the searcher
    searcher = NewsFeedSearch()
    
    # Do the search
    results = await searcher.search_news(
        query=query,
        max_results=5,
        use_cache=True
    )
    
    # Close the session
    await searcher.close()
    
    # Output the results
    print(f"\n=== RSS SEARCH RESULTS FOR '{query}' ===\n")
    
    for i, article in enumerate(results, 1):
        print(f"ARTICLE {i}:")
        print(f"Title: {article.get('title', '')}")
        print(f"Source: {article.get('source', '')}")
        print(f"Date: {article.get('publish_date', '')}")
        print(f"Link: {article.get('link', '')}")
        print("-" * 80)
    
    # Save to file for verification
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(project_root) / "output"
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / f"rss_simple_{timestamp}.json"
    with open(output_file, "w") as f:
        json.dump({
            "query": query,
            "timestamp": timestamp,
            "results": [
                {
                    "title": article.get("title", ""),
                    "source": article.get("source", ""),
                    "publish_date": article.get("publish_date", ""),
                    "link": article.get("link", "")
                    # No authors field!
                }
                for article in results
            ]
        }, f, indent=2)
    
    print(f"Results saved to {output_file}")

if __name__ == "__main__":
    asyncio.run(test_search())
