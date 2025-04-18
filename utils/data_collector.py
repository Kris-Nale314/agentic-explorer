"""
DataStore Population Scripts for Agentic Explorer

This module contains functions to collect and organize financial data
from FMP API into the project's DataStore structure.
"""

import os
import json
import time
from datetime import datetime, timedelta
import pandas as pd
import requests
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TimeElapsedColumn, SpinnerColumn
from tqdm import tqdm

# Import project structure utilities
from project_structure import get_project_root, get_data_path

# Load environment variables
load_dotenv()
FMP_API_KEY = os.getenv("FMP_API_KEY")
BASE_URL = "https://financialmodelingprep.com/api/v3"

# Initialize Rich console
console = Console()

def ensure_directories(ticker):
    """Create necessary directories for a ticker if they don't exist."""
    base_dir = get_data_path(ticker)
    
    # Create main directories
    directories = [
        base_dir,
        base_dir / "financials",
        base_dir / "filings" / "full_texts",
        base_dir / "earnings" / "transcripts",
        base_dir / "news" / "articles"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    # Also ensure market_data directory exists
    get_data_path("market_data").mkdir(parents=True, exist_ok=True)
    
    return base_dir

def fmp_request(endpoint, params=None):
    """Make a request to FMP API with error handling and rate limiting."""
    if params is None:
        params = {}
    
    params["apikey"] = FMP_API_KEY
    url = f"{BASE_URL}/{endpoint}"
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        # Simple rate limiting
        time.sleep(0.5)
        
        return response.json()
    except requests.exceptions.RequestException as e:
        console.log(f"Error in API request to {endpoint}: {e}")
        return None

def fetch_company_profile(ticker):
    """Fetch and save company profile information."""
    console.log(f"Fetching company profile for {ticker}")
    
    data = fmp_request(f"profile/{ticker}")
    if not data:
        return False
    
    profile_path = get_data_path(ticker) / "profile.json"
    with open(profile_path, "w") as f:
        json.dump(data, f, indent=2)
    
    console.log(f"Saved company profile for {ticker}")
    return True

def fetch_financial_statements(ticker, years=5):
    """Fetch and save financial statements."""
    statement_types = {
        "income-statement": "income",
        "balance-sheet-statement": "balance",
        "cash-flow-statement": "cashflow"
    }
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task(f"Fetching financial statements for {ticker}", total=len(statement_types) * 2)
        
        for endpoint, name in statement_types.items():
            # Fetch quarterly statements
            quarterly_data = fmp_request(f"{endpoint}/{ticker}", {"period": "quarter", "limit": years * 4})
            if quarterly_data:
                quarterly_path = get_data_path(ticker) / "financials" / f"quarterly_{name}.json"
                with open(quarterly_path, "w") as f:
                    json.dump(quarterly_data, f, indent=2)
            progress.update(task, advance=1)
                
            # Fetch annual statements
            annual_data = fmp_request(f"{endpoint}/{ticker}", {"limit": years})
            if annual_data:
                annual_path = get_data_path(ticker) / "financials" / f"annual_{name}.json"
                with open(annual_path, "w") as f:
                    json.dump(annual_data, f, indent=2)
            progress.update(task, advance=1)
    
    console.log(f"Financial statements saved for {ticker}")
    return True

def fetch_historical_prices(ticker, years=5):
    """Fetch and save historical stock prices."""
    console.log(f"Fetching historical prices for {ticker}")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * years)
    
    data = fmp_request(f"historical-price-full/{ticker}", {
        "from": start_date.strftime("%Y-%m-%d"),
        "to": end_date.strftime("%Y-%m-%d")
    })
    
    if not data or "historical" not in data:
        console.log(f"No historical data found for {ticker}")
        return False
    
    # Convert to DataFrame for easier processing
    df = pd.DataFrame(data["historical"])
    
    # Save to company directory for individual access
    prices_path = get_data_path(ticker) / "historical_prices.csv"
    df.to_csv(prices_path, index=False)
    
    # Also append to the combined market data file
    market_data_path = get_data_path("market_data") / "daily_prices.csv"
    
    # Add ticker column
    df["ticker"] = ticker
    
    # If the combined file exists, append; otherwise create new
    if market_data_path.exists():
        # Read existing data
        existing_data = pd.read_csv(market_data_path)
        
        # Remove any existing data for this ticker
        existing_data = existing_data[existing_data.ticker != ticker]
        
        # Append new data
        updated_data = pd.concat([existing_data, df])
        updated_data.to_csv(market_data_path, index=False)
    else:
        df.to_csv(market_data_path, index=False)
    
    console.log(f"Historical prices saved for {ticker}")
    return True

def fetch_sec_filings(ticker, years=5):
    """Fetch and save SEC filings metadata and important full texts."""
    console.log(f"Fetching SEC filings for {ticker}")
    
    # Get all filings
    filings = fmp_request(f"sec_filings/{ticker}", {"limit": 500})
    if not filings:
        return False
    
    # Organize by type
    filing_types = {"10-K": [], "10-Q": [], "8-K": []}
    
    for filing in filings:
        if filing["type"] in filing_types:
            filing_types[filing["type"]].append(filing)
    
    # Save metadata by type
    for filing_type, items in filing_types.items():
        clean_type = filing_type.replace("-", "")
        with open(get_data_path(ticker) / "filings" / f"{clean_type}_filings.json", "w") as f:
            json.dump(items, f, indent=2)
    
    # For important filings (10-K, 10-Q), fetch the full text for the most recent ones
    important_filings = []
    for filing_type in ["10-K", "10-Q"]:
        for filing in filing_types[filing_type][:years]:
            important_filings.append((filing_type, filing))
    
    # Limited to the most recent years of each important filing
    console.log(f"Downloading {len(important_filings)} full text filings for {ticker}")
    
    for filing_type, filing in tqdm(important_filings, desc="Downloading filings"):
        try:
            # Extract year and quarter if applicable
            filing_date = filing.get("fillingDate", "")
            year = "unknown"
            
            # Handle different date formats
            if filing_date:
                # Strip any time component if present
                if " " in filing_date:
                    filing_date = filing_date.split(" ")[0]
                
                # Extract year safely
                date_parts = filing_date.split("-")
                if len(date_parts) >= 1 and len(date_parts[0]) == 4:
                    year = date_parts[0]
            
            if filing_type == "10-Q":
                # Try to determine which quarter
                quarter = "Q?"
                
                try:
                    if filing_date:
                        # Parse the date safely
                        date_obj = datetime.strptime(filing_date, "%Y-%m-%d")
                        month = date_obj.month
                        
                        if month <= 3:
                            quarter = "Q1"
                        elif month <= 6:
                            quarter = "Q2"
                        elif month <= 9:
                            quarter = "Q3"
                        else:
                            quarter = "Q4"
                except ValueError as e:
                    console.log(f"Warning: Could not parse date '{filing_date}': {e}")
                
                filename = f"{clean_type}_{year}{quarter}.txt"
            else:
                filename = f"{clean_type}_{year}.txt"
            
            # Try to get the document text
            if "finalLink" in filing:
                try:
                    response = requests.get(filing["finalLink"], timeout=30)
                    if response.status_code == 200:
                        filing_text = response.text
                        with open(get_data_path(ticker) / "filings" / "full_texts" / filename, "w", encoding="utf-8") as f:
                            f.write(filing_text)
                except Exception as e:
                    console.log(f"Error downloading {filing_type} for {ticker}: {e}")
        except Exception as e:
            console.log(f"Error processing {filing_type} for {ticker}: {e}")
            continue
    
    console.log(f"SEC filings saved for {ticker}")
    return True

def fetch_earnings_data(ticker, quarters=8):
    """Fetch and save earnings data and transcripts."""
    console.log(f"Fetching earnings data for {ticker}")
    
    # Get earnings history
    earnings_history = fmp_request(f"historical/earning_calendar/{ticker}", {"limit": quarters})
    if earnings_history:
        with open(get_data_path(ticker) / "earnings" / "earnings_history.json", "w") as f:
            json.dump(earnings_history, f, indent=2)
    
    # Get earnings estimates
    earnings_estimates = fmp_request(f"earnings-calendar-confirmed/{ticker}")
    if earnings_estimates:
        with open(get_data_path(ticker) / "earnings" / "earnings_estimates.json", "w") as f:
            json.dump(earnings_estimates, f, indent=2)
    
    # Get earnings call transcripts for recent quarters
    for i in range(quarters):
        # Try to get transcript
        transcript = fmp_request(f"earning_call_transcript/{ticker}", {"quarter": i + 1})
        if transcript and len(transcript) > 0:
            # Extract quarter and year
            quarter = transcript[0].get("quarter", "Q?")
            year = transcript[0].get("year", "YYYY")
            
            filename = f"{ticker}_{year}{quarter}.txt"
            with open(get_data_path(ticker) / "earnings" / "transcripts" / filename, "w", encoding="utf-8") as f:
                f.write(transcript[0].get("content", "No transcript content available"))
    
    console.log(f"Earnings data saved for {ticker}")
    return True

def fetch_news_and_sentiment(ticker, articles_limit=100):
    """Fetch and save news articles and sentiment data."""
    console.log(f"Fetching news and sentiment for {ticker}")
    
    # Get news articles
    news = fmp_request("stock_news", {"tickers": ticker, "limit": articles_limit})
    if news:
        # Save metadata
        with open(get_data_path(ticker) / "news" / "news_metadata.json", "w") as f:
            json.dump(news, f, indent=2)
        
        # Save individual articles
        for i, article in enumerate(news):
            # Create a filename based on date and index
            date_str = article.get("publishedDate", "").split(" ")[0].replace("-", "")
            filename = f"{ticker}_{date_str}_{i:03d}.txt"
            
            # Save article content
            article_path = get_data_path(ticker) / "news" / "articles" / filename
            with open(article_path, "w", encoding="utf-8") as f:
                f.write(f"Title: {article.get('title', 'No title')}\n")
                f.write(f"Date: {article.get('publishedDate', 'No date')}\n")
                f.write(f"Source: {article.get('site', 'Unknown source')}\n")
                f.write(f"URL: {article.get('url', 'No URL')}\n\n")
                f.write(article.get("text", "No article content available"))
    
    # Get sentiment data
    sentiment = fmp_request(f"stock-news-sentiments/{ticker}", {"limit": 500})
    if sentiment:
        # Process sentiment data into a timeline
        sentiment_timeline = {}
        for item in sentiment:
            date = item.get("publishedDate", "").split(" ")[0]
            if date in sentiment_timeline:
                sentiment_timeline[date].append({
                    "title": item.get("title", ""),
                    "sentiment": item.get("sentiment", ""),
                    "sentimentScore": item.get("sentimentScore", 0)
                })
            else:
                sentiment_timeline[date] = [{
                    "title": item.get("title", ""),
                    "sentiment": item.get("sentiment", ""),
                    "sentimentScore": item.get("sentimentScore", 0)
                }]
        
        # Save sentiment timeline
        with open(get_data_path(ticker) / "news" / "sentiment_timeline.json", "w") as f:
            json.dump(sentiment_timeline, f, indent=2)
    
    console.log(f"News and sentiment saved for {ticker}")
    return True

def fetch_market_indices(years=5):
    """Fetch and save market indices data."""
    console.log("Fetching market indices data")
    
    indices = ["^GSPC", "^DJI", "^IXIC"]  # S&P 500, Dow Jones, NASDAQ
    index_names = ["S&P 500", "Dow Jones", "NASDAQ"]
    
    all_data = pd.DataFrame()
    
    for idx, index_symbol in enumerate(indices):
        console.log(f"Fetching data for {index_names[idx]} ({index_symbol})")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * years)
        
        data = fmp_request(f"historical-price-full/{index_symbol}", {
            "from": start_date.strftime("%Y-%m-%d"),
            "to": end_date.strftime("%Y-%m-%d"),
            "serietype": "line"
        })
        
        if not data or "historical" not in data:
            console.log(f"No data found for {index_symbol}")
            continue
        
        df = pd.DataFrame(data["historical"])
        df["index"] = index_names[idx]
        
        all_data = pd.concat([all_data, df])
    
    if not all_data.empty:
        all_data.to_csv(get_data_path("market_data") / "index_data.csv", index=False)
        console.log("Market indices data saved")
    
    return True

def fetch_all_data(ticker, years=5):
    """Fetch all data for a ticker."""
    console.log(f"Starting data collection for {ticker}", style="bold green")
    
    # Ensure directories exist
    ensure_directories(ticker)
    
    # Fetch all data types
    fetch_company_profile(ticker)
    fetch_financial_statements(ticker, years)
    fetch_historical_prices(ticker, years)
    fetch_sec_filings(ticker, years)
    fetch_earnings_data(ticker, min(8, years * 4))  # 4 quarters per year
    fetch_news_and_sentiment(ticker, 100)
    
    console.log(f"Completed data collection for {ticker}", style="bold green")
    return True

def fetch_data_for_companies(tickers, years=5):
    """Fetch data for multiple companies and market indices."""
    console.log("Starting data collection process", style="bold blue")
    
    # First fetch market indices for context
    fetch_market_indices(years)
    
    # Then fetch data for each company
    for ticker in tickers:
        fetch_all_data(ticker, years)
    
    console.log("Data collection complete!", style="bold green")
    return True

if __name__ == "__main__":
    # Example usage
    tickers = ["NVDA", "MSFT", "AAPL", "TSLA", "AMZN"]
    fetch_data_for_companies(tickers, years=5)