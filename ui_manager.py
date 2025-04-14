"""
UI Manager Module
Handles user interface display and formatting for the document search application.
"""
import os
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.box import ROUNDED
from rich.text import Text
from rich.style import Style
from rich.padding import Padding
from rich.theme import Theme

class UIManager:
    """Class to handle UI display and formatting"""
    
    # Colors from the specified style guide
    COLORS = {
        'primary': '#0078D4',     # Windows blue
        'secondary': '#107C10',   # Success green
        'background': '#F9F9F9',  # Light grey
        'text': '#323130',        # Dark grey
        'accent': '#C4314B'       # Attention red
    }
    
    def __init__(self, console: Optional[Console] = None):
        """Initialize the UI manager"""
        # Define theme with the specified colors
        self.theme = Theme({
            "primary": self.COLORS['primary'],
            "secondary": self.COLORS['secondary'],
            "background": self.COLORS['background'],
            "text": self.COLORS['text'],
            "accent": self.COLORS['accent'],
            "info": "cyan",
            "warning": "yellow",
            "error": self.COLORS['accent'],
            "success": self.COLORS['secondary']
        })
        
        # Initialize console with theme
        self.console = console or Console(theme=self.theme)
    
    def display_welcome(self) -> None:
        """Display welcome message"""
        title = Text("Semantic Document Search", style=f"bold {self.COLORS['primary']}")
        
        panel = Panel(
            Text.from_markup(
                "Search for documents using natural language queries\n"
                "Index your documents with [bold primary]index[/] command\n"
                "Search your documents with [bold primary]search[/] command\n"
                "Configure settings with [bold primary]config[/] command\n\n"
                "Type [bold]--help[/] after any command for more information"
            ),
            title=title,
            border_style=self.COLORS['primary'],
            box=ROUNDED
        )
        
        self.console.print()
        self.console.print(panel)
        self.console.print()
    
    def display_help(self) -> None:
        """Display help information"""
        table = Table(
            title="Available Commands",
            box=ROUNDED,
            border_style=self.COLORS['primary'],
            title_style=f"bold {self.COLORS['primary']}"
        )
        
        table.add_column("Command", style=f"bold {self.COLORS['primary']}")
        table.add_column("Description", style=self.COLORS['text'])
        table.add_column("Example", style="dim")
        
        table.add_row(
            "index <directory>", 
            "Index documents in a directory for searching",
            "index C:\\Documents"
        )
        table.add_row(
            "search <query>", 
            "Search for documents matching your query",
            "search quarterly financial report"
        )
        table.add_row(
            "config", 
            "Configure application settings",
            "config --list"
        )
        
        self.console.print()
        self.console.print(table)
        self.console.print()
    
    def display_search_results(self, results: List[Dict[str, Any]], query: str) -> None:
        """
        Display search results in a formatted table
        
        Args:
            results: List of search result dictionaries
            query: The search query that produced these results
        """
        if not results:
            self.display_message("No matching documents found for your query")
            return
        
        # Create results table
        table = Table(
            title=f"Search Results for: '{query}'",
            box=ROUNDED,
            border_style=self.COLORS['primary'],
            title_style=f"bold {self.COLORS['primary']}"
        )
        
        table.add_column("#", style="dim", width=3)
        table.add_column("Filename", style=f"bold {self.COLORS['primary']}")
        table.add_column("Path", style=self.COLORS['text'])
        table.add_column("Relevance", style=self.COLORS['secondary'], width=10)
        table.add_column("Preview", style="dim")
        
        # Add rows for each result
        for i, result in enumerate(results, 1):
            # Format the relevance score as a percentage
            relevance = f"{result.get('similarity', 0) * 100:.1f}%"
            
            # Get the preview or snippet
            preview = result.get('content_preview', '')
            if len(preview) > 60:
                preview = preview[:57] + "..."
            
            # Get the path and format it for display
            path = result.get('path', '')
            if len(path) > 40:
                # Show only the first and last parts of the path
                parts = path.split(os.sep)
                if len(parts) > 3:
                    path = os.sep.join([parts[0], "...", parts[-2], parts[-1]])
            
            table.add_row(
                str(i),
                result.get('filename', ''),
                path,
                relevance,
                preview
            )
        
        # Add instructions footer
        table.caption = "To open a document, use: search <query> --open"
        
        self.console.print()
        self.console.print(table)
        self.console.print()
    
    def display_message(self, message: str) -> None:
        """Display a simple message"""
        self.console.print(f"  {message}")
    
    def display_success(self, message: str) -> None:
        """Display a success message"""
        text = Text(f"✓ {message}", style=f"bold {self.COLORS['secondary']}")
        self.console.print(text)
    
    def display_error(self, message: str) -> None:
        """Display an error message"""
        text = Text(f"✗ {message}", style=f"bold {self.COLORS['accent']}")
        self.console.print(text)
    
    def display_warning(self, message: str) -> None:
        """Display a warning message"""
        text = Text(f"⚠ {message}", style="bold yellow")
        self.console.print(text)
    
    def display_config(self, config_dict: Dict[str, Any]) -> None:
        """Display configuration settings"""
        table = Table(
            title="Current Configuration",
            box=ROUNDED,
            border_style=self.COLORS['primary'],
            title_style=f"bold {self.COLORS['primary']}"
        )
        
        table.add_column("Setting", style=f"bold {self.COLORS['primary']}")
        table.add_column("Value", style=self.COLORS['text'])
        table.add_column("Description", style="dim")
        
        # Add rows for each configuration setting
        for key, value in config_dict.items():
            description = {
                'data_dir': "Directory for storing application data",
                'vector_db_path': "Path to the vector database",
                'embedding_model': "Model used for generating embeddings",
                'chunk_size': "Size of text chunks for indexing",
                'chunk_overlap': "Overlap between text chunks"
            }.get(key, "")
            
            table.add_row(key, str(value), description)
        
        self.console.print()
        self.console.print(table)
        self.console.print()
