#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script to verify RSS search properly handles date ranges for VIBE integration.
This tests different date range parameters to make sure we get appropriate results.
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
import argparse

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
logger.add(
    "logs/date_range_test_{time}.log",
    rotation="100 MB", 
    level="DEBUG"
)

# Ensure output directory exists
output_dir = Path(project_root) / "output" / "date_tests"
output_dir.mkdir(parents=True, exist_ok=True)

async def test_date_range(
    query: str, 
    from_date: str, 
    to_date: str, 
    max_results: int = 10
):
    """Test RSS search with specific date range."""
    logger.info(f"Testing date range: {query} from {from_date} to {to_date}")
    
    # Create the searcher
    searcher = NewsFeedSearch()
    
    # Start timing
    start_time = datetime.now()
    
    # Do the search
    results = await searcher.search_news(
        query=query,
        from_date=from_date,
        to_date=to_date,
        max_results=max_results,
        use_cache=False  # Don't use cache to make sure we're testing date filtering
    )
    
    # Close the session
    await searcher.close()
    
    # Calculate time taken
    elapsed = (datetime.now() - start_time).total_seconds()
    
    # Output the results
    logger.info(f"Found {len(results)} articles in {elapsed:.2f} seconds")
    
    # Check if we found any articles
    if not results:
        logger.warning(f"No articles found for {query} between {from_date} and {to_date}")
        return results
    
    # Check the dates of articles
    date_check_pass = True
    for article in results:
        pub_date_str = article.get("publish_date", "")
        try:
            # Parse the date (Google News format)
            pub_date = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %Z").date()
            
            # Convert string dates to date objects for comparison
            from_date_obj = datetime.strptime(from_date, "%Y-%m-%d").date() if from_date else None
            to_date_obj = datetime.strptime(to_date, "%Y-%m-%d").date() if to_date else None
            
            # Check if date is in range
            if from_date_obj and pub_date < from_date_obj:
                logger.error(f"Article date {pub_date} is before from_date {from_date_obj}")
                date_check_pass = False
            
            if to_date_obj and pub_date > to_date_obj:
                logger.error(f"Article date {pub_date} is after to_date {to_date_obj}")
                date_check_pass = False
                
        except ValueError:
            logger.warning(f"Could not parse date: {pub_date_str}")
    
    if date_check_pass:
        logger.info("✅ All articles are within the requested date range")
    else:
        logger.error("❌ Some articles are outside the requested date range")
    
    # Save to file for verification
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"{query}_{from_date}_to_{to_date}_{timestamp}.json"
    
    with open(output_file, "w") as f:
        json.dump({
            "query": query,
            "from_date": from_date,
            "to_date": to_date,
            "timestamp": timestamp,
            "results_count": len(results),
            "results": results
        }, f, indent=2)
    
    logger.info(f"Results saved to {output_file}")
    return results

async def main():
    """Run various date range tests for VIBE integration."""
    parser = argparse.ArgumentParser(description="Test RSS news search with date ranges")
    parser.add_argument("-q", "--query", type=str, default="NVIDIA", help="Search query")
    parser.add_argument("-t", "--tests", type=str, choices=["all", "recent", "month", "year", "custom"], default="all", help="Test type")
    parser.add_argument("--from", dest="from_date", type=str, help="Custom from date (YYYY-MM-DD)")
    parser.add_argument("--to", dest="to_date", type=str, help="Custom to date (YYYY-MM-DD)")
    args = parser.parse_args()
    
    today = datetime.now().date()
    
    # Determine which tests to run
    if args.tests == "custom" and (args.from_date or args.to_date):
        # Single custom test
        await test_date_range(
            args.query,
            args.from_date,
            args.to_date
        )
        return
    
    tests = []
    
    if args.tests in ["all", "recent"]:
        # Last 7 days
        seven_days_ago = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        today_str = today.strftime("%Y-%m-%d")
        tests.append(("Last 7 days", seven_days_ago, today_str))
    
    if args.tests in ["all", "month"]:
        # Last 30 days
        thirty_days_ago = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        tests.append(("Last 30 days", thirty_days_ago, today.strftime("%Y-%m-%d")))
    
    if args.tests in ["all", "year"]:
        # Last year
        one_year_ago = (today - timedelta(days=365)).strftime("%Y-%m-%d")
        tests.append(("Last year", one_year_ago, today.strftime("%Y-%m-%d")))
    
    if args.tests == "all":
        # Edge cases
        
        # Future dates (should return no results)
        tomorrow = (today + timedelta(days=1)).strftime("%Y-%m-%d")
        next_week = (today + timedelta(days=7)).strftime("%Y-%m-%d")
        tests.append(("Future dates", tomorrow, next_week))
        
        # Very old dates (likely no results)
        old_date = "2010-01-01"
        less_old_date = "2010-12-31"
        tests.append(("Very old dates", old_date, less_old_date))
        
        # Missing dates - should use defaults
        tests.append(("Missing from_date", None, today.strftime("%Y-%m-%d")))
        tests.append(("Missing to_date", thirty_days_ago, None))
        tests.append(("Missing both dates", None, None))
        
        # Invalid date formats - should handle gracefully
        tests.append(("Invalid from_date", "not-a-date", today.strftime("%Y-%m-%d")))
        tests.append(("Invalid to_date", thirty_days_ago, "not-a-date"))
    
    # Run all the tests
    for name, from_date, to_date in tests:
        logger.info(f"\n--- TESTING: {name} ---")
        await test_date_range(args.query, from_date, to_date)

if __name__ == "__main__":
    asyncio.run(main())
