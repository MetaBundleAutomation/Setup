#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Article cleaner to remove boilerplate content from articles.
"""

import re
from typing import List, Set

from src.models.data_schema import RawArticle, CleanedArticle
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ArticleCleaner:
    """
    Class to clean and prepare article content for summarization.
    """
    
    def __init__(self):
        """Initialize the ArticleCleaner."""
        # Common patterns to remove from text
        self.noise_patterns = [
            r'Share on \w+',
            r'Copyright ©.*?reserved',
            r'\d+ (min|minute|hour)s? read',
            r'Follow us on \w+',
            r'Click to share',
            r'Terms of (Use|Service)',
            r'Privacy Policy',
            r'Cookie Policy',
            r'All Rights Reserved',
            r'Advertisement',
        ]
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.noise_patterns]
        
        logger.debug("ArticleCleaner initialized")
    
    def clean(self, article: RawArticle) -> CleanedArticle:
        """
        Clean an article by removing boilerplate and formatting content.
        
        Args:
            article: RawArticle object to clean
            
        Returns:
            CleanedArticle object with processed content
        """
        if not article.content:
            logger.warning(f"Empty content for article: {article.url}")
            return CleanedArticle.from_raw_article(article, "")
        
        # Start with the parsed content
        content = article.content
        
        # Remove noise patterns
        for pattern in self.compiled_patterns:
            content = pattern.sub('', content)
        
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content).strip()
        
        # Remove very short paragraphs that are likely navigation or headers
        paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
        paragraphs = [p for p in paragraphs if len(p) > 40 or p.endswith('.')]
        
        cleaned_content = '\n\n'.join(paragraphs)
        
        logger.debug(f"Cleaned article from {len(article.content)} to {len(cleaned_content)} chars")
        
        return CleanedArticle.from_raw_article(article, cleaned_content)
