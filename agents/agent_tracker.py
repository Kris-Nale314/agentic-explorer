# agents/agent_tracker.py
"""
Simple tracking system for agent activities and interactions.
Captures agent operations and generates visualizations of multi-agent processes.
"""

import time
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AgentTracker:
    """Track agent activities and interactions for visualization."""
    
    def __init__(self, session_name=None):
        """Initialize the agent tracker."""
        self.session_name = session_name or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.activities = []
        self.start_time = time.time()
        logger.info(f"Started tracking session: {self.session_name}")
    
    def log_activity(self, agent_name, activity_type, input_data, output_data, reasoning=None, metadata=None):
        """
        Log an agent activity.
        
        Args:
            agent_name (str): Name of the agent
            activity_type (str): Type of activity (e.g., "analyze", "detect_boundaries")
            input_data: The input to the activity
            output_data: The output from the activity
            reasoning (list, optional): List of reasoning steps
            metadata (dict, optional): Additional metadata
        """
        activity = {
            "timestamp": time.time(),
            "agent": agent_name,
            "activity": activity_type,
            "input": self._prepare_data(input_data),
            "output": self._prepare_data(output_data),
            "reasoning": reasoning or [],
            "metadata": metadata or {}
        }
        
        self.activities.append(activity)
        logger.debug(f"Logged activity for {agent_name}: {activity_type}")
        return activity
    
    def log_message(self, from_agent, to_agent, message, message_type="information"):
        """
        Log a message passed between agents.
        
        Args:
            from_agent (str): Sending agent name
            to_agent (str): Receiving agent name
            message: The message content
            message_type (str, optional): Type of message
        """
        message_record = {
            "timestamp": time.time(),
            "type": "message",
            "from_agent": from_agent,
            "to_agent": to_agent,
            "message": self._prepare_data(message),
            "message_type": message_type
        }
        
        self.activities.append(message_record)
        logger.debug(f"Logged message from {from_agent} to {to_agent}")
        return message_record
    
    def _prepare_data(self, data):
        """
        Prepare data for logging by making it serializable.
        
        Args:
            data: Any data to be logged
            
        Returns:
            Serializable version of the data
        """
        # If data is too large, truncate it
        if isinstance(data, str) and len(data) > 1000:
            return data[:1000] + "... [truncated]"
        
        # Try to make it JSON serializable
        try:
            json.dumps(data)
            return data
        except (TypeError, OverflowError):
            # If it's not serializable, convert to string
            return str(data)
    
    def export_json(self, file_path=None):
        """
        Export the tracked activities as JSON.
        
        Args:
            file_path (str, optional): Path to save the JSON file
            
        Returns:
            str: JSON string representation
        """
        session_data = {
            "session_name": self.session_name,
            "start_time": self.start_time,
            "end_time": time.time(),
            "duration": time.time() - self.start_time,
            "activities": self.activities
        }
        
        json_str = json.dumps(session_data, indent=2)
        
        if file_path:
            with open(file_path, 'w') as f:
                f.write(json_str)
            logger.info(f"Exported tracking data to {file_path}")
        
        return json_str
    
    def generate_markdown(self):
        """
        Generate a Markdown representation of the activities.
        
        Returns:
            str: Markdown content
        """
        if not self.activities:
            return "# Agent Activity Log\n\nNo activities recorded."
        
        markdown = [f"# Agent Activity Log: {self.session_name}\n"]
        markdown.append(f"Duration: {time.time() - self.start_time:.2f} seconds\n")
        
        # Group activities by agent
        agents = {}
        for activity in self.activities:
            if activity.get("type") == "message":
                continue
                
            agent_name = activity.get("agent")
            if agent_name not in agents:
                agents[agent_name] = []
            
            agents[agent_name].append(activity)
        
        # Add agent sections
        for agent_name, activities in agents.items():
            markdown.append(f"## Agent: {agent_name}\n")
            
            for idx, activity in enumerate(activities):
                markdown.append(f"### Activity {idx+1}: {activity['activity']}\n")
                markdown.append(f"Time: {datetime.fromtimestamp(activity['timestamp']).strftime('%H:%M:%S')}\n")
                
                # Add reasoning if available
                if activity.get("reasoning"):
                    markdown.append("\n#### Reasoning:\n")
                    for i, step in enumerate(activity["reasoning"]):
                        markdown.append(f"{i+1}. {step}\n")
                
                # Add truncated input/output info
                markdown.append("\n#### Input:\n```\n")
                markdown.append(str(activity["input"])[:500])
                if len(str(activity["input"])) > 500:
                    markdown.append("... [truncated]")
                markdown.append("\n```\n")
                
                markdown.append("\n#### Output:\n```\n")
                markdown.append(str(activity["output"])[:500])
                if len(str(activity["output"])) > 500:
                    markdown.append("... [truncated]")
                markdown.append("\n```\n")
        
        # Add message section
        messages = [a for a in self.activities if a.get("type") == "message"]
        if messages:
            markdown.append("## Agent Messages\n")
            for idx, msg in enumerate(messages):
                markdown.append(f"{idx+1}. **{msg['from_agent']}** → **{msg['to_agent']}**: {msg['message']}\n")
        
        return "\n".join(markdown)