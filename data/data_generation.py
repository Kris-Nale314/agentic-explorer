"""
Enhanced data generation for Agentic Explorer.

Creates comprehensive company datasets and mixed documents for testing RAG capabilities.
"""

import os
import sys
import json
import logging
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Add the project root to Python path to find modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file
load_dotenv()

# Import the FMP tool
from utils.fmp_tool import FMPTool

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataGenerator:
    """Data generator for creating comprehensive test datasets."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the data generator.
        
        Args:
            api_key: FMP API key (uses environment variable if not provided)
        """
        self.api_key = api_key or os.environ.get('FMP_API_KEY')
        if not self.api_key:
            raise ValueError("FMP_API_KEY is required. Set it in .env file or pass directly.")
        
        self.fmp = FMPTool(self.api_key)
        self.data_dir = os.path.join(os.path.dirname(__file__))
        
        # Create directories if they don't exist
        os.makedirs(os.path.join(self.data_dir, "companies"), exist_ok=True)
        os.makedirs(os.path.join(self.data_dir, "mixed"), exist_ok=True)
        
        logger.info("Initialized DataGenerator")
    
    def generate_company_profile(self, symbol: str) -> Dict[str, Any]:
        """
        Generate a comprehensive company profile.
        
        Args:
            symbol: Company stock symbol
            
        Returns:
            Dictionary with company data
        """
        logger.info(f"Generating comprehensive profile for {symbol}")
        
        try:
            # Get basic company profile
            profile = self.fmp.get_company_profile(symbol)
            
            # Get financial metrics
            metrics = self.fmp.get_company_metrics(symbol)
            
            # Get latest earnings call transcript
            transcripts = self.fmp.get_earnings_call_transcripts(symbol, limit=2)
            
            # Get recent news
            news = self.fmp.get_company_news(symbol, limit=5)
            
            # Combine all data
            company_data = {
                "symbol": symbol,
                "profile": profile,
                "metrics": metrics,
                "earnings_calls": transcripts,
                "news": news,
                "generated_at": datetime.now().isoformat()
            }
            
            return company_data
            
        except Exception as e:
            logger.error(f"Error generating profile for {symbol}: {e}")
            raise
    
    def save_company_profile(self, symbol: str) -> str:
        """
        Generate and save a company profile.
        
        Args:
            symbol: Company stock symbol
            
        Returns:
            Path to saved file
        """
        company_data = self.generate_company_profile(symbol)
        
        # Save to file
        file_path = os.path.join(self.data_dir, "companies", f"{symbol.lower()}_profile.json")
        with open(file_path, 'w') as f:
            json.dump(company_data, f, indent=2)
        
        logger.info(f"Saved company profile: {file_path}")
        return file_path
    
    def create_earnings_call_mix(self, symbols: List[str], output_file: str = None) -> str:
        """
        Create a mixed document of earnings call transcripts.
        
        Args:
            symbols: List of company symbols
            output_file: Output file path (generated if None)
            
        Returns:
            Path to saved file
        """
        logger.info(f"Creating earnings call mix for: {symbols}")
        
        # Default output file
        if not output_file:
            symbols_str = '_'.join(symbols).lower()
            output_file = os.path.join(self.data_dir, "mixed", f"earnings_calls_{symbols_str}.json")
        
        # Get transcripts for each company
        all_transcripts = []
        for symbol in symbols:
            try:
                transcripts = self.fmp.get_earnings_call_transcripts(symbol, limit=2)
                for transcript in transcripts:
                    # Add company symbol for clarity
                    transcript["company"] = symbol
                    all_transcripts.append(transcript)
            except Exception as e:
                logger.warning(f"Error getting transcripts for {symbol}: {e}")
        
        # Shuffle transcripts for a more mixed document
        random.shuffle(all_transcripts)
        
        # Create mixed document
        mixed_doc = {
            "type": "earnings_call_mix",
            "companies": symbols,
            "transcripts": all_transcripts,
            "combined_text": "\n\n".join([
                f"## {t.get('company', 'Unknown')} Earnings Call: {t.get('date', 'Unknown')}\n\n{t.get('content', '')}"
                for t in all_transcripts
            ]),
            "generated_at": datetime.now().isoformat()
        }
        
        # Save to file
        with open(output_file, 'w') as f:
            json.dump(mixed_doc, f, indent=2)
        
        logger.info(f"Saved earnings call mix: {output_file}")
        return output_file
    
    def create_news_mix(self, symbols: List[str], output_file: str = None) -> str:
        """
        Create a mixed document of company news.
        
        Args:
            symbols: List of company symbols
            output_file: Output file path (generated if None)
            
        Returns:
            Path to saved file
        """
        logger.info(f"Creating news mix for: {symbols}")
        
        # Default output file
        if not output_file:
            symbols_str = '_'.join(symbols).lower()
            output_file = os.path.join(self.data_dir, "mixed", f"news_mix_{symbols_str}.json")
        
        # Get news for each company
        all_news = []
        for symbol in symbols:
            try:
                news = self.fmp.get_company_news(symbol, limit=5)
                for article in news:
                    # Add company symbol for clarity
                    article["company"] = symbol
                    all_news.append(article)
            except Exception as e:
                logger.warning(f"Error getting news for {symbol}: {e}")
        
        # Sort by date (recent first)
        all_news.sort(key=lambda x: x.get("publishedDate", ""), reverse=True)
        
        # Create mixed document
        mixed_doc = {
            "type": "news_mix",
            "companies": symbols,
            "news": all_news,
            "combined_text": "\n\n".join([
                f"## {n.get('company', 'Unknown')} News: {n.get('publishedDate', 'Unknown')}\n\n" +
                f"### {n.get('title', 'Untitled')}\n\n{n.get('content', '')}"
                for n in all_news
            ]),
            "generated_at": datetime.now().isoformat()
        }
        
        # Save to file
        with open(output_file, 'w') as f:
            json.dump(mixed_doc, f, indent=2)
        
        logger.info(f"Saved news mix: {output_file}")
        return output_file
    
    def create_metrics_mix(self, symbols: List[str], output_file: str = None) -> str:
        """
        Create a mixed document of financial metrics.
        
        Args:
            symbols: List of company symbols
            output_file: Output file path (generated if None)
            
        Returns:
            Path to saved file
        """
        logger.info(f"Creating metrics mix for: {symbols}")
        
        # Default output file
        if not output_file:
            symbols_str = '_'.join(symbols).lower()
            output_file = os.path.join(self.data_dir, "mixed", f"metrics_mix_{symbols_str}.json")
        
        # Get metrics for each company
        all_metrics = []
        for symbol in symbols:
            try:
                metrics = self.fmp.get_company_metrics(symbol)
                metrics["company"] = symbol
                all_metrics.append(metrics)
            except Exception as e:
                logger.warning(f"Error getting metrics for {symbol}: {e}")
        
        # Create mixed document with nice text formatting
        metrics_text = ""
        for company_metrics in all_metrics:
            symbol = company_metrics.get("company", "Unknown")
            
            metrics_text += f"# Financial Metrics for {symbol}\n\n"
            
            if "quarterlyMetrics" in company_metrics:
                metrics_text += "## Quarterly Performance\n\n"
                
                for quarter in company_metrics["quarterlyMetrics"][:4]:  # Last 4 quarters
                    period = quarter.get("period", "Unknown Quarter")
                    metrics_text += f"### {period}\n\n"
                    
                    # Revenue
                    revenue = quarter.get("revenue", "N/A")
                    revenue_growth = quarter.get("revenueGrowth", "N/A")
                    metrics_text += f"- Revenue: ${revenue} million (Growth: {revenue_growth}%)\n"
                    
                    # Earnings
                    eps = quarter.get("eps", "N/A")
                    net_income = quarter.get("netIncome", "N/A")
                    metrics_text += f"- EPS: ${eps}\n"
                    metrics_text += f"- Net Income: ${net_income} million\n"
                    
                    # Other metrics
                    gross_margin = quarter.get("grossMargin", "N/A")
                    operating_margin = quarter.get("operatingMargin", "N/A")
                    metrics_text += f"- Gross Margin: {gross_margin}%\n"
                    metrics_text += f"- Operating Margin: {operating_margin}%\n\n"
            
            metrics_text += "\n\n"
        
        # Create mixed document
        mixed_doc = {
            "type": "metrics_mix",
            "companies": symbols,
            "metrics": all_metrics,
            "combined_text": metrics_text,
            "generated_at": datetime.now().isoformat()
        }
        
        # Save to file
        with open(output_file, 'w') as f:
            json.dump(mixed_doc, f, indent=2)
        
        logger.info(f"Saved metrics mix: {output_file}")
        return output_file
    
    def create_complex_document(self, symbols: List[str], output_file: str = None) -> str:
        """
        Create a complex mixed document with different types of information.
        
        Args:
            symbols: List of company symbols
            output_file: Output file path (generated if None)
            
        Returns:
            Path to saved file
        """
        logger.info(f"Creating complex document for: {symbols}")
        
        # Default output file
        if not output_file:
            symbols_str = '_'.join(symbols).lower()
            output_file = os.path.join(self.data_dir, "mixed", f"complex_mix_{symbols_str}.json")
        
        # Collect all types of information
        company_data = {}
        for symbol in symbols:
            try:
                company_data[symbol] = {
                    "profile": self.fmp.get_company_profile(symbol),
                    "transcripts": self.fmp.get_earnings_call_transcripts(symbol, limit=1),
                    "news": self.fmp.get_company_news(symbol, limit=3),
                    "metrics": self.fmp.get_company_metrics(symbol)
                }
            except Exception as e:
                logger.warning(f"Error getting data for {symbol}: {e}")
        
        # Create a complex mixed document
        combined_text = ""
        
        # First add company profiles
        for symbol, data in company_data.items():
            profile = data.get("profile", {})
            combined_text += f"# Company Profile: {symbol}\n\n"
            combined_text += f"{profile.get('description', 'No description available.')}\n\n"
            combined_text += f"- Industry: {profile.get('industry', 'N/A')}\n"
            combined_text += f"- CEO: {profile.get('ceo', 'N/A')}\n"
            combined_text += f"- Website: {profile.get('website', 'N/A')}\n\n"
        
        combined_text += "\n\n"
        
        # Then add intermixed earnings calls
        combined_text += "# Recent Earnings Call Transcripts\n\n"
        all_transcripts = []
        for symbol, data in company_data.items():
            for transcript in data.get("transcripts", []):
                transcript["company"] = symbol
                all_transcripts.append(transcript)
        
        # Shuffle to create a more challenging mixed document
        random.shuffle(all_transcripts)
        
        for transcript in all_transcripts:
            symbol = transcript.get("company", "Unknown")
            date = transcript.get("date", "Unknown Date")
            content = transcript.get("content", "No transcript available.")
            
            combined_text += f"## {symbol} Earnings Call ({date})\n\n{content}\n\n"
        
        combined_text += "\n\n"
        
        # Then add news articles
        combined_text += "# Recent News\n\n"
        all_news = []
        for symbol, data in company_data.items():
            for article in data.get("news", []):
                article["company"] = symbol
                all_news.append(article)
        
        # Sort by date (recent first)
        all_news.sort(key=lambda x: x.get("publishedDate", ""), reverse=True)
        
        for article in all_news:
            symbol = article.get("company", "Unknown")
            date = article.get("publishedDate", "Unknown Date")
            title = article.get("title", "Untitled")
            content = article.get("content", "No content available.")
            
            combined_text += f"## {symbol} News: {date}\n\n"
            combined_text += f"### {title}\n\n{content}\n\n"
        
        # Create the complex document
        complex_doc = {
            "type": "complex_mix",
            "companies": symbols,
            "data": company_data,
            "combined_text": combined_text,
            "generated_at": datetime.now().isoformat()
        }
        
        # Save to file
        with open(output_file, 'w') as f:
            json.dump(complex_doc, f, indent=2)
        
        logger.info(f"Saved complex document mix: {output_file}")
        return output_file
    
    def create_all_test_datasets(self, symbols: List[str]) -> Dict[str, str]:
        """
        Create a complete set of test datasets for the provided symbols.
        
        Args:
            symbols: List of company symbols
            
        Returns:
            Dictionary of created file paths
        """
        logger.info(f"Creating complete test dataset collection for: {symbols}")
        
        file_paths = {}
        
        # Generate individual company profiles
        for symbol in symbols:
            try:
                file_path = self.save_company_profile(symbol)
                file_paths[f"{symbol}_profile"] = file_path
            except Exception as e:
                logger.error(f"Error generating profile for {symbol}: {e}")
        
        # Create various mixed documents
        try:
            # Earnings call mix
            earnings_path = self.create_earnings_call_mix(symbols)
            file_paths["earnings_mix"] = earnings_path
            
            # News mix
            news_path = self.create_news_mix(symbols)
            file_paths["news_mix"] = news_path
            
            # Metrics mix
            metrics_path = self.create_metrics_mix(symbols)
            file_paths["metrics_mix"] = metrics_path
            
            # Complex document mix
            complex_path = self.create_complex_document(symbols)
            file_paths["complex_mix"] = complex_path
            
        except Exception as e:
            logger.error(f"Error creating mixed documents: {e}")
        
        logger.info(f"Created {len(file_paths)} test datasets")
        return file_paths

def main():
    """Main function to run the data generation script."""
    # Check for API key
    api_key = os.environ.get('FMP_API_KEY')
    if not api_key:
        logger.error("FMP_API_KEY environment variable not set")
        print("Error: FMP_API_KEY environment variable not set. Please set it in your .env file.")
        return 1
    
    # Target companies
    symbols = ["DELL", "NVDA", "AAPL"]
    print(f"Generating datasets for: {', '.join(symbols)}")
    
    try:
        # Initialize generator
        generator = DataGenerator(api_key)
        
        # Create all test datasets
        file_paths = generator.create_all_test_datasets(symbols)
        
        # Print results
        print("\nCreated datasets:")
        for name, path in file_paths.items():
            print(f"- {name}: {path}")
        
        print("\nData generation complete!")
        return 0
        
    except Exception as e:
        logger.error(f"Error in data generation: {e}")
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())