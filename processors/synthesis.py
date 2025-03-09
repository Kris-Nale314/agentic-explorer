# processors/synthesis.py
"""
Synthesis processor for the RAG Showdown.

This module handles the final synthesis of retrieved information,
comparing traditional single-prompt approaches with multi-agent strategies.
"""

import logging
import time
import json
from typing import List, Dict, Any, Optional, Union
from utils.openai_client import OpenAIClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SynthesisProcessor:
    """
    Processor for synthesizing information from retrieved document chunks.
    Supports both traditional single-prompt RAG and multi-agent analysis.
    """
    
    def __init__(self):
        """Initialize the synthesis processor."""
        self.openai_client = OpenAIClient()
        logger.info("Initialized SynthesisProcessor")
    
    def single_prompt_synthesis(self, 
                               query: str, 
                               context_chunks: List[Dict[str, Any]],
                               max_tokens: int = 2000,
                               temperature: float = 0.3,
                               model: str = None) -> Dict[str, Any]:
        """
        Perform traditional single-prompt RAG synthesis.
        
        Args:
            query: User query
            context_chunks: List of retrieved context chunks
            max_tokens: Maximum tokens in response
            temperature: LLM temperature
            model: Optional model override
            
        Returns:
            Dictionary with generated response and metadata
        """
        logger.info(f"Performing single-prompt synthesis for query: '{query}'")
        start_time = time.time()
        
        # Format context from chunks
        context_texts = []
        
        for i, chunk in enumerate(context_chunks):
            chunk_text = chunk.get("text", "")
            if not chunk_text:
                continue
                
            # Add chunk metadata if available
            metadata = ""
            if "metadata" in chunk and chunk["metadata"]:
                metadata_str = ", ".join(f"{k}: {v}" for k, v in chunk["metadata"].items() 
                                       if k not in ["text", "embedding"])
                if metadata_str:
                    metadata = f" [{metadata_str}]"
            
            # Format chunk with index
            context_texts.append(f"Context Chunk {i+1}{metadata}:\n{chunk_text}\n")
        
        # Combine context chunks
        combined_context = "\n".join(context_texts)
        
        # Build prompt
        prompt = f"""
        Answer the following query based on the provided context chunks only. If the context doesn't contain the 
        information needed to answer the query, acknowledge this limitation. Do not use knowledge that isn't 
        provided in the context.
        
        Query: {query}
        
        {combined_context}
        
        Based on the context chunks provided above, please answer the query thoughtfully and accurately.
        """
        
        try:
            # Generate completion
            response = self.openai_client.generate_completion(
                prompt=prompt,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            processing_time = time.time() - start_time
            
            result = {
                "query": query,
                "response": response,
                "processing_time": processing_time,
                "chunk_count": len(context_chunks),
                "context_length": len(combined_context),
                "method": "single_prompt",
                "model": model or self.openai_client.model
            }
            
            logger.info(f"Single-prompt synthesis completed in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error in single-prompt synthesis: {e}")
            return {
                "query": query,
                "error": str(e),
                "method": "single_prompt"
            }
    
    def entity_focused_synthesis(self, 
                                query: str, 
                                context_chunks: List[Dict[str, Any]],
                                max_tokens: int = 2500,
                                model: str = None) -> Dict[str, Any]:
        """
        Perform entity-focused synthesis that organizes information by entities.
        
        Args:
            query: User query
            context_chunks: List of retrieved context chunks
            max_tokens: Maximum tokens in response
            model: Optional model override
            
        Returns:
            Dictionary with generated response and metadata
        """
        logger.info(f"Performing entity-focused synthesis for query: '{query}'")
        start_time = time.time()
        
        # Extract entities from query and chunks
        entities = self._extract_entities(query, context_chunks)
        
        if not entities:
            logger.info("No significant entities found, falling back to single-prompt synthesis")
            result = self.single_prompt_synthesis(query, context_chunks, max_tokens, model=model)
            result["method"] = "entity_focused_fallback"
            return result
        
        # Format context from chunks
        context_texts = []
        
        for i, chunk in enumerate(context_chunks):
            chunk_text = chunk.get("text", "")
            if not chunk_text:
                continue
            
            # Add retrieveal method if available
            method = chunk.get("retrieval_method", "")
            method_str = f" (via {method})" if method else ""
            
            # Format chunk with index
            context_texts.append(f"Context Chunk {i+1}{method_str}:\n{chunk_text}\n")
        
        # Combine context chunks
        combined_context = "\n".join(context_texts)
        
        # Format entities string
        entities_str = ", ".join(entities[:5])  # Top 5 entities
        
        # Build prompt
        prompt = f"""
        Answer the following query based on the provided context chunks only. Focus your analysis on key entities mentioned.
        
        Query: {query}
        
        Key entities to focus on: {entities_str}
        
        {combined_context}
        
        Your task:
        1. For each key entity mentioned in the query and context, summarize what the context reveals about it
        2. After covering each entity, provide an overall answer to the query
        3. Only use information from the provided context
        4. Structure your response by entity for clarity
        
        Begin your entity-focused analysis:
        """
        
        try:
            # Generate completion
            response = self.openai_client.generate_completion(
                prompt=prompt,
                model=model,
                max_tokens=max_tokens,
                temperature=0.2  # Lower temperature for more focused response
            )
            
            processing_time = time.time() - start_time
            
            result = {
                "query": query,
                "response": response,
                "processing_time": processing_time,
                "chunk_count": len(context_chunks),
                "context_length": len(combined_context),
                "entities": entities,
                "method": "entity_focused",
                "model": model or self.openai_client.model
            }
            
            logger.info(f"Entity-focused synthesis completed in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error in entity-focused synthesis: {e}")
            return {
                "query": query,
                "error": str(e),
                "method": "entity_focused"
            }
    
    def _extract_entities(self, query: str, chunks: List[Dict[str, Any]]) -> List[str]:
        """
        Extract key entities from query and context chunks.
        
        Args:
            query: User query
            chunks: List of context chunks
            
        Returns:
            List of key entity names
        """
        # Simple approach: look for entity info already in chunk metadata
        entity_candidates = set()
        
        # Check if chunks already have entity information
        for chunk in chunks:
            if chunk.get("entity_match"):
                entity_candidates.add(chunk["entity_match"])
            
            # Check metadata
            metadata = chunk.get("metadata", {})
            if metadata.get("entities"):
                if isinstance(metadata["entities"], list):
                    entity_candidates.update(metadata["entities"])
                elif isinstance(metadata["entities"], str):
                    entity_candidates.add(metadata["entities"])
        
        # If not enough entities found, use LLM to extract
        if len(entity_candidates) < 2:
            # Combine some chunk text for entity extraction
            combined_text = query + "\n\n"
            
            # Add text from first few chunks
            for chunk in chunks[:3]:
                if "text" in chunk:
                    combined_text += chunk["text"][:500] + "\n\n"
            
            # Use LLM to extract entities
            prompt = """
            Identify the top 5 most important entities (companies, people, products, etc.) in the following text.
            Output only a comma-separated list of entity names without explanation or commentary.
            
            TEXT:
            """
            
            try:
                result = self.openai_client.generate_completion(prompt + combined_text)
                
                # Clean result
                result = result.strip().strip('[]"\'')
                
                # Split into entities
                extracted_entities = [e.strip() for e in result.split(',')]
                
                # Add to candidates
                entity_candidates.update(extracted_entities)
                
            except Exception as e:
                logger.warning(f"Error extracting entities with LLM: {e}")
        
        # Remove empty or very short entities
        filtered_entities = [e for e in entity_candidates if e and len(e) > 1]
        
        return filtered_entities
    
    def multi_agent_synthesis(self, 
                             query: str, 
                             context_chunks: List[Dict[str, Any]],
                             max_tokens: int = 3000,
                             model: str = None) -> Dict[str, Any]:
        """
        Perform multi-agent synthesis with specialized roles.
        
        Args:
            query: User query
            context_chunks: List of retrieved context chunks
            max_tokens: Maximum tokens in response
            model: Optional model override
            
        Returns:
            Dictionary with generated response and metadata
        """
        logger.info(f"Performing multi-agent synthesis for query: '{query}'")
        start_time = time.time()
        
        # Format context from chunks
        context_texts = []
        
        for i, chunk in enumerate(context_chunks):
            chunk_text = chunk.get("text", "")
            if not chunk_text:
                continue
                
            # Format chunk with index and retrieval method
            method = chunk.get("retrieval_method", "")
            method_str = f" (via {method})" if method else ""
            
            context_texts.append(f"Context Chunk {i+1}{method_str}:\n{chunk_text}\n")
        
        # Combine context chunks
        combined_context = "\n".join(context_texts)
        
        # 1. Researcher Agent: Analyze and extract relevant information
        researcher_prompt = f"""
        You are a Research Analyst agent. Your role is to carefully analyze the provided context 
        chunks and extract the most relevant information for answering the query.
        
        Query: {query}
        
        {combined_context}
        
        Your task:
        1. Identify key facts in the context relevant to the query
        2. Note any inconsistencies or contradictions in the context
        3. Highlight information gaps if the context is insufficient
        4. Extract quotes that directly address the query
        
        Format your analysis as a JSON object with these keys:
        - key_facts: Array of relevant facts
        - inconsistencies: Array of any contradictions found
        - information_gaps: Array of missing information needed to fully answer the query
        - relevant_quotes: Array of direct quotes from the context that support answering the query
        - confidence: Your confidence score (0-10) in the completeness of the context
        
        Research Analysis:
        """
        
        try:
            # Run researcher agent
            researcher_response = self.openai_client.generate_completion(
                prompt=researcher_prompt,
                model=model,
                max_tokens=max_tokens // 2,
                temperature=0.1
            )
            
            # Extract researcher insights
            researcher_insights = self._extract_json(researcher_response)
            
            # 2. Synthesizer Agent: Create cohesive answer
            synthesizer_prompt = f"""
            You are a Synthesis Specialist agent. Your role is to create a cohesive, accurate answer to the query
            based on the Research Analyst's findings.
            
            Query: {query}
            
            Research Analysis:
            {researcher_response}
            
            Your task:
            1. Synthesize the key facts into a comprehensive answer to the query
            2. Address any inconsistencies noted by the researcher
            3. Acknowledge information gaps where appropriate
            4. Use relevant quotes to support your answer
            5. Maintain factual accuracy based strictly on the provided context
            
            Format your response as a clear, well-structured answer to the original query.
            """
            
            # Run synthesizer agent
            synthesizer_response = self.openai_client.generate_completion(
                prompt=synthesizer_prompt,
                model=model,
                max_tokens=max_tokens // 2,
                temperature=0.3
            )
            
            # 3. Critic Agent: Evaluate and improve
            critic_prompt = f"""
            You are a Quality Control agent. Your role is to evaluate and improve the synthesized answer.
            
            Original Query: {query}
            
            Synthesized Answer:
            {synthesizer_response}
            
            Research Analysis:
            {researcher_response}
            
            Your task:
            1. Evaluate the factual accuracy of the synthesized answer
            2. Check if all key points from the research are included
            3. Ensure information gaps are properly acknowledged
            4. Verify that inconsistencies are appropriately addressed
            5. Provide 2-3 specific improvements (if needed)
            
            If the answer is satisfactory, simply state "The synthesized answer is accurate and comprehensive."
            Otherwise, provide your specific recommendations for improvement.
            """
            
            # Run critic agent
            critic_response = self.openai_client.generate_completion(
                prompt=critic_prompt,
                model=model,
                max_tokens=max_tokens // 4,
                temperature=0.2
            )
            
            # Final response with multi-agent insights
            final_response = synthesizer_response
            
            # Add critique if substantial
            if len(critic_response) > 50 and "satisfactory" not in critic_response.lower():
                final_response += f"\n\n[Quality Control Note: {critic_response}]"
            
            processing_time = time.time() - start_time
            
            result = {
                "query": query,
                "response": final_response,
                "processing_time": processing_time,
                "chunk_count": len(context_chunks),
                "context_length": len(combined_context),
                "method": "multi_agent",
                "agent_insights": {
                    "researcher": researcher_insights,
                    "critic_feedback": critic_response if "satisfactory" not in critic_response.lower() else "Approved"
                },
                "model": model or self.openai_client.model
            }
            
            logger.info(f"Multi-agent synthesis completed in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error in multi-agent synthesis: {e}")
            return {
                "query": query,
                "error": str(e),
                "method": "multi_agent"
            }
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """
        Extract JSON object from text.
        
        Args:
            text: Text potentially containing JSON
            
        Returns:
            Extracted JSON object or empty dict if not found
        """
        import re
        import json
        
        # Find JSON-like patterns
        json_pattern = r'({[\s\S]*})'
        match = re.search(json_pattern, text)
        
        if match:
            try:
                # Try to parse the JSON
                json_str = match.group(1)
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # If JSON parsing failed, return empty dict
        return {}
    
    def synthesize(self, 
                  query: str, 
                  context_chunks: List[Dict[str, Any]],
                  method: str = "single_prompt",
                  max_tokens: int = 2000,
                  model: str = None) -> Dict[str, Any]:
        """
        Synthesize information from context chunks using specified method.
        
        Args:
            query: User query
            context_chunks: List of retrieved context chunks
            method: Synthesis method ('single_prompt', 'entity_focused', 'multi_agent')
            max_tokens: Maximum tokens in response
            model: Optional model override
            
        Returns:
            Dictionary with generated response and metadata
        """
        if method == "single_prompt":
            return self.single_prompt_synthesis(
                query=query,
                context_chunks=context_chunks,
                max_tokens=max_tokens,
                model=model
            )
        elif method == "entity_focused":
            return self.entity_focused_synthesis(
                query=query,
                context_chunks=context_chunks,
                max_tokens=max_tokens,
                model=model
            )
        elif method == "multi_agent":
            return self.multi_agent_synthesis(
                query=query,
                context_chunks=context_chunks,
                max_tokens=max_tokens,
                model=model
            )
        else:
            raise ValueError(f"Unknown synthesis method: {method}")
    
    def compare_synthesis_methods(self, 
                                 query: str, 
                                 context_chunks: List[Dict[str, Any]],
                                 methods: List[str] = None,
                                 max_tokens: int = 2000,
                                 model: str = None) -> Dict[str, Any]:
        """
        Compare different synthesis methods on the same query and context.
        
        Args:
            query: User query
            context_chunks: List of retrieved context chunks
            methods: List of synthesis methods to compare
            max_tokens: Maximum tokens in response
            model: Optional model override
            
        Returns:
            Dictionary with results for each method and comparison analysis
        """
        methods = methods or ["single_prompt", "entity_focused", "multi_agent"]
        
        logger.info(f"Comparing synthesis methods ({', '.join(methods)}) for query '{query}'")
        
        start_time = time.time()
        
        # Run each method
        method_results = {}
        
        for method in methods:
            method_result = self.synthesize(
                query=query,
                context_chunks=context_chunks,
                method=method,
                max_tokens=max_tokens,
                model=model
            )
            
            method_results[method] = method_result
        
        # Calculate comparison metrics and insights
        comparison = self._analyze_synthesis_comparison(query, method_results)
        
        # Format response
        total_time = time.time() - start_time
        
        response = {
            "query": query,
            "methods_compared": methods,
            "method_results": method_results,
            "comparison": comparison,
            "total_comparison_time": total_time
        }
        
        logger.info(f"Completed synthesis method comparison in {total_time:.2f}s")
        
        return response
    
    def _analyze_synthesis_comparison(self, 
                                     query: str, 
                                     method_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze and compare synthesis results from different methods.
        
        Args:
            query: Original user query
            method_results: Dictionary of results for each synthesis method
            
        Returns:
            Dictionary of comparison analysis
        """
        # Extract responses for each method
        method_responses = {
            method: result.get("response", "")
            for method, result in method_results.items()
        }
        
        # Calculate basic metrics
        metrics = {
            "processing_times": {
                method: result.get("processing_time", 0)
                for method, result in method_results.items()
            },
            "response_lengths": {
                method: len(response)
                for method, response in method_responses.items()
            }
        }
        
        # Use LLM to compare and analyze responses
        analysis_prompt = f"""
        Compare these different AI-generated responses to the same query and analyze their differences:
        
        Query: {query}
        
        """
        
        # Add each response to the prompt
        for method, response in method_responses.items():
            analysis_prompt += f"\n{method.upper()} RESPONSE:\n{response}\n"
        
        analysis_prompt += """
        Analyze the differences between these responses based on:
        1. Factual completeness - which covers more relevant facts?
        2. Structure and organization - which is better organized?
        3. Clarity and readability - which is easier to understand?
        4. Addressing the query - which most directly answers the original question?
        
        Provide your analysis as a JSON object with these keys:
        - factual_completeness_ranking: Array of methods ranked from most to least complete
        - structure_ranking: Array of methods ranked from best to worst structure
        - clarity_ranking: Array of methods ranked from most to least clear
        - query_relevance_ranking: Array of methods ranked by how directly they address the query
        - key_differences: Array of notable differences between the approaches
        - overall_best_method: The method that produced the most effective response overall
        - reasoning: Brief explanation for the overall best method selection
        """
        
        try:
            analysis_response = self.openai_client.generate_completion(analysis_prompt)
            analysis_json = self._extract_json(analysis_response)
            
            # If JSON extraction failed, provide simple comparison
            if not analysis_json:
                # Determine fastest method
                fastest_method = min(
                    metrics["processing_times"].items(),
                    key=lambda x: x[1]
                )[0]
                
                # Determine most verbose method
                most_verbose = max(
                    metrics["response_lengths"].items(),
                    key=lambda x: x[1]
                )[0]
                
                analysis_json = {
                    "factual_completeness_ranking": list(method_responses.keys()),
                    "overall_best_method": most_verbose,
                    "reasoning": f"The {most_verbose} method produced the longest response which likely contains more information."
                }
            
            # Combine analysis with basic metrics
            comparison = {
                "metrics": metrics,
                "analysis": analysis_json
            }
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error analyzing synthesis comparison: {e}")
            
            # Return basic metrics if analysis fails
            return {
                "metrics": metrics,
                "error": str(e)
            }
    
    def generate_educational_insights(self, comparison_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate educational insights about the different synthesis methods.
        
        Args:
            comparison_results: Results from compare_synthesis_methods
            
        Returns:
            Dictionary with educational insights about each method
        """
        method_results = comparison_results.get("method_results", {})
        comparison = comparison_results.get("comparison", {})
        
        insights = {
            "method_characteristics": {},
            "key_differences": [],
            "best_uses": {},
            "educational_summary": ""
        }
        
        # Generate insights for each method
        for method, result in method_results.items():
            if method == "single_prompt":
                insights["method_characteristics"][method] = {
                    "description": "Traditional RAG with a single prompt combining query and contexts",
                    "strengths": [
                        "Simplicity and efficiency",
                        "Works well for straightforward queries",
                        "Lower latency and token usage"
                    ],
                    "limitations": [
                        "May miss nuance when handling complex information",
                        "Often less structured than multi-agent approaches",
                        "More prone to hallucination when contexts conflict"
                    ]
                }
            elif method == "entity_focused":
                insights["method_characteristics"][method] = {
                    "description": "Organizes information by entities mentioned in the query and context",
                    "strengths": [
                        "Clearer structure for entity-heavy queries",
                        "Better at disambiguating different entities",
                        "Reduces confusion when multiple subjects are discussed"
                    ],
                    "limitations": [
                        "Less effective for queries without clear entities",
                        "May over-compartmentalize related information",
                        "Higher latency than single-prompt approach"
                    ]
                }
            elif method == "multi_agent":
                insights["method_characteristics"][method] = {
                    "description": "Uses specialized agents (researcher, synthesizer, critic) to collaborate",
                    "strengths": [
                        "More thorough fact-checking and evaluation",
                        "Better handling of inconsistencies in context",
                        "Higher overall quality through specialized roles",
                        "Self-critique improves accuracy"
                    ],
                    "limitations": [
                        "Significantly higher latency and token usage",
                        "More complex implementation",
                        "Diminishing returns for simple queries"
                    ]
                }
        
        # Add best use cases
        insights["best_uses"] = {
            "single_prompt": "Quick answers to factual questions with clear contexts",
            "entity_focused": "Questions involving multiple entities or comparing subjects",
            "multi_agent": "Complex questions requiring careful analysis of conflicting information"
        }
        
        # Add key differences from comparison
        if "analysis" in comparison and "key_differences" in comparison["analysis"]:
            insights["key_differences"] = comparison["analysis"]["key_differences"]
        else:
            insights["key_differences"] = [
                "Single-prompt is fastest but may miss nuance",
                "Entity-focused provides better structure for entity-heavy queries",
                "Multi-agent is most thorough but has highest latency"
            ]
        
        # Generate educational summary
        insights["educational_summary"] = f"""
        Different RAG synthesis methods have distinct trade-offs in quality, structure, and efficiency.
        
        Traditional single-prompt RAG is simple and efficient but may miss nuance in complex scenarios.
        Entity-focused approaches provide better structure when multiple subjects are involved.
        Multi-agent systems deliver higher quality through specialization but with increased latency.
        
        The best synthesis method depends on query complexity, time constraints, and information structure.
        """
        
        return insights