# analysis.py
"""
Core CrewAI setup and task definitions for the Agentic Explorer.
This module defines the agents and their interactions, creating the multi-agent system.
"""

import os
import json
import logging
from dotenv import load_dotenv
from crewai import Crew, Agent, Task, Process
from langchain_community.chat_models import ChatOpenAI
from data.content import AGENT_DESCRIPTIONS, TASK_DESCRIPTIONS
from processors.document_analyzer import DocumentAnalyzer
from processors.summarization_manager import SummarizationManager
from agents.agent_tracker import AgentTracker
from agents.boundary_detective import BoundaryDetectiveAgent
from agents.document_agent import DocumentAnalyzerAgent
from agents.summarization_agent import SummarizationAgent
from judge.analysis_judge import AnalysisJudgeAgent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_tracked_crew(document_text, session_name=None, output_dir="output"):
    """
    Create and return a CrewAI crew with activity tracking for educational purposes.
    
    Args:
        document_text (str): The text to be analyzed
        session_name (str, optional): Name for the tracking session
        output_dir (str, optional): Directory to save tracking outputs
        
    Returns:
        tuple: (crew, tracker, agent_dict) - The crew, tracker instance, and dictionary of agents
    """
    # Initialize tracking
    tracker = AgentTracker(session_name=session_name or "document_analysis_session")
    
    # Create directory for outputs if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info("Creating agents with activity tracking...")
    
    # Initialize our local agents with tracking
    boundary_agent = BoundaryDetectiveAgent()
    boundary_agent.set_tracker(tracker)
    
    document_agent = DocumentAnalyzerAgent()
    document_agent.set_tracker(tracker)
    
    summarization_agent = SummarizationAgent()
    summarization_agent.set_tracker(tracker)
    
    judge_agent = AnalysisJudgeAgent()
    judge_agent.set_tracker(tracker)
    
    # Initialize the LLM for CrewAI using langchain
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.7,
        verbose=True
    )
    
    # Record initial state before creating CrewAI agents
    tracker.log_activity(
        "system",
        "initialize_agents",
        {"document_length": len(document_text)},
        {
            "boundary_agent": boundary_agent.name,
            "document_agent": document_agent.name,
            "summarization_agent": summarization_agent.name,
            "judge_agent": judge_agent.name
        },
        reasoning=["Initialized all agents with tracking capabilities"]
    )
    
    # Create CrewAI agents with langchain LLM
    crew_boundary_agent = Agent(
        role=boundary_agent.role,
        goal=boundary_agent.goal,
        backstory=boundary_agent.backstory,
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
    
    crew_document_agent = Agent(
        role=document_agent.role,
        goal=document_agent.goal,
        backstory=document_agent.backstory,
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
    
    crew_summarization_agent = Agent(
        role=summarization_agent.role,
        goal=summarization_agent.goal,
        backstory=summarization_agent.backstory,
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
    
    crew_judge_agent = Agent(
        role=judge_agent.role,
        goal=judge_agent.goal,
        backstory=judge_agent.backstory,
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
    
    # Map the CrewAI agents to our tracked agents
    agent_map = {
        "boundary_detective": (crew_boundary_agent, boundary_agent),
        "document_analyzer": (crew_document_agent, document_agent),
        "summarization_manager": (crew_summarization_agent, summarization_agent),
        "analysis_judge": (crew_judge_agent, judge_agent)
    }
    
    # Create tracking record of CrewAI agent creation
    tracker.log_activity(
        "system",
        "create_crewai_agents",
        {},
        {"agent_count": len(agent_map)},
        reasoning=["Created CrewAI agents that parallel our tracked agents"]
    )
    
    # Create tasks (without modifying their execute method)
    boundary_detection_task = Task(
        description=TASK_DESCRIPTIONS["boundary_detection"],
        agent=crew_boundary_agent,
        expected_output="Structured analysis of document boundaries with positions and confidence levels"
    )
    
    document_classification_task = Task(
        description=TASK_DESCRIPTIONS["document_classification"],
        agent=crew_boundary_agent,
        expected_output="Classification of each document segment by type, company, and time period",
        context=[boundary_detection_task]
    )
    
    document_analysis_task = Task(
        description=TASK_DESCRIPTIONS.get("document_analysis", 
            "Analyze the document structure and metrics. Compute word counts, sentence counts, paragraph counts, " +
            "and extract key entities. Identify patterns in the document's structure and organization. " +
            "Provide a quantitative assessment of the document's characteristics."),
        agent=crew_document_agent,
        expected_output="Document metrics and structure analysis",
        context=[boundary_detection_task, document_classification_task]
    )
    
    summarization_task = Task(
        description=TASK_DESCRIPTIONS.get("summarization", 
            "Generate multiple summary approaches for the document: standard full-document summary, " +
            "partition-based summaries that respect document boundaries, and entity-focused summaries. " +
            "Compare these approaches and recommend which works best for this document type with explanation."),
        agent=crew_summarization_agent,
        expected_output="Multi-strategy summarization results with comparisons",
        context=[boundary_detection_task, document_classification_task, document_analysis_task]
    )
    
    synthesis_task = Task(
        description=TASK_DESCRIPTIONS["synthesis"],
        agent=crew_judge_agent,
        expected_output="Comprehensive analysis with insights and recommendations",
        context=[boundary_detection_task, document_classification_task, 
                 document_analysis_task, summarization_task]
    )
    
    # Log task creation
    tracker.log_activity(
        "system",
        "create_tasks",
        {},
        {
            "task_count": 5,
            "tasks": [
                "boundary_detection", 
                "document_classification", 
                "document_analysis", 
                "summarization", 
                "synthesis"
            ]
        },
        reasoning=["Created 5 tasks for the CrewAI agents to execute sequentially"]
    )
    
    # Create crew
    document_crew = Crew(
        agents=[crew_boundary_agent, crew_document_agent, crew_summarization_agent, crew_judge_agent],
        tasks=[boundary_detection_task, document_classification_task, 
               document_analysis_task, summarization_task, synthesis_task],
        verbose=True,
        process=Process.sequential  # Start with sequential for easier debugging
    )
    
    # Log crew creation
    tracker.log_activity(
        "system",
        "create_crew",
        {},
        {"process_type": "sequential"},
        reasoning=["Created CrewAI crew with sequential process flow for easier debugging"]
    )
    
    return document_crew, tracker, agent_map

def run_analysis_with_tracking(document_text, session_name=None, output_dir="output"):
    """
    Run document analysis with the multi-agent system and track all activities.
    
    Args:
        document_text (str): The text to be analyzed
        session_name (str, optional): Name for the tracking session
        output_dir (str, optional): Directory to save tracking outputs
        
    Returns:
        dict: Results and tracking information
    """
    logger.info("Starting multi-agent document analysis with tracking")
    
    # Create crew with tracking
    document_crew, tracker, agent_map = create_tracked_crew(
        document_text, 
        session_name=session_name,
        output_dir=output_dir
    )
    
    # Start timing
    import time
    start_time = time.time()
    
    # Log analysis start
    tracker.log_activity(
        "system",
        "start_analysis",
        {"document_length": len(document_text)},
        {"start_time": start_time},
        reasoning=["Beginning multi-agent analysis of document"]
    )
    
    # Run the crew
    try:
        crew_result = document_crew.kickoff(inputs={"document": document_text})
        
        # Track the final result
        tracker.log_activity(
            "system",
            "complete_analysis",
            {"document_length": len(document_text)},
            {"completion_status": "success"},
            reasoning=["Multi-agent analysis completed successfully"]
        )
        
    except Exception as e:
        logger.error(f"Error in crew execution: {e}")
        tracker.log_activity(
            "system",
            "analysis_error",
            {"document_length": len(document_text)},
            {"error": str(e)},
            reasoning=["Error occurred during multi-agent analysis"]
        )
        crew_result = {"error": str(e)}
    
    # End timing
    total_time = time.time() - start_time
    
    # Log completion information
    tracker.log_activity(
        "system",
        "analysis_statistics",
        {},
        {
            "total_time": total_time,
            "activity_count": len(tracker.activities)
        },
        reasoning=["Calculated final statistics for the analysis run"]
    )
    
    # Generate tracking outputs
    json_output_path = os.path.join(output_dir, f"{tracker.session_name}_tracking.json")
    tracker.export_json(json_output_path)
    
    markdown_output = tracker.generate_markdown()
    markdown_output_path = os.path.join(output_dir, f"{tracker.session_name}_report.md")
    with open(markdown_output_path, "w") as f:
        f.write(markdown_output)
    
    # Create a combined result
    result = {
        "crew_result": crew_result,
        "tracking": {
            "session_name": tracker.session_name,
            "json_output": json_output_path,
            "markdown_report": markdown_output_path,
            "total_time": total_time,
            "activity_count": len(tracker.activities)
        }
    }
    
    logger.info(f"Analysis complete in {total_time:.2f} seconds")
    logger.info(f"Tracking information saved to {output_dir}")
    
    return result

# For direct testing
if __name__ == "__main__":
    # Test with a simple document
    test_text = """
    Apple Inc. reported strong earnings for Q3 2023, with revenue reaching $81.8 billion.
    CEO Tim Cook highlighted the growth in Services, which set another all-time record.
    
    Meanwhile, Microsoft Corporation announced its Q2 2023 results on January 24, 2023,
    with cloud revenue growing 22% year-over-year to $27.1 billion.
    
    Both companies discussed AI investments during their earnings calls.
    """
    
    result = run_analysis_with_tracking(test_text, session_name="test_analysis")
    print(json.dumps(result, indent=2))