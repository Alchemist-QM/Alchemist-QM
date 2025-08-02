# 🔬 Scholarly Clone

A powerful research-focused web scraping and summarization platform that leverages Crawl4AI and LangChain to provide comprehensive research capabilities similar to Scholarly.so.

## 🏗️ Architecture

The platform follows a sophisticated pipeline architecture:

```
User Query
    ↓
URL Discovery + Prioritization
    ↓
Playwright Scraper (Crawl4AI)
    ↓
Raw Text Content
    ↓
LangChain Processing Pipeline:
    • Content Summarization
    • Citation Extraction  
    • Insight Generation
    • Quality Assessment
    ↓
Formatted JSON Response
```

## ✨ Features

- **🔍 Intelligent URL Discovery**: Multi-source URL discovery with domain-specific prioritization
- **🌐 Advanced Web Scraping**: Crawl4AI integration with Playwright for JS-heavy sites
- **🤖 AI-Powered Analysis**: LangChain pipeline for summarization and insights
- **📚 Citation Extraction**: Automatic extraction and validation of citations
- **🎯 Research-Focused**: Optimized for academic papers, news articles, and research content
- **⚡ Concurrent Processing**: Parallel scraping and processing for efficiency
- **🎨 Modern Web Interface**: Beautiful, responsive frontend for easy interaction
- **📊 Quality Assessment**: AI-driven content quality scoring
- **🔧 Configurable**: Extensive configuration options for different use cases

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API Key
- Git

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd scholarly-clone
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Install Playwright browsers**
```bash
playwright install
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your OpenAI API key and other settings
```

5. **Run the application**
```bash
python main.py
```

The application will be available at:
- **API**: http://localhost:8000
- **Frontend**: http://localhost:8000/frontend/
- **API Documentation**: http://localhost:8000/docs

## 📋 Environment Configuration

Create a `.env` file based on `.env.example`:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration
DATABASE_URL=sqlite:///./scholarly_clone.db

# Redis Configuration (optional)
REDIS_URL=redis://localhost:6379

# Web Scraping Configuration
USER_AGENT=ScholaryClone/1.0
MAX_CONCURRENT_REQUESTS=5
REQUEST_DELAY=1

# Application Configuration
DEBUG=true
LOG_LEVEL=INFO
MAX_PAGES_PER_QUERY=10
```

## 🔧 API Usage

### Research Endpoint

**POST** `/research`

Conduct comprehensive research on a given query.

```python
import requests

response = requests.post("http://localhost:8000/research", json={
    "query": "What are the latest developments in quantum computing?",
    "query_type": "academic",
    "max_results": 10,
    "language": "en"
})

result = response.json()
print(f"Found {len(result['sources'])} sources")
print(f"Summary: {result['overall_summary']}")
```

### URL Discovery

**POST** `/discover-urls`

Discover relevant URLs for a research query.

```python
response = requests.post("http://localhost:8000/discover-urls", json={
    "query": "machine learning research",
    "max_urls": 20,
    "source_types": ["academic_paper", "website"]
})
```

### Single URL Scraping

**POST** `/scrape-url`

Scrape a single URL for testing.

```python
response = requests.post("http://localhost:8000/scrape-url", json={
    "url": "https://arxiv.org/abs/2301.00000",
    "extraction_strategy": "academic"
})
```

## 📊 Response Format

The main research endpoint returns a comprehensive JSON response:

```json
{
    "query": "quantum computing developments",
    "query_type": "academic",
    "sources": [
        {
            "url": "https://example.com/paper",
            "title": "Quantum Computing Advances",
            "summary": "This paper discusses...",
            "source_type": "academic_paper",
            "citations": [
                {
                    "text": "Smith et al. (2023)",
                    "context": "Recent work by Smith...",
                    "confidence": 0.95
                }
            ],
            "insights": [
                {
                    "insight": "Key finding about quantum algorithms",
                    "relevance_score": 0.89,
                    "supporting_evidence": ["Evidence from the paper"]
                }
            ],
            "processing_time": 2.3
        }
    ],
    "overall_summary": "Comprehensive summary across all sources...",
    "key_findings": ["Finding 1", "Finding 2"],
    "related_topics": ["quantum algorithms", "quantum hardware"],
    "confidence_score": 0.87,
    "total_sources_found": 15,
    "sources_processed": 10,
    "processing_time": 45.2
}
```

## 🏗️ Project Structure

```
scholarly_clone/
├── __init__.py                 # Package initialization
├── core/                       # Core application logic
│   ├── config.py              # Configuration management
│   └── research_orchestrator.py # Main orchestration logic
├── agents/                     # Specialized agents
│   ├── crawl4ai_agent.py      # Custom Crawl4AI integration
│   └── url_discovery.py       # URL discovery and prioritization
├── pipeline/                   # Processing pipeline
│   └── langchain_processor.py  # LangChain content processing
├── models/                     # Data models
│   └── schemas.py             # Pydantic models
├── api/                        # FastAPI endpoints
│   └── endpoints.py           # API route definitions
├── frontend/                   # Web interface
│   └── index.html             # Frontend application
├── utils/                      # Utility functions
├── tests/                      # Test suite
└── crawl4ai/                   # Crawl4AI submodule
```

## 🔧 Configuration Options

### Query Types

- **`general`**: General web research
- **`academic`**: Academic papers and research
- **`news`**: News articles and current events
- **`comparative`**: Comparative analysis

### Source Types

- **`academic_paper`**: Scholarly articles and papers
- **`news_article`**: News and journalism
- **`blog_post`**: Blog posts and opinions
- **`website`**: General web content
- **`documentation`**: Technical documentation

### Extraction Strategies

- **`academic`**: Optimized for research papers
- **`news`**: Optimized for news content
- **`general`**: General content extraction

## 🧪 Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black scholarly_clone/
isort scholarly_clone/
```

### Development Mode

```bash
python main.py --reload
```

## 📈 Performance Optimization

### Concurrent Processing

The platform uses asyncio for concurrent URL scraping and content processing:

- Configurable concurrent request limits
- Rate limiting for respectful scraping
- Parallel LangChain processing

### Caching

- Redis support for caching scraped content
- Intelligent URL deduplication
- Response caching for repeated queries

### Resource Management

- Automatic cleanup of browser instances
- Memory-efficient text processing
- Configurable timeout settings

## 🔒 Security Considerations

- Input validation and sanitization
- Rate limiting on API endpoints
- Secure handling of API keys
- Content filtering for malicious sites

## 📚 Advanced Usage

### Custom Extraction Strategies

```python
from scholarly_clone.agents.crawl4ai_agent import ScholaryCrawl4AIAgent

agent = ScholaryCrawl4AIAgent()
result = await agent.scrape_url(
    url="https://example.com",
    extraction_strategy="academic",
    custom_js="// Custom JavaScript for site-specific processing"
)
```

### Batch Processing

```python
from scholarly_clone.core.research_orchestrator import ResearchOrchestrator

async with ResearchOrchestrator() as orchestrator:
    queries = [
        ResearchQuery(query="AI ethics", query_type="academic"),
        ResearchQuery(query="climate change", query_type="news")
    ]
    
    results = []
    for query in queries:
        result = await orchestrator.conduct_research(query)
        results.append(result)
```

## 🛠️ Troubleshooting

### Common Issues

1. **Playwright Installation**
   ```bash
   playwright install chromium
   ```

2. **OpenAI API Errors**
   - Verify API key is set correctly
   - Check API usage limits
   - Ensure sufficient credits

3. **Memory Issues**
   - Reduce `MAX_CONCURRENT_REQUESTS`
   - Increase system memory
   - Enable content caching

4. **Slow Performance**
   - Check network connectivity
   - Reduce `max_results` parameter
   - Use specific domain filtering

### Logs

Check application logs for detailed error information:
```bash
tail -f scholarly_clone.log
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Crawl4AI**: For the excellent web scraping framework
- **LangChain**: For the powerful NLP processing capabilities
- **FastAPI**: For the robust API framework
- **Playwright**: For reliable browser automation

## 📞 Support

For questions, issues, or contributions:

- Create an issue on GitHub
- Check the documentation at `/docs`
- Review the API reference at `/redoc`

---

**Built with ❤️ for the research community**
