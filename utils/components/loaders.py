"""
Loading and progress indicator components for the Agentic Explorer application.

This module provides fun and informative progress indicators for long-running processes.
"""

import streamlit as st
import time
from typing import Optional, List, Dict, Any, Callable
import random

def neon_spinner(message: str, key: Optional[str] = None):
    """
    Creates a neon-styled spinner with pulsating effects.
    
    Args:
        message: Text to display with the spinner
        key: Optional key for the component
    
    Returns:
        A spinner container that can be used as a context manager
    
    Example:
        ```python
        with neon_spinner("Processing data..."):
            time.sleep(5)  # Some long operation
        ```
    """
    # Custom CSS for neon effect
    st.markdown("""
    <style>
        @keyframes neon-pulse {
            0% {
                text-shadow: 0 0 5px #00b8d4, 0 0 10px #00b8d4, 0 0 15px #00b8d4;
            }
            50% {
                text-shadow: 0 0 10px #00b8d4, 0 0 20px #00b8d4, 0 0 30px #00b8d4, 0 0 40px #00b8d4;
            }
            100% {
                text-shadow: 0 0 5px #00b8d4, 0 0 10px #00b8d4, 0 0 15px #00b8d4;
            }
        }
        
        @keyframes ripple {
            0% {
                box-shadow: 0 0 0 0 rgba(0, 184, 212, 0.3), 0 0 0 0.5em rgba(0, 184, 212, 0.2), 0 0 0 1em rgba(0, 184, 212, 0.1);
            }
            100% {
                box-shadow: 0 0 0 0.5em rgba(0, 184, 212, 0.2), 0 0 0 1em rgba(0, 184, 212, 0.1), 0 0 0 1.5em rgba(0, 184, 212, 0);
            }
        }
        
        .neon-spinner-container {
            display: flex;
            align-items: center;
            margin: 1rem 0;
            padding: 1rem;
            background: rgba(30, 30, 30, 0.7);
            border-radius: 10px;
        }
        
        .neon-spinner {
            width: 1.5rem;
            height: 1.5rem;
            border-radius: 50%;
            background: #00b8d4;
            margin-right: 1rem;
            animation: ripple 1.5s linear infinite;
        }
        
        .neon-message {
            color: #f5f5f5;
            font-weight: 500;
            animation: neon-pulse 2s infinite;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Create spinner container
    spinner_placeholder = st.empty(key=key)
    
    # Display the spinner
    spinner_placeholder.markdown(f"""
    <div class="neon-spinner-container">
        <div class="neon-spinner"></div>
        <div class="neon-message">{message}</div>
    </div>
    """, unsafe_allow_html=True)
    
    return spinner_placeholder

def thinking_animation(message: str, key: Optional[str] = None):
    """
    Displays a fun "thinking" animation with animated messages.
    
    Args:
        message: The base message to display
        key: Optional key for the component
    
    Returns:
        A placeholder that can be used to update the message
    
    Example:
        ```python
        thinking = thinking_animation("AI assistant is thinking")
        # Do long computation
        thinking.complete("Analysis complete!")
        ```
    """
    # Custom CSS for the animation
    st.markdown("""
    <style>
        @keyframes gradient-shift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        .thinking-container {
            background: linear-gradient(45deg, #121212, #1e1e1e, #2d2d2d, #1e1e1e, #121212);
            background-size: 500% 500%;
            animation: gradient-shift 10s ease infinite;
            padding: 1.5rem;
            border-radius: 10px;
            margin: 1rem 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .thinking-header {
            font-size: 1.2rem;
            font-weight: 600;
            color: #00b8d4;
            margin-bottom: 1rem;
        }
        
        .thinking-message {
            color: #f5f5f5;
            margin: 0.3rem 0;
            opacity: 0.8;
            font-size: 1rem;
        }
        
        .thinking-dots span {
            display: inline-block;
            width: 8px;
            height: 8px;
            background: #00b8d4;
            border-radius: 50%;
            margin: 0 3px;
            opacity: 0;
            animation: thinking-dot 1.5s infinite;
        }
        
        .thinking-dots span:nth-child(1) {
            animation-delay: 0s;
        }
        
        .thinking-dots span:nth-child(2) {
            animation-delay: 0.3s;
        }
        
        .thinking-dots span:nth-child(3) {
            animation-delay: 0.6s;
        }
        
        @keyframes thinking-dot {
            0%, 20% {
                opacity: 0;
            }
            50% {
                opacity: 1;
            }
            80%, 100% {
                opacity: 0;
            }
        }
        
        .thinking-progress {
            height: 4px;
            background: linear-gradient(90deg, #00b8d4, #4caf50);
            margin-top: 1rem;
            width: 0%;
            transition: width 0.3s ease;
            border-radius: 2px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Create placeholder
    placeholder = st.empty(key=key)
    
    # Display initial thinking animation
    placeholder.markdown(f"""
    <div class="thinking-container">
        <div class="thinking-header">{message}</div>
        <div class="thinking-message">
            Processing
            <span class="thinking-dots">
                <span></span><span></span><span></span>
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Return object with update methods
    class ThinkingIndicator:
        def __init__(self, placeholder, message):
            self.placeholder = placeholder
            self.message = message
        
        def update(self, new_message):
            """Update the thinking message."""
            self.placeholder.markdown(f"""
            <div class="thinking-container">
                <div class="thinking-header">{self.message}</div>
                <div class="thinking-message">
                    {new_message}
                    <span class="thinking-dots">
                        <span></span><span></span><span></span>
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            return self
        
        def complete(self, completion_message=None):
            """Complete the animation with optional message."""
            if completion_message:
                html = f"""
                <div class="thinking-container" style="background: linear-gradient(45deg, #121212, #1e1e1e, #2d2d2d, #1e1e1e, #121212); background-size: 500% 500%;">
                    <div class="thinking-header">{self.message}</div>
                    <div class="thinking-message" style="color: #4caf50; font-weight: 500;">✓ {completion_message}</div>
                    <div class="thinking-progress" style="width: 100%"></div>
                </div>
                """
            else:
                html = f"""
                <div class="thinking-container" style="background: linear-gradient(45deg, #121212, #1e1e1e, #2d2d2d, #1e1e1e, #121212); background-size: 500% 500%;">
                    <div class="thinking-header">{self.message}</div>
                    <div class="thinking-message" style="color: #4caf50; font-weight: 500;">✓ Complete</div>
                    <div class="thinking-progress" style="width: 100%"></div>
                </div>
                """
                
            self.placeholder.markdown(html, unsafe_allow_html=True)
            return self
        
        def error(self, error_message):
            """Show an error state."""
            html = f"""
            <div class="thinking-container" style="background: linear-gradient(45deg, #121212, #1e1e1e, #2d2d2d, #1e1e1e, #121212); background-size: 500% 500%;">
                <div class="thinking-header">{self.message}</div>
                <div class="thinking-message" style="color: #f44336; font-weight: 500;">❌ {error_message}</div>
                <div class="thinking-progress" style="width: 100%; background: linear-gradient(90deg, #f44336, #ff9800);"></div>
            </div>
            """
                
            self.placeholder.markdown(html, unsafe_allow_html=True)
            return self
    
    return ThinkingIndicator(placeholder, message)