#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
FastAPI application for the DataProcessor.
"""

import sys
import os
import time
import asyncio
from pathlib import Path
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any
import random

# Add project root to path for imports to work correctly
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from src.config import settings
from src.models.api_schema import SearchRequest, SearchResponse, ArticleResponse
from src.search.google_search import GoogleSearch
from src.scrape.async_scraper import AsyncScraper
from src.utils.logger import get_logger
from src.search.news_feed_search import NewsFeedSearch

logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="DataProcessor API",
    description="API for searching and processing news articles",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Output directory for storing articles
OUTPUT_DIR = Path(project_root) / "output"

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def get_index():
    """Serve the frontend application."""
    return FileResponse("static/index.html")

@app.get("/api/")
async def root():
    """Root endpoint to check if API is running."""
    return {"status": "OK", "message": "DataProcessor API is running"}


@app.post("/api/search", response_model=SearchResponse)
async def search_articles(request: SearchRequest):
    """
    Search for articles based on the provided search term and date range.
    
    Args:
        request: SearchRequest object with search parameters
        
    Returns:
        SearchResponse object with matching articles
    """
    logger.info(f"Received search request: {request.search_term} from {request.from_date} to {request.to_date}")
    
    start_time = time.time()
    
    try:
        # Initialize Google search
        google_search = GoogleSearch(
            api_key=settings.GOOGLE_SEARCH_API_KEY,
            engine_id=settings.GOOGLE_SEARCH_ENGINE_ID
        )
        
        # Convert dates to string format for file naming
        from_date_str = request.from_date.strftime("%Y-%m-%d")
        to_date_str = request.to_date.strftime("%Y-%m-%d")
        
        # Search for articles - note we're passing the actual date objects
        # and explicitly setting news_only=True
        search_results = await google_search.search_with_date_range(
            query=request.search_term,
            from_date=request.from_date,
            to_date=request.to_date,
            max_results=request.max_results,
            news_only=True  # Ensure we only get news articles
        )
        
        logger.info(f"Found {len(search_results)} search results for '{request.search_term}'")
        
        if not search_results:
            # Return empty response if no results found
            return SearchResponse(
                search_term=request.search_term,
                from_date=request.from_date,
                to_date=request.to_date,
                total_results=0,
                articles=[],
                processing_time=time.time() - start_time
            )
        
        # Extract URLs
        urls = [result["link"] for result in search_results if "link" in result]
        
        if not urls:
            logger.warning("No valid URLs found in search results")
            return SearchResponse(
                search_term=request.search_term,
                from_date=request.from_date,
                to_date=request.to_date,
                total_results=0,
                articles=[],
                processing_time=time.time() - start_time
            )
        
        # Scrape article content
        async_scraper = AsyncScraper(
            max_concurrent=settings.MAX_CONCURRENT_SCRAPES,
            timeout=30
        )
        articles = await async_scraper.scrape_urls(urls)
        
        logger.info(f"Successfully scraped {len(articles)} articles")
        
        # Process articles into response format
        article_responses = []
        processed_articles = []
        
        for article in articles:
            if not article or not article.content:
                continue
                
            # Skip articles without a publish date if we can extract it
            publish_date = article.publish_date
            # If article doesn't have date, try to find it in search results metadata
            if not publish_date:
                for result in search_results:
                    if result.get("link") == article.url and result.get("published_time"):
                        try:
                            # Parse the date from the search result
                            date_str = result.get("published_time")
                            # Handle various date formats
                            if date_str:
                                # Try ISO format first (YYYY-MM-DDTHH:MM:SS) 
                                try:
                                    publish_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                                except ValueError:
                                    # Try other common formats
                                    try:
                                        from dateutil import parser
                                        publish_date = parser.parse(date_str)
                                    except Exception:
                                        # If all parsing fails, leave as None
                                        pass
                        except Exception as e:
                            logger.debug(f"Error parsing date for {article.url}: {str(e)}")
            
            # Skip articles without a publish date
            if not publish_date and not article.authors:
                logger.debug(f"Skipping article without publish date or authors: {article.url}")
                continue
            
            # Full article data for storage
            article_data = {
                "url": article.url,
                "title": article.title or "Untitled",
                "source": article.source,
                "publish_date": str(publish_date) if publish_date else None,
                "authors": article.authors,
                "content_snippet": article.content[:200] + "..." if article.content and len(article.content) > 200 else article.content,
                "keywords": list(article.keywords) if article.keywords else [],
                "images": list(article.images)[:3] if article.images else [],
                "extracted_at": datetime.now().isoformat(),
            }
            processed_articles.append(article_data)
            
            # Simplified article data for response
            response_data = {
                "url": article.url,
                "title": article.title or "Untitled",
                "source": article.source,
                "publish_date": str(publish_date) if publish_date else None,
                "authors": article.authors
            }
            article_responses.append(ArticleResponse(**response_data))
        
        # Save results to file in background
        search_id = f"{request.search_term.replace(' ', '_')}_{from_date_str}_to_{to_date_str}"
        save_results_to_file(search_id, processed_articles)
        
        # Create response
        response = SearchResponse(
            search_term=request.search_term,
            from_date=request.from_date,
            to_date=request.to_date,
            total_results=len(article_responses),
            articles=article_responses,
            processing_time=time.time() - start_time
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing search request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing search request: {str(e)}")


@app.get("/api/rss-search", response_model=List[ArticleResponse])
async def rss_search(
    query: str,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    topic: Optional[str] = None,
    resolve_urls: bool = True,
    use_cache: bool = True
):
    """
    Search for news articles using RSS feeds.
    Designed for integration with VIBE frontend date range selectors.
    
    Args:
        query: Search query
        from_date: Start date in format YYYY-MM-DD (default: 7 days ago)
        to_date: End date in format YYYY-MM-DD (default: today)
        topic: Specific news topic to search within
        resolve_urls: Whether to resolve redirect URLs (slightly slower but better links)
        use_cache: Whether to use cached results for faster response
        
    Returns:
        List of articles matching the query
    """
    try:
        # Log the request
        logger.info(f"RSS search request - Query: {query}, From: {from_date}, To: {to_date}, Topic: {topic}, Resolve: {resolve_urls}, Cache: {use_cache}")
        
        # Create the news feed searcher
        news_searcher = NewsFeedSearch()
        
        # Search for articles - always return 20 results by default
        search_results = await news_searcher.search_news(
            query=query,
            from_date=from_date,
            to_date=to_date,
            max_results=20,  # Fixed to always return 20 results
            topic=topic,
            resolve_urls=resolve_urls,
            use_cache=use_cache
        )
        
        # Close the session
        await news_searcher.close()
        
        # Convert to response model
        articles = []
        for article in search_results:
            # Create the response with required fields
            response = ArticleResponse(
                title=article.get("title", ""),
                link=article.get("link", ""),
                source=article.get("source", ""),
                publish_date=article.get("publish_date", "")
            )
            articles.append(response)
        
        # Save results for debugging if needed
        if search_results:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_results_to_file(f"rss_{query}_{timestamp}", search_results)
        
        return articles
    except Exception as e:
        logger.error(f"Error in RSS search endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching for articles: {str(e)}")


@app.get("/api/article-content")
async def get_article_content(url: str):
    """
    Get the full content of a specific article.
    This is an expensive operation so it should only be called when needed.
    
    Args:
        url: URL of the article to retrieve
        
    Returns:
        The article content and metadata
    """
    try:
        # Log the request
        logger.info(f"Article content request - URL: {url}")
        
        # Create the news feed searcher
        news_searcher = NewsFeedSearch()
        
        # Get the article content
        article = await news_searcher.get_article_content(url)
        
        # Close the session
        await news_searcher.close()
        
        return article
    except Exception as e:
        logger.error(f"Error getting article content: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving article: {str(e)}")


@app.get("/api/news", response_model=List[ArticleResponse])
async def news_search(
    symbol: str = "GENERAL",
    days: int = 30,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
):
    """
    Get news articles for the Bloomberg Terminal.
    
    Args:
        symbol: Stock symbol or topic to search for
        days: Number of days to look back if no date range is provided
        from_date: Start date (optional) in YYYY-MM-DD format
        to_date: End date (optional) in YYYY-MM-DD format
        
    Returns:
        List of news articles formatted for the Bloomberg Terminal
    """
    try:
        # Log the request
        logger.info(f"News search request - Symbol: {symbol}, Days: {days}")
        
        # Convert symbol to a search query
        query = symbol if symbol != "GENERAL" else ""
        if not query:
            # For general news, use a default business news query
            query = "business news"
        
        # Create the news feed searcher
        news_searcher = NewsFeedSearch()
        
        # Search for news articles
        search_results = await news_searcher.search_news(
            query=query,
            from_date=from_date,
            to_date=to_date,
            max_results=20,
            resolve_urls=True,
            use_cache=True
        )
        
        # Close the session
        await news_searcher.close()
        
        # Format for Bloomberg Terminal frontend
        articles = []
        for i, article in enumerate(search_results):
            # Format date for the frontend
            pub_date = article.get("publish_date", "")
            formatted_date = ""
            display_date = ""
            
            try:
                # Try to parse and format the date for storage
                date_obj = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z")
                formatted_date = date_obj.strftime("%Y-%m-%d")
                
                # Create a more human-readable date for display
                display_date = date_obj.strftime("%b %d, %Y")
            except Exception as e:
                # If parsing fails, use a fallback format
                logger.warning(f"Failed to parse date: {pub_date} - {str(e)}")
                formatted_date = datetime.now().strftime("%Y-%m-%d")
                display_date = "Recently"
                
            # Generate a sentiment score (mock)
            sentiment = random.uniform(-0.5, 0.5)
            
            # Create a response that matches the format expected by the frontend
            response = ArticleResponse(
                title=article.get("title", ""),
                link=article.get("link", ""),
                source=article.get("source", ""),
                publish_date=formatted_date
            )
            
            # Add required properties for the frontend that aren't in our schema
            response_dict = response.dict()
            response_dict["id"] = f"news-{i}"
            response_dict["date"] = formatted_date  # ISO format for filtering
            response_dict["display_date"] = display_date  # Formatted for display
            response_dict["sentiment"] = sentiment
            response_dict["summary"] = article.get("snippet", "Click to read the full article.")
            response_dict["raw_data"] = article  # Include the raw article data
            
            articles.append(response_dict)
        
        # Debug logging
        logger.info(f"Returning {len(articles)} articles")
        
        # Save results for debugging
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_results_to_file(f"news_{symbol}_{timestamp}", articles)
        
        return articles
    except Exception as e:
        logger.error(f"Error in news endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving news: {str(e)}")


@app.get("/api/news/date-range")
async def news_search_by_date_range(
    symbol: str = "GENERAL",
    start_date: str = None,
    end_date: str = None
):
    """
    Get news articles for a specific date range.
    This endpoint is specifically for the Bloomberg Terminal timeline's
    date range selection feature.
    
    Args:
        symbol: Stock symbol or topic to search for
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Returns:
        List of news articles within the date range
    """
    try:
        if not start_date or not end_date:
            raise HTTPException(
                status_code=400, 
                detail="Both start_date and end_date are required"
            )
            
        # Log the request
        logger.info(f"Date range news request - Symbol: {symbol}, Range: {start_date} to {end_date}")
        
        # Convert symbol to a search query
        query = symbol if symbol != "GENERAL" else ""
        if not query:
            # For general news, use a default business news query
            query = "business news"
        
        # Add time components to dates to ensure we get the full day range
        # Start date gets 00:01 time
        # End date gets 23:59 time
        start_date_with_time = f"{start_date}T00:01:00"
        end_date_with_time = f"{end_date}T23:59:59"
        
        logger.info(f"Using time range: {start_date_with_time} to {end_date_with_time}")
        
        # Create the news feed searcher
        news_searcher = NewsFeedSearch()
        
        # Search for articles within the date range
        search_results = await news_searcher.search_news(
            query=query,
            from_date=start_date_with_time,
            to_date=end_date_with_time,
            max_results=20,
            resolve_urls=True,
            use_cache=True
        )
        
        # Close the session
        await news_searcher.close()
        
        # Format for Bloomberg Terminal frontend
        articles = []
        for i, article in enumerate(search_results):
            # Format date for the frontend
            pub_date = article.get("publish_date", "")
            formatted_date = ""
            display_date = ""
            
            try:
                # Try to parse and format the date for storage
                date_obj = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z")
                formatted_date = date_obj.strftime("%Y-%m-%d")
                
                # Create a more human-readable date for display
                display_date = date_obj.strftime("%b %d, %Y")
            except Exception as e:
                # If parsing fails, use a fallback format
                logger.warning(f"Failed to parse date: {pub_date} - {str(e)}")
                formatted_date = datetime.now().strftime("%Y-%m-%d")
                display_date = "Recently"
                
            # Generate a sentiment score (mock)
            sentiment = random.uniform(-0.5, 0.5)
            
            # Create a response that matches the format expected by the frontend
            response = ArticleResponse(
                title=article.get("title", ""),
                link=article.get("link", ""),
                source=article.get("source", ""),
                publish_date=formatted_date
            )
            
            # Add required properties for the frontend that aren't in our schema
            response_dict = response.dict()
            response_dict["id"] = f"news-{i}"
            response_dict["date"] = formatted_date  # ISO format for filtering
            response_dict["display_date"] = display_date  # Formatted for display
            response_dict["sentiment"] = sentiment
            response_dict["summary"] = article.get("snippet", "Click to read the full article.")
            response_dict["raw_data"] = article  # Include the raw article data
            
            articles.append(response_dict)
        
        # Debug logging
        logger.info(f"Returning {len(articles)} articles for date range: {start_date} to {end_date}")
        
        # Save results for debugging
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_results_to_file(f"news_range_{symbol}_{timestamp}", articles)
        
        return articles
    except Exception as e:
        logger.error(f"Error in date range endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving news: {str(e)}")


@app.get("/api/news/date")
async def news_search_by_date(
    symbol: str = "GENERAL",
    date: str = None
):
    """
    Get news articles for a specific date.
    This endpoint is specifically for the Bloomberg Terminal timeline's
    date point selection feature.
    
    Args:
        symbol: Stock symbol or topic to search for
        date: Date in YYYY-MM-DD format
        
    Returns:
        List of news articles for the specified date
    """
    try:
        if not date:
            raise HTTPException(
                status_code=400, 
                detail="Date parameter is required"
            )
            
        # Log the request
        logger.info(f"Single date news request - Symbol: {symbol}, Date: {date}")
        
        # For a single date search, we'll search for the entire day
        # by adding time components to the start and end of the day
        start_date_with_time = f"{date}T00:01:00"
        end_date_with_time = f"{date}T23:59:59"
        
        logger.info(f"Using time range: {start_date_with_time} to {end_date_with_time}")
        
        # Convert symbol to a search query
        query = symbol if symbol != "GENERAL" else ""
        if not query:
            # For general news, use a default business news query
            query = "business news"
        
        # Create the news feed searcher
        news_searcher = NewsFeedSearch()
        
        # Search for articles for the specific date
        search_results = await news_searcher.search_news(
            query=query,
            from_date=start_date_with_time,
            to_date=end_date_with_time,
            max_results=20,
            resolve_urls=True,
            use_cache=True
        )
        
        # Close the session
        await news_searcher.close()
        
        # Format for Bloomberg Terminal frontend
        articles = []
        for i, article in enumerate(search_results):
            # Format date for the frontend
            pub_date = article.get("publish_date", "")
            formatted_date = ""
            display_date = ""
            
            try:
                # Try to parse and format the date for storage
                date_obj = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z")
                formatted_date = date_obj.strftime("%Y-%m-%d")
                
                # Create a more human-readable date for display
                display_date = date_obj.strftime("%b %d, %Y")
            except Exception as e:
                # If parsing fails, use a fallback format
                logger.warning(f"Failed to parse date: {pub_date} - {str(e)}")
                formatted_date = date  # Use the requested date
                display_date = "Today"  # Generic display
                
            # Generate a sentiment score (mock)
            sentiment = random.uniform(-0.5, 0.5)
            
            # Create a response that matches the format expected by the frontend
            response = ArticleResponse(
                title=article.get("title", ""),
                link=article.get("link", ""),
                source=article.get("source", ""),
                publish_date=formatted_date
            )
            
            # Add required properties for the frontend that aren't in our schema
            response_dict = response.dict()
            response_dict["id"] = f"news-{i}"
            response_dict["date"] = formatted_date  # ISO format for filtering
            response_dict["display_date"] = display_date  # Formatted for display
            response_dict["sentiment"] = sentiment
            response_dict["summary"] = article.get("snippet", "Click to read the full article.")
            response_dict["raw_data"] = article  # Include the raw article data
            
            articles.append(response_dict)
        
        # Debug logging
        logger.info(f"Returning {len(articles)} articles for date: {date}")
        
        # Save results for debugging
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_results_to_file(f"news_date_{symbol}_{timestamp}", articles)
        
        return articles
    except Exception as e:
        logger.error(f"Error in date endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving news: {str(e)}")


@app.get("/api/timeline")
async def get_timeline_data(
    symbol: str = "GENERAL",
    days: int = 30
):
    """
    Get timeline data for the Bloomberg Terminal frontend.
    This endpoint provides stock price, volume, sentiment, and news count data
    for the timeline visualization.
    
    Args:
        symbol: Stock symbol to get data for
        days: Number of days to look back
        
    Returns:
        List of daily data points with price, volume, sentiment, and news count
    """
    try:
        logger.info(f"Timeline data request - Symbol: {symbol}, Days: {days}")
        
        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Create mock timeline data or fetch from a real source
        timeline_data = []
        
        # Generate random but sensible mock data for demonstration
        current_date = start_date
        base_price = 100.0  # Starting price
        
        # Create the news feed searcher for counting news articles
        news_searcher = NewsFeedSearch()
        
        # Get a batch of news articles for the entire period to count by date
        query = symbol if symbol != "GENERAL" else ""
        if not query:
            # For general news, use a default business news query
            query = "business news"
        
        news_data = await news_searcher.search_news(
            query=query,
            from_date=start_date.strftime("%Y-%m-%d"),
            to_date=end_date.strftime("%Y-%m-%d"),
            max_results=100,  # Get more articles to count across dates
            use_cache=True
        )
        
        # Close the session
        await news_searcher.close()
        
        # Group news articles by date
        news_by_date = {}
        for article in news_data:
            pub_date = article.get("publish_date", "")
            try:
                # Parse the date
                date_obj = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z").date()
                date_str = date_obj.strftime("%Y-%m-%d")
                
                if date_str in news_by_date:
                    news_by_date[date_str] += 1
                else:
                    news_by_date[date_str] = 1
            except:
                # Skip articles with unparseable dates
                continue
        
        # Generate daily data points
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            
            # Calculate a realistic price movement (random walk with some trend)
            price_change = random.uniform(-2.0, 2.0)
            if current_date.weekday() < 5:  # Weekdays tend to be more positive
                price_change += 0.2
            
            base_price = max(10, base_price + price_change)  # Ensure price doesn't go too low
            
            # Generate volume - higher on days with news
            has_news = date_str in news_by_date
            base_volume = random.randint(500000, 1500000)
            volume = base_volume * (1.5 if has_news else 1.0)
            
            # Generate sentiment - slightly correlated with price change
            sentiment = min(1.0, max(-1.0, price_change / 4 + random.uniform(-0.2, 0.2)))
            
            # Get news count for this date
            news_count = news_by_date.get(date_str, 0)
            
            # Add data point
            timeline_data.append({
                "date": date_str,
                "price": round(base_price, 2),
                "volume": int(volume),
                "sentiment": round(sentiment, 2),
                "newsCount": news_count
            })
            
            # Move to next day
            current_date += timedelta(days=1)
        
        # Save results for debugging
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_results_to_file(f"timeline_{symbol}_{timestamp}", timeline_data)
        
        return timeline_data
        
    except Exception as e:
        logger.error(f"Error generating timeline data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def save_results_to_file(search_id: str, articles: List[Dict[str, Any]]):
    """
    Save search results to a JSON file.
    
    Args:
        search_id: Unique identifier for the search
        articles: List of processed articles
    """
    try:
        # Create output directory if it doesn't exist
        output_dir = OUTPUT_DIR / "searches"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save the processed articles to a JSON file
        import json
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"{search_id}_{timestamp}.json"
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(articles, f, indent=2)
        
        logger.info(f"Saved search results to {output_file}")
    except Exception as e:
        logger.error(f"Error saving search results: {str(e)}")


if __name__ == "__main__":
    # Make sure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Start the API server
    port = int(os.environ.get("API_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
