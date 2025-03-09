# processors/document_analyzer.py
"""
Document analyzer for computing metrics and detecting document structure.
"""

import re
import nltk
import logging
from collections import Counter
from utils.openai_client import get_openai_client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
    nltk.download('maxent_ne_chunker', quiet=True)
    nltk.download('words', quiet=True)
except Exception as e:
    logger.warning(f"Could not download NLTK data: {e}")

class DocumentAnalyzer:
    """Analyzes documents to extract metrics and detect boundaries."""
    
    def __init__(self):
        """Initialize the DocumentAnalyzer."""
        self.openai_client = get_openai_client()
    
    def compute_basic_metrics(self, text):
        """
        Compute basic metrics for the document.
        
        Args:
            text (str): The document text
            
        Returns:
            dict: Dictionary of metrics
        """
        # Word count (simple approximation)
        words = re.findall(r'\b\w+\b', text)
        word_count = len(words)
        
        # Sentence count
        try:
            sentences = nltk.sent_tokenize(text)
            sentence_count = len(sentences)
        except:
            # Fallback if NLTK fails
            sentence_count = text.count('.') + text.count('!') + text.count('?')
        
        # Paragraph count (approximation)
        paragraphs = re.split(r'\n\s*\n', text)
        paragraph_count = len(paragraphs)
        
        # Estimate page count (approximation: ~500 words per page)
        page_count = max(1, round(word_count / 500))
        
        # Estimate token count
        token_count = self.openai_client.estimate_token_count(text)
        
        # Most frequent words (excluding common stopwords)
        stopwords = set(['the', 'and', 'a', 'to', 'of', 'in', 'is', 'that', 'it', 'for', 'on', 'with', 'as', 'be', 'at', 'this', 'by', 'from'])
        word_freq = Counter([word.lower() for word in words if word.lower() not in stopwords])
        most_common_words = word_freq.most_common(10)
        
        return {
            "word_count": word_count,
            "sentence_count": sentence_count,
            "paragraph_count": paragraph_count,
            "page_count": page_count,
            "estimated_token_count": token_count,
            "most_common_words": most_common_words
        }
    
    def detect_potential_boundaries(self, text, min_paragraph_length=100):
        """
        Detect potential document boundaries using basic NLP techniques.
        
        Args:
            text (str): The document text
            min_paragraph_length (int, optional): Minimum paragraph length to consider. Defaults to 100.
            
        Returns:
            list: List of dictionaries with boundary information
        """
        # Split into paragraphs
        paragraphs = re.split(r'\n\s*\n', text)
        
        boundaries = []
        prev_entities = set()
        prev_dates = set()
        
        # Process each paragraph
        char_position = 0
        
        for i, para in enumerate(paragraphs):
            if len(para) < min_paragraph_length:
                char_position += len(para) + 2  # +2 for the newlines
                continue
                
            # Extract entities using NLTK
            try:
                sentences = nltk.sent_tokenize(para)
                words = [nltk.word_tokenize(sentence) for sentence in sentences]
                pos_tags = [nltk.pos_tag(word) for word in words]
                
                # Extract named entities
                entities = set()
                for sentence_tags in pos_tags:
                    for chunk in nltk.ne_chunk(sentence_tags):
                        if hasattr(chunk, 'label'):
                            entity_name = ' '.join(c[0] for c in chunk)
                            entities.add(entity_name)
                
                # Simple date detection (can be improved)
                date_pattern = r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}\b'
                dates = set(re.findall(date_pattern, para, re.IGNORECASE))
                
                # Add year detection
                year_pattern = r'\b20\d{2}\b'
                years = set(re.findall(year_pattern, para))
                dates.update(years)
                
                # Check for potential boundary
                if prev_entities and entities and len(entities.intersection(prev_entities)) < 0.3 * min(len(entities), len(prev_entities)):
                    # Low entity overlap suggests a boundary
                    boundaries.append({
                        "position": char_position,
                        "type": "entity_shift",
                        "confidence": "medium",
                        "prev_entities": list(prev_entities),
                        "current_entities": list(entities),
                        "context": para[:100] + "..."
                    })
                
                if prev_dates and dates and not prev_dates.intersection(dates):
                    # Different dates suggests a boundary
                    boundaries.append({
                        "position": char_position,
                        "type": "temporal_shift",
                        "confidence": "medium",
                        "prev_dates": list(prev_dates),
                        "current_dates": list(dates),
                        "context": para[:100] + "..."
                    })
                
                # Update for next iteration
                prev_entities = entities
                prev_dates = dates
                
            except Exception as e:
                logger.warning(f"Error processing paragraph {i}: {e}")
            
            char_position += len(para) + 2  # +2 for the newlines
        
        return boundaries
    
    def generate_summary(self, text, approach="standard", max_length=None):
        """
        Generate a summary of the document using OpenAI.
        
        Args:
            text (str): The document text
            approach (str, optional): Summarization approach. Options:
                - "standard": Standard summarization
                - "entity_focused": Focus on specific entities
                - "temporal": Organize by time periods
            max_length (int, optional): Maximum summary length in words
            
        Returns:
            str: The generated summary
        """
        # Add length constraint if specified
        length_constraint = f"Keep your summary under {max_length} words." if max_length else ""
        
        if approach == "standard":
            prompt = f"""
            Please provide a concise summary of the following text. Focus on the key points and main ideas.
            {length_constraint}
            
            TEXT:
            {text}
            """
        
        elif approach == "entity_focused":
            prompt = f"""
            Please provide a summary of the following text, organized by the main entities (companies, people, organizations) mentioned.
            For each key entity, summarize what the text says about them.
            {length_constraint}
            
            TEXT:
            {text}
            """
        
        elif approach == "temporal":
            prompt = f"""
            Please provide a summary of the following text, organized chronologically by time periods mentioned.
            Identify different time frames discussed and summarize what happened in each period.
            {length_constraint}
            
            TEXT:
            {text}
            """
        
        else:
            raise ValueError(f"Unknown summarization approach: {approach}")
        
        try:
            return self.openai_client.generate_completion(prompt)
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return f"Error generating summary: {e}"
    
    def analyze_document_boundaries(self, text):
        """
        Use OpenAI to analyze document boundaries in a comprehensive way.
        
        Args:
            text (str): The document text
            
        Returns:
            dict: Dictionary with boundary analysis
        """
        system_message = """
        You are an expert document analyst specialized in identifying boundaries between different documents that have been combined into a single text.
        
        Your task is to carefully analyze the provided text and determine where one document ends and another begins.
        
        Look for these signals:
        - Abrupt topic changes
        - Shifts in writing style or formatting
        - Changes in document type (e.g., from transcript to news article)
        - Temporal discontinuities (dates/times that don't follow in sequence)
        - Entity switches (different companies being discussed)
        - Discourse markers indicating endings or beginnings
        
        Provide your analysis in a structured JSON format with these fields:
        - "boundaries": array of detected boundaries with positions, context, and confidence
        - "document_types": array of detected document types with descriptions
        - "entities": key entities mentioned across the document
        - "time_periods": key time periods mentioned
        - "confidence_score": your overall confidence in the boundary detection (0-10)
        """
        
        prompt = f"""
        Analyze the following text to identify boundaries between potentially different documents that have been combined.
        
        TEXT:
        {text}
        
        Return your analysis as structured JSON with the fields described in your instructions.
        """
        
        try:
            result = self.openai_client.generate_completion(prompt, system_message=system_message)
            
            # Try to parse as JSON, but handle the case where the model doesn't return valid JSON
            try:
                import json
                return json.loads(result)
            except:
                logger.warning("Could not parse boundary analysis as JSON, returning raw text")
                return {"raw_analysis": result}
                
        except Exception as e:
            logger.error(f"Error analyzing document boundaries: {e}")
            return {"error": str(e)}