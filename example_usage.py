#!/usr/bin/env python3
"""
Example usage script for Scholarly Clone API.
Demonstrates how to use the platform programmatically.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add the scholarly_clone package to Python path
sys.path.insert(0, str(Path(__file__).parent))

from scholarly_clone.core.research_orchestrator import ResearchOrchestrator
from scholarly_clone.models.schemas import ResearchQuery, QueryType


async def example_research_query():
    """Example of conducting research using the orchestrator directly."""
    print("🔬 Scholarly Clone - Example Usage")
    print("=" * 50)
    
    # Create a research query
    query = ResearchQuery(
        query="What are the latest developments in quantum computing?",
        query_type=QueryType.ACADEMIC,
        max_results=5,
        language="en"
    )
    
    print(f"Query: {query.query}")
    print(f"Type: {query.query_type}")
    print(f"Max Results: {query.max_results}")
    print()
    
    # Conduct research using the orchestrator
    async with ResearchOrchestrator() as orchestrator:
        print("🚀 Starting research...")
        response = await orchestrator.conduct_research(query)
        
        print(f"✅ Research completed in {response.processing_time:.2f} seconds")
        print(f"📊 Sources found: {response.total_sources_found}")
        print(f"📝 Sources processed: {response.sources_processed}")
        print(f"🎯 Confidence score: {response.confidence_score:.2%}")
        print()
        
        # Display overall summary
        print("📋 Overall Summary:")
        print("-" * 20)
        print(response.overall_summary)
        print()
        
        # Display key findings
        if response.key_findings:
            print("🔑 Key Findings:")
            print("-" * 15)
            for i, finding in enumerate(response.key_findings, 1):
                print(f"{i}. {finding}")
            print()
        
        # Display related topics
        if response.related_topics:
            print("🔗 Related Topics:")
            print("-" * 16)
            print(", ".join(response.related_topics))
            print()
        
        # Display source details
        print("📚 Sources:")
        print("-" * 10)
        for i, source in enumerate(response.sources, 1):
            print(f"\n{i}. {source.title}")
            print(f"   URL: {source.url}")
            print(f"   Type: {source.source_type}")
            print(f"   Summary: {source.summary[:200]}...")
            print(f"   Citations: {len(source.citations)}")
            print(f"   Insights: {len(source.insights)}")
            print(f"   Processing time: {source.processing_time:.2f}s")
        
        return response


async def example_url_discovery():
    """Example of URL discovery functionality."""
    print("\n🔍 URL Discovery Example")
    print("=" * 30)
    
    async with ResearchOrchestrator() as orchestrator:
        urls = await orchestrator.url_discovery_agent.discover_urls(
            query="artificial intelligence ethics",
            query_type=QueryType.ACADEMIC,
            max_results=10
        )
        
        print(f"Found {len(urls)} URL candidates:")
        for i, url_candidate in enumerate(urls, 1):
            print(f"\n{i}. {url_candidate.title}")
            print(f"   URL: {url_candidate.url}")
            print(f"   Relevance: {url_candidate.relevance_score:.2f}")
            print(f"   Quality: {url_candidate.estimated_quality:.2f}")
            print(f"   Source: {url_candidate.discovery_source}")
            print(f"   Type: {url_candidate.source_type}")


async def example_api_usage():
    """Example of using the API client approach."""
    print("\n🌐 API Client Example")
    print("=" * 25)
    
    # This would be used with the running API server
    import aiohttp
    
    api_url = "http://localhost:8000"
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test health endpoint
            async with session.get(f"{api_url}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"✅ API Health: {health_data['status']}")
                else:
                    print(f"❌ API Health Check Failed: {response.status}")
                    return
            
            # Example research request
            research_data = {
                "query": "climate change impacts",
                "query_type": "news",
                "max_results": 3,
                "language": "en"
            }
            
            async with session.post(f"{api_url}/research", json=research_data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ API Research completed: {result['sources_processed']} sources")
                    print(f"📊 Confidence: {result['confidence_score']:.2%}")
                else:
                    print(f"❌ API Research Failed: {response.status}")
                    
    except aiohttp.ClientConnectorError:
        print("❌ Could not connect to API. Make sure the server is running:")
        print("   python main.py")


def save_example_results(response):
    """Save example results to a JSON file."""
    output_file = "example_results.json"
    
    # Convert response to dict for JSON serialization
    result_dict = response.dict()
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result_dict, f, indent=2, default=str)
    
    print(f"💾 Results saved to {output_file}")


async def main():
    """Main example execution function."""
    try:
        print("Starting Scholarly Clone examples...\n")
        
        # Example 1: Direct research orchestrator usage
        response = await example_research_query()
        
        # Example 2: URL discovery
        await example_url_discovery()
        
        # Example 3: API usage (requires running server)
        await example_api_usage()
        
        # Save results
        save_example_results(response)
        
        print("\n🎉 All examples completed successfully!")
        print("\nTo explore more:")
        print("- Start the server: python main.py")
        print("- Visit frontend: http://localhost:8000/frontend/")
        print("- Check API docs: http://localhost:8000/docs")
        
    except Exception as e:
        print(f"❌ Example failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())