# run_demo.py
"""
Demonstration script for the Agentic Explorer project.

This script showcases the multi-agent document analysis system
and provides an educational view of what's happening "under the hood"
of AI document processing.
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from config import Config
from orchestration import create_demo_session, load_test_document
from data.content import AGENT_DESCRIPTIONS

def print_section(title, underline_char='='):
    """Print a section title with underlines."""
    print(f"\n{title}")
    print(underline_char * len(title))

def main():
    """Run the Agentic Explorer demonstration."""
    print_section("🚀 Agentic Explorer Demonstration", "=")
    print("Demystifying multi-agent AI by showing what's happening under the hood")
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Run Agentic Explorer demonstration")
    parser.add_argument('--document', type=str, help="Path to document file")
    parser.add_argument('--type', type=str, default="multi_agent", 
                        choices=["basic", "summary", "boundary", "multi_summary", "comprehensive", "multi_agent"],
                        help="Type of analysis to run")
    parser.add_argument('--output', type=str, help="Directory for output files")
    
    args = parser.parse_args()
    
    # Set document path
    document_path = args.document or Config.TEST_DATA_FILE
    if not os.path.exists(document_path):
        print(f"Document file not found: {document_path}")
        print("Please provide a valid document path with --document")
        return
    
    # Set output directory
    output_dir = args.output or Config.OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)
    
    # Set demo type
    demo_type = args.type
    
    print_section("Demo Configuration", "-")
    print(f"Document: {document_path}")
    print(f"Analysis Type: {demo_type}")
    print(f"Output Directory: {output_dir}")
    
    # Preview document
    try:
        document_text = load_test_document(document_path)
        word_count = len(document_text.split())
        
        print_section("Document Preview", "-")
        print(f"Document length: {len(document_text)} characters, approximately {word_count} words")
        print("First 300 characters:")
        print(f"\n{document_text[:300]}...\n")
    except Exception as e:
        print(f"Error loading document: {e}")
        return
    
    # Confirm before proceeding
    proceed = input(f"Run {demo_type} analysis on this document? (y/n): ").lower() == 'y'
    if not proceed:
        print("Demo cancelled")
        return
    
    # Run the demo
    print_section(f"Running {demo_type.title()} Analysis", "-")
    print("This may take a few minutes depending on document size and analysis type...")
    
    try:
        session_info = create_demo_session(
            document_path=document_path,
            output_dir=output_dir,
            demo_type=demo_type
        )
        
        print_section("Analysis Complete!", "-")
        print(f"Session name: {session_info['session_name']}")
        
        # Display appropriate results based on demo type
        if demo_type == "multi_agent":
            tracking_info = session_info['results'].get('tracking', {})
            print(f"Agent tracking information:")
            print(f"- Activity count: {tracking_info.get('activity_count', 'N/A')}")
            print(f"- Total time: {tracking_info.get('total_time', 'N/A'):.2f} seconds")
            print(f"- Markdown report: {tracking_info.get('markdown_report', 'N/A')}")
            
            # Try to extract key insights if available
            crew_result = session_info['results'].get('crew_result', {})
            if isinstance(crew_result, dict) and 'key_insights' in crew_result:
                print_section("Key Insights", "-")
                for i, insight in enumerate(crew_result['key_insights'], 1):
                    print(f"{i}. {insight}")
        else:
            if 'metrics' in session_info['results']:
                metrics = session_info['results']['metrics']
                print_section("Document Metrics", "-")
                print(f"- Word count: {metrics.get('word_count', 'N/A')}")
                print(f"- Sentence count: {metrics.get('sentence_count', 'N/A')}")
                print(f"- Paragraph count: {metrics.get('paragraph_count', 'N/A')}")
            
            if 'educational_materials' in session_info['results']:
                edu_path = session_info['results']['educational_materials'].get('markdown_report', 'N/A')
                print_section("Educational Materials", "-")
                print(f"Educational report available at: {edu_path}")
                
                # Try to read and display a snippet of the educational materials
                try:
                    with open(edu_path, 'r') as f:
                        edu_content = f.read()
                        print_section("Educational Report Preview", "-")
                        print(f"{edu_content[:500]}...\n")
                except Exception as e:
                    print(f"Could not read educational report: {e}")
        
        print_section("Next Steps", "-")
        print("1. Review the generated reports in the output directory")
        print("2. Explore how different analysis types process the same document")
        print("3. Use these outputs to understand what's happening 'under the hood' of AI systems")
        
        print_section("Thank You!", "=")
        print("Agentic Explorer - Demystifying AI one document at a time.")
        
    except Exception as e:
        print(f"Error running demo: {e}")
        return

if __name__ == "__main__":
    main()