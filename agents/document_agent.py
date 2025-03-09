# agents/document_agent.py
"""
Document Analyzer agent specializing in document metrics and structure analysis.
"""

import logging
import json
from agents.base_agent import BaseAgent
from processors.document_analyzer import DocumentAnalyzer as DocumentAnalyzerProcessor
from processors.partitioning_strategies import DocumentPartitioner
from processors.text_processor import process_document
from data.content import AGENT_DESCRIPTIONS, TASK_DESCRIPTIONS
from agents.agent_tracker import AgentTracker

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DocumentAnalyzerAgent(BaseAgent):
    """Agent that specializes in analyzing document metrics and structure."""
    
    def __init__(self, model="gpt-3.5-turbo"):
        """
        Initialize the Document Analyzer agent.
        
        Args:
            model (str, optional): OpenAI model to use. Defaults to "gpt-3.5-turbo".
        """
        # Use proper agent description from content
        agent_info = AGENT_DESCRIPTIONS.get("document_analyzer", {
            "name": "Document Analyzer",
            "role": "Document Metrics and Structure Analyst",
            "goal": "Compute metrics, extract structures, and identify patterns across documents",
            "backstory": "I specialize in analyzing document structures, calculating metrics, and identifying patterns that reveal how documents are organized and composed."
        })
        
        super().__init__(
            name=agent_info.get("name", "Document Analyzer"),
            role=agent_info.get("role", "Document Metrics and Structure Analyst"),
            goal=agent_info.get("goal", "Compute metrics, extract structures, and identify patterns across documents"),
            backstory=agent_info.get("backstory", "I specialize in analyzing document structures, calculating metrics, and identifying patterns."),
            model=model
        )
        
        # Initialize the processors
        self.analyzer_processor = DocumentAnalyzerProcessor()
        self.partitioner = DocumentPartitioner()
        logger.info("Document Analyzer agent initialized")
    
    def compute_document_metrics(self, text):
        """
        Compute comprehensive metrics for a document.
        
        Args:
            text (str): Document text
            
        Returns:
            dict: Document metrics
        """
        logger.info("Computing document metrics")
        
        # Start tracking reasoning
        reasoning = ["Beginning document metrics computation"]
        
        # Process the document if it's not already processed
        if isinstance(text, str):
            reasoning.append("Pre-processing the document to normalize text")
            processed_doc = process_document(text)
            if isinstance(processed_doc, dict):
                doc_text = processed_doc["text"]
                # Include any metadata from processing
                reasoning.append(f"Document processing metadata: {processed_doc.get('metadata', {})}")
            else:
                doc_text = processed_doc
        else:
            doc_text = text
            
        reasoning.append("Getting basic metrics from document analyzer processor")
        
        # Get basic metrics from the processor
        basic_metrics = self.analyzer_processor.compute_basic_metrics(doc_text)
        reasoning.append(f"Basic metrics calculated: {len(basic_metrics)} properties")
        
        # Track the activity
        self.track_activity(
            "compute_basic_metrics",
            {"document_length": len(doc_text)},
            {"metrics": basic_metrics},
            reasoning
        )
        
        # Enhance with AI-derived metrics
        reasoning.append("Requesting enhanced metrics with AI analysis")
        enhanced_metrics_prompt = f"""
        Please analyze the following document and provide enhanced metrics:
        
        1. Readability scores (estimate):
           - Approximate reading grade level
           - Clarity rating (1-10)
           
        2. Content structure:
           - Identify major sections and their sizes
           - Estimate percentage of factual vs. opinion content
           
        3. Language characteristics:
           - Formality level (1-10)
           - Technical complexity (1-10)
           - Domain-specific terminology density
        
        Return your analysis in JSON format for easy parsing.
        
        TEXT SAMPLE (excerpt):
        {doc_text[:1500]}...
        
        JSON response only:
        """
        
        try:
            enhanced_response = self.analyze(doc_text, specific_prompt=enhanced_metrics_prompt)
            
            # Attempt to parse JSON response
            try:
                enhanced_metrics = json.loads(enhanced_response)
                reasoning.append("Successfully parsed enhanced metrics from AI response")
            except json.JSONDecodeError:
                reasoning.append("Could not parse enhanced metrics as JSON")
                enhanced_metrics = {"raw_analysis": enhanced_response}
            
            # Combine metrics
            combined_metrics = {**basic_metrics, "enhanced_metrics": enhanced_metrics}
            
            # Track the enhanced metrics activity
            self.track_activity(
                "compute_enhanced_metrics",
                {"prompt_length": len(enhanced_metrics_prompt)},
                {"enhanced_metrics": enhanced_metrics},
                reasoning
            )
            
            return combined_metrics
            
        except Exception as e:
            error_msg = f"Error computing enhanced metrics: {e}"
            logger.error(error_msg)
            
            # Track the error
            reasoning.append(f"Error encountered: {e}")
            self.track_activity(
                "enhanced_metrics_error",
                {"prompt_length": len(enhanced_metrics_prompt)},
                {"error": str(e)},
                reasoning
            )
            
            return basic_metrics
    
    def analyze_document_structure(self, text, section_count=None):
        """
        Analyze the document's structure.
        
        Args:
            text (str): Document text
            section_count (int, optional): Target number of sections. Defaults to None (auto-determine).
            
        Returns:
            dict: Document structure analysis
        """
        logger.info("Analyzing document structure")
        
        # Start tracking reasoning
        reasoning = ["Beginning document structure analysis"]
        
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
        
        # Calculate appropriate section count if not provided
        if section_count is None:
            # Rough heuristic: 1 section per ~1000 words, min 3, max 10
            word_count = len(doc_text.split())
            section_count = max(3, min(10, word_count // 1000 + 2))
            reasoning.append(f"Auto-determined section count: {section_count} based on document length")
        
        # Get potential document partitions
        try:
            reasoning.append("Attempting to partition document by detected boundaries")
            segments = self.partitioner.partition_by_detected_boundaries(doc_text)
            reasoning.append(f"Document partitioned into {len(segments)} segments")
            
            # If we got too many segments, try to group them
            if len(segments) > section_count + 5:
                reasoning.append(f"Too many segments ({len(segments)}), combining to approach target count ({section_count})")
                # Group segments to get closer to the target section count
                grouped_segments = []
                group_size = max(1, len(segments) // section_count)
                
                for i in range(0, len(segments), group_size):
                    group = segments[i:i+group_size]
                    grouped_segments.append("\n\n".join(group))
                
                segments = grouped_segments
                reasoning.append(f"Grouped into {len(segments)} segments")
        except Exception as e:
            reasoning.append(f"Error partitioning document: {e}")
            reasoning.append("Falling back to paragraph-based partitioning")
            segments = self.partitioner.partition_by_paragraph_groups(doc_text)
        
        # Generate structure analysis prompt
        structure_prompt = f"""
        Please analyze the structure of the following document and segment it into approximately {section_count} logical sections.
        
        For each section you identify:
        1. Provide a concise title
        2. Identify the key topics or themes
        3. Summarize the key content in 1-2 sentences
        4. Rate the importance of the section to the overall document (1-10)
        
        Return your analysis as structured JSON with an array of sections containing:
        - title
        - topics (array of key topics)
        - summary 
        - importance_score (1-10)
        
        Document has been pre-segmented into {len(segments)} parts. Here are the segment previews:
        
        {chr(10).join([f"SEGMENT {i+1}: {s[:150]}..." for i, s in enumerate(segments)])}
        
        JSON response only:
        """
        
        try:
            # Track segments analysis preparation
            self.track_activity(
                "prepare_structure_analysis",
                {"segment_count": len(segments)},
                {"prompt_length": len(structure_prompt)},
                reasoning
            )
            
            structure_response = self.analyze(doc_text, specific_prompt=structure_prompt)
            
            # Attempt to parse JSON response
            try:
                structure_analysis = json.loads(structure_response)
                reasoning.append("Successfully parsed structure analysis as JSON")
            except json.JSONDecodeError:
                reasoning.append("Could not parse structure analysis as JSON")
                structure_analysis = {"raw_analysis": structure_response}
            
            # Track the completed analysis
            self.track_activity(
                "complete_structure_analysis",
                {"prompt_length": len(structure_prompt)},
                {"structure_analysis": structure_analysis},
                reasoning + ["Structure analysis completed successfully"]
            )
            
            return structure_analysis
            
        except Exception as e:
            error_msg = f"Error analyzing document structure: {e}"
            logger.error(error_msg)
            
            # Track the error
            reasoning.append(f"Error encountered: {e}")
            self.track_activity(
                "structure_analysis_error",
                {"prompt_length": len(structure_prompt)},
                {"error": str(e)},
                reasoning
            )
            
            return {"error": str(e)}
    
    def extract_key_entities(self, text):
        """
        Extract key entities from the document.
        
        Args:
            text (str): Document text
            
        Returns:
            dict: Extracted entities
        """
        logger.info("Extracting key entities")
        
        # Start tracking reasoning
        reasoning = ["Beginning key entity extraction"]
        
        # Use the boundary analysis from the processor, which also extracts entities
        reasoning.append("Using document boundary analysis to identify entities")
        boundary_analysis = self.analyzer_processor.analyze_document_boundaries(text)
        
        # Extract entities from boundary analysis
        entities = boundary_analysis.get('entities', [])
        reasoning.append(f"Found {len(entities)} entities in boundary analysis")
        
        # If we didn't get enough entities, use AI to extract more
        if len(entities) < 3:
            reasoning.append("Not enough entities found, using AI to extract more")
            
            entity_prompt = """
            Please extract key entities from the following document, organized by type:
            
            1. Organizations (companies, agencies, institutions)
            2. People (names, roles, relationships)
            3. Locations (countries, cities, regions)
            4. Temporal references (dates, time periods, events)
            5. Financial metrics (monetary values, percentages, statistics)
            
            For each entity, provide:
            - Name/identifier
            - Category
            - Frequency of mention (estimate)
            - Contextual importance (1-10)
            
            Return as structured JSON with an entity array:
            
            Document:
            {text}
            
            JSON response only:
            """
            
            try:
                # Track entity extraction preparation
                self.track_activity(
                    "prepare_entity_extraction",
                    {"document_length": len(text)},
                    {"boundary_entities": entities},
                    reasoning
                )
                
                entity_response = self.analyze(text, specific_prompt=entity_prompt)
                
                # Attempt to parse JSON response
                try:
                    entity_analysis = json.loads(entity_response)
                    reasoning.append("Successfully parsed entity analysis as JSON")
                except json.JSONDecodeError:
                    reasoning.append("Could not parse entity analysis as JSON")
                    entity_analysis = {"raw_analysis": entity_response}
                
                # Track the completed extraction
                self.track_activity(
                    "complete_entity_extraction",
                    {"prompt_length": len(entity_prompt)},
                    {"entity_analysis": entity_analysis},
                    reasoning + ["Entity extraction completed successfully"]
                )
                
                return entity_analysis
                
            except Exception as e:
                error_msg = f"Error extracting entities: {e}"
                logger.error(error_msg)
                
                # Track the error
                reasoning.append(f"Error encountered: {e}")
                self.track_activity(
                    "entity_extraction_error",
                    {"prompt_length": len(entity_prompt)},
                    {"error": str(e)},
                    reasoning
                )
                
                # Return whatever we got from boundary analysis
                return {"entities": entities, "error": str(e)}
        else:
            # Format entities from boundary analysis
            entity_results = {"entities": []}
            
            for entity in entities:
                entity_results["entities"].append({
                    "name": entity,
                    "category": "Unknown",  # We don't have categories from boundary analysis
                    "frequency": "Unknown",
                    "importance": 5  # Default importance
                })
            
            # Track the entity extraction
            self.track_activity(
                "extract_entities_from_boundaries",
                {"document_length": len(text)},
                {"entity_results": entity_results},
                reasoning + [f"Using {len(entities)} entities from boundary analysis"]
            )
            
            return entity_results
    
    def analyze_document(self, text):
        """
        Perform a comprehensive document analysis.
        
        Args:
            text (str): Document text
            
        Returns:
            dict: Full document analysis
        """
        logger.info("Performing comprehensive document analysis")
        
        # Start tracking reasoning
        reasoning = ["Beginning comprehensive document analysis"]
        
        try:
            # Track that we're starting the analysis
            self.track_activity(
                "start_comprehensive_analysis",
                {"document_length": len(text)},
                None,
                reasoning
            )
            
            # Collect all the different analyses
            reasoning.append("Computing document metrics")
            metrics = self.compute_document_metrics(text)
            
            reasoning.append("Analyzing document structure")
            structure = self.analyze_document_structure(text)
            
            reasoning.append("Extracting key entities")
            entities = self.extract_key_entities(text)
            
            # Combine into a comprehensive analysis
            comprehensive_analysis = {
                "metrics": metrics,
                "structure": structure,
                "entities": entities
            }
            
            # Add a meta-analysis that ties everything together
            reasoning.append("Generating meta-analysis to tie everything together")
            meta_prompt = """
            Based on the metrics, structure, and entity analysis of this document, please provide:
            
            1. Overall document assessment (quality, coherence, organization)
            2. Key insights that combine multiple aspects of the analysis
            3. Educational explanation of what this reveals about document structure and AI processing
            4. Recommendations for how to better understand or process this document
            
            Return your analysis in JSON format with these fields:
            - assessment: overall quality and characteristics
            - key_insights: array of insights
            - educational_explanation: what this reveals about AI document processing
            - recommendations: array of recommendations
            
            JSON response only:
            """
            
            meta_response = self.analyze(text, specific_prompt=meta_prompt)
            
            # Attempt to parse JSON response
            try:
                meta_analysis = json.loads(meta_response)
                reasoning.append("Successfully parsed meta-analysis as JSON")
                comprehensive_analysis["meta_analysis"] = meta_analysis
            except json.JSONDecodeError:
                reasoning.append("Could not parse meta-analysis as JSON")
                comprehensive_analysis["meta_analysis"] = {"raw_analysis": meta_response}
            
            # Track the completed analysis
            self.track_activity(
                "complete_comprehensive_analysis",
                {"document_length": len(text)},
                {"analysis_keys": list(comprehensive_analysis.keys())},
                reasoning + ["Comprehensive analysis completed successfully"]
            )
            
            return comprehensive_analysis
            
        except Exception as e:
            error_msg = f"Error in comprehensive document analysis: {e}"
            logger.error(error_msg)
            
            # Track the error
            reasoning.append(f"Error encountered: {e}")
            self.track_activity(
                "comprehensive_analysis_error",
                {"document_length": len(text)},
                {"error": str(e)},
                reasoning
            )
            
            return {"error": str(e), "partial_results": locals().get('comprehensive_analysis', {})}