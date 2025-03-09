# processors/retrieval.py
"""
Retrieval processor for the RAG Showdown.

This module handles document retrieval strategies, including:
1. Traditional vector similarity search
2. Entity-aware retrieval
3. Context-enhanced retrieval with relationship mapping
"""

import re
import logging
import time
from typing import List, Dict, Any, Optional, Tuple, Set
import nltk
from collections import defaultdict

# Import other processors
from processors.embedding import EmbeddingProcessor
from processors.index import IndexProcessor
from utils.openai_client import OpenAIClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure NLTK resources are available
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('averaged_perceptron_tagger')
    nltk.data.find('maxent_ne_chunker')
    nltk.data.find('words')
except LookupError:
    nltk.download('punkt')
    nltk.download('averaged_perceptron_tagger')
    nltk.download('maxent_ne_chunker')
    nltk.download('words')

class RetrievalProcessor:
    """
    Processor for retrieving relevant document chunks using different strategies.
    """
    
    def __init__(self, 
                 embedding_processor: Optional[EmbeddingProcessor] = None,
                 index_processor: Optional[IndexProcessor] = None,
                 default_top_k: int = 5):
        """
        Initialize the retrieval processor.
        
        Args:
            embedding_processor: EmbeddingProcessor instance (created if None)
            index_processor: IndexProcessor instance (created if None)
            default_top_k: Default number of results to return
        """
        self.embedding_processor = embedding_processor or EmbeddingProcessor()
        self.index_processor = index_processor or IndexProcessor()
        self.default_top_k = default_top_k
        self.openai_client = OpenAIClient()
        
        # Cache for entity identification and disambiguation
        self.entity_cache = {}
        
        logger.info(f"Initialized RetrievalProcessor with default top_k={default_top_k}")
    
    def vector_search(self, 
                     query: str, 
                     top_k: Optional[int] = None, 
                     filter_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Perform standard vector similarity search.
        
        Args:
            query: User query string
            top_k: Number of results to return
            filter_metadata: Optional metadata filter
            
        Returns:
            List of matching chunks with similarity scores
        """
        top_k = top_k or self.default_top_k
        
        logger.info(f"Performing vector search for query: '{query}', top_k={top_k}")
        
        # Generate embedding for query
        start_time = time.time()
        query_embedding = self.embedding_processor.generate_embedding(query)
        
        # Query the index
        results = self.index_processor.query(
            query_embedding=query_embedding.embedding,
            top_k=top_k,
            filter_metadata=filter_metadata
        )
        
        search_time = time.time() - start_time
        
        logger.info(f"Vector search found {len(results)} results in {search_time:.2f}s")
        
        # Add search metadata
        for result in results:
            result["retrieval_method"] = "vector_similarity"
            result["search_time_seconds"] = search_time
        
        return results
    
    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract named entities from text.
        
        Args:
            text: Text to extract entities from
            
        Returns:
            List of entity dictionaries with name, type, and positions
        """
        # Check cache first
        cache_key = hash(text)
        if cache_key in self.entity_cache:
            return self.entity_cache[cache_key]
        
        entities = []
        
        # Use NLTK for initial entity extraction
        try:
            sentences = nltk.sent_tokenize(text)
            for sentence in sentences:
                words = nltk.word_tokenize(sentence)
                tagged = nltk.pos_tag(words)
                tree = nltk.ne_chunk(tagged)
                
                for subtree in tree:
                    if hasattr(subtree, 'label'):
                        entity_text = ' '.join(word for word, pos in subtree.leaves())
                        entity_type = subtree.label()
                        
                        # Find position in original text
                        position = text.find(entity_text)
                        
                        entities.append({
                            "name": entity_text,
                            "type": entity_type,
                            "position": position if position != -1 else None
                        })
            
            # Store in cache
            self.entity_cache[cache_key] = entities
            
            return entities
        
        except Exception as e:
            logger.warning(f"Error extracting entities with NLTK: {e}")
            return []
    
    def _extract_entities_with_llm(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract entities using LLM for higher quality.
        
        Args:
            text: Text to extract entities from
            
        Returns:
            List of entity dictionaries
        """
        # Check cache first
        cache_key = hash(text) + 1  # Different from NLTK cache key
        if cache_key in self.entity_cache:
            return self.entity_cache[cache_key]
        
        # For very long texts, sample or chunk
        if len(text) > 4000:
            # Simple approach: take first 4000 chars
            analysis_text = text[:4000]
        else:
            analysis_text = text
        
        prompt = """
        Extract all named entities from the following text. Focus on:
        - Companies and organizations
        - People
        - Products
        - Locations
        - Time periods and dates
        
        For each entity, determine its type and any aliases or references to the same entity.
        
        Return the result as a JSON array with this structure:
        [
            {
                "name": "primary name of entity",
                "type": "ORGANIZATION/PERSON/PRODUCT/LOCATION/TIME",
                "aliases": ["other names or references to this entity"],
                "importance": 1-10 scale of how central this entity is to the text
            }
        ]
        
        Text to analyze:
        """
        
        try:
            result = self.openai_client.generate_completion(prompt + analysis_text)
            
            # Extract JSON from result
            import json
            import re
            
            # Find JSON array in the response
            json_match = re.search(r'\[\s*\{.*\}\s*\]', result, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(0)
                entities = json.loads(json_str)
                
                # Store in cache
                self.entity_cache[cache_key] = entities
                
                return entities
            else:
                logger.warning("Could not extract JSON from LLM entity response")
                return []
                
        except Exception as e:
            logger.error(f"Error extracting entities with LLM: {e}")
            return []
    
    def entity_aware_search(self, 
                           query: str, 
                           top_k: Optional[int] = None,
                           use_llm: bool = True) -> List[Dict[str, Any]]:
        """
        Perform entity-aware search.
        
        Args:
            query: User query string
            top_k: Number of results to return
            use_llm: Whether to use LLM for entity extraction (higher quality)
            
        Returns:
            List of matching chunks with similarity scores
        """
        top_k = top_k or self.default_top_k
        
        logger.info(f"Performing entity-aware search for query: '{query}', top_k={top_k}")
        
        start_time = time.time()
        
        # Extract entities from query
        if use_llm:
            query_entities = self._extract_entities_with_llm(query)
        else:
            query_entities = self._extract_entities(query)
        
        # If no entities found, fall back to vector search
        if not query_entities:
            logger.info("No entities found in query, falling back to vector search")
            results = self.vector_search(query, top_k)
            for result in results:
                result["retrieval_method"] = "entity_aware_fallback"
            return results
        
        # Get primary entity focus
        main_entities = sorted(query_entities, key=lambda e: e.get("importance", 0), reverse=True)
        
        # Generate entity-focused queries
        entity_results = []
        
        for entity in main_entities[:3]:  # Focus on top 3 entities
            entity_name = entity["name"]
            entity_type = entity.get("type", "UNKNOWN")
            
            # Create entity filter
            entity_filter = {
                "contains_entity": entity_name
            }
            
            # Perform vector search with entity focus
            entity_query = f"{query} about {entity_name}"
            
            # Get results for this entity
            entity_search_results = self.vector_search(
                query=entity_query,
                top_k=max(2, top_k // 2),  # Get some results per entity
                filter_metadata=entity_filter
            )
            
            # Add entity info to results
            for result in entity_search_results:
                result["entity_match"] = entity_name
                result["entity_type"] = entity_type
                result["retrieval_method"] = "entity_aware"
            
            entity_results.extend(entity_search_results)
        
        # Remove duplicates (keeping highest similarity)
        seen_ids = set()
        unique_results = []
        
        for result in sorted(entity_results, key=lambda x: x["similarity"], reverse=True):
            if result["id"] not in seen_ids:
                seen_ids.add(result["id"])
                unique_results.append(result)
                
                if len(unique_results) >= top_k:
                    break
        
        # If we don't have enough results, supplement with standard vector search
        if len(unique_results) < top_k:
            remaining = top_k - len(unique_results)
            logger.info(f"Entity search found only {len(unique_results)} results, adding {remaining} from vector search")
            
            # Get IDs to exclude
            exclude_ids = seen_ids
            
            # Get standard results
            standard_results = self.vector_search(query, remaining * 2)
            
            # Filter out duplicates
            for result in standard_results:
                if result["id"] not in exclude_ids and len(unique_results) < top_k:
                    result["retrieval_method"] = "vector_supplementary"
                    unique_results.append(result)
                    exclude_ids.add(result["id"])
        
        search_time = time.time() - start_time
        
        # Add search metadata
        for result in unique_results:
            result["search_time_seconds"] = search_time
        
        logger.info(f"Entity-aware search found {len(unique_results)} results in {search_time:.2f}s")
        
        return unique_results
    
    def _find_related_chunks(self, 
                            chunk_id: str, 
                            all_chunks: List[Dict[str, Any]], 
                            connection_threshold: float = 0.75) -> List[str]:
        """
        Find chunks related to a given chunk based on similarity.
        
        Args:
            chunk_id: ID of the chunk to find relations for
            all_chunks: List of all chunks to search in
            connection_threshold: Similarity threshold for considering chunks related
            
        Returns:
            List of related chunk IDs
        """
        # Find the source chunk
        source_chunk = None
        for chunk in all_chunks:
            if chunk["id"] == chunk_id:
                source_chunk = chunk
                break
        
        if not source_chunk or "embedding" not in source_chunk:
            return []
        
        source_embedding = source_chunk["embedding"]
        
        # Find related chunks
        related_ids = []
        for chunk in all_chunks:
            if chunk["id"] != chunk_id and "embedding" in chunk:
                similarity = self.embedding_processor.compute_embedding_similarity(
                    source_embedding, 
                    chunk["embedding"]
                )
                
                if similarity >= connection_threshold:
                    related_ids.append(chunk["id"])
        
        return related_ids
    
    def context_enhanced_search(self, 
                               query: str, 
                               top_k: Optional[int] = None,
                               depth: int = 1) -> List[Dict[str, Any]]:
        """
        Perform context-enhanced search with relationship mapping.
        
        Args:
            query: User query string
            top_k: Number of results to return
            depth: How many levels of related chunks to include
            
        Returns:
            List of matching chunks with similarity scores and relationships
        """
        top_k = top_k or self.default_top_k
        base_results = min(top_k, 3)  # Start with fewer base results
        
        logger.info(f"Performing context-enhanced search for query: '{query}', top_k={top_k}, depth={depth}")
        
        start_time = time.time()
        
        # Initial vector search
        initial_results = self.vector_search(query, base_results)
        
        # Get all chunks needed for relationship mapping
        all_chunks = []
        seen_ids = set()
        
        # Build a queue of chunks to process, starting with initial results
        chunk_queue = [(chunk["id"], 0) for chunk in initial_results]  # (id, depth)
        
        while chunk_queue:
            current_id, current_depth = chunk_queue.pop(0)
            
            if current_id in seen_ids:
                continue
                
            seen_ids.add(current_id)
            
            # Get the chunk details
            chunk_details = self.index_processor.get_entry(current_id)
            if not chunk_details:
                continue
                
            all_chunks.append(chunk_details)
            
            # If we haven't reached max depth, add related chunks to the queue
            if current_depth < depth:
                # Find chunks related to this one
                related_ids = self._find_related_chunks(current_id, all_chunks)
                
                # Add new related chunks to the queue
                for related_id in related_ids:
                    if related_id not in seen_ids:
                        chunk_queue.append((related_id, current_depth + 1))
        
        # Build relationship graph
        relationships = defaultdict(set)
        
        for chunk in all_chunks:
            related_ids = self._find_related_chunks(chunk["id"], all_chunks)
            relationships[chunk["id"]].update(related_ids)
        
        # Calculate relevance scores taking relationships into account
        relevance_scores = {}
        
        # Generate query embedding
        query_embedding = self.embedding_processor.generate_embedding(query).embedding
        
        # Calculate direct relevance for all chunks
        for chunk in all_chunks:
            if "embedding" in chunk:
                direct_score = self.embedding_processor.compute_embedding_similarity(
                    query_embedding, 
                    chunk["embedding"]
                )
                
                # Start with direct relevance
                relevance_scores[chunk["id"]] = direct_score
        
        # Enhance scores based on relationships
        for _ in range(depth):  # Propagate through the network
            new_scores = relevance_scores.copy()
            
            for chunk_id, related_ids in relationships.items():
                if not related_ids:
                    continue
                    
                # Get boost from related chunks (dampened by relationship distance)
                relationship_boost = sum(relevance_scores.get(related_id, 0) * 0.2 
                                       for related_id in related_ids) / max(1, len(related_ids))
                
                # Apply boost to this chunk's score
                new_scores[chunk_id] = relevance_scores[chunk_id] + relationship_boost
            
            relevance_scores = new_scores
        
        # Format results with enhanced scores
        enhanced_results = []
        
        for chunk in all_chunks:
            # Skip chunks with no relevance score (shouldn't happen but just in case)
            if chunk["id"] not in relevance_scores:
                continue
                
            # Create result with enhanced score
            result = chunk.copy()
            result["similarity"] = relevance_scores[chunk["id"]]
            result["related_chunks"] = list(relationships[chunk["id"]])
            result["retrieval_method"] = "context_enhanced"
            result["relationship_depth"] = len(result["related_chunks"])
            
            enhanced_results.append(result)
        
        # Sort by enhanced relevance and take top_k
        enhanced_results.sort(key=lambda x: x["similarity"], reverse=True)
        final_results = enhanced_results[:top_k]
        
        search_time = time.time() - start_time
        
        # Add search metadata
        for result in final_results:
            result["search_time_seconds"] = search_time
        
        logger.info(f"Context-enhanced search found {len(final_results)} results in {search_time:.2f}s")
        
        return final_results
    
    def hybrid_search(self, 
                     query: str, 
                     top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining vector, entity, and context approaches.
        
        Args:
            query: User query string
            top_k: Number of results to return
            
        Returns:
            List of matching chunks with similarity scores
        """
        top_k = top_k or self.default_top_k
        
        logger.info(f"Performing hybrid search for query: '{query}', top_k={top_k}")
        
        start_time = time.time()
        
        # Run all search methods in parallel (or sequentially for simpler implementation)
        vector_results = self.vector_search(query, top_k)
        entity_results = self.entity_aware_search(query, top_k)
        context_results = self.context_enhanced_search(query, top_k)
        
        # Combine results with method weighting
        # In a real system, these weights would be tuned or adapted per query
        method_weights = {
            "vector_similarity": 1.0,
            "entity_aware": 1.2,      # Prefer entity matches
            "context_enhanced": 1.1,  # Slightly prefer context-enhanced
            "vector_supplementary": 0.9,  # Slightly reduce supplementary matches
            "entity_aware_fallback": 0.95  # Slightly reduce fallbacks
        }
        
        # Combine all results
        all_results = []
        all_results.extend(vector_results)
        all_results.extend(entity_results)
        all_results.extend(context_results)
        
        # Calculate weighted scores and remove duplicates
        weighted_results = {}
        
        for result in all_results:
            result_id = result["id"]
            method = result.get("retrieval_method", "vector_similarity")
            similarity = result.get("similarity", 0.0)
            
            # Apply method weight
            weighted_similarity = similarity * method_weights.get(method, 1.0)
            
            # Keep the highest weighted score for each chunk
            if result_id not in weighted_results or weighted_similarity > weighted_results[result_id]["weighted_similarity"]:
                result_copy = result.copy()
                result_copy["original_similarity"] = similarity
                result_copy["weighted_similarity"] = weighted_similarity
                weighted_results[result_id] = result_copy
        
        # Convert to list and sort by weighted similarity
        final_results = list(weighted_results.values())
        final_results.sort(key=lambda x: x["weighted_similarity"], reverse=True)
        
        # Take top_k results
        final_results = final_results[:top_k]
        
        search_time = time.time() - start_time
        
        # Add search metadata
        for result in final_results:
            result["search_time_seconds"] = search_time
            result["retrieval_method"] = "hybrid"
        
        logger.info(f"Hybrid search found {len(final_results)} results in {search_time:.2f}s")
        
        return final_results
    
    def retrieve(self, 
                query: str, 
                method: str = "vector", 
                top_k: Optional[int] = None, 
                **kwargs) -> Dict[str, Any]:
        """
        Retrieve relevant chunks using the specified method.
        
        Args:
            query: User query string
            method: Retrieval method to use ('vector', 'entity', 'context', 'hybrid')
            top_k: Number of results to return
            **kwargs: Additional parameters for specific retrieval methods
            
        Returns:
            Dictionary with results and metadata
        """
        top_k = top_k or self.default_top_k
        
        logger.info(f"Retrieving chunks for query '{query}' using method '{method}'")
        
        start_time = time.time()
        
        # Select retrieval method
        if method == "vector":
            results = self.vector_search(
                query=query, 
                top_k=top_k, 
                filter_metadata=kwargs.get("filter_metadata")
            )
        elif method == "entity":
            results = self.entity_aware_search(
                query=query, 
                top_k=top_k,
                use_llm=kwargs.get("use_llm", True)
            )
        elif method == "context":
            results = self.context_enhanced_search(
                query=query, 
                top_k=top_k,
                depth=kwargs.get("depth", 1)
            )
        elif method == "hybrid":
            results = self.hybrid_search(
                query=query, 
                top_k=top_k
            )
        else:
            raise ValueError(f"Unknown retrieval method: {method}")
        
        # Format full response
        retrieval_time = time.time() - start_time
        
        response = {
            "query": query,
            "method": method,
            "results": results,
            "result_count": len(results),
            "retrieval_time": retrieval_time,
            "metadata": {
                "top_k": top_k,
                **kwargs
            }
        }
        
        logger.info(f"Retrieved {len(results)} chunks in {retrieval_time:.2f}s using {method} method")
        
        return response
    
    def compare_retrieval_methods(self, 
                                 query: str, 
                                 methods: List[str] = None, 
                                 top_k: Optional[int] = None) -> Dict[str, Any]:
        """
        Compare different retrieval methods on the same query.
        
        Args:
            query: User query string
            methods: List of retrieval methods to compare
            top_k: Number of results to return per method
            
        Returns:
            Dictionary with results for each method and comparison metrics
        """
        methods = methods or ["vector", "entity", "context", "hybrid"]
        top_k = top_k or self.default_top_k
        
        logger.info(f"Comparing retrieval methods ({', '.join(methods)}) for query '{query}'")
        
        start_time = time.time()
        
        # Run each method
        method_results = {}
        
        for method in methods:
            method_result = self.retrieve(
                query=query,
                method=method,
                top_k=top_k
            )
            
            method_results[method] = method_result
        
        # Calculate comparison metrics
        comparison = self._calculate_retrieval_comparison(method_results)
        
        # Format response
        total_time = time.time() - start_time
        
        response = {
            "query": query,
            "methods_compared": methods,
            "top_k": top_k,
            "method_results": method_results,
            "comparison": comparison,
            "total_comparison_time": total_time
        }
        
        logger.info(f"Completed retrieval method comparison in {total_time:.2f}s")
        
        return response
    
    def _calculate_retrieval_comparison(self, method_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate comparison metrics between retrieval methods.
        
        Args:
            method_results: Dictionary of results for each method
            
        Returns:
            Dictionary of comparison metrics
        """
        comparison = {
            "result_overlap": {},
            "unique_results": {},
            "speed_comparison": {},
            "result_diversity": {},
            "summary": {}
        }
        
        # Calculate result overlap between methods
        methods = list(method_results.keys())
        
        for i, method1 in enumerate(methods):
            results1 = {r["id"] for r in method_results[method1]["results"]}
            
            for method2 in methods[i+1:]:
                results2 = {r["id"] for r in method_results[method2]["results"]}
                
                overlap = results1.intersection(results2)
                
                comparison["result_overlap"][f"{method1}_vs_{method2}"] = {
                    "overlap_count": len(overlap),
                    "overlap_percentage": len(overlap) / max(1, len(results1.union(results2))) * 100
                }
        
        # Calculate unique results per method
        all_result_ids = set()
        for method in methods:
            all_result_ids.update(r["id"] for r in method_results[method]["results"])
        
        for method in methods:
            method_ids = {r["id"] for r in method_results[method]["results"]}
            unique_ids = method_ids - (all_result_ids - method_ids)
            
            comparison["unique_results"][method] = {
                "unique_count": len(unique_ids),
                "unique_percentage": len(unique_ids) / max(1, len(method_ids)) * 100,
                "unique_ids": list(unique_ids)
            }
        
        # Speed comparison
        for method in methods:
            comparison["speed_comparison"][method] = method_results[method]["retrieval_time"]
        
        # Result diversity - measure how distributed the results are
        for method in methods:
            similarity_values = [r.get("similarity", 0) for r in method_results[method]["results"]]
            
            import numpy as np
            
            if similarity_values:
                comparison["result_diversity"][method] = {
                    "mean_similarity": np.mean(similarity_values),
                    "std_dev": np.std(similarity_values),
                    "min": np.min(similarity_values),
                    "max": np.max(similarity_values)
                }
            else:
                comparison["result_diversity"][method] = {
                    "error": "No results with similarity scores"
                }
        
        # Summary
        fastest_method = min(methods, key=lambda m: comparison["speed_comparison"][m])
        
        most_unique_method = max(
            methods, 
            key=lambda m: comparison["unique_results"][m]["unique_percentage"]
        )
        
        comparison["summary"] = {
            "fastest_method": fastest_method,
            "fastest_time": comparison["speed_comparison"][fastest_method],
            "most_unique_method": most_unique_method,
            "most_unique_percentage": comparison["unique_results"][most_unique_method]["unique_percentage"],
            "highest_overlap": max(
                comparison["result_overlap"].items(),
                key=lambda x: x[1]["overlap_percentage"],
                default=(None, {"overlap_percentage": 0})
            )[0]
        }
        
        return comparison