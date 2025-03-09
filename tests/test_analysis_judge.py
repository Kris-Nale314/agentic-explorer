# tests/test_analysis_judge.py
"""
Test script for the Analysis Judge agent functionality.
"""

import os
import sys
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from agents.agent_tracker import AgentTracker
from agents.boundary_detective import BoundaryDetectiveAgent
from agents.document_analyzer import DocumentAnalyzerAgent
from agents.summarization_manager import SummarizationManagerAgent
from agents.analysis_judge import AnalysisJudgeAgent
from processors.text_processor import process_document
from orchestration import load_test_document

def test_analysis_judge():
    """Test the AnalysisJudgeAgent class."""
    print("\n=== Testing Analysis Judge Agent ===")
    
    # Initialize a tracker for all agents
    tracker = AgentTracker(session_name=f"judge_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    
    # Create output directory if it doesn't exist
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Simple test text
    test_text = """
    Apple Inc. reported strong earnings for Q3 2023, with revenue reaching $81.8 billion.
    CEO Tim Cook highlighted the growth in Services, which set another all-time record.
    iPhone sales were slightly down but still exceeded analyst expectations.
    
    Meanwhile, Microsoft Corporation announced its Q2 2023 results on January 24, 2023,
    with cloud revenue growing 22% year-over-year to $27.1 billion. CEO Satya Nadella
    emphasized the company's AI investments and integration into Microsoft products.
    
    In other tech news, Google's parent company Alphabet reported mixed results for Q2,
    with revenue of $74.6 billion, up 7% year-over-year. YouTube advertising revenue
    showed signs of recovery after several challenging quarters.
    
    Analysts noted that all three companies are heavily investing in AI capabilities,
    setting up a competitive landscape for the coming years in cloud services and
    consumer products. The market responded positively to all three earnings reports.
    """
    
    # Process the document
    processed_text = process_document(test_text)
    
    print("Initializing agents...")
    
    # Initialize agents
    boundary_agent = BoundaryDetectiveAgent()
    boundary_agent.set_tracker(tracker)
    
    document_agent = DocumentAnalyzerAgent()
    document_agent.set_tracker(tracker)
    
    summarization_agent = SummarizationManagerAgent()
    summarization_agent.set_tracker(tracker)
    
    analysis_judge = AnalysisJudgeAgent()
    analysis_judge.set_tracker(tracker)
    
    print("Running boundary detection...")
    
    # Run boundary detection
    boundary_analysis = boundary_agent.detect_boundaries(processed_text)
    
    print("Running document classification...")
    
    # Run document classification
    document_classification = boundary_agent.classify_document_segments(processed_text, boundary_analysis)
    
    print("Computing document metrics...")
    
    # Run document analysis
    document_metrics = document_agent.compute_document_metrics(processed_text)
    
    print("Generating summaries...")
    
    # Run summarization
    multi_strategy_summary = summarization_agent.generate_all_summaries(processed_text)
    
    print("Running analysis judge synthesis...")
    
    # Run analysis judge synthesis
    synthesis = analysis_judge.synthesize_analysis(
        processed_text,
        boundary_analysis,
        document_classification,
        document_metrics,
        multi_strategy_summary
    )
    
    print("\nAnalysis Judge Synthesis:")
    print(json.dumps(synthesis, indent=2)[:500] + "...\n")
    
    print("Running summarization evaluation...")
    
    # Run summarization evaluation
    evaluation = analysis_judge.evaluate_summarization_strategies(processed_text, multi_strategy_summary)
    
    print("\nSummarization Evaluation:")
    print(json.dumps(evaluation, indent=2)[:500] + "...\n")
    
    print("Creating educational report...")
    
    # Create educational report
    educational_report = analysis_judge.create_educational_report(
        processed_text,
        {
            "boundaries": boundary_analysis,
            "classification": document_classification,
            "metrics": document_metrics,
            "multi_strategy_summary": multi_strategy_summary
        }
    )
    
    print("\nEducational Report:")
    print(json.dumps(educational_report, indent=2)[:500] + "...\n")
    
    # Export tracking data
    json_output_path = os.path.join(output_dir, f"{tracker.session_name}_tracking.json")
    tracker.export_json(json_output_path)
    
    markdown_output = tracker.generate_markdown()
    markdown_output_path = os.path.join(output_dir, f"{tracker.session_name}_report.md")
    with open(markdown_output_path, "w") as f:
        f.write(markdown_output)
    
    # Save the synthesis results
    synthesis_output_path = os.path.join(output_dir, f"{tracker.session_name}_synthesis.json")
    with open(synthesis_output_path, "w") as f:
        json.dump(synthesis, f, indent=2)
    
    print(f"\nResults and tracking information saved to:")
    print(f"- Tracking JSON: {json_output_path}")
    print(f"- Tracking Markdown: {markdown_output_path}")
    print(f"- Synthesis Results: {synthesis_output_path}")
    
    print("\nReal Document Analysis Judge test completed")
    
    return synthesis

if __name__ == "__main__":
    # Run tests based on command line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Analysis Judge functionality')
    parser.add_argument('--simple', action='store_true', help='Run simple test with sample text')
    parser.add_argument('--real', action='store_true', help='Run test with real document')
    
    args = parser.parse_args()
    
    # If no specific tests are specified, run the simple test
    run_simple = args.simple or not args.real
    
    if run_simple:
        test_analysis_judge()
    
    if args.real:
        test_with_real_document() f"{tracker.session_name}_report.md")
    with open(markdown_output_path, "w") as f:
        f.write(markdown_output)
    
    print(f"Tracking information saved to:")
    print(f"- JSON: {json_output_path}")
    print(f"- Markdown: {markdown_output_path}")
    
    print("\nAnalysis Judge tests completed")

def test_with_real_document():
    """Test the Analysis Judge with a real document from files."""
    print("\n=== Testing Analysis Judge with Real Document ===")
    
    # Check if test file exists
    test_file = "data/dev_eval_files.json"
    if not os.path.exists(test_file):
        print(f"Test file not found: {test_file}")
        return
    
    # Load test document
    try:
        document_text = load_test_document(test_file)
        print(f"Loaded document with {len(document_text)} characters")
    except Exception as e:
        print(f"Error loading test document: {e}")
        return
    
    # Ask if user wants to proceed (this could be expensive with a large document)
    proceed = input("\nThis will run a full analysis on a potentially large document. Proceed? (y/n): ").lower() == 'y'
    
    if not proceed:
        print("Test cancelled")
        return
    
    # Initialize a tracker for all agents
    tracker = AgentTracker(session_name=f"real_doc_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    
    # Create output directory if it doesn't exist
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Process the document
    processed_text = process_document(document_text)
    
    print("Initializing agents...")
    
    # Initialize agents
    boundary_agent = BoundaryDetectiveAgent()
    boundary_agent.set_tracker(tracker)
    
    document_agent = DocumentAnalyzerAgent()
    document_agent.set_tracker(tracker)
    
    summarization_agent = SummarizationManagerAgent()
    summarization_agent.set_tracker(tracker)
    
    analysis_judge = AnalysisJudgeAgent()
    analysis_judge.set_tracker(tracker)
    
    print("Running boundary detection...")
    boundary_analysis = boundary_agent.detect_boundaries(processed_text)
    
    print("Running document classification...")
    document_classification = boundary_agent.classify_document_segments(processed_text, boundary_analysis)
    
    print("Computing document metrics...")
    document_metrics = document_agent.compute_document_metrics(processed_text)
    
    print("Generating summaries...")
    multi_strategy_summary = summarization_agent.generate_all_summaries(processed_text)
    
    print("Running analysis judge synthesis...")
    synthesis = analysis_judge.synthesize_analysis(
        processed_text,
        boundary_analysis,
        document_classification,
        document_metrics,
        multi_strategy_summary
    )
    
    # Export tracking data
    json_output_path = os.path.join(output_dir, f"{tracker.session_name}_tracking.json")
    tracker.export_json(json_output_path)
    
    markdown_output = tracker.generate_markdown()
    markdown_output_path = os.path.join(output_dir, f"{tracker.session_name}_report.md")