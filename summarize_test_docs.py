"""
Script to analyze and summarize test documents.

This script uses the SummarizationProcessor to analyze and summarize
documents in the test data folder, saving results as markdown files.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, Optional
import argparse
import time

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import processors
from processors.summarize import SummarizationProcessor
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("summarization.log")
    ]
)
logger = logging.getLogger(__name__)

def load_test_document(file_path: str) -> str:
    """
    Load a test document from a file.
    
    Args:
        file_path: Path to the document file
        
    Returns:
        Document text
    """
    logger.info(f"Loading document from {file_path}")
    
    try:
        # Check file extension
        _, ext = os.path.splitext(file_path)
        
        if ext.lower() == '.json':
            # Handle JSON files
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if 'combined_text' in data:
                return data['combined_text']
            elif 'documents' in data and isinstance(data['documents'], list):
                return '\n\n'.join(data['documents'])
            else:
                # Return formatted JSON as a fallback
                return json.dumps(data, indent=2)
        else:
            # Handle as plain text
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
    
    except Exception as e:
        logger.error(f"Error loading document: {e}")
        raise

def summarize_document(text: str, output_dir: str, filename_base: str) -> Dict[str, Any]:
    """
    Analyze and summarize a document using multiple strategies.
    
    Args:
        text: Document text
        output_dir: Directory to save results
        filename_base: Base name for output files
        
    Returns:
        Dictionary with summarization results
    """
    logger.info(f"Analyzing document ({len(text)} characters)")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize summarization processor
    summarizer = SummarizationProcessor()
    
    # Start timing
    start_time = time.time()
    
    # Generate different summary types
    results = {}
    
    # 1. Basic concise summary
    logger.info("Generating basic concise summary")
    basic_summary = summarizer.basic_summary(text, style="concise")
    results["basic_concise"] = basic_summary
    
    # 2. Entity-focused summary
    logger.info("Generating entity-focused summary")
    entity_summary = summarizer.entity_focused_summary(text)
    results["entity_focused"] = entity_summary
    
    # 3. Temporal summary
    logger.info("Generating temporal summary")
    temporal_summary = summarizer.temporal_summary(text)
    results["temporal"] = temporal_summary
    
    # 4. Extractive summary
    logger.info("Generating extractive summary")
    extractive_summary = summarizer.extractive_summary(text)
    results["extractive"] = extractive_summary
    
    # Calculate total processing time
    total_time = time.time() - start_time
    results["total_processing_time"] = total_time
    
    # Generate markdown report
    md_content = generate_markdown_report(text, results)
    
    # Save markdown report
    output_path = os.path.join(output_dir, f"{filename_base}_summary.md")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    logger.info(f"Saved summary report to {output_path}")
    
    # Save raw results as JSON for reference
    json_path = os.path.join(output_dir, f"{filename_base}_raw_summary.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Saved raw results to {json_path}")
    
    return {
        "results": results,
        "markdown_path": output_path,
        "json_path": json_path
    }

def generate_markdown_report(original_text: str, results: Dict[str, Any]) -> str:
    """
    Generate a markdown report of summarization results.
    
    Args:
        original_text: Original document text
        results: Summarization results
        
    Returns:
        Markdown content
    """
    md_lines = []
    
    # Add title and introduction
    md_lines.append("# Document Analysis and Summary Report\n")
    md_lines.append(f"*Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}*\n")
    
    # Document statistics
    md_lines.append("## Document Statistics\n")
    md_lines.append(f"- **Document Length**: {len(original_text)} characters\n")
    md_lines.append(f"- **Word Count**: Approximately {len(original_text.split())} words\n")
    md_lines.append(f"- **Processing Time**: {results.get('total_processing_time', 0):.2f} seconds\n")
    
    # Basic concise summary
    basic_summary = results.get("basic_concise", {})
    if "summary" in basic_summary:
        md_lines.append("\n## Executive Summary\n")
        md_lines.append(basic_summary["summary"])
        md_lines.append(f"\n*Word count: {basic_summary.get('word_count', 'N/A')}*\n")
    
    # Entity-focused summary
    entity_summary = results.get("entity_focused", {})
    if "summary" in entity_summary:
        md_lines.append("\n## Key Entities and Their Context\n")
        md_lines.append(entity_summary["summary"])
        
        # List detected entities
        entities = entity_summary.get("entities", [])
        if entities:
            md_lines.append("\n### Detected Key Entities\n")
            for entity in entities:
                md_lines.append(f"- {entity}\n")
    
    # Temporal summary
    temporal_summary = results.get("temporal", {})
    if "summary" in temporal_summary:
        md_lines.append("\n## Chronological Analysis\n")
        md_lines.append(temporal_summary["summary"])
        
        # List detected time periods
        time_periods = temporal_summary.get("time_periods", [])
        if time_periods:
            md_lines.append("\n### Detected Time Periods\n")
            for period in time_periods:
                md_lines.append(f"- {period}\n")
    
    # Extractive summary
    extractive_summary = results.get("extractive", {})
    if "summary" in extractive_summary:
        md_lines.append("\n## Key Statements\n")
        md_lines.append("The following statements represent the most important information in the document:\n")
        md_lines.append(extractive_summary["summary"])
    
    # Document complexity assessment
    md_lines.append("\n## Document Complexity Assessment\n")
    
    # Entity complexity
    entity_count = len(entity_summary.get("entities", []))
    if entity_count > 5:
        complexity = "High"
    elif entity_count > 2:
        complexity = "Medium"
    else:
        complexity = "Low"
    md_lines.append(f"- **Entity Complexity**: {complexity} ({entity_count} key entities detected)\n")
    
    # Temporal complexity
    time_period_count = len(temporal_summary.get("time_periods", []))
    if time_period_count > 3:
        complexity = "High"
    elif time_period_count > 1:
        complexity = "Medium"
    else:
        complexity = "Low"
    md_lines.append(f"- **Temporal Complexity**: {complexity} ({time_period_count} time periods detected)\n")
    
    # Overall assessment
    md_lines.append("\n## RAG Strategy Recommendations\n")
    recommendations = []
    
    if entity_count > 3:
        recommendations.append("- Use entity-aware retrieval to properly track and disambiguate multiple entities")
    
    if time_period_count > 1:
        recommendations.append("- Implement temporal tracking to maintain chronological consistency")
    
    if entity_count > 3 or time_period_count > 1:
        recommendations.append("- Consider boundary-aware chunking to preserve context around entity and time references")
        recommendations.append("- Multi-agent synthesis would help manage the complex interrelationships in this document")
    else:
        recommendations.append("- Standard RAG approaches may be sufficient for this relatively straightforward document")
        recommendations.append("- Focus on ensuring high-quality embeddings as the document has low complexity")
    
    md_lines.extend(recommendations)
    
    return "\n".join(md_lines)

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Analyze and summarize test documents")
    
    parser.add_argument("--document", "-d", type=str, default=Config.TEST_DATA_FILE,
                       help=f"Path to document file (default: {Config.TEST_DATA_FILE})")
    parser.add_argument("--output", "-o", type=str, default=Config.OUTPUT_DIR,
                       help=f"Output directory (default: {Config.OUTPUT_DIR})")
    
    args = parser.parse_args()
    
    try:
        # Get document path
        document_path = args.document
        if not os.path.exists(document_path):
            logger.error(f"Document not found: {document_path}")
            print(f"Error: Document not found: {document_path}")
            return 1
        
        # Generate filename base from document name
        filename_base = os.path.splitext(os.path.basename(document_path))[0]
        
        # Load document
        document_text = load_test_document(document_path)
        
        # Process document
        print(f"Analyzing document: {document_path}")
        print(f"Document length: {len(document_text)} characters")
        
        # Summarize document
        results = summarize_document(document_text, args.output, filename_base)
        
        # Print results
        print("\nSummarization complete!")
        print(f"Summary report saved to: {results['markdown_path']}")
        print(f"Raw results saved to: {results['json_path']}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error in summarization: {e}", exc_info=True)
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())