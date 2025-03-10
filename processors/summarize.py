"""
Summarization processor for RAG Showdown.

This module provides advanced document summarization capabilities with multiple
strategies, evaluation metrics, and customization options.
"""

import re
import logging
import time
from typing import List, Dict, Any, Optional, Union, Tuple
import json
from utils.openai_client import OpenAIClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SummarizationProcessor:
    """
    Processor for generating summaries with multiple strategies and evaluations.
    """
    
    def __init__(self, model: str = "gpt-3.5-turbo"):
        """
        Initialize the summarization processor.
        
        Args:
            model: Default model to use for summarization
        """
        self.openai_client = OpenAIClient(model=model)
        self.default_model = model
        logger.info(f"Initialized SummarizationProcessor with model {model}")
    
    def basic_summary(self, 
                     text: str, 
                     max_length: Optional[int] = None, 
                     style: str = "concise") -> Dict[str, Any]:
        """
        Generate a basic document summary.
        
        Args:
            text: Text to summarize
            max_length: Maximum length of summary in words
            style: Summarization style ("concise", "detailed", "bullet", "narrative")
            
        Returns:
            Dictionary with summary and metadata
        """
        logger.info(f"Generating {style} summary for text ({len(text)} chars)")
        start_time = time.time()
        
        # Create custom instructions based on style
        style_instructions = {
            "concise": "Create a brief, high-level summary of the key points. Be concise and direct.",
            "detailed": "Provide a comprehensive summary that captures main points and important details.",
            "bullet": "Create a bullet-point summary of the key information, organized by topic.",
            "narrative": "Generate a narrative summary that flows naturally and maintains the original tone."
        }.get(style, "Create a concise summary of the main points.")
        
        # Add length constraint if specified
        length_constraint = f"Keep your summary under {max_length} words." if max_length else ""
        
        # Build prompt
        prompt = f"""
        {style_instructions}
        
        {length_constraint}
        
        TEXT TO SUMMARIZE:
        {text}
        """
        
        system_message = """
        You are a specialized summarization AI that creates accurate, informative summaries.
        Focus only on information present in the provided text.
        Do not add information, opinions, or analysis not present in the original.
        """
        
        try:
            summary = self.openai_client.generate_completion(
                prompt=prompt, 
                system_message=system_message,
                model=self.default_model
            )
            
            processing_time = time.time() - start_time
            
            # Estimate word count
            word_count = len(summary.split())
            
            return {
                "summary": summary,
                "style": style,
                "word_count": word_count,
                "processing_time": processing_time,
                "method": "basic_summary"
            }
            
        except Exception as e:
            logger.error(f"Error generating basic summary: {e}")
            return {
                "error": str(e),
                "method": "basic_summary"
            }
    
    def extractive_summary(self, 
                          text: str, 
                          ratio: float = 0.2, 
                          min_length: int = 100) -> Dict[str, Any]:
        """
        Generate an extractive summary by selecting the most important sentences.
        
        Args:
            text: Text to summarize
            ratio: Target ratio of summary to original text length
            min_length: Minimum summary length in characters
            
        Returns:
            Dictionary with extractive summary and metadata
        """
        logger.info(f"Generating extractive summary for text ({len(text)} chars)")
        start_time = time.time()
        
        # Approach 1: Use LLM to identify important sentences
        prompt = f"""
        Identify the 5-8 most important sentences from the following text that capture its key information.
        Return ONLY the exact sentences, exactly as they appear in the original text, with no modifications.
        Do not add your own words or explanations.
        
        TEXT TO ANALYZE:
        {text}
        """
        
        system_message = """
        You are an extractive summarization engine. Your task is to identify and extract the most informative 
        sentences from the text without modifying them. Provide only the extracted sentences.
        """
        
        try:
            extracted_sentences = self.openai_client.generate_completion(
                prompt=prompt, 
                system_message=system_message,
                model=self.default_model
            )
            
            processing_time = time.time() - start_time
            
            # Count original sentences for comparison
            original_sentence_count = len(re.split(r'[.!?]+', text))
            summary_sentence_count = len(re.split(r'[.!?]+', extracted_sentences))
            
            return {
                "summary": extracted_sentences,
                "original_sentences": original_sentence_count,
                "summary_sentences": summary_sentence_count,
                "compression_ratio": summary_sentence_count / max(1, original_sentence_count),
                "processing_time": processing_time,
                "method": "extractive_summary"
            }
            
        except Exception as e:
            logger.error(f"Error generating extractive summary: {e}")
            return {
                "error": str(e),
                "method": "extractive_summary"
            }
    
    def entity_focused_summary(self, 
                              text: str, 
                              entities: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate a summary focused on specific entities.
        
        Args:
            text: Text to summarize
            entities: List of entities to focus on (detected automatically if None)
            
        Returns:
            Dictionary with entity-focused summary and metadata
        """
        logger.info(f"Generating entity-focused summary for text ({len(text)} chars)")
        start_time = time.time()
        
        # If entities not provided, detect them first
        if entities is None:
            entities = self._extract_key_entities(text)
        
        if not entities:
            logger.warning("No entities found for entity-focused summary")
            return {
                "error": "No entities identified in the text",
                "method": "entity_focused_summary"
            }
        
        # Build prompt
        entities_list = ", ".join(entities)
        prompt = f"""
        Create a summary of the text that focuses on these key entities: {entities_list}.
        
        For each entity, summarize the most important information mentioned about it.
        Organize your summary by entity, with clear headings for each one.
        Include only information that is explicitly mentioned in the text.
        
        TEXT TO SUMMARIZE:
        {text}
        """
        
        system_message = """
        You are a specialized entity-focused summarization AI. Your summaries organize information 
        by key entities while maintaining factual accuracy. Focus only on information present 
        in the source text.
        """
        
        try:
            summary = self.openai_client.generate_completion(
                prompt=prompt, 
                system_message=system_message,
                model=self.default_model
            )
            
            processing_time = time.time() - start_time
            
            return {
                "summary": summary,
                "entities": entities,
                "entity_count": len(entities),
                "processing_time": processing_time,
                "method": "entity_focused_summary"
            }
            
        except Exception as e:
            logger.error(f"Error generating entity-focused summary: {e}")
            return {
                "error": str(e),
                "method": "entity_focused_summary"
            }
    
    def _extract_key_entities(self, text: str) -> List[str]:
        """
        Extract key entities from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of key entity names
        """
        # Use a simple LLM approach for entity extraction
        prompt = """
        Identify the 3-5 most important named entities (people, organizations, products, locations) 
        in the following text. Return only a comma-separated list of entity names, with no additional text.
        
        TEXT TO ANALYZE:
        """
        
        system_message = """
        You are an entity recognition specialist. Extract only the most important named entities 
        from the text. Return only the entity names as a comma-separated list.
        """
        
        # If text is very long, use just the first part
        analysis_text = text[:6000] if len(text) > 6000 else text
        
        try:
            result = self.openai_client.generate_completion(
                prompt=prompt + analysis_text, 
                system_message=system_message,
                model=self.default_model
            )
            
            # Clean up and parse result
            result = result.strip()
            entities = [entity.strip() for entity in result.split(",") if entity.strip()]
            
            return entities
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return []
    
    def temporal_summary(self, 
                        text: str, 
                        chrono_order: bool = True) -> Dict[str, Any]:
        """
        Generate a summary organized by time periods/events.
        
        Args:
            text: Text to summarize
            chrono_order: Whether to present events in chronological order
            
        Returns:
            Dictionary with temporal summary and metadata
        """
        logger.info(f"Generating temporal summary for text ({len(text)} chars)")
        start_time = time.time()
        
        # Build prompt
        time_order = "chronological" if chrono_order else "reverse chronological"
        prompt = f"""
        Create a summary of the text organized by time periods or key events.
        
        Identify the main time periods, dates, or temporal events in the text.
        Organize the information in {time_order} order.
        For each time period or event, summarize the relevant information.
        Use clear temporal markers and headings in your summary.
        
        TEXT TO SUMMARIZE:
        {text}
        """
        
        system_message = """
        You are a specialized temporal summarization AI. Your summaries organize information 
        by time periods and events, maintaining a clear temporal structure while preserving 
        factual accuracy.
        """
        
        try:
            summary = self.openai_client.generate_completion(
                prompt=prompt, 
                system_message=system_message,
                model=self.default_model
            )
            
            processing_time = time.time() - start_time
            
            # Extract time periods mentioned
            time_periods = self._extract_time_periods(summary)
            
            return {
                "summary": summary,
                "time_periods": time_periods,
                "chronological_order": chrono_order,
                "period_count": len(time_periods),
                "processing_time": processing_time,
                "method": "temporal_summary"
            }
            
        except Exception as e:
            logger.error(f"Error generating temporal summary: {e}")
            return {
                "error": str(e),
                "method": "temporal_summary"
            }
    
    def _extract_time_periods(self, text: str) -> List[str]:
        """
        Extract time periods mentioned in a summary.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of time periods
        """
        # Simple regex-based approach for demo purposes
        # In production, would use NER or more sophisticated techniques
        date_pattern = r'\b((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})'
        year_pattern = r'\b((?:19|20)\d{2})\b'
        quarter_pattern = r'\b(Q[1-4]\s+\d{4}|(?:first|second|third|fourth) quarter of \d{4})'
        
        # Find all matches
        dates = re.findall(date_pattern, text, re.IGNORECASE)
        years = re.findall(year_pattern, text)
        quarters = re.findall(quarter_pattern, text, re.IGNORECASE)
        
        # Combine and remove duplicates
        all_periods = list(set(dates + years + quarters))
        
        return all_periods
    
    def multi_document_summary(self, 
                             texts: List[str], 
                             query: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a summary of multiple documents, optionally focused on a query.
        
        Args:
            texts: List of texts to summarize
            query: Optional query to focus the summary
            
        Returns:
            Dictionary with multi-document summary and metadata
        """
        logger.info(f"Generating multi-document summary for {len(texts)} texts")
        start_time = time.time()
        
        # If texts are too long, summarize each one first
        if sum(len(text) for text in texts) > 8000:
            # Summarize each document individually first
            individual_summaries = []
            for i, text in enumerate(texts):
                summary_result = self.basic_summary(text, style="concise")
                if "summary" in summary_result:
                    individual_summaries.append(f"Document {i+1} Summary:\n{summary_result['summary']}")
            
            combined_text = "\n\n".join(individual_summaries)
        else:
            # Combine texts with clear document markers
            combined_text = ""
            for i, text in enumerate(texts):
                combined_text += f"Document {i+1}:\n{text}\n\n"
        
        # Build prompt
        if query:
            prompt = f"""
            Create a summary of the following documents that answers this query: "{query}"
            
            Focus on information relevant to the query, while noting any contradictions or differences 
            between documents. Maintain factual accuracy and cite document numbers when appropriate.
            
            DOCUMENTS:
            {combined_text}
            """
        else:
            prompt = f"""
            Create a comprehensive summary of the following documents, highlighting:
            1. Key points shared across multiple documents
            2. Important unique information from individual documents
            3. Any contradictions or differences between documents
            
            Maintain factual accuracy and cite document numbers when appropriate.
            
            DOCUMENTS:
            {combined_text}
            """
        
        system_message = """
        You are a specialized multi-document summarization AI. Your task is to synthesize information 
        across multiple documents while maintaining factual accuracy and highlighting important 
        relationships between documents.
        """
        
        try:
            summary = self.openai_client.generate_completion(
                prompt=prompt, 
                system_message=system_message,
                model=self.default_model
            )
            
            processing_time = time.time() - start_time
            
            return {
                "summary": summary,
                "document_count": len(texts),
                "query": query,
                "is_query_focused": query is not None,
                "processing_time": processing_time,
                "method": "multi_document_summary"
            }
            
        except Exception as e:
            logger.error(f"Error generating multi-document summary: {e}")
            return {
                "error": str(e),
                "method": "multi_document_summary"
            }
    
    def contrastive_summary(self, 
                           text1: str, 
                           text2: str, 
                           focus: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a summary that contrasts two texts.
        
        Args:
            text1: First text
            text2: Second text
            focus: Optional aspect to focus the comparison on
            
        Returns:
            Dictionary with contrastive summary and metadata
        """
        logger.info(f"Generating contrastive summary between two texts")
        start_time = time.time()
        
        # Build prompt
        focus_instruction = f"Focus your comparison on {focus}." if focus else ""
        prompt = f"""
        Create a summary that compares and contrasts the following two texts.
        
        {focus_instruction}
        
        Highlight:
        1. Key similarities between the texts
        2. Important differences between the texts
        3. Unique information provided by each text
        
        TEXT 1:
        {text1}
        
        TEXT 2:
        {text2}
        """
        
        system_message = """
        You are a specialized contrastive summarization AI. Your task is to compare and contrast 
        different texts, highlighting similarities and differences while maintaining factual accuracy.
        """
        
        try:
            summary = self.openai_client.generate_completion(
                prompt=prompt, 
                system_message=system_message,
                model=self.default_model
            )
            
            processing_time = time.time() - start_time
            
            return {
                "summary": summary,
                "focus": focus,
                "processing_time": processing_time,
                "method": "contrastive_summary"
            }
            
        except Exception as e:
            logger.error(f"Error generating contrastive summary: {e}")
            return {
                "error": str(e),
                "method": "contrastive_summary"
            }
    
    def evaluate_summary(self, 
                        original_text: str, 
                        summary: str) -> Dict[str, Any]:
        """
        Evaluate the quality of a summary.
        
        Args:
            original_text: Original text
            summary: Summary to evaluate
            
        Returns:
            Dictionary with evaluation metrics
        """
        logger.info(f"Evaluating summary quality")
        start_time = time.time()
        
        # Build prompt for evaluation
        prompt = f"""
        Evaluate the quality of the following summary based on the original text.
        
        Please assess the summary on these dimensions, scoring each from 1-10:
        1. Completeness: Does it include all important information?
        2. Conciseness: Is it appropriately brief without unnecessary details?
        3. Accuracy: Does it contain only factual information from the original?
        4. Coherence: Does it flow logically and is it well-organized?
        
        Also identify:
        - Any factual errors or hallucinations (information not in the original)
        - Any important information that was omitted
        
        Return your evaluation as a JSON object with these fields:
        {{
          "completeness_score": [1-10],
          "conciseness_score": [1-10], 
          "accuracy_score": [1-10],
          "coherence_score": [1-10],
          "overall_score": [1-10],
          "factual_errors": ["error1", "error2", ...],
          "important_omissions": ["omission1", "omission2", ...],
          "strengths": ["strength1", "strength2", ...],
          "improvement_suggestions": ["suggestion1", "suggestion2", ...]
        }}
        
        ORIGINAL TEXT:
        {original_text}
        
        SUMMARY TO EVALUATE:
        {summary}
        """
        
        system_message = """
        You are a specialized summary evaluation AI. Your task is to objectively evaluate the quality of summaries 
        based on completeness, conciseness, accuracy, and coherence. Provide your evaluation in the requested JSON format.
        """
        
        try:
            evaluation_result = self.openai_client.generate_completion(
                prompt=prompt, 
                system_message=system_message,
                model=self.default_model
            )
            
            # Parse JSON from response
            evaluation_json = self._extract_json(evaluation_result)
            
            processing_time = time.time() - start_time
            
            # Add additional metadata
            evaluation_json["processing_time"] = processing_time
            evaluation_json["original_length"] = len(original_text)
            evaluation_json["summary_length"] = len(summary)
            evaluation_json["compression_ratio"] = len(summary) / max(1, len(original_text))
            
            return evaluation_json
            
        except Exception as e:
            logger.error(f"Error evaluating summary: {e}")
            return {
                "error": str(e),
                "method": "evaluate_summary"
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
    
    def summarize(self, 
                 text: str, 
                 method: str = "basic", 
                 **kwargs) -> Dict[str, Any]:
        """
        Generate a summary using the specified method.
        
        Args:
            text: Text to summarize
            method: Summarization method to use
            **kwargs: Additional parameters for the specific method
            
        Returns:
            Dictionary with summary and metadata
        """
        if method == "basic":
            return self.basic_summary(
                text=text,
                max_length=kwargs.get("max_length"),
                style=kwargs.get("style", "concise")
            )
        elif method == "extractive":
            return self.extractive_summary(
                text=text,
                ratio=kwargs.get("ratio", 0.2),
                min_length=kwargs.get("min_length", 100)
            )
        elif method == "entity_focused":
            return self.entity_focused_summary(
                text=text,
                entities=kwargs.get("entities")
            )
        elif method == "temporal":
            return self.temporal_summary(
                text=text,
                chrono_order=kwargs.get("chrono_order", True)
            )
        else:
            raise ValueError(f"Unknown summarization method: {method}")
    
    def compare_summaries(self, 
                         text: str, 
                         methods: List[str] = None, 
                         evaluate: bool = True) -> Dict[str, Any]:
        """
        Compare different summarization methods on the same text.
        
        Args:
            text: Text to summarize
            methods: List of summarization methods to compare
            evaluate: Whether to evaluate summaries
            
        Returns:
            Dictionary with results for each method and comparison
        """
        methods = methods or ["basic", "extractive", "entity_focused", "temporal"]
        logger.info(f"Comparing summarization methods ({', '.join(methods)}) on text ({len(text)} chars)")
        
        summaries = {}
        evaluations = {}
        
        # Generate summaries with each method
        for method in methods:
            try:
                result = self.summarize(text, method=method)
                summaries[method] = result
                
                # Evaluate if requested
                if evaluate and "summary" in result:
                    evaluation = self.evaluate_summary(text, result["summary"])
                    evaluations[method] = evaluation
            except Exception as e:
                logger.error(f"Error with method {method}: {e}")
                summaries[method] = {"error": str(e)}
        
        # Compare summaries
        comparison = self._compare_summary_results(summaries, evaluations)
        
        return {
            "text_length": len(text),
            "methods": methods,
            "summaries": summaries,
            "evaluations": evaluations,
            "comparison": comparison
        }
    
    def _compare_summary_results(self, 
                               summaries: Dict[str, Dict[str, Any]], 
                               evaluations: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate comparison metrics between summary methods.
        
        Args:
            summaries: Dictionary of summary results by method
            evaluations: Dictionary of evaluation results by method
            
        Returns:
            Dictionary of comparison metrics
        """
        comparison = {
            "length_comparison": {},
            "processing_time_comparison": {},
            "rankings": {}
        }
        
        # Compare summary lengths
        for method, result in summaries.items():
            if "summary" in result:
                comparison["length_comparison"][method] = len(result["summary"])
        
        # Compare processing times
        for method, result in summaries.items():
            if "processing_time" in result:
                comparison["processing_time_comparison"][method] = result["processing_time"]
        
        # Generate rankings based on evaluations
        if evaluations:
            for metric in ["completeness_score", "conciseness_score", "accuracy_score", 
                          "coherence_score", "overall_score"]:
                # Get methods with this metric
                methods_with_metric = []
                for method, eval_result in evaluations.items():
                    if metric in eval_result:
                        methods_with_metric.append((method, eval_result[metric]))
                
                # Sort by score (descending)
                methods_with_metric.sort(key=lambda x: x[1], reverse=True)
                
                # Add to rankings
                comparison["rankings"][metric] = [
                    {"method": method, "score": score}
                    for method, score in methods_with_metric
                ]
        
        return comparison
    
    def get_metrics_schema(self, 
                          results: Dict[str, Any], 
                          comparison_type: str = "Summarization Method") -> Dict[str, Any]:
        """
        Convert summary comparison results to metrics schema.
        
        Args:
            results: Results from compare_summaries
            comparison_type: Type of comparison
            
        Returns:
            Dictionary following the metrics schema
        """
        schema = {
            "comparison_type": comparison_type,
            "compared_entities": [],
            "visualization_type": "radar_chart",
            "title": "Summarization Method Comparison",
            "description": f"Comparison of {len(results.get('methods', []))} summarization methods",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Extract evaluations for each method
        evaluations = results.get("evaluations", {})
        methods = results.get("methods", [])
        
        for method in methods:
            entity = {
                "name": method.replace("_", " ").title(),
                "description": f"{method.replace('_', ' ').title()} summarization approach",
                "metrics": {}
            }
            
            # Add evaluation metrics if available
            if method in evaluations:
                eval_result = evaluations[method]
                
                # Add core metrics
                metric_fields = [
                    ("completeness_score", "Completeness", "score", "Higher is better"),
                    ("conciseness_score", "Conciseness", "score", "Higher is better"),
                    ("accuracy_score", "Accuracy", "score", "Higher is better"),
                    ("coherence_score", "Coherence", "score", "Higher is better"),
                    ("overall_score", "Overall Quality", "score", "Higher is better")
                ]
                
                for field, display_name, display_format, interpretation in metric_fields:
                    if field in eval_result:
                        entity["metrics"][display_name] = {
                            "value": eval_result[field],
                            "display_format": display_format,
                            "visualization_hint": "radar",
                            "interpretation": interpretation
                        }
            
            # Add processing time if available
            summary_result = results.get("summaries", {}).get(method, {})
            if "processing_time" in summary_result:
                entity["metrics"]["Processing Time"] = {
                    "value": summary_result["processing_time"],
                    "display_format": "seconds",
                    "visualization_hint": "bar",
                    "interpretation": "Lower is faster"
                }
            
            # Add to compared entities
            schema["compared_entities"].append(entity)
        
        return schema