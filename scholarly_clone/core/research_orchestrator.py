"""
Research Orchestrator for Scholarly Clone.
Main component that coordinates the entire research pipeline.
"""

import asyncio
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from loguru import logger
from ..agents.crawl4ai_agent import ScholaryCrawl4AIAgent
from ..agents.url_discovery import URLDiscoveryAgent, URLCandidate
from ..pipeline.langchain_processor import LangChainProcessor
from ..models.schemas import (
    ResearchQuery, ResearchResponse, ScrapedSource, 
    SourceType, QueryType, Citation, ExtractedInsight
)
from ..core.config import settings


class ResearchOrchestrator:
    """
    Main orchestrator that coordinates the entire research pipeline:
    User Query → URL Discovery → Crawl4AI Scraping → LangChain Processing → Formatted Response
    """
    
    def __init__(self):
        self.url_discovery_agent = None
        self.crawl4ai_agent = None
        self.langchain_processor = None
        
    async def __aenter__(self):
        """Initialize all components."""
        logger.info("Initializing Research Orchestrator")
        
        # Initialize components
        self.url_discovery_agent = URLDiscoveryAgent()
        self.crawl4ai_agent = ScholaryCrawl4AIAgent()
        self.langchain_processor = LangChainProcessor()
        
        # Initialize async components
        await self.url_discovery_agent.__aenter__()
        await self.crawl4ai_agent.__aenter__()
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up all components."""
        logger.info("Cleaning up Research Orchestrator")
        
        if self.url_discovery_agent:
            await self.url_discovery_agent.__aexit__(exc_type, exc_val, exc_tb)
        
        if self.crawl4ai_agent:
            await self.crawl4ai_agent.__aexit__(exc_type, exc_val, exc_tb)
    
    async def conduct_research(self, research_query: ResearchQuery) -> ResearchResponse:
        """
        Conduct comprehensive research following the full pipeline.
        
        Architecture Flow:
        User Query → URL Discovery + Prioritization → Playwright Scraper → 
        Raw Text → LangChain Pipeline (Summarize + Extract Citations + Extract Insights) → 
        Formatted JSON Response
        
        Args:
            research_query: The research query request
            
        Returns:
            Complete research response with processed sources
        """
        start_time = time.time()
        
        logger.info(f"Starting research for query: '{research_query.query}' (type: {research_query.query_type})")
        
        try:
            # Step 1: URL Discovery + Prioritization
            logger.info("Step 1: URL Discovery and Prioritization")
            url_candidates = await self._discover_urls(research_query)
            
            if not url_candidates:
                logger.warning("No URLs discovered for the query")
                return self._create_empty_response(research_query, "No relevant sources found")
            
            logger.info(f"Discovered {len(url_candidates)} URL candidates")
            
            # Step 2: Playwright Scraper (via Crawl4AI)
            logger.info("Step 2: Web Scraping with Crawl4AI")
            scraped_content = await self._scrape_urls(url_candidates, research_query.query_type)
            
            successful_scrapes = [content for content in scraped_content if content.get("success", False)]
            logger.info(f"Successfully scraped {len(successful_scrapes)} out of {len(url_candidates)} URLs")
            
            if not successful_scrapes:
                logger.warning("No content successfully scraped")
                return self._create_empty_response(research_query, "Failed to scrape any content")
            
            # Step 3: LangChain Pipeline (Summarize + Extract Citations + Extract Insights)
            logger.info("Step 3: LangChain Processing Pipeline")
            processed_content = await self._process_content(successful_scrapes, research_query.query)
            
            # Step 4: Aggregate and format results
            logger.info("Step 4: Aggregating and formatting results")
            research_response = await self._create_research_response(
                research_query, 
                url_candidates,
                processed_content,
                start_time
            )
            
            logger.info(f"Research completed in {research_response.processing_time:.2f} seconds")
            return research_response
            
        except Exception as e:
            logger.error(f"Research orchestration failed: {e}")
            processing_time = time.time() - start_time
            return self._create_error_response(research_query, str(e), processing_time)
    
    async def _discover_urls(self, research_query: ResearchQuery) -> List[URLCandidate]:
        """Step 1: Discover and prioritize URLs for the research query."""
        try:
            url_candidates = await self.url_discovery_agent.discover_urls(
                query=research_query.query,
                query_type=research_query.query_type,
                max_results=research_query.max_results,
                include_domains=research_query.include_domains,
                exclude_domains=research_query.exclude_domains
            )
            
            # Log discovered URLs for debugging
            for i, candidate in enumerate(url_candidates[:5]):  # Log first 5
                logger.debug(f"URL {i+1}: {candidate.url} (score: {candidate.relevance_score:.2f})")
            
            return url_candidates
            
        except Exception as e:
            logger.error(f"URL discovery failed: {e}")
            return []
    
    async def _scrape_urls(self, url_candidates: List[URLCandidate], query_type: QueryType) -> List[Dict[str, Any]]:
        """Step 2: Scrape the discovered URLs using Crawl4AI."""
        urls_to_scrape = [candidate.url for candidate in url_candidates]
        
        try:
            # Determine extraction strategy based on query type
            extraction_strategy = self._get_extraction_strategy(query_type)
            
            # Scrape URLs concurrently
            scraped_results = await self.crawl4ai_agent.scrape_multiple_urls(
                urls=urls_to_scrape,
                max_concurrent=settings.max_concurrent_requests
            )
            
            # Enhance results with URL candidate metadata
            enhanced_results = []
            for i, result in enumerate(scraped_results):
                if i < len(url_candidates):
                    candidate = url_candidates[i]
                    result["source_type"] = candidate.source_type.value
                    result["discovery_source"] = candidate.discovery_source
                    result["relevance_score"] = candidate.relevance_score
                    result["estimated_quality"] = candidate.estimated_quality
                
                enhanced_results.append(result)
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"URL scraping failed: {e}")
            return []
    
    async def _process_content(self, scraped_content: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Step 3: Process scraped content through LangChain pipeline."""
        try:
            # Prepare content for processing
            content_for_processing = []
            for content_data in scraped_content:
                if content_data.get("success") and content_data.get("content"):
                    content_for_processing.append({
                        "content": content_data["content"],
                        "url": content_data["url"],
                        "source_type": content_data.get("source_type", "website")
                    })
            
            # Process content through LangChain pipeline
            processed_results = await self.langchain_processor.process_multiple_contents(
                contents=content_for_processing,
                query=query
            )
            
            # Combine scraping results with processing results
            combined_results = []
            for i, scraped in enumerate(scraped_content):
                if i < len(processed_results):
                    processed = processed_results[i]
                    combined = {**scraped, **processed}
                else:
                    combined = scraped
                
                combined_results.append(combined)
            
            return combined_results
            
        except Exception as e:
            logger.error(f"Content processing failed: {e}")
            return scraped_content  # Return scraped content without processing
    
    async def _create_research_response(self,
                                      research_query: ResearchQuery,
                                      url_candidates: List[URLCandidate],
                                      processed_content: List[Dict[str, Any]],
                                      start_time: float) -> ResearchResponse:
        """Step 4: Create the final formatted research response."""
        
        # Create ScrapedSource objects
        sources = []
        successful_summaries = []
        all_insights = []
        all_citations = []
        
        for content_data in processed_content:
            if not content_data.get("success", False):
                continue
                
            # Extract citations
            citations = []
            if content_data.get("citations"):
                for citation_data in content_data["citations"]:
                    if isinstance(citation_data, dict):
                        citations.append(Citation(**citation_data))
                    elif hasattr(citation_data, '__dict__'):
                        citations.append(citation_data)
            
            # Extract insights
            insights = []
            if content_data.get("insights"):
                for insight_data in content_data["insights"]:
                    if isinstance(insight_data, dict):
                        insights.append(ExtractedInsight(**insight_data))
                    elif hasattr(insight_data, '__dict__'):
                        insights.append(insight_data)
            
            # Determine source type
            source_type_str = content_data.get("source_type", "website")
            try:
                source_type = SourceType(source_type_str)
            except ValueError:
                source_type = SourceType.WEBSITE
            
            # Create ScrapedSource
            source = ScrapedSource(
                url=content_data["url"],
                title=content_data.get("title", "No title"),
                summary=content_data.get("summary", "No summary available"),
                content_preview=content_data.get("content", "")[:500],  # First 500 chars
                source_type=source_type,
                citations=citations,
                insights=insights,
                metadata={
                    "word_count": content_data.get("word_count", 0),
                    "character_count": content_data.get("character_count", 0),
                    "processing_time": content_data.get("processing_time", 0),
                    "quality_assessment": content_data.get("quality_assessment", {}),
                    "discovery_source": content_data.get("discovery_source", "unknown"),
                    "relevance_score": content_data.get("relevance_score", 0.0)
                },
                processing_time=content_data.get("processing_time", 0.0)
            )
            
            sources.append(source)
            
            # Collect data for overall analysis
            if content_data.get("summary"):
                successful_summaries.append(content_data["summary"])
            
            all_insights.extend(insights)
            all_citations.extend(citations)
        
        # Generate overall summary
        if successful_summaries:
            overall_summary = await self.langchain_processor.generate_overall_summary(
                successful_summaries, 
                research_query.query
            )
        else:
            overall_summary = "No content available for summary generation."
        
        # Extract key findings from insights
        key_findings = []
        high_relevance_insights = [
            insight for insight in all_insights 
            if insight.relevance_score > 0.7
        ]
        
        for insight in high_relevance_insights[:5]:  # Top 5 key findings
            key_findings.append(insight.insight)
        
        # Generate related topics (simplified approach)
        related_topics = self._extract_related_topics(successful_summaries, research_query.query)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(sources, all_insights)
        
        # Calculate processing time
        total_processing_time = time.time() - start_time
        
        return ResearchResponse(
            query=research_query.query,
            query_type=research_query.query_type,
            sources=sources,
            overall_summary=overall_summary,
            key_findings=key_findings,
            related_topics=related_topics,
            confidence_score=confidence_score,
            total_sources_found=len(url_candidates),
            sources_processed=len(sources),
            processing_time=total_processing_time
        )
    
    def _get_extraction_strategy(self, query_type: QueryType) -> str:
        """Determine the extraction strategy based on query type."""
        strategy_map = {
            QueryType.ACADEMIC: "academic",
            QueryType.NEWS: "news",
            QueryType.GENERAL: "general",
            QueryType.COMPARATIVE: "general"
        }
        return strategy_map.get(query_type, "general")
    
    def _extract_related_topics(self, summaries: List[str], original_query: str) -> List[str]:
        """Extract related topics from summaries (simplified implementation)."""
        # This is a simplified approach - in production, you might use more sophisticated NLP
        related_topics = []
        
        # Common research-related keywords that often indicate related topics
        topic_indicators = [
            "related", "similar", "compared to", "in contrast", "furthermore",
            "additionally", "meanwhile", "consequently", "therefore"
        ]
        
        # Extract potential topics (this is a placeholder implementation)
        for summary in summaries:
            words = summary.lower().split()
            for i, word in enumerate(words):
                if word in topic_indicators and i + 1 < len(words):
                    # Take the next few words as potential related topic
                    topic_candidate = " ".join(words[i+1:i+4])
                    if len(topic_candidate) > 10 and topic_candidate not in related_topics:
                        related_topics.append(topic_candidate.title())
        
        return related_topics[:5]  # Return top 5 related topics
    
    def _calculate_confidence_score(self, sources: List[ScrapedSource], insights: List[ExtractedInsight]) -> float:
        """Calculate overall confidence score for the research."""
        if not sources:
            return 0.0
        
        # Factor in source quality
        quality_scores = []
        for source in sources:
            quality_assessment = source.metadata.get("quality_assessment", {})
            quality_score = quality_assessment.get("quality_score", 0.5)
            quality_scores.append(quality_score)
        
        avg_quality = sum(quality_scores) / len(quality_scores)
        
        # Factor in insight relevance
        if insights:
            avg_insight_relevance = sum(insight.relevance_score for insight in insights) / len(insights)
        else:
            avg_insight_relevance = 0.5
        
        # Factor in number of successful sources
        source_coverage = min(len(sources) / 5, 1.0)  # Normalized to 5 sources as good coverage
        
        # Weighted combination
        confidence = (avg_quality * 0.4 + avg_insight_relevance * 0.3 + source_coverage * 0.3)
        
        return min(confidence, 1.0)
    
    def _create_empty_response(self, research_query: ResearchQuery, reason: str) -> ResearchResponse:
        """Create an empty response when research fails."""
        return ResearchResponse(
            query=research_query.query,
            query_type=research_query.query_type,
            sources=[],
            overall_summary=f"Research could not be completed: {reason}",
            key_findings=[],
            related_topics=[],
            confidence_score=0.0,
            total_sources_found=0,
            sources_processed=0,
            processing_time=0.0
        )
    
    def _create_error_response(self, research_query: ResearchQuery, error: str, processing_time: float) -> ResearchResponse:
        """Create an error response when research fails."""
        return ResearchResponse(
            query=research_query.query,
            query_type=research_query.query_type,
            sources=[],
            overall_summary=f"Research failed due to error: {error}",
            key_findings=[],
            related_topics=[],
            confidence_score=0.0,
            total_sources_found=0,
            sources_processed=0,
            processing_time=processing_time
        )