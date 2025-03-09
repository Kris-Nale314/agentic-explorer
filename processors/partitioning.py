# processors/partitioning_strategies.py
"""
Strategies for partitioning documents into meaningful segments.
"""

import re
import logging
from processors.document_analyzer import DocumentAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DocumentPartitioner:
    """Partitions documents into meaningful segments using various strategies."""
    
    def __init__(self):
        """Initialize the DocumentPartitioner."""
        self.analyzer = DocumentAnalyzer()
    
    def partition_by_paragraph_groups(self, text, min_group_size=3):
        """
        Partition document by grouping paragraphs.
        
        Args:
            text (str): The document text
            min_group_size (int, optional): Minimum paragraphs per group. Defaults to 3.
            
        Returns:
            list: List of text segments
        """
        paragraphs = re.split(r'\n\s*\n', text)
        
        if len(paragraphs) <= min_group_size:
            return [text]  # Return the whole text if it's too short
            
        segments = []
        for i in range(0, len(paragraphs), min_group_size):
            group = paragraphs[i:i+min_group_size]
            segments.append('\n\n'.join(group))
            
        return segments
    
    def partition_by_detected_boundaries(self, text):
        """
        Partition document using boundary detection.
        
        Args:
            text (str): The document text
            
        Returns:
            list: List of text segments
        """
        # Get comprehensive boundary analysis
        analysis = self.analyzer.analyze_document_boundaries(text)
        
        # Extract boundary positions
        try:
            boundaries = analysis.get('boundaries', [])
            positions = [b.get('position', 0) for b in boundaries if isinstance(b, dict)]
            
            # Add start and end positions
            positions = [0] + sorted(positions) + [len(text)]
            
            # Create segments
            segments = []
            for i in range(len(positions) - 1):
                start = positions[i]
                end = positions[i + 1]
                segment = text[start:end].strip()
                if segment:  # Only add non-empty segments
                    segments.append(segment)
                    
            return segments if segments else [text]  # Return original if no valid segments
            
        except Exception as e:
            logger.error(f"Error partitioning by detected boundaries: {e}")
            # Fall back to paragraph grouping
            return self.partition_by_paragraph_groups(text)
    
    def partition_by_entity_mentions(self, text):
        """
        Partition document based on main entity mentions.
        
        Args:
            text (str): The document text
            
        Returns:
            dict: Dictionary mapping entities to relevant text segments
        """
        # Get comprehensive boundary analysis to identify entities
        analysis = self.analyzer.analyze_document_boundaries(text)
        
        try:
            entities = analysis.get('entities', [])
            if not entities:
                return {"full_document": text}
                
            # Split into paragraphs for entity analysis
            paragraphs = re.split(r'\n\s*\n', text)
            entity_segments = {entity: [] for entity in entities}
            
            # Scan paragraphs for entity mentions
            for para in paragraphs:
                for entity in entities:
                    if re.search(r'\b' + re.escape(entity) + r'\b', para, re.IGNORECASE):
                        entity_segments[entity].append(para)
            
            # Join paragraphs for each entity
            for entity in entity_segments:
                entity_segments[entity] = '\n\n'.join(entity_segments[entity])
                
            return entity_segments
            
        except Exception as e:
            logger.error(f"Error partitioning by entity mentions: {e}")
            return {"full_document": text}