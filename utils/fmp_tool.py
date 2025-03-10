"""
Financial Modeling Prep API tool for Agentic Explorer.

This module provides functions to retrieve and process financial data
from the Financial Modeling Prep API for use in testing RAG capabilities.
"""

import os
import json
import time
import logging
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FMPTool:
    """Tool for accessing Financial Modeling Prep API data."""
    
    def __init__(self, api_key: str):
        """
        Initialize the FMP API tool.
        
        Args:
            api_key: FMP API key
        """
        if not api_key:
            raise ValueError("API key is required")
        
        self.api_key = api_key
        self.base_url = "https://financialmodelingprep.com/api/v3"
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        logger.info("Initialized FMPTool")
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Make a request to the FMP API.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            API response as dictionary
        """
        # Initialize parameters
        request_params = params.copy() if params else {}
        
        # Add API key
        request_params["apikey"] = self.api_key
        
        # Construct URL
        url = f"{self.base_url}/{endpoint}"
        
        # Make request
        try:
            response = requests.get(url, params=request_params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error making request to {url}: {e}")
            raise
    
    def get_company_profile(self, symbol: str) -> Dict[str, Any]:
        """
        Get company profile information.
        
        Args:
            symbol: Company stock symbol
            
        Returns:
            Company profile data
        """
        logger.info(f"Getting company profile for {symbol}")
        
        try:
            # Get company profile
            data = self._make_request(f"profile/{symbol}")
            
            if not data or len(data) == 0:
                logger.warning(f"No profile data found for {symbol}")
                return {}
            
            return data[0]
            
        except Exception as e:
            logger.error(f"Error getting company profile for {symbol}: {e}")
            raise
    
    def get_company_metrics(self, symbol: str) -> Dict[str, Any]:
        """
        Get company financial metrics.
        
        Args:
            symbol: Company stock symbol
            
        Returns:
            Financial metrics data
        """
        logger.info(f"Getting financial metrics for {symbol}")
        
        try:
            # Get quarterly metrics
            quarterly_data = self._make_request(f"key-metrics-ttm/{symbol}")
            
            # Get historical metrics (last 4 quarters)
            historical_data = self._make_request(f"key-metrics/{symbol}", {"period": "quarter", "limit": 4})
            
            # Combine data
            metrics = {
                "symbol": symbol,
                "currentMetrics": quarterly_data[0] if quarterly_data else {},
                "quarterlyMetrics": historical_data if historical_data else []
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting financial metrics for {symbol}: {e}")
            raise
    
    def get_earnings_call_transcripts(self, symbol: str, limit: int = 1) -> List[Dict[str, Any]]:
        """
        Get earnings call transcripts.
        
        Args:
            symbol: Company stock symbol
            limit: Maximum number of transcripts to retrieve
            
        Returns:
            List of transcript data
        """
        logger.info(f"Getting earnings call transcripts for {symbol} (limit: {limit})")
        
        try:
            # Get transcript list
            transcript_list = self._make_request(f"earning_call_transcript/{symbol}", {"quarter": "0"})
            
            if not transcript_list:
                logger.warning(f"No transcripts found for {symbol}")
                return []
            
            # Take only the requested number of transcripts
            transcripts = []
            for i, info in enumerate(transcript_list[:limit]):
                # Get full transcript
                try:
                    quarter = info.get("quarter", "")
                    year = info.get("year", "")
                    
                    if quarter and year:
                        full_transcript = self._make_request(f"earning_call_transcript/{symbol}", {
                            "quarter": quarter,
                            "year": year
                        })
                        
                        if full_transcript and len(full_transcript) > 0:
                            transcript_data = {
                                "symbol": symbol,
                                "date": full_transcript[0].get("date", ""),
                                "quarter": quarter,
                                "year": year,
                                "content": full_transcript[0].get("content", "")
                            }
                            transcripts.append(transcript_data)
                    
                    # Add a small delay to avoid hitting rate limits
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.warning(f"Error getting transcript details: {e}")
            
            return transcripts
            
        except Exception as e:
            logger.error(f"Error getting transcripts for {symbol}: {e}")
            raise
    
    def get_company_news(self, symbol: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get company news articles.
        
        Args:
            symbol: Company stock symbol
            limit: Maximum number of news items to retrieve
            
        Returns:
            List of news data
        """
        logger.info(f"Getting news for {symbol} (limit: {limit})")
        
        try:
            # Get company news
            news_data = self._make_request(f"stock_news", {"tickers": symbol, "limit": limit})
            
            if not news_data:
                logger.warning(f"No news found for {symbol}")
                return []
            
            # Process and return news items
            processed_news = []
            for item in news_data:
                news_item = {
                    "symbol": symbol,
                    "title": item.get("title", ""),
                    "publishedDate": item.get("publishedDate", ""),
                    "site": item.get("site", ""),
                    "url": item.get("url", ""),
                    "content": item.get("text", "")
                }
                processed_news.append(news_item)
            
            return processed_news
            
        except Exception as e:
            logger.error(f"Error getting news for {symbol}: {e}")
            raise
    
    def save_company_dataset(self, symbol: str) -> str:
        """
        Generate and save a complete company dataset.
        
        Args:
            symbol: Company stock symbol
            
        Returns:
            Path to saved file
        """
        logger.info(f"Generating dataset for {symbol}")
        
        try:
            # Get company profile
            profile = self.get_company_profile(symbol)
            
            # Get financial metrics
            metrics = self.get_company_metrics(symbol)
            
            # Get earnings call transcripts (last 2 quarters)
            transcripts = self.get_earnings_call_transcripts(symbol, limit=2)
            
            # Get recent news
            news = self.get_company_news(symbol, limit=5)
            
            # Combine all data
            company_data = {
                "symbol": symbol,
                "profile": profile,
                "metrics": metrics,
                "earnings_calls": transcripts,
                "news": news,
                "generated_at": datetime.now().isoformat()
            }
            
            # Save to file
            file_path = os.path.join(self.data_dir, f"{symbol.lower()}_data.json")
            with open(file_path, 'w') as f:
                json.dump(company_data, f, indent=2)
            
            logger.info(f"Saved company dataset: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error generating dataset for {symbol}: {e}")
            raise
    
    def create_mixed_document(self, symbols: List[str], output_file: str = None, 
                            content_types: List[str] = None) -> str:
        """
        Create a mixed document combining data from multiple companies.
        
        Args:
            symbols: List of company symbols
            output_file: Output file path (generated if None)
            content_types: Types of content to include (default: earnings_calls)
            
        Returns:
            Path to saved file
        """
        logger.info(f"Creating mixed document for: {symbols}")
        
        # Default output file
        if not output_file:
            symbols_str = '_'.join(symbols).lower()
            output_file = os.path.join(self.data_dir, f"mixed_{symbols_str}.json")
        
        # Default content types
        content_types = content_types or ["earnings_calls"]
        
        # Collect data for each company
        company_data = {}
        for symbol in symbols:
            company_data[symbol] = {}
            
            # Get requested content types
            if "profile" in content_types:
                company_data[symbol]["profile"] = self.get_company_profile(symbol)
            
            if "metrics" in content_types:
                company_data[symbol]["metrics"] = self.get_company_metrics(symbol)
            
            if "earnings_calls" in content_types:
                company_data[symbol]["earnings_calls"] = self.get_earnings_call_transcripts(symbol, limit=1)
            
            if "news" in content_types:
                company_data[symbol]["news"] = self.get_company_news(symbol, limit=3)
        
        # Combine earnings call transcripts
        combined_text = ""
        if "earnings_calls" in content_types:
            for symbol in symbols:
                for call in company_data[symbol].get("earnings_calls", []):
                    combined_text += f"# {symbol} Earnings Call - {call.get('date', 'Unknown')}\n\n"
                    combined_text += call.get("content", "") + "\n\n"
        
        # Create mixed document
        mixed_doc = {
            "companies": symbols,
            "content_types": content_types,
            "data": company_data,
            "combined_text": combined_text,
            "generated_at": datetime.now().isoformat()
        }
        
        # Save to file
        with open(output_file, 'w') as f:
            json.dump(mixed_doc, f, indent=2)
        
        logger.info(f"Saved mixed document: {output_file}")
        return output_file