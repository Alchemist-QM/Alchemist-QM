"""
API module for Scholarly Clone.
Contains FastAPI endpoints and route definitions.
"""

from .endpoints import app, run_server

__all__ = ["app", "run_server"]