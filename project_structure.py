"""
Project structure initialization for Agentic Explorer

This module establishes the project root and ensures the required directories exist.
It should be imported at the beginning of scripts to ensure consistent path resolution.
"""

import os
import sys
from pathlib import Path

# Define and establish project root
# This assumes this file is placed in the project root
PROJECT_ROOT = Path(__file__).resolve().parent

# Add project root to Python path for absolute imports
sys.path.insert(0, str(PROJECT_ROOT))

# Required directory structure
REQUIRED_DIRS = [
    "core",
    "core/agents",
    "core/models",
    "core/tools",
    "dataStore",
    "dataStore/market_data",
    "utils",
    "tests",
    "outputs",
    "outputs/logs",
    "outputs/reports",
    "outputs/visualizations",
    "docs",
    "pages"
]

def ensure_project_structure():
    """Ensure all required directories exist."""
    for directory in REQUIRED_DIRS:
        dir_path = PROJECT_ROOT / directory
        if not dir_path.exists():
            dir_path.mkdir(parents=True)
            print(f"Created directory: {directory}")
    
    # Create empty __init__.py files in key directories to make them proper packages
    for pkg_dir in ["core", "core/agents", "core/models", "core/tools", "utils", "pages"]:
        init_file = PROJECT_ROOT / pkg_dir / "__init__.py"
        if not init_file.exists():
            init_file.touch()

# Create required directories when imported
ensure_project_structure()

def get_project_root():
    """Return the project root as a Path object."""
    return PROJECT_ROOT

def get_data_path(ticker=None):
    """
    Get the path to the data store directory.
    
    Args:
        ticker: Optional ticker symbol to get company-specific data path
        
    Returns:
        Path object to the requested directory
    """
    data_path = PROJECT_ROOT / "dataStore"
    if ticker:
        return data_path / ticker
    return data_path

def get_output_path(output_type=None):
    """
    Get the path to the outputs directory.
    
    Args:
        output_type: Optional type of output (logs, reports, visualizations)
        
    Returns:
        Path object to the requested directory
    """
    output_path = PROJECT_ROOT / "outputs"
    if output_type:
        return output_path / output_type
    return output_path

# Test if running directly
if __name__ == "__main__":
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Data store path: {get_data_path()}")
    print(f"NVDA data path: {get_data_path('NVDA')}")
    print(f"Outputs path: {get_output_path()}")
    print(f"Reports path: {get_output_path('reports')}")
    print("Project structure verified.")