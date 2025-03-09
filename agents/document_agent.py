# agents/document_agent.py
"""
Document Analyzer agent - Thin wrapper around DocumentAnalyzer processor.
"""

import logging
import json
from agents.base_agent import BaseAgent
from processors.document_analyzer import DocumentAnalyzer
from processors.text_processor import process_document
from data.content import AGENT_DESCRIPTIONS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DocumentAnalyzerAgent(BaseAgent):
    """Agent that wraps the document analyzer processor."""
    
    def __init__(self, model="gpt-3.5-turbo"):
        """
        Initialize the Document Analyzer agent.
        
        Args:
            model (str, optional): OpenAI model to use. Defaults to "gpt-3.5-turbo".
        """
        # Use agent description from content
        agent_info = AGENT_DESCRIPTIONS.get("document_analyzer", {
            "name": "Document Analyzer",
            "role": "Document Metrics and Structure Analyst",
            "goal": "Compute metrics, extract structures, and identify patterns across documents",
            "backstory": "I specialize in analyzing document structures, calculating metrics, and identifying patterns."
        })
        
        super().__init__(
            name=agent_info.get("name", "Document Analyzer"),
            role=agent_info.get("role", "Document Metrics and Structure Analyst"),
            goal=agent_info.get("goal", "Compute metrics, extract structures, and identify patterns"),
            backstory=agent_info.get("backstory", "I specialize in analyzing document structures."),
            model=model
        )
        
        # Use the processor instead of reimplementing functionality
        self.processor = DocumentAnalyzer()
        logger.info("Document Analyzer agent initialized")
    
    def compute_document_metrics(self, text):
        """Compute comprehensive metrics for a document."""
        reasoning = ["Beginning document metrics computation using processor"]
        
        # Process text if needed
        if isinstance(text, str):
            processed_text = process_document(text)
            text_to_analyze = processed_text if isinstance(processed_text, str) else processed_text.get("text", text)
        else:
            text_to_analyze = text
        
        # Track the activity
        self.track_activity(
            "compute_metrics_start",
            {"document_length": len(text_to_analyze)},
            None,
            reasoning
        )
        
        # Use the processor to compute metrics
        metrics = self.processor.compute_basic_metrics(text_to_analyze)
        
        # Track completion
        self.track_activity(
            "compute_metrics_complete",
            None,
            {"metrics": metrics},
            reasoning + [f"Computed {len(metrics)} metrics"]
        )
        
        return metrics
    
    def analyze_document_boundaries(self, text):
        """Analyze document boundaries."""
        reasoning = ["Beginning boundary analysis using processor"]
        
        # Track the activity
        self.track_activity(
            "boundary_analysis_start",
            {"document_length": len(text)},
            None,
            reasoning
        )
        
        # Use the processor to analyze boundaries
        boundaries = self.processor.analyze_document_boundaries(text)
        
        # Track completion
        self.track_activity(
            "boundary_analysis_complete",
            None,
            {"boundary_count": len(boundaries.get("boundaries", []))},
            reasoning + ["Boundary analysis completed"]
        )
        
        return boundaries
    
    def analyze_document(self, text):
        """Perform comprehensive document analysis."""
        reasoning = ["Beginning comprehensive document analysis"]
        
        # Track start
        self.track_activity(
            "analysis_start",
            {"document_length": len(text)},
            None,
            reasoning
        )
        
        # Compute metrics
        metrics = self.compute_document_metrics(text)
        
        # Analyze boundaries
        boundaries = self.analyze_document_boundaries(text)
        
        # Add educational analysis about what this reveals
        educational_prompt = """
        Based on the document metrics and boundary analysis, explain what this reveals about:
        1. How AI systems process and understand documents
        2. What challenges document structure presents for AI comprehension
        3. Why document boundaries matter for accurate AI analysis
        
        Format your response as JSON with these fields:
        - ai_processing: how AI systems process documents
        - structural_challenges: challenges posed by document structure
        - boundary_importance: why boundaries matter
        - recommendations: how to improve document processing
        """
        
        educational_insights = self.analyze(text, specific_prompt=educational_prompt)
        
        try:
            insights = json.loads(educational_insights)
        except:
            insights = {"raw_insights": educational_insights}
        
        # Combine results
        analysis = {
            "metrics": metrics,
            "boundaries": boundaries,
            "educational_insights": insights
        }
        
        # Track completion
        self.track_activity(
            "analysis_complete",
            None,
            {"analysis_keys": list(analysis.keys())},
            reasoning + ["Analysis completed successfully"]
        )
        
        return analysis