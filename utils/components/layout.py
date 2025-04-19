"""
Layout components for the Agentic Explorer application.

This module provides reusable layout components that help maintain a consistent
look and feel across the application.
"""

import streamlit as st
from typing import List, Dict, Any, Optional, Callable, Union

def page_container(title: str, subtitle: Optional[str] = None, icon: Optional[str] = None):
    """
    Creates a standardized page container with title and optional subtitle.
    
    Args:
        title: The page title
        subtitle: Optional subtitle or description
        icon: Optional emoji icon to display with the title
    
    Returns:
        The main content container
    
    Example:
        ```python
        with page_container("Financial Analysis", "Explore financial metrics", "📊"):
            st.write("Your content here")
        ```
    """
    if icon:
        st.title(f"{icon} {title}")
    else:
        st.title(title)
        
    if subtitle:
        st.markdown(f"<p class='subtitle'>{subtitle}</p>", unsafe_allow_html=True)
    
    # Add some spacing
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Apply custom styling
    st.markdown("""
    <style>
        .subtitle {
            font-size: 1.1rem;
            color: rgba(250, 250, 250, 0.7);
            margin-top: -0.8rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Return the main container
    return st.container()

def card(title: Optional[str] = None, key: Optional[str] = None, padding: int = 20):
    """
    Creates a card-like container with consistent styling.
    
    Args:
        title: Optional card title
        key: Optional key for the container
        padding: Padding in pixels
    
    Returns:
        A container for card content
    
    Example:
        ```python
        with card("Metrics Overview"):
            st.metric("Revenue", "$1.2M")
        ```
    """
    container = st.container(key=key)
    
    # Add card styling
    container.markdown(f"""
    <style>
        div[data-testid="stContainer"] > div:has(div.card-content) {{
            background-color: rgba(35, 35, 35, 0.7);
            border-radius: 10px;
            padding: {padding}px;
            margin-bottom: 1rem;
        }}
    </style>
    """, unsafe_allow_html=True)
    
    # Add content with class for targeting
    with container:
        if title:
            st.markdown(f"<h3 style='margin-top: 0;'>{title}</h3>", unsafe_allow_html=True)
        
        content = st.container()
        content.markdown('<div class="card-content"></div>', unsafe_allow_html=True)
        
        return content

def section(title: str, description: Optional[str] = None, collapsed: bool = False,
           key: Optional[str] = None):
    """
    Creates a collapsible section with a title and optional description.
    
    Args:
        title: Section title
        description: Optional description text
        collapsed: Whether the section should be initially collapsed
        key: Optional key for the expander
    
    Returns:
        The expander container
    
    Example:
        ```python
        with section("Financial Metrics", "Key performance indicators"):
            st.metric("Revenue", "$1.2M")
        ```
    """
    if description:
        header = f"{title} <span style='font-size: 0.8rem; color: rgba(250, 250, 250, 0.6);'>{description}</span>"
    else:
        header = title
        
    return st.expander(header, expanded=not collapsed, key=key)

def tabs_container(tab_titles: List[str], icons: Optional[List[str]] = None,
                 key: Optional[str] = None):
    """
    Creates a styled tab container with optional icons.
    
    Args:
        tab_titles: List of tab titles
        icons: Optional list of emoji icons for each tab
        key: Optional key for the tabs
    
    Returns:
        List of tab containers
    
    Example:
        ```python
        tab1, tab2 = tabs_container(["Overview", "Details"], ["📊", "📝"])
        with tab1:
            st.write("Overview content")
        ```
    """
    if icons and len(icons) == len(tab_titles):
        # Add icons to tab titles
        display_titles = [f"{icon} {title}" for icon, title in zip(icons, tab_titles)]
    else:
        display_titles = tab_titles
    
    # Create tabs
    tabs = st.tabs(display_titles, key=key)
    
    # Add custom styling
    st.markdown("""
    <style>
        button[data-baseweb="tab"] {
            font-size: 0.9rem;
        }
        
        button[data-baseweb="tab"][aria-selected="true"] {
            background-color: rgba(0, 184, 212, 0.1);
            border-bottom-color: rgb(0, 184, 212) !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    return tabs

def two_column_layout(left_width: int = 1, right_width: int = 1):
    """
    Creates a two-column layout with customizable widths.
    
    Args:
        left_width: Relative width of the left column
        right_width: Relative width of the right column
    
    Returns:
        Tuple containing the left and right column containers
    
    Example:
        ```python
        left_col, right_col = two_column_layout(1, 2)
        with left_col:
            st.write("Left column content")
        ```
    """
    return st.columns([left_width, right_width])

def three_column_layout(left_width: int = 1, middle_width: int = 1, right_width: int = 1):
    """
    Creates a three-column layout with customizable widths.
    
    Args:
        left_width: Relative width of the left column
        middle_width: Relative width of the middle column
        right_width: Relative width of the right column
    
    Returns:
        Tuple containing the left, middle, and right column containers
    
    Example:
        ```python
        left, middle, right = three_column_layout(1, 2, 1)
        with middle:
            st.write("Middle column content")
        ```
    """
    return st.columns([left_width, middle_width, right_width])

def metrics_row(metrics: List[Dict[str, Any]], num_columns: Optional[int] = None):
    """
    Creates a row of evenly-spaced metric cards.
    
    Args:
        metrics: List of dicts with 'label', 'value', and optional 'delta' and 'help'
        num_columns: Number of columns to use (defaults to number of metrics)
    
    Example:
        ```python
        metrics_row([
            {"label": "Revenue", "value": "$1.2M", "delta": "15%"},
            {"label": "Profit", "value": "$300K", "delta": "-5%"},
        ])
        ```
    """
    if not num_columns:
        num_columns = len(metrics)
    
    # Create columns for metrics
    cols = st.columns(num_columns)
    
    # Add metrics to columns
    for i, metric_data in enumerate(metrics):
        col_idx = i % num_columns
        
        if "delta" in metric_data:
            cols[col_idx].metric(
                label=metric_data["label"],
                value=metric_data["value"],
                delta=metric_data["delta"],
                help=metric_data.get("help", None)
            )
        else:
            cols[col_idx].metric(
                label=metric_data["label"],
                value=metric_data["value"],
                help=metric_data.get("help", None)
            )
            
def apply_dark_theme_tweaks():
    """
    Apply custom CSS tweaks to enhance the dark theme appearance.
    
    This is useful for custom styling that Streamlit's theming doesn't cover.
    """
    st.markdown("""
    <style>
        /* Card-like appearance for metric containers */
        div[data-testid="metric-container"] {
            background-color: rgba(35, 35, 35, 0.8);
            border-radius: 5px;
            padding: 10px 15px;
            border-left: 3px solid rgba(0, 184, 212, 0.7);
        }
        
        /* Metric label styling */
        div[data-testid="metric-container"] label {
            color: rgba(250, 250, 250, 0.8);
        }
        
        /* Metric value styling */
        div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
            color: rgba(250, 250, 250, 0.95);
            font-size: 1.5rem;
        }
        
        /* Positive delta styling */
        div[data-testid="metric-container"] div[data-testid="stMetricDelta"] svg[fill="green"] {
            fill: rgb(0, 180, 120) !important;
        }
        
        /* Negative delta styling */
        div[data-testid="metric-container"] div[data-testid="stMetricDelta"] svg[fill="red"] {
            fill: rgb(230, 60, 80) !important;
        }
    </style>
    """, unsafe_allow_html=True)