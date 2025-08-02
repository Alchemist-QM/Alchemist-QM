"""
FastAPI endpoints for Scholarly Clone research API.
"""

import asyncio
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from loguru import logger
from ..core.config import settings
from ..core.research_orchestrator import ResearchOrchestrator
from ..models.schemas import (
    ResearchQuery, ResearchResponse, URLDiscoveryRequest, 
    URLDiscoveryResponse, HealthCheck, ScrapingStatus
)
from .. import __version__

# Global orchestrator instance
orchestrator: Optional[ResearchOrchestrator] = None


async def get_orchestrator() -> ResearchOrchestrator:
    """Dependency to get the research orchestrator."""
    global orchestrator
    if orchestrator is None:
        orchestrator = ResearchOrchestrator()
        await orchestrator.__aenter__()
    return orchestrator


# FastAPI app initialization
app = FastAPI(
    title="Scholarly Clone API",
    description="A research-focused web scraping and summarization platform",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    logger.info("Starting Scholarly Clone API")
    global orchestrator
    orchestrator = ResearchOrchestrator()
    await orchestrator.__aenter__()
    logger.info("Research orchestrator initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("Shutting down Scholarly Clone API")
    global orchestrator
    if orchestrator:
        await orchestrator.__aexit__(None, None, None)
        orchestrator = None
    logger.info("Research orchestrator cleaned up")


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with basic information."""
    return {
        "message": "Welcome to Scholarly Clone API",
        "version": __version__,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    try:
        # Test database connection, Redis, etc. here
        dependencies = {
            "orchestrator": "healthy" if orchestrator else "not_initialized",
            "openai": "configured" if settings.openai_api_key else "not_configured"
        }
        
        return HealthCheck(
            status="healthy",
            version=__version__,
            dependencies=dependencies
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.post("/research", response_model=ResearchResponse)
async def conduct_research(
    query: ResearchQuery,
    orchestrator: ResearchOrchestrator = Depends(get_orchestrator)
):
    """
    Main research endpoint that conducts comprehensive research on a given query.
    
    This endpoint follows the complete pipeline:
    1. URL Discovery + Prioritization
    2. Web Scraping with Crawl4AI
    3. LangChain Processing (Summarization + Citation Extraction + Insights)
    4. Formatted JSON Response
    """
    try:
        logger.info(f"Received research request: {query.query}")
        
        # Validate query
        if not query.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        if len(query.query) > 1000:
            raise HTTPException(status_code=400, detail="Query too long (max 1000 characters)")
        
        # Conduct research
        response = await orchestrator.conduct_research(query)
        
        logger.info(f"Research completed for query: {query.query}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Research failed: {e}")
        raise HTTPException(status_code=500, detail=f"Research failed: {str(e)}")


@app.post("/discover-urls", response_model=URLDiscoveryResponse)
async def discover_urls(
    request: URLDiscoveryRequest,
    orchestrator: ResearchOrchestrator = Depends(get_orchestrator)
):
    """
    URL discovery endpoint for finding relevant sources.
    This is a subset of the full research pipeline, focusing only on URL discovery.
    """
    try:
        logger.info(f"URL discovery request: {request.query}")
        
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Use the URL discovery agent
        url_candidates = await orchestrator.url_discovery_agent.discover_urls(
            query=request.query,
            max_results=request.max_urls,
            include_domains=None,
            exclude_domains=None
        )
        
        # Convert to response format
        urls = []
        for candidate in url_candidates:
            urls.append({
                "url": candidate.url,
                "title": candidate.title,
                "snippet": candidate.snippet,
                "source_type": candidate.source_type.value,
                "domain": candidate.domain,
                "relevance_score": candidate.relevance_score,
                "discovery_source": candidate.discovery_source,
                "estimated_quality": candidate.estimated_quality,
                "language": candidate.language,
                "date_published": candidate.date_published.isoformat() if candidate.date_published else None
            })
        
        return URLDiscoveryResponse(
            query=request.query,
            urls=urls,
            total_found=len(urls),
            discovery_time=1.0  # Placeholder
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"URL discovery failed: {e}")
        raise HTTPException(status_code=500, detail=f"URL discovery failed: {str(e)}")


@app.post("/scrape-url")
async def scrape_single_url(
    url: str,
    extraction_strategy: str = "general",
    orchestrator: ResearchOrchestrator = Depends(get_orchestrator)
):
    """
    Scrape a single URL using Crawl4AI.
    This endpoint allows testing the scraping functionality on individual URLs.
    """
    try:
        if not url.strip():
            raise HTTPException(status_code=400, detail="URL cannot be empty")
        
        if not url.startswith(('http://', 'https://')):
            raise HTTPException(status_code=400, detail="URL must start with http:// or https://")
        
        logger.info(f"Scraping URL: {url}")
        
        # Scrape the URL
        result = await orchestrator.crawl4ai_agent.scrape_url(
            url=url,
            extraction_strategy=extraction_strategy
        )
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"URL scraping failed: {e}")
        raise HTTPException(status_code=500, detail=f"URL scraping failed: {str(e)}")


@app.post("/process-content")
async def process_content(
    content: str,
    query: str,
    source_url: str = "https://example.com",
    source_type: str = "website",
    orchestrator: ResearchOrchestrator = Depends(get_orchestrator)
):
    """
    Process content through the LangChain pipeline.
    This endpoint allows testing the content processing functionality.
    """
    try:
        if not content.strip():
            raise HTTPException(status_code=400, detail="Content cannot be empty")
        
        if not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        logger.info(f"Processing content for query: {query}")
        
        # Process content
        from ..models.schemas import SourceType
        try:
            source_type_enum = SourceType(source_type)
        except ValueError:
            source_type_enum = SourceType.WEBSITE
        
        result = await orchestrator.langchain_processor.process_content(
            content=content,
            query=query,
            source_url=source_url,
            source_type=source_type_enum
        )
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Content processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Content processing failed: {str(e)}")


@app.get("/stats")
async def get_stats():
    """Get basic statistics about the service."""
    try:
        # In a production system, these would come from a database
        stats = {
            "total_queries_processed": 0,  # Placeholder
            "total_urls_scraped": 0,      # Placeholder
            "avg_processing_time": 0.0,   # Placeholder
            "success_rate": 0.95,         # Placeholder
            "supported_source_types": [source_type.value for source_type in SourceType],
            "supported_query_types": [query_type.value for query_type in QueryType],
            "max_concurrent_requests": settings.max_concurrent_requests,
            "max_pages_per_query": settings.max_pages_per_query
        }
        
        return JSONResponse(content=stats)
        
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")


@app.get("/config")
async def get_config():
    """Get public configuration information."""
    try:
        config = {
            "max_results_per_query": 50,
            "supported_languages": ["en"],  # Expand as needed
            "rate_limits": {
                "requests_per_minute": 60,
                "concurrent_requests": settings.max_concurrent_requests
            },
            "features": {
                "url_discovery": True,
                "web_scraping": True,
                "content_summarization": True,
                "citation_extraction": True,
                "insight_generation": True,
                "quality_assessment": True
            }
        }
        
        return JSONResponse(content=config)
        
    except Exception as e:
        logger.error(f"Config retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Config retrieval failed: {str(e)}")


@app.get("/frontend/")
async def serve_frontend():
    """Serve the frontend HTML interface."""
    try:
        frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
        if os.path.exists(frontend_path):
            return FileResponse(frontend_path)
        else:
            raise HTTPException(status_code=404, detail="Frontend not found")
    except Exception as e:
        logger.error(f"Frontend serving failed: {e}")
        raise HTTPException(status_code=500, detail=f"Frontend serving failed: {str(e)}")


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content={"detail": "Endpoint not found"}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Development server function
def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = True):
    """Run the development server."""
    uvicorn.run(
        "scholarly_clone.api.endpoints:app",
        host=host,
        port=port,
        reload=reload,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    run_server()