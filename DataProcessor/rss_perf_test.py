#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Performance test for the RSS news search functionality.
This script demonstrates the performance improvements from the optimizations.
"""

import time
import asyncio
import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger

# Add project root to path
import sys
project_root = str(Path(__file__).parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.search.news_feed_search import NewsFeedSearch

# Configure logger
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add(
    "logs/rss_perf_test_{time}.log",
    rotation="100 MB", 
    level="DEBUG"
)

# Ensure output directory exists
output_dir = Path(project_root) / "output" / "rss_test"
output_dir.mkdir(parents=True, exist_ok=True)

async def run_test_scenario(
    query: str, 
    days_back: int, 
    max_results: int = 10,
    scenario_name: str = "default",
    use_cache: bool = True,
    resolve_urls: bool = True,
    topic: str = None
):
    """Run a test scenario and measure performance."""
    logger.info(f"Running scenario: {scenario_name}")
    
    # Calculate date range
    to_date = datetime.now().date()
    from_date = to_date - timedelta(days=days_back)
    
    # Create searcher
    news_searcher = NewsFeedSearch()
    
    # Measure time
    start_time = time.time()
    
    # Search for news
    results = await news_searcher.search_news(
        query=query,
        from_date=from_date,
        to_date=to_date,
        max_results=max_results,
        topic=topic,
        use_cache=use_cache,
        resolve_urls=resolve_urls
    )
    
    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    
    # Clean up
    await news_searcher.close()
    
    # Log results
    logger.info(f"Scenario {scenario_name}: Found {len(results)} articles in {elapsed_time:.2f} seconds")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"{query}_{scenario_name}_{timestamp}.json"
    
    with open(output_file, "w") as f:
        json.dump({
            "query": query,
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat(),
            "max_results": max_results,
            "scenario": scenario_name,
            "elapsed_time": elapsed_time,
            "results_count": len(results),
            "results": results
        }, f, indent=2)
    
    logger.info(f"Saved results to {output_file}")
    
    return elapsed_time, len(results)

async def test_article_content(url: str):
    """Test article content extraction performance."""
    logger.info(f"Testing article content extraction for: {url}")
    
    # Create searcher
    news_searcher = NewsFeedSearch()
    
    # Measure time
    start_time = time.time()
    
    # Get article content
    article = await news_searcher.get_article_content(url)
    
    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    
    # Clean up
    await news_searcher.close()
    
    # Log results
    logger.info(f"Article extraction took {elapsed_time:.2f} seconds")
    logger.info(f"Article title: {article.get('title', 'N/A')}")
    logger.info(f"Article length: {len(article.get('text', ''))}")
    
    return elapsed_time, article

async def main():
    """Main performance test function."""
    parser = argparse.ArgumentParser(description="Test RSS news search performance")
    parser.add_argument("-q", "--query", type=str, default="NVIDIA", help="Search query")
    parser.add_argument("-d", "--days", type=int, default=30, help="Days to look back")
    parser.add_argument("-m", "--max", type=int, default=10, help="Max results")
    parser.add_argument("-t", "--topic", type=str, help="News topic")
    parser.add_argument("-a", "--article", type=str, help="Test article content extraction for URL")
    args = parser.parse_args()
    
    if args.article:
        # Just test article extraction
        await test_article_content(args.article)
        return
    
    # Results storage
    results = {}
    
    # Test 1: First run with cache and URL resolution (slowest, but good links)
    elapsed1, count1 = await run_test_scenario(
        args.query, 
        args.days, 
        args.max,
        scenario_name="initial_run",
        use_cache=True,
        resolve_urls=True,
        topic=args.topic
    )
    results["initial_run"] = {"time": elapsed1, "count": count1}
    
    # Test 2: Second run with cache (should be very fast)
    elapsed2, count2 = await run_test_scenario(
        args.query, 
        args.days, 
        args.max,
        scenario_name="cached",
        use_cache=True,
        resolve_urls=True,
        topic=args.topic
    )
    results["cached"] = {"time": elapsed2, "count": count2}
    
    # Test 3: Run without URL resolution (faster but with Google redirect links)
    elapsed3, count3 = await run_test_scenario(
        args.query, 
        args.days, 
        args.max,
        scenario_name="no_url_resolution",
        use_cache=False,
        resolve_urls=False,
        topic=args.topic
    )
    results["no_url_resolution"] = {"time": elapsed3, "count": count3}
    
    # Print summary
    logger.info("\n--- PERFORMANCE SUMMARY ---")
    logger.info(f"Query: {args.query}, Days: {args.days}, Max Results: {args.max}")
    
    for scenario, data in results.items():
        logger.info(f"{scenario}: {data['time']:.2f} seconds for {data['count']} articles")
    
    if "cached" in results and "initial_run" in results:
        speedup = results["initial_run"]["time"] / results["cached"]["time"]
        logger.info(f"Cache speedup: {speedup:.1f}x faster")
    
    if "no_url_resolution" in results and "initial_run" in results:
        speedup = results["initial_run"]["time"] / results["no_url_resolution"]["time"]
        logger.info(f"No URL resolution speedup: {speedup:.1f}x faster")

if __name__ == "__main__":
    asyncio.run(main())
