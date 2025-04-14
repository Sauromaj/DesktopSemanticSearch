"""
Utilities Module
Helper functions for the document search application.
"""
import os
import platform
import tempfile
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger("semantic_search")

def get_app_data_dir() -> Path:
    """
    Get the appropriate application data directory for the current platform
    
    Returns:
        Path to the application data directory
    """
    app_name = "SemanticDocSearch"
    
    if platform.system() == "Windows":
        # On Windows, use %APPDATA%
        base_dir = os.environ.get("APPDATA")
        if not base_dir:
            # Fallback if APPDATA is not defined
            base_dir = os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
        
    elif platform.system() == "Darwin":
        # On macOS, use ~/Library/Application Support
        base_dir = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
        
    else:
        # On Linux, use ~/.local/share
        base_dir = os.environ.get("XDG_DATA_HOME")
        if not base_dir:
            base_dir = os.path.join(os.path.expanduser("~"), ".local", "share")
    
    app_dir = os.path.join(base_dir, app_name)
    
    # Create the directory if it doesn't exist
    os.makedirs(app_dir, exist_ok=True)
    
    return Path(app_dir)

def get_temp_dir() -> Path:
    """
    Get a temporary directory for processing files
    
    Returns:
        Path to the temporary directory
    """
    temp_dir = os.path.join(tempfile.gettempdir(), "SemanticDocSearch")
    os.makedirs(temp_dir, exist_ok=True)
    return Path(temp_dir)

def format_file_size(size_bytes: int) -> str:
    """
    Format file size from bytes to a human-readable format
    
    Args:
        size_bytes: File size in bytes
        
    Returns:
        Formatted file size string
    """
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

def get_file_extension(file_path: str) -> str:
    """
    Get file extension from a file path
    
    Args:
        file_path: Path to the file
        
    Returns:
        File extension (lowercase, with dot)
    """
    return os.path.splitext(file_path)[1].lower()

def is_supported_file(file_path: str) -> bool:
    """
    Check if a file is supported for indexing
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if the file is supported, False otherwise
    """
    supported_extensions = {
        '.pdf', '.docx', '.doc', '.xlsx', '.xls', '.csv'
    }
    return get_file_extension(file_path) in supported_extensions

def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks for processing
    
    Args:
        text: The text to split
        chunk_size: Maximum size of each chunk
        chunk_overlap: Overlap between chunks
        
    Returns:
        List of text chunks
    """
    if not text or chunk_size <= 0:
        return []
        
    chunks = []
    start = 0
    
    while start < len(text):
        # Find a good break point (end of sentence) near the chunk_size
        end = min(start + chunk_size, len(text))
        
        # Try to end at a sentence boundary
        if end < len(text):
            # Look for sentence ending punctuation followed by space or newline
            for i in range(end - 1, max(start, end - 100), -1):
                if text[i] in '.!?' and (i + 1 == len(text) or text[i + 1].isspace()):
                    end = i + 1
                    break
        
        # Add the chunk
        chunks.append(text[start:end])
        
        # Move to next chunk with overlap
        start = end - chunk_overlap if end < len(text) else end
    
    return chunks
