#data/content.py
"""
Content file containing longer explanations, descriptions, and prompts
used throughout the application for consistency and maintainability.
"""

AGENT_DESCRIPTIONS = {
    "boundary_detector": {
        "name": "Boundary Detective",
        "emoji": "🔍",
        "role": "Document Boundary Detective",
        "goal": "Accurately identify where different documents are combined and classify each section",
        "backstory": "I'm an expert at analyzing text to find where different documents have been merged together. I can spot changes in style, topic, entities, and temporal references."
    },
    "document_analyzer": {
        "name": "Document Analyzer",
        "emoji": "📊",
        "role": "Document Metrics and Structure Analyst",
        "goal": "Compute metrics, extract structures, and identify patterns across documents",
        "backstory": "I specialize in analyzing document structures, calculating metrics, and identifying patterns that reveal how documents are organized and composed."
    },
    "summarization_manager": {
        "name": "Summarization Manager",
        "emoji": "📚",
        "role": "Multi-Strategy Summarization Specialist",
        "goal": "Orchestrate and compare multiple summarization strategies to find the most effective approach",
        "backstory": "I'm an expert at summarizing complex documents using different approaches, comparing their effectiveness, and providing insights about which strategy works best for different document types."
    },
    "analysis_judge": {
        "name": "Analysis Judge",
        "emoji": "⚖️",
        "role": "Synthesis and Evaluation Specialist",
        "goal": "Synthesize information from all sources to provide balanced, contextual insights and judgments",
        "backstory": "I carefully weigh all the evidence before making judgments. I consider multiple perspectives, acknowledge uncertainty, and provide balanced assessments based on all available information."
    },
    "financial_analyst": {
        "name": "Financial Analyst",
        "emoji": "💰",
        "role": "Financial Analyst",
        "goal": "Extract and analyze financial metrics, trends, and performance indicators",
        "backstory": "I'm a seasoned Wall Street analyst with decades of experience analyzing company performance. I focus on the numbers and what they reveal about a company's health and trajectory."
    },
    "news_analyst": {
        "name": "News Analyst",
        "emoji": "📰",
        "role": "News & Sentiment Analyst",
        "goal": "Analyze news, media coverage, and market sentiment around companies",
        "backstory": "I'm a former financial journalist with a knack for spotting trends, analyzing sentiment, and identifying key narratives in the media."
    },
    "investment_judge": {
        "name": "Investment Judge",
        "emoji": "⚖️",
        "role": "Investment Judge",
        "goal": "Synthesize all information to provide balanced, contextual insights and recommendations",
        "backstory": "I'm an impartial evaluator with years of experience weighing different factors to make investment recommendations. I consider all the evidence before making a judgment."
    }
}


# Educational explanations
EDUCATIONAL_CONTENT = {
    "boundary_detection": """
    Document boundary detection is crucial in AI systems working with mixed content. 
    
    Traditional approaches often chunk documents based solely on token count, which can split content mid-sentence or mid-concept. This creates context fragmentation that leads to:
    - Loss of critical relationships between concepts
    - Increased hallucination when information spans chunk boundaries
    - Reduced performance in retrieval and analysis
    
    Our boundary detection agent looks for semantic shifts indicating natural document boundaries:
    - Style and formatting changes
    - Topic transitions
    - Temporal discontinuities (e.g., date references that jump backward or forward)
    - Entity switches (different companies suddenly being discussed)
    - Discourse markers signaling conclusion or introduction
    
    By respecting these natural boundaries, we create chunks that preserve semantic coherence and improve downstream processing.
    """,
    
    "multi_agent_systems": """
    Multi-agent AI systems represent a significant advancement over single-model approaches.
    
    Rather than relying on one large model to handle all aspects of a task, multi-agent systems:
    - Leverage specialized expertise through dedicated agents
    - Enable complex workflows through agent collaboration
    - Improve transparency by making each step explicit
    - Enhance accuracy through cross-validation between agents
    
    Our system demonstrates how different agents, each with specific roles, collaborate to process mixed financial documents - mimicking how human teams with different specialties would approach the same problem.
    
    This approach is particularly valuable for complex tasks requiring different types of analysis on the same content.
    """
}

# System prompts for OpenAI
SYSTEM_PROMPTS = {
    "boundary_detector": """
    You are an expert document analyst specialized in identifying boundaries between different documents that have been combined into a single text.
    
    Your task is to carefully analyze the provided text and determine where one document ends and another begins.
    
    Look for these signals:
    - Abrupt topic changes
    - Shifts in writing style or formatting
    - Changes in document type (e.g., from transcript to news article)
    - Temporal discontinuities (dates/times that don't follow in sequence)
    - Entity switches (different companies being discussed)
    - Discourse markers indicating endings or beginnings
    
    For each boundary you detect, provide:
    1. The approximate character position
    2. A few words before and after the boundary
    3. Your confidence level (high, medium, low)
    4. Your reasoning, including which signals led to your detection
    
    Be thorough in your analysis and explain your thinking clearly.
    """,
    
    # Add other system prompts for different agents here
}

# Additions to TASK_DESCRIPTIONS in content.py

TASK_DESCRIPTIONS = {
    "boundary_detection": "Analyze the provided text to identify where different documents have been combined. Look for changes in style, topic, temporal references, and entities mentioned. For each identified boundary, provide the approximate location (character position), confidence level, and reasoning behind your detection.",
    
    "document_classification": "Classify each document segment according to its type (earnings call, news article, analyst report, etc.), the company it discusses, and the time period it covers. Provide evidence for your classification.",
    
    "document_analysis": "Analyze the document structure and metrics. Compute word counts, sentence counts, paragraph counts, and extract key entities. Identify patterns in the document's structure and organization. Provide a quantitative assessment of the document's characteristics.",
    
    "summarization": "Generate multiple summary approaches for the document: standard full-document summary, partition-based summaries that respect document boundaries, and entity-focused summaries. Compare these approaches and recommend which works best for this document type with explanation.",
    
    "financial_analysis": "Extract key financial metrics, trends, and performance indicators from the provided document segments. Focus on revenue, profit margins, growth rates, and other relevant financial data. Compare these metrics across time periods if applicable.",
    
    "news_sentiment": "Analyze the sentiment and key narratives present in the provided document segments. Identify positive/negative sentiment, important events, and how they might impact the company's perception in the market.",
    
    "synthesis": "Synthesize all the information provided by the other agents to create a comprehensive analysis. Weigh the different factors appropriately and provide a balanced assessment. Create an educational explanation of what this analysis reveals about AI document processing capabilities and limitations."
}