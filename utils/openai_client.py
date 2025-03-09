# utils/openai_client.py
"""
OpenAI API client wrapper for Agentic Explorer.
Provides standardized access to OpenAI models with error handling and retry logic.
"""

import os
import time
import logging
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OpenAIClient:
    """Wrapper for OpenAI API client with error handling and standardized access."""
    
    def __init__(self, api_key=None, model="gpt-3.5-turbo"):
        """
        Initialize the OpenAI client.
        
        Args:
            api_key (str, optional): OpenAI API key. Defaults to environment variable.
            model (str, optional): Default model to use. Defaults to "gpt-3.5-turbo".
        """
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set it as the OPENAI_API_KEY environment variable or pass it to the constructor.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.default_model = model
        logger.info(f"Initialized OpenAI client with model {model}")
    
    def generate_completion(self, prompt, system_message=None, model=None, max_tokens=None, temperature=0.7, retry_count=3):
        """
        Generate a completion using the OpenAI API.
        
        Args:
            prompt (str): The prompt to generate a completion for
            system_message (str, optional): System message for the model
            model (str, optional): Model to use. Defaults to the instance default.
            max_tokens (int, optional): Maximum tokens to generate
            temperature (float, optional): Sampling temperature. Defaults to 0.7.
            retry_count (int, optional): Number of retries on failure. Defaults to 3.
            
        Returns:
            str: The generated completion
        """
        model = model or self.default_model
        messages = []
        
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        messages.append({"role": "user", "content": prompt})
        
        for attempt in range(retry_count):
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"Error generating completion (attempt {attempt+1}/{retry_count}): {e}")
                if attempt < retry_count - 1:
                    # Exponential backoff with jitter
                    sleep_time = (2 ** attempt) + (0.1 * attempt)
                    logger.info(f"Retrying in {sleep_time:.2f} seconds...")
                    time.sleep(sleep_time)
                else:
                    raise
    
    def estimate_token_count(self, text):
        """
        Estimate the number of tokens in a text.
        This is a rough estimate: ~4 chars per token for English text.
        
        Args:
            text (str): The text to estimate tokens for
            
        Returns:
            int: Estimated token count
        """
        return len(text) // 4

    def get_openai_client(model="gpt-3.5-turbo"):
        """
        Get an instance of the OpenAI client.
        
        Args:
            model (str, optional): Default model to use. Defaults to "gpt-3.5-turbo".
            
        Returns:
            OpenAIClient: Configured client instance
        """
        return OpenAIClient(model=model)

    def estimate_token_count(self, text):
        """
        Estimate the number of tokens in a text.
        This is a rough estimate: ~4 chars per token for English text.
        
        Args:
            text (str): The text to estimate tokens for
            
        Returns:
            int: Estimated token count
        """
        return len(text) // 4
        
    def get_embedding(self, text, model="text-embedding-ada-002"):
        """
        Generate an embedding for the given text.
        
        Args:
            text (str): The text to generate an embedding for
            model (str, optional): Embedding model to use. Defaults to "text-embedding-ada-002".
            
        Returns:
            list: The embedding vector
        """
        try:
            response = self.client.embeddings.create(
                model=model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def get_embeddings(self, texts, model="text-embedding-ada-002"):
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts (list): List of texts to generate embeddings for
            model (str, optional): Embedding model to use. Defaults to "text-embedding-ada-002".
            
        Returns:
            list: List of embedding vectors
        """
        try:
            response = self.client.embeddings.create(
                model=model,
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise