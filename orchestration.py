# orchestration.py
"""
Orchestration module for RAG Showdown.

Handles workflow coordination, session management, and output handling.
"""

import os
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional

from analysis import AnalysisPipeline
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_document(file_path: Optional[str] = None, text_content: Optional[str] = None) -> str:
    """
    Load document content from file path or direct text input.
    
    Args:
        file_path: Path to document file (JSON or text)
        text_content: Direct text input
        
    Returns:
        Document text content
    """
    if text_content:
        return text_content
        
    if not file_path:
        file_path = Config.TEST_DATA_FILE
        
    logger.info(f"Loading document from {file_path}")
    
    try:
        # Try to load as JSON first
        if file_path.endswith('.json'):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Handle different JSON structures
            if 'combined_text' in data:
                return data['combined_text']
            elif 'documents' in data:
                return '\n\n'.join(data['documents'])
            else:
                # Return the raw JSON as a fallback
                return json.dumps(data, indent=2)
        else:
            # Load as plain text
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
                
    except Exception as e:
        logger.error(f"Error loading document: {e}")
        raise

def run_rag_showdown(file_path: Optional[str] = None, 
                    text_content: Optional[str] = None,
                    query: Optional[str] = None,
                    output_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Run the RAG Showdown analysis workflow.
    
    Args:
        file_path: Path to document file
        text_content: Direct text input (alternative to file_path)
        query: Query for testing retrieval and synthesis
        output_dir: Directory to save results
        
    Returns:
        Dictionary with analysis results
    """
    # Set up output directory
    output_dir = output_dir or Config.OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate session ID
    session_id = f"rag_showdown_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    logger.info(f"Starting RAG Showdown session: {session_id}")
    
    # Load document
    document_text = load_document(file_path, text_content)
    logger.info(f"Loaded document ({len(document_text)} chars)")
    
    # Create analysis pipeline
    pipeline = AnalysisPipeline()
    
    # Run analysis
    results = pipeline.run_complete_analysis(document_text, query)
    
    # Add session information
    results["session_id"] = session_id
    results["file_path"] = file_path
    results["output_dir"] = output_dir
    
    # Save results to JSON file
    output_file = os.path.join(output_dir, f"{session_id}_results.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Results saved to {output_file}")
    
    # Generate report
    report_file = generate_report(results, output_dir)
    results["report_file"] = report_file
    
    return results

def generate_report(results: Dict[str, Any], output_dir: Optional[str] = None) -> str:
    """
    Generate a markdown report from analysis results.
    
    Args:
        results: Analysis results
        output_dir: Directory to save report
        
    Returns:
        Path to the generated report file
    """
    output_dir = output_dir or Config.OUTPUT_DIR
    session_id = results.get("session_id", f"rag_showdown_{int(time.time())}")
    
    report_lines = [
        "# RAG Showdown Analysis Report\n\n",
        f"Session ID: {session_id}  \n",
        f"Document length: {results.get('document_length', 'Unknown')} characters  \n",
        f"Processing time: {results.get('total_processing_time', 0):.2f} seconds  \n\n"
    ]
    
    # Add document analysis
    doc_analysis = results.get("document_analysis", {})
    if doc_analysis:
        report_lines.append("## Document Analysis\n\n")
        
        # Add metrics
        metrics = doc_analysis.get("metrics", {})
        if metrics:
            report_lines.append("### Document Metrics\n\n")
            report_lines.append(f"- Word count: {metrics.get('word_count', 'N/A')}\n")
            report_lines.append(f"- Sentence count: {metrics.get('sentence_count', 'N/A')}\n")
            report_lines.append(f"- Paragraph count: {metrics.get('paragraph_count', 'N/A')}\n")
            report_lines.append(f"- Estimated tokens: {metrics.get('estimated_token_count', 'N/A')}\n\n")
        
        # Add boundary info
        boundaries = doc_analysis.get("boundaries", {})
        if boundaries:
            report_lines.append("### Document Boundaries\n\n")
            confidence = boundaries.get("confidence_score", "N/A")
            report_lines.append(f"Boundary detection confidence: {confidence}\n\n")
            
            boundary_list = boundaries.get("boundaries", [])
            if boundary_list:
                report_lines.append(f"Detected {len(boundary_list)} potential document boundaries:\n\n")
                for i, boundary in enumerate(boundary_list[:5]):  # Show first 5 boundaries
                    report_lines.append(f"- Boundary {i+1}: {boundary.get('type', 'Unknown')} " +
                                      f"at position {boundary.get('position', 'Unknown')}\n")
                
                if len(boundary_list) > 5:
                    report_lines.append(f"- ... and {len(boundary_list) - 5} more boundaries\n\n")
    
    # Add chunking comparison
    chunking_results = results.get("chunking_results", {})
    comparison = chunking_results.get("chunking_comparison", {}).get("comparison", {})
    
    if comparison:
        report_lines.append("## Chunking Strategy Comparison\n\n")
        
        # Overall ranking
        if "overall_ranking" in comparison:
            report_lines.append("### Strategy Ranking\n\n")
            for strategy, score in comparison.get("overall_ranking", []):
                report_lines.append(f"- **{strategy}**: {score:.3f}\n")
            report_lines.append("\n")
        
        # Metrics comparison
        if "metrics_comparison" in comparison:
            report_lines.append("### Metrics Comparison\n\n")
            report_lines.append("| Strategy | Chunks | Avg Size | Boundary Score | Sentence Score |\n")
            report_lines.append("|----------|--------|----------|----------------|---------------|\n")
            
            metrics = comparison.get("metrics_comparison", {})
            chunk_counts = metrics.get("chunk_count", {})
            
            for strategy in chunk_counts.keys():
                chunks = chunk_counts.get(strategy, "N/A")
                avg_size = metrics.get("avg_chunk_size", {}).get(strategy, "N/A")
                boundary_score = metrics.get("boundary_preservation_score", {}).get(strategy, "N/A")
                sentence_score = metrics.get("sentence_integrity_score", {}).get(strategy, "N/A")
                
                # Format numbers
                if isinstance(avg_size, (int, float)):
                    avg_size = f"{avg_size:.1f}"
                if isinstance(boundary_score, (int, float)):
                    boundary_score = f"{boundary_score:.2f}"
                if isinstance(sentence_score, (int, float)):
                    sentence_score = f"{sentence_score:.2f}"
                
                report_lines.append(f"| {strategy} | {chunks} | {avg_size} | {boundary_score} | {sentence_score} |\n")
            
            report_lines.append("\n")
    
    # Add retrieval comparison
    retrieval_results = results.get("retrieval_results", {})
    if retrieval_results:
        report_lines.append("## Retrieval Method Comparison\n\n")
        
        # Add comparison for each chunking strategy
        for strategy, strategy_results in retrieval_results.items():
            report_lines.append(f"### Retrieval with {strategy} chunking\n\n")
            
            comparison = strategy_results.get("comparison", {})
            summary = comparison.get("summary", {})
            
            if summary:
                report_lines.append(f"Fastest method: **{summary.get('fastest_method', 'N/A')}**\n")
                report_lines.append(f"Most unique results: **{summary.get('most_unique_method', 'N/A')}**\n\n")
            
            # Add speed comparison
            speeds = comparison.get("speed_comparison", {})
            if speeds:
                report_lines.append("#### Retrieval Speed\n\n")
                for method, speed in speeds.items():
                    report_lines.append(f"- {method}: {speed:.3f}s\n")
                report_lines.append("\n")
    
    # Add synthesis comparison
    synthesis_results = results.get("synthesis_results", {})
    if synthesis_results:
        report_lines.append("## Synthesis Method Comparison\n\n")
        
        # Add analysis from synthesis comparison
        comparison = synthesis_results.get("synthesis_comparison", {})
        analysis = comparison.get("comparison", {}).get("analysis", {})
        
        if analysis:
            # Method rankings
            if "factual_completeness_ranking" in analysis:
                report_lines.append("### Factual Completeness Ranking\n\n")
                for method in analysis.get("factual_completeness_ranking", []):
                    report_lines.append(f"- {method}\n")
                report_lines.append("\n")
            
            # Overall best method
            if "overall_best_method" in analysis:
                report_lines.append(f"### Overall Best Method: **{analysis.get('overall_best_method', 'N/A')}**\n\n")
                report_lines.append(f"Reasoning: {analysis.get('reasoning', 'N/A')}\n\n")
        
        # Add educational insights
        insights = synthesis_results.get("educational_insights", {})
        if insights:
            report_lines.append("## Educational Insights\n\n")
            
            # Method characteristics
            for method, chars in insights.get("method_characteristics", {}).items():
                report_lines.append(f"### {method.replace('_', ' ').title()}\n\n")
                report_lines.append(f"{chars.get('description', '')}\n\n")
                
                report_lines.append("**Strengths:**\n\n")
                for strength in chars.get("strengths", []):
                    report_lines.append(f"- {strength}\n")
                report_lines.append("\n")
                
                report_lines.append("**Limitations:**\n\n")
                for limitation in chars.get("limitations", []):
                    report_lines.append(f"- {limitation}\n")
                report_lines.append("\n")
            
            # Add summary
            if "educational_summary" in insights:
                report_lines.append("### Summary\n\n")
                report_lines.append(insights.get("educational_summary", ""))
    
    # Save report to file
    report_file = os.path.join(output_dir, f"{session_id}_report.md")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.writelines(report_lines)
    
    logger.info(f"Report generated: {report_file}")
    
    return report_file

def create_demo_session(document_path=None, output_dir=None, query=None):
    """
    Create a demo session for the RAG Showdown.
    
    Args:
        document_path: Path to document file
        output_dir: Directory to save results
        query: Query for testing
        
    Returns:
        Dictionary with session results
    """
    document_path = document_path or Config.TEST_DATA_FILE
    output_dir = output_dir or Config.OUTPUT_DIR
    
    logger.info(f"Creating demo session with {document_path}")
    
    # Run analysis
    results = run_rag_showdown(
        file_path=document_path,
        query=query,
        output_dir=output_dir
    )
    
    return results

if __name__ == "__main__":
    # Test with default document
    create_demo_session()