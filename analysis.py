# analysis.py
"""
Core CrewAI setup and task definitions for the Agentic Explorer.
This module defines the agents and their tasks, creating the multi-agent system.
"""

import os
from dotenv import load_dotenv
from crewai import Crew, Agent, Task, Process
from utils.openai_client import get_openai_client
from content import AGENT_DESCRIPTIONS, TASK_DESCRIPTIONS

# Load environment variables
load_dotenv()

def create_boundary_detector_agent():
    """Create and return the Boundary Detective agent."""
    agent_info = AGENT_DESCRIPTIONS["boundary_detector"]
    
    return Agent(
        role=agent_info["role"],
        goal=agent_info["goal"],
        backstory=agent_info["backstory"],
        verbose=True,
        allow_delegation=False,
        # We'll use OpenAI's 3.5 for cost efficiency in the POC
        llm=get_openai_client()
    )

def create_financial_analyst_agent():
    """Create and return the Financial Analyst agent."""
    agent_info = AGENT_DESCRIPTIONS["financial_analyst"]
    
    return Agent(
        role=agent_info["role"],
        goal=agent_info["goal"],
        backstory=agent_info["backstory"],
        verbose=True,
        allow_delegation=False,
        llm=get_openai_client()
    )

def create_news_analyst_agent():
    """Create and return the News Analyst agent."""
    agent_info = AGENT_DESCRIPTIONS["news_analyst"]
    
    return Agent(
        role=agent_info["role"],
        goal=agent_info["goal"],
        backstory=agent_info["backstory"],
        verbose=True,
        allow_delegation=False,
        llm=get_openai_client()
    )

def create_investment_judge_agent():
    """Create and return the Investment Judge agent."""
    agent_info = AGENT_DESCRIPTIONS["investment_judge"]
    
    return Agent(
        role=agent_info["role"],
        goal=agent_info["goal"],
        backstory=agent_info["backstory"],
        verbose=True,
        allow_delegation=False,
        llm=get_openai_client()
    )

def create_document_analysis_crew(document_text):
    """
    Create and return a CrewAI crew for document analysis.
    
    Args:
        document_text (str): The text to be analyzed
        
    Returns:
        dict: The results of the crew's analysis
    """
    # Initialize agents
    boundary_agent = create_boundary_detector_agent()
    financial_agent = create_financial_analyst_agent()
    news_agent = create_news_analyst_agent()
    judge_agent = create_investment_judge_agent()
    
    # Create tasks
    boundary_detection_task = Task(
        description=TASK_DESCRIPTIONS["boundary_detection"],
        agent=boundary_agent,
        expected_output="Structured analysis of document boundaries with positions and confidence levels"
    )
    
    document_classification_task = Task(
        description=TASK_DESCRIPTIONS["document_classification"],
        agent=boundary_agent,
        expected_output="Classification of each document segment by type, company, and time period",
        context=[boundary_detection_task]
    )
    
    financial_analysis_task = Task(
        description=TASK_DESCRIPTIONS["financial_analysis"],
        agent=financial_agent,
        expected_output="Financial metrics and insights for each document segment",
        context=[boundary_detection_task, document_classification_task]
    )
    
    news_sentiment_task = Task(
        description=TASK_DESCRIPTIONS["news_sentiment"],
        agent=news_agent,
        expected_output="Sentiment analysis and key narratives for each document segment",
        context=[boundary_detection_task, document_classification_task]
    )
    
    synthesis_task = Task(
        description=TASK_DESCRIPTIONS["synthesis"],
        agent=judge_agent,
        expected_output="Comprehensive analysis with insights and recommendations",
        context=[boundary_detection_task, document_classification_task, 
                 financial_analysis_task, news_sentiment_task]
    )
    
    # Create and run crew
    document_crew = Crew(
        agents=[boundary_agent, financial_agent, news_agent, judge_agent],
        tasks=[boundary_detection_task, document_classification_task, 
               financial_analysis_task, news_sentiment_task, synthesis_task],
        verbose=True,
        process=Process.sequential  # Start with sequential for easier debugging
    )
    
    result = document_crew.kickoff(inputs={"document": document_text})
    return result