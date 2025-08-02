"""
Agents module for Scholarly Clone.
Contains specialized agents for URL discovery and web scraping.
"""

from .crawl4ai_agent import ScholaryCrawl4AIAgent
from .url_discovery import URLDiscoveryAgent, URLCandidate

__all__ = ["ScholaryCrawl4AIAgent", "URLDiscoveryAgent", "URLCandidate"]