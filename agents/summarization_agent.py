# agents/summarization_manager.py
"""
Summarization Manager agent specializing in multi-strategy document summarization.
"""

import logging
import json
from agents.base_agent import BaseAgent
from processors.summarization_manager import SummarizationManager as SummarizationProcessor
from processors.text_processor import process_document
from data.content import AGENT_DESCRIPTIONS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SummarizationAgent(BaseAgent):
    """Agent that specializes in orchestrating multiple summarization approaches."""
    
    def __init__(self, model="gpt-3.5-turbo"):
        """
        Initialize the Summarization Manager agent.
        
        Args:
            model (str, optional): OpenAI model to use. Defaults to "gpt-3.5-turbo".
        """
        # Use proper agent description from content
        agent_info = AGENT_DESCRIPTIONS.get("summarization_manager", {
            "name": "Summarization Manager",
            "role": "Multi-Strategy Summarization Specialist",
            "goal": "Orchestrate and compare multiple summarization strategies to find the most effective approach",
            "backstory": "I'm an expert at summarizing complex documents using different approaches, comparing their effectiveness, and providing insights about which strategy works best for different document types."
        })
        
        super().__init__(
            name=agent_info.get("name", "Summarization Manager"),
            role=agent_info.get("role", "Multi-Strategy Summarization Specialist"),
            goal=agent_info.get("goal", "Orchestrate and compare multiple summarization strategies to find the most effective approach"),
            backstory=agent_info.get("backstory", "I'm an expert at summarizing complex documents using different approaches."),
            model=model
        )
        
        # Initialize the summarization processor
        self.summarization_processor = SummarizationProcessor()
        logger.info("Summarization Manager agent initialized")
    
    def generate_standard_summary(self, text, max_length=None):
        """
        Generate a standard summary of the document.
        
        Args:
            text (str): Document text
            max_length (int, optional): Maximum summary length. Defaults to None.
            
        Returns:
            dict: Standard summary results
        """
        logger.info("Generating standard summary")
        
        # Start tracking reasoning
        reasoning = ["Beginning standard document summarization"]
        
        # Process the document if needed
        if isinstance(text, str):
            reasoning.append("Pre-processing the document to normalize text")
            processed_doc = process_document(text)
            if isinstance(processed_doc, dict):
                doc_text = processed_doc["text"]
            else:
                doc_text = processed_doc
        else:
            doc_text = text
        
        reasoning.append(f"Calling summarization processor for standard summary with max_length={max_length}")
        
        # Track the summarization attempt
        self.track_activity(
            "start_standard_summarization",
            {"document_length": len(doc_text), "max_length": max_length},
            None,
            reasoning
        )
        
        # Call the processor to generate the summary
        result = self.summarization_processor.summarize_full_document(doc_text, max_length=max_length)
        
        # Track the completed summary
        self.track_activity(
            "complete_standard_summarization",
            {"document_length": len(doc_text)},
            {"summary_length": len(result.get("summary", "")) if isinstance(result.get("summary"), str) else 0},
            reasoning + ["Standard summarization completed"]
        )
        
        return result
    
    def generate_partitioned_summary(self, text, max_length=None):
        """
        Generate partition-based summaries.
        
        Args:
            text (str): Document text
            max_length (int, optional): Maximum summary length. Defaults to None.
            
        Returns:
            dict: Partitioned summary results
        """
        logger.info("Generating partition-based summary")
        
        # Start tracking reasoning
        reasoning = ["Beginning partition-based document summarization"]
        
        # Process the document if needed
        if isinstance(text, str):
            reasoning.append("Pre-processing the document to normalize text")
            processed_doc = process_document(text)
            if isinstance(processed_doc, dict):
                doc_text = processed_doc["text"]
            else:
                doc_text = processed_doc
        else:
            doc_text = text
        
        reasoning.append(f"Calling summarization processor for partition-based summary with max_length={max_length}")
        
        # Track the summarization attempt
        self.track_activity(
            "start_partitioned_summarization",
            {"document_length": len(doc_text), "max_length": max_length},
            None,
            reasoning
        )
        
        # Call the processor to generate the summary
        result = self.summarization_processor.summarize_by_partition(doc_text, max_length=max_length)
        
        # Extract info for tracking
        segment_count = result.get("segment_count", 0)
        meta_summary_length = len(result.get("meta_summary", "")) if isinstance(result.get("meta_summary"), str) else 0
        
        # Track the completed summary
        self.track_activity(
            "complete_partitioned_summarization",
            {"document_length": len(doc_text)},
            {"segment_count": segment_count, "meta_summary_length": meta_summary_length},
            reasoning + [f"Partition-based summarization completed with {segment_count} segments"]
        )
        
        return result
    
    def generate_entity_summary(self, text, max_length=None):
        """
        Generate entity-focused summaries.
        
        Args:
            text (str): Document text
            max_length (int, optional): Maximum summary length. Defaults to None.
            
        Returns:
            dict: Entity-focused summary results
        """
        logger.info("Generating entity-focused summary")
        
        # Start tracking reasoning
        reasoning = ["Beginning entity-focused document summarization"]
        
        # Process the document if needed
        if isinstance(text, str):
            reasoning.append("Pre-processing the document to normalize text")
            processed_doc = process_document(text)
            if isinstance(processed_doc, dict):
                doc_text = processed_doc["text"]
            else:
                doc_text = processed_doc
        else:
            doc_text = text
        
        reasoning.append(f"Calling summarization processor for entity-focused summary with max_length={max_length}")
        
        # Track the summarization attempt
        self.track_activity(
            "start_entity_summarization",
            {"document_length": len(doc_text), "max_length": max_length},
            None,
            reasoning
        )
        
        # Call the processor to generate the summary
        result = self.summarization_processor.summarize_by_entity(doc_text, max_length=max_length)
        
        # Extract info for tracking
        entity_count = result.get("entity_count", 0)
        meta_summary_length = len(result.get("meta_summary", "")) if isinstance(result.get("meta_summary"), str) else 0
        
        # Track the completed summary
        self.track_activity(
            "complete_entity_summarization",
            {"document_length": len(doc_text)},
            {"entity_count": entity_count, "meta_summary_length": meta_summary_length},
            reasoning + [f"Entity-focused summarization completed with {entity_count} entities"]
        )
        
        return result
    
    def generate_all_summaries(self, text, max_length=None):
        """
        Generate summaries using all strategies and compare them.
        
        Args:
            text (str): Document text
            max_length (int, optional): Maximum summary length. Defaults to None.
            
        Returns:
            dict: Comprehensive summary results
        """
        logger.info("Generating all summary types")
        
        # Start tracking reasoning
        reasoning = ["Beginning comprehensive multi-strategy summarization"]
        
        # Process the document if needed
        if isinstance(text, str):
            reasoning.append("Pre-processing the document to normalize text")
            processed_doc = process_document(text)
            if isinstance(processed_doc, dict):
                doc_text = processed_doc["text"]
            else:
                doc_text = processed_doc
        else:
            doc_text = text
        
        reasoning.append(f"Calling summarization processor for multi-strategy summary with max_length={max_length}")
        
        # Track the summarization attempt
        self.track_activity(
            "start_multi_strategy_summarization",
            {"document_length": len(doc_text), "max_length": max_length},
            None,
            reasoning
        )
        
        # Call the processor to generate all summaries
        multi_strategy_results = self.summarization_processor.generate_multi_strategy_summary(doc_text, max_length=max_length)
        
        # Add agent's educational reflection on the results
        reasoning.append("Adding agent's educational reflection on the summarization results")
        reflection_prompt = """
        Examine the multi-strategy summarization results and provide educational insights:
        
        1. What does this reveal about how AI processes documents differently using different approaches?
        2. Why do some summarization strategies work better than others for certain document types?
        3. How does document structure impact summarization quality?
        4. What are the educational takeaways about AI summarization that non-technical people should understand?
        
        Frame your response as an educational explanation that helps demystify how AI summarization works.
        
        Return your analysis in JSON format with these fields:
        - process_insights: what this reveals about AI document processing
        - strategy_comparison: why different strategies perform differently
        - structure_impact: how document structure affects summarization
        - key_takeaways: main educational points about AI summarization
        
        JSON response only:
        """
        
        try:
            # Get the combined summaries for reflection
            standard_summary = multi_strategy_results.get("standard_summary", "")
            partitioned_summary = (multi_strategy_results.get("partitioned_summary", {}) or {}).get("meta_summary", "")
            entity_summary = (multi_strategy_results.get("entity_summary", {}) or {}).get("meta_summary", "")
            comparative_analysis = multi_strategy_results.get("comparative_analysis", "")
            
            # Get the recommended approach
            recommended_approach = multi_strategy_results.get("recommended_approach", {})
            approach = recommended_approach.get("recommended_approach", "unknown")
            explanation = recommended_approach.get("explanation", "")
            
            reasoning.append(f"Recommended approach: {approach} - {explanation}")
            
            combined_text = f"""
            STANDARD SUMMARY:
            {standard_summary}
            
            PARTITION-BASED SUMMARY:
            {partitioned_summary}
            
            ENTITY-FOCUSED SUMMARY:
            {entity_summary}
            
            COMPARATIVE ANALYSIS:
            {comparative_analysis}
            
            RECOMMENDED APPROACH:
            {approach} - {explanation}
            
            ORIGINAL DOCUMENT EXCERPT:
            {doc_text[:1000]}...
            """
            
            # Track the educational reflection request
            self.track_activity(
                "prepare_educational_reflection",
                {"prompt_length": len(reflection_prompt)},
                {"combined_text_length": len(combined_text)},
                reasoning + ["Preparing educational reflection on summarization strategies"]
            )
            
            reflection_response = self.analyze(combined_text, specific_prompt=reflection_prompt)
            
            # Attempt to parse JSON response
            try:
                reflection = json.loads(reflection_response)
                reasoning.append("Successfully parsed educational reflection as JSON")
            except json.JSONDecodeError:
                reasoning.append("Could not parse educational reflection as JSON")
                reflection = {"raw_reflection": reflection_response}
            
            # Add reflection to the results
            multi_strategy_results["educational_reflection"] = reflection
            
            # Track the completed reflection
            self.track_activity(
                "complete_educational_reflection",
                {"prompt_length": len(reflection_prompt)},
                {"reflection_keys": list(reflection.keys())},
                reasoning + ["Educational reflection completed"]
            )
            
        except Exception as e:
            error_msg = f"Error generating summary reflection: {e}"
            logger.error(error_msg)
            reasoning.append(f"Error in educational reflection: {e}")
            multi_strategy_results["educational_reflection_error"] = str(e)
        
        # Track the completed multi-strategy summarization
        self.track_activity(
            "complete_multi_strategy_summarization",
            {"document_length": len(doc_text)},
            {"result_keys": list(multi_strategy_results.keys())},
            reasoning + ["Multi-strategy summarization completed"]
        )
        
        return multi_strategy_results
    
    def generate_custom_summary(self, text, approach_type, parameters=None):
        """
        Generate a summary with custom parameters.
        
        Args:
            text (str): Document text
            approach_type (str): Type of summary approach
            parameters (dict, optional): Custom parameters. Defaults to None.
            
        Returns:
            dict: Custom summary results
        """
        logger.info(f"Generating custom summary with approach: {approach_type}")
        
        # Start tracking reasoning
        reasoning = [f"Beginning custom summarization with approach: {approach_type}"]
        
        if parameters is None:
            parameters = {}
        
        max_length = parameters.get("max_length")
        reasoning.append(f"Parameters: max_length={max_length}")
        
        # Track the custom summarization request
        self.track_activity(
            "start_custom_summarization",
            {"document_length": len(text), "approach": approach_type, "parameters": parameters},
            None,
            reasoning
        )
        
        if approach_type == "standard":
            result = self.generate_standard_summary(text, max_length=max_length)
        elif approach_type == "partitioned":
            result = self.generate_partitioned_summary(text, max_length=max_length)
        elif approach_type == "entity":
            result = self.generate_entity_summary(text, max_length=max_length)
        elif approach_type == "all":
            result = self.generate_all_summaries(text, max_length=max_length)
        else:
            error_msg = f"Unknown summary approach type: {approach_type}"
            logger.error(error_msg)
            result = {"error": error_msg}
            
            # Track the error
            self.track_activity(
                "custom_summarization_error",
                {"document_length": len(text), "approach": approach_type},
                {"error": error_msg},
                reasoning + [f"Error: {error_msg}"]
            )
            
            return result
        
        # Track the completed custom summarization
        self.track_activity(
            "complete_custom_summarization",
            {"document_length": len(text), "approach": approach_type},
            {"result_keys": list(result.keys())},
            reasoning + [f"Custom summarization with approach '{approach_type}' completed"]
        )
        
        return result
    
    def create_educational_explanation(self, text, summary_results):
        """
        Create an educational explanation of the summarization strategies.
        
        Args:
            text (str): Original document text
            summary_results (dict): Results from multiple summarization strategies
            
        Returns:
            dict: Educational explanation
        """
        logger.info("Creating educational explanation of summarization strategies")
        
        # Start tracking reasoning
        reasoning = ["Beginning creation of educational explanation"]
        
        explanation_prompt = """
        Please create an educational explanation of different summarization strategies that helps non-technical people understand:
        
        1. Why different summarization approaches yield different results
        2. How document structure impacts summarization quality
        3. When each approach (standard, partition-based, entity-focused) would be most appropriate
        4. What this reveals about how AI actually processes documents
        5. Why AI is not "magic" but rather a set of techniques with specific strengths and limitations
        
        Make your explanation accessible to someone without a technical background in AI.
        
        Return your explanation in JSON format with these fields:
        - strategy_differences: explanation of why strategies yield different results
        - structure_impact: how document structure affects summaries
        - approach_recommendations: when each approach is most appropriate
        - ai_processing_insights: what this reveals about AI document processing
        - demystifying_ai: how this demonstrates that AI is not magic
        - key_takeaways: main lessons about document summarization
        
        JSON response only:
        """
        
        try:
            # Extract summaries from the results
            standard_summary = summary_results.get("standard_summary", "")
            
            partitioned_summary = "No partition summary available"
            if "partitioned_summary" in summary_results:
                partition_data = summary_results["partitioned_summary"]
                if isinstance(partition_data, dict):
                    partitioned_summary = partition_data.get("meta_summary", "")
            
            entity_summary = "No entity summary available"
            if "entity_summary" in summary_results:
                entity_data = summary_results["entity_summary"]
                if isinstance(entity_data, dict):
                    entity_summary = entity_data.get("meta_summary", "")
            
            comparative_analysis = summary_results.get("comparative_analysis", "")
            
            # Get the recommended approach
            recommended_approach = summary_results.get("recommended_approach", {})
            approach = recommended_approach.get("recommended_approach", "unknown")
            explanation = recommended_approach.get("explanation", "")
            
            reasoning.append(f"Extracted summary data and recommended approach: {approach}")
            
            combined_text = f"""
            STANDARD SUMMARY:
            {standard_summary}
            
            PARTITION-BASED SUMMARY:
            {partitioned_summary}
            
            ENTITY-FOCUSED SUMMARY:
            {entity_summary}
            
            COMPARATIVE ANALYSIS:
            {comparative_analysis}
            
            RECOMMENDED APPROACH:
            {approach} - {explanation}
            
            ORIGINAL DOCUMENT EXCERPT:
            {text[:1000]}...
            """
            
            # Track the educational explanation request
            self.track_activity(
                "prepare_educational_explanation",
                {"prompt_length": len(explanation_prompt)},
                {"combined_text_length": len(combined_text)},
                reasoning + ["Preparing educational explanation of summarization strategies"]
            )
            
            explanation_response = self.analyze(combined_text, specific_prompt=explanation_prompt)
            
            # Attempt to parse JSON response
            try:
                explanation = json.loads(explanation_response)
                reasoning.append("Successfully parsed educational explanation as JSON")
            except json.JSONDecodeError:
                reasoning.append("Could not parse educational explanation as JSON")
                explanation = {"raw_explanation": explanation_response}
            
            # Track the completed explanation
            self.track_activity(
                "complete_educational_explanation",
                {"prompt_length": len(explanation_prompt)},
                {"explanation_keys": list(explanation.keys())},
                reasoning + ["Educational explanation completed"]
            )
            
            return explanation
            
        except Exception as e:
            error_msg = f"Error creating educational explanation: {e}"
            logger.error(error_msg)
            
            # Track the error
            reasoning.append(f"Error in educational explanation: {e}")
            self.track_activity(
                "educational_explanation_error",
                {"document_length": len(text)},
                {"error": str(e)},
                reasoning
            )
            
            return {"error": str(e)}