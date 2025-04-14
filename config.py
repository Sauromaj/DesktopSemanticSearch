"""
Configuration Module
Manages application configuration settings.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from utils import get_app_data_dir

logger = logging.getLogger("semantic_search")

class ApplicationConfig:
    """Class to manage application configuration"""
    
    # Default configuration values
    DEFAULTS = {
        'data_dir': str(get_app_data_dir()),
        'vector_db_path': str(get_app_data_dir() / "vector_db"),
        'embedding_model': 'all-MiniLM-L6-v2',
        'chunk_size': 1000,
        'chunk_overlap': 200
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration with optional custom path
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.config_path = config_path or str(get_app_data_dir() / "config.json")
        self.config = self.DEFAULTS.copy()
        
        # Load existing configuration if available
        self._load_config()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value
        
        Args:
            key: Configuration key
            default: Default value if key doesn't exist
            
        Returns:
            Configuration value
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """
        Set a configuration value
        
        Args:
            key: Configuration key
            value: Configuration value
            
        Returns:
            True if successful, False otherwise
        """
        if key not in self.DEFAULTS:
            logger.warning(f"Unknown configuration key: {key}")
            return False
        
        # Type validation
        expected_type = type(self.DEFAULTS[key])
        try:
            # Convert value to expected type
            if expected_type == int:
                value = int(value)
            elif expected_type == float:
                value = float(value)
            elif expected_type == bool:
                if isinstance(value, str):
                    value = value.lower() in ('true', 'yes', '1', 'y')
                else:
                    value = bool(value)
            elif expected_type == str:
                value = str(value)
        except ValueError:
            logger.error(f"Invalid value type for {key}: expected {expected_type.__name__}")
            return False
        
        # Update configuration
        self.config[key] = value
        
        # Save configuration
        self._save_config()
        return True
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration values
        
        Returns:
            Dictionary of all configuration values
        """
        return self.config.copy()
    
    def reset(self) -> None:
        """Reset configuration to defaults"""
        self.config = self.DEFAULTS.copy()
        self._save_config()
    
    def _load_config(self) -> None:
        """Load configuration from file"""
        if not os.path.exists(self.config_path):
            logger.info(f"Configuration file not found, using defaults: {self.config_path}")
            return
        
        try:
            with open(self.config_path, 'r') as f:
                loaded_config = json.load(f)
                
            # Update configuration with loaded values
            for key, value in loaded_config.items():
                if key in self.DEFAULTS:
                    self.config[key] = value
                    
            logger.debug(f"Loaded configuration from {self.config_path}")
            
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
    
    def _save_config(self) -> None:
        """Save configuration to file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
                
            logger.debug(f"Saved configuration to {self.config_path}")
            
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")
    
    # Properties for common configuration values
    
    @property
    def data_dir(self) -> str:
        """Get the data directory path"""
        return self.get('data_dir')
    
    @property
    def vector_db_path(self) -> str:
        """Get the vector database path"""
        return self.get('vector_db_path')
    
    @property
    def embedding_model(self) -> str:
        """Get the embedding model name"""
        return self.get('embedding_model')
    
    @property
    def chunk_size(self) -> int:
        """Get the text chunk size"""
        return self.get('chunk_size')
    
    @property
    def chunk_overlap(self) -> int:
        """Get the text chunk overlap"""
        return self.get('chunk_overlap')
