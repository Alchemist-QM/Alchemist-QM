"""
LangChain Processing Pipeline for Scholarly Clone.
Handles content summarization, citation extraction, and insight generation.
"""

import asyncio
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import MapReduceDocumentsChain, ReduceDocumentsChain
from langchain.chains.llm import LLMChain
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.prompts import PromptTemplate
from langchain.schema import Document

from loguru import logger
from ..core.config import settings
from ..models.schemas import Citation, ExtractedInsight, SourceType, QueryType


class LangChainProcessor:
    """
    Advanced LangChain pipeline for processing scraped content.
    Handles summarization, citation extraction, and insight generation.
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            temperature=0.1,  # Low temperature for consistent, factual outputs
            model_name="gpt-4",  # Use GPT-4 for better reasoning
            openai_api_key=settings.openai_api_key,
            max_tokens=2000
        )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=4000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ". ", ".", " ", ""]
        )
        
        # Initialize processing chains
        self._setup_chains()
    
    def _setup_chains(self):
        """Set up the various LangChain processing chains."""
        
        # Summarization chain
        self.summary_prompt = PromptTemplate(
            input_variables=["text", "query"],
            template="""
            You are an expert research assistant. Summarize the following content in relation to the research query: "{query}"

            Content:
            {text}

            Provide a comprehensive but concise summary that:
            1. Captures the main points relevant to the research query
            2. Maintains academic rigor and accuracy
            3. Highlights key findings, arguments, or insights
            4. Is approximately 150-300 words

            Summary:
            """
        )
        
        self.summary_chain = LLMChain(
            llm=self.llm,
            prompt=self.summary_prompt
        )
        
        # Citation extraction chain
        self.citation_prompt = PromptTemplate(
            input_variables=["text"],
            template="""
            Extract all citations, references, and quoted sources from the following text.
            
            Text:
            {text}
            
            For each citation found, provide:
            1. The exact citation text
            2. The surrounding context (1-2 sentences)
            3. The type of citation (author-date, numeric, footnote, etc.)
            4. A confidence score (0.0-1.0) for the extraction accuracy
            
            Format your response as JSON:
            [
                {{
                    "text": "citation text here",
                    "context": "surrounding context here",
                    "citation_type": "type here",
                    "confidence": 0.95
                }}
            ]
            
            If no citations are found, return an empty array: []
            """
        )
        
        self.citation_chain = LLMChain(
            llm=self.llm,
            prompt=self.citation_prompt
        )
        
        # Insight extraction chain
        self.insight_prompt = PromptTemplate(
            input_variables=["text", "query"],
            template="""
            Analyze the following content and extract key insights relevant to the research query: "{query}"
            
            Content:
            {text}
            
            Extract insights that are:
            1. Directly relevant to the research query
            2. Supported by evidence in the text
            3. Novel or particularly important findings
            4. Actionable or meaningful for research purposes
            
            For each insight, provide:
            - The insight itself (clear, concise statement)
            - Relevance score to the query (0.0-1.0)
            - Supporting evidence from the text
            - Category (methodology, findings, implications, etc.)
            
            Format as JSON:
            [
                {{
                    "insight": "insight statement here",
                    "relevance_score": 0.85,
                    "supporting_evidence": ["evidence 1", "evidence 2"],
                    "category": "findings"
                }}
            ]
            
            Limit to the top 5 most relevant insights.
            """
        )
        
        self.insight_chain = LLMChain(
            llm=self.llm,
            prompt=self.insight_prompt
        )
        
        # Quality assessment chain
        self.quality_prompt = PromptTemplate(
            input_variables=["text", "source_type"],
            template="""
            Assess the quality and credibility of this {source_type} content:
            
            {text}
            
            Evaluate based on:
            1. Factual accuracy and evidence quality
            2. Source credibility and authoritativeness  
            3. Methodological rigor (for research content)
            4. Clarity and coherence
            5. Bias and objectivity
            
            Provide a quality score from 0.0-1.0 and brief justification.
            
            Format as JSON:
            {{
                "quality_score": 0.85,
                "justification": "explanation here",
                "strengths": ["strength 1", "strength 2"],
                "weaknesses": ["weakness 1", "weakness 2"]
            }}
            """
        )
        
        self.quality_chain = LLMChain(
            llm=self.llm,
            prompt=self.quality_prompt
        )
    
    async def process_content(self, 
                             content: str, 
                             query: str,
                             source_url: str,
                             source_type: SourceType = SourceType.WEBSITE) -> Dict[str, Any]:
        """
        Process scraped content through the full LangChain pipeline.
        
        Args:
            content: Raw scraped content
            query: Original research query
            source_url: URL of the content source
            source_type: Type of source content
            
        Returns:
            Dictionary containing processed results
        """
        logger.info(f"Processing content from {source_url} with LangChain pipeline")
        
        start_time = datetime.now()
        
        # Clean and prepare content
        cleaned_content = self._clean_content(content)
        
        if len(cleaned_content.strip()) < 100:
            logger.warning(f"Content too short for processing: {source_url}")
            return self._create_empty_result(source_url, "Content too short")
        
        try:
            # Process in parallel for efficiency
            tasks = [
                self._generate_summary(cleaned_content, query),
                self._extract_citations(cleaned_content),
                self._extract_insights(cleaned_content, query),
                self._assess_quality(cleaned_content, source_type.value)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            summary, citations, insights, quality = results
            
            # Handle any exceptions
            if isinstance(summary, Exception):
                logger.error(f"Summary generation failed: {summary}")
                summary = "Summary generation failed"
            
            if isinstance(citations, Exception):
                logger.error(f"Citation extraction failed: {citations}")
                citations = []
            
            if isinstance(insights, Exception):
                logger.error(f"Insight extraction failed: {insights}")
                insights = []
            
            if isinstance(quality, Exception):
                logger.error(f"Quality assessment failed: {quality}")
                quality = {"quality_score": 0.5, "justification": "Assessment failed"}
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "summary": summary,
                "citations": citations,
                "insights": insights,
                "quality_assessment": quality,
                "processing_time": processing_time,
                "content_length": len(cleaned_content),
                "success": True,
                "error": None
            }
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Content processing failed for {source_url}: {e}")
            return self._create_empty_result(source_url, str(e), processing_time)
    
    async def _generate_summary(self, content: str, query: str) -> str:
        """Generate a summary using LangChain."""
        try:
            # Split content if it's too long
            if len(content) > 8000:
                chunks = self.text_splitter.split_text(content)
                # Use map-reduce for long content
                summaries = []
                for chunk in chunks[:5]:  # Limit to first 5 chunks
                    chunk_summary = await self.summary_chain.arun(
                        text=chunk, 
                        query=query
                    )
                    summaries.append(chunk_summary)
                
                # Combine summaries
                combined_summary = "\n\n".join(summaries)
                if len(combined_summary) > 2000:
                    # Final reduction
                    final_summary = await self.summary_chain.arun(
                        text=combined_summary,
                        query=query
                    )
                    return final_summary
                else:
                    return combined_summary
            else:
                return await self.summary_chain.arun(text=content, query=query)
                
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return f"Summary generation failed: {str(e)}"
    
    async def _extract_citations(self, content: str) -> List[Citation]:
        """Extract citations using LangChain."""
        try:
            # Split content for citation extraction
            chunks = self.text_splitter.split_text(content)
            all_citations = []
            
            for chunk in chunks:
                citation_result = await self.citation_chain.arun(text=chunk)
                
                try:
                    import json
                    citation_data = json.loads(citation_result)
                    
                    for citation_dict in citation_data:
                        citation = Citation(
                            text=citation_dict.get("text", ""),
                            context=citation_dict.get("context", ""),
                            confidence=float(citation_dict.get("confidence", 0.5)),
                            citation_type=citation_dict.get("citation_type")
                        )
                        all_citations.append(citation)
                        
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Failed to parse citation JSON: {e}")
                    continue
            
            # Deduplicate citations
            unique_citations = []
            seen_texts = set()
            
            for citation in all_citations:
                if citation.text not in seen_texts and len(citation.text.strip()) > 10:
                    seen_texts.add(citation.text)
                    unique_citations.append(citation)
            
            return unique_citations[:10]  # Limit to top 10 citations
            
        except Exception as e:
            logger.error(f"Citation extraction failed: {e}")
            return []
    
    async def _extract_insights(self, content: str, query: str) -> List[ExtractedInsight]:
        """Extract insights using LangChain."""
        try:
            # Use first chunk if content is too long
            if len(content) > 8000:
                chunks = self.text_splitter.split_text(content)
                content = chunks[0]  # Focus on first chunk for insights
            
            insight_result = await self.insight_chain.arun(text=content, query=query)
            
            try:
                import json
                insight_data = json.loads(insight_result)
                
                insights = []
                for insight_dict in insight_data:
                    insight = ExtractedInsight(
                        insight=insight_dict.get("insight", ""),
                        relevance_score=float(insight_dict.get("relevance_score", 0.5)),
                        supporting_evidence=insight_dict.get("supporting_evidence", []),
                        category=insight_dict.get("category")
                    )
                    insights.append(insight)
                
                return insights
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse insight JSON: {e}")
                return []
                
        except Exception as e:
            logger.error(f"Insight extraction failed: {e}")
            return []
    
    async def _assess_quality(self, content: str, source_type: str) -> Dict[str, Any]:
        """Assess content quality using LangChain."""
        try:
            # Use first chunk for quality assessment
            if len(content) > 4000:
                chunks = self.text_splitter.split_text(content)
                content = chunks[0]
            
            quality_result = await self.quality_chain.arun(
                text=content, 
                source_type=source_type
            )
            
            try:
                import json
                return json.loads(quality_result)
            except (json.JSONDecodeError, ValueError):
                return {
                    "quality_score": 0.5,
                    "justification": "Quality assessment parsing failed",
                    "strengths": [],
                    "weaknesses": ["Assessment parsing failed"]
                }
                
        except Exception as e:
            logger.error(f"Quality assessment failed: {e}")
            return {
                "quality_score": 0.5,
                "justification": f"Quality assessment failed: {str(e)}",
                "strengths": [],
                "weaknesses": ["Assessment failed"]
            }
    
    def _clean_content(self, content: str) -> str:
        """Clean and preprocess content for LangChain processing."""
        if not content:
            return ""
        
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove common web artifacts
        content = re.sub(r'Cookie\s+Policy|Privacy\s+Policy|Terms\s+of\s+Service', '', content, flags=re.IGNORECASE)
        
        # Remove navigation elements
        content = re.sub(r'Home\s+\|\s+About\s+\|\s+Contact', '', content, flags=re.IGNORECASE)
        
        # Remove excessive punctuation
        content = re.sub(r'[.]{3,}', '...', content)
        
        # Remove email addresses and URLs from content for cleaner processing
        content = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', content)
        content = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '[URL]', content)
        
        return content.strip()
    
    def _create_empty_result(self, source_url: str, error: str, processing_time: float = 0.0) -> Dict[str, Any]:
        """Create an empty result for failed processing."""
        return {
            "summary": "",
            "citations": [],
            "insights": [],
            "quality_assessment": {
                "quality_score": 0.0,
                "justification": f"Processing failed: {error}",
                "strengths": [],
                "weaknesses": ["Processing failed"]
            },
            "processing_time": processing_time,
            "content_length": 0,
            "success": False,
            "error": error
        }
    
    async def process_multiple_contents(self, 
                                      contents: List[Dict[str, Any]], 
                                      query: str) -> List[Dict[str, Any]]:
        """Process multiple content pieces concurrently."""
        logger.info(f"Processing {len(contents)} content pieces with LangChain")
        
        tasks = []
        for content_data in contents:
            task = self.process_content(
                content=content_data.get("content", ""),
                query=query,
                source_url=content_data.get("url", ""),
                source_type=SourceType(content_data.get("source_type", "website"))
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Content processing failed for item {i}: {result}")
                processed_results.append(
                    self._create_empty_result(
                        contents[i].get("url", "unknown"), 
                        str(result)
                    )
                )
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def generate_overall_summary(self, 
                                     summaries: List[str], 
                                     query: str) -> str:
        """Generate an overall summary from individual summaries."""
        if not summaries:
            return "No content available for summary generation."
        
        combined_content = "\n\n".join(summaries)
        
        overall_prompt = f"""
        Based on the following individual summaries of research sources, create a comprehensive overall summary that addresses the research query: "{query}"
        
        Individual Summaries:
        {combined_content}
        
        Provide a coherent, well-structured overall summary that:
        1. Synthesizes information from all sources
        2. Identifies common themes and patterns
        3. Highlights contradictions or different perspectives
        4. Addresses the original research query comprehensively
        5. Is approximately 300-500 words
        
        Overall Summary:
        """
        
        try:
            messages = [
                SystemMessage(content="You are an expert research analyst capable of synthesizing information from multiple sources."),
                HumanMessage(content=overall_prompt)
            ]
            
            response = await self.llm.agenerate([messages])
            return response.generations[0][0].text.strip()
            
        except Exception as e:
            logger.error(f"Overall summary generation failed: {e}")
            return f"Overall summary generation failed: {str(e)}"