#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Summarization module using a local LLM to summarize article content.
"""

import json
import asyncio
import aiohttp
from typing import Dict, Any, Optional

from src.utils.logger import get_logger
from src.models.data_schema import ArticleSummary

logger = get_logger(__name__)


class Summarizer:
    """
    Class to handle article summarization using a local LLM.
    """
    
    def __init__(self, host: str = "localhost", port: int = 8080, model: str = "deepseek-v1"):
        """
        Initialize the Summarizer.
        
        Args:
            host: LLM server hostname
            port: LLM server port
            model: Model name
        """
        self.host = host
        self.port = port
        self.model = model
        self.api_url = f"http://{host}:{port}/v1/completions"
        logger.debug(f"Summarizer initialized with LLM at {self.api_url}")
        self.llm_available = False
        self.check_llm_connection()
    
    def check_llm_connection(self):
        """Check if the LLM service is available."""
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            result = s.connect_ex((self.host, self.port))
            s.close()
            if result == 0:
                logger.info(f"LLM service is available at {self.host}:{self.port}")
                self.llm_available = True
            else:
                logger.warning(f"LLM service not available at {self.host}:{self.port}. Will use fallback summarization.")
                self.llm_available = False
        except Exception as e:
            logger.warning(f"Error checking LLM availability: {str(e)}")
            self.llm_available = False
    
    async def summarize(self, content: str, max_length: int = 200) -> ArticleSummary:
        """
        Summarize article content using the LLM.
        
        Args:
            content: Article content to summarize
            max_length: Maximum summary length
            
        Returns:
            ArticleSummary object
        """
        if not content:
            logger.warning("Empty content provided for summarization")
            return ArticleSummary(
                title="No content available",
                content="The article had no content to summarize.",
                sentiment=0.0,
                keywords=[]
            )
        
        # If LLM is not available, use the extractive fallback immediately
        if not self.llm_available:
            logger.info("Using fallback extractive summarization (LLM not available)")
            return self._create_extractive_summary(content)
        
        # Truncate content if too long to avoid token limits
        if len(content) > 8000:
            content = content[:8000] + "..."
        
        prompt = f"""Summarize the following news article in a concise paragraph of no more than {max_length} characters.
Also generate a short, catchy title, analyze the sentiment (on a scale from -1.0 to 1.0, where -1.0 is very negative, 0.0 is neutral, and 1.0 is very positive),
and extract 3-5 relevant keywords.
Format your response as a JSON object with the following keys: title, summary, sentiment, keywords.

ARTICLE:
{content}

JSON RESPONSE:"""
        
        try:
            # Call the LLM API
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "max_tokens": 500,
                    "temperature": 0.3,
                    "stop": None
                }
                
                try:
                    # Use a shorter timeout to avoid long waiting
                    async with session.post(self.api_url, json=payload, timeout=5) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            logger.error(f"LLM API error: Status {response.status}, {error_text}")
                            return self._create_extractive_summary(content)
                        
                        result = await response.json()
                        
                        if "choices" not in result or not result["choices"]:
                            logger.error("Invalid response from LLM API")
                            return self._create_extractive_summary(content)
                        
                        llm_response = result["choices"][0]["text"].strip()
                        
                        try:
                            # Find the start of the JSON in the response
                            json_start = llm_response.find("{")
                            if json_start == -1:
                                logger.warning("No JSON found in LLM response")
                                return self._create_extractive_summary(content)
                            
                            json_text = llm_response[json_start:]
                            summary_data = json.loads(json_text)
                            
                            return ArticleSummary(
                                title=summary_data.get("title", "Untitled"),
                                content=summary_data.get("summary", "No summary available"),
                                sentiment=float(summary_data.get("sentiment", 0.0)),
                                keywords=summary_data.get("keywords", [])
                            )
                            
                        except (json.JSONDecodeError, ValueError) as e:
                            logger.error(f"Error parsing LLM response: {str(e)}")
                            return self._create_extractive_summary(content, llm_response)
                except asyncio.TimeoutError:
                    logger.warning("LLM API timeout - using fallback summarization")
                    return self._create_extractive_summary(content)
                        
        except Exception as e:
            logger.error(f"Error during summarization: {str(e)}")
            return self._create_extractive_summary(content)
            
    def _create_extractive_summary(self, content: str, llm_response: Optional[str] = None) -> ArticleSummary:
        """
        Create an extractive summary when the LLM fails.
        
        Args:
            content: The original article content
            llm_response: The raw LLM response, if available
            
        Returns:
            A basic ArticleSummary using extractive summarization
        """
        logger.info("Creating extractive summary as fallback")
        
        # Split into sentences and paragraphs
        paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
        sentences = []
        for paragraph in paragraphs:
            sentences.extend([s.strip() + '.' for s in paragraph.split('.') if s.strip()])
        
        # Use first sentence as title
        title = sentences[0] if sentences else "Article"
        title = title[:50] + ("..." if len(title) > 50 else "")
        
        # Take first 2-3 sentences for the summary
        summary_sentences = sentences[:min(3, len(sentences))]
        summary = ' '.join(summary_sentences)
        
        # Truncate if too long
        if len(summary) > 200:
            summary = summary[:197] + "..."
        
        # Try to extract some keywords
        keywords = []
        try:
            # Very simple keyword extraction based on frequency
            import re
            from collections import Counter
            
            # Remove common stop words
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with', 
                         'by', 'about', 'as', 'into', 'like', 'through', 'after', 'over', 'between',
                         'out', 'of', 'during', 'without', 'before', 'under', 'around', 'among'}
            
            # Extract words, clean them, and filter out stop words
            words = re.findall(r'\b[a-zA-Z]{3,15}\b', content.lower())
            words = [word for word in words if word not in stop_words]
            
            # Get the most common words as keywords
            word_counts = Counter(words)
            keywords = [word for word, _ in word_counts.most_common(5)]
        except Exception as e:
            logger.error(f"Error extracting keywords: {str(e)}")
        
        if llm_response:
            logger.debug(f"Raw LLM response: {llm_response}")
            
        return ArticleSummary(
            title=title,
            content=summary,
            sentiment=0.0,  # Neutral sentiment as default
            keywords=keywords
        )
