"""
Interactive data collection script for SignalStore

This script provides a command-line interface to collect financial data
for the SignalStore DataStore.
"""

import argparse
import sys
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

# Import our enhanced data collector
from utils.data_collector import (
    collect_all_data, 
    collect_company_data,
    collect_market_data,
    collect_event_data,
    collect_relationship_data
)

console = Console()

def print_header():
    """Print a stylized header."""
    header = """
     ███████╗██╗ ██████╗ ███╗   ██╗ █████╗ ██╗         
     ██╔════╝██║██╔════╝ ████╗  ██║██╔══██╗██║         
     ███████╗██║██║  ███╗██╔██╗ ██║███████║██║         
     ╚════██║██║██║   ██║██║╚██╗██║██╔══██║██║         
     ███████║██║╚██████╔╝██║ ╚████║██║  ██║███████╗    
     ╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝    
     ███████╗████████╗ ██████╗ ██████╗ ███████╗        
     ██╔════╝╚══██╔══╝██╔═══██╗██╔══██╗██╔════╝        
     ███████╗   ██║   ██║   ██║██████╔╝█████╗          
     ╚════██║   ██║   ██║   ██║██╔══██╗██╔══╝          
     ███████║   ██║   ╚██████╔╝██║  ██║███████╗        
     ╚══════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚══════╝        
                                                        
    DataStore Population Utility
    """
    console.print(Panel(header, style="bold blue"))

def interactive_mode():
    """Run the data collector in interactive mode."""
    print_header()
    
    console.print("\n[bold]Welcome to the SignalStore DataStore Population Utility![/bold]")
    console.print("This tool will help you collect financial data for building early warning signals.\n")
    
    # Main menu
    options = [
        "Collect comprehensive data for multiple companies",
        "Collect data for a single company",
        "Collect market-wide data only",
        "Collect event-based data only",
        "Exit"
    ]
    
    option_selected = Prompt.ask(
        "[bold yellow]Select an option[/bold yellow]",
        choices=[str(i+1) for i in range(len(options))],
        default="1"
    )
    
    if option_selected == "1":
        # Comprehensive collection
        ticker_input = Prompt.ask(
            "[bold yellow]Enter ticker symbols[/bold yellow] (comma-separated, e.g., DELL,NVDA,TSLA,ACN)",
            default="DELL,NVDA,TSLA,ACN"
        )
        tickers = [ticker.strip().upper() for ticker in ticker_input.split(",")]
        
        years = int(Prompt.ask(
            "\n[bold yellow]How many years of historical data[/bold yellow] would you like to collect?",
            default="3"
        ))
        
        console.print(f"\nReady to collect {years} years of comprehensive data for: [bold green]{', '.join(tickers)}[/bold green]")
        if Confirm.ask("Proceed with data collection?"):
            collect_all_data(tickers, years)
    
    elif option_selected == "2":
        # Single company
        ticker = Prompt.ask(
            "[bold yellow]Enter ticker symbol[/bold yellow]",
            default="NVDA"
        ).strip().upper()
        
        years = int(Prompt.ask(
            "\n[bold yellow]How many years of historical data[/bold yellow] would you like to collect?",
            default="3"
        ))
        
        console.print(f"\nReady to collect {years} years of data for: [bold green]{ticker}[/bold green]")
        if Confirm.ask("Proceed with data collection?"):
            collect_company_data(ticker, years)
    
    elif option_selected == "3":
        # Market data only
        years = int(Prompt.ask(
            "[bold yellow]How many years of historical data[/bold yellow] would you like to collect?",
            default="3"
        ))
        
        console.print(f"\nReady to collect {years} years of market data")
        if Confirm.ask("Proceed with data collection?"):
            collect_market_data(years)
    
    elif option_selected == "4":
        # Event data only
        console.print("\nReady to collect recent event-based data")
        if Confirm.ask("Proceed with data collection?"):
            collect_event_data()
    
    else:
        # Exit
        console.print("Exiting data collection utility.")
        return
    
    console.print("\n[bold green]Data collection complete![/bold green]")

def cli_mode():
    """Run the data collector in command-line interface mode."""
    parser = argparse.ArgumentParser(description="SignalStore DataStore Population Utility")
    parser.add_argument(
        "--tickers", "-t", 
        type=str, 
        help="Comma-separated list of ticker symbols (e.g., DELL,NVDA,TSLA,ACN)"
    )
    parser.add_argument(
        "--years", "-y", 
        type=int, 
        default=3,
        help="Number of years of historical data to collect (default: 3)"
    )
    parser.add_argument(
        "--single", "-s", 
        type=str, 
        help="Collect data for a single ticker only"
    )
    parser.add_argument(
        "--market", "-m",
        action="store_true",
        help="Collect market data only"
    )
    parser.add_argument(
        "--events", "-e",
        action="store_true",
        help="Collect event data only"
    )
    
    args = parser.parse_args()
    
    if args.single:
        # Single ticker mode
        ticker = args.single.upper()
        console.print(f"Collecting data for single ticker: [bold green]{ticker}[/bold green]")
        collect_company_data(ticker, years=args.years)
    
    elif args.market:
        # Market data only
        console.print(f"Collecting market data for {args.years} years")
        collect_market_data(years=args.years)
    
    elif args.events:
        # Event data only
        console.print("Collecting event-based data")
        collect_event_data()
    
    elif args.tickers:
        # Multiple tickers mode
        tickers = [ticker.strip().upper() for ticker in args.tickers.split(",")]
        console.print(f"Collecting comprehensive data for: [bold green]{', '.join(tickers)}[/bold green]")
        collect_all_data(tickers, years=args.years)
    
    else:
        # No arguments provided
        console.print("No collection options specified. Use --help for usage information.")
        return
    
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