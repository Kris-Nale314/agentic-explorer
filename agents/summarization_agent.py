# agents/summarization_agent.py
"""
Summarization agent - Thin wrapper around SummarizationManager processor.
"""

import logging
import json
from agents.base_agent import BaseAgent
from processors.summarization_manager import SummarizationManager
from processors.text_processor import process_document
from data.content import AGENT_DESCRIPTIONS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SummarizationAgent(BaseAgent):
    """Agent that wraps the summarization manager processor."""
    
    def __init__(self, model="gpt-3.5-turbo"):
        """
        Initialize the Summarization Agent.
        
        Args:
            model (str, optional): OpenAI model to use. Defaults to "gpt-3.5-turbo".
        """
        # Use agent description from content
        agent_info = AGENT_DESCRIPTIONS.get("summarization_manager", {
            "name": "Summarization Manager",
            "role": "Multi-Strategy Summarization Specialist",
            "goal": "Orchestrate and compare multiple summarization strategies",
            "backstory": "I specialize in summarizing documents using different approaches."
        })
        
        super().__init__(
            name=agent_info.get("name", "Summarization Manager"),
            role=agent_info.get("role", "Multi-Strategy Summarization Specialist"),
            goal=agent_info.get("goal", "Orchestrate and compare multiple summarization strategies"),
            backstory=agent_info.get("backstory", "I specialize in summarizing documents."),
            model=model
        )
        
        # Use the processor instead of reimplementing functionality
        self.processor = SummarizationManager()
        logger.info("Summarization Manager agent initialized")
    
    def generate_standard_summary(self, text, max_length=None):
        """Generate a standard summary of the document."""
        reasoning = ["Generating standard summary using processor"]
        
        # Track the activity
        self.track_activity(
            "standard_summary_start",
            {"document_length": len(text), "max_length": max_length},
            None,
            reasoning
        )
        
        # Use the processor to generate the summary
        summary = self.processor.summarize_full_document(text, max_length=max_length)
        
        # Track completion
        self.track_activity(
            "standard_summary_complete",
            None,
            {"summary_type": summary.get("summary_type", "standard")},
            reasoning + ["Standard summary completed"]
        )
        
        return summary
    
    def generate_partitioned_summary(self, text, max_length=None):
        """Generate partition-based summaries."""
        reasoning = ["Generating partition-based summary using processor"]
        
        # Track the activity
        self.track_activity(
            "partitioned_summary_start",
            {"document_length": len(text), "max_length": max_length},
            None,
            reasoning
        )
        
        # Use the processor to generate the summary
        summary = self.processor.summarize_by_partition(text, max_length=max_length)
        
        # Track completion
        self.track_activity(
            "partitioned_summary_complete",
            None,
            {"segment_count": summary.get("segment_count", 0)},
            reasoning + ["Partition-based summary completed"]
        )
        
        return summary
    
    def generate_entity_summary(self, text, max_length=None):
        """Generate entity-focused summaries."""
        reasoning = ["Generating entity-focused summary using processor"]
        
        # Track the activity
        self.track_activity(
            "entity_summary_start",
            {"document_length": len(text), "max_length": max_length},
            None,
            reasoning
        )
        
        # Use the processor to generate the summary
        summary = self.processor.summarize_by_entity(text, max_length=max_length)
        
        # Track completion
        self.track_activity(
            "entity_summary_complete",
            None,
            {"entity_count": summary.get("entity_count", 0)},
            reasoning + ["Entity-focused summary completed"]
        )
        
        return summary
    
    def generate_summaries(self, text, max_length=None):
        """Generate summaries using all strategies and compare them."""
        reasoning = ["Beginning multi-strategy summarization"]
        
        # Track start
        self.track_activity(
            "multi_strategy_start",
            {"document_length": len(text), "max_length": max_length},
            None,
            reasoning
        )
        
        # Use the processor to generate multi-strategy summaries
        results = self.processor.generate_multi_strategy_summary(text, max_length=max_length)
        
        # Add educational analysis about summarization approaches
        educational_prompt = """
        Based on the multi-strategy summarization results, explain:
        1. Why different summarization strategies produce different results
        2. How document structure affects summarization quality
        3. What this reveals about AI's understanding of documents
        
        Format your response as JSON with these fields:
        - strategy_differences: why strategies yield different results
        - structure_impact: how document structure affects summarization
        - ai_understanding: what this reveals about AI comprehension
        - best_practices: recommendations for effective summarization
        """
        
        educational_insights = self.analyze(text, specific_prompt=educational_prompt)
        
        try:
            insights = json.loads(educational_insights)
        except:
            insights = {"raw_insights": educational_insights}
        
        # Add educational insights to results
        results["educational_insights"] = insights
        
        # Track completion
        self.track_activity(
            "multi_strategy_complete",
            None,
            {"result_keys": list(results.keys())},
            reasoning + ["Multi-strategy summarization completed"]
        )
        
        return results