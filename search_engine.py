"""
Search Engine Module
Handles search queries and result processing for the document search application.
"""
import os
import subprocess
import platform
import logging
from typing import List, Dict, Any

from vector_store import VectorStore
from ui_manager import UIManager
from config import ApplicationConfig

logger = logging.getLogger("semantic_search")

class SearchEngine:
    """Class to handle semantic search functionality"""
    
    def __init__(self, vector_store: VectorStore, ui_manager: UIManager, config: ApplicationConfig):
        """Initialize the search engine"""
        self.vector_store = vector_store
        self.ui_manager = ui_manager
        self.config = config
    
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for documents matching the query
        
        Args:
            query: Natural language search query
            limit: Maximum number of results to return
            
        Returns:
            List of search results with metadata
        """
        # Enhance query if needed (e.g., add synonyms, handle specific file types)
        enhanced_query = self._enhance_query(query)
        
        # Execute search using vector store
        results = self.vector_store.search(enhanced_query, limit=limit)
        
        # Validate results (ensure files still exist)
        validated_results = []
        for result in results:
            file_path = result.get('path')
            if os.path.exists(file_path):
                validated_results.append(result)
            else:
                logger.warning(f"File no longer exists: {file_path}")
        
        return validated_results
    
    def open_document(self, document: Dict[str, Any]) -> bool:
        """
        Open a document using the system's default application
        
        Args:
            document: Document metadata dictionary
            
        Returns:
            True if document was opened successfully, False otherwise
        """
        file_path = document.get('path')
        if not file_path or not os.path.exists(file_path):
            self.ui_manager.display_error(f"File not found: {file_path}")
            return False
        
        try:
            # Open the file with the default application
            if platform.system() == 'Windows':
                os.startfile(file_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', file_path], check=True)
            else:  # Linux
                subprocess.run(['xdg-open', file_path], check=True)
                
            logger.info(f"Opened document: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error opening document {file_path}: {str(e)}")
            self.ui_manager.display_error(f"Error opening document: {str(e)}")
            return False
    
    def _enhance_query(self, query: str) -> str:
        """
        Enhance the search query to improve search results
        
        Args:
            query: Original search query
            
        Returns:
            Enhanced query
        """
        # If query specifically mentions a file type, we could boost certain aspects
        enhanced_query = query
        
        # Example: If query mentions Excel/spreadsheet, prioritize numerical content
        if any(term in query.lower() for term in ['excel', 'spreadsheet', 'sheet', 'xlsx', 'csv']):
            enhanced_query = f"{query} spreadsheet data columns rows"
            
        # If query mentions Word/document, prioritize text content
        elif any(term in query.lower() for term in ['word', 'document', 'doc', 'docx']):
            enhanced_query = f"{query} document text paragraphs"
            
        # If query mentions PDF, prioritize formatted content
        elif any(term in query.lower() for term in ['pdf']):
            enhanced_query = f"{query} pdf document pages"
            
        return enhanced_query
