"""
Company Financial Explorer for the Agentic Explorer platform.

This page provides in-depth financial analysis for a single company,
highlighting performance trends, financial health indicators, and anomalies.
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
from utils.components.charts import line_chart, bar_chart
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
    format_large_number
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

def company_financial_explorer():
    """Main function for the Company Financial Explorer page."""
    
    # Create page container with title
    with page_container("Company Financial Explorer", "In-depth financial analysis and health assessment"):
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
        
        # Period type selector
        period_type = st.sidebar.radio(
            "Period Type",
            ["quarterly", "annual"],
            index=0
        )
        
        # Process selected company data
        if selected_ticker:
            # Load profile data
            profile = load_company_profile(selected_ticker)
            
            # Load financial data
            financials = load_company_financials(selected_ticker)
            
            if profile and financials is not None and not financials.empty:
                # Clean financial data
                financials = prepare_financial_data(financials)
                
                # Extract company name
                company_name = profile.get("companyName", selected_ticker)
                
                # Calculate financial ratios
                ratios_df = calculate_financial_ratios(financials, "Income Statement", period_type)
                
                # Display Company Overview Section
                display_company_overview(profile, company_name, ratios_df)
                
                # Display Financial Health Dashboard
                display_financial_health(ratios_df, financials, period_type)
                
                # Display Statement Trend Analysis
                display_statement_trends(financials, period_type)
                
                # Display Period-by-Period Analysis
                display_period_comparison(financials, period_type)
            else:
                st.warning(f"No financial data found for {selected_ticker}")

def display_company_overview(profile, company_name, ratios_df):
    """Display company overview section."""
    
    # Calculate financial health score
    score, category = calculate_financial_health_score(ratios_df)
    
    # Create two-column layout
    left_col, right_col = two_column_layout(1, 3)
    
    with left_col:
        # Display company logo if available
        if "image" in profile and profile["image"]:
            st.image(profile["image"], width=150)
        
        # Company metadata
        with card("Company Info"):
            st.markdown(f"**Industry:** {profile.get('industry', 'N/A')}")
            st.markdown(f"**Sector:** {profile.get('sector', 'N/A')}")
            
            # Add market cap
            mkt_cap = profile.get("mktCap", "N/A")
            if isinstance(mkt_cap, (int, float)):
                st.markdown(f"**Market Cap:** {format_large_number(mkt_cap)}")
            else:
                st.markdown(f"**Market Cap:** {mkt_cap}")
            
            # Add beta
            beta = profile.get("beta", "N/A")
            if isinstance(beta, (int, float)):
                st.markdown(f"**Beta:** {beta:.2f}")
            else:
                st.markdown(f"**Beta:** {beta}")
    
    with right_col:
        # Display company name as header
        st.header(company_name)
        
        # Financial health score with color coding
        with card("Financial Health Assessment"):
            # Create color based on score
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
            
            # Create a circular progress indicator with custom styling
            st.markdown(f"""
            <div style="display: flex; align-items: center; margin-bottom: 20px;">
                <div style="position: relative; width: 100px; height: 100px; margin-right: 20px;">
                    <svg width="100" height="100" viewBox="0 0 100 100">
                        <circle cx="50" cy="50" r="45" fill="none" stroke="#333333" stroke-width="10" />
                        <circle cx="50" cy="50" r="45" fill="none" stroke="{color}" stroke-width="10"
                                stroke-dasharray="283" stroke-dashoffset="{283 - (score/100 * 283)}"
                                transform="rotate(-90 50 50)" />
                    </svg>
                    <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); 
                                font-size: 24px; font-weight: bold; color: white;">
                        {int(score)}
                    </div>
                </div>
                <div>
                    <h3 style="margin: 0; color: {color};">{category}</h3>
                    <p style="margin: 5px 0 0 0; color: #AAAAAA; font-size: 14px;">Financial Health Score</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Add explanation based on category
            if category == "Strong":
                st.markdown("The company demonstrates strong financial health with excellent performance across key metrics.")
            elif category == "Healthy":
                st.markdown("The company shows good financial health with solid performance in most areas.")
            elif category == "Adequate":
                st.markdown("The company maintains adequate financial health with mixed performance across metrics.")
            elif category == "Vulnerable":
                st.markdown("The company shows concerning signs in multiple financial areas and may be vulnerable to challenges.")
            else:  # Distressed
                st.markdown("The company exhibits serious financial weakness across multiple metrics, indicating potential distress.")

def display_financial_health(ratios_df, financials, period_type):
    """Display financial health dashboard with key ratios and indicators."""
    
    st.markdown("## Financial Health Dashboard")
    
    if ratios_df.empty:
        st.warning("Insufficient ratio data available for analysis")
        return
    
    # Ensure data is sorted by date descending
    ratios_df = ratios_df.sort_values('date', ascending=False)
    
    # Get the most recent values
    latest_ratios = ratios_df.iloc[0]
    
    # Detect anomalies
    anomalies = detect_financial_anomalies(financials, ratios_df)
    
    # Create layout
    left_col, right_col = two_column_layout(3, 1)
    
    with left_col:
        # Key Ratios Section
        with card("Key Financial Ratios"):
            # Define the ratios to display
            display_ratios = [
                {'name': 'gross_margin', 'display': 'Gross Margin', 'format': '{:.1%}'},
                {'name': 'operating_margin', 'display': 'Operating Margin', 'format': '{:.1%}'},
                {'name': 'net_margin', 'display': 'Net Margin', 'format': '{:.1%}'},
                {'name': 'current_ratio', 'display': 'Current Ratio', 'format': '{:.2f}'},
                {'name': 'debt_to_equity', 'display': 'Debt-to-Equity', 'format': '{:.2f}'},
                {'name': 'asset_turnover', 'display': 'Asset Turnover', 'format': '{:.2f}'}
            ]
            
            # Create two columns for the ratios
            col1, col2 = st.columns(2)
            
            # Display each ratio in alternating columns
            for i, ratio in enumerate(display_ratios):
                col = col1 if i % 2 == 0 else col2
                
                with col:
                    if ratio['name'] in latest_ratios:
                        value = latest_ratios[ratio['name']]
                        
                        # Determine trend if possible
                        trend = determine_ratio_trend(ratios_df, ratio['name'])
                        
                        # Skip if value is NaN or invalid
                        if pd.isna(value) or not np.isfinite(value):
                            st.markdown(f"**{ratio['display']}:** N/A")
                            continue
                            
                        # Get evaluation
                        indicator, status, description = evaluate_ratio(ratio['name'], value, trend)
                        
                        # Format the value
                        try:
                            formatted_value = ratio['format'].format(value)
                        except:
                            formatted_value = f"{value:.2f}"
                        
                        # Display with indicator
                        st.markdown(f"**{ratio['display']}:** {indicator} {formatted_value}")
                        
                        # Add tooltip with explanation
                        st.caption(f"{status}: {description}")
                        
                        # Show small trend chart if enough data
                        if len(ratios_df) >= 3 and not ratios_df[ratio['name']].isnull().all():
                            # Get the last 6 periods or all available
                            chart_data = ratios_df.head(min(6, len(ratios_df))).sort_values('date')
                            
                            # Create a small line chart
                            fig = line_chart(
                                chart_data,
                                x='date',
                                y=ratio['name'],
                                height=120,
                                markers=True
                            )
                            
                            # Customize for small display
                            fig.update_layout(
                                margin=dict(l=10, r=10, t=10, b=10),
                                showlegend=False,
                                xaxis=dict(
                                    showticklabels=True,
                                    tickformat="%b '%y",
                                    tickangle=45
                                )
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.markdown(f"**{ratio['display']}:** N/A")
        
        # Display period-over-period growth rates for key metrics
        with card("Key Growth Metrics"):
            # Get growth rates
            growth_data = calculate_growth_rates(financials, 'Income Statement', period_type)
            
            if not growth_data.empty:
                # Define metrics to show growth for
                growth_metrics = [
                    {'col': 'revenue_growth', 'display': 'Revenue Growth'},
                    {'col': 'grossProfit_growth', 'display': 'Gross Profit Growth'},
                    {'col': 'operatingIncome_growth', 'display': 'Operating Income Growth'},
                    {'col': 'netIncome_growth', 'display': 'Net Income Growth'}
                ]
                
                # Create columns
                mcol1, mcol2 = st.columns(2)
                
                # Display each growth metric
                for i, metric in enumerate(growth_metrics):
                    col = mcol1 if i % 2 == 0 else mcol2
                    
                    with col:
                        if metric['col'] in growth_data.columns:
                            # Get the most recent growth rate
                            growth = growth_data[metric['col']].iloc[-1]
                            
                            if not pd.isna(growth):
                                # Determine color and indicator
                                if growth >= 0.05:  # 5% or higher growth
                                    color = "#4CAF50"  # Green
                                    indicator = "🟢"
                                elif growth >= -0.05:  # Between -5% and 5%
                                    color = "#FFEB3B"  # Yellow
                                    indicator = "🟡"
                                else:  # Below -5%
                                    color = "#F44336"  # Red
                                    indicator = "🔴"
                                
                                st.markdown(f"**{metric['display']}:** {indicator} {growth:.1%}")
                                
                                # Get enough data for a chart
                                if len(growth_data) >= 3:
                                    # Create chart data sorted by date
                                    chart_data = growth_data.sort_values('date')
                                    
                                    # Create a bar chart
                                    fig = bar_chart(
                                        chart_data,
                                        x='date',
                                        y=metric['col'],
                                        height=120
                                    )
                                    
                                    # Customize the chart
                                    fig.update_layout(
                                        margin=dict(l=10, r=10, t=10, b=10),
                                        showlegend=False,
                                        xaxis=dict(
                                            showticklabels=True,
                                            tickformat="%b '%y",
                                            tickangle=45
                                        ),
                                        yaxis=dict(
                                            tickformat=".0%"
                                        )
                                    )
                                    
                                    # Add color based on value
                                    fig.update_traces(
                                        marker_color=[
                                            "#4CAF50" if x >= 0.05 else 
                                            "#FFEB3B" if x >= -0.05 else 
                                            "#F44336" for x in chart_data[metric['col']]
                                        ]
                                    )
                                    
                                    st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.markdown(f"**{metric['display']}:** N/A")
                        else:
                            st.markdown(f"**{metric['display']}:** N/A")
            else:
                st.warning("Insufficient data to calculate growth metrics")
    
    with right_col:
        # Display anomalies
        with card("Detected Anomalies"):
            if anomalies:
                for anomaly in anomalies:
                    # Determine severity color
                    if anomaly['severity'] == 'high':
                        severity_color = "#F44336"  # Red
                        indicator = "🔴"
                    elif anomaly['severity'] == 'medium':
                        severity_color = "#FF9800"  # Orange
                        indicator = "🟠"
                    else:
                        severity_color = "#2196F3"  # Blue
                        indicator = "🔵"
                    
                    # Display anomaly
                    st.markdown(f"### {indicator} {anomaly['title']}")
                    st.markdown(f"<div style='color: {severity_color};'>{anomaly['description']}</div>", 
                                unsafe_allow_html=True)
                    st.markdown("---")
            else:
                st.info("No significant anomalies detected in the financial data.")

def display_statement_trends(financials, period_type):
    """Display trend analysis for key financial statement items."""
    
    st.markdown("## Statement Trend Analysis")
    
    # Filter for income statement data
    income_data = get_statement_data(financials, 'Income Statement', period_type)
    
    # Filter for balance sheet data
    balance_data = get_statement_data(financials, 'Balance Sheet', period_type)
    
    # Filter for cash flow data
    cashflow_data = get_statement_data(financials, 'Cash Flow', period_type)
    
    # Create tabs for different statement types
    tabs = st.tabs(["Income Statement", "Balance Sheet", "Cash Flow"])
    
    # Income Statement Tab
    with tabs[0]:
        if not income_data.empty and len(income_data) >= 2:
            # Create two columns for different chart types
            col1, col2 = st.columns(2)
            
            with col1:
                # Revenue and Profitability trend
                with card("Revenue & Profitability Trends"):
                    # Check if required columns exist
                    if all(col in income_data.columns for col in ['revenue', 'grossProfit', 'operatingIncome', 'netIncome']):
                        # Create figure for revenue
                        fig = go.Figure()
                        
                        # Add revenue line (primary y-axis)
                        fig.add_trace(go.Scatter(
                            x=income_data['date'],
                            y=income_data['revenue'],
                            name='Revenue',
                            line=dict(color='#2196F3', width=3),
                            mode='lines+markers'
                        ))
                        
                        # Create layout
                        fig.update_layout(
                            title="Revenue & Margin Trends",
                            xaxis_title="Period",
                            yaxis_title="Revenue"
                        )
                        
                        # Add secondary y-axis
                        fig.update_layout(
                            yaxis2=dict(
                                title="Margin (%)",
                                title_font=dict(color="#4CAF50"),
                                tickfont=dict(color="#4CAF50"),
                                anchor="x",
                                overlaying="y",
                                side="right",
                                tickformat=".0%"
                            )
                        )
                        
                        # Calculate margins and handle potential division by zero
                        if 'grossProfit' in income_data.columns and 'revenue' in income_data.columns:
                            gross_margin = income_data['grossProfit'] / income_data['revenue'].replace(0, np.nan)
                            
                            # Add gross margin line
                            fig.add_trace(go.Scatter(
                                x=income_data['date'],
                                y=gross_margin,
                                name='Gross Margin',
                                line=dict(color='#4CAF50', width=2, dash='dot'),
                                mode='lines+markers',
                                yaxis="y2"
                            ))
                        
                        if 'operatingIncome' in income_data.columns and 'revenue' in income_data.columns:
                            operating_margin = income_data['operatingIncome'] / income_data['revenue'].replace(0, np.nan)
                            
                            # Add operating margin line
                            fig.add_trace(go.Scatter(
                                x=income_data['date'],
                                y=operating_margin,
                                name='Operating Margin',
                                line=dict(color='#FF9800', width=2, dash='dot'),
                                mode='lines+markers',
                                yaxis="y2"
                            ))
                        
                        if 'netIncome' in income_data.columns and 'revenue' in income_data.columns:
                            net_margin = income_data['netIncome'] / income_data['revenue'].replace(0, np.nan)
                            
                            # Add net margin line
                            fig.add_trace(go.Scatter(
                                x=income_data['date'],
                                y=net_margin,
                                name='Net Margin',
                                line=dict(color='#F44336', width=2, dash='dot'),
                                mode='lines+markers',
                                yaxis="y2"
                            ))
                        
                        # Apply style consistent with theme
                        fig.update_layout(
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(30,30,30,0.3)',
                            font=dict(color='white'),
                            legend=dict(orientation="h", y=1.1)
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("Required data for revenue and profitability analysis is not available")
            
            with col2:
                # Expense breakdown trend
                with card("Expense Breakdown"):
                    # Check for required columns
                    expense_cols = [
                        'costOfRevenue', 
                        'researchAndDevelopmentExpenses', 
                        'sellingGeneralAndAdministrativeExpenses',
                        'otherExpenses'
                    ]
                    
                    available_cols = [col for col in expense_cols if col in income_data.columns]
                    
                    if len(available_cols) >= 2:
                        # Create a stacked area chart
                        fig = go.Figure()
                        
                        # Define colors for each expense type
                        colors = ['#FF9800', '#F44336', '#9C27B0', '#3F51B5', '#009688']
                        
                        # Add traces for each expense type
                        for i, col in enumerate(available_cols):
                            # Replace NaN with 0
                            values = income_data[col].fillna(0)
                            
                            fig.add_trace(go.Scatter(
                                x=income_data['date'],
                                y=values,
                                name=col.replace('Expenses', '').replace('And', '&').replace('Of', 'of'),
                                mode='lines',
                                stackgroup='one',
                                line=dict(width=0.5, color=colors[i % len(colors)]),
                                fillcolor=colors[i % len(colors)]
                            ))
                        
                        # Add revenue for comparison
                        if 'revenue' in income_data.columns:
                            fig.add_trace(go.Scatter(
                                x=income_data['date'],
                                y=income_data['revenue'],
                                name='Revenue',
                                mode='lines+markers',
                                line=dict(color='#2196F3', width=3, dash='dash'),
                                yaxis="y"
                            ))
                        
                        # Update layout
                        fig.update_layout(
                            title="Expense Breakdown vs. Revenue",
                            xaxis_title="Period",
                            yaxis_title="Amount",
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="center",
                                x=0.5
                            ),
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(30,30,30,0.3)',
                            font=dict(color='white')
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("Insufficient expense breakdown data available")
                    
            # Additional income statement analysis
            with card("Income Statement Key Metrics"):
                # EPS Trend
                if 'eps' in income_data.columns:
                    fig = line_chart(
                        income_data,
                        x='date',
                        y='eps',
                        title="Earnings Per Share (EPS) Trend",
                        height=300,
                        markers=True
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("EPS data not available")
        else:
            st.warning("Insufficient income statement data available for trend analysis")
    
    # Balance Sheet Tab
    with tabs[1]:
        if not balance_data.empty and len(balance_data) >= 2:
            # Create two columns for different chart types
            col1, col2 = st.columns(2)
            
            with col1:
                # Assets and Liabilities trend
                with card("Assets & Liabilities Overview"):
                    # Check if required columns exist
                    if all(col in balance_data.columns for col in ['totalAssets', 'totalLiabilities', 'totalEquity']):
                        # Create figure
                        fig = go.Figure()
                        
                        # Add traces
                        fig.add_trace(go.Bar(
                            x=balance_data['date'],
                            y=balance_data['totalAssets'],
                            name='Total Assets',
                            marker_color='#2196F3'
                        ))
                        
                        fig.add_trace(go.Bar(
                            x=balance_data['date'],
                            y=balance_data['totalLiabilities'],
                            name='Total Liabilities',
                            marker_color='#F44336'
                        ))
                        
                        fig.add_trace(go.Bar(
                            x=balance_data['date'],
                            y=balance_data['totalEquity'],
                            name='Total Equity',
                            marker_color='#4CAF50'
                        ))
                        
                        # Update layout
                        fig.update_layout(
                            title="Assets, Liabilities & Equity",
                            xaxis_title="Period",
                            yaxis_title="Amount",
                            barmode='group',
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="center",
                                x=0.5
                            ),
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(30,30,30,0.3)',
                            font=dict(color='white')
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("Required data for assets and liabilities analysis is not available")
            
            with col2:
                # Liquidity Metrics
                with card("Liquidity Metrics"):
                    # Check for required columns
                    liquidity_cols = [
                        'cashAndCashEquivalents', 
                        'shortTermInvestments', 
                        'inventory',
                        'totalCurrentAssets',
                        'totalCurrentLiabilities'
                    ]
                    
                    available_cols = [col for col in liquidity_cols if col in balance_data.columns]
                    
                    if 'totalCurrentAssets' in available_cols and 'totalCurrentLiabilities' in available_cols:
                        # Calculate current ratio
                        current_ratio = balance_data['totalCurrentAssets'] / balance_data['totalCurrentLiabilities'].replace(0, np.nan)
                        
                        # Calculate quick ratio if data available
                        if 'inventory' in available_cols:
                            quick_ratio = (balance_data['totalCurrentAssets'] - balance_data['inventory']) / balance_data['totalCurrentLiabilities'].replace(0, np.nan)
                        else:
                            quick_ratio = None
                        
                        # Create figure
                        fig = go.Figure()
                        
                        # Add current ratio
                        fig.add_trace(go.Scatter(
                            x=balance_data['date'],
                            y=current_ratio,
                            name='Current Ratio',
                            mode='lines+markers',
                            line=dict(color='#2196F3', width=3)
                        ))
                        
                        # Add quick ratio if available
                        if quick_ratio is not None:
                            fig.add_trace(go.Scatter(
                                x=balance_data['date'],
                                y=quick_ratio,
                                name='Quick Ratio',
                                mode='lines+markers',
                                line=dict(color='#FF9800', width=3, dash='dot')
                            ))
                        
                        # Add reference lines
                        fig.add_shape(
                            type="line",
                            x0=balance_data['date'].min(),
                            y0=1,
                            x1=balance_data['date'].max(),
                            y1=1,
                            line=dict(color="#F44336", width=2, dash="dash"),
                        )
                        
                        fig.add_shape(
                            type="line",
                            x0=balance_data['date'].min(),
                            y0=2,
                            x1=balance_data['date'].max(),
                            y1=2,
                            line=dict(color="#4CAF50", width=2, dash="dash"),
                        )
                        
                        # Update layout
                        fig.update_layout(
                            title="Liquidity Ratios",
                            xaxis_title="Period",
                            yaxis_title="Ratio",
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="center",
                                x=0.5
                            ),
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(30,30,30,0.3)',
                            font=dict(color='white')
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("Required data for liquidity analysis is not available")
            
            # Additional balance sheet analysis
            with card("Asset Composition"):
                # Asset breakdown
                asset_cols = [
                    'cashAndCashEquivalents',
                    'shortTermInvestments',
                    'netReceivables',
                    'inventory',
                    'propertyPlantEquipmentNet',
                    'goodwill',
                    'intangibleAssets',
                    'longTermInvestments'
                ]
                
                available_assets = [col for col in asset_cols if col in balance_data.columns]
                
                if len(available_assets) >= 3:
                    # Create a stacked area chart for asset composition
                    fig = go.Figure()
                    
                    # Define colors
                    colors = ['#2196F3', '#4CAF50', '#FF9800', '#F44336', '#9C27B0', '#3F51B5', '#009688', '#FFEB3B']
                    
                    # Add traces for each asset type
                    for i, col in enumerate(available_assets):
                        fig.add_trace(go.Scatter(
                            x=balance_data['date'],
                            y=balance_data[col],
                            name=col.replace('And', '&').replace('Equipment', 'Equip.').replace('Receivables', 'Recv.'),
                            mode='lines',
                            stackgroup='one',
                            line=dict(width=0.5, color=colors[i % len(colors)]),
                            fillcolor=colors[i % len(colors)]
                        ))
                    
                    # Update layout
                    fig.update_layout(
                        title="Asset Composition Over Time",
                        xaxis_title="Period",
                        yaxis_title="Amount",
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="center",
                            x=0.5
                        ),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(30,30,30,0.3)',
                        font=dict(color='white')
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Insufficient asset breakdown data available")
        else:
            st.warning("Insufficient balance sheet data available for trend analysis")
    
    # Cash Flow Tab
    with tabs[2]:
        if not cashflow_data.empty and len(cashflow_data) >= 2:
            # Create two columns for different chart types
            col1, col2 = st.columns(2)
            
            with col1:
                # Operating Cash Flow vs. Net Income
                with card("Operating Cash Flow vs. Net Income"):
                    # Check if required columns exist
                    if all(col in cashflow_data.columns for col in ['operatingCashFlow']) and 'netIncome' in income_data.columns:
                        # Create figure
                        fig = go.Figure()
                        
                        # Add Operating Cash Flow
                        fig.add_trace(go.Bar(
                            x=cashflow_data['date'],
                            y=cashflow_data['operatingCashFlow'],
                            name='Operating Cash Flow',
                            marker_color='#2196F3'
                        ))
                        
                        # Add Net Income
                        # Match dates between datasets
                        matching_income = pd.DataFrame()
                        matching_income['date'] = cashflow_data['date']
                        matching_income['netIncome'] = None
                        
                        for i, date in enumerate(matching_income['date']):
                            matches = income_data[income_data['date'] == date]
                            if not matches.empty:
                                matching_income.loc[i, 'netIncome'] = matches['netIncome'].values[0]
                        
                        fig.add_trace(go.Scatter(
                            x=matching_income['date'],
                            y=matching_income['netIncome'],
                            name='Net Income',
                            mode='lines+markers',
                            line=dict(color='#F44336', width=3)
                        ))
                        
                        # Calculate ratio of OCF to Net Income
                        ratio = []
                        for i in range(len(matching_income)):
                            ni = matching_income['netIncome'].iloc[i]
                            ocf = cashflow_data['operatingCashFlow'].iloc[i]
                            
                            if pd.notna(ni) and pd.notna(ocf) and ni != 0:
                                ratio.append(ocf / ni)
                            else:
                                ratio.append(None)
                        
                        # Add ratio line
                        if any(r is not None for r in ratio):
                            fig.add_trace(go.Scatter(
                                x=cashflow_data['date'],
                                y=ratio,
                                name='OCF/Net Income Ratio',
                                mode='lines+markers',
                                line=dict(color='#4CAF50', width=2, dash='dot'),
                                yaxis="y2"
                            ))
                            
                            # Add secondary y-axis for ratio
                            fig.update_layout(
                                yaxis2=dict(
                                    title="Ratio",
                                    title_font=dict(color="#4CAF50"),
                                    tickfont=dict(color="#4CAF50"),
                                    anchor="x",
                                    overlaying="y",
                                    side="right"
                                )
                            )
                        
                        # Update layout
                        fig.update_layout(
                            title="Operating Cash Flow vs. Net Income",
                            xaxis_title="Period",
                            yaxis_title="Amount",
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="center",
                                x=0.5
                            ),
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(30,30,30,0.3)',
                            font=dict(color='white')
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("Required data for operating cash flow analysis is not available")
            
            with col2:
                # Free Cash Flow and Capital Expenditure
                with card("Free Cash Flow & Capital Expenditure"):
                    # Check for required columns
                    required_cols = ['operatingCashFlow', 'capitalExpenditure']
                    
                    if all(col in cashflow_data.columns for col in required_cols):
                        # Calculate Free Cash Flow
                        cashflow_data['freeCashFlow'] = cashflow_data['operatingCashFlow'] + cashflow_data['capitalExpenditure']
                        
                        # Create figure
                        fig = go.Figure()
                        
                        # Add Free Cash Flow
                        fig.add_trace(go.Bar(
                            x=cashflow_data['date'],
                            y=cashflow_data['freeCashFlow'],
                            name='Free Cash Flow',
                            marker_color='#4CAF50'
                        ))
                        
                        # Add Capital Expenditure (negative values)
                        fig.add_trace(go.Bar(
                            x=cashflow_data['date'],
                            y=cashflow_data['capitalExpenditure'],
                            name='Capital Expenditure',
                            marker_color='#F44336'
                        ))
                        
                        # Add Operating Cash Flow line
                        fig.add_trace(go.Scatter(
                            x=cashflow_data['date'],
                            y=cashflow_data['operatingCashFlow'],
                            name='Operating Cash Flow',
                            mode='lines+markers',
                            line=dict(color='#2196F3', width=3)
                        ))
                        
                        # Update layout
                        fig.update_layout(
                            title="Free Cash Flow Components",
                            xaxis_title="Period",
                            yaxis_title="Amount",
                            barmode='relative',
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="center",
                                x=0.5
                            ),
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(30,30,30,0.3)',
                            font=dict(color='white')
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("Required data for free cash flow analysis is not available")
            
            # Additional cash flow analysis
            with card("Cash Flow Breakdown"):
                # Cash flow breakdown
                cf_cols = [
                    'operatingCashFlow',
                    'capitalExpenditure',
                    'cashflowFromInvestment',
                    'cashflowFromFinancing',
                    'dividendPayout'
                ]
                
                available_cf = [col for col in cf_cols if col in cashflow_data.columns]
                
                if len(available_cf) >= 3:
                    # Create a waterfall chart-like visual
                    dates = cashflow_data['date'].unique()
                    
                    if len(dates) > 0:
                        # Select the most recent date for detailed breakdown
                        latest_date = dates[-1]
                        latest_data = cashflow_data[cashflow_data['date'] == latest_date]
                        
                        # Create custom waterfall chart
                        labels = []
                        values = []
                        colors = []
                        
                        # Define display names and colors
                        display_names = {
                            'operatingCashFlow': 'Operating CF',
                            'capitalExpenditure': 'CapEx',
                            'cashflowFromInvestment': 'Investing CF',
                            'cashflowFromFinancing': 'Financing CF',
                            'dividendPayout': 'Dividends'
                        }
                        
                        color_map = {
                            'operatingCashFlow': '#4CAF50',
                            'capitalExpenditure': '#F44336',
                            'cashflowFromInvestment': '#FF9800',
                            'cashflowFromFinancing': '#2196F3',
                            'dividendPayout': '#9C27B0'
                        }
                        
                        # Add items to chart
                        for col in available_cf:
                            if col in latest_data.columns:
                                value = latest_data[col].values[0]
                                
                                if pd.notna(value):
                                    labels.append(display_names.get(col, col))
                                    values.append(value)
                                    colors.append(color_map.get(col, '#757575'))
                        
                        # Create the bar chart
                        fig = go.Figure()
                        
                        fig.add_trace(go.Bar(
                            x=labels,
                            y=values,
                            marker_color=colors
                        ))
                        
                        # Update layout
                        fig.update_layout(
                            title=f"Cash Flow Breakdown (Latest Period: {latest_date})",
                            xaxis_title="Component",
                            yaxis_title="Amount",
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(30,30,30,0.3)',
                            font=dict(color='white')
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("No date data available for cash flow breakdown")
                else:
                    st.warning("Insufficient cash flow breakdown data available")
        else:
            st.warning("Insufficient cash flow data available for trend analysis")

def display_period_comparison(financials, period_type):
    """Display period-by-period comparison."""
    
    st.markdown(f"## Period-by-Period Comparison")
    
    # Get income statement data
    income_data = get_statement_data(financials, 'Income Statement', period_type)
    
    if not income_data.empty and len(income_data) >= 2:
        # Select specific periods for comparison
        with card("Period Selection"):
            # Get available periods
            available_periods = income_data['date'].unique()
            
            # Create period selectors
            col1, col2 = st.columns(2)
            
            with col1:
                base_period = st.selectbox(
                    "Base Period",
                    available_periods,
                    index=1 if len(available_periods) > 1 else 0
                )
            
            with col2:
                compare_period = st.selectbox(
                    "Comparison Period",
                    available_periods,
                    index=0
                )
            
            # Get data for selected periods
            base_data = income_data[income_data['date'] == base_period]
            compare_data = income_data[income_data['date'] == compare_period]
            
            if not base_data.empty and not compare_data.empty:
                # Key metrics to compare
                metrics = [
                    'revenue',
                    'grossProfit',
                    'operatingIncome',
                    'netIncome',
                    'eps'
                ]
                
                # Display comparison table
                st.markdown("### Key Metric Comparison")
                
                comparison_data = []
                
                for metric in metrics:
                    if metric in base_data.columns and metric in compare_data.columns:
                        base_value = base_data[metric].values[0]
                        compare_value = compare_data[metric].values[0]
                        
                        if pd.notna(base_value) and pd.notna(compare_value) and base_value != 0:
                            change = (compare_value - base_value) / abs(base_value)
                            
                            # Format values
                            if metric == 'eps':
                                base_fmt = f"${base_value:.2f}"
                                compare_fmt = f"${compare_value:.2f}"
                            else:
                                base_fmt = format_large_number(base_value)
                                compare_fmt = format_large_number(compare_value)
                            
                            # Add to comparison data
                            comparison_data.append({
                                'Metric': metric.replace('Income', ' Income').replace('Profit', ' Profit').title(),
                                'Base Period': base_fmt,
                                'Compare Period': compare_fmt,
                                'Change': f"{change:.1%}",
                                'Change_raw': change
                            })
                
                # Convert to DataFrame for display
                if comparison_data:
                    df = pd.DataFrame(comparison_data)
                    
                    # Create styled HTML table
                    html = "<table style='width:100%; border-collapse: collapse;'>"
                    
                    # Add header
                    html += "<tr style='background-color:rgba(50,50,50,0.8);'>"
                    html += f"<th style='text-align:left; padding:8px;'>Metric</th>"
                    html += f"<th style='text-align:right; padding:8px;'>{base_period}</th>"
                    html += f"<th style='text-align:right; padding:8px;'>{compare_period}</th>"
                    html += f"<th style='text-align:right; padding:8px;'>Change</th>"
                    html += "</tr>"
                    
                    # Add rows
                    for _, row in df.iterrows():
                        change = float(row['Change_raw'])
                        
                        # Determine color based on change
                        if change > 0:
                            color = "#4CAF50"  # Green
                        elif change < 0:
                            color = "#F44336"  # Red
                        else:
                            color = "#757575"  # Gray
                        
                        # Add row with colored change
                        html += "<tr style='border-bottom: 1px solid rgba(80,80,80,0.5);'>"
                        html += f"<td style='text-align:left; padding:8px;'>{row['Metric']}</td>"
                        html += f"<td style='text-align:right; padding:8px;'>{row['Base Period']}</td>"
                        html += f"<td style='text-align:right; padding:8px;'>{row['Compare Period']}</td>"
                        html += f"<td style='text-align:right; color:{color}; padding:8px;'>{row['Change']}</td>"
                        html += "</tr>"
                    
                    # Close table
                    html += "</table>"
                    
                    # Display the HTML table
                    st.markdown(html, unsafe_allow_html=True)
                else:
                    st.warning("No comparable metrics available")
        
        # Detailed income statement comparison
        with card("Income Statement Comparison"):
            if not base_data.empty and not compare_data.columns.empty:
                # Select key metrics for comparison
                income_metrics = [
                    'revenue',
                    'costOfRevenue',
                    'grossProfit',
                    'researchAndDevelopmentExpenses',
                    'sellingGeneralAndAdministrativeExpenses',
                    'operatingExpenses',
                    'operatingIncome',
                    'interestExpense',
                    'interestIncome',
                    'otherNonOperatingIncome',
                    'incomeBeforeTax',
                    'incomeTaxExpense',
                    'netIncome',
                    'eps'
                ]
                
                # Filter for available metrics
                available_metrics = [m for m in income_metrics if m in base_data.columns and m in compare_data.columns]
                
                if available_metrics:
                    # Prepare data for visualization
                    labels = []
                    base_values = []
                    compare_values = []
                    percent_changes = []
                    
                    for metric in available_metrics:
                        base_value = base_data[metric].values[0]
                        compare_value = compare_data[metric].values[0]
                        
                        if pd.notna(base_value) and pd.notna(compare_value) and base_value != 0:
                            # Format label
                            label = metric.replace('Income', ' Income').replace('Profit', ' Profit').replace('Expenses', ' Expenses').title()
                            
                            labels.append(label)
                            base_values.append(base_value)
                            compare_values.append(compare_value)
                            percent_changes.append((compare_value - base_value) / abs(base_value) * 100)
                    
                    # Create horizontal bar chart for comparison
                    fig = go.Figure()
                    
                    # Add base period bars
                    fig.add_trace(go.Bar(
                        y=labels,
                        x=base_values,
                        name=str(base_period),
                        orientation='h',
                        marker_color='rgba(33, 150, 243, 0.7)'
                    ))
                    
                    # Add comparison period bars
                    fig.add_trace(go.Bar(
                        y=labels,
                        x=compare_values,
                        name=str(compare_period),
                        orientation='h',
                        marker_color='rgba(76, 175, 80, 0.7)'
                    ))
                    
                    # Update layout
                    fig.update_layout(
                        title="Income Statement Comparison",
                        xaxis_title="Amount",
                        barmode='group',
                        height=max(400, len(labels) * 30),  # Adjust height based on number of items
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(30,30,30,0.3)',
                        font=dict(color='white'),
                        margin=dict(l=200)  # Add margin for labels
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Add percentage change visualization
                    st.markdown("### Percentage Changes")
                    
                    # Create horizontal bar chart for percentage changes
                    fig = go.Figure()
                    
                    # Define colors based on change direction
                    colors = ['#4CAF50' if x >= 0 else '#F44336' for x in percent_changes]
                    
                    # Add percentage change bars
                    fig.add_trace(go.Bar(
                        y=labels,
                        x=percent_changes,
                        orientation='h',
                        marker_color=colors
                    ))
                    
                    # Add zero line
                    fig.add_shape(
                        type="line",
                        x0=0,
                        y0=-0.5,
                        x1=0,
                        y1=len(labels) - 0.5,
                        line=dict(color="#FFFFFF", width=2, dash="solid"),
                    )
                    
                    # Update layout
                    fig.update_layout(
                        title="Percentage Change by Metric",
                        xaxis_title="Percent Change (%)",
                        xaxis=dict(ticksuffix="%"),
                        height=max(400, len(labels) * 30),  # Adjust height based on number of items
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(30,30,30,0.3)',
                        font=dict(color='white'),
                        margin=dict(l=200)  # Add margin for labels
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No comparable income statement metrics available")
            else:
                st.warning("Income statement data not available for the selected periods")
        
        # Trend indicators
        with card("Key Trend Indicators"):
            # Get the latest 4-6 periods of data
            trend_data = income_data.head(min(6, len(income_data)))
            
            if not trend_data.empty and len(trend_data) >= 3:
                # Key metrics to analyze
                trend_metrics = [
                    {'name': 'revenue', 'display': 'Revenue Trend'},
                    {'name': 'grossProfit', 'display': 'Gross Profit Trend'},
                    {'name': 'operatingIncome', 'display': 'Operating Income Trend'},
                    {'name': 'netIncome', 'display': 'Net Income Trend'}
                ]
                
                # Create columns for trend indicators
                cols = st.columns(len(trend_metrics))
                
                # Display trend indicators
                for i, metric in enumerate(trend_metrics):
                    if metric['name'] in trend_data.columns:
                        with cols[i]:
                            # Analyze trend
                            trend_analysis = analyze_trend_direction(trend_data, metric['name'])
                            
                            # Display trend information
                            st.markdown(f"#### {metric['display']}")
                            
                            if trend_analysis['direction'] != 'insufficient_data':
                                st.markdown(f"##### {trend_analysis['icon']} {trend_analysis['description']}")
                                
                                # Format and display strength
                                strength = trend_analysis['strength']
                                if strength > 0:
                                    st.markdown(f"Average change: **{strength:.1%}** per period")
                            else:
                                st.markdown("##### ❓ Insufficient Data")
                                st.markdown("Not enough periods to determine trend")
            else:
                st.warning("Insufficient data for trend analysis")
    else:
        st.warning("Insufficient income statement data available for period comparison")

# Run the app
if __name__ == "__main__":
    company_financial_explorer()