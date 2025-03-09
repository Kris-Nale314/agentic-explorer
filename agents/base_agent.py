# agents/base_agent.py
"""
Base agent class providing common functionality for all specialized agents.
"""

import logging
from utils.openai_client import get_openai_client
from agents.agent_tracker import AgentTracker

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BaseAgent:
    """Base class for all agents in the Agentic Explorer system."""
    
    def __init__(self, name, role, goal, backstory=None, model="gpt-3.5-turbo"):
        """
        Initialize the base agent.
        
        Args:
            name (str): Agent name
            role (str): Agent role description
            goal (str): Primary goal for the agent
            backstory (str, optional): Agent backstory for context
            model (str, optional): OpenAI model to use. Defaults to "gpt-3.5-turbo".
        """
        self.name = name
        self.role = role
        self.goal = goal
        self.backstory = backstory or ""
        self.model = model
        self.openai_client = get_openai_client(model=model)
        
        logger.info(f"Initialized {name} agent with role '{role}'")
    
    def get_system_prompt(self):
        """
        Generate the system prompt for this agent based on its attributes.
        
        Returns:
            str: System prompt for the agent
        """
        return f"""
        You are {self.name}, a specialized AI agent with the role of {self.role}.
        
        Your goal is to {self.goal}.
        
        {self.backstory}
        
        Always focus on your specific expertise and provide detailed, well-reasoned responses.
        """
    
    def analyze(self, text, specific_prompt=None):
        """
        Analyze text according to the agent's specialty.
        
        Args:
            text (str): Text to analyze
            specific_prompt (str, optional): Additional specific instructions
            
        Returns:
            str: Analysis results
        """
        # Create a complete prompt combining system prompt, specific instructions, and text
        system_prompt = self.get_system_prompt()
        
        # Base prompt asks for structured analysis
        base_prompt = "Please analyze the following text according to your expertise."
        
        # Add specific instructions if provided
        if specific_prompt:
            base_prompt = f"{base_prompt}\n\n{specific_prompt}"
        
        # Add the text to analyze
        full_prompt = f"{base_prompt}\n\nTEXT TO ANALYZE:\n\n{text}"
        
        try:
            return self.openai_client.generate_completion(
                prompt=full_prompt,
                system_message=system_prompt,
                model=self.model
            )
        except Exception as e:
            logger.error(f"Error during analysis by {self.name}: {e}")
            return f"Analysis error: {e}"
    
    def reflect(self, original_analysis, question=None):
        """
        Reflect on a previous analysis to improve or clarify it.
        
        Args:
            original_analysis (str): The original analysis to reflect on
            question (str, optional): Specific question or direction for reflection
            
        Returns:
            str: Refined analysis
        """
        system_prompt = self.get_system_prompt()
        
        reflection_prompt = "Review your previous analysis and improve upon it."
        
        if question:
            reflection_prompt = f"Review your previous analysis and address the following question or issue:\n\n{question}"
        
        full_prompt = f"""
        Here is your previous analysis:
        
        {original_analysis}
        
        {reflection_prompt}
        
        Provide a refined and improved analysis that addresses any gaps or weaknesses in your original assessment.
        """
        
        try:
            return self.openai_client.generate_completion(
                prompt=full_prompt,
                system_message=system_prompt,
                model=self.model
            )
        except Exception as e:
            logger.error(f"Error during reflection by {self.name}: {e}")
            return f"Reflection error: {e}"


    def set_tracker(self, tracker=None):
        """
        Set an agent tracker to record this agent's activities.
        
        Args:
            tracker (AgentTracker, optional): Tracker to use, or create new one if None
        """
        self.tracker = tracker or AgentTracker()
        return self.tracker
    
    def track_activity(self, activity_type, input_data, output_data, reasoning=None, metadata=None):
        """
        Track an agent activity if tracking is enabled.
        
        Args:
            activity_type (str): Type of activity
            input_data: Input to the activity
            output_data: Output from the activity
            reasoning (list, optional): Reasoning steps
            metadata (dict, optional): Additional metadata
        """
        if hasattr(self, 'tracker'):
            return self.tracker.log_activity(
                self.name, 
                activity_type, 
                input_data, 
                output_data,
                reasoning, 
                metadata
            )
        return None