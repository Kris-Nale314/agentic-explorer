# analysis.py
"""
Core data processing pipeline for RAG Showdown.
"""

import logging
import time
import json
from typing import Dict, Any, List, Optional

# Import processors
from processors.document import DocumentAnalyzer
from processors.chunking import ChunkingProcessor
from processors.embedding import EmbeddingProcessor
from processors.index import IndexProcessor
from processors.retrieval import RetrievalProcessor
from processors.synthesis import SynthesisProcessor
from utils.openai_client import OpenAIClient
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AnalysisPipeline:
    """Core analysis pipeline for RAG Showdown."""
    
    def __init__(self):
        """Initialize the analysis pipeline with all processors."""
        self.document_analyzer = DocumentAnalyzer()
        self.chunking_processor = ChunkingProcessor()
        self.embedding_processor = EmbeddingProcessor()
        self.index_processor = IndexProcessor()
        self.retrieval_processor = RetrievalProcessor()
        self.synthesis_processor = SynthesisProcessor()
        self.openai_client = OpenAIClient()
        
        logger.info("Initialized RAG Showdown analysis pipeline")
    
    def analyze_document(self, document_text: str) -> Dict[str, Any]:
        """
        Analyze document text and compute basic metrics.
        
        Args:
            document_text: Document text to analyze
            
        Returns:
            Dict with document metrics and analysis
        """
        logger.info(f"Analyzing document ({len(document_text)} chars)")
        start_time = time.time()
        
        # Compute basic metrics
        metrics = self.document_analyzer.compute_basic_metrics(document_text)
        
        # Detect document boundaries
        boundaries = self.document_analyzer.analyze_document_boundaries(document_text)
        
        # Generate summary
        summary = self.document_analyzer.generate_summary(document_text)
        
        processing_time = time.time() - start_time
        
        return {
            "document_length": len(document_text),
            "metrics": metrics,
            "boundaries": boundaries,
            "summary": summary,
            "processing_time": processing_time, 
            "start_time": start_time
        }
    
    def compare_chunking_strategies(self, document_text: str) -> Dict[str, Any]:
        """
        Compare different chunking strategies on the document.
        
        Args:
            document_text: Document text to chunk
            
        Returns:
            Dict with chunking comparison results
        """
        logger.info(f"Comparing chunking strategies for document ({len(document_text)} chars)")
        start_time = time.time()
        
        # Run chunking comparison
        comparison = self.chunking_processor.compare_chunking_strategies(
            text=document_text,
            strategies=[
                {"name": "Traditional Fixed-Size", "strategy": "fixed_size"},
                {"name": "Boundary-Aware", "strategy": "boundary_aware"},
                {"name": "Semantic", "strategy": "semantic"}
            ]
        )
        
        processing_time = time.time() - start_time
        
        return {
            "chunking_comparison": comparison,
            "processing_time": processing_time
        }
    
    def build_retrieval_indices(self, 
                              document_text: str, 
                              chunking_strategies: List[str] = None) -> Dict[str, Any]:
        """
        Build retrieval indices for different chunking strategies.
        
        Args:
            document_text: Document text to process
            chunking_strategies: List of chunking strategies to use
            
        Returns:
            Dict with index information for each strategy
        """
        chunking_strategies = chunking_strategies or ["fixed_size", "boundary_aware"]
        logger.info(f"Building indices for {len(chunking_strategies)} chunking strategies")
        
        indices = {}
        
        for strategy in chunking_strategies:
            start_time = time.time()
            
            # Create a unique collection name for this strategy and session
            collection_name = f"rag_showdown_{strategy}_{int(time.time())}"
            
            # 1. Chunk document
            chunking_result = self.chunking_processor.chunk_document(
                text=document_text,
                strategy=strategy
            )
            chunks = chunking_result.get("chunks", [])
            
            # 2. Generate embeddings
            embedded_chunks = self.embedding_processor.embed_chunks(chunks)
            
            # 3. Build index
            # Create a separate collection for each strategy
            index = IndexProcessor(
                collection_name=collection_name,
                use_chroma=False  # Use in-memory for demo purposes
            )
            index_ids = index.build_index_from_embeddings(embedded_chunks)
            
            processing_time = time.time() - start_time
            
            indices[strategy] = {
                "strategy": strategy,
                "chunk_count": len(chunks),
                "index_ids": index_ids,
                "processing_time": processing_time,
                "index_processor": index,  # Keep reference to the index
                "collection_name": collection_name
            }
            
            logger.info(f"Built index for {strategy} strategy with {len(chunks)} chunks in {processing_time:.2f}s")
        
        return indices
    
    def compare_retrieval_methods(self, 
                                query: str, 
                                indices: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare different retrieval methods using the built indices.
        
        Args:
            query: Query to test
            indices: Dict of indices from build_retrieval_indices
            
        Returns:
            Dict with retrieval comparison results
        """
        logger.info(f"Comparing retrieval methods for query: '{query}'")
        
        retrieval_results = {}
        
        # For each chunking strategy's index
        for strategy, index_info in indices.items():
            index_processor = index_info.get("index_processor")
            if not index_processor:
                continue
                
            # Create retrieval processor with this index
            retrieval_processor = RetrievalProcessor(
                index_processor=index_processor
            )
            
            # Compare retrieval methods
            comparison = retrieval_processor.compare_retrieval_methods(
                query=query,
                methods=["vector", "entity", "context", "hybrid"]
            )
            
            retrieval_results[strategy] = comparison
        
        return retrieval_results
    
    def compare_synthesis_methods(self, 
                                query: str, 
                                retrieval_results: Dict[str, Any],
                                strategy: str = "boundary_aware") -> Dict[str, Any]:
        """
        Compare different synthesis methods using retrieval results.
        
        Args:
            query: Original query
            retrieval_results: Results from compare_retrieval_methods
            strategy: Which chunking strategy's results to use
            
        Returns:
            Dict with synthesis comparison results
        """
        logger.info(f"Comparing synthesis methods for query: '{query}'")
        
        # Get retrieved chunks from the hybrid method for the selected strategy
        strategy_results = retrieval_results.get(strategy, {})
        method_results = strategy_results.get("method_results", {})
        hybrid_retrieval = method_results.get("hybrid", {})
        context_chunks = hybrid_retrieval.get("results", [])
        
        if not context_chunks:
            logger.warning(f"No context chunks found for strategy {strategy}")
            return {"error": "No context chunks available for synthesis comparison"}
        
        # Compare synthesis methods
        synthesis_comparison = self.synthesis_processor.compare_synthesis_methods(
            query=query,
            context_chunks=context_chunks,
            methods=["single_prompt", "entity_focused", "multi_agent"]
        )
        
        # Generate educational insights
        educational_insights = self.synthesis_processor.generate_educational_insights(
            synthesis_comparison
        )
        
        return {
            "synthesis_comparison": synthesis_comparison,
            "educational_insights": educational_insights
        }
    
    def run_complete_analysis(self, 
                            document_text: str, 
                            query: str = None) -> Dict[str, Any]:
        """
        Run a complete analysis pipeline.
        
        Args:
            document_text: Document text to analyze
            query: Query to test retrieval and synthesis (generated if None)
            
        Returns:
            Dict with all analysis results
        """
        logger.info(f"Running complete RAG Showdown analysis pipeline")
        start_time = time.time()
        
        results = {
            "document_length": len(document_text),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 1. Document analysis
        document_analysis = self.analyze_document(document_text)
        results["document_analysis"] = document_analysis
        
        # 2. Chunking comparison
        chunking_results = self.compare_chunking_strategies(document_text)
        results["chunking_results"] = chunking_results
        
        # 3. Build indices
        indices = self.build_retrieval_indices(
            document_text, 
            chunking_strategies=["fixed_size", "boundary_aware"]
        )
        results["indices"] = {k: {key: v[key] for key in v if key != "index_processor"} 
                             for k, v in indices.items()}
        
        # Generate query if not provided
        if not query:
            summary = document_analysis.get("summary", "")
            query = f"What are the main topics discussed in this document: {summary[:100]}...?"
            
        results["query"] = query
        
        # 4. Retrieval comparison
        retrieval_results = self.compare_retrieval_methods(query, indices)
        results["retrieval_results"] = retrieval_results
        
        # 5. Synthesis comparison
        synthesis_results = self.compare_synthesis_methods(query, retrieval_results)
        results["synthesis_results"] = synthesis_results
        
        # Calculate total processing time
        results["total_processing_time"] = time.time() - start_time
        
        logger.info(f"Complete analysis pipeline finished in {results['total_processing_time']:.2f}s")
        
        return results