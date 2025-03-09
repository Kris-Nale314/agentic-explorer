# processors/summarization_manager.py
"""
Manager for document summarization with different strategies.
"""

import logging
from processors.document_analyzer import DocumentAnalyzer
from processors.partitioning_strategies import DocumentPartitioner

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SummarizationManager:
    """Manages document summarization with different strategies."""
    
    def __init__(self):
        """Initialize the SummarizationManager."""
        self.analyzer = DocumentAnalyzer()
        self.partitioner = DocumentPartitioner()
    
    def summarize_full_document(self, text, max_length=None):
        """
        Generate a standard summary of the full document.
        
        Args:
            text (str): The document text
            max_length (int, optional): Maximum length in words
            
        Returns:
            dict: Summary results
        """
        try:
            metrics = self.analyzer.compute_basic_metrics(text)
            summary = self.analyzer.generate_summary(text, approach="standard", max_length=max_length)
            
            return {
                "summary_type": "full_document",
                "summary": summary,
                "document_metrics": metrics
            }
        except Exception as e:
            logger.error(f"Error in full document summarization: {e}")
            return {"error": str(e)}
    
    def summarize_by_partition(self, text, max_length=None):
        """
        Generate summaries based on document partitions.
        
        Args:
            text (str): The document text
            max_length (int, optional): Maximum length per partition summary
            
        Returns:
            dict: Summary results
        """
        try:
            metrics = self.analyzer.compute_basic_metrics(text)
            
            # Get partitions based on detected boundaries
            segments = self.partitioner.partition_by_detected_boundaries(text)
            
            # Maximum length per segment summary (distributed proportionally)
            if max_length:
                segment_max_length = max(50, max_length // len(segments))
            else:
                segment_max_length = None
            
            # Generate summary for each segment
            segment_summaries = []
            for i, segment in enumerate(segments):
                segment_metrics = self.analyzer.compute_basic_metrics(segment)
                summary = self.analyzer.generate_summary(segment, max_length=segment_max_length)
                
                segment_summaries.append({
                    "segment_index": i,
                    "segment_metrics": segment_metrics,
                    "summary": summary
                })
            
            # Generate a meta-summary from the segment summaries
            combined_summaries = "\n\n".join([s["summary"] for s in segment_summaries])
            meta_prompt = f"""
            I have divided a document into {len(segments)} segments and created summaries for each.
            Based on these summaries, provide a coherent overall summary that captures the key points.
            
            SEGMENT SUMMARIES:
            {combined_summaries}
            """
            
            meta_summary = self.analyzer.openai_client.generate_completion(meta_prompt)
            
            return {
                "summary_type": "partitioned",
                "document_metrics": metrics,
                "segment_count": len(segments),
                "segment_summaries": segment_summaries,
                "meta_summary": meta_summary
            }
        except Exception as e:
            logger.error(f"Error in partitioned summarization: {e}")
            return {"error": str(e)}
    
    def summarize_by_entity(self, text, max_length=None):
        """
        Generate summaries focused on different entities mentioned.
        
        Args:
            text (str): The document text
            max_length (int, optional): Maximum length per entity summary
            
        Returns:
            dict: Summary results
        """
        try:
            metrics = self.analyzer.compute_basic_metrics(text)
            
            # Get entity-based partitions
            entity_segments = self.partitioner.partition_by_entity_mentions(text)
            
            # Maximum length per entity summary
            if max_length and len(entity_segments) > 1:
                entity_max_length = max(50, max_length // len(entity_segments))
            else:
                entity_max_length = max_length
            
            # Generate summary for each entity
            entity_summaries = {}
            for entity, segment in entity_segments.items():
                if entity != "full_document":  # Skip the fallback full document
                    summary = self.analyzer.generate_summary(
                        segment, 
                        approach="entity_focused", 
                        max_length=entity_max_length
                    )
                    entity_summaries[entity] = summary
            
            # Generate a meta-summary if we have multiple entities
            if len(entity_summaries) > 1:
                combined_summaries = "\n\n".join([f"{entity}: {summary}" for entity, summary in entity_summaries.items()])
                meta_prompt = f"""
                I have analyzed a document by focusing on different entities mentioned and created summaries for each.
                Based on these entity-focused summaries, provide a coherent overall summary that captures the relationships and key points.
                
                ENTITY SUMMARIES:
                {combined_summaries}
                """
                
                meta_summary = self.analyzer.openai_client.generate_completion(meta_prompt)
            else:
                # If we only have one entity or fallback, use that as the meta summary
                meta_summary = next(iter(entity_summaries.values())) if entity_summaries else "Could not identify distinct entities for summarization."
            
            return {
                "summary_type": "entity_focused",
                "document_metrics": metrics,
                "entity_count": len(entity_summaries),
                "entity_summaries": entity_summaries,
                "meta_summary": meta_summary
            }
        except Exception as e:
            logger.error(f"Error in entity-focused summarization: {e}")
            return {"error": str(e)}
    
    def generate_multi_strategy_summary(self, text, max_length=None):
        """
        Generate summaries using multiple strategies and compare them.
        
        Args:
            text (str): The document text
            max_length (int, optional): Maximum total summary length
            
        Returns:
            dict: Comprehensive summary results
        """
        try:
            # Calculate metrics once
            metrics = self.analyzer.compute_basic_metrics(text)
            
            # Distribute max_length across summary types if specified
            if max_length:
                strategy_max_length = max(100, max_length // 3)
            else:
                strategy_max_length = None
            
            # Get all three summary types
            standard_summary = self.summarize_full_document(text, max_length=strategy_max_length)
            partitioned_summary = self.summarize_by_partition(text, max_length=strategy_max_length)
            entity_summary = self.summarize_by_entity(text, max_length=strategy_max_length)
            
            # Generate a comparative analysis
            comparison_prompt = f"""
            I have analyzed a document using three different summarization strategies:
            
            1. STANDARD SUMMARY:
            {standard_summary.get('summary', 'Error generating standard summary')}
            
            2. PARTITION-BASED SUMMARY:
            {partitioned_summary.get('meta_summary', 'Error generating partitioned summary')}
            
            3. ENTITY-FOCUSED SUMMARY:
            {entity_summary.get('meta_summary', 'Error generating entity summary')}
            
            Compare and contrast these summaries. What unique insights does each approach provide?
            What are the strengths and limitations of each approach for this specific document?
            How do they differ in their coverage of key information?
            """
            
            comparison = self.analyzer.openai_client.generate_completion(comparison_prompt)
            
            # Also detect if the document appears to contain multiple merged documents
            boundary_analysis = self.analyzer.analyze_document_boundaries(text)
            
            return {
                "document_metrics": metrics,
                "standard_summary": standard_summary.get('summary'),
                "partitioned_summary": partitioned_summary,
                "entity_summary": entity_summary,
                "boundary_analysis": boundary_analysis,
                "comparative_analysis": comparison,
                "recommended_approach": self._recommend_approach(metrics, boundary_analysis)
            }
        except Exception as e:
            logger.error(f"Error in multi-strategy summarization: {e}")
            return {"error": str(e), "partial_results": locals()}
    
    def _recommend_approach(self, metrics, boundary_analysis):
        """
        Recommend the best summarization approach based on document characteristics.
        
        Args:
            metrics (dict): Document metrics
            boundary_analysis (dict): Boundary analysis results
            
        Returns:
            dict: Recommendation with explanation
        """
        confidence_score = boundary_analysis.get('confidence_score', 0)
        if isinstance(confidence_score, str):
            try:
                confidence_score = float(confidence_score)
            except:
                confidence_score = 0
                
        boundary_count = len(boundary_analysis.get('boundaries', []))
        entity_count = len(boundary_analysis.get('entities', []))
        
        if boundary_count > 1 and confidence_score > 6:
            approach = "partitioned"
            explanation = "This document appears to contain multiple distinct sections or merged documents. A partition-based approach preserves the context of each section."
        elif entity_count > 3:
            approach = "entity_focused"
            explanation = "This document mentions multiple key entities. An entity-focused approach helps organize information around these main subjects."
        else:
            approach = "standard"
            explanation = "This document appears to be coherent with a single focus. A standard summary approach is sufficient."
            
        return {
            "recommended_approach": approach,
            "explanation": explanation,
            "factors": {
                "boundary_confidence": confidence_score,
                "boundary_count": boundary_count,
                "entity_count": entity_count,
                "word_count": metrics.get('word_count', 0)
            }
        }