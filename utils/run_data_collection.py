"""
Interactive data collection script for Agentic Explorer

This script provides a command-line interface to collect financial data
for the Agentic Explorer DataStore.
"""

import argparse
import sys
import rich
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
# Import project structure utilities
from project_structure import get_project_root, get_data_path
from utils.data_collector import fetch_data_for_companies, fetch_all_data

console = Console()

def print_header():
    """Print a stylized header."""
    header = """
     █████╗  ██████╗ ███████╗███╗   ██╗████████╗██╗ ██████╗
    ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝██║██╔════╝
    ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║   ██║██║     
    ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║   ██║██║     
    ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║   ██║╚██████╗
    ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝ ╚═════╝
    ███████╗██╗  ██╗██████╗ ██╗      ██████╗ ██████╗ ███████╗██████╗ 
    ██╔════╝╚██╗██╔╝██╔══██╗██║     ██╔═══██╗██╔══██╗██╔════╝██╔══██╗
    █████╗   ╚███╔╝ ██████╔╝██║     ██║   ██║██████╔╝█████╗  ██████╔╝
    ██╔══╝   ██╔██╗ ██╔═══╝ ██║     ██║   ██║██╔══██╗██╔══╝  ██╔══██╗
    ███████╗██╔╝ ██╗██║     ███████╗╚██████╔╝██║  ██║███████╗██║  ██║
    ╚══════╝╚═╝  ╚═╝╚═╝     ╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
                                                                     
    DataStore Population Utility
    """
    console.print(Panel(header, style="bold blue"))

def interactive_mode():
    """Run the data collector in interactive mode."""
    print_header()
    
    console.print("\n[bold]Welcome to the Agentic Explorer DataStore Population Utility![/bold]")
    console.print("This tool will help you collect financial data for the Agentic Explorer project.\n")
    
    # Get tickers
    ticker_input = Prompt.ask(
        "[bold yellow]Enter ticker symbols[/bold yellow] (comma-separated, e.g., NVDA,MSFT,AAPL)",
        default="NVDA"
    )
    tickers = [ticker.strip().upper() for ticker in ticker_input.split(",")]
    
    # Validate tickers
    console.print(f"\nCollecting data for: [bold green]{', '.join(tickers)}[/bold green]")
    if not Confirm.ask("Is this correct?"):
        console.print("Aborting. Please run the script again with the correct tickers.")
        return
    
    # Get years
    years = int(Prompt.ask(
        "\n[bold yellow]How many years of historical data[/bold yellow] would you like to collect?",
        default="5"
    ))
    
    # Confirm before proceeding
    console.print(f"\nReady to collect {years} years of data for: [bold green]{', '.join(tickers)}[/bold green]")
    console.print("[bold yellow]Note:[/bold yellow] This may take several minutes depending on the number of tickers.")
    
    if Confirm.ask("Proceed with data collection?"):
        console.print("\n[bold]Starting data collection...[/bold]")
        fetch_data_for_companies(tickers, years=years)
        console.print("\n[bold green]Data collection complete![/bold green]")
    else:
        console.print("Operation cancelled by user.")

def cli_mode():
    """Run the data collector in command-line interface mode."""
    parser = argparse.ArgumentParser(description="Agentic Explorer DataStore Population Utility")
    parser.add_argument(
        "--tickers", "-t", 
        type=str, 
        required=True,
        help="Comma-separated list of ticker symbols (e.g., NVDA,MSFT,AAPL)"
    )
    parser.add_argument(
        "--years", "-y", 
        type=int, 
        default=5,
        help="Number of years of historical data to collect (default: 5)"
    )
    parser.add_argument(
        "--single", "-s", 
        type=str, 
        help="Collect data for a single ticker only"
    )
    
    args = parser.parse_args()
    
    if args.single:
        # Single ticker mode
        ticker = args.single.upper()
        console.print(f"Collecting data for single ticker: [bold green]{ticker}[/bold green]")
        fetch_all_data(ticker, years=args.years)
    else:
        # Multiple tickers mode
        tickers = [ticker.strip().upper() for ticker in args.tickers.split(",")]
        console.print(f"Collecting data for: [bold green]{', '.join(tickers)}[/bold green]")
        fetch_data_for_companies(tickers, years=args.years)
    
    console.print("[bold green]Data collection complete![/bold green]")

if __name__ == "__main__":
    try:
        if len(sys.argv) > 1:
            # If arguments are provided, run in CLI mode
            cli_mode()
        else:
            # Otherwise, run in interactive mode
            interactive_mode()
    except KeyboardInterrupt:
        console.print("\n[bold red]Operation cancelled by user.[/bold red]")
    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]")