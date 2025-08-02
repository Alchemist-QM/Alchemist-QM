"""
URL Discovery and Prioritization Agent for Scholarly Clone.
This module handles intelligent URL discovery based on research queries.
"""

import asyncio
import aiohttp
import re
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse, urljoin, quote_plus
from dataclasses import dataclass
from datetime import datetime, timedelta
import validators

from loguru import logger
from ..core.config import settings, ScrapingTargets
from ..models.schemas import SourceType, QueryType


@dataclass
class URLCandidate:
    """Represents a discovered URL candidate with metadata."""
    url: str
    title: str
    snippet: str
    source_type: SourceType
    domain: str
    relevance_score: float
    discovery_source: str  # google, bing, direct, etc.
    estimated_quality: float
    language: str
    date_published: Optional[datetime] = None


class URLDiscoveryAgent:
    """
    Intelligent URL discovery agent that finds and prioritizes relevant sources
    based on research queries and content types.
    """
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": settings.user_agent}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def discover_urls(self, 
                           query: str, 
                           query_type: QueryType = QueryType.GENERAL,
                           max_results: int = 20,
                           include_domains: Optional[List[str]] = None,
                           exclude_domains: Optional[List[str]] = None) -> List[URLCandidate]:
        """
        Discover URLs relevant to the research query.
        
        Args:
            query: The research query
            query_type: Type of query (academic, news, etc.)
            max_results: Maximum number of URLs to return
            include_domains: Specific domains to include
            exclude_domains: Domains to exclude
            
        Returns:
            List of prioritized URL candidates
        """
        logger.info(f"Starting URL discovery for query: '{query}' (type: {query_type})")
        
        # Generate search variations based on query type
        search_queries = self._generate_search_queries(query, query_type)
        
        # Discover URLs from multiple sources
        discovery_tasks = []
        
        # Google Scholar for academic queries
        if query_type == QueryType.ACADEMIC:
            discovery_tasks.append(
                self._search_google_scholar(search_queries[0], max_results // 3)
            )
        
        # General Google search
        discovery_tasks.append(
            self._search_google(search_queries[0], max_results // 2, query_type)
        )
        
        # Bing search as backup
        discovery_tasks.append(
            self._search_bing(search_queries[0], max_results // 3, query_type)
        )
        
        # Direct domain searches for specific sites
        if include_domains:
            for domain in include_domains:
                discovery_tasks.append(
                    self._search_domain_specific(query, domain, max_results // len(include_domains))
                )
        
        # Execute all discovery tasks concurrently
        results = await asyncio.gather(*discovery_tasks, return_exceptions=True)
        
        # Combine and deduplicate results
        all_candidates = []
        for result in results:
            if isinstance(result, list):
                all_candidates.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Discovery task failed: {result}")
        
        # Filter and prioritize
        filtered_candidates = self._filter_candidates(
            all_candidates, include_domains, exclude_domains
        )
        
        # Prioritize and limit results
        prioritized = self._prioritize_candidates(filtered_candidates, query, query_type)
        
        return prioritized[:max_results]
    
    def _generate_search_queries(self, query: str, query_type: QueryType) -> List[str]:
        """Generate optimized search queries based on the query type."""
        base_query = query.strip()
        queries = [base_query]
        
        if query_type == QueryType.ACADEMIC:
            # Academic-focused query variations
            queries.extend([
                f"{base_query} academic research",
                f"{base_query} scholarly article",
                f"{base_query} study paper",
                f'"{base_query}" research',
                f"{base_query} site:arxiv.org OR site:scholar.google.com"
            ])
        
        elif query_type == QueryType.NEWS:
            # News-focused query variations
            queries.extend([
                f"{base_query} news",
                f"{base_query} latest",
                f"{base_query} recent",
                f'"{base_query}" breaking',
                f"{base_query} site:reuters.com OR site:bbc.com OR site:cnn.com"
            ])
        
        elif query_type == QueryType.COMPARATIVE:
            # Comparative analysis queries
            queries.extend([
                f"{base_query} comparison",
                f"{base_query} vs versus",
                f"{base_query} analysis",
                f"{base_query} review",
                f'"{base_query}" pros cons'
            ])
        
        return queries[:3]  # Limit to top 3 variations
    
    async def _search_google_scholar(self, query: str, max_results: int) -> List[URLCandidate]:
        """Search Google Scholar for academic sources."""
        candidates = []
        
        try:
            # Note: In a production environment, you'd want to use the official Google Scholar API
            # or a service like Serpapi. This is a simplified approach.
            
            search_url = f"https://scholar.google.com/scholar?q={quote_plus(query)}&num={max_results}"
            
            if self.session:
                async with self.session.get(search_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        candidates = self._parse_google_scholar_results(html)
                        
        except Exception as e:
            logger.error(f"Google Scholar search failed: {e}")
            
        return candidates
    
    async def _search_google(self, query: str, max_results: int, query_type: QueryType) -> List[URLCandidate]:
        """Search Google for general sources."""
        candidates = []
        
        try:
            # Add query type specific modifiers
            if query_type == QueryType.ACADEMIC:
                query += " academic research paper"
            elif query_type == QueryType.NEWS:
                query += " news article"
                
            # Note: In production, use Google Custom Search API
            # This is a placeholder for the search implementation
            logger.info(f"Would search Google for: {query}")
            
            # Placeholder results - replace with actual API implementation
            candidates = self._generate_placeholder_candidates(query, "google", max_results)
            
        except Exception as e:
            logger.error(f"Google search failed: {e}")
            
        return candidates
    
    async def _search_bing(self, query: str, max_results: int, query_type: QueryType) -> List[URLCandidate]:
        """Search Bing for additional sources."""
        candidates = []
        
        try:
            # Note: In production, use Bing Search API
            logger.info(f"Would search Bing for: {query}")
            
            # Placeholder results - replace with actual API implementation
            candidates = self._generate_placeholder_candidates(query, "bing", max_results)
            
        except Exception as e:
            logger.error(f"Bing search failed: {e}")
            
        return candidates
    
    async def _search_domain_specific(self, query: str, domain: str, max_results: int) -> List[URLCandidate]:
        """Search within a specific domain."""
        candidates = []
        
        try:
            # Use site: operator for domain-specific search
            domain_query = f"site:{domain} {query}"
            logger.info(f"Domain-specific search: {domain_query}")
            
            # Placeholder implementation
            candidates = self._generate_placeholder_candidates(domain_query, domain, max_results)
            
        except Exception as e:
            logger.error(f"Domain-specific search failed for {domain}: {e}")
            
        return candidates
    
    def _parse_google_scholar_results(self, html: str) -> List[URLCandidate]:
        """Parse Google Scholar search results."""
        candidates = []
        
        # Simplified parsing - in production, use proper HTML parsing
        # This is a placeholder implementation
        
        return candidates
    
    def _generate_placeholder_candidates(self, query: str, source: str, max_results: int) -> List[URLCandidate]:
        """Generate placeholder candidates for testing purposes."""
        candidates = []
        
        # Placeholder URLs based on query type and source
        if "academic" in query.lower() or source == "google_scholar":
            base_urls = [
                "https://arxiv.org/abs/2301.00000",
                "https://pubmed.ncbi.nlm.nih.gov/12345678/",
                "https://ieeexplore.ieee.org/document/9999999",
                "https://dl.acm.org/doi/10.1145/1234567",
                "https://www.nature.com/articles/s41586-023-05678-1"
            ]
            source_type = SourceType.ACADEMIC_PAPER
        elif "news" in query.lower():
            base_urls = [
                "https://www.reuters.com/article/example-news",
                "https://www.bbc.com/news/world-12345678",
                "https://edition.cnn.com/2024/01/01/world/example",
                "https://www.theguardian.com/world/2024/jan/01/example",
                "https://www.npr.org/2024/01/01/1234567890/example"
            ]
            source_type = SourceType.NEWS_ARTICLE
        else:
            base_urls = [
                "https://en.wikipedia.org/wiki/Example_Article",
                "https://medium.com/@author/example-post",
                "https://stackoverflow.com/questions/12345678/example",
                "https://github.com/user/repo/blob/main/README.md",
                "https://docs.example.com/guide/topic"
            ]
            source_type = SourceType.WEBSITE
        
        for i, url in enumerate(base_urls[:max_results]):
            domain = urlparse(url).netloc
            candidates.append(URLCandidate(
                url=url,
                title=f"Example {source.title()} Result {i+1} for: {query}",
                snippet=f"This is a sample snippet for result {i+1} from {source}...",
                source_type=source_type,
                domain=domain,
                relevance_score=0.9 - (i * 0.1),  # Decreasing relevance
                discovery_source=source,
                estimated_quality=0.8 + (i % 3) * 0.05,  # Varying quality
                language="en",
                date_published=datetime.now() - timedelta(days=i*30)
            ))
        
        return candidates
    
    def _filter_candidates(self, 
                          candidates: List[URLCandidate],
                          include_domains: Optional[List[str]],
                          exclude_domains: Optional[List[str]]) -> List[URLCandidate]:
        """Filter candidates based on domain restrictions."""
        filtered = []
        seen_urls = set()
        
        for candidate in candidates:
            # Skip duplicates
            if candidate.url in seen_urls:
                continue
            seen_urls.add(candidate.url)
            
            # Validate URL
            if not validators.url(candidate.url):
                continue
            
            # Apply domain filters
            if exclude_domains and any(domain in candidate.domain for domain in exclude_domains):
                continue
                
            if include_domains and not any(domain in candidate.domain for domain in include_domains):
                continue
            
            filtered.append(candidate)
        
        return filtered
    
    def _prioritize_candidates(self, 
                              candidates: List[URLCandidate],
                              query: str,
                              query_type: QueryType) -> List[URLCandidate]:
        """Prioritize candidates based on relevance and quality."""
        
        # Calculate priority scores
        for candidate in candidates:
            priority_score = self._calculate_priority_score(candidate, query, query_type)
            candidate.relevance_score = priority_score
        
        # Sort by priority score (descending)
        return sorted(candidates, key=lambda x: x.relevance_score, reverse=True)
    
    def _calculate_priority_score(self, 
                                 candidate: URLCandidate,
                                 query: str,
                                 query_type: QueryType) -> float:
        """Calculate a priority score for a candidate URL."""
        score = candidate.relevance_score * 0.4  # Base relevance
        score += candidate.estimated_quality * 0.3  # Quality boost
        
        # Domain authority bonus
        if candidate.domain in ScrapingTargets.ACADEMIC_SITES:
            score += 0.2 if query_type == QueryType.ACADEMIC else 0.1
        elif candidate.domain in ScrapingTargets.NEWS_SITES:
            score += 0.2 if query_type == QueryType.NEWS else 0.1
        
        # Source type alignment bonus
        if query_type == QueryType.ACADEMIC and candidate.source_type == SourceType.ACADEMIC_PAPER:
            score += 0.15
        elif query_type == QueryType.NEWS and candidate.source_type == SourceType.NEWS_ARTICLE:
            score += 0.15
        
        # Recency bonus for news content
        if candidate.date_published and query_type == QueryType.NEWS:
            days_old = (datetime.now() - candidate.date_published).days
            if days_old < 7:
                score += 0.1
            elif days_old < 30:
                score += 0.05
        
        # Penalize very old content for certain query types
        if candidate.date_published and query_type == QueryType.NEWS:
            days_old = (datetime.now() - candidate.date_published).days
            if days_old > 365:
                score -= 0.2
        
        return min(score, 1.0)  # Cap at 1.0