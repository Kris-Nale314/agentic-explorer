# config.py
"""
Configuration management for the Agentic Explorer application.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration manager for application settings."""
    
    # API Keys
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    FMP_API_KEY = os.environ.get('FMP_API_KEY')
    
    # Default models
    DEFAULT_MODEL = os.environ.get('DEFAULT_MODEL', 'gpt-3.5-turbo')
    
    # Feature flags
    ENABLE_LOGGING = os.environ.get('ENABLE_LOGGING', 'true').lower() == 'true'
    DEBUG_MODE = os.environ.get('DEBUG_MODE', 'false').lower() == 'true'
    
    # Application settings
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    MAX_DOCUMENT_SIZE = int(os.environ.get('MAX_DOCUMENT_SIZE', '100000'))
    MAX_SUMMARY_LENGTH = int(os.environ.get('MAX_SUMMARY_LENGTH', '1000'))
    
    # Paths
    DATA_DIR = os.environ.get('DATA_DIR', 'data')
    TEST_DATA_FILE = os.path.join(DATA_DIR, os.environ.get('TEST_DATA_FILE', 'dev_eval_files.txt'))
    OUTPUT_DIR = os.environ.get('OUTPUT_DIR', 'output')
    
    @classmethod
    def validate(cls):
        """
        Validate the configuration.
        
        Returns:
            tuple: (is_valid, error_message)
        """
        if not cls.OPENAI_API_KEY:
            return False, "OPENAI_API_KEY is required but not set"
            
        if not cls.FMP_API_KEY:
            return False, "FMP_API_KEY is required but not set"
            
        return True, "Configuration is valid"

# Example usage
if __name__ == "__main__":
    is_valid, message = Config.validate()
    if is_valid:
        print("Configuration is valid.")
        print(f"Using OpenAI model: {Config.DEFAULT_MODEL}")
        print(f"Using data directory: {Config.DATA_DIR}")
    else:
        print(f"Configuration error: {message}")