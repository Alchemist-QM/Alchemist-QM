#!/usr/bin/env python3
"""
Main entry point for Scholarly Clone application.
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add the scholarly_clone package to Python path
sys.path.insert(0, str(Path(__file__).parent))

from scholarly_clone.api.endpoints import run_server
from scholarly_clone.core.config import settings
from scholarly_clone import __version__

def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description=f"Scholarly Clone v{__version__} - Research-focused web scraping and summarization platform"
    )
    
    parser.add_argument(
        "--host", 
        default="0.0.0.0", 
        help="Host to bind the server to (default: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="Port to bind the server to (default: 8000)"
    )
    
    parser.add_argument(
        "--reload", 
        action="store_true", 
        help="Enable auto-reload for development"
    )
    
    parser.add_argument(
        "--no-reload", 
        action="store_true", 
        help="Disable auto-reload (production mode)"
    )
    
    parser.add_argument(
        "--version", 
        action="version", 
        version=f"Scholarly Clone {__version__}"
    )
    
    args = parser.parse_args()
    
    # Determine reload setting
    if args.no_reload:
        reload = False
    elif args.reload:
        reload = True
    else:
        reload = settings.debug  # Default to debug setting
    
    print(f"""
🔬 Scholarly Clone v{__version__}
=====================================

Starting research platform...

🌐 API Server: http://{args.host}:{args.port}
📚 API Docs: http://{args.host}:{args.port}/docs
🎨 Frontend: http://{args.host}:{args.port}/frontend/
🔧 Debug Mode: {settings.debug}
🔄 Auto-reload: {reload}

Architecture:
User Query → URL Discovery → Crawl4AI Scraping → LangChain Processing → JSON Response

Ready to conduct research! 🚀
    """)
    
    try:
        run_server(host=args.host, port=args.port, reload=reload)
    except KeyboardInterrupt:
        print("\n👋 Shutting down Scholarly Clone. Goodbye!")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()