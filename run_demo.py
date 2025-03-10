"""
CLI runner for the RAG Showdown.

Provides a command-line interface for running the RAG comparison.
"""

import os
import sys
import argparse
import logging
import time
from typing import Dict, Any
import textwrap
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from orchestration import run_rag_showdown, create_demo_session
from processors.summarize import SummarizationProcessor
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

# Initialize Rich console
console = Console()

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
    parser.add_argument("--summaries", "-s", action="store_true",
                        help="Generate multiple summary types to showcase document structure")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show more detailed output")
    
    return parser.parse_args()

def show_document_understanding(document_text, verbose=False):
    """
    Generate and display document understanding insights.
    
    Args:
        document_text: Document text to analyze
        verbose: Whether to show more detailed output
        
    Returns:
        Dict with document understanding results
    """
    console.print(Panel("[bold blue]📄 Document Understanding Phase[/bold blue]", 
                       subtitle="Analyzing document structure and content"))
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}[/bold blue]"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Analyzing document structure...", total=100)
        
        # Initialize summarization processor
        summarizer = SummarizationProcessor()
        
        # Extract basic summary
        progress.update(task, completed=20, description="Generating concise summary...")
        basic_summary = summarizer.basic_summary(document_text, style="concise")
        
        # Extract entity-focused summary
        progress.update(task, completed=40, description="Identifying key entities...")
        entity_summary = summarizer.entity_focused_summary(document_text)
        
        # Extract temporal summary
        progress.update(task, completed=60, description="Analyzing temporal structure...")
        temporal_summary = summarizer.temporal_summary(document_text)
        
        # Get comprehensive document understanding
        progress.update(task, completed=80, description="Synthesizing document understanding...")
        
        # Complete
        progress.update(task, completed=100, description="Document analysis complete!")
    
    # Display document insights
    console.print("\n[bold]Document Overview:[/bold]")
    if "summary" in basic_summary:
        # Show truncated summary
        summary_text = basic_summary["summary"]
        if len(summary_text) > 300 and not verbose:
            summary_text = summary_text[:300] + "..."
        
        # Format and display summary
        wrapped_summary = textwrap.fill(summary_text, width=100)
        console.print(Panel(wrapped_summary, title="Document Summary", border_style="blue"))
    
    # Display entity insights
    if "entities" in entity_summary:
        console.print("\n[bold]Key Entities:[/bold]")
        entities = entity_summary.get("entities", [])
        console.print(", ".join(f"[bold cyan]{entity}[/bold cyan]" for entity in entities))
    
    # Display temporal insights
    if "time_periods" in temporal_summary and temporal_summary["time_periods"]:
        console.print("\n[bold]Temporal Structure:[/bold]")
        time_periods = temporal_summary.get("time_periods", [])
        console.print(", ".join(f"[bold green]{period}[/bold green]" for period in time_periods))
    
    # Display document complexity
    console.print("\n[bold]Document Complexity Analysis:[/bold]")
    complexity_factors = []
    
    if entity_summary.get("entities") and len(entity_summary["entities"]) > 1:
        complexity_factors.append(f"Multiple entities ({len(entity_summary['entities'])})")
    
    if temporal_summary.get("time_periods") and len(temporal_summary["time_periods"]) > 1:
        complexity_factors.append(f"Multiple time periods ({len(temporal_summary['time_periods'])})")
    
    if basic_summary.get("word_count", 0) > 1000:
        complexity_factors.append("Long document")
    
    if not complexity_factors:
        complexity_factors.append("Simple document structure")
    
    for factor in complexity_factors:
        console.print(f"• {factor}")
    
    console.print("\n[bold blue]→ This document complexity affects how chunking and retrieval should be performed[/bold blue]")
    
    # Return results for further use
    return {
        "basic_summary": basic_summary,
        "entity_summary": entity_summary,
        "temporal_summary": temporal_summary
    }

def display_rag_comparison_results(results, verbose=False):
    """
    Display RAG comparison results in a user-friendly way.
    
    Args:
        results: Results from run_rag_showdown
        verbose: Whether to show more detailed output
    """
    console.print(Panel("[bold green]🚀 RAG Showdown Results[/bold green]", 
                       subtitle=f"Processing time: {results.get('total_processing_time', 0):.2f} seconds"))
    
    # Print chunking comparison
    if "chunking_results" in results and "chunking_comparison" in results["chunking_results"]:
        comparison = results["chunking_results"]["chunking_comparison"]
        if "comparison" in comparison and "overall_ranking" in comparison["comparison"]:
            console.print("\n[bold]Chunking Strategy Comparison:[/bold]")
            
            ranking = comparison["comparison"]["overall_ranking"]
            for i, (strategy, score) in enumerate(ranking):
                if i == 0:
                    console.print(f"🥇 [bold green]{strategy}[/bold green] (score: {score:.2f})")
                elif i == 1:
                    console.print(f"🥈 [bold]{strategy}[/bold] (score: {score:.2f})")
                else:
                    console.print(f"• {strategy} (score: {score:.2f})")
            
            # Show boundary preservation stats
            if "metrics_comparison" in comparison["comparison"]:
                metrics = comparison["comparison"]["metrics_comparison"]
                if "boundary_preservation_score" in metrics:
                    console.print("\n[bold]Boundary Preservation Scores:[/bold]")
                    
                    boundary_scores = metrics["boundary_preservation_score"]
                    for strategy, score in boundary_scores.items():
                        color = "green" if score > 0.8 else "yellow" if score > 0.5 else "red"
                        console.print(f"• {strategy}: [bold {color}]{score:.2f}[/bold {color}]")
    
    # Print retrieval comparison
    if "retrieval_results" in results:
        console.print("\n[bold]Retrieval Method Comparison:[/bold]")
        
        for strategy, strategy_results in results["retrieval_results"].items():
            if "comparison" in strategy_results and "summary" in strategy_results["comparison"]:
                summary = strategy_results["comparison"]["summary"]
                
                console.print(f"[bold]Strategy: {strategy}[/bold]")
                if "fastest_method" in summary:
                    console.print(f"⚡ Fastest method: [bold cyan]{summary['fastest_method']}[/bold cyan]")
                
                if "most_unique_method" in summary:
                    console.print(f"🔍 Most unique results: [bold magenta]{summary['most_unique_method']}[/bold magenta]")
    
    # Print synthesis comparison
    if "synthesis_results" in results and "synthesis_comparison" in results["synthesis_results"]:
        comparison = results["synthesis_results"]["synthesis_comparison"]
        if "comparison" in comparison and "analysis" in comparison["comparison"]:
            analysis = comparison["comparison"]["analysis"]
            
            console.print("\n[bold]Synthesis Method Comparison:[/bold]")
            
            if "overall_best_method" in analysis:
                console.print(f"🏆 Best overall method: [bold green]{analysis['overall_best_method']}[/bold green]")
                
                if "reasoning" in analysis:
                    console.print(f"   Reason: {analysis['reasoning']}")
            
            # Show rankings if available
            if "factual_completeness_ranking" in analysis:
                console.print(f"\n📊 Most factually complete: [bold]{analysis['factual_completeness_ranking'][0]}[/bold]")
    
    # Print final summary
    console.print("\n[bold]Key Findings:[/bold]")
    
    # Determine if agentic approach was better
    agentic_wins = 0
    traditional_wins = 0
    
    # Check chunking winner
    if "chunking_results" in results and "chunking_comparison" in results["chunking_results"]:
        comparison = results["chunking_results"]["chunking_comparison"]
        if "comparison" in comparison and "overall_ranking" in comparison["comparison"]:
            top_strategy = comparison["comparison"]["overall_ranking"][0][0]
            if "Boundary" in top_strategy or "semantic" in top_strategy.lower():
                agentic_wins += 1
                console.print("✅ Agentic chunking outperformed traditional fixed-size chunking")
            else:
                traditional_wins += 1
                console.print("• Traditional chunking performed well for this document")
    
    # Check synthesis winner  
    if "synthesis_results" in results and "synthesis_comparison" in results["synthesis_results"]:
        comparison = results["synthesis_results"]["synthesis_comparison"]
        if "comparison" in comparison and "analysis" in comparison["comparison"]:
            analysis = comparison["comparison"]["analysis"]
            if "overall_best_method" in analysis:
                best_method = analysis["overall_best_method"]
                if "multi" in best_method.lower() or "entity" in best_method.lower():
                    agentic_wins += 1
                    console.print("✅ Agentic synthesis produced more comprehensive results")
                else:
                    traditional_wins += 1
                    console.print("• Traditional synthesis was sufficient for this document")
    
    # Overall verdict
    console.print("\n[bold]Verdict:[/bold]")
    if agentic_wins > traditional_wins:
        console.print(Panel("[bold green]Agentic RAG outperformed Traditional RAG[/bold green]\n" +
                          "The document's complexity benefited from intelligent processing", 
                          border_style="green"))
    elif traditional_wins > agentic_wins:
        console.print(Panel("[bold blue]Traditional RAG was sufficient for this document[/bold blue]\n" +
                          "The document's simplicity didn't require advanced techniques", 
                          border_style="blue"))
    else:
        console.print(Panel("[bold yellow]Mixed results between Traditional and Agentic RAG[/bold yellow]\n" +
                          "Each approach had strengths for different aspects of this document", 
                          border_style="yellow"))
    
    # Note about detailed results
    console.print(f"\nDetailed results saved to: [bold]{results.get('report_file')}[/bold]")

def main():
    """Main entry point for the script."""
    args = parse_arguments()
    
    console.print(Panel("[bold]🚀 RAG Showdown: Traditional vs. Agentic RAG[/bold]", 
                       subtitle="Comparing intelligent vs. traditional approaches"))
    
    try:
        # Load document
        document_path = args.document or Config.TEST_DATA_FILE
        console.print(f"\nAnalyzing document: [bold]{document_path}[/bold]")
        
        # Load the document text for analysis
        from orchestration import load_document
        document_text = load_document(document_path)
        
        # Document understanding phase
        document_insights = None
        if args.summaries:
            document_insights = show_document_understanding(document_text, verbose=args.verbose)
        
        # Query setup
        query = args.query
        if not query and document_insights and "basic_summary" in document_insights:
            # Generate query based on document content
            summary = document_insights["basic_summary"].get("summary", "")
            entities = document_insights["entity_summary"].get("entities", [])
            
            if entities and len(entities) >= 2:
                # Create query comparing entities
                query = f"Compare {entities[0]} and {entities[1]} based on the document."
            elif summary:
                # Create general query
                query = f"What are the main topics discussed in this document?"
        
        if query:
            console.print(f"\nUsing query: [bold cyan]{query}[/bold cyan]")
        
        # Run analysis
        console.print("\n[bold]Running RAG Showdown Analysis...[/bold]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}[/bold blue]"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Starting analysis...", total=100)
            
            # Run in appropriate mode
            if args.demo:
                progress.update(task, description="Running in demo mode...")
                results = create_demo_session(
                    document_path=document_path,
                    output_dir=args.output,
                    query=query
                )
            else:
                # Run with progress updates
                def progress_callback(stage, percent):
                    progress.update(task, completed=percent, description=f"Running {stage}...")
                
                # Run standard analysis
                results = run_rag_showdown(
                    file_path=document_path,
                    query=query,
                    output_dir=args.output,
                    progress_callback=progress_callback,
                    document_insights=document_insights
                )
            
            # Complete progress
            progress.update(task, completed=100, description="Analysis complete!")
        
        # Display results
        display_rag_comparison_results(results, verbose=args.verbose)
        
        return 0
        
    except Exception as e:
        logger.error(f"Error running RAG Showdown: {e}", exc_info=True)
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())