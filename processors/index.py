# processors/index.py
"""
Index processor for the RAG Showdown.

This module handles vector database management, providing a unified
interface for storing, retrieving, and searching document embeddings.
"""

import os
import json
import logging
import time
import numpy as np
from typing import List, Dict, Any, Union, Optional, Tuple
import uuid
from dataclasses import dataclass, field
from datetime import datetime

# For ChromaDB integration
try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class IndexEntry:
    """Class representing an entry in the vector index."""
    id: str
    text: str
    embedding: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)
    

    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary representation."""
        return {
            "id": self.id,
            "text": self.text,
            "embedding": self.embedding,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IndexEntry':
        """Create entry from dictionary representation."""
        return cls(
            id=data["id"],
            text=data["text"],
            embedding=data["embedding"],
            metadata=data.get("metadata", {})
        )

class IndexProcessor:
    """
    Processor for managing vector database operations.
    Supports in-memory index, file-based persistence, and ChromaDB integration.
    """
    
    def __init__(self, 
        persistent_dir: str = "data/index",
        collection_name: str = "document_chunks",
        embedding_dimension: int = 1536,
        use_chroma: bool = True):
        """
        Initialize the index processor.
        
        Args:
            persistent_dir: Directory for persistent storage
            collection_name: Name of the vector collection
            embedding_dimension: Dimension of embedding vectors
            use_chroma: Whether to use ChromaDB (if available)
        """
        self.persistent_dir = persistent_dir
        self.collection_name = collection_name
        self.embedding_dimension = embedding_dimension
        self.use_chroma = use_chroma and CHROMA_AVAILABLE
        
        # Create persistent directory if it doesn't exist
        os.makedirs(persistent_dir, exist_ok=True)
        
        # Initialize index
        self.entries = {}  # Local in-memory cache
        self.chroma_client = None
        self.collection = None
        
        # Initialize appropriate backend
        if self.use_chroma:
            self._init_chroma()
        else:
            self._init_file_based()
            
        logger.info(f"Initialized IndexProcessor with backend: {'ChromaDB' if self.use_chroma else 'File-based'}, collection: {collection_name}")
    
    def _init_chroma(self):
        """Initialize ChromaDB client and collection."""
        try:
            chroma_path = os.path.join(self.persistent_dir, "chroma")
            os.makedirs(chroma_path, exist_ok=True)
            
            self.chroma_client = chromadb.PersistentClient(
                path=chroma_path,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Get or create collection
            try:
                self.collection = self.chroma_client.get_collection(self.collection_name)
                logger.info(f"Loaded existing ChromaDB collection: {self.collection_name}")
            except:
                self.collection = self.chroma_client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "Document chunks for RAG Showdown"}
                )
                logger.info(f"Created new ChromaDB collection: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {e}")
            self.use_chroma = False
            self._init_file_based()
    
    def _init_file_based(self):
        """Initialize file-based index."""
        index_file = os.path.join(self.persistent_dir, f"{self.collection_name}.json")
        
        if os.path.exists(index_file):
            try:
                with open(index_file, 'r') as f:
                    data = json.load(f)
                
                # Load entries
                for entry_data in data.get("entries", []):
                    entry = IndexEntry.from_dict(entry_data)
                    self.entries[entry.id] = entry
                
                logger.info(f"Loaded {len(self.entries)} entries from file-based index")
            
            except Exception as e:
                logger.error(f"Error loading index from file: {e}")
                self.entries = {}
    
    def _save_file_based(self):
        """Save index to file."""
        if not self.use_chroma:
            index_file = os.path.join(self.persistent_dir, f"{self.collection_name}.json")
            
            try:
                data = {
                    "metadata": {
                        "collection_name": self.collection_name,
                        "last_updated": datetime.now().isoformat(),
                        "entry_count": len(self.entries)
                    },
                    "entries": [entry.to_dict() for entry in self.entries.values()]
                }
                
                with open(index_file, 'w') as f:
                    json.dump(data, f, indent=2)
                
                logger.info(f"Saved {len(self.entries)} entries to file-based index")
            
            except Exception as e:
                logger.error(f"Error saving index to file: {e}")
    
    def add_entries(self, 
                   texts: List[str], 
                   embeddings: List[List[float]], 
                   metadatas: List[Dict[str, Any]] = None) -> List[str]:
        """
        Add multiple entries to the index.
        
        Args:
            texts: List of text strings
            embeddings: List of embedding vectors
            metadatas: List of metadata dictionaries (optional)
            
        Returns:
            List of entry IDs
        """
        if len(texts) != len(embeddings):
            raise ValueError("Number of texts must match number of embeddings")
        
        if metadatas is None:
            metadatas = [{} for _ in texts]
        elif len(metadatas) != len(texts):
            raise ValueError("Number of metadatas must match number of texts")
        
        # Generate IDs for new entries
        ids = [str(uuid.uuid4()) for _ in texts]
        
        # Add to appropriate backend
        if self.use_chroma:
            try:
                self.collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=texts,
                    metadatas=metadatas
                )
            except Exception as e:
                logger.error(f"Error adding entries to ChromaDB: {e}")
                # Fall back to file-based storage on error
                for i in range(len(texts)):
                    self.entries[ids[i]] = IndexEntry(
                        id=ids[i],
                        text=texts[i],
                        embedding=embeddings[i],
                        metadata=metadatas[i]
                    )
                self._save_file_based()
        else:
            # Add to in-memory index
            for i in range(len(texts)):
                self.entries[ids[i]] = IndexEntry(
                    id=ids[i],
                    text=texts[i],
                    embedding=embeddings[i],
                    metadata=metadatas[i]
                )
            
            # Save to file
            self._save_file_based()
        
        logger.info(f"Added {len(texts)} entries to index")
        return ids
    
    def add_entry(self, 
                 text: str, 
                 embedding: List[float], 
                 metadata: Dict[str, Any] = None) -> str:
        """
        Add a single entry to the index.
        
        Args:
            text: Document text
            embedding: Embedding vector
            metadata: Optional metadata
            
        Returns:
            Entry ID
        """
        return self.add_entries(
            texts=[text],
            embeddings=[embedding],
            metadatas=[metadata or {}]
        )[0]
    
    def query(self, 
             query_embedding: List[float], 
             top_k: int = 5, 
             filter_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Query the index for entries similar to the query embedding.
        
        Args:
            query_embedding: Embedding vector to query with
            top_k: Number of results to return
            filter_metadata: Optional metadata filter
            
        Returns:
            List of matching entries with similarity scores
        """
        if self.use_chroma:
            try:
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    where=filter_metadata
                )
                
                # Format results to match our standard format
                formatted_results = []
                
                if results.get("ids") and results["ids"][0]:
                    for i in range(len(results["ids"][0])):
                        entry_id = results["ids"][0][i]
                        document = results["documents"][0][i] if results.get("documents") else None
                        metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
                        distance = results["distances"][0][i] if results.get("distances") else None
                        
                        # Convert distance to similarity score (ChromaDB returns distance, not similarity)
                        # Different distance measures need different conversions
                        similarity = 1.0 - min(1.0, max(0.0, distance)) if distance is not None else None
                        
                        formatted_results.append({
                            "id": entry_id,
                            "text": document,
                            "metadata": metadata,
                            "similarity": similarity
                        })
                
                return formatted_results
            
            except Exception as e:
                logger.error(f"Error querying ChromaDB: {e}")
                # Fall back to in-memory search on error
        
        # File-based/in-memory search
        if not self.entries:
            return []
        
        results = []
        
        for entry_id, entry in self.entries.items():
            # Apply metadata filter if provided
            if filter_metadata:
                skip = False
                for k, v in filter_metadata.items():
                    if entry.metadata.get(k) != v:
                        skip = True
                        break
                if skip:
                    continue
            
            # Calculate similarity
            similarity = self._cosine_similarity(query_embedding, entry.embedding)
            
            results.append({
                "id": entry_id,
                "text": entry.text,
                "metadata": entry.metadata,
                "similarity": similarity
            })
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x["similarity"], reverse=True)
        
        # Return top k results
        return results[:top_k]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        # Convert to numpy arrays
        a = np.array(vec1)
        b = np.array(vec2)
        
        # Handle zero vectors
        if np.all(a == 0) or np.all(b == 0):
            return 0.0
        
        # Calculate cosine similarity
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    def get_entry(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific entry by ID.
        
        Args:
            entry_id: ID of the entry to retrieve
            
        Returns:
            Entry data or None if not found
        """
        if self.use_chroma:
            try:
                results = self.collection.get(ids=[entry_id])
                
                if results.get("ids") and results["ids"]:
                    return {
                        "id": results["ids"][0],
                        "text": results["documents"][0] if results.get("documents") else None,
                        "metadata": results["metadatas"][0] if results.get("metadatas") else {}
                    }
                return None
                
            except Exception as e:
                logger.error(f"Error retrieving entry from ChromaDB: {e}")
                # Fall back to in-memory retrieval
        
        # In-memory retrieval
        entry = self.entries.get(entry_id)
        if entry:
            return {
                "id": entry.id,
                "text": entry.text,
                "metadata": entry.metadata,
                "embedding": entry.embedding
            }
        
        return None
    
    def delete_entry(self, entry_id: str) -> bool:
        """
        Delete an entry from the index.
        
        Args:
            entry_id: ID of the entry to delete
            
        Returns:
            True if successful, False otherwise
        """
        if self.use_chroma:
            try:
                self.collection.delete(ids=[entry_id])
                return True
            except Exception as e:
                logger.error(f"Error deleting entry from ChromaDB: {e}")
                # Fall back to in-memory deletion
        
        # In-memory deletion
        if entry_id in self.entries:
            del self.entries[entry_id]
            self._save_file_based()
            return True
        
        return False
    
    def clear_index(self) -> bool:
        """
        Clear all entries from the index.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.use_chroma:
                self.collection.delete(ids=self.collection.get()["ids"])
            
            self.entries = {}
            self._save_file_based()
            
            logger.info("Cleared index")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing index: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the index.
        
        Returns:
            Dictionary of statistics
        """
        stats = {
            "collection_name": self.collection_name,
            "backend": "ChromaDB" if self.use_chroma else "File-based",
            "embedding_dimension": self.embedding_dimension,
            "persistent_dir": self.persistent_dir
        }
        
        if self.use_chroma:
            try:
                collection_data = self.collection.get()
                stats["entry_count"] = len(collection_data.get("ids", []))
            except Exception as e:
                logger.error(f"Error getting ChromaDB stats: {e}")
                stats["entry_count"] = "Error"
        else:
            stats["entry_count"] = len(self.entries)
        
        return stats
    
    def build_index_from_embeddings(self, 
                                   embedded_chunks: List[Dict[str, Any]]) -> List[str]:
        """
        Build index from pre-computed embeddings.
        
        Args:
            embedded_chunks: List of dictionaries with text, embedding, and metadata
            
        Returns:
            List of entry IDs
        """
        # Extract data from embedded chunks
        texts = []
        embeddings = []
        metadatas = []
        
        for chunk in embedded_chunks:
            texts.append(chunk["text"])
            embeddings.append(chunk["embedding"])
            
            # Include all metadata except the embedding itself
            metadata = {k: v for k, v in chunk.items() 
                       if k not in ["text", "embedding", "embedding_model"]}
            
            # Include embedding model as metadata
            if "embedding_model" in chunk:
                metadata["embedding_model"] = chunk["embedding_model"]
                
            metadatas.append(metadata)
        
        # Add entries to index
        return self.add_entries(texts, embeddings, metadatas)