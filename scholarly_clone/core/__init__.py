"""
Core module for Scholarly Clone.
Contains configuration, orchestration, and main application logic.
"""

from .config import settings, ScrapingTargets
from .research_orchestrator import ResearchOrchestrator

__all__ = ["settings", "ScrapingTargets", "ResearchOrchestrator"]