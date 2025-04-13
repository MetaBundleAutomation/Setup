# DataProcessor

Real-time news scraping, summarization, and timeline event processing engine for financial data analysis.

## Overview

DataProcessor fetches top search results via Google APIs, scrapes content from linked articles, summarizes them using a local LLM (e.g., DeepSeek V1), and returns structured metadata for stock timeline applications. Designed to run locally or server-side in Docker containers.

## Quick Start

1. Clone the repository:
   ```
   git clone https://github.com/MetaBundleAutomation/Data-Processor.git
   cd DataProcessor
   ```

2. Set up environment variables:
   
   Option A: Using PowerShell to set system-wide environment variables:
   ```powershell
   # Set environment variables at the user level
   [System.Environment]::SetEnvironmentVariable("GOOGLE_SEARCH_API_KEY", "your_api_key_here", "User")
   [System.Environment]::SetEnvironmentVariable("GOOGLE_SEARCH_ENGINE_ID", "15cb95703c7e2469c", "User")
   ```
   
   Option B: Using a local .env file:
   ```
   cp .env.example .env
   # Edit .env with your API keys or let it use the system environment variables
   ```

3. Run with Docker:
   ```
   docker-compose up -d
   ```

   Or locally:
   ```
   pip install -r requirements.txt
   python src/main.py
   ```

## Environment Variables

The application uses the following environment variables that can be set either through system environment variables or in the `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| GOOGLE_SEARCH_API_KEY | Your Google API key for search | Required |
| GOOGLE_SEARCH_ENGINE_ID | Your Google Custom Search Engine ID | Required |
| LLM_HOST | Host for the LLM service | localhost |
| LLM_PORT | Port for the LLM service | 8080 |
| LLM_MODEL | Model name to use for summarization | deepseek-v1 |
| LOG_LEVEL | Logging level | INFO |
| MAX_CONCURRENT_SCRAPES | Maximum number of concurrent scrapes | 10 |
| MAX_SEARCH_RESULTS | Maximum number of search results to process | 20 |
| SUMMARY_MAX_LENGTH | Maximum length of article summaries | 200 |

## Features

- Real-time news scraping via Google Custom Search API
- Asynchronous web scraping with retry logic and anti-detection measures
- Article content extraction and cleaning
- Article summarization with local LLM option
- FastAPI endpoint for custom search requests with date ranges
- Structured JSON output for easy integration

## Setup

### Environment Variables

Create a `.env` file in the project root directory by copying the provided `.env.example`:

```bash
cp .env.example .env
```

Then edit the `.env` file to set the required environment variables:

```
GOOGLE_SEARCH_API_KEY=your_google_api_key
GOOGLE_SEARCH_ENGINE_ID=your_google_search_engine_id
MAX_CONCURRENT_SCRAPES=10
MAX_SEARCH_RESULTS=20
LOG_LEVEL=INFO
```

Alternatively, you can set these environment variables directly in your PowerShell session:

```powershell
$env:GOOGLE_SEARCH_API_KEY="your_google_api_key"
$env:GOOGLE_SEARCH_ENGINE_ID="your_google_search_engine_id"
$env:MAX_CONCURRENT_SCRAPES="10"
$env:MAX_SEARCH_RESULTS="20"
$env:LOG_LEVEL="INFO"
```

### Google Search API Setup

1. Create a project in the [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the Custom Search API
3. Create API credentials (API Key)
4. Create a Custom Search Engine in the [Google Programmable Search Engine](https://programmablesearchengine.google.com/about/)
5. Add the API key and Search Engine ID to your environment variables

### Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Command Line Interface

Run the data processor from the command line:

```bash
python src/main.py
```

This will:
1. Search for news articles related to the specified stock tickers
2. Scrape and extract content from the found articles
3. Save the article data to JSON files in the `output` directory

### API Server

Start the FastAPI server:

```bash
python run_api.py
```

By default, the server runs on `http://localhost:8000`. You can access the API documentation at `http://localhost:8000/docs`.

#### API Endpoints

**Search Endpoint**

```
POST /search
```

Request body:
```json
{
  "search_term": "climate change",
  "from_date": "2025-03-01",
  "to_date": "2025-04-01",
  "max_results": 10
}
```

This will:
1. Search for articles matching the search term in the specified date range
2. Scrape and extract content from the found articles
3. Return structured article data in the response
4. Save the article data to JSON files in the `output/searches` directory

## Architecture

```plaintext
DataProcessor/
├── .env                        # API keys, config vars
├── docker-compose.yml         # Local LLM containers, scraper workers
├── requirements.txt           # Python packages
├── README.md                  # Setup + architecture docs
├── /src
│   ├── main.py                # Entrypoint to coordinate workflow
│   ├── config.py              # Loads env and app config
│   ├── search/
│   │   └── google_search.py   # Fetches top N URLs for a stock ticker
│   ├── scrape/
│   │   ├── async_scraper.py   # Asynchronous web scraping logic
│   │   └── article_cleaner.py # Strips boilerplate, ads, etc.
│   ├── summarize/
│   │   └── summarizer.py      # LLM wrapper to summarize content
│   ├── utils/
│   │   └── logger.py          # Custom logger
│   └── models/
│       └── data_schema.py     # Pydantic data models
└── /tests                     # Unit tests for each module
```

## Workflow

1. **Google Search** – Grab top links based on date & ticker keyword
2. **Scraping** – Asynchronously scrape article content 
3. **Cleaning** – Remove page noise, ads, HTML artifacts
4. **Summarization** – Use local LLM to produce headline + summary
5. **Structuring** – Convert results into structured objects

## Tech Stack

- Python 3.11+
- FastAPI (optional endpoints)
- Docker (LLM containers, scraper isolation)
- Asyncio + aiohttp
- Pydantic
- Local LLMs like DeepSeek V1
- Google Custom Search API

## Use Cases

- Stock chart timeline annotation
- Investor sentiment analysis
- Breaking news alerts on price events
- Offline research tool for analysts

## Docker

Build and run with Docker:

```bash
docker build -t dataprocessor .
docker run -p 8000:8000 -e GOOGLE_SEARCH_API_KEY=your_key -e GOOGLE_SEARCH_ENGINE_ID=your_id dataprocessor
```

## Output Format

The article data is saved in JSON format with the following structure:

```json
[
  {
    "url": "https://example.com/article1",
    "title": "Example Article Title",
    "source": "example.com",
    "publish_date": "2025-04-01T00:00:00",
    "authors": ["Author Name"],
    "content_snippet": "First 200 characters of the article content...",
    "keywords": ["keyword1", "keyword2"],
    "images": ["https://example.com/image1.jpg"],
    "ticker": "AAPL",
    "extracted_at": "2025-04-13T14:25:40.123456"
  },
  ...
]
```
