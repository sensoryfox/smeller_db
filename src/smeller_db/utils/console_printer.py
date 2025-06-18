# src/utils/console_printer.py
from rich.console import Console
from rich.table import Table
from typing import List, Dict, Any

console = Console()

def print_table_data(title: str, headers: List[str], rows: List[List[Any]], row_limit: int = None):
    """
    Prints data in a Rich Table format.

    Args:
        title (str): Title for the table.
        headers (List[str]): List of column headers.
        rows (List[List[Any]]): List of lists, where each inner list is a row of data.
        row_limit (int, optional): Maximum number of rows to display. Defaults to None (all rows).
    """
    table = Table(title=title, show_header=True, header_style="bold magenta")
    for header in headers:
        table.add_column(header)

    display_rows = rows[:row_limit] if row_limit is not None else rows

    for row in display_rows:
        # Ensure all items are strings for rich, handle None explicitly
        table.add_row(*[str(item) if item is not None else "[dim]NULL[/dim]" for item in row])

    if row_limit is not None and len(rows) > row_limit:
        table.caption = f"Displaying {len(display_rows)} of {len(rows)} rows."

    console.print(table)

def print_key_value_pairs(title: str, data: Dict[str, Any]):
    """
    Prints key-value pairs in a readable format.

    Args:
        title (str): Title for the section.
        data (Dict[str, Any]): Dictionary of data to display.
    """
    console.print(f"\n[bold green]{title}[/bold green]")
    for key, value in data.items():
        console.print(f"  [cyan]{key}[/cyan]: [white]{value}[/white]")

def print_message(message: str, style: str = "white"):
    """
    Prints a general message to the console.
    """
    console.print(f"[{style}]{message}[/{style}]")