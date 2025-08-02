"""
Pydantic models for API requests and responses.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum


class QueryType(str, Enum):
    """Types of research queries supported."""
    ACADEMIC = "academic"
    NEWS = "news"
    GENERAL = "general"
    COMPARATIVE = "comparative"


class SourceType(str, Enum):
    """Types of sources that can be scraped."""
    ACADEMIC_PAPER = "academic_paper"
    NEWS_ARTICLE = "news_article"
    BLOG_POST = "blog_post"
    WEBSITE = "website"
    DOCUMENTATION = "documentation"


class ResearchQuery(BaseModel):
    """Request model for research queries."""
    query: str = Field(..., description="The research question or topic to investigate")
    query_type: QueryType = Field(default=QueryType.GENERAL, description="Type of research query")
    max_results: int = Field(default=10, ge=1, le=50, description="Maximum number of sources to analyze")
    include_domains: Optional[List[str]] = Field(default=None, description="Specific domains to include")
    exclude_domains: Optional[List[str]] = Field(default=None, description="Domains to exclude from search")
    language: str = Field(default="en", description="Language preference for sources")
    date_range: Optional[Dict[str, str]] = Field(default=None, description="Date range filter (start_date, end_date)")


class Citation(BaseModel):
    """Model for extracted citations."""
    text: str = Field(..., description="The citation text")
    context: str = Field(..., description="Surrounding context where citation appears")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for citation extraction")
    citation_type: Optional[str] = Field(default=None, description="Type of citation (e.g., author-date, numeric)")


class ExtractedInsight(BaseModel):
    """Model for extracted insights from content."""
    insight: str = Field(..., description="The extracted insight or key finding")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance to the original query")
    supporting_evidence: List[str] = Field(default=[], description="Supporting evidence for the insight")
    category: Optional[str] = Field(default=None, description="Category of the insight")


class ScrapedSource(BaseModel):
    """Model for a scraped source with processed content."""
    url: HttpUrl = Field(..., description="Source URL")
    title: str = Field(..., description="Page title")
    summary: str = Field(..., description="Generated summary of the content")
    content_preview: str = Field(..., description="Preview of the raw content")
    source_type: SourceType = Field(..., description="Type of source")
    citations: List[Citation] = Field(default=[], description="Extracted citations")
    insights: List[ExtractedInsight] = Field(default=[], description="Extracted insights")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")
    scraped_at: datetime = Field(default_factory=datetime.utcnow, description="When the source was scraped")
    processing_time: float = Field(..., description="Time taken to process this source (seconds)")


class ResearchResponse(BaseModel):
    """Response model for research queries."""
    query: str = Field(..., description="Original research query")
    query_type: QueryType = Field(..., description="Type of query processed")
    sources: List[ScrapedSource] = Field(..., description="Processed sources")
    overall_summary: str = Field(..., description="Overall summary across all sources")
    key_findings: List[str] = Field(default=[], description="Key findings from the research")
    related_topics: List[str] = Field(default=[], description="Related topics discovered")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall confidence in the results")
    total_sources_found: int = Field(..., description="Total number of sources discovered")
    sources_processed: int = Field(..., description="Number of sources successfully processed")
    processing_time: float = Field(..., description="Total processing time in seconds")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the response was generated")


class URLDiscoveryRequest(BaseModel):
    """Request model for URL discovery."""
    query: str = Field(..., description="Search query for URL discovery")
    max_urls: int = Field(default=20, ge=1, le=100, description="Maximum URLs to discover")
    source_types: List[SourceType] = Field(default=[], description="Preferred source types")
    search_engines: List[str] = Field(default=["google", "bing"], description="Search engines to use")


class URLDiscoveryResponse(BaseModel):
    """Response model for URL discovery."""
    query: str = Field(..., description="Original search query")
    urls: List[Dict[str, Any]] = Field(..., description="Discovered URLs with metadata")
    total_found: int = Field(..., description="Total URLs found")
    discovery_time: float = Field(..., description="Time taken for discovery in seconds")


class ScrapingStatus(BaseModel):
    """Model for tracking scraping status."""
    url: HttpUrl = Field(..., description="URL being scraped")
    status: str = Field(..., description="Current status (pending, processing, completed, failed)")
    progress: float = Field(default=0.0, ge=0.0, le=1.0, description="Progress percentage")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    started_at: datetime = Field(default_factory=datetime.utcnow, description="When scraping started")
    completed_at: Optional[datetime] = Field(default=None, description="When scraping completed")


class HealthCheck(BaseModel):
    """Health check response model."""
    status: str = Field(default="healthy", description="Service status")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    dependencies: Dict[str, str] = Field(default={}, description="Status of dependencies")