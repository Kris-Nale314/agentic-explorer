"""
Enhanced data collection script for SignalStore

This module contains functions to collect and organize financial data
using the FMP API into the project's enhanced DataStore structure.
"""

import os
import json
import time
from datetime import datetime, timedelta
import pandas as pd
import requests
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TimeElapsedColumn

# Load environment variables
load_dotenv()
FMP_API_KEY = os.getenv("FMP_API_KEY")
BASE_URL = "https://financialmodelingprep.com/api/v3"
BASE_URL_V4 = "https://financialmodelingprep.com/api/v4"

# Initialize console
console = Console()

def ensure_datastore_structure():
    """Create the base SignalStore dataStore structure."""
    # Define base directories
    base_dirs = [
        "dataStore/companies",
        "dataStore/market",
        "dataStore/events",
        "dataStore/relationships",
        "dataStore/signals/cost_pressure",
        "dataStore/signals/revenue_vulnerability", 
        "dataStore/signals/market_environment"
    ]
    
    # Create directories
    for directory in base_dirs:
        os.makedirs(directory, exist_ok=True)
    
    console.log("DataStore structure created")

def fmp_request(endpoint, params=None, version="v3"):
    """Make a request to FMP API with error handling and rate limiting."""
    if params is None:
        params = {}
    
    params["apikey"] = FMP_API_KEY
    
    # Select base URL based on version
    base_url = BASE_URL if version == "v3" else BASE_URL_V4
    url = f"{base_url}/{endpoint}"
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        # Simple rate limiting
        time.sleep(0.5)
        
        return response.json()
    except requests.exceptions.RequestException as e:
        console.log(f"Error in API request to {endpoint}: {e}")
        return None

# Company data collection functions
def collect_company_profile(ticker):
    """Collect and save company profile data."""
    console.log(f"Collecting profile data for {ticker}")
    
    data = fmp_request(f"profile/{ticker}")
    if data and len(data) > 0:
        # Save as JSON for human readability
        os.makedirs(f"dataStore/companies/{ticker}", exist_ok=True)
        with open(f"dataStore/companies/{ticker}/profile.json", "w") as f:
            json.dump(data[0], f, indent=2)
        
        console.log(f"Profile data saved for {ticker}")
        return True
    return False

def collect_company_financials(ticker, years=3):
    """Collect and save company financial statements."""
    console.log(f"Collecting financial data for {ticker}")
    
    # Define statement types to collect
    statement_types = {
        "income-statement": "Income Statement",
        "balance-sheet-statement": "Balance Sheet",
        "cash-flow-statement": "Cash Flow",
        "key-metrics": "Key Metrics",
        "ratios": "Financial Ratios"
    }
    
    # Create DataFrame to store all financial data
    all_financials = pd.DataFrame()
    
    for endpoint, name in statement_types.items():
        # Collect quarterly data
        quarterly = fmp_request(f"{endpoint}/{ticker}", {"period": "quarter", "limit": years * 4})
        
        if quarterly:
            # Convert to DataFrame
            df = pd.DataFrame(quarterly)
            df['statement_type'] = name
            df['period_type'] = 'quarterly'
            
            # Append to main DataFrame
            all_financials = pd.concat([all_financials, df])
        
        # Collect annual data
        annual = fmp_request(f"{endpoint}/{ticker}", {"limit": years})
        
        if annual:
            # Convert to DataFrame
            df = pd.DataFrame(annual)
            df['statement_type'] = name
            df['period_type'] = 'annual'
            
            # Append to main DataFrame
            all_financials = pd.concat([all_financials, df])
    
    # Save all financial data as parquet file
    if not all_financials.empty:
        os.makedirs(f"dataStore/companies/{ticker}", exist_ok=True)
        all_financials.to_parquet(f"dataStore/companies/{ticker}/financials.parquet", engine='pyarrow')
        console.log(f"Financial data saved for {ticker}")
        return True
    
    return False

def collect_historical_prices(ticker, years=3):
    """Collect and save historical stock prices."""
    console.log(f"Collecting price data for {ticker}")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * years)
    
    data = fmp_request(f"historical-price-full/{ticker}", {
        "from": start_date.strftime("%Y-%m-%d"),
        "to": end_date.strftime("%Y-%m-%d")
    })
    
    if data and "historical" in data:
        # Convert to DataFrame
        df = pd.DataFrame(data["historical"])
        df['ticker'] = ticker
        
        # Save as parquet file
        os.makedirs(f"dataStore/companies/{ticker}", exist_ok=True)
        df.to_parquet(f"dataStore/companies/{ticker}/prices.parquet", engine='pyarrow')
        
        console.log(f"Price data saved for {ticker}")
        return True
    
    return False

def collect_earnings_data(ticker, quarters=12):
    """Collect earnings history and call transcripts."""
    console.log(f"Collecting earnings data for {ticker}")
    
    # Collect earnings history
    earnings_history = fmp_request(f"historical/earning_calendar/{ticker}", {"limit": quarters})
    
    if earnings_history:
        # Convert to DataFrame
        df = pd.DataFrame(earnings_history)
        
        # Save as parquet file
        os.makedirs(f"dataStore/companies/{ticker}", exist_ok=True)
        df.to_parquet(f"dataStore/companies/{ticker}/earnings.parquet", engine='pyarrow')
    
    # Collect earnings call transcripts
    transcripts = []
    
    for i in range(min(quarters, 12)):  # Limit to reasonable number
        transcript = fmp_request(f"earning_call_transcript/{ticker}", {"quarter": i + 1})
        
        if transcript and len(transcript) > 0:
            # Extract transcript data
            transcripts.append({
                'ticker': ticker,
                'quarter': transcript[0].get('quarter'),
                'year': transcript[0].get('year'),
                'date': transcript[0].get('date'),
                'content': transcript[0].get('content', '')
            })
    
    if transcripts:
        # Convert to DataFrame
        df = pd.DataFrame(transcripts)
        
        # Save as parquet file
        df.to_parquet(f"dataStore/companies/{ticker}/transcripts.parquet", engine='pyarrow')
    
    console.log(f"Earnings data saved for {ticker}")
    return True

def collect_sec_filings(ticker, years=3):
    """Collect SEC filing metadata."""
    console.log(f"Collecting SEC filing data for {ticker}")
    
    # Get filing metadata
    filings = fmp_request(f"sec_filings/{ticker}", {"limit": years * 20})  # Approximation
    
    if filings:
        # Convert to DataFrame
        df = pd.DataFrame(filings)
        
        # Save as parquet file
        os.makedirs(f"dataStore/companies/{ticker}", exist_ok=True)
        df.to_parquet(f"dataStore/companies/{ticker}/filings.parquet", engine='pyarrow')
        
        console.log(f"SEC filing data saved for {ticker}")
        return True
    
    return False

def collect_company_news(ticker, limit=100):
    """Collect company news articles."""
    console.log(f"Collecting news data for {ticker}")
    
    # Get news articles
    news = fmp_request("stock_news", {"tickers": ticker, "limit": limit})
    
    if news:
        # Convert to DataFrame
        df = pd.DataFrame(news)
        
        # Save as parquet file
        os.makedirs(f"dataStore/companies/{ticker}", exist_ok=True)
        df.to_parquet(f"dataStore/companies/{ticker}/news.parquet", engine='pyarrow')
        
        console.log(f"News data saved for {ticker}")
        return True
    
    return False

# Market-wide data collection functions
def collect_economic_indicators(years=3):
    """Collect economic indicators."""
    console.log("Collecting economic indicators")
    
    # Define indicators to collect
    indicators = [
        "GDP", "realGDP", "nominalPotentialGDP", "realGDPPerCapita", 
        "federalFunds", "CPI", "inflationRate", "inflation", 
        "retailSales", "consumerSentiment", "durableGoods", 
        "unemploymentRate", "totalNonfarmPayroll", "initialClaims", 
        "industrialProductionTotalIndex", "newPrivatelyOwnedHousingUnitsStartedTotalUnits", 
        "totalVehicleSales", "retailMoneyFunds", "smoothedUSRecessionProbabilities"
    ]
    
    # Collect data for each indicator
    all_data = pd.DataFrame()
    
    for indicator in indicators:
        data = fmp_request(f"economic/{indicator}", {"limit": years * 12})  # Monthly data approximation
        
        if data:
            # Convert to DataFrame
            df = pd.DataFrame(data)
            df['indicator'] = indicator
            
            # Append to main DataFrame
            all_data = pd.concat([all_data, df])
    
    # Save as parquet file
    if not all_data.empty:
        os.makedirs("dataStore/market", exist_ok=True)
        all_data.to_parquet("dataStore/market/economic.parquet", engine='pyarrow')
        
        console.log("Economic indicators saved")
        return True
    
    return False

def collect_treasury_rates(years=3):
    """Collect treasury rates."""
    console.log("Collecting treasury rates")
    
    # Get treasury rates
    data = fmp_request("treasury", {"limit": years * 250})  # Daily data approximation
    
    if data:
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Save as parquet file
        os.makedirs("dataStore/market", exist_ok=True)
        df.to_parquet("dataStore/market/treasury.parquet", engine='pyarrow')
        
        console.log("Treasury rates saved")
        return True
    
    return False

def collect_market_indexes(years=3):
    """Collect market index data."""
    console.log("Collecting market index data")
    
    # Define indexes to collect
    indexes = ["^GSPC", "^DJI", "^IXIC"]  # S&P 500, Dow Jones, NASDAQ
    
    # Collect data for each index
    all_data = pd.DataFrame()
    
    for index_symbol in indexes:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * years)
        
        data = fmp_request(f"historical-price-full/{index_symbol}", {
            "from": start_date.strftime("%Y-%m-%d"),
            "to": end_date.strftime("%Y-%m-%d")
        })
        
        if data and "historical" in data:
            # Convert to DataFrame
            df = pd.DataFrame(data["historical"])
            df['symbol'] = index_symbol
            
            # Append to main DataFrame
            all_data = pd.concat([all_data, df])
    
    # Save as parquet file
    if not all_data.empty:
        os.makedirs("dataStore/market", exist_ok=True)
        all_data.to_parquet("dataStore/market/indices.parquet", engine='pyarrow')
        
        console.log("Market index data saved")
        return True
    
    return False

def collect_sector_pe_ratios():
    """Collect sector P/E ratios."""
    console.log("Collecting sector P/E ratios")
    
    # Get sector P/E ratios
    data = fmp_request("sector_price_earning_ratio", version="v4")
    
    if data:
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Save as parquet file
        os.makedirs("dataStore/market", exist_ok=True)
        df.to_parquet("dataStore/market/sector_pe.parquet", engine='pyarrow')
        
        console.log("Sector P/E ratios saved")
        return True
    
    return False

# Event-based data collection functions
def collect_material_events(days=90):
    """Collect 8-K filings (material events) across companies."""
    console.log("Collecting material events (8-K filings)")
    
    # Get RSS feed of 8-K filings
    data = fmp_request("rss_feed_8k", version="v4")
    
    if data:
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Save as parquet file
        os.makedirs("dataStore/events", exist_ok=True)
        df.to_parquet("dataStore/events/material_events.parquet", engine='pyarrow')
        
        console.log("Material events saved")
        return True
    
    return False

def collect_insider_trading(limit=1000):
    """Collect insider trading data across companies."""
    console.log("Collecting insider trading data")
    
    # Get insider trading data
    data = fmp_request("insider-trading", {"limit": limit})
    
    if data:
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Save as parquet file
        os.makedirs("dataStore/events", exist_ok=True)
        df.to_parquet("dataStore/events/insider_trading.parquet", engine='pyarrow')
        
        console.log("Insider trading data saved")
        return True
    
    return False

# Relationship data collection functions
def collect_peer_relationships(tickers):
    """Collect peer relationship data for a list of tickers."""
    console.log("Collecting peer relationship data")
    
    # Collect peer data for each ticker
    all_peers = pd.DataFrame()
    
    for ticker in tickers:
        peers = fmp_request(f"stock_peers?symbol={ticker}")
        
        if peers:
            # Convert to DataFrame
            df = pd.DataFrame(peers)
            df['source_ticker'] = ticker
            
            # Append to main DataFrame
            all_peers = pd.concat([all_peers, df])
    
    # Save as parquet file
    if not all_peers.empty:
        os.makedirs("dataStore/relationships", exist_ok=True)
        all_peers.to_parquet("dataStore/relationships/peers.parquet", engine='pyarrow')
        
        console.log("Peer relationship data saved")
        return True
    
    return False

def collect_supply_chain_relationships(tickers):
    """Collect supply chain relationship data for a list of tickers."""
    console.log("Collecting supply chain relationship data")
    
    # Collect supply chain data for each ticker
    all_relationships = pd.DataFrame()
    
    for ticker in tickers:
        relationships = fmp_request(f"stock_supply_chain/{ticker}")
        
        if relationships:
            # Convert to DataFrame
            df = pd.DataFrame(relationships)
            df['source_ticker'] = ticker
            
            # Append to main DataFrame
            all_relationships = pd.concat([all_relationships, df])
    
    # Save as parquet file
    if not all_relationships.empty:
        os.makedirs("dataStore/relationships", exist_ok=True)
        all_relationships.to_parquet("dataStore/relationships/supply_chain.parquet", engine='pyarrow')
        
        console.log("Supply chain relationship data saved")
        return True
    
    return False

# Main collection functions
def collect_company_data(ticker, years=3):
    """Collect all data for a specific company."""
    console.log(f"Starting data collection for {ticker}")
    
    # Collect company-specific data
    collect_company_profile(ticker)
    collect_company_financials(ticker, years)
    collect_historical_prices(ticker, years)
    collect_earnings_data(ticker, years * 4)  # Quarterly data
    collect_sec_filings(ticker, years)
    collect_company_news(ticker, 100)
    
    console.log(f"Completed data collection for {ticker}")
    return True

def collect_market_data(years=3):
    """Collect market-wide data."""
    console.log("Starting market data collection")
    
    # Collect market data
    collect_economic_indicators(years)
    collect_treasury_rates(years)
    collect_market_indexes(years)
    collect_sector_pe_ratios()
    
    console.log("Completed market data collection")
    return True

def collect_event_data():
    """Collect event-based data."""
    console.log("Starting event data collection")
    
    # Collect event data
    collect_material_events()
    collect_insider_trading()
    
    console.log("Completed event data collection")
    return True

def collect_relationship_data(tickers):
    """Collect relationship data for a list of tickers."""
    console.log("Starting relationship data collection")
    
    # Collect relationship data
    collect_peer_relationships(tickers)
    collect_supply_chain_relationships(tickers)
    
    console.log("Completed relationship data collection")
    return True

def collect_all_data(tickers, years=3):
    """Collect all data for the SignalStore POC."""
    console.log("Starting comprehensive data collection")
    
    # Ensure data structure exists
    ensure_datastore_structure()
    
    # Collect company-specific data
    for ticker in tickers:
        collect_company_data(ticker, years)
    
    # Collect market-wide data
    collect_market_data(years)
    
    # Collect event-based data
    collect_event_data()
    
    # Collect relationship data
    collect_relationship_data(tickers)
    
    console.log("Completed comprehensive data collection")
    return True

if __name__ == "__main__":
    # Example usage
    target_companies = ["DELL", "NVDA", "TSLA", "ACN"]
    collect_all_data(target_companies, years=3)