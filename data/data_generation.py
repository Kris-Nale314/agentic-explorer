# data/data_generation.py
import os
import sys
from dotenv import load_dotenv
import logging

# Add the project root to Python path to find modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file
load_dotenv()

# Now you can access the environment variables
from utils.fmp_tool import FMPTool

# Configure logging for data generation script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """
    Main function to generate company datasets and mixed documents using FMPTool.

    This script initializes the FMPTool, creates datasets for a list of companies,
    and generates example mixed documents for testing purposes.  It saves the datasets
    as JSON files in the 'data' directory.

    Environment Variables:
        FMP_API_KEY: Required Financial Modeling Prep API key. Must be set in .env file or environment.

    Example Usage (from terminal):
    >>> python data/data_generation.py
    """
    # Get API key from environment
    api_key = os.environ.get('FMP_API_KEY')
    if not api_key:
        logging.error("FMP_API_KEY environment variable not set. Please set it in your .env file.")
        print("Error: FMP_API_KEY environment variable not set. Please set it in your .env file.") # Print for user visibility in terminal
        return

    # Initialize the tool
    try:
        fmp = FMPTool(api_key)
        logging.info("FMPTool initialized successfully.")
    except ValueError as e:
        logging.error(f"Error initializing FMPTool: {e}")
        print(f"Error initializing FMPTool: {e}") # Print for user visibility in terminal
        return

    # Create datasets for target companies
    companies = ["AAPL", "GOOGL", "MSFT", "NVDA", "DELL", "AMZN", "JPM", "TSLA"]
    logging.info(f"Generating datasets for {len(companies)} companies: {companies}")
    print(f"Generating datasets for {len(companies)} companies: {companies}...") # Print for user visibility

    file_paths = {}
    for symbol in companies:
        try:
            file_path = fmp.save_company_dataset(symbol)
            file_paths[symbol] = file_path
            logging.info(f"Dataset created successfully for {symbol}: {file_path}")
        except Exception as e: # Catch more general exceptions during dataset creation for robustness
            logging.error(f"Error creating dataset for {symbol}: {e}")
            print(f"Error creating dataset for {symbol}: {e}") # Print for user visibility

    print("\nDatasets created:")
    for symbol, path in file_paths.items():
        print(f"- {symbol}: {path}")

    # Create mixed document examples
    logging.info("Creating mixed document examples...")
    print("\nCreating mixed document examples...") # Print for user visibility

    # Example 1: Mix of recent earnings calls
    try:
        mixed_path1 = fmp.create_mixed_document(
            symbols=["DELL", "AAPL", "MSFT"],
            output_file="data/mixed_recent_calls.json"
        )
        print(f"Created mixed recent calls document: {mixed_path1}")
        logging.info(f"Created mixed recent calls document: {mixed_path1}")
    except Exception as e: # Catch exceptions during mixed document creation
        logging.error(f"Error creating mixed recent calls document: {e}")
        print(f"Error creating mixed recent calls document: {e}") # Print for user visibility

    # Example 2 & 3 notes remain as placeholders - implementation is future enhancement
    print("\nNote: For historical call mixing, we would need additional API calls")
    print("Note: For mixing different document types, we would need additional implementation")
    logging.info("Example mixed document creation notes added to output.")

    logging.info("Data generation script completed.")
    print("\nData generation script completed.") # Final message for user


if __name__ == "__main__":
    main()