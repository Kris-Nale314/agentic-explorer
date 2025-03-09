# utils/fmp_tool.py
import os
import json
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import logging

# Configure logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

class FMPTool:
    """
    A tool to interact with the Financial Modeling Prep (FMP) API.

    Provides methods to fetch company profiles, financial metrics, earnings call transcripts,
    news, and sentiment data.  Requires an FMP API key to be set as an environment variable
    'FMP_API_KEY' or passed to the constructor.

    Rate limits are handled with a basic delay, but more robust rate limiting may be needed
    for production use.
    """
    def __init__(self, api_key: str = None):
        """
        Initialize the FMP API tool with an API key.

        Args:
            api_key (str, optional): Your Financial Modeling Prep API key.
                                     If not provided, it will be read from the 'FMP_API_KEY'
                                     environment variable. Defaults to None.

        Raises:
            ValueError: If the FMP API key is not provided and not found in environment variables.
        """
        self.api_key = api_key or os.environ.get('FMP_API_KEY')
        if not self.api_key:
            raise ValueError("FMP API key is required. Set it as the FMP_API_KEY environment variable or pass it to the constructor.")
        self.base_url = "https://financialmodelingprep.com/api/v3"

    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """
        Make a request to the FMP API endpoint.

        Handles API requests, error handling, and basic rate limiting.

        Args:
            endpoint (str): The API endpoint to call (e.g., 'profile/AAPL').
            params (Dict, optional): Query parameters to include in the request. Defaults to None.

        Returns:
            Dict: JSON response from the API as a Python dictionary.

        Raises:
            requests.exceptions.HTTPError: If the HTTP status code indicates an error.
            requests.exceptions.RequestException: For other request-related errors (timeout, connection error, etc.).
        """
        if params is None:
            params = {}
        params['apikey'] = self.api_key

        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP error calling {url}: {http_err}")
            raise http_err
        except requests.exceptions.RequestException as req_err:
            logging.error(f"Request error calling {url}: {req_err}")
            raise req_err
        finally:
            time.sleep(0.25)  # Basic rate limiting - delay after each request


    def get_company_profile(self, symbol: str) -> Dict:
        """
        Get company profile information from Financial Modeling Prep API.

        Fetches profile details for a given stock symbol, including company name, sector,
        industry, description, website, CEO, etc.

        Args:
            symbol (str): The stock ticker symbol of the company (e.g., 'AAPL').

        Returns:
            Dict: A dictionary containing company profile information.
                  Returns an empty dictionary if no profile is found or in case of API errors
                  (errors are already logged by _make_request).

        Raises:
            requests.exceptions.HTTPError: If the HTTP status code indicates an error.
            requests.exceptions.RequestException: For other request-related errors.

        Usage Example (from terminal):
        >>> python -c "from utils.fmp_tool import FMPTool; tool = FMPTool(); profile = tool.get_company_profile('AAPL'); import json; print(json.dumps(profile, indent=2))"
        """
        endpoint = f"profile/{symbol}"
        try:
            response = self._make_request(endpoint)
            return response[0] if response else {} # Return first profile or empty dict if no profile
        except Exception: # Let the caller handle specific exceptions if needed, but tool should not crash
            return {}


    def get_financial_metrics(self, symbol: str) -> Dict:
        """
        Get key financial metrics for a company from Financial Modeling Prep API.

        Fetches a range of financial metrics, ratios, and income/cash flow statement data
        for a given stock symbol.  Metrics are TTM (Trailing Twelve Months) where available.

        Args:
            symbol (str): The stock ticker symbol of the company (e.g., 'AAPL').

        Returns:
            Dict: A dictionary containing key financial metrics, ratios, and selected income/cashflow
                  statement items. Structure:
                  {
                      "ratios": Dict,
                      "metrics": Dict,
                      "income": {"revenue": float, "netIncome": float, ...},
                      "cashflow": {"freeCashFlow": float, "operatingCashFlow": float, ...}
                  }
                  Returns a dictionary with empty dictionaries if data is not available or in case of API errors
                  (errors are already logged by _make_request).

        Raises:
            requests.exceptions.HTTPError: If the HTTP status code indicates an error.
            requests.exceptions.RequestException: For other request-related errors.

        Usage Example (from terminal):
        >>> python -c "from utils.fmp_tool import FMPTool; tool = FMPTool(); metrics = tool.get_financial_metrics('AAPL'); import json; print(json.dumps(metrics, indent=2))"
        """
        try:
            # Get financial ratios
            ratios_endpoint = f"ratios-ttm/{symbol}"
            ratios_response = self._make_request(ratios_endpoint)
            ratios = ratios_response[0] if ratios_response else {}

            # Get key metrics
            metrics_endpoint = f"key-metrics-ttm/{symbol}"
            metrics_response = self._make_request(metrics_endpoint)
            metrics = metrics_response[0] if metrics_response else {}

            # Get income statement (limit=1 for latest)
            income_endpoint = f"income-statement/{symbol}?limit=1"
            income_response = self._make_request(income_endpoint)
            income_data = income_response[0] if income_response else {}
            income = {
                "revenue": income_data.get("revenue"),
                "netIncome": income_data.get("netIncome"),
                "grossProfit": income_data.get("grossProfit"),
                "operatingIncome": income_data.get("operatingIncome")
            }

            # Get cash flow statement (limit=1 for latest)
            cashflow_endpoint = f"cash-flow-statement/{symbol}?limit=1"
            cashflow_response = self._make_request(cashflow_endpoint)
            cashflow_data = cashflow_response[0] if cashflow_response else {}
            cashflow = {
                "freeCashFlow": cashflow_data.get("freeCashFlow"),
                "operatingCashFlow": cashflow_data.get("operatingCashFlow")
            }

            return {
                "ratios": ratios,
                "metrics": metrics,
                "income": income,
                "cashflow": cashflow
            }
        except Exception: # Let the caller handle specific exceptions if needed, but tool should not crash
            return { "ratios": {}, "metrics": {}, "income": {}, "cashflow": {}}


    def get_earnings_calls(self, symbol: str, limit: int = 3) -> List[Dict]:
        """
        Get the most recent earnings call transcripts for a company from Financial Modeling Prep API.

        Fetches earnings call transcripts, including date, quarter, year, and the transcript content.

        Args:
            symbol (str): The stock ticker symbol of the company (e.g., 'AAPL').
            limit (int, optional): The maximum number of transcripts to retrieve. Defaults to 3.

        Returns:
            List[Dict]: A list of dictionaries, where each dictionary represents an earnings call transcript
                         and contains keys: 'date', 'quarter', 'year', 'content'.
                         Returns an empty list if no transcripts are found or in case of API errors
                         (errors are already logged by _make_request).

        Raises:
            requests.exceptions.HTTPError: If the HTTP status code indicates an error.
            requests.exceptions.RequestException: For other request-related errors.

        Usage Example (from terminal):
        >>> python -c "from utils.fmp_tool import FMPTool; tool = FMPTool(); transcripts = tool.get_earnings_calls('AAPL', limit=2); import json; print(json.dumps(transcripts, indent=2))"
        """
        endpoint = f"earning_call_transcript/{symbol}?limit={limit}"
        try:
            transcripts = self._make_request(endpoint)
            # Format the transcript data
            formatted_transcripts = []
            for transcript in transcripts:
                formatted_transcripts.append({
                    "date": transcript.get("date"),
                    "quarter": transcript.get("quarter"),
                    "year": transcript.get("year"),
                    "content": transcript.get("content")
                })
            return formatted_transcripts
        except Exception: # Let the caller handle specific exceptions if needed, but tool should not crash
            return []


    def get_news(self, symbol: str, limit: int = 10) -> List[Dict]:
        """
        Get the most recent news articles about a company from Financial Modeling Prep API.

        Fetches news articles related to a specific stock ticker, including article title,
        URL, publication date, and summary.

        Args:
            symbol (str): The stock ticker symbol of the company (e.g., 'AAPL').
            limit (int, optional): The maximum number of news articles to retrieve. Defaults to 10.

        Returns:
            List[Dict]: A list of dictionaries, where each dictionary represents a news article
                         and contains keys: 'title', 'url', 'publishedDate', 'summary', etc.
                         Returns an empty list if no news articles are found or in case of API errors
                         (errors are already logged by _make_request).

        Raises:
            requests.exceptions.HTTPError: If the HTTP status code indicates an error.
            requests.exceptions.RequestException: For other request-related errors.

        Usage Example (from terminal):
        >>> python -c "from utils.fmp_tool import FMPTool; tool = FMPTool(); news = tool.get_news('AAPL', limit=5); import json; print(json.dumps(news, indent=2))"
        """
        endpoint = f"stock_news?tickers={symbol}&limit={limit}"
        try:
            news = self._make_request(endpoint)
            return news
        except Exception: # Let the caller handle specific exceptions if needed, but tool should not crash
            return []


    def get_sentiment(self, symbol: str) -> Dict:
        """
        Get stock sentiment data for a company from Financial Modeling Prep API.

        Fetches sentiment data, including overall sentiment score and news sentiment score.

        Args:
            symbol (str): The stock ticker symbol of the company (e.g., 'AAPL').

        Returns:
            Dict: A dictionary containing sentiment data. Structure may vary based on API response.
                  Returns an empty dictionary if sentiment data is not available or in case of API errors
                  (errors are already logged by _make_request).

        Raises:
            requests.exceptions.HTTPError: If the HTTP status code indicates an error.
            requests.exceptions.RequestException: For other request-related errors.

        Usage Example (from terminal):
        >>> python -c "from utils.fmp_tool import FMPTool; tool = FMPTool(); sentiment = tool.get_sentiment('AAPL'); import json; print(json.dumps(sentiment, indent=2))"
        """
        endpoint = f"stock-sentiment/{symbol}"
        try:
            sentiment_response = self._make_request(endpoint)
            return sentiment_response[0] if sentiment_response else {} # Return first sentiment or empty dict if no sentiment
        except Exception: # Let the caller handle specific exceptions if needed, but tool should not crash
            return {}


    def create_company_dataset(self, symbol: str = "DELL") -> Dict:
        """
        Create a comprehensive dataset for a company by fetching various data points from FMP API.

        Combines company profile, financial metrics, earnings calls, news, and sentiment data
        into a single structured dataset.

        Args:
            symbol (str, optional): The stock ticker symbol of the company. Defaults to "DELL".

        Returns:
            Dict: A dictionary containing the combined dataset for the company. Structure:
                  {
                      "symbol": str,
                      "company_name": str,
                      "sector": str,
                      "industry": str,
                      "description": str,
                      "website": str,
                      "ceo": str,
                      "financials": Dict,
                      "earnings_calls": List[Dict],
                      "news": List[Dict],
                      "sentiment": Dict,
                      "metadata": Dict
                  }

        Raises:
            requests.exceptions.HTTPError: If the HTTP status code indicates an error during any API call.
            requests.exceptions.RequestException: For other request-related errors during any API call.

        Usage Example (from terminal):
        >>> python -c "from utils.fmp_tool import FMPTool; tool = FMPTool(); dataset = tool.create_company_dataset('AAPL'); import json; print(json.dumps(dataset, indent=2))"
        """
        # Get all data components
        profile = self.get_company_profile(symbol)
        financials = self.get_financial_metrics(symbol)
        earnings_calls = self.get_earnings_calls(symbol)
        news = self.get_news(symbol)
        sentiment = self.get_sentiment(symbol)

        # Combine into a structured dataset
        dataset = {
            "symbol": symbol,
            "company_name": profile.get("companyName"),
            "sector": profile.get("sector"),
            "industry": profile.get("industry"),
            "description": profile.get("description"),
            "website": profile.get("website"),
            "ceo": profile.get("ceo"),
            "financials": financials,
            "earnings_calls": earnings_calls,
            "news": news,
            "sentiment": sentiment,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "data_source": "Financial Modeling Prep API"
            }
        }

        return dataset


    def save_company_dataset(self, symbol: str = "DELL", output_dir: str = "data") -> str:
        """
        Create and save a company dataset to a JSON file.

        Calls create_company_dataset to generate the dataset and then saves it as
        a JSON file in the specified output directory.

        Args:
            symbol (str, optional): The stock ticker symbol of the company. Defaults to "DELL".
            output_dir (str, optional): The directory to save the JSON file to. Defaults to "data".

        Returns:
            str: The full path to the saved JSON file.

        Raises:
            requests.exceptions.HTTPError: If the HTTP status code indicates an error during dataset creation.
            requests.exceptions.RequestException: For other request-related errors during dataset creation.

        Usage Example (from terminal):
        >>> python -c "from utils.fmp_tool import FMPTool; tool = FMPTool(); file_path = tool.save_company_dataset('AAPL'); print(file_path)"
        """
        dataset = self.create_company_dataset(symbol)

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Save to file
        output_path = os.path.join(output_dir, f"{symbol.lower()}_dataset.json")
        with open(output_path, "w") as f:
            json.dump(dataset, f, indent=2)

        return output_path


    def create_multi_company_datasets(self, symbols: List[str] = None) -> Dict[str, str]:
        """
        Create datasets for multiple companies and return file paths.

        Generates and saves datasets for a list of company symbols. If no symbols are provided,
        it uses a default list of tech companies.

        Args:
            symbols (List[str], optional): A list of stock ticker symbols.
                                           Defaults to ["AAPL", "GOOGL", "MSFT", "NVDA", "DELL", "AMZN", "JPM", "TSLA"].

        Returns:
            Dict[str, str]: A dictionary where keys are company symbols and values are the file paths
                             to the saved JSON datasets.

        Raises:
            requests.exceptions.HTTPError: If the HTTP status code indicates an error during dataset creation for any company.
            requests.exceptions.RequestException: For other request-related errors during dataset creation for any company.

        Usage Example (from terminal):
        >>> python -c "from utils.fmp_tool import FMPTool; tool = FMPTool(); file_paths = tool.create_multi_company_datasets(['AAPL', 'MSFT']); import json; print(json.dumps(file_paths, indent=2))"
        """
        if symbols is None:
            symbols = ["AAPL", "GOOGL", "MSFT", "NVDA", "DELL", "AMZN", "JPM", "TSLA"]

        file_paths = {}
        for symbol in symbols:
            try:
                file_path = self.save_company_dataset(symbol)
                file_paths[symbol] = file_path
                print(f"Created dataset for {symbol} at {file_path}")
            except Exception as e:
                print(f"Error creating dataset for {symbol}: {e}")

        return file_paths


    def create_mixed_document(self, symbols: List[str] = None, output_file: str = "data/mixed_document.json") -> str:
        """
        Create a mixed document combining earnings call excerpts from different companies.

        This function is primarily for testing purposes, creating a document with segments
        from different company earnings calls to simulate a more complex data environment
        for agent analysis (e.g., boundary detection tasks).

        Args:
            symbols (List[str], optional): List of stock ticker symbols to include in the mixed document.
                                           Defaults to ["DELL", "AAPL", "MSFT"].
            output_file (str, optional): Path to save the mixed document JSON file.
                                            Defaults to "data/mixed_document.json".

        Returns:
            str: The full path to the saved mixed document JSON file.

        Raises:
            requests.exceptions.HTTPError: If the HTTP status code indicates an error during data fetching.
            requests.exceptions.RequestException: For other request-related errors during data fetching.

        Usage Example (from terminal):
        >>> python -c "from utils.fmp_tool import FMPTool; tool = FMPTool(); file_path = tool.create_mixed_document(['AAPL', 'MSFT', 'GOOGL']); print(file_path)"
        """
        if symbols is None:
            symbols = ["DELL", "AAPL", "MSFT"]

        mixed_content = []

        for symbol in symbols:
            try:
                # Load the company dataset if it exists, otherwise create it
                data_path = f"data/{symbol.lower()}_dataset.json"
                if os.path.exists(data_path):
                    with open(data_path, "r") as f:
                        company_data = json.load(f)
                else:
                    company_data = self.create_company_dataset(symbol)

                # Get the most recent earnings call
                if company_data.get("earnings_calls"):
                    call = company_data["earnings_calls"][0]
                    # Add a segment of the call (first 3000 chars for simplicity)
                    if call.get("content"):
                        segment = {
                            "company": company_data["company_name"],
                            "symbol": symbol,
                            "date": call.get("date"),
                            "quarter": call.get("quarter"),
                            "year": call.get("year"),
                            "content": call.get("content")[:3000]  # First 3000 chars
                        }
                        mixed_content.append(segment)
            except Exception as e:
                print(f"Error processing {symbol}: {e}")

        # Combine all segments into one document
        combined_text = ""
        segments = []

        for i, segment in enumerate(mixed_content):
            segment_text = f"TRANSCRIPT EXCERPT: {segment['company']} ({segment['symbol']}) - {segment['quarter']} {segment['year']}\n\n"
            segment_text += segment["content"]

            # For all but the last segment, add some separator text to make it harder
            if i < len(mixed_content) - 1:
                segment_text += "\n\nNow, moving on to other market information...\n\n"

            combined_text += segment_text
            segments.append({
                "company": segment["company"],
                "symbol": segment["symbol"],
                "date": segment["date"],
                "start_char": len(combined_text) - len(segment_text),
                "end_char": len(combined_text)
            })

        # Create the mixed document with ground truth
        mixed_document = {
            "combined_text": combined_text,
            "ground_truth": {
                "segments": segments
            },
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "description": "Mixed earnings call segments for boundary detection testing"
            }
        }

        # Save to file
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(mixed_document, f, indent=2)

        return output_file


if __name__ == '__main__':
    # Example usage from terminal for testing
    tool = FMPTool() # Assumes FMP_API_KEY is set in environment

    print("\n--- Company Profile (AAPL) ---")
    profile = tool.get_company_profile('AAPL')
    print(json.dumps(profile, indent=2))

    print("\n--- Financial Metrics (AAPL) ---")
    metrics = tool.get_financial_metrics('AAPL')
    print(json.dumps(metrics, indent=2))

    print("\n--- Earnings Calls (AAPL, limit=2) ---")
    transcripts = tool.get_earnings_calls('AAPL', limit=2)
    print(json.dumps(transcripts, indent=2))

    print("\n--- News (AAPL, limit=3) ---")
    news = tool.get_news('AAPL', limit=3)
    print(json.dumps(news, indent=2))

    print("\n--- Sentiment (AAPL) ---")
    sentiment = tool.get_sentiment('AAPL')
    print(json.dumps(sentiment, indent=2))

    print("\n--- Create Company Dataset (DELL) and Save ---")
    dataset_path = tool.save_company_dataset('DELL')
    print(f"Dataset saved to: {dataset_path}")

    print("\n--- Create Mixed Document (AAPL, MSFT, GOOGL) ---")
    mixed_doc_path = tool.create_mixed_document(['AAPL', 'MSFT', 'GOOGL'])
    print(f"Mixed document saved to: {mixed_doc_path}")