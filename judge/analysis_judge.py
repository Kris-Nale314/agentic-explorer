# agents/analysis_judge.py
"""
Analysis Judge agent specializing in synthesizing information and providing balanced insights.
"""

import logging
import json
from agents.base_agent import BaseAgent
from data.content import AGENT_DESCRIPTIONS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AnalysisJudgeAgent(BaseAgent):
    """Agent that synthesizes information from all sources to provide balanced insights."""
    
    def __init__(self, model="gpt-3.5-turbo"):
        """
        Initialize the Analysis Judge agent.
        
        Args:
            model (str, optional): OpenAI model to use. Defaults to "gpt-3.5-turbo".
        """
        agent_info = AGENT_DESCRIPTIONS["investment_judge"]
        
        super().__init__(
            name=agent_info["name"],
            role=agent_info["role"],
            goal=agent_info["goal"],
            backstory=agent_info["backstory"],
            model=model
        )
        
        logger.info("Analysis Judge agent initialized")
    
    def synthesize_analysis(self, document_text, boundary_analysis, document_classification, document_metrics=None, summarization_results=None):
        """
        Synthesize all analyses into a comprehensive evaluation.
        
        Args:
            document_text (str): Original document text
            boundary_analysis (dict): Results of boundary detection
            document_classification (list): Classification of document segments
            document_metrics (dict, optional): Document metrics results
            summarization_results (dict, optional): Summarization results
            
        Returns:
            dict: Synthesized analysis
        """
        logger.info("Synthesizing analysis from all sources")
        
        # Start tracking reasoning steps
        reasoning = ["Beginning synthesis of all analysis components"]
        reasoning.append("Examining document boundaries and classifications")
        
        # Create a structured prompt that includes all the analysis components
        synthesis_prompt = """
        Please synthesize the following analyses of a document into a comprehensive evaluation.
        
        First, here's a snippet of the original document:
        ```
        {document_excerpt}
        ```
        
        BOUNDARY ANALYSIS:
        {boundary_summary}
        
        DOCUMENT CLASSIFICATION:
        {classification_summary}
        
        {metrics_section}
        
        {summarization_section}
        
        Based on all this information, please provide:
        
        1. A holistic assessment of the document contents
        2. Key insights that emerge from combining these analyses
        3. Any conflicts or discrepancies between the different analyses
        4. Confidence assessment for the overall evaluation
        5. Recommendations for further analysis
        6. Educational insights about what this reveals about AI document processing
        
        Return your synthesis in JSON format with these fields:
        - holistic_assessment: overall evaluation
        - key_insights: array of insights from combined analyses
        - conflicts: any conflicts between analyses
        - confidence: overall confidence assessment (1-10 with explanation)
        - recommendations: recommendations for further analysis
        - educational_insights: what this reveals about AI document processing
        
        JSON response only:
        """
        
        # Format the boundary analysis summary
        try:
            if isinstance(boundary_analysis, dict):
                if "boundaries" in boundary_analysis:
                    boundary_count = len(boundary_analysis["boundaries"])
                    boundary_summary = f"Found {boundary_count} potential document boundaries with confidence score {boundary_analysis.get('confidence_score', 'N/A')}."
                    
                    # Add details about each boundary
                    boundary_details = []
                    for i, boundary in enumerate(boundary_analysis["boundaries"]):
                        if isinstance(boundary, dict):
                            pos = boundary.get("position", "unknown")
                            confidence = boundary.get("confidence", "unknown")
                            boundary_type = boundary.get("type", "unknown")
                            boundary_details.append(f"Boundary {i+1}: Position {pos}, Type {boundary_type}, Confidence {confidence}")
                    
                    if boundary_details:
                        boundary_summary += "\n" + "\n".join(boundary_details)
                else:
                    boundary_summary = "No clear document boundaries detected."
            else:
                boundary_summary = str(boundary_analysis)
                
            reasoning.append(f"Processed boundary analysis with {boundary_count if 'boundary_count' in locals() else 'unknown'} boundaries")
        except Exception as e:
            boundary_summary = f"Error processing boundary analysis: {e}"
            reasoning.append(f"Had difficulty processing boundary analysis: {e}")
        
        # Format the document classification summary
        try:
            if isinstance(document_classification, list):
                classification_parts = []
                for i, segment in enumerate(document_classification):
                    if isinstance(segment, dict) and "classification" in segment:
                        cls = segment["classification"]
                        if isinstance(cls, dict):
                            doc_type = cls.get("document_type", "Unknown")
                            entities = ", ".join(cls.get("entities", []))[:100]
                            time_period = cls.get("time_period", "Unknown")
                            topics = ", ".join(cls.get("topics", []))[:100]
                            classification_parts.append(f"Segment {i+1}: Type: {doc_type}, Entities: {entities}, Time: {time_period}, Topics: {topics}")
                
                classification_summary = "\n".join(classification_parts)
                reasoning.append(f"Processed classification for {len(classification_parts)} document segments")
            else:
                classification_summary = str(document_classification)
                reasoning.append("Processed document classification in non-standard format")
        except Exception as e:
            classification_summary = f"Error processing document classification: {e}"
            reasoning.append(f"Had difficulty processing document classification: {e}")
        
        # Format document metrics if available
        metrics_section = ""
        if document_metrics:
            try:
                if isinstance(document_metrics, dict):
                    word_count = document_metrics.get("word_count", "Unknown")
                    sentence_count = document_metrics.get("sentence_count", "Unknown")
                    paragraph_count = document_metrics.get("paragraph_count", "Unknown")
                    token_count = document_metrics.get("estimated_token_count", "Unknown")
                    
                    metrics_section = f"""
                    DOCUMENT METRICS:
                    Word Count: {word_count}
                    Sentence Count: {sentence_count}
                    Paragraph Count: {paragraph_count}
                    Estimated Token Count: {token_count}
                    """
                    
                    # Add most common words if available
                    if "most_common_words" in document_metrics:
                        common_words = document_metrics["most_common_words"]
                        if common_words:
                            metrics_section += "\nMost Common Words:\n"
                            for word, count in common_words:
                                metrics_section += f"- {word}: {count}\n"
                            
                    reasoning.append("Incorporated document metrics into analysis")
                else:
                    metrics_section = f"DOCUMENT METRICS:\n{str(document_metrics)[:300]}..."
                    reasoning.append("Processed document metrics in non-standard format")
            except Exception as e:
                metrics_section = f"Error processing document metrics: {e}"
                reasoning.append(f"Had difficulty processing document metrics: {e}")
        
        # Format summarization results if available
        summarization_section = ""
        if summarization_results:
            reasoning.append("Examining summarization results")
            try:
                if isinstance(summarization_results, dict):
                    # Standard summary
                    standard_summary = summarization_results.get("standard_summary", "")
                    
                    # Partitioned summary
                    partition_summary = ""
                    if "partitioned_summary" in summarization_results:
                        partition_data = summarization_results["partitioned_summary"]
                        if isinstance(partition_data, dict):
                            partition_summary = partition_data.get("meta_summary", "")
                    
                    # Entity summary
                    entity_summary = ""
                    if "entity_summary" in summarization_results:
                        entity_data = summarization_results["entity_summary"]
                        if isinstance(entity_data, dict):
                            entity_summary = entity_data.get("meta_summary", "")
                    
                    # Recommended approach
                    recommendation = ""
                    if "recommended_approach" in summarization_results:
                        rec_data = summarization_results["recommended_approach"]
                        if isinstance(rec_data, dict):
                            approach = rec_data.get("recommended_approach", "unknown")
                            explanation = rec_data.get("explanation", "")
                            recommendation = f"Recommended Approach: {approach}\nExplanation: {explanation}"
                    
                    summarization_section = f"""
                    SUMMARIZATION RESULTS:
                    
                    Standard Summary:
                    {standard_summary}
                    
                    Partition-Based Summary:
                    {partition_summary}
                    
                    Entity-Focused Summary:
                    {entity_summary}
                    
                    {recommendation}
                    """
                    
                    reasoning.append("Successfully processed multiple summarization approaches")
                else:
                    summarization_section = f"SUMMARIZATION RESULTS:\n{str(summarization_results)[:300]}..."
                    reasoning.append("Processed summarization results in non-standard format")
            except Exception as e:
                summarization_section = f"Error processing summarization results: {e}"
                reasoning.append(f"Had difficulty processing summarization results: {e}")
        
        # Create the formatted prompt
        document_excerpt = document_text[:1000] + "..." if len(document_text) > 1000 else document_text
        formatted_prompt = synthesis_prompt.format(
            document_excerpt=document_excerpt,
            boundary_summary=boundary_summary,
            classification_summary=classification_summary,
            metrics_section=metrics_section,
            summarization_section=summarization_section
        )
        
        reasoning.append("Sending synthesis request to AI model")
        
        try:
            # Track this activity
            self.track_activity(
                "prepare_synthesis",
                {"document_length": len(document_text)},
                {"prompt_length": len(formatted_prompt)},
                reasoning
            )
            
            # Send to model
            synthesis_response = self.analyze(document_text, specific_prompt=formatted_prompt)
            
            # Attempt to parse JSON response
            try:
                synthesis = json.loads(synthesis_response)
                reasoning.append("Successfully parsed synthesis response as JSON")
            except json.JSONDecodeError:
                reasoning.append("Could not parse synthesis as JSON, using raw response")
                synthesis = {"raw_synthesis": synthesis_response}
            
            # Track the completed synthesis
            self.track_activity(
                "complete_synthesis",
                {"prompt_length": len(formatted_prompt)},
                {"synthesis": synthesis},
                reasoning
            )
            
            return synthesis
            
        except Exception as e:
            error_msg = f"Error synthesizing analysis: {e}"
            logger.error(error_msg)
            
            # Track the error
            self.track_activity(
                "synthesis_error",
                {"document_length": len(document_text)},
                {"error": str(e)},
                reasoning
            )
            
            return {"error": str(e)}
    
    def evaluate_summarization_strategies(self, document_text, multi_strategy_summary):
        """
        Evaluate different summarization strategies and recommend the best approach.
        
        Args:
            document_text (str): Original document text
            multi_strategy_summary (dict): Results from multiple summarization strategies
            
        Returns:
            dict: Evaluation of summarization strategies
        """
        logger.info("Evaluating summarization strategies")
        
        # Start tracking reasoning steps
        reasoning = ["Beginning evaluation of summarization strategies"]
        
        evaluation_prompt = """
        Please evaluate the effectiveness of different summarization strategies for this document:
        
        First, here's a snippet of the original document:
        ```
        {document_excerpt}
        ```
        
        STANDARD SUMMARY:
        {standard_summary}
        
        PARTITION-BASED SUMMARY:
        {partition_summary}
        
        ENTITY-FOCUSED SUMMARY:
        {entity_summary}
        
        Based on these summaries, please evaluate:
        
        1. Information preservation: How well does each approach preserve key information?
        2. Coherence: How coherent and readable is each summary?
        3. Context handling: How well does each approach handle context shifts?
        4. Entity coverage: How well does each approach cover important entities?
        5. Overall effectiveness: Which approach is most effective for this document and why?
        6. Educational value: What does this comparison teach us about AI summarization?
        
        Return your evaluation in JSON format with these fields:
        - standard_evaluation: assessment of standard approach
        - partition_evaluation: assessment of partition-based approach
        - entity_evaluation: assessment of entity-focused approach
        - comparative_scores: numerical scores (1-10) for each approach on the criteria
        - recommended_approach: which approach is best with explanation
        - educational_insights: what this comparison teaches about AI summarization
        
        JSON response only:
        """
        
        try:
            reasoning.append("Extracting summaries from the multi-strategy results")
            
            # Extract summaries from the results
            standard_summary = multi_strategy_summary.get("standard_summary", "No standard summary available")
            
            partition_summary = "No partition summary available"
            if "partitioned_summary" in multi_strategy_summary:
                partition_summary = multi_strategy_summary["partitioned_summary"].get("meta_summary", "No meta-summary available")
            
            entity_summary = "No entity summary available"
            if "entity_summary" in multi_strategy_summary:
                entity_summary = multi_strategy_summary["entity_summary"].get("meta_summary", "No meta-summary available")
            
            reasoning.append("Successfully extracted all summary types")
            
            # Create the formatted prompt
            document_excerpt = document_text[:1000] + "..." if len(document_text) > 1000 else document_text
            formatted_prompt = evaluation_prompt.format(
                document_excerpt=document_excerpt,
                standard_summary=standard_summary,
                partition_summary=partition_summary,
                entity_summary=entity_summary
            )
            
            reasoning.append("Sending evaluation request to AI model")
            
            # Track this activity
            self.track_activity(
                "prepare_evaluation",
                {"document_length": len(document_text)},
                {"prompt_length": len(formatted_prompt)},
                reasoning
            )
            
            evaluation_response = self.analyze(document_text, specific_prompt=formatted_prompt)
            
            # Attempt to parse JSON response
            try:
                evaluation = json.loads(evaluation_response)
                reasoning.append("Successfully parsed evaluation response as JSON")
            except json.JSONDecodeError:
                reasoning.append("Could not parse evaluation as JSON, using raw response")
                evaluation = {"raw_evaluation": evaluation_response}
            
            # Track the completed evaluation
            self.track_activity(
                "complete_evaluation",
                {"prompt_length": len(formatted_prompt)},
                {"evaluation": evaluation},
                reasoning
            )
            
            return evaluation
            
        except Exception as e:
            error_msg = f"Error evaluating summarization strategies: {e}"
            logger.error(error_msg)
            
            # Track the error
            self.track_activity(
                "evaluation_error",
                {"document_length": len(document_text)},
                {"error": str(e)},
                reasoning + [f"Encountered error: {e}"]
            )
            
            return {"error": str(e)}
    
    def create_educational_report(self, document_text, analysis_results):
        """
        Create an educational report explaining what this analysis reveals about AI processing.
        
        Args:
            document_text (str): Original document text
            analysis_results (dict): Combined results from all analyses
            
        Returns:
            dict: Educational report
        """
        logger.info("Creating educational report")
        
        # Start tracking reasoning steps
        reasoning = ["Beginning creation of educational report"]
        
        report_prompt = """
        Create an educational report that explains what this document analysis reveals about how AI systems process and understand documents.
        
        The report should:
        
        1. Explain the challenges AI faces when processing mixed documents
        2. Highlight how different summarization strategies impact understanding
        3. Show how detecting document boundaries affects AI performance
        4. Discuss entity confusion and how it leads to hallucinations
        5. Provide clear explanations suitable for non-technical audiences
        
        The goal is to demystify AI and show that it's not "magic" but a process with specific strengths and weaknesses.
        
        Here's a snippet of the original document:
        ```
        {document_excerpt}
        ```
        
        And here are the analysis results:
        {analysis_summary}
        
        Return your educational report in JSON format with these sections:
        - introduction: What this report demonstrates about AI
        - boundary_detection: How boundary detection impacts understanding
        - summarization_strategies: How different approaches yield different results
        - entity_handling: How AI tracks and sometimes confuses entities
        - hallucination_risks: How document structure contributes to hallucination
        - best_practices: Recommendations for better AI document processing
        
        JSON response only:
        """
        
        try:
            reasoning.append("Creating summary of analysis results for educational report")
            
            # Format all analyses into a summary string
            analysis_summary = "ANALYSIS SUMMARY:\n"
            
            analysis_items = []
            
            if "boundaries" in analysis_results:
                boundary_count = len(analysis_results.get("boundaries", {}).get("boundaries", []))
                analysis_items.append(f"- Boundary Detection: Found {boundary_count} potential document boundaries")
            
            if "metrics" in analysis_results:
                metrics = analysis_results["metrics"]
                analysis_items.append(f"- Document Metrics: {metrics.get('word_count', 'N/A')} words, {metrics.get('sentence_count', 'N/A')} sentences")
            
            if "multi_strategy_summary" in analysis_results and "recommended_approach" in analysis_results["multi_strategy_summary"]:
                rec = analysis_results["multi_strategy_summary"]["recommended_approach"]
                analysis_items.append(f"- Recommended Summarization: {rec.get('recommended_approach', 'N/A')} - {rec.get('explanation', 'N/A')}")
            
            analysis_summary += "\n".join(analysis_items)
            
            reasoning.append("Successfully created analysis summary")
            
            # Create the formatted prompt
            document_excerpt = document_text[:1000] + "..." if len(document_text) > 1000 else document_text
            formatted_prompt = report_prompt.format(
                document_excerpt=document_excerpt,
                analysis_summary=analysis_summary
            )
            
            reasoning.append("Sending educational report request to AI model")
            
            # Track this activity
            self.track_activity(
                "prepare_educational_report",
                {"document_length": len(document_text)},
                {"prompt_length": len(formatted_prompt)},
                reasoning
            )
            
            report_response = self.analyze(document_text, specific_prompt=formatted_prompt)
            
            # Attempt to parse JSON response
            try:
                report = json.loads(report_response)
                reasoning.append("Successfully parsed educational report as JSON")
            except json.JSONDecodeError:
                reasoning.append("Could not parse educational report as JSON, using raw response")
                report = {"raw_report": report_response}
            
            # Track the completed report
            self.track_activity(
                "complete_educational_report",
                {"prompt_length": len(formatted_prompt)},
                {"report": report},
                reasoning
            )
            
            return report
            
        except Exception as e:
            error_msg = f"Error creating educational report: {e}"
            logger.error(error_msg)
            
            # Track the error
            self.track_activity(
                "educational_report_error",
                {"document_length": len(document_text)},
                {"error": str(e)},
                reasoning + [f"Encountered error: {e}"]
            )
            
            return {"error": str(e)}