"""
Agentic Explorer - Main Application

This Streamlit application serves as the entry point for the Agentic Explorer platform,
providing an overview and navigation to the various exploration modules.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import os
import json
import random

# Import our custom components
from utils.components.layout import page_container, card, two_column_layout, three_column_layout, metrics_row
from utils.components.themes import apply_theme, color, get_chart_colors



# Set page configuration
st.set_page_config(
    page_title="Agentic Explorer",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply theme enhancements
apply_theme()

# Utility functions
def get_datastore_path():
    """Get the path to the dataStore directory."""
    # Check if running in GitHub Codespaces
    if os.environ.get("CODESPACES"):
        # Adjust path for Codespaces environment
        return Path("/workspaces/agentic-explorer/dataStore")
    
    # Local environment
    return Path("dataStore")

def get_available_tickers():
    """Get a list of available tickers in the dataStore."""
    companies_path = get_datastore_path() / "companies"
    if not companies_path.exists():
        return []
    
    return [d.name for d in companies_path.iterdir() if d.is_dir()]

def load_company_profile(ticker):
    """Load company profile data for a given ticker."""
    profile_path = get_datastore_path() / "companies" / ticker / "profile.json"
    if profile_path.exists():
        with open(profile_path, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return None
    return None

def main():
    """Main application entry point."""
    # Add logo and title to sidebar
    st.sidebar.image("docs/images/agentic_explorer_logo.svg", width=150)
    st.sidebar.title("Navigation")
    
    # Add sidebar navigation (pages will be automatically added by Streamlit)
    st.sidebar.markdown("""
    - [Home](#)
    - [Data Explorer](/Data_Explorer)
    """)
    
    # Add separator
    st.sidebar.markdown("---")
    
    # App information
    st.sidebar.info(
        "This application is an experimental platform for exploring multi-agent "
        "intelligence systems focused on extracting meaningful insights from data."
    )
    
    # Main content
    with page_container("Agentic Explorer", "An Interactive Platform for Multi-Agent Systems"):
        st.markdown("""
        ## Welcome to Agentic Explorer
        
        This platform serves as a sandbox for exploring how specialized AI agents collaborate 
        to transform diverse data sources into actionable intelligence.
        
        Use the navigation menu to access different modules, or explore the available company data below.
        """)
        
        # Display available modules
        st.markdown("## Available Modules")
        
        # Create module cards in a grid
        col1, col2 = two_column_layout()
        
        with col1:
            with card("Data Explorer"):
                st.markdown("""
                **Explore financial data collected in the dataStore.**

                This module provides comprehensive access to company profiles, financial statements,
                stock prices, news articles, and earnings call transcripts with powerful
                visualization and analysis tools.
                
                [Open Data Explorer](/Data_Explorer)
                """)
        
        with col2:
            with card("Coming Soon: Multi-Agent Analysis"):
                st.markdown("""
                **Watch specialized AI agents analyze financial data in real-time.**

                This upcoming module will demonstrate how different agent configurations
                affect analysis quality, cost, and accuracy while making agent interactions
                visible and measurable.
                
                _Under development_
                """)
                
        # Display available company data
        st.markdown("## Available Company Data")
        
        # Get available tickers
        available_tickers = get_available_tickers()
        
        if not available_tickers:
            st.warning("""
            No company data found in the dataStore. Please run the data collector first:
            ```bash
            python -m utils.run_data_collector --tickers DELL,NVDA,TSLA,ACN --years 3
            ```
            """)
        else:
            # Create company cards
            company_profiles = []
            
            # Load profile data for all available tickers
            for ticker in available_tickers:
                profile = load_company_profile(ticker)
                if profile:
                    company_profiles.append({
                        'ticker': ticker,
                        'profile': profile
                    })
            
            # Display company cards in rows of 3
            for i in range(0, len(company_profiles), 3):
                # Create a row for each 3 companies
                cols = st.columns(3)
                
                # Fill each column with a company card
                for j in range(3):
                    idx = i + j
                    if idx < len(company_profiles):
                        company = company_profiles[idx]
                        ticker = company['ticker']
                        profile = company['profile']
                        
                        with cols[j]:
                            with card(f"{ticker}: {profile.get('companyName', '')}"):
                                # Display company logo if available
                                if "image" in profile and profile["image"]:
                                    st.image(profile["image"], width=100)
                                
                                # Display key info
                                st.markdown(f"**Industry:** {profile.get('industry', 'N/A')}")
                                st.markdown(f"**Sector:** {profile.get('sector', 'N/A')}")
                                
                                # Display a key metric if available
                                if "mktCap" in profile:
                                    mkt_cap = profile["mktCap"]
                                    if isinstance(mkt_cap, (int, float)):
                                        if mkt_cap >= 1_000_000_000:
                                            formatted_mkt_cap = f"${mkt_cap / 1_000_000_000:.2f}B"
                                        else:
                                            formatted_mkt_cap = f"${mkt_cap / 1_000_000:.2f}M"
                                        st.markdown(f"**Market Cap:** {formatted_mkt_cap}")
                                
                                # Add a link to explore in Data Explorer
                                st.markdown(f"[Explore in Data Explorer](/Data_Explorer?ticker={ticker})")

        # Add project information
        with st.expander("About Agentic Explorer", expanded=False):
            st.markdown("""
            ### Project Overview
            
            Agentic Explorer is an experimental framework for building, testing, and visualizing 
            multi-agent LLM systems. We're tackling the signal-versus-noise challenge in operational 
            decision making, using public company data as our proving ground.
            
            ### The "Last Mile" Intelligence Advantage
            
            A key concept we're exploring is how unstructured data can serve as the "last mile" 
            connector that provides early warning signals before they manifest in traditional metrics.
            
            This approach emphasizes awareness over precision, focusing on identifying emerging 
            patterns rather than making exact predictions.
            
            ### The Signal Intelligence Framework
            
            We're exploring a Signal Intelligence Framework that organizes insights into five 
            universal indices:
            
            1. **Cost Pressure Index (CPI)**: Forward-looking measure of factors impacting cost structure
            2. **Revenue Vulnerability Index (RVI)**: Predictive assessment of revenue stream stability
            3. **Brand Resilience Index (BRI)**: Measure of reputation capital and recovery ability
            4. **Risk Exposure Index (REI)**: Assessment of vulnerability to operational disruption
            5. **Market Environment Index (MEI)**: Indicator of external conditions for strategic position
            """)

# Run the app
if __name__ == "__main__":
    main()