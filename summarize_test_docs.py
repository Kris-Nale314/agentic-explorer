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
    
    # Initialize processors
    summarizer = SummarizationProcessor()
    
    # Import chunking processor here to avoid circular imports
    from processors.chunking import ChunkingProcessor
    chunking_processor = ChunkingProcessor()
    
    # Start timing
    start_time = time.time()
    
    # Generate different summary types
    results = {}
    
    # Check if text is very long
    original_length = len(text)
    is_long_document = original_length > 15000
    
    # Store document info
    results["document_info"] = {
        "length": original_length,
        "is_long_document": is_long_document
    }
    
    # For long documents, use boundary-aware chunking
    document_chunks = []
    boundaries = []
    chunking_metrics = {}
    
    if is_long_document:
        logger.info(f"Long document detected ({original_length} chars), applying boundary-aware chunking")
        
        # Use our ChunkingProcessor to intelligently chunk the document
        chunking_result = chunking_processor.chunk_document(
            text=text,
            strategy="boundary_aware",
            max_chunk_size=8000  # Large enough for good summaries but small enough for models
        )
        
        document_chunks = chunking_result.get("chunks", [])
        boundaries = chunking_result.get("boundaries", [])
        chunking_metrics = chunking_result.get("metrics", {})
        
        logger.info(f"Document divided into {len(document_chunks)} boundary-aware chunks")
        
        # Store chunking information
        results["chunking_info"] = {
            "strategy": "boundary_aware",
            "chunk_count": len(document_chunks),
            "metrics": chunking_metrics,
            "boundary_count": len(boundaries)
        }
    else:
        # For shorter documents, still capture boundary information for analysis
        # but don't chunk for processing
        logger.info(f"Standard-length document, detecting boundaries without chunking")
        boundaries = chunking_processor.detect_document_boundaries(text)
        document_chunks = [chunking_processor.Chunk(text=text, start_idx=0, end_idx=len(text))]
        
        results["chunking_info"] = {
            "strategy": "no_chunking",
            "boundary_count": len(boundaries)
        }
    
    # 1. Basic concise summary - different approach based on document length
    logger.info("Generating basic concise summary")
    try:
        if is_long_document:
            # For long documents, summarize each chunk, then summarize the summaries
            chunk_summaries = []
            
            for i, chunk in enumerate(document_chunks):
                logger.info(f"Summarizing chunk {i+1}/{len(document_chunks)}")
                chunk_summary = summarizer.basic_summary(chunk.text, style="concise")
                if "summary" in chunk_summary:
                    chunk_summaries.append(chunk_summary["summary"])
            
            # Create a combined text from all chunk summaries
            combined_summary_text = "\n\n".join([
                f"Section {i+1}:\n{summary}" 
                for i, summary in enumerate(chunk_summaries)
            ])
            
            # Generate a meta-summary of all chunk summaries
            meta_summary = summarizer.basic_summary(
                combined_summary_text,
                style="concise",
                max_length=300  # Keep meta-summary reasonably sized
            )
            
            # Store both the meta-summary and individual chunk summaries
            basic_summary = {
                "summary": meta_summary.get("summary", ""),
                "chunk_summaries": chunk_summaries,
                "method": "hierarchical_summary",
                "word_count": len(meta_summary.get("summary", "").split()),
                "processed_chunks": len(document_chunks),
                "model": meta_summary.get("model", summarizer.default_model)
            }
        else:
            # For standard documents, use regular summary
            basic_summary = summarizer.basic_summary(text, style="concise")
        
    except Exception as e:
        logger.error(f"Error generating basic summary: {e}")
        basic_summary = {"error": str(e), "method": "basic_concise", "model": summarizer.default_model}
    
    results["basic_concise"] = basic_summary
    
    # 2. Entity-focused summary - use boundary-aware approach for long documents
    logger.info("Generating entity-focused summary")
    try:
        if is_long_document:
            # Extract entities from each chunk
            all_entities = set()
            chunk_entity_summaries = {}
            
            for i, chunk in enumerate(document_chunks):
                logger.info(f"Extracting entities from chunk {i+1}/{len(document_chunks)}")
                entity_result = summarizer.entity_focused_summary(chunk.text)
                
                if "entities" in entity_result:
                    # Add new entities to our set
                    all_entities.update(entity_result.get("entities", []))
                    
                    # Save the summary for this chunk
                    if "summary" in entity_result:
                        chunk_entity_summaries[i] = {
                            "summary": entity_result["summary"],
                            "entities": entity_result.get("entities", [])
                        }
            
            # Convert entity set to sorted list
            entity_list = sorted(list(all_entities))
            
            # Generate a combined entity-focused summary
            if entity_list and chunk_entity_summaries:
                combined_text = "Key entities in this document:\n"
                combined_text += ", ".join(entity_list)
                combined_text += "\n\nEntity information from document sections:\n\n"
                
                for i, entity_data in chunk_entity_summaries.items():
                    combined_text += f"Section {i+1}:\n{entity_data['summary']}\n\n"
                
                # Generate a meta-summary focused on entities
                meta_entity_summary = summarizer.entity_focused_summary(combined_text)
                
                entity_summary = {
                    "summary": meta_entity_summary.get("summary", ""),
                    "entities": entity_list,
                    "entity_count": len(entity_list),
                    "chunk_summaries": chunk_entity_summaries,
                    "method": "hierarchical_entity_summary",
                    "model": meta_entity_summary.get("model", summarizer.default_model)
                }
            else:
                # Fallback if entity extraction failed
                entity_summary = {
                    "error": "Failed to extract entities from chunks",
                    "method": "entity_focused",
                    "model": summarizer.default_model
                }
        else:
            # For standard documents, use regular entity summary
            entity_summary = summarizer.entity_focused_summary(text)
        
    except Exception as e:
        logger.error(f"Error generating entity summary: {e}")
        entity_summary = {"error": str(e), "method": "entity_focused", "model": summarizer.default_model}
    
    results["entity_focused"] = entity_summary
    
    # 3. Temporal summary - similar boundary-aware approach
    logger.info("Generating temporal summary")
    try:
        if is_long_document:
            # Extract time periods from each chunk
            all_time_periods = set()
            chunk_temporal_summaries = {}
            
            for i, chunk in enumerate(document_chunks):
                logger.info(f"Extracting temporal information from chunk {i+1}/{len(document_chunks)}")
                temporal_result = summarizer.temporal_summary(chunk.text)
                
                if "time_periods" in temporal_result:
                    # Add new time periods to our set
                    all_time_periods.update(temporal_result.get("time_periods", []))
                    
                    # Save the summary for this chunk
                    if "summary" in temporal_result:
                        chunk_temporal_summaries[i] = {
                            "summary": temporal_result["summary"],
                            "time_periods": temporal_result.get("time_periods", [])
                        }
            
            # Convert time periods set to sorted list
            time_period_list = sorted(list(all_time_periods))
            
            # Generate a combined temporal summary
            if time_period_list and chunk_temporal_summaries:
                combined_text = "Time periods in this document:\n"
                combined_text += ", ".join(time_period_list)
                combined_text += "\n\nChronological information from document sections:\n\n"
                
                for i, temporal_data in chunk_temporal_summaries.items():
                    combined_text += f"Section {i+1}:\n{temporal_data['summary']}\n\n"
                
                # Generate a meta-summary with chronological focus
                meta_temporal_summary = summarizer.temporal_summary(combined_text)
                
                temporal_summary = {
                    "summary": meta_temporal_summary.get("summary", ""),
                    "time_periods": time_period_list,
                    "period_count": len(time_period_list),
                    "chunk_summaries": chunk_temporal_summaries,
                    "method": "hierarchical_temporal_summary",
                    "model": meta_temporal_summary.get("model", summarizer.default_model)
                }
            else:
                # Fallback if temporal extraction failed
                temporal_summary = {
                    "error": "Failed to extract time periods from chunks",
                    "method": "temporal",
                    "model": summarizer.default_model
                }
        else:
            # For standard documents, use regular temporal summary
            temporal_summary = summarizer.temporal_summary(text)
        
    except Exception as e:
        logger.error(f"Error generating temporal summary: {e}")
        temporal_summary = {"error": str(e), "method": "temporal", "model": summarizer.default_model}
    
    results["temporal"] = temporal_summary
    
    # 4. Extractive summary - leverage boundary information
    logger.info("Generating extractive summary")
    try:
        if is_long_document:
            # Get important sentences from each chunk
            all_extractive_sentences = []
            
            for i, chunk in enumerate(document_chunks):
                logger.info(f"Extracting key sentences from chunk {i+1}/{len(document_chunks)}")
                
                # Use a lower ratio for each chunk to keep total reasonable
                chunk_ratio = min(0.1, 500 / max(1, len(chunk.text)))
                extractive_result = summarizer.extractive_summary(chunk.text, ratio=chunk_ratio)
                
                if "summary" in extractive_result:
                    # Mark which chunk this came from
                    marked_summary = f"\nFrom section {i+1}:\n{extractive_result['summary']}"
                    all_extractive_sentences.append(marked_summary)
            
            # Combine extractive summaries but limit total length
            combined_extractive_text = "\n".join(all_extractive_sentences)
            
            # If still too long, use the summary processor to extract most important parts
            if len(combined_extractive_text) > 6000:
                extractive_meta = summarizer.extractive_summary(
                    combined_extractive_text,
                    ratio=6000 / max(1, len(combined_extractive_text))
                )
                final_extractive_text = extractive_meta.get("summary", combined_extractive_text)
            else:
                final_extractive_text = combined_extractive_text
            
            extractive_summary = {
                "summary": final_extractive_text,
                "method": "boundary_aware_extractive",
                "extracted_from_chunks": len(document_chunks),
                "model": summarizer.default_model
            }
        else:
            # For standard documents, use regular extractive summary
            extractive_summary = summarizer.extractive_summary(text)
        
    except Exception as e:
        logger.error(f"Error generating extractive summary: {e}")
        extractive_summary = {"error": str(e), "method": "extractive", "model": summarizer.default_model}
    
    results["extractive"] = extractive_summary
    
    # Calculate total processing time
    total_time = time.time() - start_time
    results["total_processing_time"] = total_time
    
    # Generate markdown report
    md_content = generate_markdown_report(text, results, boundaries, document_chunks)
    
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

def generate_markdown_report(original_text: str, results: Dict[str, Any], 
                       boundaries=None, document_chunks=None) -> str:
    """
    Generate a markdown report of summarization results.
    
    Args:
        original_text: Original document text
        results: Summarization results
        boundaries: Detected document boundaries
        document_chunks: Document chunks used for processing
        
    Returns:
        Markdown content
    """
    md_lines = []
    
    # Add title and introduction
    md_lines.append("# Document Analysis and Summary Report\n")
    md_lines.append(f"*Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}*\n")
    
    # Document statistics
    md_lines.append("## Document Statistics\n")
    md_lines.append(f"- **Document Length**: {len(original_text):,} characters\n")
    md_lines.append(f"- **Word Count**: Approximately {len(original_text.split()):,} words\n")
    md_lines.append(f"- **Processing Time**: {results.get('total_processing_time', 0):.2f} seconds\n")
    
    # Add boundary-aware processing information if available
    chunking_info = results.get("chunking_info", {})
    document_info = results.get("document_info", {})
    
    if document_info.get("is_long_document", False):
        md_lines.append("\n## 🔍 Boundary-Aware Processing Applied\n")
        
        md_lines.append("This document was processed using intelligent boundary detection and chunking:\n")
        
        # Show chunking strategy details
        if chunking_info:
            md_lines.append(f"- **Chunking Strategy**: {chunking_info.get('strategy', 'boundary_aware').replace('_', ' ').title()}\n")
            md_lines.append(f"- **Chunks Created**: {chunking_info.get('chunk_count', len(document_chunks) if document_chunks else 0)}\n")
            md_lines.append(f"- **Boundaries Detected**: {chunking_info.get('boundary_count', len(boundaries) if boundaries else 0)}\n")
        
        # Add boundary preservation metrics if available
        metrics = chunking_info.get("metrics", {})
        if metrics and "boundary_preservation_score" in metrics:
            score = metrics["boundary_preservation_score"]
            md_lines.append(f"- **Boundary Preservation Score**: {score:.2f} ")
            if score > 0.9:
                md_lines.append("(Excellent)\n")
            elif score > 0.7:
                md_lines.append("(Good)\n")
            else:
                md_lines.append("(Moderate)\n")
                
        if document_chunks and len(document_chunks) > 1:
            md_lines.append("\nEach chunk was processed independently to preserve context, then results were combined.\n")
    
    # Basic concise summary
    basic_summary = results.get("basic_concise", {})
    if "summary" in basic_summary:
        md_lines.append("\n## Executive Summary\n")
        md_lines.append(basic_summary["summary"])
        
        # Add method information
        if basic_summary.get("method", "") == "hierarchical_summary":
            md_lines.append("\n*Generated using hierarchical boundary-aware summarization*\n")
        else:
            md_lines.append(f"\n*Word count: {basic_summary.get('word_count', 'N/A')}*\n")
        
        # Add chunk summary info if available
        if "chunk_summaries" in basic_summary and basic_summary.get("processed_chunks", 0) > 1:
            md_lines.append("\n<details>")
            md_lines.append("<summary><b>Section-by-Section Summaries</b> (Click to expand)</summary>\n")
            
            for i, summary in enumerate(basic_summary["chunk_summaries"]):
                md_lines.append(f"\n### Section {i+1} Summary\n")
                md_lines.append(f"{summary}\n")
            
            md_lines.append("</details>\n")
    elif "error" in basic_summary:
        md_lines.append("\n## Executive Summary\n")
        md_lines.append("*Error generating summary: The document may be too large for standard processing.*\n")
        md_lines.append("*This illustrates why intelligent document handling is necessary for RAG systems.*\n")
    
    # Entity-focused summary
    entity_summary = results.get("entity_focused", {})
    if "summary" in entity_summary:
        md_lines.append("\n## Key Entities and Their Context\n")
        md_lines.append(entity_summary["summary"])
        
        # Add method information
        if entity_summary.get("method", "") == "hierarchical_entity_summary":
            md_lines.append("\n*Generated using boundary-aware entity extraction and analysis*\n")
        
        # List detected entities
        entities = entity_summary.get("entities", [])
        if entities:
            md_lines.append("\n### Detected Key Entities\n")
            for entity in entities:
                md_lines.append(f"- {entity}\n")
            
        # Add chunk summary info if available
        if "chunk_summaries" in entity_summary:
            md_lines.append("\n<details>")
            md_lines.append("<summary><b>Entity Analysis by Section</b> (Click to expand)</summary>\n")
            
            for i, (chunk_idx, data) in enumerate(entity_summary["chunk_summaries"].items()):
                md_lines.append(f"\n### Section {chunk_idx+1} Entity Analysis\n")
                md_lines.append(f"{data['summary']}\n")
                
                if "entities" in data and data["entities"]:
                    md_lines.append("\nEntities in this section:\n")
                    md_lines.append(", ".join(data["entities"]))
                    md_lines.append("\n")
            
            md_lines.append("</details>\n")
    elif "error" in entity_summary:
        md_lines.append("\n## Key Entities and Their Context\n")
        md_lines.append("*Error generating entity summary: The document may be too complex for standard entity extraction.*\n")
    
    # Temporal summary
    temporal_summary = results.get("temporal", {})
    if "summary" in temporal_summary:
        md_lines.append("\n## Chronological Analysis\n")
        md_lines.append(temporal_summary["summary"])
        
        # Add method information
        if temporal_summary.get("method", "") == "hierarchical_temporal_summary":
            md_lines.append("\n*Generated using boundary-aware temporal analysis*\n")
        
        # List detected time periods
        time_periods = temporal_summary.get("time_periods", [])
        if time_periods:
            md_lines.append("\n### Detected Time Periods\n")
            for period in time_periods:
                md_lines.append(f"- {period}\n")
                
        # Add chunk summary info if available
        if "chunk_summaries" in temporal_summary:
            md_lines.append("\n<details>")
            md_lines.append("<summary><b>Temporal Analysis by Section</b> (Click to expand)</summary>\n")
            
            for i, (chunk_idx, data) in enumerate(temporal_summary["chunk_summaries"].items()):
                md_lines.append(f"\n### Section {chunk_idx+1} Temporal Analysis\n")
                md_lines.append(f"{data['summary']}\n")
                
                if "time_periods" in data and data["time_periods"]:
                    md_lines.append("\nTime periods in this section:\n")
                    md_lines.append(", ".join(data["time_periods"]))
                    md_lines.append("\n")
            
            md_lines.append("</details>\n")
    elif "error" in temporal_summary:
        md_lines.append("\n## Chronological Analysis\n")
        md_lines.append("*Error generating temporal summary: The document may be too complex for standard temporal analysis.*\n")
    
    # Extractive summary
    extractive_summary = results.get("extractive", {})
    if "summary" in extractive_summary:
        md_lines.append("\n## Key Statements\n")
        
        if extractive_summary.get("method", "") == "boundary_aware_extractive":
            md_lines.append("The following statements represent the most important information from each section of the document:\n")
        else:
            md_lines.append("The following statements represent the most important information in the document:\n")
            
        md_lines.append(extractive_summary["summary"])
        
        # Add method information
        if extractive_summary.get("method", "") == "boundary_aware_extractive":
            md_lines.append("\n*Generated using boundary-aware extractive summarization*\n")
    elif "error" in extractive_summary:
        md_lines.append("\n## Key Statements\n")
        md_lines.append("*Error generating extractive summary: The document may be too large for standard extraction.*\n")
    
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
    
    # Size complexity
    if len(original_text) > 50000:
        size_complexity = "Very High"
    elif len(original_text) > 15000:
        size_complexity = "High"
    elif len(original_text) > 5000:
        size_complexity = "Medium"
    else:
        size_complexity = "Low"
    md_lines.append(f"- **Size Complexity**: {size_complexity} ({len(original_text):,} characters)\n")
    
    # Boundary complexity - new!
    if boundaries:
        boundary_count = len(boundaries)
        if boundary_count > 10:
            boundary_complexity = "Very High"
        elif boundary_count > 5:
            boundary_complexity = "High"
        elif boundary_count > 2:
            boundary_complexity = "Medium"
        else:
            boundary_complexity = "Low"
        md_lines.append(f"- **Structural Complexity**: {boundary_complexity} ({boundary_count} document boundaries detected)\n")
    
    # Overall assessment
    md_lines.append("\n## RAG Strategy Recommendations\n")
    recommendations = []
    
    # Size-based recommendations
    if len(original_text) > 15000:
        recommendations.append("- **Boundary-Aware Chunking**: This document benefits significantly from intelligent chunking.")
        recommendations.append("- **Hierarchical Processing**: Process the document in stages to maintain coherence between sections.")
    
    if entity_count > 3:
        recommendations.append("- **Entity-Aware Retrieval**: Use entity tracking to properly disambiguate multiple entities.")
    
    if time_period_count > 1:
        recommendations.append("- **Temporal Tracking**: Implement chronological awareness to maintain temporal consistency.")
    
    if boundaries and len(boundaries) > 5:
        recommendations.append("- **Structure Preservation**: Respect document structure when processing to maintain context.")
        recommendations.append("- **Multi-Agent Synthesis**: Use specialized agents for different document sections or topics.")
    
    if document_info.get("is_long_document", False):
        recommendations.append("- **Context Management**: Use techniques that preserve context across document sections.")
        recommendations.append("- **Agentic Coordination**: Employ agents to handle different aspects of the document.")
    
    md_lines.extend(recommendations)
    
    # Add a demonstration of boundary detection
    if boundaries and len(boundaries) > 0:
        md_lines.append("\n## 📊 Document Boundary Analysis\n")
        md_lines.append("The following boundaries were detected in your document:\n")
        
        # Show top 5 boundaries
        shown_boundaries = boundaries[:5] if len(boundaries) > 5 else boundaries
        
        md_lines.append("\n| Position | Type | Confidence | Context |\n")
        md_lines.append("|----------|------|------------|----------|\n")
        
        for boundary in shown_boundaries:
            position = boundary.position if hasattr(boundary, "position") else boundary.get("position", "N/A")
            b_type = boundary.boundary_type if hasattr(boundary, "boundary_type") else boundary.get("type", "N/A")
            confidence = boundary.confidence if hasattr(boundary, "confidence") else boundary.get("confidence", "N/A")
            
            # Format confidence if it's a number
            if isinstance(confidence, (int, float)):
                confidence = f"{confidence:.2f}"
                
            # Get context for display
            context = boundary.context if hasattr(boundary, "context") else boundary.get("context", "")
            if context:
                # Truncate and clean context for table display
                context = context.replace("\n", " ").strip()
                if len(context) > 40:
                    context = context[:37] + "..."
            
            md_lines.append(f"| {position} | {b_type} | {confidence} | {context} |\n")
            
        if len(boundaries) > 5:
            md_lines.append(f"\n*...and {len(boundaries) - 5} more boundaries.*\n")
    
    # Add a section about chunks if available
    if document_chunks and len(document_chunks) > 1:
        md_lines.append("\n## 📄 Boundary-Aware Document Chunks\n")
        md_lines.append("The document was divided into these logical chunks for processing:\n")
        
        md_lines.append("\n| Chunk | Length | Start | End | Boundary Type |\n")
        md_lines.append("|-------|--------|-------|-----|---------------|\n")
        
        # Show information about each chunk
        for i, chunk in enumerate(document_chunks):
            length = chunk.length if hasattr(chunk, "length") else len(chunk.text)
            start = chunk.start_idx if hasattr(chunk, "start_idx") else "N/A"
            end = chunk.end_idx if hasattr(chunk, "end_idx") else "N/A"
            
            # Get boundary type if available
            boundary_type = "N/A"
            if hasattr(chunk, "metadata") and chunk.metadata:
                boundary_type = chunk.metadata.get("boundary_type", "N/A")
            
            md_lines.append(f"| {i+1} | {length:,} chars | {start:,} | {end:,} | {boundary_type} |\n")
    
    # Add explanation of why this matters for RAG
    md_lines.append("\n## Why Boundary-Aware Processing Matters for RAG\n")
    md_lines.append("This document demonstrates several key advantages of boundary-aware processing:\n")
    
    md_lines.append("1. **Context Preservation**: Natural document boundaries prevent context from being fragmented\n")
    md_lines.append("2. **Entity Coherence**: Entities are tracked accurately across document sections\n")
    md_lines.append("3. **Temporal Consistency**: Time-based information maintains proper ordering\n")
    md_lines.append("4. **Complete Coverage**: Even long documents can be fully processed without arbitrary truncation\n")
    
    md_lines.append("\nAgentic RAG with boundary awareness addresses the core limitations of traditional RAG systems.\n")
    
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