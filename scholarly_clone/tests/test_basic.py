"""
Basic tests for Scholarly Clone functionality.
"""

import pytest
from unittest.mock import Mock, patch
from scholarly_clone.models.schemas import ResearchQuery, QueryType, SourceType
from scholarly_clone.core.config import settings


def test_research_query_validation():
    """Test ResearchQuery model validation."""
    # Valid query
    query = ResearchQuery(
        query="What is quantum computing?",
        query_type=QueryType.ACADEMIC,
        max_results=10
    )
    
    assert query.query == "What is quantum computing?"
    assert query.query_type == QueryType.ACADEMIC
    assert query.max_results == 10
    assert query.language == "en"  # Default value


def test_research_query_invalid_max_results():
    """Test ResearchQuery validation with invalid max_results."""
    with pytest.raises(ValueError):
        ResearchQuery(
            query="test query",
            max_results=100  # Should fail due to le=50 constraint
        )


def test_source_type_enum():
    """Test SourceType enum values."""
    assert SourceType.ACADEMIC_PAPER == "academic_paper"
    assert SourceType.NEWS_ARTICLE == "news_article"
    assert SourceType.WEBSITE == "website"


def test_query_type_enum():
    """Test QueryType enum values."""
    assert QueryType.ACADEMIC == "academic"
    assert QueryType.NEWS == "news"
    assert QueryType.GENERAL == "general"
    assert QueryType.COMPARATIVE == "comparative"


def test_settings_loading():
    """Test that settings can be loaded."""
    # Settings should load without error
    assert hasattr(settings, 'max_concurrent_requests')
    assert hasattr(settings, 'request_delay')
    assert hasattr(settings, 'max_pages_per_query')


@pytest.mark.asyncio
async def test_url_discovery_agent_initialization():
    """Test URL discovery agent can be initialized."""
    from scholarly_clone.agents.url_discovery import URLDiscoveryAgent
    
    agent = URLDiscoveryAgent()
    assert agent.session is None  # Should be None before context manager
    
    # Test context manager initialization
    async with agent as initialized_agent:
        assert initialized_agent.session is not None


def test_url_candidate_creation():
    """Test URL candidate creation."""
    from scholarly_clone.agents.url_discovery import URLCandidate
    from datetime import datetime
    
    candidate = URLCandidate(
        url="https://example.com",
        title="Test Article",
        snippet="Test snippet",
        source_type=SourceType.WEBSITE,
        domain="example.com",
        relevance_score=0.85,
        discovery_source="test",
        estimated_quality=0.9,
        language="en",
        date_published=datetime.now()
    )
    
    assert candidate.url == "https://example.com"
    assert candidate.relevance_score == 0.85
    assert candidate.source_type == SourceType.WEBSITE


def test_scraping_targets_config():
    """Test scraping targets configuration."""
    from scholarly_clone.core.config import ScrapingTargets
    
    # Test academic sites list
    assert "arxiv.org" in ScrapingTargets.ACADEMIC_SITES
    assert "scholar.google.com" in ScrapingTargets.ACADEMIC_SITES
    
    # Test news sites list
    assert "reuters.com" in ScrapingTargets.NEWS_SITES
    assert "bbc.com" in ScrapingTargets.NEWS_SITES
    
    # Test site configuration
    config = ScrapingTargets.get_site_config("arxiv.org")
    assert config["extraction_strategy"] == "academic"
    assert config["wait_for"] == "networkidle"


@pytest.mark.asyncio
async def test_langchain_processor_initialization():
    """Test LangChain processor can be initialized."""
    with patch('scholarly_clone.pipeline.langchain_processor.ChatOpenAI'):
        from scholarly_clone.pipeline.langchain_processor import LangChainProcessor
        
        processor = LangChainProcessor()
        assert processor.llm is not None
        assert processor.text_splitter is not None


def test_package_imports():
    """Test that main package components can be imported."""
    # Test core imports
    from scholarly_clone.core import settings, ResearchOrchestrator
    from scholarly_clone.models import ResearchQuery, ResearchResponse
    from scholarly_clone.agents import URLDiscoveryAgent
    from scholarly_clone.pipeline import LangChainProcessor
    
    # All imports should succeed without error
    assert settings is not None
    assert ResearchOrchestrator is not None
    assert ResearchQuery is not None
    assert URLDiscoveryAgent is not None
    assert LangChainProcessor is not None


def test_version_import():
    """Test that version can be imported."""
    from scholarly_clone import __version__
    assert __version__ == "1.0.0"


if __name__ == "__main__":
    pytest.main([__file__])