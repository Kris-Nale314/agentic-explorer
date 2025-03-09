"""
Text preprocessing utilities for document analysis.
"""

import re

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

def process_document(text):
    """
    Process a document for analysis.
    
    Args:
        text (str): The document text
        
    Returns:
        str: The processed document
    """
    # For now, just do basic cleaning
    # As development progresses, more sophisticated processing can be added
    return clean_text(text)