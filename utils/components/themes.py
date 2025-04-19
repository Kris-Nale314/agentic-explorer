"""
Theme utilities for the Agentic Explorer application.

This module provides functions to apply consistent theming across the application.
"""

import streamlit as st

# Default color palette optimized for dark mode
COLORS = {
    'background': {
        'primary': '#121212',      # Very dark gray (main background)
        'secondary': '#1e1e1e',    # Dark gray (card background)
        'tertiary': '#2d2d2d',     # Medium gray (hover states)
    },
    'text': {
        'primary': '#f5f5f5',      # Off-white (main text)
        'secondary': '#b0b0b0',    # Light gray (secondary text)
        'disabled': '#707070',     # Medium gray (disabled text)
    },
    'accent': {
        'primary': '#00b8d4',      # Teal (primary accent)
        'secondary': '#ffab00',    # Amber (secondary accent)
        'tertiary': '#9c27b0',     # Purple (tertiary accent)
    },
    'semantic': {
        'positive': '#4caf50',     # Green (positive values)
        'negative': '#f44336',     # Red (negative values)
        'warning': '#ff9800',      # Orange (warnings)
        'info': '#2196f3',         # Blue (information)
    },
    'chart': {
        'sequential': ['#005f73', '#0a9396', '#94d2bd', '#e9d8a6', '#ee9b00', '#ca6702', '#bb3e03'],
        'diverging': ['#7b3294', '#c2a5cf', '#f7f7f7', '#a6dba0', '#008837'],
        'categorical': ['#00b8d4', '#ffab00', '#9c27b0', '#4caf50', '#f44336', '#2196f3', '#ff5722']
    }
}

def apply_theme():
    """
    Apply the Agentic Explorer theme to the Streamlit app.
    
    This adds custom CSS to enhance the dark theme with our color palette.
    
    Example:
        ```python
        apply_theme()
        ```
    """
    # Apply custom CSS for the dark theme
    st.markdown("""
    <style>
        /* Base styles */
        .stApp {
            background-color: #121212;
        }
        
        /* Typography */
        h1, h2, h3, h4, h5, h6, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, 
        .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
            color: #f5f5f5;
            font-family: 'Roboto', sans-serif;
        }
        
        h1, .stMarkdown h1 {
            border-bottom: 1px solid rgba(0, 184, 212, 0.3);
            padding-bottom: 0.3em;
        }
        
        .stMarkdown p, .stMarkdown li {
            color: #f5f5f5;
            font-family: 'Roboto', sans-serif;
        }
        
        /* Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #1e1e1e;
            border-right: 1px solid #2d2d2d;
        }
        
        section[data-testid="stSidebar"] .stMarkdown h1,
        section[data-testid="stSidebar"] .stMarkdown h2,
        section[data-testid="stSidebar"] .stMarkdown h3 {
            color: #00b8d4;
        }
        
        /* Widgets */
        div[data-testid="stSelectbox"] > div:first-child,
        div[data-testid="stMultiselect"] > div:first-child,
        div[data-testid="stDateInput"] > div:first-child {
            background-color: #1e1e1e;
            color: #f5f5f5;
            border-radius: 4px;
            border: 1px solid #2d2d2d;
        }
        
        div[data-testid="stSlider"] > div {
            color: #f5f5f5;
        }
        
        div[data-testid="stSlider"] > div > div {
            background-color: #1e1e1e;
        }
        
        div[data-testid="stSlider"] > div > div > div > div {
            background-color: #00b8d4;
        }
        
        div[data-baseweb="tab-list"] {
            background-color: #1e1e1e;
            border-radius: 4px;
        }
        
        button[data-baseweb="tab"] {
            color: #b0b0b0;
        }
        
        button[data-baseweb="tab"][aria-selected="true"] {
            color: #00b8d4;
            background-color: rgba(0, 184, 212, 0.1);
            border-bottom-color: #00b8d4 !important;
        }
        
        /* Buttons */
        .stButton button, div[data-testid="stDownloadButton"] button {
            background-color: rgba(0, 184, 212, 0.1);
            color: #00b8d4;
            border: 1px solid rgba(0, 184, 212, 0.3);
            border-radius: 4px;
            transition: all 0.3s;
        }
        
        .stButton button:hover, div[data-testid="stDownloadButton"] button:hover {
            background-color: rgba(0, 184, 212, 0.2);
            border: 1px solid rgba(0, 184, 212, 0.5);
        }
        
        /* Expanders */
        details {
            background-color: #1e1e1e;
            border-radius: 4px;
        }
        
        details summary {
            padding: 0.5rem;
            border-radius: 4px;
        }
        
        details summary:hover {
            background-color: #2d2d2d;
        }
        
        details .stExpander {
            border: none !important;
        }
        
        /* DataFrames */
        .dataframe {
            background-color: #1e1e1e;
            border-radius: 4px;
        }
        
        .dataframe th {
            background-color: #2d2d2d;
            color: #f5f5f5;
            padding: 0.5rem !important;
        }
        
        .dataframe td {
            color: #f5f5f5;
            background-color: #1e1e1e;
            padding: 0.5rem !important;
        }
        
        .dataframe tr:nth-child(even) td {
            background-color: #232323;
        }
        
        /* Metrics */
        div[data-testid="metric-container"] {
            background-color: #1e1e1e;
            border-radius: 4px;
            padding: 1rem;
            border-left: 3px solid #00b8d4;
        }
        
        div[data-testid="metric-container"] label {
            color: #b0b0b0;
        }
        
        div[data-testid="metric-container"] .stMetricValue {
            color: #f5f5f5;
            font-size: 2rem;
        }
        
        /* Alerts and messages */
        div[data-testid="stAlert"] {
            border-radius: 4px;
        }
        
        div[data-testid="stAlert"][data-baseweb="notification"] {
            background-color: #1e1e1e;
            border-left: 3px solid #00b8d4;
        }
        
        div[data-testid="stAlert"][data-baseweb="notification"] div[data-testid="stMarkdownContainer"] {
            color: #f5f5f5;
        }
    </style>
    """, unsafe_allow_html=True)

def add_logo():
    """
    Adds the Agentic Explorer logo to the sidebar.
    
    Example:
        ```python
        add_logo()
        ```
    """
    # Add logo to sidebar
    st.sidebar.image("docs/images/agentic_explorer_logo.svg", width=150)
    
    # Add separator
    st.sidebar.markdown("---")

def color(name: str) -> str:
    """
    Get a color from the theme palette.
    
    Args:
        name: Color name in format 'category.name' (e.g., 'accent.primary')
    
    Returns:
        The hex color code
    
    Example:
        ```python
        primary_color = color('accent.primary')
        ```
    """
    category, color_name = name.split('.')
    return COLORS[category][color_name]

def get_chart_colors(palette: str = 'categorical', num_colors: int = 7) -> list:
    """
    Get a list of colors for charts.
    
    Args:
        palette: Which palette to use ('sequential', 'diverging', 'categorical')
        num_colors: Number of colors needed
    
    Returns:
        List of hex color codes
    
    Example:
        ```python
        colors = get_chart_colors('sequential', 5)
        ```
    """
    colors = COLORS['chart'][palette]
    
    # If we need fewer colors than available, select a subset
    if num_colors < len(colors):
        # For sequential and diverging, take evenly spaced colors
        if palette in ['sequential', 'diverging']:
            indices = [int(i * (len(colors) - 1) / (num_colors - 1)) for i in range(num_colors)]
            return [colors[i] for i in indices]
        # For categorical, take the first num_colors
        else:
            return colors[:num_colors]
    
    # If we need more colors than available, cycle through them
    elif num_colors > len(colors):
        return [colors[i % len(colors)] for i in range(num_colors)]
    
    # If we need exactly the number available, return the full palette
    else:
        return colors

def apply_chart_theme(fig):
    """
    Apply the Agentic Explorer theme to a Plotly figure.
    
    Args:
        fig: A Plotly figure
    
    Returns:
        The styled figure
    
    Example:
        ```python
        fig = px.line(df, x='date', y='value')
        fig = apply_chart_theme(fig)
        ```
    """
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor=COLORS['background']['secondary'],
        font=dict(
            family="Roboto, sans-serif",
            size=12,
            color=COLORS['text']['primary']
        ),
        title=dict(
            font=dict(
                family="Roboto, sans-serif",
                size=16,
                color=COLORS['text']['primary']
            )
        ),
        legend=dict(
            font=dict(
                family="Roboto, sans-serif",
                size=12,
                color=COLORS['text']['primary']
            ),
            bgcolor='rgba(0,0,0,0)',
            bordercolor='rgba(0,0,0,0)',
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=20, r=20, t=30, b=20),
    )
    
    # Update axes
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor=COLORS['background']['tertiary'],
        showline=True,
        linewidth=1,
        linecolor=COLORS['background']['tertiary'],
        tickfont=dict(
            family="Roboto, sans-serif",
            size=10,
            color=COLORS['text']['secondary']
        ),
        title=dict(
            font=dict(
                family="Roboto, sans-serif",
                size=12,
                color=COLORS['text']['secondary']
            )
        )
    )
    
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor=COLORS['background']['tertiary'],
        showline=True,
        linewidth=1,
        linecolor=COLORS['background']['tertiary'],
        tickfont=dict(
            family="Roboto, sans-serif",
            size=10,
            color=COLORS['text']['secondary']
        ),
        title=dict(
            font=dict(
                family="Roboto, sans-serif",
                size=12,
                color=COLORS['text']['secondary']
            )
        )
    )
    
    return fig