# tests/test_document_analysis.py
"""
Test script for document analysis functionality.
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

from processors.document_analyzer import DocumentAnalyzer
from processors.summarization_manager import SummarizationManager
from orchestration import run_analysis

def test_document_analyzer():
    """Test the DocumentAnalyzer class."""
    print("\n=== Testing DocumentAnalyzer ===")
    
    # Simple test text
    test_text = """
    Apple Inc. reported strong earnings for Q3 2023, with revenue reaching $81.8 billion.
    CEO Tim Cook highlighted the growth in Services, which set another all-time record.
    
    Meanwhile, Microsoft Corporation announced its Q2 2023 results on January 24, 2023,
    with cloud revenue growing 22% year-over-year to $27.1 billion.
    
    Both companies discussed AI investments during their earnings calls.
    """
    
    analyzer = DocumentAnalyzer()
    
    # Test basic metrics
    print("Testing compute_basic_metrics...")
    metrics = analyzer.compute_basic_metrics(test_text)
    print(f"Word count: {metrics['word_count']}")
    print(f"Sentence count: {metrics['sentence_count']}")
    
    # Test boundary detection
    print("\nTesting detect_potential_boundaries...")
    boundaries = analyzer.detect_potential_boundaries(test_text)
    print(f"Detected {len(boundaries)} potential boundaries")
    
    # Test summary generation
    print("\nTesting generate_summary...")
    summary = analyzer.generate_summary(test_text, approach="standard")
    print(f"Summary: {summary}")
    
    print("\nDocumentAnalyzer tests completed")

def test_summarization_manager():
    """Test the SummarizationManager class."""
    print("\n=== Testing SummarizationManager ===")
    
    # Simple test text with multiple entities and potential boundaries
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
    
    manager = SummarizationManager()
    
    # Test full document summarization
    print("Testing summarize_full_document...")
    full_summary = manager.summarize_full_document(test_text)
    print(f"Full document summary: {full_summary.get('summary', 'N/A')[:150]}...")
    
    # Test partition-based summarization
    print("\nTesting summarize_by_partition...")
    partition_summary = manager.summarize_by_partition(test_text)
    print(f"Partition count: {partition_summary.get('segment_count', 'N/A')}")
    print(f"Meta-summary: {partition_summary.get('meta_summary', 'N/A')[:150]}...")
    
    # Test entity-based summarization
    print("\nTesting summarize_by_entity...")
    entity_summary = manager.summarize_by_entity(test_text)
    print(f"Entity count: {entity_summary.get('entity_count', 'N/A')}")
    print(f"Meta-summary: {entity_summary.get('meta_summary', 'N/A')[:150]}...")
    
    print("\nSummarizationManager tests completed")

def test_orchestration():
    """Test the orchestration module with a test file."""
    print("\n=== Testing Orchestration ===")
    
    # Check if test file exists
    test_file = "data/dev_eval_files.json"
    if not os.path.exists(test_file):
        print(f"Test file not found: {test_file}")
        return
    
    # Run basic analysis first (faster)
    print(f"Running basic analysis on {test_file}...")
    basic_results = run_analysis(file_path=test_file, analysis_type="basic")
    
    if "metrics" in basic_results:
        metrics = basic_results["metrics"]
        print("\nDocument Metrics:")
        print(f"- Word count: {metrics.get('word_count', 'N/A')}")
        print(f"- Sentence count: {metrics.get('sentence_count', 'N/A')}")
        print(f"- Estimated token count: {metrics.get('estimated_token_count', 'N/A')}")
    
    # Ask if user wants to run comprehensive analysis (which takes longer)
    run_comprehensive = input("\nRun comprehensive analysis? (y/n): ").lower() == 'y'
    
    if run_comprehensive:
        print(f"Running comprehensive analysis on {test_file}...")
        results = run_analysis(file_path=test_file, analysis_type="comprehensive")
        
        # Save results to a file for inspection
        output_file = "data/test_analysis_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
            
        print(f"Comprehensive analysis complete! Results saved to {output_file}")
        
        if "multi_strategy_summary" in results and "recommended_approach" in results["multi_strategy_summary"]:
            recommendation = results["multi_strategy_summary"]["recommended_approach"]
            print(f"\nRecommended Approach: {recommendation.get('recommended_approach', 'N/A')}")
            print(f"Explanation: {recommendation.get('explanation', 'N/A')}")
    
    print("\nOrchestration tests completed")

if __name__ == "__main__":
    # Run tests based on command line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description='Test document analysis functionality')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    parser.add_argument('--analyzer', action='store_true', help='Test DocumentAnalyzer')
    parser.add_argument('--summarizer', action='store_true', help='Test SummarizationManager')
    parser.add_argument('--orchestration', action='store_true', help='Test Orchestration')
    
    args = parser.parse_args()
    
    # If no specific tests are specified, run all tests
    run_all = args.all or not (args.analyzer or args.summarizer or args.orchestration)
    
    if run_all or args.analyzer:
        test_document_analyzer()
    
    if run_all or args.summarizer:
        test_summarization_manager()
    
    if run_all or args.orchestration:
        test_orchestration()