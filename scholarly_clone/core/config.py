"""
Core configuration module for Scholarly Clone.
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, Field
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    
    # Database Configuration
    database_url: str = Field(default="sqlite:///./scholarly_clone.db", env="DATABASE_URL")
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # Web Scraping Configuration
    user_agent: str = Field(default="ScholaryClone/1.0", env="USER_AGENT")
    max_concurrent_requests: int = Field(default=5, env="MAX_CONCURRENT_REQUESTS")
    request_delay: float = Field(default=1.0, env="REQUEST_DELAY")
    
    # LangChain Configuration
    langchain_tracing_v2: bool = Field(default=False, env="LANGCHAIN_TRACING_V2")
    langchain_api_key: Optional[str] = Field(default=None, env="LANGCHAIN_API_KEY")
    
    # Application Configuration
    debug: bool = Field(default=True, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    max_pages_per_query: int = Field(default=10, env="MAX_PAGES_PER_QUERY")
    
    # Playwright Configuration
    playwright_headless: bool = Field(default=True, env="PLAYWRIGHT_HEADLESS")
    playwright_timeout: int = Field(default=30000, env="PLAYWRIGHT_TIMEOUT")
    
    # Crawl4AI Configuration
    crawl4ai_verbose: bool = Field(default=False, env="CRAWL4AI_VERBOSE")
    crawl4ai_warmup: bool = Field(default=True, env="CRAWL4AI_WARMUP")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


class ScrapingTargets:
    """Configuration for different scraping targets and their specific requirements."""
    
    ACADEMIC_SITES = [
        "arxiv.org",
        "scholar.google.com",
        "pubmed.ncbi.nlm.nih.gov",
        "jstor.org",
        "ieee.org",
        "acm.org",
        "researchgate.net",
        "academia.edu"
    ]
    
    NEWS_SITES = [
        "reuters.com",
        "bbc.com",
        "cnn.com",
        "npr.org",
        "theguardian.com",
        "nytimes.com"
    ]
    
    BLOG_SITES = [
        "medium.com",
        "dev.to",
        "hackernoon.com",
        "towardsdatascience.com"
    ]
    
    @classmethod
    def get_site_config(cls, domain: str) -> dict:
        """Get specific configuration for a domain."""
        if any(site in domain for site in cls.ACADEMIC_SITES):
            return {
                "wait_for": "networkidle",
                "timeout": 45000,
                "js_code": None,
                "extraction_strategy": "academic"
            }
        elif any(site in domain for site in cls.NEWS_SITES):
            return {
                "wait_for": "domcontentloaded",
                "timeout": 30000,
                "js_code": """
                // Remove ads and popups
                document.querySelectorAll('[class*="ad"], [id*="ad"], .popup, .modal').forEach(el => el.remove());
                """,
                "extraction_strategy": "news"
            }
        else:
            return {
                "wait_for": "networkidle",
                "timeout": 30000,
                "js_code": None,
                "extraction_strategy": "general"
            }