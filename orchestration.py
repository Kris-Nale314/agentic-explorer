# orchestration.py
"""
Higher-level orchestration for the Agentic Explorer application.
This module provides the interface between the core analysis logic and the UI.
"""

import os
import json
import logging
import time
from datetime import datetime
from config import Config
from processors.document_analyzer import DocumentAnalyzer
from processors.summarization_manager import SummarizationManager
from processors.text_processor import process_document
from analysis import run_analysis_with_tracking
from agents.agent_tracker import AgentTracker


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

def run_analysis(file_path=None, text_content=None, analysis_type="comprehensive", 
                output_dir=None, track_agents=True):
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
            - "multi_agent": Full multi-agent analysis with tracking
        output_dir (str, optional): Directory to save outputs
        track_agents (bool, optional): Whether to track agent activities
        
    Returns:
        dict: Structured analysis results
    """
    # Set default output directory
    if output_dir is None:
        output_dir = Config.OUTPUT_DIR
        os.makedirs(output_dir, exist_ok=True)
    
    # Load document if needed
    if file_path and not text_content:
        logger.info(f"Loading document from {file_path}")
        text_content = load_test_document(file_path)
    
    if not text_content:
        error_msg = "Either file_path or text_content must be provided"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Generate session name from current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_name = f"analysis_{analysis_type}_{timestamp}"
    
    # Pre-process the document
    processed_text = process_document(text_content)
    
    # For multi-agent analysis, use the tracked CrewAI system
    if analysis_type == "multi_agent":
        logger.info("Running multi-agent analysis with CrewAI")
        return run_analysis_with_tracking(
            processed_text, 
            session_name=session_name,
            output_dir=output_dir
        )
    
    # For other analysis types, use the processor-based approach
    logger.info(f"Starting {analysis_type} analysis using processors")
    
    # Initialize analyzers
    document_analyzer = DocumentAnalyzer()
    summarization_manager = SummarizationManager()
    
    # Start timing
    start_time = time.time()
    
    # Results dictionary
    results = {
        "document_length": len(processed_text),
        "analysis_type": analysis_type,
        "session_name": session_name
    }
    
    # Run requested analysis
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
    
    # End timing
    total_time = time.time() - start_time
    results["processing_time"] = total_time
    
    # Save results to a file
    output_file = os.path.join(output_dir, f"{session_name}_results.json")
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"{analysis_type} analysis completed in {total_time:.2f} seconds")
    logger.info(f"Results saved to {output_file}")
    
    # Add file information to results
    results["output_file"] = output_file
    
    return results

def generate_educational_material(analysis_results, output_dir=None):
    """
    Generate educational materials from analysis results.
    
    Args:
        analysis_results (dict): Results from analysis
        output_dir (str, optional): Directory to save outputs
        
    Returns:
        dict: Paths to generated educational materials
    """
    if output_dir is None:
        output_dir = Config.OUTPUT_DIR
        os.makedirs(output_dir, exist_ok=True)
    
    logger.info("Generating educational materials from analysis results")
    
    session_name = analysis_results.get("session_name", f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    
    # Create educational markdown
    markdown_lines = [
        f"# Document Analysis Educational Report\n",
        f"Session: {session_name}\n",
        f"Analysis Type: {analysis_results.get('analysis_type', 'Unknown')}\n",
        f"Document Length: {analysis_results.get('document_length', 'Unknown')} characters\n",
    ]
    
    # Add specific sections based on analysis type
    if "metrics" in analysis_results:
        metrics = analysis_results["metrics"]
        markdown_lines.extend([
            "## Document Metrics\n",
            f"- **Word Count**: {metrics.get('word_count', 'N/A')}\n",
            f"- **Sentence Count**: {metrics.get('sentence_count', 'N/A')}\n",
            f"- **Paragraph Count**: {metrics.get('paragraph_count', 'N/A')}\n",
            f"- **Estimated Token Count**: {metrics.get('estimated_token_count', 'N/A')}\n",
            "\n### Most Common Words\n"
        ])
        
        if "most_common_words" in metrics:
            for word, count in metrics.get("most_common_words", []):
                markdown_lines.append(f"- {word}: {count}\n")
    
    if "boundaries" in analysis_results:
        boundaries = analysis_results["boundaries"]
        markdown_lines.extend([
            "\n## Document Boundary Analysis\n",
            f"- **Confidence Score**: {boundaries.get('confidence_score', 'N/A')}\n",
            "\n### Detected Boundaries\n"
        ])
        
        if "boundaries" in boundaries:
            for i, boundary in enumerate(boundaries.get("boundaries", [])):
                markdown_lines.extend([
                    f"#### Boundary {i+1}\n",
                    f"- **Position**: {boundary.get('position', 'N/A')}\n",
                    f"- **Type**: {boundary.get('type', 'N/A')}\n",
                    f"- **Confidence**: {boundary.get('confidence', 'N/A')}\n",
                    f"- **Context**: {boundary.get('context', 'N/A')}\n\n"
                ])
    
    if "multi_strategy_summary" in analysis_results:
        multi_summary = analysis_results["multi_strategy_summary"]
        
        markdown_lines.extend([
            "\n## Multi-Strategy Summarization\n",
            "\n### Standard Summary\n",
            f"{multi_summary.get('standard_summary', 'N/A')}\n",
            "\n### Partitioned Summary\n",
            f"{multi_summary.get('partitioned_summary', {}).get('meta_summary', 'N/A')}\n",
            "\n### Entity-Focused Summary\n",
            f"{multi_summary.get('entity_summary', {}).get('meta_summary', 'N/A')}\n",
            "\n### Comparative Analysis\n",
            f"{multi_summary.get('comparative_analysis', 'N/A')}\n"
        ])
        
        if "recommended_approach" in multi_summary:
            recommendation = multi_summary["recommended_approach"]
            markdown_lines.extend([
                "\n### Recommended Approach\n",
                f"- **Approach**: {recommendation.get('recommended_approach', 'N/A')}\n",
                f"- **Explanation**: {recommendation.get('explanation', 'N/A')}\n"
            ])
    
    # Add educational explanations
    markdown_lines.extend([
        "\n## Educational Insights\n",
        "\n### Why Document Boundaries Matter\n",
        "Document boundaries are critical in AI systems working with mixed content. Traditional approaches often chunk documents based solely on token count, which can split content mid-sentence or mid-concept. This creates context fragmentation that leads to:\n",
        "- Loss of critical relationships between concepts\n",
        "- Increased hallucination when information spans chunk boundaries\n",
        "- Reduced performance in retrieval and analysis\n",
        "\n### How Different Summarization Strategies Work\n",
        "1. **Standard Summarization**: Treats the entire document as a unified whole, which works well for coherent, single-topic documents but can lose nuance with mixed content.\n",
        "2. **Partition-Based Summarization**: Divides the document at natural boundaries before summarizing each section separately, then combines these summaries into a meta-summary. This preserves context within sections.\n",
        "3. **Entity-Focused Summarization**: Organizes information around key entities (companies, people, etc.), which helps maintain clarity when multiple entities are discussed across a document.\n",
        "\nThe optimal strategy depends on document structure: boundary-rich documents benefit from partitioning, while documents with many entities benefit from entity-focused approaches.\n"
    ])
    
    # Write the markdown file
    markdown_output_path = os.path.join(output_dir, f"{session_name}_educational.md")
    with open(markdown_output_path, 'w') as f:
        f.write("".join(markdown_lines))
    
    logger.info(f"Educational materials generated and saved to {markdown_output_path}")
    
    return {
        "markdown_report": markdown_output_path
    }

def create_demo_session(document_path=None, output_dir=None, demo_type="comprehensive"):
    """
    Create a complete demo session with all outputs.
    
    Args:
        document_path (str, optional): Path to document file
        output_dir (str, optional): Directory to save outputs
        demo_type (str, optional): Type of demo to run
            
    Returns:
        dict: Demo session results
    """
    if output_dir is None:
        output_dir = Config.OUTPUT_DIR
        os.makedirs(output_dir, exist_ok=True)
    
    if document_path is None:
        document_path = Config.TEST_DATA_FILE
    
    logger.info(f"Creating demo session with {demo_type} analysis on {document_path}")
    
    # Run appropriate analysis
    if demo_type == "multi_agent":
        results = run_analysis(
            file_path=document_path,
            analysis_type="multi_agent",
            output_dir=output_dir
        )
    else:
        # Run processor-based analysis
        results = run_analysis(
            file_path=document_path,
            analysis_type=demo_type,
            output_dir=output_dir
        )
        
        # Generate educational materials
        educational_materials = generate_educational_material(results, output_dir=output_dir)
        results["educational_materials"] = educational_materials
    
    # Save the complete session information
    session_name = results.get("session_name", f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    session_info = {
        "session_name": session_name,
        "demo_type": demo_type,
        "document_path": document_path,
        "output_dir": output_dir,
        "results": results
    }
    
    session_info_path = os.path.join(output_dir, f"{session_name}_session_info.json")
    with open(session_info_path, 'w') as f:
        json.dump(session_info, f, indent=2)
    
    logger.info(f"Demo session complete! Session info saved to {session_info_path}")
    
    return session_info

# For testing in development
if __name__ == "__main__":
    # Test with the development evaluation file
    test_file = "data/dev_eval_files.json"
    if os.path.exists(test_file):
        print(f"Creating demo session with {test_file}...")
        
        # Ask for demo type
        demo_type = input("Enter demo type (comprehensive, multi_agent): ").strip() or "comprehensive"
        
        # Run the demo
        session_info = create_demo_session(document_path=test_file, demo_type=demo_type)
        
        print(f"\nDemo session created with {demo_type} analysis!")
        print(f"Session name: {session_info['session_name']}")
        print(f"Output directory: {session_info['output_dir']}")
        
        # Show specific results based on demo type
        if demo_type == "multi_agent":
            tracking_info = session_info['results'].get('tracking', {})
            print(f"\nAgent tracking information:")
            print(f"- Activity count: {tracking_info.get('activity_count', 'N/A')}")
            print(f"- Total time: {tracking_info.get('total_time', 'N/A'):.2f} seconds")
            print(f"- Markdown report: {tracking_info.get('markdown_report', 'N/A')}")
        else:
            if 'metrics' in session_info['results']:
                metrics = session_info['results']['metrics']
                print("\nDocument Metrics:")
                print(f"- Word count: {metrics.get('word_count', 'N/A')}")
                print(f"- Sentence count: {metrics.get('sentence_count', 'N/A')}")
            
            if 'educational_materials' in session_info['results']:
                print(f"\nEducational materials available at:")
                print(f"- {session_info['results']['educational_materials'].get('markdown_report', 'N/A')}")
    else:
        print(f"Test file not found: {test_file}")