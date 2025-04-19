"""
Chart components for the Agentic Explorer application.

This module provides reusable, styled chart components using Plotly.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple, Union, Callable

# Color scheme optimized for dark mode
COLORS = {
    'primary': '#00b8d4',      # Teal
    'secondary': '#ffab00',    # Amber
    'positive': '#4caf50',     # Green
    'negative': '#f44336',     # Red
    'neutral': '#2196f3',      # Blue
    'background': '#121212',   # Very dark gray
    'text': '#f5f5f5',         # Off-white
    'grid': '#333333',         # Dark gray
}

# Ensure consistent chart styling
def apply_chart_style(fig):
    """
    Apply consistent styling to a Plotly figure.
    
    Args:
        fig: A Plotly figure
    
    Returns:
        The styled figure
    """
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(30,30,30,0.3)',
        margin=dict(l=20, r=20, t=30, b=20),
        font=dict(
            family="Roboto, sans-serif",
            size=12,
            color=COLORS['text']
        ),
        xaxis=dict(
            gridcolor=COLORS['grid'],
            linecolor=COLORS['grid'],
            tickfont=dict(size=10)
        ),
        yaxis=dict(
            gridcolor=COLORS['grid'],
            linecolor=COLORS['grid'],
            tickfont=dict(size=10)
        ),
        legend=dict(
            font=dict(size=10),
            orientation="h",
            yanchor="top",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hoverlabel=dict(
            font_size=12,
            font_family="Roboto, sans-serif"
        )
    )
    return fig

def line_chart(data: pd.DataFrame, 
               x: str, 
               y: Union[str, List[str]], 
               title: Optional[str] = None,
               height: int = 400,
               color_discrete_map: Optional[Dict] = None,
               hover_data: Optional[List[str]] = None,
               custom_data: Optional[List[str]] = None,
               tooltip_format: Optional[Dict[str, str]] = None,
               markers: bool = False,
               range_slider: bool = False):
    """
    Create a styled line chart.
    
    Args:
        data: DataFrame containing the data
        x: Column to use for x-axis
        y: Column or list of columns for y-axis
        title: Chart title
        height: Chart height in pixels
        color_discrete_map: Custom color mapping for series
        hover_data: Additional columns to include in hover tooltip
        custom_data: Custom data for hover tooltips
        tooltip_format: Format string for tooltip values
        markers: Whether to show markers on the lines
        range_slider: Whether to include a range slider
    
    Returns:
        Plotly figure
    
    Example:
        ```python
        fig = line_chart(df, 'date', ['close', 'open'], 'Stock Price')
        st.plotly_chart(fig, use_container_width=True)
        ```
    """
    # Handle single y value
    if isinstance(y, str):
        y = [y]
    
    # Create figure
    fig = px.line(
        data,
        x=x,
        y=y,
        title=title,
        height=height,
        hover_data=hover_data,
        custom_data=custom_data,
    )
    
    # Apply custom colors if provided
    if color_discrete_map:
        for i, series_name in enumerate(y):
            if series_name in color_discrete_map:
                fig.data[i].line.color = color_discrete_map[series_name]
    
    # Apply markers if requested
    if markers:
        for trace in fig.data:
            trace.mode = 'lines+markers'
            trace.marker.size = 6
    
    # Add range slider if requested
    if range_slider:
        fig.update_layout(
            xaxis=dict(
                rangeslider=dict(visible=True),
                rangeslider_thickness=0.05,
            )
        )
    
    # Apply custom tooltip formatting if provided
    if tooltip_format and custom_data:
        for i, trace in enumerate(fig.data):
            hovertemplate = "<b>%{x}</b><br>"
            for j, col in enumerate(custom_data):
                if col in tooltip_format:
                    hovertemplate += f"{col}: {tooltip_format[col]}<br>"
                else:
                    hovertemplate += f"{col}: %{{customdata[{j}]}}<br>"
            hovertemplate += "<extra></extra>"
            trace.hovertemplate = hovertemplate
    
    # Apply consistent styling
    fig = apply_chart_style(fig)
    
    return fig

def bar_chart(data: pd.DataFrame,
              x: str,
              y: str,
              title: Optional[str] = None,
              height: int = 400,
              color: Optional[str] = None,
              color_discrete_map: Optional[Dict] = None,
              hover_data: Optional[List[str]] = None,
              text: Optional[str] = None,
              orientation: str = 'v',
              is_stacked: bool = False):
    """
    Create a styled bar chart.
    
    Args:
        data: DataFrame containing the data
        x: Column to use for x-axis
        y: Column for y-axis
        title: Chart title
        height: Chart height in pixels
        color: Column to use for color encoding
        color_discrete_map: Custom color mapping
        hover_data: Additional columns to include in hover tooltip
        text: Column to use for bar text
        orientation: 'v' for vertical bars, 'h' for horizontal
        is_stacked: Whether to stack bars when using color groups
    
    Returns:
        Plotly figure
    
    Example:
        ```python
        fig = bar_chart(df, 'category', 'revenue', 'Revenue by Category')
        st.plotly_chart(fig, use_container_width=True)
        ```
    """
    # Create figure
    fig = px.bar(
        data,
        x=x,
        y=y,
        title=title,
        height=height,
        color=color,
        color_discrete_map=color_discrete_map,
        hover_data=hover_data,
        text=text,
        orientation=orientation,
    )
    
    # Apply stacking if requested
    if is_stacked and color:
        fig.update_layout(barmode='stack')
    
    # Adjust text position
    if text:
        fig.update_traces(textposition='auto')
    
    # Apply consistent styling
    fig = apply_chart_style(fig)
    
    return fig

def candlestick_chart(data: pd.DataFrame,
                      date_col: str = 'date',
                      open_col: str = 'open',
                      high_col: str = 'high',
                      low_col: str = 'low',
                      close_col: str = 'close',
                      volume_col: Optional[str] = 'volume',
                      title: Optional[str] = None,
                      height: int = 500,
                      range_slider: bool = True,
                      moving_averages: Optional[List[int]] = None):
    """
    Create a styled candlestick chart with optional volume and moving averages.
    
    Args:
        data: DataFrame containing OHLC data
        date_col: Name of date column
        open_col: Name of open price column
        high_col: Name of high price column
        low_col: Name of low price column
        close_col: Name of close price column
        volume_col: Name of volume column (None to exclude volume)
        title: Chart title
        height: Chart height in pixels
        range_slider: Whether to include a range slider
        moving_averages: List of periods for moving averages (e.g., [20, 50])
    
    Returns:
        Plotly figure
    
    Example:
        ```python
        fig = candlestick_chart(df, moving_averages=[20, 50])
        st.plotly_chart(fig, use_container_width=True)
        ```
    """
    # Create subplots with or without volume
    if volume_col and volume_col in data.columns:
        fig = make_subplots(
            rows=2, 
            cols=1, 
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.8, 0.2]
        )
    else:
        fig = make_subplots(rows=1, cols=1)
    
    # Add candlestick trace
    fig.add_trace(
        go.Candlestick(
            x=data[date_col],
            open=data[open_col],
            high=data[high_col],
            low=data[low_col],
            close=data[close_col],
            name="Price",
            increasing_line_color=COLORS['positive'],
            decreasing_line_color=COLORS['negative']
        ),
        row=1, col=1
    )
    
    # Add moving averages if requested
    if moving_averages:
        for period in moving_averages:
            if len(data) >= period:
                ma_name = f"MA{period}"
                # Create a copy to avoid the SettingWithCopyWarning
                data_copy = data.copy()
                data_copy.loc[:, ma_name] = data_copy[close_col].rolling(window=period).mean()
                
                fig.add_trace(
                    go.Scatter(
                        x=data_copy[date_col],
                        y=data_copy[ma_name],
                        name=ma_name,
                        line=dict(width=2)
                    ),
                    row=1, col=1
                )
    
    # Add volume if available
    if volume_col and volume_col in data.columns:
        # Calculate color for volume bars
        colors = [COLORS['positive'] if data[close_col].iloc[i] >= data[open_col].iloc[i] 
                 else COLORS['negative'] for i in range(len(data))]
        
        fig.add_trace(
            go.Bar(
                x=data[date_col],
                y=data[volume_col],
                name="Volume",
                marker=dict(
                    color=colors,
                    opacity=0.7
                )
            ),
            row=2, col=1
        )
    
    # Set title
    if title:
        fig.update_layout(title=title)
    
    # Add range slider if requested
    if range_slider:
        fig.update_layout(
            xaxis=dict(
                rangeslider=dict(visible=True),
                rangeslider_thickness=0.05,
            )
        )
    
    # Apply consistent styling
    fig = apply_chart_style(fig)
    
    # Update height
    fig.update_layout(height=height)
    
    return fig

def event_timeline_chart(price_data: pd.DataFrame,
                         events: Dict[str, pd.DataFrame],
                         date_col: str = 'date',
                         price_col: str = 'close',
                         title: Optional[str] = None,
                         height: int = 500,
                         event_config: Optional[Dict[str, Dict]] = None,
                         range_slider: bool = True):
    """
    Create a price chart with event markers overlaid on the timeline.
    
    Args:
        price_data: DataFrame containing price data
        events: Dict of DataFrames containing event data (key is event type)
        date_col: Name of date column (must be present in all DataFrames)
        price_col: Name of price column to display
        title: Chart title
        height: Chart height in pixels
        event_config: Dict of configuration for each event type (icons, colors)
        range_slider: Whether to include a range slider
    
    Returns:
        Plotly figure
    
    Example:
        ```python
        events = {
            'earnings': earnings_df,
            'filings': filings_df,
            'news': news_df
        }
        
        event_config = {
            'earnings': {'icon': '📊', 'color': '#4caf50'},
            'filings': {'icon': '📄', 'color': '#2196f3'},
            'news': {'icon': '📰', 'color': '#ff9800'}
        }
        
        fig = event_timeline_chart(price_df, events, event_config=event_config)
        st.plotly_chart(fig, use_container_width=True)
        ```
    """
    # Default event configuration
    if not event_config:
        event_config = {
            'earnings': {'symbol': '📊', 'color': COLORS['positive']},
            'filings': {'symbol': '📄', 'color': COLORS['neutral']},
            'news': {'symbol': '📰', 'color': COLORS['secondary']},
            'insider': {'symbol': '👤', 'color': '#9c27b0'},
            'rating': {'symbol': '⭐', 'color': '#ff5722'},
            'default': {'symbol': '•', 'color': COLORS['text']}
        }
    
    # Create base figure with price data
    fig = px.line(
        price_data,
        x=date_col,
        y=price_col,
        title=title,
        height=height,
    )
    
    # Style the price line
    fig.update_traces(line=dict(color=COLORS['primary'], width=2))
    
    # Track y-positions for event markers to avoid overlap
    date_positions = {}
    
    # Add event markers for each event type
    for event_type, event_df in events.items():
        if date_col not in event_df.columns:
            continue
            
        config = event_config.get(event_type, event_config.get('default', {}))
        symbol = config.get('symbol', '•')
        color = config.get('color', COLORS['text'])
        
        # Process each event
        for _, event in event_df.iterrows():
            event_date = event[date_col]
            
            # Find closest price point
            if isinstance(event_date, str):
                # Convert string to datetime if needed
                try:
                    event_date = pd.to_datetime(event_date)
                except:
                    continue
            
            # Find price on event date (or closest date)
            price_point = price_data.loc[price_data[date_col] >= event_date].iloc[0] if not price_data[price_data[date_col] >= event_date].empty else None
            
            if price_point is None:
                continue
                
            price_value = price_point[price_col]
            price_date = price_point[date_col]
            
            # Adjust y-position to avoid overlapping markers on same date
            position_key = price_date.strftime('%Y-%m-%d') if hasattr(price_date, 'strftime') else str(price_date)
            position_count = date_positions.get(position_key, 0)
            date_positions[position_key] = position_count + 1
            
            # Calculate adjusted position (add small offset for multiple events on same date)
            y_position = price_value * (1 + 0.02 * position_count)
            
            # Get hover text
            if 'title' in event:
                hover_text = f"{event_type.capitalize()}: {event['title']}"
            elif 'text' in event:
                hover_text = f"{event_type.capitalize()}: {event['text'][:100]}..."
            else:
                hover_text = f"{event_type.capitalize()} event"
            
            # Add marker
            fig.add_trace(
                go.Scatter(
                    x=[price_date],
                    y=[y_position],
                    mode='markers+text',
                    text=[symbol],
                    textposition="middle center",
                    textfont=dict(size=14),
                    marker=dict(
                        color=color,
                        size=20,
                        opacity=0.8,
                        line=dict(width=1, color='white')
                    ),
                    name=event_type.capitalize(),
                    hoverinfo='text',
                    hovertext=hover_text,
                    showlegend=False
                )
            )
    
    # Add a legend for event types
    for event_type, config in event_config.items():
        if event_type == 'default':
            continue
            
        if event_type in events:
            symbol = config.get('symbol', '•')
            color = config.get('color', COLORS['text'])
            
            fig.add_trace(
                go.Scatter(
                    x=[None],
                    y=[None],
                    mode='markers+text',
                    text=[symbol],
                    textposition="middle center",
                    marker=dict(color=color, size=15),
                    name=event_type.capitalize()
                )
            )
    
    # Add range slider if requested
    if range_slider:
        fig.update_layout(
            xaxis=dict(
                rangeslider=dict(visible=True),
                rangeslider_thickness=0.05,
            )
        )
    
    # Apply consistent styling
    fig = apply_chart_style(fig)
    
    return fig

def heatmap(data: pd.DataFrame,
           x: str,
           y: str,
           z: str,
           title: Optional[str] = None,
           height: int = 500,
           color_scale: Optional[List] = None,
           hover_text: Optional[str] = None):
    """
    Create a styled heatmap.
    
    Args:
        data: DataFrame containing the data
        x: Column to use for x-axis
        y: Column to use for y-axis
        z: Column to use for color values
        title: Chart title
        height: Chart height in pixels
        color_scale: Custom color scale
        hover_text: Column to use for hover text
    
    Returns:
        Plotly figure
    
    Example:
        ```python
        fig = heatmap(df, 'quarter', 'year', 'growth_rate')
        st.plotly_chart(fig, use_container_width=True)
        ```
    """
    # Default color scale
    if color_scale is None:
        color_scale = [
            [0, "rgb(34, 94, 168)"],  # Dark blue
            [0.25, "rgb(65, 125, 167)"],  # Medium blue
            [0.5, "rgb(120, 120, 120)"],  # Gray
            [0.75, "rgb(202, 111, 70)"],  # Medium orange
            [1, "rgb(237, 85, 59)"]   # Dark orange
        ]
    
    # Create heatmap figure
    fig = px.density_heatmap(
        data_frame=data,
        x=x,
        y=y,
        z=z,
        title=title,
        height=height,
        color_continuous_scale=color_scale,
        text_auto='.2f' if hover_text is None else False,
        hover_name=hover_text
    )
    
    # Apply consistent styling
    fig = apply_chart_style(fig)
    
    # Additional heatmap-specific styling
    fig.update_layout(
        coloraxis_colorbar=dict(
            title=z,
            titleside="right",
            ticks="outside",
            tickfont=dict(size=10)
        )
    )
    
    return fig

def radar_chart(data: pd.DataFrame,
                categories: List[str],
                values: List[str],
                title: Optional[str] = None,
                height: int = 500,
                color_discrete_map: Optional[Dict] = None):
    """
    Create a radar (spider) chart for comparing multiple metrics.
    
    Args:
        data: DataFrame containing the data
        categories: List of category names for the radar axes
        values: List of column names containing values for each series
        title: Chart title
        height: Chart height in pixels
        color_discrete_map: Custom color mapping for series
    
    Returns:
        Plotly figure
    
    Example:
        ```python
        fig = radar_chart(df, ['metric1', 'metric2', 'metric3'], ['company1', 'company2'])
        st.plotly_chart(fig, use_container_width=True)
        ```
    """
    fig = go.Figure()
    
    # Default colors if not provided
    series_colors = color_discrete_map or {
        values[i]: [COLORS['primary'], COLORS['secondary'], COLORS['neutral'], 
                   COLORS['positive'], COLORS['negative']][i % 5]
        for i in range(len(values))
    }
    
    # Add a trace for each value column/series
    for value_col in values:
        fig.add_trace(go.Scatterpolar(
            r=data[value_col].tolist(),
            theta=categories,
            fill='toself',
            name=value_col,
            line=dict(color=series_colors.get(value_col, COLORS['primary']))
        ))
    
    # Set chart layout
    fig.update_layout(
        title=title,
        height=height,
        polar=dict(
            radialaxis=dict(
                visible=True,
                linecolor=COLORS['grid']
            ),
            angularaxis=dict(
                linecolor=COLORS['grid']
            ),
            bgcolor='rgba(30,30,30,0.3)'
        )
    )
    
    # Apply consistent styling
    fig = apply_chart_style(fig)
    
    return fig

def scatter_plot(data: pd.DataFrame,
                x: str,
                y: str,
                title: Optional[str] = None,
                height: int = 400,
                color: Optional[str] = None,
                size: Optional[str] = None,
                hover_data: Optional[List[str]] = None,
                text: Optional[str] = None,
                trendline: Optional[str] = None,
                color_discrete_map: Optional[Dict] = None):
    """
    Create a styled scatter plot.
    
    Args:
        data: DataFrame containing the data
        x: Column to use for x-axis
        y: Column to use for y-axis
        title: Chart title
        height: Chart height in pixels
        color: Column to use for color encoding
        size: Column to use for point size
        hover_data: Additional columns to include in hover tooltip
        text: Column to use for point labels
        trendline: Type of trendline ('ols', 'lowess', None)
        color_discrete_map: Custom color mapping
    
    Returns:
        Plotly figure
    
    Example:
        ```python
        fig = scatter_plot(df, 'revenue', 'profit', color='sector', trendline='ols')
        st.plotly_chart(fig, use_container_width=True)
        ```
    """
    # Create figure
    fig = px.scatter(
        data,
        x=x,
        y=y,
        title=title,
        height=height,
        color=color,
        size=size,
        hover_data=hover_data,
        text=text,
        trendline=trendline,
        color_discrete_map=color_discrete_map
    )
    
    # Apply consistent styling
    fig = apply_chart_style(fig)
    
    return fig