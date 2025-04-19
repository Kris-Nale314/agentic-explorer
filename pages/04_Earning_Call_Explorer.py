"""
Earnings Call Explorer for the Agentic Explorer platform.

This page provides analysis of earnings call transcripts, highlighting language patterns,
key topics, and potential signals that could indicate future business impacts.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import os
import json
import re

# Import our custom components
from utils.components.layout import page_container, card, two_column_layout, metrics_row
from utils.components.charts import line_chart, bar_chart
from utils.components.data_display import styled_dataframe, metric_card
from utils.components.interactive import styled_date_selector, segmented_control, search_box
from utils.components.loaders import neon_spinner
from utils.components.themes import apply_theme, color, get_chart_colors

# Import document assessment tools
from core.tools.docuAssess import (
    clean_text,
    extract_qa_section,
    extract_questions,
    extract_answers,
    extract_speakers,
    detect_uncertainty,
    categorize_topics,
    detect_emphasis_changes,
    analyze_comparative_language,
    categorize_analyst_questions,
    analyze_management_language,
    extract_guidance,
    detect_warning_signals,
    detect_opportunity_signals,
    create_sentiment_timeline,
    create_topic_distribution
)

# Apply theme enhancements
apply_theme()

# Helper function for uncertainty color
def get_uncertainty_color(score):
    """Get color based on uncertainty score."""
    if score < 10:
        return "#4CAF50"  # Green
    elif score < 20:
        return "#FFEB3B"  # Yellow
    else:
        return "#F44336"  # Red

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

def load_earnings_transcripts(ticker):
    """Load earnings call transcripts for a given ticker."""
    transcripts_path = get_datastore_path() / "companies" / ticker / "transcripts.parquet"
    if transcripts_path.exists():
        return pd.read_parquet(transcripts_path)
    return None

def earnings_call_explorer():
    """Main function for the Earnings Call Explorer page."""
    
    # Create page container with title
    with page_container("Earnings Call Explorer", "Analyze earnings call language patterns and signals"):
        # Get available tickers
        available_tickers = get_available_tickers()
        
        if not available_tickers:
            st.warning("No company data found in the dataStore. Please run the data collector first.")
            st.code("python -m utils.run_data_collector --tickers DELL,NVDA,TSLA,ACN --years 3", language="bash")
            return
        
        # Create sidebar for company selection
        st.sidebar.header("Company Selection")
        
        # Company selector
        selected_ticker = st.sidebar.selectbox(
            "Select Company",
            available_tickers,
            index=0
        )
        
        # Process selected company data
        if selected_ticker:
            # Load profile data
            profile = load_company_profile(selected_ticker)
            
            # Load earnings call transcripts
            transcripts = load_earnings_transcripts(selected_ticker)
            
            if profile and transcripts is not None and not transcripts.empty:
                # Extract company name
                company_name = profile.get("companyName", selected_ticker)
                
                # Display company header
                st.header(f"{company_name} ({selected_ticker}) Earnings Call Analysis")
                
                # Create transcript selector section
                with card("Transcript Selection"):
                    if 'quarter' in transcripts.columns and 'year' in transcripts.columns:
                        # Create options for selection
                        transcript_options = [
                            f"Q{row['quarter']} {row['year']}" 
                            for _, row in transcripts.iterrows()
                        ]
                        
                        # Add dates if available
                        if 'date' in transcripts.columns:
                            transcript_options = [
                                f"{opt} ({transcripts.iloc[i]['date'].strftime('%Y-%m-%d') if hasattr(transcripts.iloc[i]['date'], 'strftime') else transcripts.iloc[i]['date']})" 
                                for i, opt in enumerate(transcript_options)
                            ]
                    else:
                        # Fallback options
                        transcript_options = [f"Transcript {i+1}" for i in range(len(transcripts))]
                    
                    # Create selection columns
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        selected_transcript_idx = st.selectbox(
                            "Select Earnings Call",
                            range(len(transcript_options)),
                            format_func=lambda x: transcript_options[x]
                        )
                    
                    # Get current and previous transcripts
                    current_transcript = transcripts.iloc[selected_transcript_idx]
                    
                    # Check if comparison is possible
                    comparison_possible = selected_transcript_idx < len(transcripts) - 1
                    
                    with col2:
                        enable_comparison = st.checkbox(
                            "Compare with Previous", 
                            value=comparison_possible,
                            disabled=not comparison_possible
                        )
                    
                    # Get previous transcript if comparison enabled
                    previous_transcript = None
                    if enable_comparison and comparison_possible:
                        previous_transcript = transcripts.iloc[selected_transcript_idx + 1]
                
                # Create analysis view selector
                analysis_view = segmented_control(
                    ["Overview", "Language Analysis", "Q&A Analysis", "Signal Detection", "Full Transcript"],
                    key="analysis_view"
                )
                
                # Display selected view
                if analysis_view == "Overview":
                    display_overview(current_transcript, previous_transcript if enable_comparison else None)
                elif analysis_view == "Language Analysis":
                    display_language_analysis(current_transcript, previous_transcript if enable_comparison else None)
                elif analysis_view == "Q&A Analysis":
                    display_qa_analysis(current_transcript)
                elif analysis_view == "Signal Detection":
                    display_signal_detection(current_transcript, previous_transcript if enable_comparison else None)
                else:  # "Full Transcript"
                    display_full_transcript(current_transcript)
            else:
                st.warning(f"No earnings call transcripts found for {selected_ticker}")

def display_overview(transcript, previous_transcript=None):
    """Display overview of earnings call transcript."""
    
    # Check if transcript has content
    if 'content' not in transcript or not transcript['content']:
        st.warning("This transcript does not contain any content to analyze")
        return
    
    # Get transcript content
    content = transcript['content']
    
    # Clean text for analysis
    cleaned_content = clean_text(content)
    
    # Extract Q&A section
    qa_section = extract_qa_section(cleaned_content)
    
    # Get transcript metadata
    st.markdown("## Earnings Call Summary")
    
    # Create metadata card
    with card("Call Information"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'quarter' in transcript and 'year' in transcript:
                st.markdown(f"**Quarter:** Q{transcript['quarter']} {transcript['year']}")
            
            if 'date' in transcript:
                date_str = transcript['date'].strftime('%Y-%m-%d') if hasattr(transcript['date'], 'strftime') else transcript['date']
                st.markdown(f"**Date:** {date_str}")
        
        with col2:
            # Show basic stats
            total_words = len(cleaned_content.split())
            st.markdown(f"**Total Length:** {total_words:,} words")
            
            if qa_section:
                qa_words = len(qa_section.split())
                presentation_words = total_words - qa_words
                st.markdown(f"**Q&A Section:** {qa_words:,} words ({qa_words/total_words:.0%})")
            else:
                st.markdown("**Q&A Section:** Not identified")
        
        with col3:
            # Show basic uncertainty score
            uncertainty = detect_uncertainty(cleaned_content)
            
            # Create uncertainty indicator
            if uncertainty['score'] < 10:
                uncertainty_color = "#4CAF50"  # Green
                uncertainty_level = "Low"
            elif uncertainty['score'] < 20:
                uncertainty_color = "#FFEB3B"  # Yellow
                uncertainty_level = "Moderate"
            else:
                uncertainty_color = "#F44336"  # Red
                uncertainty_level = "High"
            
            st.markdown(f"**Uncertainty Level:** <span style='color:{uncertainty_color};'>{uncertainty_level}</span> ({uncertainty['score']:.1f})", unsafe_allow_html=True)
            
            # Show top uncertainty term
            if uncertainty['found_terms']:
                top_term = uncertainty['found_terms'][0]
                st.markdown(f"**Top Uncertainty Term:** \"{top_term['term']}\" ({top_term['count']} mentions)")
    
    # Create two columns for visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        # Topic distribution visualization
        with card("Topic Distribution"):
            # Create topic distribution chart
            fig = create_topic_distribution(cleaned_content)
            st.plotly_chart(fig, use_container_width=True)
            
            # Show top 3 topics
            topic_scores = categorize_topics(cleaned_content)
            sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)[:3]
            
            st.markdown("**Primary Topics:**")
            for topic, score in sorted_topics:
                st.markdown(f"- {topic.capitalize()}: {score:.1f}")
    
    with col2:
        # Sentiment timeline visualization
        with card("Sentiment Timeline"):
            # Create sentiment timeline chart
            fig = create_sentiment_timeline(cleaned_content)
            
            if fig:
                st.plotly_chart(fig, use_container_width=True)
                st.caption("This chart shows sentiment and uncertainty levels throughout the document")
            else:
                st.warning("Transcript too short for meaningful sentiment timeline analysis")
    
    # Guidance statements
    with card("Forward-Looking Statements"):
        guidance_statements = extract_guidance(cleaned_content)
        
        if guidance_statements:
            # Show top 5 guidance statements
            st.markdown(f"**Found {len(guidance_statements)} forward-looking statements. Top examples:**")
            
            for i, statement in enumerate(guidance_statements[:5]):
                st.markdown(f"{i+1}. \"{statement['statement']}\"")
                st.markdown(f"   *Trigger: \"{statement['trigger_phrase']}\"*")
                st.markdown("---")
        else:
            st.warning("No clear forward-looking statements detected")
    
    # Signal overview
    with card("Signal Overview"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Warning signals
            previous_content = previous_transcript['content'] if previous_transcript is not None else None
            warning_signals = detect_warning_signals(cleaned_content, previous_content)
            
            if warning_signals:
                st.markdown(f"**⚠️ {len(warning_signals)} Warning Signals Detected**")
                
                for signal in warning_signals:
                    severity_color = "#F44336" if signal['severity'] == 'high' else "#FF9800"
                    st.markdown(f"- <span style='color:{severity_color};'>**{signal['description']}**</span>", unsafe_allow_html=True)
            else:
                st.markdown("**✓ No significant warning signals detected**")
        
        with col2:
            # Opportunity signals
            previous_content = previous_transcript['content'] if previous_transcript is not None else None
            opportunity_signals = detect_opportunity_signals(cleaned_content, previous_content)
            
            if opportunity_signals:
                st.markdown(f"**🚀 {len(opportunity_signals)} Opportunity Signals Detected**")
                
                for signal in opportunity_signals:
                    strength_color = "#4CAF50" if signal['strength'] == 'high' else "#8BC34A"
                    st.markdown(f"- <span style='color:{strength_color};'>**{signal['description']}**</span>", unsafe_allow_html=True)
            else:
                st.markdown("**No significant opportunity signals detected**")

def display_language_analysis(transcript, previous_transcript=None):
    """Display detailed language pattern analysis of earnings call transcript."""
    
    # Check if transcript has content
    if 'content' not in transcript or not transcript['content']:
        st.warning("This transcript does not contain any content to analyze")
        return
    
    # Get transcript content
    content = transcript['content']
    
    # Clean text for analysis
    cleaned_content = clean_text(content)
    
    # Extract Q&A section
    qa_section = extract_qa_section(cleaned_content)
    
    # Get presentation section (everything before Q&A)
    presentation_section = cleaned_content.replace(qa_section, "").strip() if qa_section else cleaned_content
    
    st.markdown("## Language Pattern Analysis")
    
    # Create tabs for different analysis views
    tabs = st.tabs(["Uncertainty Analysis", "Topic Analysis", "Comparative Language", "Management Tone"])
    
    # Uncertainty Analysis Tab
    with tabs[0]:
        # Analyze different sections
        presentation_uncertainty = detect_uncertainty(presentation_section)
        qa_uncertainty = detect_uncertainty(qa_section) if qa_section else None
        overall_uncertainty = detect_uncertainty(cleaned_content)
        
        # Display uncertainty scores
        with card("Uncertainty Level by Section"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Create a gauge-like visualization for overall uncertainty
                uncertainty_color = get_uncertainty_color(overall_uncertainty['score'])
                
                st.markdown(f"""
                <div style="text-align: center;">
                    <h3>Overall Uncertainty</h3>
                    <div style="position: relative; width: 150px; height: 150px; margin: 0 auto;">
                        <svg width="150" height="150" viewBox="0 0 150 150">
                            <circle cx="75" cy="75" r="65" fill="none" stroke="#333333" stroke-width="15" />
                            <circle cx="75" cy="75" r="65" fill="none" stroke="{uncertainty_color}" stroke-width="15"
                                    stroke-dasharray="409" stroke-dashoffset="{409 - (min(overall_uncertainty['score'], 50) / 50 * 409)}"
                                    transform="rotate(-90 75 75)" />
                            <text x="75" y="85" text-anchor="middle" font-size="30" fill="white">{min(int(overall_uncertainty['score']), 50)}</text>
                        </svg>
                    </div>
                    <p>{overall_uncertainty['interpretation']}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                # Presentation section uncertainty
                uncertainty_color = get_uncertainty_color(presentation_uncertainty['score'])
                
                st.markdown(f"""
                <div style="text-align: center;">
                    <h3>Presentation Section</h3>
                    <div style="position: relative; width: 150px; height: 150px; margin: 0 auto;">
                        <svg width="150" height="150" viewBox="0 0 150 150">
                            <circle cx="75" cy="75" r="65" fill="none" stroke="#333333" stroke-width="15" />
                            <circle cx="75" cy="75" r="65" fill="none" stroke="{uncertainty_color}" stroke-width="15"
                                    stroke-dasharray="409" stroke-dashoffset="{409 - (min(presentation_uncertainty['score'], 50) / 50 * 409)}"
                                    transform="rotate(-90 75 75)" />
                            <text x="75" y="85" text-anchor="middle" font-size="30" fill="white">{min(int(presentation_uncertainty['score']), 50)}</text>
                        </svg>
                    </div>
                    <p>{presentation_uncertainty['interpretation']}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                # Q&A section uncertainty
                if qa_uncertainty:
                    uncertainty_color = get_uncertainty_color(qa_uncertainty['score'])
                    
                    st.markdown(f"""
                    <div style="text-align: center;">
                        <h3>Q&A Section</h3>
                        <div style="position: relative; width: 150px; height: 150px; margin: 0 auto;">
                            <svg width="150" height="150" viewBox="0 0 150 150">
                                <circle cx="75" cy="75" r="65" fill="none" stroke="#333333" stroke-width="15" />
                                <circle cx="75" cy="75" r="65" fill="none" stroke="{uncertainty_color}" stroke-width="15"
                                        stroke-dasharray="409" stroke-dashoffset="{409 - (min(qa_uncertainty['score'], 50) / 50 * 409)}"
                                        transform="rotate(-90 75 75)" />
                                <text x="75" y="85" text-anchor="middle" font-size="30" fill="white">{min(int(qa_uncertainty['score']), 50)}</text>
                            </svg>
                        </div>
                        <p>{qa_uncertainty['interpretation']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="text-align: center;">
                        <h3>Q&A Section</h3>
                        <p>No Q&A section detected in transcript</p>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Display uncertainty terms
        with card("Top Uncertainty Terms"):
            if overall_uncertainty['found_terms']:
                # Create a bar chart of top terms
                terms = [term['term'] for term in overall_uncertainty['found_terms'][:10]]
                counts = [term['count'] for term in overall_uncertainty['found_terms'][:10]]
                weights = [term['weight'] for term in overall_uncertainty['found_terms'][:10]]
                
                # Calculate weighted counts for visualization
                weighted_counts = [count * weight for count, weight in zip(counts, weights)]
                
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    x=terms,
                    y=weighted_counts,
                    marker_color='#F44336',
                    text=counts,
                    textposition='auto'
                ))
                
                fig.update_layout(
                    title="Top Uncertainty Terms (by weighted count)",
                    xaxis_title="Term",
                    yaxis_title="Weighted Count",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(30,30,30,0.3)',
                    font=dict(color='white')
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Display examples in context
                st.markdown("### Examples in Context")
                
                for term in overall_uncertainty['found_terms'][:3]:
                    # Find examples in the text
                    pattern = r'[^.!?]*\b' + re.escape(term['term']) + r'\b[^.!?]*[.!?]'
                    matches = re.findall(pattern, cleaned_content, re.IGNORECASE)
                    
                    if matches:
                        example = matches[0].strip()
                        # Highlight the term
                        highlighted = example.replace(term['term'], f"**{term['term']}**")
                        
                        st.markdown(f"- \"{highlighted}\"")
            else:
                st.warning("No significant uncertainty terms detected")
        
        # Historical comparison if available
        if previous_transcript is not None:
            with card("Uncertainty Comparison with Previous Call"):
                previous_content = previous_transcript['content']
                previous_cleaned = clean_text(previous_content)
                previous_uncertainty = detect_uncertainty(previous_cleaned)
                
                # Create comparison
                col1, col2 = st.columns(2)
                
                with col1:
                    # Current call uncertainty
                    st.markdown(f"**Current Call (Score: {overall_uncertainty['score']:.1f})**")
                    st.markdown(f"- Interpretation: {overall_uncertainty['interpretation']}")
                    st.markdown(f"- Top terms: {', '.join([term['term'] for term in overall_uncertainty['found_terms'][:3]])}")
                
                with col2:
                    # Previous call uncertainty
                    st.markdown(f"**Previous Call (Score: {previous_uncertainty['score']:.1f})**")
                    st.markdown(f"- Interpretation: {previous_uncertainty['interpretation']}")
                    st.markdown(f"- Top terms: {', '.join([term['term'] for term in previous_uncertainty['found_terms'][:3]])}")
                
                # Calculate change
                uncertainty_change = overall_uncertainty['score'] - previous_uncertainty['score']
                
                if abs(uncertainty_change) < 2:
                    change_desc = "Uncertainty level is virtually unchanged from the previous call."
                    change_color = "#FFEB3B"  # Yellow
                elif uncertainty_change > 0:
                    change_desc = f"Uncertainty level has increased by {uncertainty_change:.1f} points from the previous call."
                    change_color = "#F44336"  # Red
                else:
                    change_desc = f"Uncertainty level has decreased by {abs(uncertainty_change):.1f} points from the previous call."
                    change_color = "#4CAF50"  # Green
                
                st.markdown(f"**<span style='color:{change_color};'>Change: {change_desc}</span>**", unsafe_allow_html=True)
    
    # Topic Analysis Tab
    with tabs[1]:
        # Analyze topics for different sections
        overall_topics = categorize_topics(cleaned_content)
        presentation_topics = categorize_topics(presentation_section)
        qa_topics = categorize_topics(qa_section) if qa_section else {}
        
        # Create topic distribution visualization
        with card("Topic Distribution by Section"):
            # Convert to DataFrame for visualization
            topic_data = []
            
            for topic, score in overall_topics.items():
                presentation_score = presentation_topics.get(topic, 0)
                qa_score = qa_topics.get(topic, 0) if qa_topics else 0
                
                topic_data.append({
                    'Topic': topic.capitalize(),
                    'Overall': score,
                    'Presentation': presentation_score,
                    'Q&A': qa_score
                })
            
            # Create DataFrame
            topic_df = pd.DataFrame(topic_data)
            
            # Sort by overall score
            topic_df = topic_df.sort_values('Overall', ascending=False)
            
            # Create visualization
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=topic_df['Topic'],
                y=topic_df['Overall'],
                name='Overall',
                marker_color='#2196F3'
            ))
            
            fig.add_trace(go.Bar(
                x=topic_df['Topic'],
                y=topic_df['Presentation'],
                name='Presentation',
                marker_color='#4CAF50'
            ))
            
            if qa_section:
                fig.add_trace(go.Bar(
                    x=topic_df['Topic'],
                    y=topic_df['Q&A'],
                    name='Q&A',
                    marker_color='#FF9800'
                ))
            
            fig.update_layout(
                title="Topic Distribution by Section",
                xaxis_title="Topic",
                yaxis_title="Score",
                barmode='group',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(30,30,30,0.3)',
                font=dict(color='white')
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Historical comparison if available
        if previous_transcript is not None:
            with card("Topic Emphasis Changes from Previous Call"):
                previous_content = previous_transcript['content']
                previous_cleaned = clean_text(previous_content)
                
                # Detect emphasis changes
                emphasis_changes = detect_emphasis_changes(cleaned_content, previous_cleaned)
                
                # Display changes
                fig = go.Figure()
                
                # Prepare data for visualization
                topics = [change['topic'].capitalize() for change in emphasis_changes]
                percent_changes = [change['pct_change'] for change in emphasis_changes]
                
                # Define colors based on direction
                colors = ['#4CAF50' if pct > 0 else '#F44336' for pct in percent_changes]
                
                fig.add_trace(go.Bar(
                    x=topics,
                    y=percent_changes,
                    marker_color=colors,
                    text=[f"{pct:.0f}%" for pct in percent_changes],
                    textposition='auto'
                ))
                
                fig.update_layout(
                    title="Topic Emphasis Changes from Previous Call",
                    xaxis_title="Topic",
                    yaxis_title="Percent Change",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(30,30,30,0.3)',
                    font=dict(color='white')
                )
                
                # Add zero line
                fig.add_shape(
                    type="line",
                    x0=-0.5,
                    y0=0,
                    x1=len(topics) - 0.5,
                    y1=0,
                    line=dict(color="#FFFFFF", width=1, dash="dash"),
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Display significant changes
                significant_changes = [change for change in emphasis_changes if abs(change['pct_change']) > 50]
                
                if significant_changes:
                    st.markdown("### Significant Topic Shifts")
                    
                    for change in significant_changes:
                        if change['pct_change'] > 0:
                            st.markdown(f"- **{change['topic'].capitalize()}**: Increased emphasis by {change['pct_change']:.0f}% (from {change['previous_score']:.1f} to {change['current_score']:.1f})")
                        else:
                            st.markdown(f"- **{change['topic'].capitalize()}**: Decreased emphasis by {abs(change['pct_change']):.0f}% (from {change['previous_score']:.1f} to {change['current_score']:.1f})")
                else:
                    st.info("No significant topic emphasis changes detected between calls.")
    
    # Comparative Language Tab
    with tabs[2]:
        # Analyze comparative language
        comparative_language = analyze_comparative_language(cleaned_content)
        
        with card("Comparative Language Analysis"):
            st.markdown(f"**Total comparative references:** {comparative_language['total_count']}")
            st.markdown(f"**Comparative language score:** {comparative_language['comparative_score']:.1f}")
            
            # Create visualization of categories
            categories = list(comparative_language['categories'].keys())
            counts = [comparative_language['categories'][cat]['count'] for cat in categories]
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=categories,
                y=counts,
                marker_color=['#2196F3', '#4CAF50', '#FF9800', '#9C27B0'],
                text=counts,
                textposition='auto'
            ))
            
            fig.update_layout(
                title="Comparative Language Categories",
                xaxis_title="Category",
                yaxis_title="Count",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(30,30,30,0.3)',
                font=dict(color='white')
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Display examples
            st.markdown("### Examples by Category")
            
            for category, data in comparative_language['categories'].items():
                if data['count'] > 0:
                    with st.expander(f"{category.capitalize()} ({data['count']} references)"):
                        for example in data['examples']:
                            st.markdown(f"- \"{example['context']}\"")
                            st.markdown(f"  *Matched term: \"{example['term']}\"*")
    
    # Management Tone Tab
    with tabs[3]:
        # Analyze management language
        management_analysis = analyze_management_language(cleaned_content)
        
        with card("Management Tone Analysis"):
            # Create tone visualization
            tone_ratio = management_analysis['tone']['tone_ratio']
            
            # Determine color based on tone
            if tone_ratio > 0.65:
                tone_color = "#4CAF50"  # Green - Positive
            elif tone_ratio > 0.45:
                tone_color = "#FFEB3B"  # Yellow - Balanced
            else:
                tone_color = "#F44336"  # Red - Cautious/Defensive
            
            # Create a gauge-like visualization
            st.markdown(f"""
            <div style="text-align: center;">
                <h3>Management Tone</h3>
                <div style="position: relative; width: 200px; height: 100px; margin: 0 auto; overflow: hidden;">
                    <svg width="200" height="100" viewBox="0 0 200 100">
                        <path d="M20,80 A80,80 0 0,1 180,80" fill="none" stroke="#333333" stroke-width="15" />
                        <path d="M20,80 A80,80 0 0,1 180,80" fill="none" stroke="{tone_color}" stroke-width="15"
                               stroke-dasharray="251" stroke-dashoffset="{251 - (tone_ratio * 251)}" />
                        <circle cx="{20 + (160 * tone_ratio)}" cy="80" r="10" fill="white" />
                    </svg>
                </div>
                <p><strong>Tone Ratio:</strong> {tone_ratio:.2f}</p>
                <p>{management_analysis['tone']['interpretation']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Display counts
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Accomplishment terms:** {management_analysis['tone']['accomplishment_count']}")
            
            with col2:
                st.markdown(f"**Challenge terms:** {management_analysis['tone']['challenge_count']}")
            
            # Display topic scores
            st.markdown("### Topic Focus")
            
            # Convert to DataFrame for visualization
            topic_scores = management_analysis['topics']
            topic_df = pd.DataFrame({
                'Topic': [topic.capitalize() for topic in topic_scores.keys()],
                'Score': list(topic_scores.values())
            })
            
            # Sort by score
            topic_df = topic_df.sort_values('Score', ascending=False)
            
            # Create visualization
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=topic_df['Topic'],
                y=topic_df['Score'],
                marker_color='#2196F3'
            ))
            
            fig.update_layout(
                title="Management Topic Focus",
                xaxis_title="Topic",
                yaxis_title="Score",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(30,30,30,0.3)',
                font=dict(color='white')
            )
            
            st.plotly_chart(fig, use_container_width=True)

def display_qa_analysis(transcript):
    """Display analysis of the Q&A portion of the earnings call."""
    
    # Check if transcript has content
    if 'content' not in transcript or not transcript['content']:
        st.warning("This transcript does not contain any content to analyze")
        return
    
    # Get transcript content
    content = transcript['content']
    
    # Clean text for analysis
    cleaned_content = clean_text(content)
    
    # Extract Q&A section
    qa_section = extract_qa_section(cleaned_content)
    
    if not qa_section:
        st.warning("No Q&A section detected in this transcript")
        return
    
    st.markdown("## Q&A Session Analysis")
    
    # Extract questions and answers
    questions = extract_questions(qa_section)
    answers = extract_answers(qa_section)
    
    # Basic statistics
    with card("Q&A Overview"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Questions", len(questions))
        
        with col2:
            st.metric("Answers", len(answers))
        
        with col3:
            avg_question_length = sum(len(q.split()) for q in questions) / len(questions) if questions else 0
            st.metric("Avg. Question Length", f"{avg_question_length:.0f} words")
    
    # Categorize analyst questions
    categorized_questions = categorize_analyst_questions(qa_section)
    
    # Question topics
    with card("Analyst Question Topics"):
        # Aggregate topic frequencies
        topic_counts = {}
        
        for question in categorized_questions:
            for topic, score in question['topics']:
                topic_name = topic
                if topic_name in topic_counts:
                    topic_counts[topic_name] += 1
                else:
                    topic_counts[topic_name] = 1
        
        # Convert to DataFrame for visualization
        topic_df = pd.DataFrame({
            'Topic': [topic.capitalize() for topic in topic_counts.keys()],
            'Count': list(topic_counts.values())
        })
        
        # Sort by count
        topic_df = topic_df.sort_values('Count', ascending=False)
        
        # Create visualization
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=topic_df['Topic'],
            y=topic_df['Count'],
            marker_color='#2196F3',
            text=topic_df['Count'],
            textposition='auto'
        ))
        
        fig.update_layout(
            title="Analyst Question Topics",
            xaxis_title="Topic",
            yaxis_title="Number of Questions",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(30,30,30,0.3)',
            font=dict(color='white')
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Question uncertainty
    with card("Analyst Question Uncertainty"):
        # Calculate average uncertainty
        avg_uncertainty = sum(q['uncertainty_score'] for q in categorized_questions) / len(categorized_questions) if categorized_questions else 0
        
        # Determine color based on uncertainty
        if avg_uncertainty < 10:
            uncertainty_color = "#4CAF50"  # Green - Low uncertainty
        elif avg_uncertainty < 20:
            uncertainty_color = "#FFEB3B"  # Yellow - Moderate uncertainty
        else:
            uncertainty_color = "#F44336"  # Red - High uncertainty
        
        # Display average uncertainty
        st.markdown(f"""
        <div style="text-align: center;">
            <h3>Average Question Uncertainty</h3>
            <div style="position: relative; width: 150px; height: 150px; margin: 0 auto;">
                <svg width="150" height="150" viewBox="0 0 150 150">
                    <circle cx="75" cy="75" r="65" fill="none" stroke="#333333" stroke-width="15" />
                    <circle cx="75" cy="75" r="65" fill="none" stroke="{uncertainty_color}" stroke-width="15"
                            stroke-dasharray="409" stroke-dashoffset="{409 - (min(avg_uncertainty, 50) / 50 * 409)}"
                            transform="rotate(-90 75 75)" />
                    <text x="75" y="85" text-anchor="middle" font-size="30" fill="white">{min(int(avg_uncertainty), 50)}</text>
                </svg>
            </div>
            <p>Average uncertainty score: {avg_uncertainty:.1f}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Create distribution of uncertainty scores
        uncertainty_scores = [q['uncertainty_score'] for q in categorized_questions]
        
        fig = go.Figure()
        
        fig.add_trace(go.Histogram(
            x=uncertainty_scores,
            marker_color='#2196F3',
            nbinsx=10
        ))
        
        fig.update_layout(
            title="Distribution of Question Uncertainty Scores",
            xaxis_title="Uncertainty Score",
            yaxis_title="Number of Questions",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(30,30,30,0.3)',
            font=dict(color='white')
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Display individual questions
    with card("Individual Questions"):
        # Sort questions by uncertainty (high to low)
        sorted_questions = sorted(categorized_questions, key=lambda q: q['uncertainty_score'], reverse=True)
        
        # Create tabs for different sorting options
        tabs = st.tabs(["By Uncertainty", "By Topic", "By Length"])
        
        # By Uncertainty tab
        with tabs[0]:
            for i, question in enumerate(sorted_questions):
                # Determine color based on uncertainty
                if question['uncertainty_score'] < 10:
                    q_color = "#4CAF50"  # Green - Low uncertainty
                elif question['uncertainty_score'] < 20:
                    q_color = "#FFEB3B"  # Yellow - Moderate uncertainty
                else:
                    q_color = "#F44336"  # Red - High uncertainty
                
                with st.expander(f"Q{i+1}: Uncertainty Score {question['uncertainty_score']:.1f}"):
                    # Show question text
                    st.markdown(f"**Question:** {question['text']}")
                    
                    # Show topics
                    st.markdown("**Topics:**")
                    for topic, score in question['topics']:
                        st.markdown(f"- {topic.capitalize()}: {score:.1f}")
                    
                    # Show uncertainty level
                    st.markdown(f"**Uncertainty Level:** <span style='color:{q_color};'>{question['uncertainty_score']:.1f}</span>", unsafe_allow_html=True)
                    
                    # Show length
                    st.markdown(f"**Length:** {question['length']} words")
        
        # By Topic tab
        with tabs[1]:
            # Group questions by primary topic
            topic_groups = {}
            
            for question in categorized_questions:
                if question['topics']:
                    primary_topic = question['topics'][0][0]  # First topic in the list
                    
                    if primary_topic in topic_groups:
                        topic_groups[primary_topic].append(question)
                    else:
                        topic_groups[primary_topic] = [question]
            
            # Display questions by topic
            for topic, questions in topic_groups.items():
                st.markdown(f"### {topic.capitalize()} ({len(questions)} questions)")
                
                for i, question in enumerate(questions):
                    with st.expander(f"Q{i+1}: {question['text'][:100]}..."):
                        # Show question text
                        st.markdown(f"**Question:** {question['text']}")
                        
                        # Show uncertainty level
                        if question['uncertainty_score'] < 10:
                            q_color = "#4CAF50"  # Green - Low uncertainty
                        elif question['uncertainty_score'] < 20:
                            q_color = "#FFEB3B"  # Yellow - Moderate uncertainty
                        else:
                            q_color = "#F44336"  # Red - High uncertainty
                        
                        st.markdown(f"**Uncertainty Level:** <span style='color:{q_color};'>{question['uncertainty_score']:.1f}</span>", unsafe_allow_html=True)
                        
                        # Show length
                        st.markdown(f"**Length:** {question['length']} words")
        
        # By Length tab
        with tabs[2]:
            # Sort by length
            length_sorted = sorted(categorized_questions, key=lambda q: q['length'], reverse=True)
            
            for i, question in enumerate(length_sorted):
                with st.expander(f"Q{i+1}: {question['length']} words"):
                    # Show question text
                    st.markdown(f"**Question:** {question['text']}")
                    
                    # Show topics
                    st.markdown("**Topics:**")
                    for topic, score in question['topics']:
                        st.markdown(f"- {topic.capitalize()}: {score:.1f}")
                    
                    # Show uncertainty level
                    if question['uncertainty_score'] < 10:
                        q_color = "#4CAF50"  # Green - Low uncertainty
                    elif question['uncertainty_score'] < 20:
                        q_color = "#FFEB3B"  # Yellow - Moderate uncertainty
                    else:
                        q_color = "#F44336"  # Red - High uncertainty
                    
                    st.markdown(f"**Uncertainty Level:** <span style='color:{q_color};'>{question['uncertainty_score']:.1f}</span>", unsafe_allow_html=True)

def display_signal_detection(transcript, previous_transcript=None):
    """Display signal detection analysis of earnings call transcript."""
    
    # Check if transcript has content
    if 'content' not in transcript or not transcript['content']:
        st.warning("This transcript does not contain any content to analyze")
        return
    
    # Get transcript content
    content = transcript['content']
    
    # Clean text for analysis
    cleaned_content = clean_text(content)
    
    st.markdown("## Signal Detection Analysis")
    
    # Detect warning and opportunity signals
    with neon_spinner("Detecting signals..."):
        previous_content = previous_transcript['content'] if previous_transcript is not None else None
        warning_signals = detect_warning_signals(cleaned_content, previous_content)
        
        previous_content = previous_transcript['content'] if previous_transcript is not None else None
        opportunity_signals = detect_opportunity_signals(cleaned_content, previous_content)
    
    # Create tabs for different signal types
    tabs = st.tabs(["Warning Signals", "Opportunity Signals", "Guidance Analysis", "Signal Timeline"])
    
    # Warning Signals tab
    with tabs[0]:
        if warning_signals:
            with card("Detected Warning Signals"):
                # Create visualization of severity
                high_severity = sum(1 for signal in warning_signals if signal['severity'] == 'high')
                medium_severity = sum(1 for signal in warning_signals if signal['severity'] == 'medium')
                
                # Create pie chart
                fig = go.Figure()
                
                fig.add_trace(go.Pie(
                    labels=['High Severity', 'Medium Severity'],
                    values=[high_severity, medium_severity],
                    marker=dict(colors=['#F44336', '#FF9800'])
                ))
                
                fig.update_layout(
                    title="Warning Signal Severity",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(30,30,30,0.3)',
                    font=dict(color='white')
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Display individual signals
                for i, signal in enumerate(warning_signals):
                    severity_color = "#F44336" if signal['severity'] == 'high' else "#FF9800"
                    
                    with st.expander(f"Warning {i+1}: {signal['type']} ({signal['severity'].capitalize()} Severity)"):
                        st.markdown(f"**<span style='color:{severity_color};'>{signal['description']}</span>**", unsafe_allow_html=True)
                        
                        if signal['evidence']:
                            st.markdown("**Evidence:**")
                            for evidence in signal['evidence']:
                                st.markdown(f"- {evidence}")
        else:
            st.info("No significant warning signals detected in this transcript.")
    
    # Opportunity Signals tab
    with tabs[1]:
        if opportunity_signals:
            with card("Detected Opportunity Signals"):
                # Create visualization of strength
                high_strength = sum(1 for signal in opportunity_signals if signal['strength'] == 'high')
                medium_strength = sum(1 for signal in opportunity_signals if signal['strength'] == 'medium')
                
                # Create pie chart
                fig = go.Figure()
                
                fig.add_trace(go.Pie(
                    labels=['High Strength', 'Medium Strength'],
                    values=[high_strength, medium_strength],
                    marker=dict(colors=['#4CAF50', '#8BC34A'])
                ))
                
                fig.update_layout(
                    title="Opportunity Signal Strength",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(30,30,30,0.3)',
                    font=dict(color='white')
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Display individual signals
                for i, signal in enumerate(opportunity_signals):
                    strength_color = "#4CAF50" if signal['strength'] == 'high' else "#8BC34A"
                    
                    with st.expander(f"Opportunity {i+1}: {signal['type']} ({signal['strength'].capitalize()} Strength)"):
                        st.markdown(f"**<span style='color:{strength_color};'>{signal['description']}</span>**", unsafe_allow_html=True)
                        
                        if signal['evidence']:
                            st.markdown("**Evidence:**")
                            for evidence in signal['evidence']:
                                st.markdown(f"- {evidence}")
        else:
            st.info("No significant opportunity signals detected in this transcript.")
    
    # Guidance Analysis tab
    with tabs[2]:
        guidance_statements = extract_guidance(cleaned_content)
        
        if guidance_statements:
            with card("Forward-Looking Statements Analysis"):
                # Analyze sentiment of guidance statements
                positive_guidance = 0
                negative_guidance = 0
                neutral_guidance = 0
                
                # Simple keyword-based sentiment analysis
                positive_words = ['increase', 'higher', 'growth', 'improve', 'better', 'exceed', 'above', 'strong', 'opportunity']
                negative_words = ['decrease', 'lower', 'decline', 'reduce', 'worse', 'below', 'challenge', 'headwind', 'risk']
                
                for statement in guidance_statements:
                    statement_text = statement['statement'].lower()
                    positive_count = sum(statement_text.count(word) for word in positive_words)
                    negative_count = sum(statement_text.count(word) for word in negative_words)
                    
                    if positive_count > negative_count:
                        positive_guidance += 1
                    elif negative_count > positive_count:
                        negative_guidance += 1
                    else:
                        neutral_guidance += 1
                
                # Create sentiment visualization
                fig = go.Figure()
                
                fig.add_trace(go.Pie(
                    labels=['Positive', 'Neutral', 'Negative'],
                    values=[positive_guidance, neutral_guidance, negative_guidance],
                    marker=dict(colors=['#4CAF50', '#9E9E9E', '#F44336'])
                ))
                
                fig.update_layout(
                    title="Guidance Statement Sentiment",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(30,30,30,0.3)',
                    font=dict(color='white')
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Group statements by trigger phrase
                triggers = {}
                
                for statement in guidance_statements:
                    trigger = statement['trigger_phrase']
                    
                    if trigger in triggers:
                        triggers[trigger].append(statement)
                    else:
                        triggers[trigger] = [statement]
                
                # Display statements by trigger
                st.markdown("### Forward-Looking Statements by Trigger")
                
                for trigger, statements in triggers.items():
                    with st.expander(f"{trigger.capitalize()} ({len(statements)} statements)"):
                        for i, statement in enumerate(statements):
                            st.markdown(f"{i+1}. \"{statement['statement']}\"")
        else:
            st.warning("No clear forward-looking statements detected in this transcript.")
    
    # Signal Timeline tab
    with tabs[3]:
        with card("Signal Timeline"):
            st.markdown("### Timeline of Detected Signals")
            
            # Create a simple timeline visualization
            all_signals = []
            
            for signal in warning_signals:
                all_signals.append({
                    'type': signal['type'],
                    'description': signal['description'],
                    'strength': 'warning',
                    'severity': signal['severity']
                })
            
            for signal in opportunity_signals:
                all_signals.append({
                    'type': signal['type'],
                    'description': signal['description'],
                    'strength': 'opportunity',
                    'severity': signal['strength']
                })
            
            if all_signals:
                # Create a timeline-like visualization
                for i, signal in enumerate(all_signals):
                    # Determine color based on signal type
                    if signal['strength'] == 'warning':
                        bg_color = "#F44336" if signal['severity'] == 'high' else "#FF9800"
                        icon = "⚠️"
                    else:  # opportunity
                        bg_color = "#4CAF50" if signal['severity'] == 'high' else "#8BC34A"
                        icon = "🚀"
                    
                    # Create a timeline item
                    st.markdown(f"""
                    <div style="display: flex; margin-bottom: 15px;">
                        <div style="width: 40px; height: 40px; border-radius: 50%; background-color: {bg_color}; 
                                    display: flex; align-items: center; justify-content: center; margin-right: 15px;">
                            <span style="font-size: 20px;">{icon}</span>
                        </div>
                        <div style="flex-grow: 1; background-color: rgba(30, 30, 30, 0.7); padding: 10px; border-radius: 5px;">
                            <strong>{signal['type'].replace('_', ' ').title()}</strong><br>
                            {signal['description']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No significant signals detected in this transcript.")

def display_full_transcript(transcript):
    """Display the full transcript with highlighting options."""
    
    # Check if transcript has content
    if 'content' not in transcript or not transcript['content']:
        st.warning("This transcript does not contain any content to analyze")
        return
    
    # Get transcript content
    content = transcript['content']
    
    st.markdown("## Full Transcript")
    
    # Add search functionality
    search_query = search_box("Search in transcript", key="transcript_search")
    
    # Metadata display
    with card("Transcript Information"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'quarter' in transcript and 'year' in transcript:
                st.markdown(f"**Quarter:** Q{transcript['quarter']} {transcript['year']}")
            
        with col2:
            if 'date' in transcript:
                date_str = transcript['date'].strftime('%Y-%m-%d') if hasattr(transcript['date'], 'strftime') else transcript['date']
                st.markdown(f"**Date:** {date_str}")
        
        with col3:
            if 'ticker' in transcript:
                st.markdown(f"**Ticker:** {transcript['ticker']}")
    
    # Display options
    display_option = st.radio("Display Options", ["Full Transcript", "Presentation", "Q&A"], horizontal=True)
    
    # Clean text and extract sections
    cleaned_content = clean_text(content)
    qa_section = extract_qa_section(cleaned_content)
    presentation_section = cleaned_content.replace(qa_section, "").strip() if qa_section else cleaned_content
    
    # Apply highlighting based on search query
    if search_query:
        count = content.lower().count(search_query.lower())
        st.markdown(f"**Found {count} occurrences of '{search_query}'**")
        
        # Create highlighted text
        def highlight_text(text, query):
            pattern = re.compile(f"({re.escape(query)})", re.IGNORECASE)
            highlighted = pattern.sub(r"<span style='background-color: yellow; color: black;'>\1</span>", text)
            return highlighted
        
        # Apply highlighting to the selected section
        if display_option == "Full Transcript":
            display_text = highlight_text(content, search_query)
        elif display_option == "Presentation":
            display_text = highlight_text(presentation_section, search_query)
        else:  # Q&A
            if qa_section:
                display_text = highlight_text(qa_section, search_query)
            else:
                st.warning("No Q&A section detected in this transcript")
                display_text = ""
    else:
        # Display without highlighting
        if display_option == "Full Transcript":
            display_text = content
        elif display_option == "Presentation":
            display_text = presentation_section
        else:  # Q&A
            if qa_section:
                display_text = qa_section
            else:
                st.warning("No Q&A section detected in this transcript")
                display_text = ""
    
    # Display text with formatting
    with card("Transcript Text"):
        st.markdown(f"<div style='height: 500px; overflow-y: scroll; white-space: pre-wrap;'>{display_text}</div>", unsafe_allow_html=True)

# Run the main function
if __name__ == "__main__":
    earnings_call_explorer()