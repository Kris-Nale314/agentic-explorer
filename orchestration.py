# orchestration.py
"""
Higher-level orchestration for the Agentic Explorer application.
This module provides the interface between the core analysis logic and the UI.
"""

import os
import json
import logging
from processors.document_analyzer import DocumentAnalyzer
from processors.summarization_manager import SummarizationManager
from processors.text_processor import process_document

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_test_document(file_path):
    """
    Load a test document from a JSON file.
    
    Args:
        file_path (str): Path to the JSON file
        
    Returns:
        str: The document text
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        # Handle different JSON structures
        if 'combined_text' in data:
            return data['combined_text']
        elif 'documents' in data:
            return '\n\n'.join(data['documents'])
        else:
            # Attempt to convert the whole JSON to a string if structure is unknown
            return json.dumps(data)
            
    except Exception as e:
        logger.error(f"Error loading test document: {e}")
        raise

def run_analysis(file_path=None, text_content=None, analysis_type="comprehensive"):
    """
    Run document analysis through our processing pipeline.
    
    Args:
        file_path (str, optional): Path to JSON file with documents
        text_content (str, optional): Direct text input for analysis
        analysis_type (str, optional): Type of analysis to run
            - "basic": Just document metrics
            - "summary": Basic document summary
            - "boundary": Document boundary detection
            - "multi_summary": Multiple summarization strategies
            - "comprehensive": All analysis types
        
    Returns:
        dict: Structured analysis results
    """
    if file_path and not text_content:
        logger.info(f"Loading document from {file_path}")
        text_content = load_test_document(file_path)
    
    if not text_content:
        error_msg = "Either file_path or text_content must be provided"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Pre-process the document
    processed_text = process_document(text_content)
    
    # Initialize analyzers
    document_analyzer = DocumentAnalyzer()
    summarization_manager = SummarizationManager()
    
    # Results dictionary
    results = {
        "document_length": len(processed_text),
        "analysis_type": analysis_type
    }
    
    # Run requested analysis
    logger.info(f"Starting {analysis_type} analysis")
    
    if analysis_type in ["basic", "comprehensive"]:
        # Basic document metrics
        results["metrics"] = document_analyzer.compute_basic_metrics(processed_text)
    
    if analysis_type in ["summary", "comprehensive"]:
        # Standard document summary
        results["summary"] = summarization_manager.summarize_full_document(processed_text)
    
    if analysis_type in ["boundary", "comprehensive"]:
        # Boundary detection
        results["boundaries"] = document_analyzer.analyze_document_boundaries(processed_text)
   
    if analysis_type in ["multi_summary", "comprehensive"]:
        # Multi-strategy summarization
        results["multi_strategy_summary"] = summarization_manager.generate_multi_strategy_summary(processed_text)
    
    logger.info(f"{analysis_type} analysis completed")
    return results

# For testing in development
if __name__ == "__main__":
    # Test with the development evaluation file
    test_file = "data/dev_eval_files.json"
    if os.path.exists(test_file):
        print(f"Running analysis on {test_file}...")
        results = run_analysis(file_path=test_file, analysis_type="comprehensive")
        
        # Save results to a file for inspection
        output_file = "data/analysis_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
            
        print(f"Analysis complete! Results saved to {output_file}")
        
        # Also print a summary to console
        if "metrics" in results:
            metrics = results["metrics"]
            print("\nDocument Metrics:")
            print(f"- Word count: {metrics.get('word_count', 'N/A')}")
            print(f"- Sentence count: {metrics.get('sentence_count', 'N/A')}")
            print(f"- Estimated token count: {metrics.get('estimated_token_count', 'N/A')}")
            
        if "multi_strategy_summary" in results and "recommended_approach" in results["multi_strategy_summary"]:
            recommendation = results["multi_strategy_summary"]["recommended_approach"]
            print(f"\nRecommended Approach: {recommendation.get('recommended_approach', 'N/A')}")
            print(f"Explanation: {recommendation.get('explanation', 'N/A')}")
    else:
        print(f"Test file not found: {test_file}")