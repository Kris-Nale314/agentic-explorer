"""
CLI runner for the RAG Showdown.

Provides a command-line interface for running the RAG comparison.
"""

import os
import sys
import argparse
import logging
from typing import Dict, Any

from orchestration import run_rag_showdown, create_demo_session
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("rag_showdown.log")
    ]
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="RAG Showdown: Traditional vs. Agentic RAG")
    
    parser.add_argument("--document", "-d", type=str, 
                        help="Path to document file (default: uses Config.TEST_DATA_FILE)")
    parser.add_argument("--query", "-q", type=str, 
                        help="Query to test retrieval and synthesis (default: auto-generated)")
    parser.add_argument("--output", "-o", type=str, default=Config.OUTPUT_DIR,
                        help=f"Output directory (default: {Config.OUTPUT_DIR})")
    parser.add_argument("--demo", action="store_true",
                        help="Run in demo mode with predefined settings")
    
    return parser.parse_args()

def main():
    """Main entry point for the script."""
    args = parse_arguments()
    
    print("\n=== RAG Showdown: Traditional vs. Agentic RAG ===\n")
    
    try:
        if args.demo:
            # Run demo mode
            print("Running in demo mode with predefined settings...")
            results = create_demo_session(
                document_path=args.document,
                output_dir=args.output,
                query=args.query
            )
        else:
            # Run standard analysis
            document_path = args.document or Config.TEST_DATA_FILE
            print(f"Analyzing document: {document_path}")
            
            if args.query:
                print(f"Using query: {args.query}")
            
            results = run_rag_showdown(
                file_path=document_path,
                query=args.query,
                output_dir=args.output
            )
        
        # Print summary
        print("\nAnalysis complete!")
        print(f"Total processing time: {results.get('total_processing_time', 0):.2f} seconds")
        print(f"Results saved to: {results.get('report_file')}")
        
        # Print interesting findings
        if "document_analysis" in results and "metrics" in results["document_analysis"]:
            metrics = results["document_analysis"]["metrics"]
            print(f"\nDocument stats: {metrics.get('word_count', 'N/A')} words, "
                 f"{metrics.get('sentence_count', 'N/A')} sentences")
        
        if "chunking_results" in results and "chunking_comparison" in results["chunking_results"]:
            comparison = results["chunking_results"]["chunking_comparison"]
            if "comparison" in comparison and "overall_ranking" in comparison["comparison"]:
                top_strategy = comparison["comparison"]["overall_ranking"][0][0]
                print(f"\nBest chunking strategy: {top_strategy}")
        
        if "synthesis_results" in results and "synthesis_comparison" in results["synthesis_results"]:
            comparison = results["synthesis_results"]["synthesis_comparison"]
            if "comparison" in comparison and "analysis" in comparison["comparison"]:
                analysis = comparison["comparison"]["analysis"]
                if "overall_best_method" in analysis:
                    print(f"\nBest synthesis method: {analysis['overall_best_method']}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error running RAG Showdown: {e}", exc_info=True)
        print(f"\nError: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())