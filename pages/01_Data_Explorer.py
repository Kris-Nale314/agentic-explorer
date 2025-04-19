"""
Agentic Explorer - Data Explorer 

An enhanced data exploration interface that provides intuitive 
access to company data, financials, price history, and more.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import json
import os
from pathlib import Path
import re

# Import our custom components
from utils.components.layout import page_container, card, two_column_layout, metrics_row
from utils.components.charts import line_chart, candlestick_chart, event_timeline_chart
from utils.components.data_display import styled_dataframe, metric_card
from utils.components.interactive import styled_date_selector, search_box, segmented_control
from utils.components.loaders import neon_spinner
from utils.components.themes import apply_theme

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

def load_company_prices(ticker):
    """Load historical price data for a given ticker."""
    prices_path = get_datastore_path() / "companies" / ticker / "prices.parquet"
    if prices_path.exists():
        return pd.read_parquet(prices_path)
    return None

def load_company_news(ticker):
    """Load news data for a given ticker."""
    news_path = get_datastore_path() / "companies" / ticker / "news.parquet"
    if news_path.exists():
        return pd.read_parquet(news_path)
    return None

def load_earnings_transcripts(ticker):
    """Load earnings call transcripts for a given ticker."""
    transcripts_path = get_datastore_path() / "companies" / ticker / "transcripts.parquet"
    if transcripts_path.exists():
        return pd.read_parquet(transcripts_path)
    return None

def format_large_number(num):
    """Format large numbers with K, M, B suffixes."""
    if num is None:
        return "N/A"
    
    if not isinstance(num, (int, float)):
        return str(num)
    
    if abs(num) >= 1_000_000_000:
        return f"${num / 1_000_000_000:.2f}B"
    elif abs(num) >= 1_000_000:
        return f"${num / 1_000_000:.2f}M"
    elif abs(num) >= 1_000:
        return f"${num / 1_000:.2f}K"
    else:
        return f"${num:.2f}"

def data_explorer():
    """Main data explorer interface."""
    # Create page container with title
    with page_container("Data Explorer", "Explore financial data for analysis"):
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
        
        # Add a quick view of available companies
        with st.sidebar.expander("Available Companies", expanded=False):
            for ticker in available_tickers:
                profile = load_company_profile(ticker)
                if profile:
                    company_name = profile.get("companyName", ticker)
                    st.sidebar.markdown(f"**{ticker}**: {company_name}")
                else:
                    st.sidebar.markdown(f"**{ticker}**")
        
        # Data type tabs
        data_view = segmented_control(
            ["Overview", "Financials", "Stock Price", "News", "Transcripts"],
            key="data_view"
        )
        
        # Process selected company data
        if selected_ticker:
            # Load profile data
            profile = load_company_profile(selected_ticker)
            
            if profile:
                # Display different views based on selection
                if data_view == "Overview":
                    display_company_overview(selected_ticker, profile)
                elif data_view == "Financials":
                    display_financial_data(selected_ticker)
                elif data_view == "Stock Price":
                    display_stock_price_data(selected_ticker)
                elif data_view == "News":
                    display_news_data(selected_ticker)
                elif data_view == "Transcripts":
                    display_transcript_data(selected_ticker)
            else:
                st.warning(f"No profile data found for {selected_ticker}")

def display_company_overview(ticker, profile):
    """Display company overview information."""
    # Extract profile info
    company_name = profile.get("companyName", ticker)
    industry = profile.get("industry", "N/A")
    sector = profile.get("sector", "N/A")
    website = profile.get("website", "#")
    description = profile.get("description", "No description available.")
    
    # Create two-column layout
    left_col, right_col = two_column_layout(1, 2)
    
    with left_col:
        # Display company logo if available
        if "image" in profile and profile["image"]:
            st.image(profile["image"], width=200)
        
        # Company metadata
        with card("Company Info"):
            st.markdown(f"**Exchange:** {profile.get('exchange', 'N/A')}")
            st.markdown(f"**Industry:** {industry}")
            st.markdown(f"**Sector:** {sector}")
            st.markdown(f"**CEO:** {profile.get('ceo', 'N/A')}")
            st.markdown(f"**Website:** [{website}]({website})")
            
            # Add horizontal line
            st.markdown("---")
            
            # Additional metrics
            st.markdown(f"**IPO Date:** {profile.get('ipoDate', 'N/A')}")
            st.markdown(f"**CIK:** {profile.get('cik', 'N/A')}")
            
            # Handle employees field safely
            employees = profile.get('fullTimeEmployees', 'N/A')
            if isinstance(employees, (int, float)):
                st.markdown(f"**Employees:** {employees:,}")
            else:
                st.markdown(f"**Employees:** {employees}")
    
    with right_col:
        # Display company name as header
        st.header(company_name)
        
        # Company description
        st.markdown(description)
        
        # Financial highlights
        with card("Financial Highlights"):
            # Create key metrics from profile data
            metrics = []
            
            # Only add metrics that exist in the profile
            if "mktCap" in profile:
                metrics.append({
                    "label": "Market Cap",
                    "value": format_large_number(profile.get("mktCap"))
                })
                
            if "price" in profile:
                metrics.append({
                    "label": "Stock Price",
                    "value": f"${profile.get('price', 0):.2f}"
                })
                
            if "beta" in profile:
                metrics.append({
                    "label": "Beta",
                    "value": f"{profile.get('beta', 0):.2f}"
                })
                
            if "volAvg" in profile:
                metrics.append({
                    "label": "Avg. Volume",
                    "value": f"{profile.get('volAvg', 0):,}"
                })
                
            if "lastDiv" in profile:
                metrics.append({
                    "label": "Last Dividend",
                    "value": f"${profile.get('lastDiv', 0):.2f}"
                })
            
            # Display metrics in a row
            if metrics:
                metrics_row(metrics)
            else:
                st.info("No financial metrics available")
        
        # Check if we have price data for a quick chart
        prices = load_company_prices(ticker)
        if prices is not None and not prices.empty and 'date' in prices.columns and 'close' in prices.columns:
            with card("Stock Price Trend"):
                # Convert date to datetime if it's not already
                if not pd.api.types.is_datetime64_any_dtype(prices['date']):
                    prices['date'] = pd.to_datetime(prices['date'])
                
                # Sort by date
                prices = prices.sort_values('date')
                
                # Take the most recent year of data
                recent_prices = prices.tail(252)  # ~1 trading year
                
                # Create simple line chart
                fig = line_chart(
                    recent_prices,
                    x='date',
                    y='close',
                    title=f"{ticker} - 1 Year Price Trend"
                )
                
                st.plotly_chart(fig, use_container_width=True)

def display_financial_data(ticker):
    """Display financial statement data."""
    financials = load_company_financials(ticker)
    
    if financials is None or financials.empty:
        st.warning(f"No financial data found for {ticker}")
        return
    
    # Create filters for statement type and period
    col1, col2 = two_column_layout()
    
    with col1:
        statement_types = financials['statement_type'].unique().tolist() if 'statement_type' in financials.columns else []
        selected_statement = st.selectbox(
            "Statement Type",
            statement_types if statement_types else ["No statements available"]
        )
    
    with col2:
        period_types = financials['period_type'].unique().tolist() if 'period_type' in financials.columns else []
        selected_period = st.selectbox(
            "Period Type",
            period_types if period_types else ["No periods available"]
        )
    
    if not statement_types or not period_types:
        st.warning("Financial data structure is not as expected")
        return
    
    # Filter data based on selection
    filtered_data = financials[
        (financials['statement_type'] == selected_statement) & 
        (financials['period_type'] == selected_period)
    ]
    
    if filtered_data.empty:
        st.warning(f"No data available for the selected filters")
        return
    
    # Sort by date
    if 'date' in filtered_data.columns:
        filtered_data = filtered_data.sort_values('date', ascending=False)
    
    # Create visualization section
    with card("Financial Metrics Visualization"):
        # Select metrics based on statement type
        if selected_statement == "Income Statement":
            default_metrics = ['revenue', 'grossProfit', 'netIncome', 'eps']
        elif selected_statement == "Balance Sheet":
            default_metrics = ['totalAssets', 'totalLiabilities', 'totalEquity', 'cashAndCashEquivalents']
        elif selected_statement == "Cash Flow":
            default_metrics = ['operatingCashFlow', 'capitalExpenditure', 'freeCashFlow', 'dividendsPaid']
        elif selected_statement == "Key Metrics":
            default_metrics = ['revenuePerShare', 'netIncomePerShare', 'operatingCashFlowPerShare', 'freeCashFlowPerShare']
        elif selected_statement == "Financial Ratios":
            default_metrics = ['returnOnEquity', 'returnOnAssets', 'debtToEquity', 'currentRatio']
        else:
            # Default metrics if statement type is not recognized
            default_metrics = [col for col in filtered_data.columns if filtered_data[col].dtype in [float, int] and col not in ['date', 'period']][:4]
        
        # Filter out metrics that don't exist in the data
        available_metrics = [m for m in default_metrics if m in filtered_data.columns]
        
        if not available_metrics:
            st.warning(f"No numeric metrics found for the selected statement type")
            return
        
        # Create metrics selection
        selected_metrics = st.multiselect(
            "Select metrics to visualize",
            available_metrics,
            default=available_metrics[:min(4, len(available_metrics))]
        )
        
        if not selected_metrics:
            st.warning("Please select at least one metric to visualize")
            return
        
        # Create plot
        if 'date' in filtered_data.columns:
            # Create plot
            fig = line_chart(
                filtered_data,
                x='date',
                y=selected_metrics,
                title=f"{selected_statement} - {selected_period}"
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # Display raw data
    with st.expander("View Raw Data", expanded=False):
        styled_dataframe(filtered_data)

def display_stock_price_data(ticker):
    """Display stock price data with enhanced visualizations."""
    prices = load_company_prices(ticker)
    
    if prices is None or prices.empty:
        st.warning(f"No price data found for {ticker}")
        return
    
    # Date range selector
    start_date, end_date = styled_date_selector("Select Date Range", default_days_back=365)
    
    # Ensure dates are datetime
    if not pd.api.types.is_datetime64_any_dtype(prices['date']):
        prices['date'] = pd.to_datetime(prices['date'])
    
    # Filter by date range
    filtered_prices = prices[
        (prices['date'].dt.date >= start_date) & 
        (prices['date'].dt.date <= end_date)
    ]
    
    if filtered_prices.empty:
        st.warning(f"No data available for the selected date range")
        return
    
    # Price chart options
    chart_type = st.radio("Chart Type", ["Candlestick", "Line"], horizontal=True)
    
    with card("Price Chart"):
        # Create appropriate chart based on selection
        if chart_type == "Candlestick":
            # Check if we have all required columns
            if all(col in filtered_prices.columns for col in ['date', 'open', 'high', 'low', 'close']):
                fig = candlestick_chart(
                    filtered_prices,
                    moving_averages=[20, 50],
                    title=f"{ticker} Stock Price",
                    range_slider=True
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Missing required columns for candlestick chart")
        else:  # Line chart
            if 'close' in filtered_prices.columns:
                fig = line_chart(
                    filtered_prices,
                    x='date',
                    y='close',
                    title=f"{ticker} Stock Price",
                    range_slider=True,
                    markers=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Missing 'close' column for line chart")
    
    # Calculate and display key statistics
    if 'close' in filtered_prices.columns:
        with card("Price Statistics"):
            col1, col2, col3, col4 = st.columns(4)
            
            # Filter out any NaN values
            close_data = filtered_prices['close'].dropna()
            
            if not close_data.empty:
                current_price = close_data.iloc[-1]
                min_price = filtered_prices['low'].min() if 'low' in filtered_prices.columns else close_data.min()
                max_price = filtered_prices['high'].max() if 'high' in filtered_prices.columns else close_data.max()
                
                # Calculate price change
                first_price = close_data.iloc[0]
                last_price = close_data.iloc[-1]
                price_change = ((last_price - first_price) / first_price) * 100
                
                with col1:
                    metric_card("Current Price", f"${current_price:.2f}")
                
                with col2:
                    metric_card("Min Price", f"${min_price:.2f}")
                
                with col3:
                    metric_card("Max Price", f"${max_price:.2f}")
                
                with col4:
                    metric_card("Price Change", f"{price_change:.2f}%", 
                               color="#4caf50" if price_change >= 0 else "#f44336")
                
                # Add more advanced statistics
                st.markdown("### Advanced Statistics")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # Calculate volatility (standard deviation of returns)
                    returns = close_data.pct_change().dropna()
                    volatility = returns.std() * (252 ** 0.5)  # Annualized
                    metric_card("Volatility (Ann.)", f"{volatility:.2%}")
                
                with col2:
                    # Calculate average daily volume
                    if 'volume' in filtered_prices.columns:
                        avg_volume = filtered_prices['volume'].mean()
                        metric_card("Avg. Volume", f"{avg_volume:,.0f}")
                
                with col3:
                    # Calculate average daily range
                    if all(col in filtered_prices.columns for col in ['high', 'low']):
                        avg_range = ((filtered_prices['high'] - filtered_prices['low']) / filtered_prices['low']).mean() * 100
                        metric_card("Avg. Daily Range", f"{avg_range:.2f}%")

def display_news_data(ticker):
    """Display news articles with search and filtering."""
    news = load_company_news(ticker)
    
    if news is None or news.empty:
        st.warning(f"No news data found for {ticker}")
        return
    
    # Convert date column if exists
    if 'publishedDate' in news.columns:
        news['publishedDate'] = pd.to_datetime(news['publishedDate'])
        news = news.sort_values('publishedDate', ascending=False)
    
    # Create search interface
    search_query = search_box("Search articles", key="news_search", placeholder="Enter keywords to search...")    
    
    # Filter by search term if provided
    if search_query:
        filtered_news = news[
            news['title'].str.contains(search_query, case=False, na=False) | 
            news['text'].str.contains(search_query, case=False, na=False) |
            (news['site'].str.contains(search_query, case=False, na=False) if 'site' in news.columns else False)
        ]
    else:
        filtered_news = news
    
    # Display article count
    st.markdown(f"**{len(filtered_news)} articles found**")
    
    # Display articles
    for i, article in filtered_news.iterrows():
        with st.expander(f"{article.get('publishedDate', 'Unknown Date').strftime('%Y-%m-%d') if isinstance(article.get('publishedDate'), pd.Timestamp) else 'Unknown Date'} - {article.get('title', 'No Title')}"):
            st.markdown(f"**Source:** {article.get('site', 'Unknown')}")
            st.markdown(f"**Published:** {article.get('publishedDate', 'Unknown')}")
            
            if 'url' in article and article['url']:
                st.markdown(f"**Link:** [{article['url']}]({article['url']})")
            
            st.markdown("### Content")
            
            # Highlight search terms if provided
            if search_query and 'text' in article:
                # Simple highlighting with markdown
                text = article['text']
                # This is a simple approach - a more sophisticated approach would use regex
                highlighted_text = text.replace(search_query, f"**{search_query}**")
                st.markdown(highlighted_text)
            else:
                st.markdown(article.get('text', 'No content available'))
            
            # Display sentiment if available
            if 'sentiment' in article:
                sentiment = article['sentiment']
                if isinstance(sentiment, (int, float)):
                    color = "green" if sentiment > 0 else "red" if sentiment < 0 else "gray"
                    st.markdown(f"**Sentiment:** <span style='color:{color}'>{sentiment:.2f}</span>", unsafe_allow_html=True)

def display_transcript_data(ticker):
    """Display earnings call transcripts with enhanced analysis."""
    transcripts = load_earnings_transcripts(ticker)
    
    if transcripts is None or transcripts.empty:
        st.warning(f"No earnings call transcripts found for {ticker}")
        return
    
    # Sort by date if available
    if 'date' in transcripts.columns:
        transcripts['date'] = pd.to_datetime(transcripts['date'])
        transcripts = transcripts.sort_values('date', ascending=False)
    
    # Create selection interface
    if 'quarter' in transcripts.columns and 'year' in transcripts.columns:
        # Create labels for selection
        transcript_labels = [
            f"Q{row['quarter']} {row['year']}" 
            for _, row in transcripts.iterrows()
        ]
    else:
        # Fallback labels
        transcript_labels = [f"Transcript {i+1}" for i in range(len(transcripts))]
    
    selected_transcript_idx = st.selectbox(
        "Select Earnings Call",
        range(len(transcript_labels)),
        format_func=lambda x: transcript_labels[x]
    )
    
    # Display selected transcript
    if not transcripts.empty:
        transcript = transcripts.iloc[selected_transcript_idx]
        
        # Create a card for the transcript metadata
        with card("Transcript Information"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if 'quarter' in transcript and 'year' in transcript:
                    metric_card("Quarter", f"Q{transcript['quarter']} {transcript['year']}")
                
            with col2:
                if 'date' in transcript:
                    metric_card("Date", transcript['date'].strftime('%Y-%m-%d') if isinstance(transcript['date'], pd.Timestamp) else transcript['date'])
            
            with col3:
                if 'ticker' in transcript:
                    metric_card("Ticker", transcript['ticker'])
        
        # Create interface for transcript content
        if 'content' in transcript and transcript['content']:
            # Add a search box for the transcript
            search_term = search_box("Search within transcript", key="transcript_search")
            
            content = transcript['content']
            
            with card("Transcript Content"):
                if search_term:
                    # Count occurrences
                    occurrences = content.lower().count(search_term.lower())
                    st.markdown(f"**{occurrences} occurrences found**")
                    
                    # Display segments with speaker identification, if available
                    if ":" in content and len(content) > 1000:  # Heuristic to detect speaker formatting
                        # Simple parsing to identify speakers
                        speakers = set(re.findall(r"^([A-Za-z\s.]+):", content, re.MULTILINE))
                        
                        if speakers:
                            # Filter speakers (exclude common false positives)
                            speakers = [s for s in speakers if len(s) > 2 and s.strip() not in ["Q", "A", "Question", "Answer"]]
                            
                            # Create tabs for different sections
                            tabs = ["Search Results", "Full Transcript", "Presentation", "Q&A"]
                            
                            selected_tab = st.radio("View", tabs, horizontal=True)
                            
                            if selected_tab == "Search Results":
                                # Find paragraphs containing the search term
                                paragraphs = content.split('\n\n')
                                matching_paragraphs = [p for p in paragraphs if search_term.lower() in p.lower()]
                                
                                if matching_paragraphs:
                                    for paragraph in matching_paragraphs:
                                        # Highlight the search term
                                        highlighted = re.sub(
                                            f"({re.escape(search_term)})",
                                            r"**\1**",
                                            paragraph,
                                            flags=re.IGNORECASE
                                        )
                                        st.markdown(highlighted)
                                        st.markdown("---")
                                else:
                                    st.warning("No paragraphs found containing the search term.")
                            
                            elif selected_tab == "Full Transcript":
                                # Highlight and show full transcript
                                highlighted_content = re.sub(
                                    f"({re.escape(search_term)})",
                                    r"**\1**",
                                    content,
                                    flags=re.IGNORECASE
                                )
                                
                                st.markdown(f"<div style='height: 500px; overflow-y: scroll;'>{highlighted_content}</div>", unsafe_allow_html=True)
                            
                            elif selected_tab == "Presentation":
                                # Extract and highlight presentation part
                                if "Question-and-Answer" in content:
                                    presentation = content.split("Question-and-Answer")[0]
                                elif "Q&A" in content:
                                    presentation = content.split("Q&A")[0]
                                else:
                                    # Heuristic: presentation is usually in the first third
                                    presentation = content[:len(content)//3]
                                
                                # Highlight search terms
                                highlighted_presentation = re.sub(
                                    f"({re.escape(search_term)})",
                                    r"**\1**",
                                    presentation,
                                    flags=re.IGNORECASE
                                )
                                
                                st.markdown(f"<div style='height: 500px; overflow-y: scroll;'>{highlighted_presentation}</div>", unsafe_allow_html=True)
                            
                            elif selected_tab == "Q&A":
                                # Extract and highlight Q&A part
                                if "Question-and-Answer" in content:
                                    qa = content.split("Question-and-Answer")[1]
                                elif "Q&A" in content:
                                    qa = content.split("Q&A")[1]
                                else:
                                    # Heuristic: Q&A is usually after the first third
                                    qa = content[len(content)//3:]
                                
                                # Highlight search terms
                                highlighted_qa = re.sub(
                                    f"({re.escape(search_term)})",
                                    r"**\1**",
                                    qa,
                                    flags=re.IGNORECASE
                                )
                                
                                st.markdown(f"<div style='height: 500px; overflow-y: scroll;'>{highlighted_qa}</div>", unsafe_allow_html=True)
                        else:
                            # No speakers identified, show highlighted transcript
                            highlighted_content = re.sub(
                                f"({re.escape(search_term)})",
                                r"**\1**",
                                content,
                                flags=re.IGNORECASE
                            )
                            
                            st.markdown(f"<div style='height: 500px; overflow-y: scroll;'>{highlighted_content}</div>", unsafe_allow_html=True)
                    else:
                        # Just show the highlighted content
                        highlighted_content = re.sub(
                            f"({re.escape(search_term)})",
                            r"**\1**",
                            content,
                            flags=re.IGNORECASE
                        )
                        
                        st.markdown(f"<div style='height: 500px; overflow-y: scroll;'>{highlighted_content}</div>", unsafe_allow_html=True)
                else:
                    # No search term - display content with tabs if speakers are detected
                    if ":" in content and len(content) > 1000:
                        # Identify speakers
                        speakers = set(re.findall(r"^([A-Za-z\s.]+):", content, re.MULTILINE))
                        
                        if speakers:
                            # Filter speakers
                            speakers = [s for s in speakers if len(s) > 2 and s.strip() not in ["Q", "A", "Question", "Answer"]]
                            
                            # Create tabs
                            tabs = ["Full Transcript", "Presentation", "Q&A"]
                            if speakers:
                                tabs.append("Speakers")
                            
                            selected_tab = st.radio("View", tabs, horizontal=True)
                            
                            if selected_tab == "Full Transcript":
                                st.markdown(f"<div style='height: 500px; overflow-y: scroll;'>{content}</div>", unsafe_allow_html=True)
                            
                            elif selected_tab == "Presentation":
                                # Extract presentation part
                                if "Question-and-Answer" in content:
                                    presentation = content.split("Question-and-Answer")[0]
                                elif "Q&A" in content:
                                    presentation = content.split("Q&A")[0]
                                else:
                                    presentation = content[:len(content)//3]
                                
                                st.markdown(f"<div style='height: 500px; overflow-y: scroll;'>{presentation}</div>", unsafe_allow_html=True)
                            
                            elif selected_tab == "Q&A":
                                # Extract Q&A part
                                if "Question-and-Answer" in content:
                                    qa = content.split("Question-and-Answer")[1]
                                elif "Q&A" in content:
                                    qa = content.split("Q&A")[1]
                                else:
                                    qa = content[len(content)//3:]
                                
                                st.markdown(f"<div style='height: 500px; overflow-y: scroll;'>{qa}</div>", unsafe_allow_html=True)
                            
                            elif selected_tab == "Speakers" and speakers:
                                st.subheader("Identified Speakers")
                                
                                for speaker in sorted(speakers):
                                    with st.expander(speaker):
                                        # Extract all lines from this speaker
                                        speaker_pattern = f"{re.escape(speaker)}:(.*?)(?=\n[A-Za-z\s.]+:|$)"
                                        speaker_lines = re.findall(speaker_pattern, content, re.DOTALL)
                                        
                                        if speaker_lines:
                                            speaker_text = "\n\n".join(line.strip() for line in speaker_lines)
                                            st.markdown(speaker_text)
                        else:
                            # No speakers identified, show full transcript
                            st.markdown(f"<div style='height: 500px; overflow-y: scroll;'>{content}</div>", unsafe_allow_html=True)
                    else:
                        # Just show the full content
                        st.markdown(f"<div style='height: 500px; overflow-y: scroll;'>{content}</div>", unsafe_allow_html=True)
            
            # Add transcript analysis section
            with st.expander("Transcript Analysis", expanded=False):
                with neon_spinner("Analyzing transcript..."):
                    # Perform simple analysis
                    word_count = len(content.split())
                    
                    # Extract key terms (simplified version)
                    important_terms = [
                        "revenue", "growth", "profit", "margin", "earnings",
                        "guidance", "outlook", "forecast", "increase", "decrease",
                        "challenge", "opportunity", "innovation", "technology",
                        "competition", "market", "customer", "product", "service"
                    ]
                    
                    # Count occurrences of important terms
                    term_counts = {}
                    for term in important_terms:
                        count = content.lower().count(term)
                        if count > 0:
                            term_counts[term] = count
                    
                    # Create a simple bar chart of key terms
                    if term_counts:
                        df = pd.DataFrame(list(term_counts.items()), columns=['Term', 'Count'])
                        df = df.sort_values('Count', ascending=False).head(10)
                        
                        fig = bar_chart(
                            df,
                            x='Term',
                            y='Count',
                            title="Key Terms Frequency"
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Display statistics
                    st.markdown(f"**Word Count:** {word_count:,} words")
                    
                    # Identify speakers with most content
                    if speakers:
                        speaker_content_length = {}
                        for speaker in speakers:
                            speaker_pattern = f"{re.escape(speaker)}:(.*?)(?=\n[A-Za-z\s.]+:|$)"
                            speaker_lines = re.findall(speaker_pattern, content, re.DOTALL)
                            
                            if speaker_lines:
                                speaker_text = " ".join(line.strip() for line in speaker_lines)
                                speaker_content_length[speaker] = len(speaker_text.split())
                        
                        # Display speaker statistics
                        if speaker_content_length:
                            st.markdown("### Speaker Participation")
                            
                            df = pd.DataFrame(list(speaker_content_length.items()), 
                                             columns=['Speaker', 'Words'])
                            df = df.sort_values('Words', ascending=False)
                            
                            fig = bar_chart(
                                df,
                                x='Speaker',
                                y='Words',
                                title="Speaker Word Count"
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No transcript content available")

# Run the app
if __name__ == "__main__":
    data_explorer()