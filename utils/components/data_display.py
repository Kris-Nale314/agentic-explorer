"""
Data display components for the Agentic Explorer application.

This module provides reusable components for displaying data in various formats.
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Union, Callable

def metric_card(label: str, value: Any, delta: Optional[Any] = None, 
               help_text: Optional[str] = None, color: Optional[str] = None,
               prefix: Optional[str] = None, suffix: Optional[str] = None,
               formatter: Optional[Callable] = None):
    """
    Displays a metric with styling consistent with the dark theme.
    
    Args:
        label: Label for the metric
        value: Value to display
        delta: Optional delta value or percentage
        help_text: Optional tooltip text
        color: Optional custom color (hex code)
        prefix: Optional prefix for the value (e.g., "$")
        suffix: Optional suffix for the value (e.g., "%")
        formatter: Optional function to format the value
    
    Example:
        ```python
        metric_card("Revenue", 1200000, 15.4, prefix="$", 
                   formatter=lambda x: f"{x:,.0f}")
        ```
    """
    # Format the value if formatter is provided
    if formatter:
        formatted_value = formatter(value)
    else:
        formatted_value = value
    
    # Add prefix/suffix if provided
    if prefix:
        formatted_value = f"{prefix}{formatted_value}"
    if suffix:
        formatted_value = f"{formatted_value}{suffix}"
    
    # Create custom container with styling
    container = st.container()
    
    # Add custom styling
    if color:
        st.markdown(f"""
        <style>
            div[data-testid="stMetricValue"] {{
                color: {color} !important;
            }}
        </style>
        """, unsafe_allow_html=True)
    
    # Display the metric
    container.metric(
        label=label,
        value=formatted_value,
        delta=delta,
        help=help_text
    )
    
    # Add border styling
    st.markdown("""
    <style>
        div[data-testid="metric-container"] {
            background-color: rgba(35, 35, 35, 0.7);
            border-radius: 5px;
            padding: 10px 15px;
            border-left: 3px solid rgba(0, 184, 212, 0.7);
        }
    </style>
    """, unsafe_allow_html=True)

def metrics_grid(metrics: List[Dict[str, Any]], columns: int = 3):
    """
    Displays a grid of metrics with consistent styling.
    
    Args:
        metrics: List of dictionaries with metric data
        columns: Number of columns in the grid
    
    Example:
        ```python
        metrics_grid([
            {"label": "Revenue", "value": 1200000, "delta": 15.4, "prefix": "$"},
            {"label": "Customers", "value": 8720, "delta": 12.1},
            {"label": "Retention", "value": 94.2, "suffix": "%", "delta": -2.1}
        ])
        ```
    """
    # Create columns
    cols = st.columns(columns)
    
    # Display metrics in columns
    for i, metric_data in enumerate(metrics):
        col_idx = i % columns
        
        with cols[col_idx]:
            metric_card(
                label=metric_data["label"],
                value=metric_data["value"],
                delta=metric_data.get("delta"),
                help_text=metric_data.get("help_text"),
                color=metric_data.get("color"),
                prefix=metric_data.get("prefix"),
                suffix=metric_data.get("suffix"),
                formatter=metric_data.get("formatter")
            )

def styled_dataframe(df: pd.DataFrame, height: Optional[int] = None, 
                    precision: Optional[int] = None, 
                    highlight_max: Optional[List[str]] = None,
                    highlight_min: Optional[List[str]] = None):
    """
    Displays a DataFrame with improved styling for dark theme.
    
    Args:
        df: Pandas DataFrame to display
        height: Optional height for the table
        precision: Number of decimal places for float columns
        highlight_max: Columns where maximum values should be highlighted
        highlight_min: Columns where minimum values should be highlighted
    
    Example:
        ```python
        styled_dataframe(df, height=400, precision=2, 
                        highlight_max=["Revenue", "Profit"])
        ```
    """
    # Apply styling
    styled_df = df.copy()
    
    # Function to highlight max values
    def highlight_max_value(s, color='#4caf50'):
        is_max = s == s.max()
        return [f'background-color: {color}; color: white' if v else '' for v in is_max]
    
    # Function to highlight min values
    def highlight_min_value(s, color='#f44336'):
        is_min = s == s.min()
        return [f'background-color: {color}; color: white' if v else '' for v in is_min]
    
    # Apply highlighting if requested
    if highlight_max:
        for col in highlight_max:
            if col in styled_df.columns and pd.api.types.is_numeric_dtype(styled_df[col]):
                styled_df = styled_df.style.apply(highlight_max_value, subset=[col])
    
    if highlight_min:
        for col in highlight_min:
            if col in styled_df.columns and pd.api.types.is_numeric_dtype(styled_df[col]):
                styled_df = styled_df.style.apply(highlight_min_value, subset=[col])
    
    # Set precision for float columns if specified
    if precision is not None:
        float_cols = styled_df.select_dtypes(include=['float']).columns
        if len(float_cols) > 0:
            styled_df = styled_df.style.format({col: f'{{:.{precision}f}}' for col in float_cols})
    
    # Custom CSS for DataFrames in dark theme
    st.markdown("""
    <style>
        .dataframe {
            background-color: rgba(30, 30, 30, 0.7);
            border-radius: 5px;
        }
        
        .dataframe th {
            background-color: rgba(50, 50, 50, 0.8);
            color: #f5f5f5;
            border-bottom: 1px solid #555;
            font-weight: 600;
        }
        
        .dataframe td {
            color: #f5f5f5;
            border-bottom: 1px solid #333;
        }
        
        .dataframe tr:hover td {
            background-color: rgba(0, 184, 212, 0.1);
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Display the DataFrame
    if height:
        return st.dataframe(styled_df, height=height)
    else:
        return st.dataframe(styled_df)

def data_card(title: str, data: pd.DataFrame, show_all: bool = False, 
             height: int = 300, key: Optional[str] = None):
    """
    Displays a DataFrame in a card with controls for viewing and downloading.
    
    Args:
        title: Card title
        data: DataFrame to display
        show_all: Whether to initially show all data
        height: Height of the card
        key: Optional key for the component
    
    Example:
        ```python
        data_card("Financial Data", financial_df, height=400)
        ```
    """
    with st.expander(title, expanded=show_all):
        # Add controls in a row
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            show_count = st.slider("Rows", min_value=5, max_value=min(100, len(data)), 
                                 value=min(10, len(data)), key=f"{key}_slider")
        
        with col2:
            # Add a search box
            search_term = st.text_input("Search", key=f"{key}_search")
        
        with col3:
            # Add download button
            if len(data) > 0:
                csv = data.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"{title.lower().replace(' ', '_')}.csv",
                    mime="text/csv",
                    key=f"{key}_download"
                )
        
        # Filter data based on search term
        if search_term:
            filtered_data = data[data.astype(str).apply(
                lambda row: row.str.contains(search_term, case=False).any(), axis=1
            )]
        else:
            filtered_data = data
        
        # Show stats
        if len(filtered_data) > 0:
            st.caption(f"Showing {min(show_count, len(filtered_data))} of {len(filtered_data)} rows" + 
                     (f" (filtered from {len(data)} total)" if search_term else ""))
            
            # Display the data
            styled_dataframe(filtered_data.head(show_count), height=height)
        else:
            st.info("No matching data found")

def info_card(title: str, content: str, icon: Optional[str] = None, 
             color: Optional[str] = None, expanded: bool = True):
    """
    Displays an information card with styled content.
    
    Args:
        title: Card title
        content: Card content (supports markdown)
        icon: Optional emoji icon for the title
        color: Optional accent color (hex code)
        expanded: Whether the card should be initially expanded
    
    Example:
        ```python
        info_card("Company Overview", "This company specializes in...", 
                 icon="🏢", color="#00b8d4")
        ```
    """
    # Set default color if not provided
    if not color:
        color = "#00b8d4"
    
    # Create title with icon if provided
    if icon:
        display_title = f"{icon} {title}"
    else:
        display_title = title
    
    # Create the expandable card
    with st.expander(display_title, expanded=expanded):
        # Add styling
        st.markdown(f"""
        <style>
            div.stExpander details summary p {{
                color: {color};
                font-weight: 600;
            }}
        </style>
        """, unsafe_allow_html=True)
        
        # Display content
        st.markdown(content)

def key_value_pairs(data: Dict[str, Any], num_columns: int = 2):
    """
    Displays a dictionary as key-value pairs in multiple columns.
    
    Args:
        data: Dictionary of key-value pairs
        num_columns: Number of columns to use
    
    Example:
        ```python
        key_value_pairs({
            "CEO": "John Smith",
            "Founded": "1985",
            "Headquarters": "New York",
            "Employees": "5,240"
        })
        ```
    """
    # Create columns
    cols = st.columns(num_columns)
    
    # Calculate items per column
    items_per_col = (len(data) + num_columns - 1) // num_columns
    
    # Convert dictionary to list of tuples
    items = list(data.items())
    
    # Display items in columns
    for i in range(num_columns):
        start_idx = i * items_per_col
        end_idx = min(start_idx + items_per_col, len(items))
        
        with cols[i]:
            for key, value in items[start_idx:end_idx]:
                st.markdown(f"**{key}:** {value}")

def search_results(results: List[Dict[str, Any]], height: int = 400):
    """
    Displays search results with highlighting and filtering.
    
    Args:
        results: List of dictionaries with search result data
        height: Height of the results container
    
    Example:
        ```python
        search_results([
            {"title": "Q1 Earnings Report", "text": "Revenue increased by 15%...", 
             "date": "2023-04-15", "source": "Earnings Call"},
            {"title": "New Product Launch", "text": "Company announced a new...", 
             "date": "2023-03-22", "source": "Press Release"}
        ])
        ```
    """
    # Add search box
    search_term = st.text_input("Search within results")
    
    # Filter results based on search term
    if search_term:
        filtered_results = [
            r for r in results if search_term.lower() in r.get("title", "").lower() or 
            search_term.lower() in r.get("text", "").lower()
        ]
    else:
        filtered_results = results
    
    # Show result count
    st.caption(f"Showing {len(filtered_results)} of {len(results)} results")
    
    # Create scrollable container
    container = st.container()
    
    # Add custom CSS for results
    st.markdown(f"""
    <style>
        .search-results {{
            height: {height}px;
            overflow-y: auto;
            padding-right: 10px;
        }}
        
        .result-card {{
            background-color: rgba(30, 30, 30, 0.7);
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 10px;
            border-left: 3px solid #00b8d4;
        }}
        
        .result-title {{
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 5px;
            color: #f5f5f5;
        }}
        
        .result-meta {{
            font-size: 0.8rem;
            color: #b0b0b0;
            margin-bottom: 10px;
        }}
        
        .result-text {{
            font-size: 0.9rem;
            color: #e0e0e0;
        }}
        
        .highlight {{
            background-color: rgba(255, 171, 0, 0.3);
            padding: 0 2px;
            border-radius: 2px;
        }}
    </style>
    """, unsafe_allow_html=True)
    
    # Function to highlight search term in text
    def highlight_text(text, term):
        if not term:
            return text
        
        parts = text.split(term.lower())
        highlighted = term.join([f'<span class="highlight">{term}</span>' for _ in range(len(parts) - 1)])
        
        for i, part in enumerate(parts):
            if i < len(parts) - 1:
                highlighted = part + highlighted
            else:
                highlighted += part
                
        return highlighted
    
    # Display results
    with container:
        st.markdown('<div class="search-results">', unsafe_allow_html=True)
        
        for result in filtered_results:
            title = result.get("title", "No Title")
            text = result.get("text", "No content")
            date = result.get("date", "No date")
            source = result.get("source", "Unknown source")
            
            # Highlight search term if provided
            if search_term:
                # This is a simplified approach; for production, use regex for case-insensitive highlighting
                title_highlighted = title.replace(search_term, f'<span class="highlight">{search_term}</span>')
                text_highlighted = text.replace(search_term, f'<span class="highlight">{search_term}</span>')
            else:
                title_highlighted = title
                text_highlighted = text
            
            # Display result card
            st.markdown(f"""
            <div class="result-card">
                <div class="result-title">{title_highlighted}</div>
                <div class="result-meta">{date} | {source}</div>
                <div class="result-text">{text_highlighted[:200]}{"..." if len(text) > 200 else ""}</div>
            </div>
            """, unsafe_allow_html=True)
        
        if not filtered_results:
            st.markdown('<div style="text-align: center; padding: 20px; color: #b0b0b0;">No results found</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)