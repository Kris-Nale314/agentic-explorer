"""
Interactive components for the Agentic Explorer application.

This module provides reusable interactive UI components with consistent styling.
"""

import streamlit as st
from typing import List, Dict, Any, Optional, Union, Callable
from datetime import datetime, timedelta

def styled_date_selector(label: str, key: Optional[str] = None, 
                        default_days_back: int = 90,
                        min_date: Optional[datetime] = None,
                        max_date: Optional[datetime] = None):
    """
    Creates a styled date range selector with presets.
    
    Args:
        label: Label for the selector
        key: Optional key for the component
        default_days_back: Default number of days to look back
        min_date: Optional minimum date
        max_date: Optional maximum date
    
    Returns:
        Tuple of (start_date, end_date)
    
    Example:
        ```python
        start_date, end_date = styled_date_selector("Select date range")
        ```
    """
    # Create container
    container = st.container()
    
    with container:
        # Calculate default dates
        today = datetime.now().date()
        
        if not max_date:
            max_date = today
        else:
            max_date = max_date.date() if isinstance(max_date, datetime) else max_date
            
        if not min_date:
            # Default to 2 years back
            min_date = today - timedelta(days=2*365)
        else:
            min_date = min_date.date() if isinstance(min_date, datetime) else min_date
        
        default_start = today - timedelta(days=default_days_back)
        default_start = max(default_start, min_date)
        
        # Create a row for the controls
        col1, col2 = st.columns([1, 2])
        
        # Preset options
        presets = {
            "Last 30 days": (today - timedelta(days=30), today),
            "Last 90 days": (today - timedelta(days=90), today),
            "Last 6 months": (today - timedelta(days=180), today),
            "Last year": (today - timedelta(days=365), today),
            "Year to date": (datetime(today.year, 1, 1).date(), today),
            "Custom": (default_start, today)
        }
        
        # Add preset selector
        with col1:
            selected_preset = st.selectbox(
                label,
                options=list(presets.keys()),
                index=2,  # Default to 90 days
                key=f"{key}_preset"
            )
        
        # Get dates from preset
        start_date, end_date = presets[selected_preset]
        
        # Add custom date selector if Custom is selected
        if selected_preset == "Custom":
            with col2:
                # Create custom date inputs
                date_cols = st.columns(2)
                with date_cols[0]:
                    start_date = st.date_input(
                        "Start date",
                        value=default_start,
                        min_value=min_date,
                        max_value=today,
                        key=f"{key}_start"
                    )
                
                with date_cols[1]:
                    end_date = st.date_input(
                        "End date",
                        value=today,
                        min_value=start_date,
                        max_value=max_date,
                        key=f"{key}_end"
                    )
    
    # Apply custom styling
    st.markdown("""
    <style>
        div[data-testid="stSelectbox"] > div:first-child {
            background-color: rgba(30, 30, 30, 0.7);
            border-radius: 5px;
            border-color: rgba(80, 80, 80, 0.5);
        }
        
        div[data-testid="stDateInput"] > div:first-child {
            background-color: rgba(30, 30, 30, 0.7);
            border-radius: 5px;
            border-color: rgba(80, 80, 80, 0.5);
        }
    </style>
    """, unsafe_allow_html=True)
    
    return start_date, end_date

def toggle_button(label: str, key: Optional[str] = None, default: bool = False):
    """
    Creates a styled toggle button.
    
    Args:
        label: Button label
        key: Optional key for the component
        default: Default state (True/False)
    
    Returns:
        Boolean indicating the button state
    
    Example:
        ```python
        is_enabled = toggle_button("Enable Feature")
        ```
    """
    # Create a unique key if not provided
    if not key:
        key = f"toggle_{label}_{id(label)}"
    
    # Get current state from session state
    if key not in st.session_state:
        st.session_state[key] = default
    
    # Define toggle function
    def toggle():
        st.session_state[key] = not st.session_state[key]
    
    # Determine button style based on state
    if st.session_state[key]:
        button_style = f"""
        background-color: rgba(0, 184, 212, 0.8);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: 500;
        """
        prefix = "✓ "
    else:
        button_style = f"""
        background-color: rgba(80, 80, 80, 0.8);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: 500;
        """
        prefix = "○ "
    
    # Create the button with custom styling
    st.markdown(f"""
    <style>
        div[data-testid="stButton"] button:hover {{
            background-color: rgba(0, 184, 212, 0.6);
            color: white;
        }}
    </style>
    """, unsafe_allow_html=True)
    
    st.button(
        f"{prefix}{label}",
        on_click=toggle,
        key=f"{key}_button"
    )
    
    return st.session_state[key]

def filter_sidebar(title: str = "Filters", key_prefix: Optional[str] = None):
    """
    Creates a styled filter sidebar that can be toggled.
    
    Args:
        title: Title for the filter sidebar
        key_prefix: Optional prefix for component keys
    
    Returns:
        The sidebar container
    
    Example:
        ```python
        with filter_sidebar():
            st.selectbox("Category", ["All", "A", "B", "C"])
            st.slider("Price Range", 0, 100, (25, 75))
        ```
    """
    # Generate key prefix if not provided
    if not key_prefix:
        key_prefix = f"filter_{id(title)}"
    
    # Check if sidebar is open in session state
    if f"{key_prefix}_open" not in st.session_state:
        st.session_state[f"{key_prefix}_open"] = False
    
    # Create toggle button
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"### {title}")
    
    with col2:
        if st.button(
            "▼" if st.session_state[f"{key_prefix}_open"] else "▶",
            key=f"{key_prefix}_toggle"
        ):
            st.session_state[f"{key_prefix}_open"] = not st.session_state[f"{key_prefix}_open"]
    
    # Create container for filters
    filter_container = st.container()
    
    # Show/hide based on state
    if not st.session_state[f"{key_prefix}_open"]:
        filter_container.empty()
    
    # Apply styling
    st.markdown("""
    <style>
        div.stButton button {
            background-color: transparent;
            color: rgba(250, 250, 250, 0.8);
            border: none;
            font-size: 1.2rem;
            line-height: 1;
            padding: 0.3rem 0.5rem;
        }
        
        div.stButton button:hover {
            background-color: rgba(0, 184, 212, 0.2);
            color: rgba(250, 250, 250, 1);
        }
    </style>
    """, unsafe_allow_html=True)
    
    return filter_container

def search_box(placeholder: str = "Search...", key: Optional[str] = None, 
             on_change: Optional[Callable] = None):
    """
    Creates a styled search box.
    
    Args:
        placeholder: Placeholder text
        key: Optional key for the component
        on_change: Optional callback function for when input changes
    
    Returns:
        The search text
    
    Example:
        ```python
        search_text = search_box("Search companies...")
        ```
    """
    # Create a container for the search box
    container = st.container()
    
    # Add custom styling
    st.markdown("""
    <style>
        div[data-testid="stTextInput"] > div:first-child {
            background-color: rgba(30, 30, 30, 0.7);
            border-radius: 20px;
            padding-left: 10px;
            padding-right: 10px;
            border: 1px solid rgba(80, 80, 80, 0.5);
        }
        
        div[data-testid="stTextInput"] input {
            color: rgba(250, 250, 250, 0.9);
        }
        
        div[data-testid="stTextInput"]::before {
            content: "🔍";
            position: absolute;
            left: 10px;
            top: 50%;
            transform: translateY(-50%);
            color: rgba(250, 250, 250, 0.6);
            z-index: 1;
        }
        
        div[data-testid="stTextInput"] input {
            padding-left: 30px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Create the search input
    with container:
        search_text = st.text_input(
            "Search", # Add a label to avoid the empty label warning
            placeholder=placeholder,
            key=key,
            on_change=on_change,
            label_visibility="collapsed" # Hide the label visually
        )
    
    return search_text

def segmented_control(options: List[str], default_index: int = 0, 
                      key: Optional[str] = None):
    """
    Creates a styled segmented control (button group).
    
    Args:
        options: List of option labels
        default_index: Index of the default selected option
        key: Optional key for the component
    
    Returns:
        The selected option label
    
    Example:
        ```python
        view_mode = segmented_control(["Table", "Chart", "Cards"])
        ```
    """
    # Generate key if not provided
    if not key:
        key = f"segment_{id(options)}"
    
    # Initialize session state
    if f"{key}_selected" not in st.session_state:
        st.session_state[f"{key}_selected"] = default_index
    
    # Create container
    container = st.container()
    
    # Create columns for each option
    cols = st.columns(len(options))
    
    # Helper function to handle button clicks
    def set_selected(index):
        st.session_state[f"{key}_selected"] = index
    
    # Add buttons for each option
    for i, option in enumerate(options):
        with cols[i]:
            is_selected = st.session_state[f"{key}_selected"] == i
            
            if is_selected:
                button_style = """
                background-color: rgba(0, 184, 212, 0.8);
                color: white;
                """
            else:
                button_style = """
                background-color: rgba(40, 40, 40, 0.8);
                color: rgba(250, 250, 250, 0.7);
                """
            
            st.button(
                option,
                on_click=set_selected,
                args=(i,),
                key=f"{key}_{i}"
            )
    
    # Add custom styling
    st.markdown(f"""
    <style>
        div[data-testid="stHorizontalBlock"] {{
            display: flex;
            justify-content: center;
            gap: 0 !important;
        }}
        
        div[data-testid="stHorizontalBlock"] > div {{
            padding: 0 !important;
        }}
        
        div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] {{
            width: 100%;
            text-align: center;
        }}
        
        div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button {{
            width: 100%;
            border-radius: 0;
            border: 1px solid rgba(60, 60, 60, 0.8);
            padding: 0.3rem 0;
        }}
        
        div[data-testid="stHorizontalBlock"] div[data-testid="stButton"]:first-child button {{
            border-top-left-radius: 5px;
            border-bottom-left-radius: 5px;
        }}
        
        div[data-testid="stHorizontalBlock"] div[data-testid="stButton"]:last-child button {{
            border-top-right-radius: 5px;
            border-bottom-right-radius: 5px;
        }}
    </style>
    """, unsafe_allow_html=True)
    
    # Return the selected option
    return options[st.session_state[f"{key}_selected"]]

def tags_input(label: str, available_tags: List[str], 
              default_tags: Optional[List[str]] = None,
              key: Optional[str] = None):
    """
    Creates an interface for selecting multiple tags from a list.
    
    Args:
        label: Label for the component
        available_tags: List of all available tags
        default_tags: List of initially selected tags
        key: Optional key for the component
    
    Returns:
        List of selected tags
    
    Example:
        ```python
        selected_tags = tags_input("Industries", 
                                 ["Technology", "Healthcare", "Finance"],
                                 ["Technology"])
        ```
    """
    # Generate key if not provided
    if not key:
        key = f"tags_{id(label)}"
    
    # Initialize session state
    if f"{key}_selected" not in st.session_state:
        st.session_state[f"{key}_selected"] = default_tags or []
    
    # Create container
    container = st.container()
    
    with container:
        # Add label
        st.markdown(f"**{label}**")
        
        # Create layout
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Show selected tags with remove option
            if not st.session_state[f"{key}_selected"]:
                st.caption("No tags selected")
            else:
                # Add custom CSS for tags
                st.markdown("""
                <style>
                    .tags-container {
                        display: flex;
                        flex-wrap: wrap;
                        gap: 5px;
                        margin-bottom: 10px;
                    }
                    
                    .tag {
                        background-color: rgba(0, 184, 212, 0.2);
                        color: rgba(250, 250, 250, 0.9);
                        border: 1px solid rgba(0, 184, 212, 0.5);
                        border-radius: 15px;
                        padding: 2px 8px;
                        font-size: 0.8rem;
                        display: inline-flex;
                        align-items: center;
                    }
                    
                    .tag-remove {
                        margin-left: 5px;
                        cursor: pointer;
                        color: rgba(250, 250, 250, 0.7);
                    }
                </style>
                """, unsafe_allow_html=True)
                
                # Build HTML for tags
                tags_html = '<div class="tags-container">'
                for tag in st.session_state[f"{key}_selected"]:
                    tags_html += f'<div class="tag">{tag}</div>'
                tags_html += '</div>'
                
                st.markdown(tags_html, unsafe_allow_html=True)
        
        with col2:
            # Add dropdown for adding new tags
            available_to_add = [t for t in available_tags if t not in st.session_state[f"{key}_selected"]]
            
            if available_to_add:
                selected_to_add = st.selectbox(
                    "Add tag",
                    [""] + available_to_add,
                    key=f"{key}_add"
                )
                
                if selected_to_add:
                    st.session_state[f"{key}_selected"].append(selected_to_add)
                    # This will trigger a rerun
                    st.experimental_rerun()
            else:
                st.caption("All tags selected")
    
    # For removing tags (using button clicks)
    col_count = min(len(st.session_state[f"{key}_selected"]), 5)
    if col_count > 0:
        remove_cols = st.columns(col_count)
        
        for i, tag in enumerate(st.session_state[f"{key}_selected"][:col_count]):
            with remove_cols[i]:
                if st.button(f"❌ {tag}", key=f"{key}_remove_{i}"):
                    st.session_state[f"{key}_selected"].remove(tag)
                    st.experimental_rerun()
    
    return st.session_state[f"{key}_selected"]