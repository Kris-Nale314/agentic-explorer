"""
Company Comparison for the Agentic Explorer platform.

This page allows for side-by-side comparison of multiple companies across key
financial metrics, including ratios, growth rates, and financial health.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import os
import json

# Import our custom components
from utils.components.layout import page_container, card, two_column_layout, metrics_row
from utils.components.charts import line_chart, bar_chart, radar_chart
from utils.components.data_display import styled_dataframe, metric_card
from utils.components.interactive import styled_date_selector, segmented_control
from utils.components.loaders import neon_spinner
from utils.components.themes import apply_theme, color, get_chart_colors

# Import financial assessment tools
from core.tools.finAssess import (
    prepare_financial_data,
    get_statement_data,
    calculate_financial_ratios,
    calculate_growth_rates,
    evaluate_ratio,
    determine_ratio_trend,
    calculate_financial_health_score,
    detect_financial_anomalies,
    analyze_trend_direction,
    format_large_number,
    compare_companies,
    rank_companies,
    calculate_industry_metrics
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
            return json.load(f)
    return None

def load_company_financials(ticker):
    """Load company financial data for a given ticker."""
    financials_path = get_datastore_path() / "companies" / ticker / "financials.parquet"
    if financials_path.exists():
        return pd.read_parquet(financials_path)
    return None

def company_comparison():
    """Main function for the Company Comparison page."""
    
    # Create page container with title
    with page_container("Company Comparison", "Compare financial metrics across multiple companies"):
        # Get available tickers
        available_tickers = get_available_tickers()
        
        if not available_tickers:
            st.warning("No company data found in the dataStore. Please run the data collector first.")
            st.code("python -m utils.run_data_collector --tickers DELL,NVDA,TSLA,ACN --years 3", language="bash")
            return
        
        # Create sidebar for company selection
        st.sidebar.header("Company Selection")
        
        # Multi-company selector (limit to 5 companies)
        selected_tickers = st.sidebar.multiselect(
            "Select Companies (max 5)",
            available_tickers,
            default=[available_tickers[0]] if available_tickers else []
        )
        
        # Enforce limit of 5 companies
        if len(selected_tickers) > 5:
            st.sidebar.warning("Maximum of 5 companies allowed. Only the first 5 will be used.")
            selected_tickers = selected_tickers[:5]
        
        # Period type selector
        period_type = st.sidebar.radio(
            "Period Type",
            ["quarterly", "annual"],
            index=0
        )
        
        # Comparison type selector
        comparison_view = st.sidebar.radio(
            "Comparison View",
            ["Financial Health", "Profitability", "Growth", "Valuation", "Solvency"],
            index=0
        )
        
        # Process company data
        if selected_tickers:
            # Load company data
            company_data = {}
            company_profiles = {}
            company_financials = {}
            company_ratios = {}
            
            # Show loading indicator while collecting data
            loading_spinner = st.spinner("Loading company data...")
            with loading_spinner:
                for ticker in selected_tickers:
                    # Load profile
                    profile = load_company_profile(ticker)
                    if profile:
                        company_profiles[ticker] = profile
                    
                    # Load financials
                    financials = load_company_financials(ticker)
                    if financials is not None and not financials.empty:
                        # Clean financial data
                        financials = prepare_financial_data(financials)
                        company_financials[ticker] = financials
                        
                        # Calculate ratios
                        ratios = calculate_financial_ratios(financials, "Income Statement", period_type)
                        if not ratios.empty:
                            company_ratios[ticker] = ratios
            
            # Display selected companies
            st.subheader("Selected Companies")
            
            # Create company profile cards
            company_cols = st.columns(len(selected_tickers))
            
            for i, ticker in enumerate(selected_tickers):
                with company_cols[i]:
                    with card(f"{ticker}"):
                        if ticker in company_profiles:
                            profile = company_profiles[ticker]
                            
                            # Show company logo if available
                            if "image" in profile and profile["image"]:
                                st.image(profile["image"], width=80)
                            
                            # Show company name
                            company_name = profile.get("companyName", ticker)
                            st.markdown(f"**{company_name}**")
                            
                            # Show industry
                            st.caption(f"Industry: {profile.get('industry', 'N/A')}")
                            
                            # Show financial health score if available
                            if ticker in company_ratios:
                                ratios_df = company_ratios[ticker]
                                if not ratios_df.empty:
                                    score, category = calculate_financial_health_score(ratios_df)
                                    
                                    # Determine color based on score
                                    if score >= 80:
                                        color = "#4CAF50"  # Green
                                    elif score >= 60:
                                        color = "#8BC34A"  # Light green
                                    elif score >= 40:
                                        color = "#FFEB3B"  # Yellow
                                    elif score >= 20:
                                        color = "#FF9800"  # Orange
                                    else:
                                        color = "#F44336"  # Red
                                    
                                    # Show score with color
                                    st.markdown(f"Health Score: <span style='color:{color};font-weight:bold;'>{int(score)}</span> ({category})", 
                                               unsafe_allow_html=True)
                        else:
                            st.markdown(f"**{ticker}**")
                            st.caption("Profile data not available")
            
            # Display comparative analysis based on selected view
            if comparison_view == "Financial Health":
                display_financial_health_comparison(company_ratios, company_financials)
            elif comparison_view == "Profitability":
                display_profitability_comparison(company_ratios, company_financials, period_type)
            elif comparison_view == "Growth":
                display_growth_comparison(company_financials, period_type)
            elif comparison_view == "Valuation":
                display_valuation_comparison(company_profiles, company_financials, company_ratios)
            elif comparison_view == "Solvency":
                display_solvency_comparison(company_ratios, company_financials)
        else:
            st.info("Please select at least one company to begin comparison")

def display_financial_health_comparison(company_ratios, company_financials):
    """Display financial health comparison across companies."""
    
    st.markdown("## Financial Health Comparison")
    
    # Check if we have ratio data
    if not company_ratios:
        st.warning("Insufficient ratio data available for comparison")
        return
    
    # Calculate health scores for all companies
    health_scores = {}
    for ticker, ratios_df in company_ratios.items():
        if not ratios_df.empty:
            score, category = calculate_financial_health_score(ratios_df)
            health_scores[ticker] = {
                'score': score,
                'category': category
            }
    
    # Display financial health score comparison
    with card("Financial Health Score Comparison"):
        # Sort companies by health score (highest first)
        sorted_companies = sorted(health_scores.items(), key=lambda x: x[1]['score'], reverse=True)
        
        # Create health score chart
        fig = go.Figure()
        
        # Add bars for each company
        companies = []
        scores = []
        colors = []
        categories = []
        
        for ticker, data in sorted_companies:
            companies.append(ticker)
            scores.append(data['score'])
            categories.append(data['category'])
            
            # Determine color based on score
            if data['score'] >= 80:
                colors.append("#4CAF50")  # Green
            elif data['score'] >= 60:
                colors.append("#8BC34A")  # Light green
            elif data['score'] >= 40:
                colors.append("#FFEB3B")  # Yellow
            elif data['score'] >= 20:
                colors.append("#FF9800")  # Orange
            else:
                colors.append("#F44336")  # Red
        
        # Add bars
        fig.add_trace(go.Bar(
            x=companies,
            y=scores,
            marker_color=colors,
            text=categories,
            textposition='auto'
        ))
        
        # Update layout
        fig.update_layout(
            title="Financial Health Score by Company",
            xaxis_title="Company",
            yaxis_title="Health Score (0-100)",
            yaxis=dict(range=[0, 100]),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(30,30,30,0.3)',
            font=dict(color='white')
        )
        
        # Add reference lines for score categories
        fig.add_shape(
            type="line",
            x0=-0.5,
            y0=80,
            x1=len(companies) - 0.5,
            y1=80,
            line=dict(color="#4CAF50", width=2, dash="dash"),
        )
        
        fig.add_shape(
            type="line",
            x0=-0.5,
            y0=60,
            x1=len(companies) - 0.5,
            y1=60,
            line=dict(color="#8BC34A", width=2, dash="dash"),
        )
        
        fig.add_shape(
            type="line",
            x0=-0.5,
            y0=40,
            x1=len(companies) - 0.5,
            y1=40,
            line=dict(color="#FFEB3B", width=2, dash="dash"),
        )
        
        fig.add_shape(
            type="line",
            x0=-0.5,
            y0=20,
            x1=len(companies) - 0.5,
            y1=20,
            line=dict(color="#FF9800", width=2, dash="dash"),
        )
        
        # Add score category annotations
        fig.add_annotation(
            x=len(companies) - 0.5,
            y=90,
            text="Strong",
            showarrow=False,
            xshift=50,
            font=dict(color="#4CAF50")
        )
        
        fig.add_annotation(
            x=len(companies) - 0.5,
            y=70,
            text="Healthy",
            showarrow=False,
            xshift=50,
            font=dict(color="#8BC34A")
        )
        
        fig.add_annotation(
            x=len(companies) - 0.5,
            y=50,
            text="Adequate",
            showarrow=False,
            xshift=50,
            font=dict(color="#FFEB3B")
        )
        
        fig.add_annotation(
            x=len(companies) - 0.5,
            y=30,
            text="Vulnerable",
            showarrow=False,
            xshift=50,
            font=dict(color="#FF9800")
        )
        
        fig.add_annotation(
            x=len(companies) - 0.5,
            y=10,
            text="Distressed",
            showarrow=False,
            xshift=50,
            font=dict(color="#F44336")
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Display key ratio comparison
    with card("Key Financial Ratios Comparison"):
        # Determine which ratios we have for each company
        key_ratios = [
            'gross_margin',
            'operating_margin', 
            'net_margin',
            'current_ratio',
            'debt_to_equity',
            'asset_turnover'
        ]
        
        ratio_display_names = {
            'gross_margin': 'Gross Margin',
            'operating_margin': 'Operating Margin',
            'net_margin': 'Net Margin',
            'current_ratio': 'Current Ratio',
            'debt_to_equity': 'Debt-to-Equity',
            'asset_turnover': 'Asset Turnover'
        }
        
        # Create radar chart data
        radar_data = pd.DataFrame()
        
        for ticker, ratios_df in company_ratios.items():
            if not ratios_df.empty:
                # Get most recent ratios
                latest_ratios = ratios_df.iloc[0].copy()
                
                # Normalize ratio values for radar chart (0-1 scale)
                normalized_ratios = {}
                
                for ratio in key_ratios:
                    if ratio in latest_ratios:
                        value = latest_ratios[ratio]
                        
                        if not pd.isna(value) and np.isfinite(value):
                            # Check if higher is better for this ratio
                            if ratio in ['debt_to_equity']:
                                # For debt_to_equity, lower is better (invert the scale)
                                normalized_ratios[ratio_display_names[ratio]] = max(0, min(1, 1 - value / 3))
                            else:
                                # For other ratios, higher is better
                                if ratio == 'current_ratio':
                                    normalized_ratios[ratio_display_names[ratio]] = max(0, min(1, value / 3))
                                elif ratio == 'asset_turnover':
                                    normalized_ratios[ratio_display_names[ratio]] = max(0, min(1, value / 1.5))
                                else:  # Margin ratios
                                    normalized_ratios[ratio_display_names[ratio]] = max(0, min(1, value / 0.4))
                
                # Add to radar data
                normalized_ratios['Company'] = ticker
                radar_data = pd.concat([radar_data, pd.DataFrame([normalized_ratios])], ignore_index=True)
        
        if not radar_data.empty:
            # Create radar chart
            fig = go.Figure()
            
            # Prepare data for radar chart
            categories = [col for col in radar_data.columns if col != 'Company']
            
            # Add a trace for each company
            for _, row in radar_data.iterrows():
                values = [row[cat] for cat in categories]
                # Add the first value again to close the loop
                values.append(values[0])
                cats = categories.copy()
                cats.append(categories[0])
                
                fig.add_trace(go.Scatterpolar(
                    r=values,
                    theta=cats,
                    fill='toself',
                    name=row['Company']
                ))
            
            # Update layout
            fig.update_layout(
                title="Financial Ratio Comparison (Normalized)",
                paper_bgcolor='rgba(0,0,0,0)',
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 1]
                    ),
                    bgcolor='rgba(30,30,30,0.3)'
                ),
                font=dict(color='white')
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Add explanation
            st.markdown("""
            **Note:** The radar chart shows normalized ratio values (0-1 scale) for fair comparison:
            - For margin ratios, 1.0 represents 40% or higher
            - For current ratio, 1.0 represents 3.0 or higher
            - For debt-to-equity, the scale is inverted (lower is better), with 1.0 representing 0.0
            - For asset turnover, 1.0 represents 1.5 or higher
            """)
            
            # Add detailed ratio comparison table
            st.markdown("### Detailed Ratio Comparison")
            
            # Create ratio comparison table
            comparison_data = []
            
            for ratio in key_ratios:
                ratio_name = ratio_display_names[ratio]
                row_data = {'Ratio': ratio_name}
                
                # Determine if higher is better for this ratio
                higher_is_better = ratio != 'debt_to_equity'
                
                for ticker, ratios_df in company_ratios.items():
                    if not ratios_df.empty and ratio in ratios_df.columns:
                        value = ratios_df[ratio].iloc[0]
                        
                        if not pd.isna(value) and np.isfinite(value):
                            # Get evaluation
                            indicator, _, _ = evaluate_ratio(ratio, value)
                            
                            # Format value
                            if ratio in ['gross_margin', 'operating_margin', 'net_margin']:
                                formatted_value = f"{value:.1%}"
                            else:
                                formatted_value = f"{value:.2f}"
                            
                            row_data[ticker] = f"{indicator} {formatted_value}"
                        else:
                            row_data[ticker] = "N/A"
                
                comparison_data.append(row_data)
            
            # Create DataFrame and display
            if comparison_data:
                df = pd.DataFrame(comparison_data)
                
                # Create styled HTML table
                html = "<table style='width:100%; border-collapse: collapse;'>"
                
                # Add header
                html += "<tr style='background-color:rgba(50,50,50,0.8);'>"
                html += f"<th style='text-align:left; padding:8px;'>Ratio</th>"
                
                for ticker in company_ratios.keys():
                    html += f"<th style='text-align:center; padding:8px;'>{ticker}</th>"
                
                html += "</tr>"
                
                # Add rows
                for _, row in df.iterrows():
                    html += "<tr style='border-bottom: 1px solid rgba(80,80,80,0.5);'>"
                    html += f"<td style='text-align:left; padding:8px;'>{row['Ratio']}</td>"
                    
                    for ticker in company_ratios.keys():
                        if ticker in row:
                            html += f"<td style='text-align:center; padding:8px;'>{row[ticker]}</td>"
                        else:
                            html += f"<td style='text-align:center; padding:8px;'>N/A</td>"
                    
                    html += "</tr>"
                
                # Close table
                html += "</table>"
                
                # Display the HTML table
                st.markdown(html, unsafe_allow_html=True)
            else:
                st.warning("Insufficient data for ratio comparison")
        else:
            st.warning("Insufficient ratio data for radar chart visualization")

def display_profitability_comparison(company_ratios, company_financials, period_type):
    """Display profitability comparison across companies."""
    
    st.markdown("## Profitability Comparison")
    
    # Check if we have ratio data
    if not company_ratios:
        st.warning("Insufficient ratio data available for comparison")
        return
    
    # Create two-column layout
    left_col, right_col = st.columns([2, 1])
    
    with left_col:
        # Margin trends comparison
        with card("Margin Trends Comparison"):
            # Create tabs for different margin types
            margin_tabs = st.tabs(["Gross Margin", "Operating Margin", "Net Margin"])
            
            # Gross Margin Tab
            with margin_tabs[0]:
                display_margin_comparison(company_ratios, 'gross_margin', 'Gross Margin')
            
            # Operating Margin Tab
            with margin_tabs[1]:
                display_margin_comparison(company_ratios, 'operating_margin', 'Operating Margin')
            
            # Net Margin Tab
            with margin_tabs[2]:
                display_margin_comparison(company_ratios, 'net_margin', 'Net Margin')
    
    with right_col:
        # Profitability rankings
        with card("Profitability Rankings"):
            # Rank companies by each profitability ratio
            display_ratio_rankings(company_ratios, [
                {'name': 'gross_margin', 'display': 'Gross Margin'},
                {'name': 'operating_margin', 'display': 'Operating Margin'},
                {'name': 'net_margin', 'display': 'Net Margin'}
            ])
    
    # Revenue and profitability comparison
    with card("Revenue & Profit Comparison"):
        # Get the most recent income statement data for each company
        income_data = {}
        
        for ticker, financials in company_financials.items():
            if financials is not None and not financials.empty:
                # Get income statement data
                income_stmt = get_statement_data(financials, 'Income Statement', period_type).head(1)
                
                if not income_stmt.empty:
                    income_data[ticker] = income_stmt
        
        if income_data:
            # Create bar chart for revenue, gross profit, and net income
            metrics = [
                {'name': 'revenue', 'display': 'Revenue'},
                {'name': 'grossProfit', 'display': 'Gross Profit'},
                {'name': 'netIncome', 'display': 'Net Income'}
            ]
            
            # Create figure
            fig = go.Figure()
            
            # Add grouped bars for each company
            for i, metric in enumerate(metrics):
                values = []
                labels = []
                
                for ticker, data in income_data.items():
                    if metric['name'] in data.columns:
                        value = data[metric['name']].iloc[0]
                        
                        if not pd.isna(value) and np.isfinite(value):
                            values.append(value)
                            labels.append(ticker)
                
                if values:
                    fig.add_trace(go.Bar(
                        x=labels,
                        y=values,
                        name=metric['display'],
                        marker_color=get_chart_colors('categorical')[i]
                    ))
            
            # Update layout
            fig.update_layout(
                title="Latest Revenue & Profit Metrics",
                xaxis_title="Company",
                yaxis_title="Amount",
                barmode='group',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(30,30,30,0.3)',
                font=dict(color='white')
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Add revenue and profit table with absolute values
            table_data = []
            
            for ticker, data in income_data.items():
                row = {'Company': ticker}
                
                for metric in metrics:
                    if metric['name'] in data.columns:
                        value = data[metric['name']].iloc[0]
                        
                        if not pd.isna(value) and np.isfinite(value):
                            row[metric['display']] = format_large_number(value)
                        else:
                            row[metric['display']] = 'N/A'
                    else:
                        row[metric['display']] = 'N/A'
                
                table_data.append(row)
            
            if table_data:
                # Display as a DataFrame
                df = pd.DataFrame(table_data)
                styled_dataframe(df)
        else:
            st.warning("Insufficient income statement data for comparison")

def display_margin_comparison(company_ratios, margin_type, margin_display):
    """Display comparison for a specific margin type."""
    
    # Extract margin data for each company
    margin_data = {}
    
    for ticker, ratios_df in company_ratios.items():
        if not ratios_df.empty and margin_type in ratios_df.columns:
            # Sort by date (ascending)
            sorted_df = ratios_df.sort_values('date')
            
            # Extract margin values
            if not sorted_df[margin_type].isnull().all():
                margin_data[ticker] = {
                    'dates': sorted_df['date'].tolist(),
                    'values': sorted_df[margin_type].tolist()
                }
    
    if margin_data:
        # Create line chart comparing margins
        fig = go.Figure()
        
        # Add a line for each company
        colors = get_chart_colors('categorical', len(margin_data))
        
        for i, (ticker, data) in enumerate(margin_data.items()):
            fig.add_trace(go.Scatter(
                x=data['dates'],
                y=data['values'],
                name=ticker,
                line=dict(color=colors[i], width=2),
                mode='lines+markers'
            ))
        
        # Update layout
        fig.update_layout(
            title=f"{margin_display} Comparison",
            xaxis_title="Period",
            yaxis_title=margin_display,
            yaxis=dict(tickformat=".0%"),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(30,30,30,0.3)',
            font=dict(color='white'),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=1.2,
                xanchor="center",
                x=0.5
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Add a table with the most recent margins
        latest_margins = []
        
        for ticker, data in margin_data.items():
            if data['values']:
                latest_margins.append({
                    'Company': ticker,
                    margin_display: f"{data['values'][-1]:.1%}",
                    'Raw Value': data['values'][-1]
                })
        
        if latest_margins:
            # Sort by margin value (highest first)
            latest_margins.sort(key=lambda x: x['Raw Value'], reverse=True)
            
            # Display as a table (without the raw value column)
            df = pd.DataFrame(latest_margins)[['Company', margin_display]]
            styled_dataframe(df)
    else:
        st.warning(f"Insufficient {margin_display.lower()} data for comparison")

def display_ratio_rankings(company_ratios, ratios_to_rank):
    """Display ranking table for specified ratios."""
    
    # Create ranking table for each ratio
    for ratio_info in ratios_to_rank:
        ratio_name = ratio_info['name']
        ratio_display = ratio_info['display']
        
        # Get the most recent value for each company
        rankings = []
        
        for ticker, ratios_df in company_ratios.items():
            if not ratios_df.empty and ratio_name in ratios_df.columns:
                value = ratios_df[ratio_name].iloc[0]
                
                if not pd.isna(value) and np.isfinite(value):
                    indicator, status, _ = evaluate_ratio(ratio_name, value)
                    
                    rankings.append({
                        'Company': ticker,
                        'Value': value,
                        'Indicator': indicator,
                        'Status': status
                    })
        
        if rankings:
            # Sort by value (highest first for most ratios)
            rankings.sort(key=lambda x: x['Value'], reverse=True)
            
            # Add rank
            for i, item in enumerate(rankings):
                item['Rank'] = i + 1
            
            # Create styled HTML table
            html = f"<h4>{ratio_display} Ranking</h4>"
            html += "<table style='width:100%; border-collapse: collapse;'>"
            
            # Add header
            html += "<tr style='background-color:rgba(50,50,50,0.8);'>"
            html += "<th style='text-align:center; padding:8px;'>Rank</th>"
            html += "<th style='text-align:left; padding:8px;'>Company</th>"
            html += "<th style='text-align:right; padding:8px;'>Value</th>"
            html += "<th style='text-align:center; padding:8px;'>Status</th>"
            html += "</tr>"
            
            # Add rows
            for item in rankings:
                # Format value as percentage for margins
                if ratio_name in ['gross_margin', 'operating_margin', 'net_margin']:
                    formatted_value = f"{item['Value']:.1%}"
                else:
                    formatted_value = f"{item['Value']:.2f}"
                
                html += "<tr style='border-bottom: 1px solid rgba(80,80,80,0.5);'>"
                html += f"<td style='text-align:center; padding:8px;'>{item['Rank']}</td>"
                html += f"<td style='text-align:left; padding:8px;'>{item['Company']}</td>"
                html += f"<td style='text-align:right; padding:8px;'>{formatted_value}</td>"
                html += f"<td style='text-align:center; padding:8px;'>{item['Indicator']} {item['Status']}</td>"
                html += "</tr>"
            
            # Close table
            html += "</table>"
            
            # Display the HTML table
            st.markdown(html, unsafe_allow_html=True)
            
            # Add some spacing
            st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.warning(f"Insufficient data for {ratio_display} ranking")

def display_growth_comparison(company_financials, period_type):
    """Display growth rate comparison across companies."""
    
    st.markdown("## Growth Comparison")
    
    # Calculate growth rates for each company
    company_growth = {}
    
    for ticker, financials in company_financials.items():
        if financials is not None and not financials.empty:
            growth_rates = calculate_growth_rates(financials, 'Income Statement', period_type)
            
            if not growth_rates.empty:
                company_growth[ticker] = growth_rates
    
    if not company_growth:
        st.warning("Insufficient data available for growth comparison")
        return
    
    # Create tabs for different growth metrics
    growth_tabs = st.tabs(["Revenue Growth", "Profit Growth", "EPS Growth"])
    
    # Revenue Growth Tab
    with growth_tabs[0]:
        display_growth_metric_comparison(company_growth, 'revenue_growth', 'Revenue Growth')
    
    # Profit Growth Tab
    with growth_tabs[1]:
        display_growth_metric_comparison(company_growth, 'netIncome_growth', 'Net Income Growth')
    
    # EPS Growth Tab
    with growth_tabs[2]:
        display_growth_metric_comparison(company_growth, 'eps_growth', 'EPS Growth')
    
    # Average growth comparison across metrics
    with card("Average Growth Comparison"):
        # Calculate average growth for key metrics
        avg_growth = []
        
        for ticker, growth_df in company_growth.items():
            if not growth_df.empty:
                # Calculate average growth for key metrics
                metrics = {
                    'Revenue': 'revenue_growth',
                    'Gross Profit': 'grossProfit_growth',
                    'Operating Income': 'operatingIncome_growth',
                    'Net Income': 'netIncome_growth',
                    'EPS': 'eps_growth'
                }
                
                company_data = {'Company': ticker}
                has_data = False
                
                for label, metric in metrics.items():
                    if metric in growth_df.columns:
                        # Get the average of the most recent 4 periods or all available
                        recent_data = growth_df[metric].head(min(4, len(growth_df)))
                        
                        if not recent_data.empty and not recent_data.isnull().all():
                            avg = recent_data.mean()
                            company_data[label] = avg
                            has_data = True
                        else:
                            company_data[label] = None
                    else:
                        company_data[label] = None
                
                if has_data:
                    avg_growth.append(company_data)
        
        if avg_growth:
            # Create a heatmap-like table
            df = pd.DataFrame(avg_growth)
            
            # Create styled HTML table
            html = "<h4>Average Growth Rates (Recent Periods)</h4>"
            html += "<table style='width:100%; border-collapse: collapse;'>"
            
            # Add header
            html += "<tr style='background-color:rgba(50,50,50,0.8);'>"
            html += "<th style='text-align:left; padding:8px;'>Company</th>"
            
            for col in df.columns:
                if col != 'Company':
                    html += f"<th style='text-align:center; padding:8px;'>{col}</th>"
            
            html += "</tr>"
            
            # Add rows
            for _, row in df.iterrows():
                html += "<tr style='border-bottom: 1px solid rgba(80,80,80,0.5);'>"
                html += f"<td style='text-align:left; padding:8px;'>{row['Company']}</td>"
                
                for col in df.columns:
                    if col != 'Company':
                        value = row[col]
                        
                        if pd.notna(value) and np.isfinite(value):
                            # Determine color based on growth rate
                            if value >= 0.20:
                                color = "#4CAF50"  # Strong positive (green)
                            elif value >= 0.05:
                                color = "#8BC34A"  # Positive (light green)
                            elif value >= -0.05:
                                color = "#FFEB3B"  # Neutral (yellow)
                            elif value >= -0.20:
                                color = "#FF9800"  # Negative (orange)
                            else:
                                color = "#F44336"  # Strong negative (red)
                            
                            html += f"<td style='text-align:center; color:{color}; padding:8px;'>{value:.1%}</td>"
                        else:
                            html += "<td style='text-align:center; padding:8px;'>N/A</td>"
                
                html += "</tr>"
            
            # Close table
            html += "</table>"
            
            # Display the HTML table
            st.markdown(html, unsafe_allow_html=True)
        else:
            st.warning("Insufficient growth data for comparison")

def display_growth_metric_comparison(company_growth, growth_metric, display_name):
    """Display comparison for a specific growth metric."""
    
    # Extract growth data for each company
    growth_data = {}
    
    for ticker, growth_df in company_growth.items():
        if not growth_df.empty and growth_metric in growth_df.columns:
            # Sort by date (ascending)
            sorted_df = growth_df.sort_values('date')
            
            # Extract growth values
            if not sorted_df[growth_metric].isnull().all():
                growth_data[ticker] = {
                    'dates': sorted_df['date'].tolist(),
                    'values': sorted_df[growth_metric].tolist()
                }
    
    if growth_data:
        # Create two columns for chart and statistics
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Create line chart comparing growth rates
            fig = go.Figure()
            
            # Add a line for each company
            colors = get_chart_colors('categorical', len(growth_data))
            
            for i, (ticker, data) in enumerate(growth_data.items()):
                fig.add_trace(go.Scatter(
                    x=data['dates'],
                    y=data['values'],
                    name=ticker,
                    line=dict(color=colors[i], width=2),
                    mode='lines+markers'
                ))
            
            # Add zero line
            fig.add_shape(
                type="line",
                x0=min([min(data['dates']) for data in growth_data.values()]) if growth_data else 0,
                y0=0,
                x1=max([max(data['dates']) for data in growth_data.values()]) if growth_data else 1,
                y1=0,
                line=dict(color="#FFFFFF", width=1, dash="dash"),
            )
            
            # Update layout
            fig.update_layout(
                title=f"{display_name} Over Time",
                xaxis_title="Period",
                yaxis_title="Growth Rate",
                yaxis=dict(tickformat=".0%"),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(30,30,30,0.3)',
                font=dict(color='white'),
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=1.2,
                    xanchor="center",
                    x=0.5
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Add average growth rates
            st.markdown(f"### Average {display_name}")
            
            avg_growth = []
            
            for ticker, data in growth_data.items():
                if data['values']:
                    # Calculate average of last 4 values or all available
                    recent_values = data['values'][-min(4, len(data['values'])):]
                    avg = sum(recent_values) / len(recent_values)
                    
                    avg_growth.append({
                        'Company': ticker,
                        'Average': avg
                    })
            
            if avg_growth:
                # Sort by average growth (highest first)
                avg_growth.sort(key=lambda x: x['Average'], reverse=True)
                
                # Create a colored table
                html = "<table style='width:100%; border-collapse: collapse;'>"
                
                # Add header
                html += "<tr style='background-color:rgba(50,50,50,0.8);'>"
                html += "<th style='text-align:left; padding:8px;'>Company</th>"
                html += "<th style='text-align:right; padding:8px;'>Avg. Growth</th>"
                html += "</tr>"
                
                # Add rows
                for item in avg_growth:
                    # Determine color based on growth rate
                    if item['Average'] >= 0.20:
                        color = "#4CAF50"  # Strong positive (green)
                    elif item['Average'] >= 0.05:
                        color = "#8BC34A"  # Positive (light green)
                    elif item['Average'] >= -0.05:
                        color = "#FFEB3B"  # Neutral (yellow)
                    elif item['Average'] >= -0.20:
                        color = "#FF9800"  # Negative (orange)
                    else:
                        color = "#F44336"  # Strong negative (red)
                    
                    html += "<tr style='border-bottom: 1px solid rgba(80,80,80,0.5);'>"
                    html += f"<td style='text-align:left; padding:8px;'>{item['Company']}</td>"
                    html += f"<td style='text-align:right; color:{color}; padding:8px;'>{item['Average']:.1%}</td>"
                    html += "</tr>"
                
                # Close table
                html += "</table>"
                
                # Display the HTML table
                st.markdown(html, unsafe_allow_html=True)
    else:
        st.warning(f"Insufficient {display_name.lower()} data for comparison")

def display_valuation_comparison(company_profiles, company_financials, company_ratios):
    """Display valuation metric comparison across companies."""
    
    st.markdown("## Valuation Comparison")
    
    # Collect valuation metrics
    valuation_data = []
    
    for ticker, profile in company_profiles.items():
        if profile:
            item = {'Company': ticker}
            
            # Extract key valuation metrics from profile
            if 'price' in profile:
                item['Price'] = profile['price']
            
            if 'mktCap' in profile:
                item['Market Cap'] = profile['mktCap']
            
            if 'pe' in profile:
                item['P/E'] = profile['pe']
            
            if 'eps' in profile:
                item['EPS'] = profile['eps']
            
            # Calculate additional metrics if financial data is available
            if ticker in company_financials and company_financials[ticker] is not None:
                financials = company_financials[ticker]
                
                # Get latest income statement
                income_stmt = get_statement_data(financials, 'Income Statement', 'annual').head(1)
                
                if not income_stmt.empty:
                    # Revenue for P/S calculation
                    if 'revenue' in income_stmt.columns and 'mktCap' in item:
                        revenue = income_stmt['revenue'].iloc[0]
                        
                        if pd.notna(revenue) and revenue > 0:
                            item['P/S'] = item['Market Cap'] / revenue
            
            # Add to data collection if we have at least some metrics
            if len(item) > 1:  # More than just the company name
                valuation_data.append(item)
    
    if not valuation_data:
        st.warning("Insufficient data available for valuation comparison")
        return
    
    # Create two columns for different visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        # P/E Ratio Comparison
        with card("P/E Ratio Comparison"):
            pe_data = []
            
            for item in valuation_data:
                if 'P/E' in item and pd.notna(item['P/E']) and np.isfinite(item['P/E']):
                    pe_data.append({
                        'Company': item['Company'],
                        'P/E': item['P/E']
                    })
            
            if pe_data:
                # Sort by P/E (lowest first, as lower P/E might be considered better value)
                pe_data.sort(key=lambda x: x['P/E'])
                
                # Create bar chart
                fig = go.Figure()
                
                # Add bars
                fig.add_trace(go.Bar(
                    x=[item['Company'] for item in pe_data],
                    y=[item['P/E'] for item in pe_data],
                    marker_color='#2196F3'
                ))
                
                # Update layout
                fig.update_layout(
                    title="Price-to-Earnings (P/E) Ratio",
                    xaxis_title="Company",
                    yaxis_title="P/E Ratio",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(30,30,30,0.3)',
                    font=dict(color='white')
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Add context
                industry_avg = sum(item['P/E'] for item in pe_data) / len(pe_data)
                st.markdown(f"**Group Average P/E:** {industry_avg:.2f}")
            else:
                st.warning("P/E ratio data not available for comparison")
    
    with col2:
        # Market Cap Comparison
        with card("Market Capitalization"):
            mktcap_data = []
            
            for item in valuation_data:
                if 'Market Cap' in item and pd.notna(item['Market Cap']):
                    mktcap_data.append({
                        'Company': item['Company'],
                        'Market Cap': item['Market Cap']
                    })
            
            if mktcap_data:
                # Sort by market cap (highest first)
                mktcap_data.sort(key=lambda x: x['Market Cap'], reverse=True)
                
                # Create pie chart
                fig = go.Figure()
                
                fig.add_trace(go.Pie(
                    labels=[item['Company'] for item in mktcap_data],
                    values=[item['Market Cap'] for item in mktcap_data],
                    hole=0.4,
                    marker=dict(
                        colors=get_chart_colors('categorical', len(mktcap_data))
                    ),
                    textinfo='label+percent',
                    insidetextorientation='radial'
                ))
                
                # Update layout
                fig.update_layout(
                    title="Market Capitalization Comparison",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(30,30,30,0.3)',
                    font=dict(color='white')
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Add table with formatted values
                table_data = []
                
                for item in mktcap_data:
                    table_data.append({
                        'Company': item['Company'],
                        'Market Cap': format_large_number(item['Market Cap'])
                    })
                
                # Display as DataFrame
                df = pd.DataFrame(table_data)
                styled_dataframe(df)
            else:
                st.warning("Market cap data not available for comparison")
    
    # Comprehensive valuation table
    with card("Comprehensive Valuation Metrics"):
        # Create a DataFrame from the collected data
        df = pd.DataFrame(valuation_data)
        
        if not df.empty:
            # Format market cap
            if 'Market Cap' in df.columns:
                df['Market Cap'] = df['Market Cap'].apply(format_large_number)
            
            # Format other metrics
            for col in ['P/E', 'P/S']:
                if col in df.columns:
                    df[col] = df[col].apply(lambda x: f"{x:.2f}" if pd.notna(x) and np.isfinite(x) else "N/A")
            
            # Format price with two decimals
            if 'Price' in df.columns:
                df['Price'] = df['Price'].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "N/A")
            
            # Format EPS with two decimals
            if 'EPS' in df.columns:
                df['EPS'] = df['EPS'].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "N/A")
            
            # Display the DataFrame
            styled_dataframe(df)
        else:
            st.warning("Valuation metric data not available for comparison")

def display_solvency_comparison(company_ratios, company_financials):
    """Display solvency and liquidity comparison across companies."""
    
    st.markdown("## Solvency & Liquidity Comparison")
    
    # Create two columns
    col1, col2 = st.columns(2)
    
    with col1:
        # Current Ratio Comparison
        with card("Current Ratio Comparison"):
            display_ratio_comparison(company_ratios, 'current_ratio', 'Current Ratio', reference_lines=[1.0, 2.0])
    
    with col2:
        # Debt-to-Equity Comparison
        with card("Debt-to-Equity Comparison"):
            display_ratio_comparison(company_ratios, 'debt_to_equity', 'Debt-to-Equity Ratio', reference_lines=[1.0, 2.0], lower_better=True)
    
    # Balance Sheet Composition Comparison
    with card("Balance Sheet Composition"):
        # Get the latest balance sheet data for each company
        balance_data = {}
        
        for ticker, financials in company_financials.items():
            if financials is not None and not financials.empty:
                # Get balance sheet data
                balance_sheet = get_statement_data(financials, 'Balance Sheet', 'annual').head(1)
                
                if not balance_sheet.empty:
                    balance_data[ticker] = balance_sheet
        
        if balance_data:
            # Create tabs for assets and liabilities
            bs_tabs = st.tabs(["Assets", "Liabilities & Equity"])
            
            # Assets Tab
            with bs_tabs[0]:
                display_balance_sheet_comparison(balance_data, asset_side=True)
            
            # Liabilities & Equity Tab
            with bs_tabs[1]:
                display_balance_sheet_comparison(balance_data, asset_side=False)
        else:
            st.warning("Balance sheet data not available for comparison")

def display_ratio_comparison(company_ratios, ratio_name, display_name, reference_lines=None, lower_better=False):
    """Display comparison for a specific financial ratio."""
    
    # Extract ratio data for each company
    ratio_data = {}
    
    for ticker, ratios_df in company_ratios.items():
        if not ratios_df.empty and ratio_name in ratios_df.columns:
            # Sort by date (ascending)
            sorted_df = ratios_df.sort_values('date')
            
            # Extract ratio values
            if not sorted_df[ratio_name].isnull().all():
                ratio_data[ticker] = {
                    'dates': sorted_df['date'].tolist(),
                    'values': sorted_df[ratio_name].tolist()
                }
    
    if ratio_data:
        # Create line chart comparing ratios
        fig = go.Figure()
        
        # Add a line for each company
        colors = get_chart_colors('categorical', len(ratio_data))
        
        for i, (ticker, data) in enumerate(ratio_data.items()):
            fig.add_trace(go.Scatter(
                x=data['dates'],
                y=data['values'],
                name=ticker,
                line=dict(color=colors[i], width=2),
                mode='lines+markers'
            ))
        
        # Add reference lines if provided
        if reference_lines:
            all_dates = [date for company in ratio_data.values() for date in company['dates']]
            if all_dates:
                min_date = min(all_dates)
                max_date = max(all_dates)
                
                for i, value in enumerate(reference_lines):
                    # Define line style based on value
                    if i == 0:  # First reference (usually the concern threshold)
                        line_color = "#F44336"  # Red
                        dash_style = "dash"
                    else:  # Second reference (usually the good threshold)
                        line_color = "#4CAF50"  # Green
                        dash_style = "dash"
                    
                    fig.add_shape(
                        type="line",
                        x0=min_date,
                        y0=value,
                        x1=max_date,
                        y1=value,
                        line=dict(color=line_color, width=2, dash=dash_style),
                    )
        
        # Update layout
        fig.update_layout(
            title=f"{display_name} Over Time",
            xaxis_title="Period",
            yaxis_title=display_name,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(30,30,30,0.3)',
            font=dict(color='white'),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=1.2,
                xanchor="center",
                x=0.5
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Add a table with the most recent values
        latest_values = []
        
        for ticker, data in ratio_data.items():
            if data['values']:
                latest_values.append({
                    'Company': ticker,
                    display_name: f"{data['values'][-1]:.2f}",
                    'Raw Value': data['values'][-1]
                })
        
        if latest_values:
            # Sort by value (direction depends on lower_better flag)
            latest_values.sort(key=lambda x: x['Raw Value'], reverse=not lower_better)
            
            # Create a styled table
            html = "<table style='width:100%; border-collapse: collapse;'>"
            
            # Add header
            html += "<tr style='background-color:rgba(50,50,50,0.8);'>"
            html += "<th style='text-align:left; padding:8px;'>Company</th>"
            html += f"<th style='text-align:center; padding:8px;'>{display_name}</th>"
            html += "<th style='text-align:center; padding:8px;'>Status</th>"
            html += "</tr>"
            
            # Add rows
            for item in latest_values:
                # Get evaluation
                indicator, status, _ = evaluate_ratio(ratio_name, item['Raw Value'])
                
                html += "<tr style='border-bottom: 1px solid rgba(80,80,80,0.5);'>"
                html += f"<td style='text-align:left; padding:8px;'>{item['Company']}</td>"
                html += f"<td style='text-align:center; padding:8px;'>{item[display_name]}</td>"
                html += f"<td style='text-align:center; padding:8px;'>{indicator} {status}</td>"
                html += "</tr>"
            
            # Close table
            html += "</table>"
            
            # Display the HTML table
            st.markdown(html, unsafe_allow_html=True)
    else:
        st.warning(f"Insufficient {display_name.lower()} data for comparison")

def display_balance_sheet_comparison(balance_data, asset_side=True):
    """Display balance sheet component comparison."""
    
    if asset_side:
        # Asset components
        components = [
            {'name': 'cashAndCashEquivalents', 'display': 'Cash & Equivalents'},
            {'name': 'shortTermInvestments', 'display': 'Short-term Investments'},
            {'name': 'netReceivables', 'display': 'Receivables'},
            {'name': 'inventory', 'display': 'Inventory'},
            {'name': 'propertyPlantEquipmentNet', 'display': 'PP&E'},
            {'name': 'goodwill', 'display': 'Goodwill'},
            {'name': 'intangibleAssets', 'display': 'Intangible Assets'}
        ]
        title = "Asset Composition by Company"
        total_field = 'totalAssets'
    else:
        # Liability and equity components
        components = [
            {'name': 'accountPayables', 'display': 'Accounts Payable'},
            {'name': 'shortTermDebt', 'display': 'Short-term Debt'},
            {'name': 'deferredRevenue', 'display': 'Deferred Revenue'},
            {'name': 'longTermDebt', 'display': 'Long-term Debt'},
            {'name': 'deferredTaxLiabilitiesNoncurrent', 'display': 'Deferred Tax Liabilities'},
            {'name': 'totalEquity', 'display': 'Total Equity'}
        ]
        title = "Liabilities & Equity Composition by Company"
        total_field = 'totalLiabilitiesAndTotalEquity'
    
    # Create a figure
    fig = go.Figure()
    
    # Add data for each company
    for ticker, data in balance_data.items():
        # Extract component values
        component_values = []
        component_labels = []
        
        # Check if we have the total field
        if total_field not in data.columns:
            continue
            
        total_value = data[total_field].iloc[0]
        
        if pd.isna(total_value) or total_value == 0:
            continue
        
        # Extract component values
        for component in components:
            if component['name'] in data.columns:
                value = data[component['name']].iloc[0]
                
                if pd.notna(value):
                    component_values.append(value)
                    component_labels.append(component['display'])
        
        if not component_values:
            continue
        
        # Create stacked bar for this company
        fig.add_trace(go.Bar(
            x=[ticker],
            y=component_values,
            name=component_labels,
            textposition='inside',
            insidetextanchor='middle'
        ))
    
    # Update layout for stacked bars
    fig.update_layout(
        title=title,
        xaxis_title="Company",
        yaxis_title="Amount",
        barmode='stack',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(30,30,30,0.3)',
        font=dict(color='white')
    )
    
    # Display the chart
    st.plotly_chart(fig, use_container_width=True)
    
    # Add a table with the component percentages
    composition_data = []
    
    for ticker, data in balance_data.items():
        # Check if we have the total field
        if total_field not in data.columns:
            continue
            
        total_value = data[total_field].iloc[0]
        
        if pd.isna(total_value) or total_value == 0:
            continue
        
        company_row = {'Company': ticker}
        
        # Calculate percentages for each component
        for component in components:
            if component['name'] in data.columns:
                value = data[component['name']].iloc[0]
                
                if pd.notna(value):
                    percentage = value / total_value
                    company_row[component['display']] = f"{percentage:.1%}"
        
        if len(company_row) > 1:  # More than just the company name
            composition_data.append(company_row)
    
    if composition_data:
        # Display as DataFrame
        df = pd.DataFrame(composition_data)
        styled_dataframe(df)

# Run the app
if __name__ == "__main__":
    company_comparison()