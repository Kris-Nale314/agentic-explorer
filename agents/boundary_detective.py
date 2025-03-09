# agents/boundary_detective.py
"""
Boundary Detective agent specializing in detecting document boundaries.
"""

import logging
import json
from agents.base_agent import BaseAgent
from processors.document_analyzer import DocumentAnalyzer
from data.content import SYSTEM_PROMPTS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BoundaryDetectiveAgent(BaseAgent):
    """Agent that specializes in detecting document boundaries."""
    
    def __init__(self, model="gpt-3.5-turbo"):
        """
        Initialize the Boundary Detective agent.
        
        Args:
            model (str, optional): OpenAI model to use. Defaults to "gpt-3.5-turbo".
        """
        # Get agent info from content
        agent_info = {
            "name": "Boundary Detective",
            "role": "Document Boundary Detective",
            "goal": "Accurately identify where different documents are combined and classify each section",
            "backstory": "I'm an expert at analyzing text to find where different documents have been merged together. I can spot changes in style, topic, entities, and temporal references."
        }
        
        super().__init__(
            name=agent_info["name"],
            role=agent_info["role"],
            goal=agent_info["goal"],
            backstory=agent_info["backstory"],
            model=model
        )
        
        self.document_analyzer = DocumentAnalyzer()
        logger.info("Boundary Detective agent initialized")
    
    def get_system_prompt(self):
        """
        Get the specialized system prompt for the Boundary Detective.
        
        Returns:
            str: System prompt
        """
        return SYSTEM_PROMPTS.get("boundary_detector", super().get_system_prompt())
    
    def detect_boundaries(self, text):
        """
        Detect document boundaries in the text.
        
        Args:
            text (str): Text to analyze for boundaries
            
        Returns:
            dict: Boundary detection results
        """
        logger.info("Boundary Detective beginning boundary detection")
        
        # First, use the document analyzer to get potential boundaries
        potential_boundaries = self.document_analyzer.detect_potential_boundaries(text)
        
        # Then, use the AI to do a more comprehensive analysis
        boundary_analysis = self.document_analyzer.analyze_document_boundaries(text)
        
        # Combine the results
        if isinstance(boundary_analysis, dict):
            boundary_analysis["rule_based_boundaries"] = potential_boundaries
        else:
            # Handle case where boundary_analysis is not a dict
            boundary_analysis = {
                "ai_analysis": boundary_analysis,
                "rule_based_boundaries": potential_boundaries
            }
        
        return boundary_analysis
    
    def classify_document_segments(self, text, boundaries):
        """
        Classify each document segment based on boundaries.
        
        Args:
            text (str): The full text
            boundaries (list): List of boundary positions
            
        Returns:
            list: Classification for each segment
        """
        logger.info("Boundary Detective classifying document segments")
        
        # Extract boundaries and sort them
        positions = []
        if isinstance(boundaries, dict) and "boundaries" in boundaries:
            for b in boundaries["boundaries"]:
                if isinstance(b, dict) and "position" in b:
                    positions.append(b["position"])
        
        # If we have no valid positions, try the rule-based boundaries
        if not positions and isinstance(boundaries, dict) and "rule_based_boundaries" in boundaries:
            for b in boundaries["rule_based_boundaries"]:
                if isinstance(b, dict) and "position" in b:
                    positions.append(b["position"])
        
        # Add start and end positions
        positions = [0] + sorted(positions) + [len(text)]
        
        # Create segments
        segments = []
        for i in range(len(positions) - 1):
            start = positions[i]
            end = positions[i + 1]
            segment_text = text[start:end].strip()
            if segment_text:  # Only add non-empty segments
                segments.append({
                    "start_position": start,
                    "end_position": end,
                    "text": segment_text[:500] + "..." if len(segment_text) > 500 else segment_text
                })
        
        # If we have no segments, just use the whole text
        if not segments:
            segments.append({
                "start_position": 0,
                "end_position": len(text),
                "text": text[:500] + "..." if len(text) > 500 else text
            })
        
        # Now classify each segment
        classified_segments = []
        
        for idx, segment in enumerate(segments):
            prompt = f"""
            Please classify the following document segment:
            
            {segment["text"]}
            
            Classify this segment according to:
            1. Document type (e.g., news article, earnings call, financial report, press release, etc.)
            2. Main entities discussed (companies, people, organizations)
            3. Time period covered or referenced
            4. Main topics or themes
            
            Return your analysis in JSON format with these fields:
            - document_type: the type of document
            - entities: array of main entities
            - time_period: the time period covered
            - topics: array of main topics
            - confidence: your confidence in this classification (1-10)
            
            JSON response only:
            """
            
            try:
                response = self.analyze(segment["text"], specific_prompt=prompt)
                
                # Attempt to parse as JSON
                try:
                    classification = json.loads(response)
                except:
                    # If parsing fails, use the raw response
                    classification = {
                        "raw_classification": response,
                        "parse_error": "Could not parse as JSON"
                    }
                
                classified_segment = {
                    "segment_id": idx + 1,
                    "start_position": segment["start_position"],
                    "end_position": segment["end_position"],
                    "length": len(segment["text"]),
                    "preview": segment["text"][:100] + "...",
                    "classification": classification
                }
                
                classified_segments.append(classified_segment)
                
            except Exception as e:
                logger.error(f"Error classifying segment {idx+1}: {e}")
                classified_segments.append({
                    "segment_id": idx + 1,
                    "start_position": segment["start_position"],
                    "end_position": segment["end_position"],
                    "error": str(e)
                })
        
        return classified_segments