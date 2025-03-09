"""
Embedding processor for the RAG Showdown.

This module handles vector embedding generation for document chunks,
supporting multiple embedding models and batch processing for efficiency.
"""

import os
import time
import logging
import numpy as np
from typing import List, Dict, Any, Union, Optional
from dataclasses import dataclass, field
import json
import hashlib

# For OpenAI embeddings
from utils.openai_client import OpenAIClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class DocumentEmbedding:
    """Class representing an embedding for a document chunk."""
    text: str
    embedding: List[float]
    model: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    text_hash: str = None
    
    def __post_init__(self):
        """Initialize computed fields if not provided."""
        if self.text_hash is None:
            self.text_hash = self._hash_text(self.text)
    
    @staticmethod
    def _hash_text(text: str) -> str:
        """Create a hash of the text for identification and caching."""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert embedding to dictionary representation."""
        return {
            "text": self.text,
            "text_hash": self.text_hash,
            "embedding": self.embedding,
            "model": self.model,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentEmbedding':
        """Create embedding from dictionary representation."""
        return cls(
            text=data["text"],
            embedding=data["embedding"],
            model=data["model"],
            metadata=data.get("metadata", {}),
            text_hash=data.get("text_hash")
        )

class EmbeddingProcessor:
    """
    Processor for generating and managing embeddings for document chunks.
    Supports caching, batch processing, and multiple embedding models.
    """
    
    def __init__(self, 
                 cache_dir: str = "cache/embeddings",
                 default_model: str = "text-embedding-ada-002",
                 batch_size: int = 10):
        """
        Initialize the embedding processor.
        
        Args:
            cache_dir: Directory to cache embeddings
            default_model: Default embedding model to use
            batch_size: Maximum batch size for embedding requests
        """
        self.cache_dir = cache_dir
        self.default_model = default_model
        self.batch_size = batch_size
        self.openai_client = OpenAIClient()
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        
        # Load embedding cache if it exists
        self.embedding_cache = {}
        self._load_cache()
        
        logger.info(f"Initialized EmbeddingProcessor with model {default_model}, cache dir: {cache_dir}")
    
    def _load_cache(self):
        """Load embedding cache from disk."""
        cache_file = os.path.join(self.cache_dir, "embedding_cache.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                # Reconstruct cache
                for model, entries in cache_data.items():
                    self.embedding_cache[model] = {}
                    for text_hash, embedding_data in entries.items():
                        self.embedding_cache[model][text_hash] = embedding_data
                
                logger.info(f"Loaded {sum(len(entries) for entries in self.embedding_cache.values())} cached embeddings")
            except Exception as e:
                logger.warning(f"Error loading embedding cache: {e}")
                self.embedding_cache = {}
    
    def _save_cache(self):
        """Save embedding cache to disk."""
        cache_file = os.path.join(self.cache_dir, "embedding_cache.json")
        try:
            # Prepare cache for serialization (only store embedding and metadata)
            serializable_cache = {}
            for model, entries in self.embedding_cache.items():
                serializable_cache[model] = {}
                for text_hash, embedding_data in entries.items():
                    serializable_cache[model][text_hash] = {
                        "embedding": embedding_data["embedding"],
                        "metadata": embedding_data.get("metadata", {})
                    }
            
            with open(cache_file, 'w') as f:
                json.dump(serializable_cache, f)
            
            logger.info(f"Saved {sum(len(entries) for entries in self.embedding_cache.values())} embeddings to cache")
        except Exception as e:
            logger.warning(f"Error saving embedding cache: {e}")
    
    def _get_from_cache(self, text: str, model: str) -> Optional[List[float]]:
        """
        Try to get embedding from cache.
        
        Args:
            text: Text to find embedding for
            model: Model name
            
        Returns:
            Embedding if found in cache, None otherwise
        """
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        
        # Check if model exists in cache
        if model not in self.embedding_cache:
            return None
        
        # Check if text hash exists for this model
        if text_hash not in self.embedding_cache[model]:
            return None
        
        return self.embedding_cache[model][text_hash]["embedding"]
    
    def _add_to_cache(self, text: str, embedding: List[float], model: str, metadata: Dict[str, Any] = None):
        """
        Add embedding to cache.
        
        Args:
            text: Original text
            embedding: Generated embedding
            model: Model used to generate embedding
            metadata: Optional metadata to store with embedding
        """
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        
        # Initialize model entry if needed
        if model not in self.embedding_cache:
            self.embedding_cache[model] = {}
        
        # Store embedding
        self.embedding_cache[model][text_hash] = {
            "embedding": embedding,
            "metadata": metadata or {}
        }
    
    def generate_embedding(self, 
                          text: str, 
                          model: str = None, 
                          use_cache: bool = True) -> DocumentEmbedding:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            model: Model to use (defaults to self.default_model)
            use_cache: Whether to use the embedding cache
            
        Returns:
            DocumentEmbedding object
        """
        if not text:
            raise ValueError("Cannot generate embedding for empty text")
        
        model = model or self.default_model
        
        # Try to get from cache
        if use_cache:
            cached_embedding = self._get_from_cache(text, model)
            if cached_embedding:
                logger.info(f"Using cached embedding for text ({len(text)} chars)")
                return DocumentEmbedding(
                    text=text,
                    embedding=cached_embedding,
                    model=model
                )
        
        # Generate new embedding
        logger.info(f"Generating embedding for text ({len(text)} chars) using model {model}")
        
        try:
            # Call OpenAI API to get embedding
            embedding = self.openai_client.get_embedding(text, model)
            
            # Add to cache
            if use_cache:
                self._add_to_cache(text, embedding, model)
                # Periodically save cache
                if len(self.embedding_cache.get(model, {})) % 10 == 0:
                    self._save_cache()
            
            return DocumentEmbedding(
                text=text,
                embedding=embedding,
                model=model
            )
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def batch_embed_texts(self, 
                         texts: List[str], 
                         model: str = None, 
                         use_cache: bool = True) -> List[DocumentEmbedding]:
        """
        Generate embeddings for multiple texts in efficient batches.
        
        Args:
            texts: List of texts to embed
            model: Model to use (defaults to self.default_model)
            use_cache: Whether to use the embedding cache
            
        Returns:
            List of DocumentEmbedding objects
        """
        if not texts:
            return []
        
        model = model or self.default_model
        logger.info(f"Batch embedding {len(texts)} texts using model {model}")
        
        # Filter out empty texts
        valid_texts = [text for text in texts if text and text.strip()]
        if len(valid_texts) < len(texts):
            logger.warning(f"Filtered out {len(texts) - len(valid_texts)} empty texts")
        
        # Track texts that need embeddings vs. those in cache
        texts_to_embed = []
        cache_hits = {}
        
        # Check cache first
        if use_cache:
            for i, text in enumerate(valid_texts):
                cached_embedding = self._get_from_cache(text, model)
                if cached_embedding:
                    cache_hits[i] = cached_embedding
                else:
                    texts_to_embed.append((i, text))
            
            logger.info(f"Cache hits: {len(cache_hits)}, texts to embed: {len(texts_to_embed)}")
        else:
            texts_to_embed = [(i, text) for i, text in enumerate(valid_texts)]
        
        # Prepare results (will fill in with cache hits and new embeddings)
        embeddings = [None] * len(valid_texts)
        
        # Add cache hits to results
        for i, embedding in cache_hits.items():
            embeddings[i] = DocumentEmbedding(
                text=valid_texts[i],
                embedding=embedding,
                model=model
            )
        
        # Process remaining texts in batches
        if texts_to_embed:
            for batch_start in range(0, len(texts_to_embed), self.batch_size):
                batch_end = min(batch_start + self.batch_size, len(texts_to_embed))
                batch = texts_to_embed[batch_start:batch_end]
                
                logger.info(f"Processing batch {batch_start//self.batch_size + 1}: {len(batch)} texts")
                
                try:
                    # Extract just the texts for the API call
                    batch_indices = [item[0] for item in batch]
                    batch_texts = [item[1] for item in batch]
                    
                    # Call OpenAI API to get embeddings for batch
                    batch_embeddings = self.openai_client.get_embeddings(batch_texts, model)
                    
                    # Process results
                    for i, (original_idx, text) in enumerate(batch):
                        embedding = batch_embeddings[i]
                        
                        # Add to cache
                        if use_cache:
                            self._add_to_cache(text, embedding, model)
                        
                        # Add to results
                        embeddings[original_idx] = DocumentEmbedding(
                            text=text,
                            embedding=embedding,
                            model=model
                        )
                    
                except Exception as e:
                    logger.error(f"Error in batch embedding: {e}")
                    
                    # Fall back to individual embeddings on batch failure
                    for original_idx, text in batch:
                        try:
                            embedding = self.generate_embedding(text, model, use_cache=use_cache)
                            embeddings[original_idx] = embedding
                        except Exception as e2:
                            logger.error(f"Error in individual embedding fallback: {e2}")
                            # Create empty embedding as placeholder
                            embeddings[original_idx] = DocumentEmbedding(
                                text=text,
                                embedding=[0.0],  # Placeholder
                                model=model,
                                metadata={"error": str(e2)}
                            )
                
                # Save cache periodically
                if use_cache and batch_end % 20 == 0:
                    self._save_cache()
        
        # Save cache after all processing
        if use_cache:
            self._save_cache()
        
        # Filter out any None values (shouldn't happen but just in case)
        return [e for e in embeddings if e is not None]
    
    def embed_chunks(self, 
                    chunks: List, 
                    model: str = None, 
                    use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Generate embeddings for a list of chunks.
        
        Args:
            chunks: List of chunk objects with 'text' attribute
            model: Model to use (defaults to self.default_model)
            use_cache: Whether to use the embedding cache
            
        Returns:
            List of dictionaries with chunk data and embeddings
        """
        chunk_texts = [chunk.text for chunk in chunks]
        chunk_embeddings = self.batch_embed_texts(chunk_texts, model, use_cache)
        
        # Combine chunk data with embeddings
        result = []
        for i, (chunk, embedding) in enumerate(zip(chunks, chunk_embeddings)):
            # Create result with all chunk data plus embedding
            chunk_data = chunk.to_dict() if hasattr(chunk, 'to_dict') else {'text': chunk.text}
            
            # Add embedding data
            chunk_data['embedding'] = embedding.embedding
            chunk_data['embedding_model'] = embedding.model
            
            result.append(chunk_data)
        
        return result
    
    def compute_embedding_similarity(self, 
                                    embedding1: List[float], 
                                    embedding2: List[float]) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity (between -1 and 1)
        """
        # Convert to numpy arrays
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0  # Handle zero vectors
            
        return dot_product / (norm1 * norm2)
    
    def find_similar_chunks(self, 
                           query: str, 
                           chunk_embeddings: List[Dict[str, Any]], 
                           top_k: int = 5, 
                           model: str = None) -> List[Dict[str, Any]]:
        """
        Find chunks most similar to a query text.
        
        Args:
            query: Query text
            chunk_embeddings: List of chunk data with embeddings
            top_k: Number of results to return
            model: Model to use for query embedding
            
        Returns:
            List of chunk data with similarity scores, sorted by similarity
        """
        # Generate embedding for query
        query_embedding = self.generate_embedding(query, model)
        
        # Calculate similarity with each chunk
        results = []
        for chunk_data in chunk_embeddings:
            chunk_embedding = chunk_data['embedding']
            similarity = self.compute_embedding_similarity(query_embedding.embedding, chunk_embedding)
            
            # Create result with similarity score
            result = chunk_data.copy()
            result['similarity'] = similarity
            results.append(result)
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Return top k results
        return results[:top_k]
    
    def embed_document(self, 
                      text: str,
                      chunking_strategy: str = "fixed_size",
                      model: str = None,
                      use_cache: bool = True,
                      **kwargs) -> Dict[str, Any]:
        """
        Process a document end-to-end: chunking and embedding.
        
        Args:
            text: Document text
            chunking_strategy: Strategy for chunking ('fixed_size', 'boundary_aware', etc.)
            model: Embedding model to use
            use_cache: Whether to use the embedding cache
            **kwargs: Additional parameters for chunking
            
        Returns:
            Dictionary with chunks and their embeddings
        """
        from chunking import ChunkingProcessor
        
        # Initialize chunking processor
        chunking_processor = ChunkingProcessor()
        
        # Chunk the document
        chunking_result = chunking_processor.chunk_document(
            text=text,
            strategy=chunking_strategy,
            **kwargs
        )
        
        # Get chunks
        chunks = chunking_result.get('chunks', [])
        
        # Generate embeddings for chunks
        embedded_chunks = self.embed_chunks(chunks, model, use_cache)
        
        # Return results
        return {
            'document_length': len(text),
            'chunking_strategy': chunking_strategy,
            'chunking_metrics': chunking_result.get('metrics', {}),
            'boundaries': chunking_result.get('boundaries', []),
            'embedded_chunks': embedded_chunks
        }
    
    def compare_embedding_models(self, 
                               text: str, 
                               models: List[str],
                               query: str = None) -> Dict[str, Any]:
        """
        Compare different embedding models on the same text.
        
        Args:
            text: Text to embed
            models: List of embedding models to compare
            query: Optional query to test similarity
            
        Returns:
            Comparison results
        """
        results = {
            'text_length': len(text),
            'models_compared': models,
            'embeddings': {},
            'comparison': {}
        }
        
        # Generate embeddings with each model
        for model in models:
            try:
                embedding = self.generate_embedding(text, model, use_cache=True)
                results['embeddings'][model] = {
                    'dimensions': len(embedding.embedding),
                    'model': model
                }
            except Exception as e:
                logger.error(f"Error with model {model}: {e}")
                results['embeddings'][model] = {
                    'error': str(e)
                }
        
        # If query provided, compare similarity across models
        if query:
            results['query'] = query
            results['similarity_scores'] = {}
            
            for model in models:
                try:
                    # Skip models that failed earlier
                    if 'error' in results['embeddings'].get(model, {}):
                        continue
                        
                    # Get embeddings for text and query
                    text_embedding = self.generate_embedding(text, model)
                    query_embedding = self.generate_embedding(query, model)
                    
                    # Calculate similarity
                    similarity = self.compute_embedding_similarity(
                        text_embedding.embedding, 
                        query_embedding.embedding
                    )
                    
                    results['similarity_scores'][model] = similarity
                    
                except Exception as e:
                    logger.error(f"Error calculating similarity with model {model}: {e}")
                    results['similarity_scores'][model] = {
                        'error': str(e)
                    }
        
        return results