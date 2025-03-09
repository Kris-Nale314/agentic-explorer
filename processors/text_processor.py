# processors/text_processor.py
"""
Text preprocessing utilities for document analysis.
"""

import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_text(text):
    """
    Clean text by removing excessive whitespace and normalizing line endings.
    
    Args:
        text (str): The text to clean
        
    Returns:
        str: The cleaned text
    """
    # Replace multiple newlines with double newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Replace multiple spaces with a single space
    text = re.sub(r' {2,}', ' ', text)
    # Trim whitespace
    text = text.strip()
    return text

def extract_code_blocks(text):
    """
    Extract code blocks from markdown or text.
    
    Args:
        text (str): The document text
        
    Returns:
        list: List of extracted code blocks
    """
    # Find code blocks demarcated by triple backticks
    code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', text, re.DOTALL)
    return code_blocks

def detect_language(text):
    """
    Attempt to detect the predominant language of the text.
    
    Args:
        text (str): The document text
        
    Returns:
        str: Detected language code
    """
    try:
        # This is a placeholder - in a real implementation, you might use a library like langdetect
        # For now, we'll just assume English
        return "en"
    except Exception as e:
        logger.warning(f"Language detection failed: {e}")
        return "en"  # Default to English

def tokenize_simple(text):
    """
    Simple word and sentence tokenization.
    
    Args:
        text (str): The document text
        
    Returns:
        dict: Dictionary with 'words' and 'sentences' lists
    """
    # Simple sentence splitting on period, question mark, or exclamation point followed by space and capital letter
    sentences = re.split(r'[.!?]\s+(?=[A-Z])', text)
    
    # Simple word tokenization
    words = re.findall(r'\b\w+\b', text.lower())
    
    return {
        "words": words,
        "sentences": sentences
    }

def process_document(text):
    """
    Process a document for analysis.
    
    Args:
        text (str): The document text
        
    Returns:
        dict: Processed document with metadata
    """
    if not text:
        logger.warning("Empty document received for processing")
        return {"text": "", "metadata": {}}
    
    # Clean the text
    cleaned_text = clean_text(text)
    
    # Extract basic metadata
    tokens = tokenize_simple(cleaned_text)
    word_count = len(tokens["words"])
    sentence_count = len(tokens["sentences"])
    
    # Detect language
    language = detect_language(cleaned_text)
    
    # Extract any code blocks
    code_blocks = extract_code_blocks(cleaned_text)
    
    return {
        "text": cleaned_text,
        "metadata": {
            "word_count": word_count,
            "sentence_count": sentence_count,
            "language": language,
            "has_code": len(code_blocks) > 0,
            "code_block_count": len(code_blocks)
        }
    }