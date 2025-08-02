"""
Custom Crawl4AI agent for the Scholarly Clone platform.
This agent extends Crawl4AI with specific configurations for research-focused scraping.
"""

import asyncio
import time
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, urljoin
import sys
import os

# Add crawl4ai to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'crawl4ai'))

try:
    from crawl4ai import AsyncWebCrawler
    from crawl4ai.extraction_strategy import LLMExtractionStrategy, CosineStrategy
    from crawl4ai.chunking_strategy import RegexChunking
except ImportError:
    # Fallback implementation if crawl4ai import fails
    class AsyncWebCrawler:
        def __init__(self, **kwargs):
            pass
        async def arun(self, **kwargs):
            return None
    
    class LLMExtractionStrategy:
        def __init__(self, **kwargs):
            pass
    
    class CosineStrategy:
        def __init__(self, **kwargs):
            pass

from loguru import logger
from ..core.config import settings, ScrapingTargets
from ..models.schemas import SourceType


class ScholaryCrawl4AIAgent:
    """
    Enhanced Crawl4AI agent optimized for research and academic content scraping.
    """
    
    def __init__(self):
        self.crawler = None
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize the crawler with optimal settings."""
        if self.is_initialized:
            return
            
        try:
            self.crawler = AsyncWebCrawler(
                headless=settings.playwright_headless,
                verbose=settings.crawl4ai_verbose,
                # Browser configuration optimized for academic content
                browser_type="chromium",
                user_agent=settings.user_agent,
                # Performance optimizations
                max_concurrent_pages=settings.max_concurrent_requests,
                delay_between_requests=settings.request_delay,
                # Memory management
                page_timeout=settings.playwright_timeout,
                # Network optimization for academic sites
                ignore_https_errors=True,
                block_resources=["image", "media", "font"],  # Block non-essential resources
            )
            
            if settings.crawl4ai_warmup:
                await self.crawler.warmup()
                
            self.is_initialized = True
            logger.info("Crawl4AI agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Crawl4AI agent: {e}")
            raise
    
    async def scrape_url(self, 
                        url: str, 
                        extraction_strategy: str = "general",
                        custom_js: Optional[str] = None) -> Dict[str, Any]:
        """
        Scrape a single URL with domain-specific optimizations.
        
        Args:
            url: The URL to scrape
            extraction_strategy: Strategy for content extraction
            custom_js: Custom JavaScript to execute on the page
            
        Returns:
            Dictionary containing scraped content and metadata
        """
        if not self.is_initialized:
            await self.initialize()
            
        start_time = time.time()
        domain = urlparse(url).netloc
        site_config = ScrapingTargets.get_site_config(domain)
        
        try:
            # Merge custom config with site-specific config
            js_code = custom_js or site_config.get("js_code")
            wait_for = site_config.get("wait_for", "networkidle")
            timeout = site_config.get("timeout", settings.playwright_timeout)
            
            # Configure extraction strategy based on content type
            extraction_strategy_obj = self._get_extraction_strategy(
                extraction_strategy, 
                site_config.get("extraction_strategy", "general")
            )
            
            logger.info(f"Scraping URL: {url} with strategy: {extraction_strategy}")
            
            result = await self.crawler.arun(
                url=url,
                wait_for=wait_for,
                timeout=timeout,
                js_code=js_code,
                extraction_strategy=extraction_strategy_obj,
                chunking_strategy=RegexChunking(),
                # Academic content specific settings
                remove_overlay_elements=True,
                simulate_user=True,
                override_navigator=True,
                # Content filtering
                excluded_tags=['nav', 'footer', 'aside', 'advertisement'],
                only_text=False,  # Keep some structure for better parsing
            )
            
            processing_time = time.time() - start_time
            
            if result and result.success:
                return self._process_crawl_result(result, url, processing_time)
            else:
                error_msg = getattr(result, 'error_message', 'Unknown error') if result else 'No result returned'
                logger.error(f"Failed to scrape {url}: {error_msg}")
                return self._create_error_result(url, error_msg, processing_time)
                
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Exception while scraping {url}: {e}")
            return self._create_error_result(url, str(e), processing_time)
    
    async def scrape_multiple_urls(self, 
                                  urls: List[str], 
                                  max_concurrent: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Scrape multiple URLs concurrently with rate limiting.
        
        Args:
            urls: List of URLs to scrape
            max_concurrent: Maximum concurrent requests (defaults to settings)
            
        Returns:
            List of scraping results
        """
        if not self.is_initialized:
            await self.initialize()
            
        max_concurrent = max_concurrent or settings.max_concurrent_requests
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def scrape_with_semaphore(url: str) -> Dict[str, Any]:
            async with semaphore:
                result = await self.scrape_url(url)
                # Add delay between requests to be respectful
                await asyncio.sleep(settings.request_delay)
                return result
        
        logger.info(f"Starting concurrent scraping of {len(urls)} URLs")
        
        tasks = [scrape_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error scraping {urls[i]}: {result}")
                processed_results.append(
                    self._create_error_result(urls[i], str(result), 0)
                )
            else:
                processed_results.append(result)
        
        return processed_results
    
    def _get_extraction_strategy(self, strategy_type: str, site_strategy: str):
        """Get the appropriate extraction strategy based on content type."""
        
        if strategy_type == "academic" or site_strategy == "academic":
            # Strategy optimized for academic papers and research content
            return LLMExtractionStrategy(
                provider="openai",
                api_token=settings.openai_api_key,
                instruction="""
                Extract the following from this academic/research content:
                1. Title and authors
                2. Abstract or summary
                3. Key findings and conclusions
                4. Methodology if mentioned
                5. References and citations
                6. Keywords or tags
                
                Focus on academic rigor and research-specific information.
                """,
                schema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "authors": {"type": "array", "items": {"type": "string"}},
                        "abstract": {"type": "string"},
                        "key_findings": {"type": "array", "items": {"type": "string"}},
                        "methodology": {"type": "string"},
                        "references": {"type": "array", "items": {"type": "string"}},
                        "keywords": {"type": "array", "items": {"type": "string"}}
                    }
                }
            )
        
        elif strategy_type == "news" or site_strategy == "news":
            # Strategy optimized for news articles
            return LLMExtractionStrategy(
                provider="openai",
                api_token=settings.openai_api_key,
                instruction="""
                Extract the following from this news article:
                1. Headline and subheadline
                2. Author and publication date
                3. Main story summary
                4. Key quotes
                5. Sources mentioned
                6. Location/dateline
                
                Focus on journalistic elements and factual information.
                """,
                schema={
                    "type": "object",
                    "properties": {
                        "headline": {"type": "string"},
                        "author": {"type": "string"},
                        "publication_date": {"type": "string"},
                        "summary": {"type": "string"},
                        "key_quotes": {"type": "array", "items": {"type": "string"}},
                        "sources": {"type": "array", "items": {"type": "string"}},
                        "location": {"type": "string"}
                    }
                }
            )
        
        else:
            # General content extraction using cosine similarity
            return CosineStrategy(
                semantic_filter="research academic scholarly scientific study analysis",
                word_count_threshold=100,
                max_dist=0.2,
                linkage_method="ward",
                top_k=5
            )
    
    def _process_crawl_result(self, result, url: str, processing_time: float) -> Dict[str, Any]:
        """Process and standardize crawl results."""
        
        # Extract basic content
        content = {
            "url": url,
            "title": getattr(result, 'title', '') or "No title found",
            "content": getattr(result, 'cleaned_html', '') or getattr(result, 'markdown', ''),
            "raw_html": getattr(result, 'html', ''),
            "processing_time": processing_time,
            "success": True,
            "error": None
        }
        
        # Add extracted data if available
        if hasattr(result, 'extracted_content') and result.extracted_content:
            try:
                import json
                if isinstance(result.extracted_content, str):
                    content["extracted_data"] = json.loads(result.extracted_content)
                else:
                    content["extracted_data"] = result.extracted_content
            except (json.JSONDecodeError, TypeError):
                content["extracted_data"] = {"raw": str(result.extracted_content)}
        
        # Add metadata
        content["metadata"] = {
            "word_count": len(content["content"].split()),
            "character_count": len(content["content"]),
            "has_extracted_data": "extracted_data" in content,
            "processing_strategy": "crawl4ai"
        }
        
        # Add links if available
        if hasattr(result, 'links') and result.links:
            content["links"] = result.links
            
        return content
    
    def _create_error_result(self, url: str, error_message: str, processing_time: float) -> Dict[str, Any]:
        """Create a standardized error result."""
        return {
            "url": url,
            "title": "",
            "content": "",
            "raw_html": "",
            "processing_time": processing_time,
            "success": False,
            "error": error_message,
            "metadata": {
                "word_count": 0,
                "character_count": 0,
                "has_extracted_data": False,
                "processing_strategy": "crawl4ai_error"
            }
        }
    
    async def cleanup(self):
        """Clean up resources."""
        if self.crawler and self.is_initialized:
            try:
                await self.crawler.cleanup()
                logger.info("Crawl4AI agent cleaned up successfully")
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
            finally:
                self.is_initialized = False
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()