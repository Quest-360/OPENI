"""
Configuration Manager Module
--------------------------
Handles configuration storage, history tracking, and persistence of settings.
Manages user preferences, scheduled tasks, and scraping history.
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Set up logging
logger = logging.getLogger("ZeptoScraper.ConfigManager")

# Constants
CONFIG_FILE = "zepto_scraper_config.json"
DEFAULT_CONFIG = {
    "rate_limiter": {
        "min_delay": 1.0,
        "max_delay": 3.0,
        "rpm_limit": 20
    },
    "browser": {
        "type": "chrome",
        "headless": True
    },
    "default_locations": "Hyderabad",
    "history": [],
    "scheduled_tasks": []
}

class ConfigManager:
    """Manages application configuration, history, and scheduled tasks"""
    
    def __init__(self, config_file=CONFIG_FILE):
        """
        Initialize the ConfigManager
        
        Args:
            config_file: Path to the configuration file
        """
        self.config_file = config_file
        self.config = self._load_config_file()
    
    def _load_config_file(self) -> Dict[str, Any]:
        """
        Load configuration from file or create default
        
        Returns:
            Configuration dictionary
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    logger.info(f"Configuration loaded from {self.config_file}")
                    return config
            else:
                logger.info(f"Configuration file not found, creating default at {self.config_file}")
                self._save_config_file(DEFAULT_CONFIG)
                return DEFAULT_CONFIG.copy()
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            logger.info("Creating default configuration")
            return DEFAULT_CONFIG.copy()
    
    def _save_config_file(self, config=None):
        """Save configuration to file"""
        config = config or self.config
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
    
    def load_config(self) -> Dict[str, Any]:
        """
        Get the current configuration
        
        Returns:
            Configuration dictionary
        """
        return self.config
    
    def save_config(self, new_config: Dict[str, Any]):
        """
        Update and save configuration
        
        Args:
            new_config: New configuration values to save
        """
        # Update config with new values, preserving history and scheduled tasks
        history = self.config.get('history', [])
        scheduled_tasks = self.config.get('scheduled_tasks', [])
        
        self.config.update(new_config)
        
        # Make sure we don't overwrite history and tasks
        if 'history' not in new_config:
            self.config['history'] = history
        if 'scheduled_tasks' not in new_config:
            self.config['scheduled_tasks'] = scheduled_tasks
        
        # Save updated config
        self._save_config_file()
    
    def get_history(self) -> List[Dict[str, Any]]:
        """
        Get the scraping history
        
        Returns:
            List of history entries
        """
        return self.config.get('history', [])
    
    def add_history_item(self, item: Dict[str, Any]):
        """
        Add an item to the scraping history
        
        Args:
            item: History item to add
        """
        # Ensure history list exists
        if 'history' not in self.config:
            self.config['history'] = []
        
        # Add timestamp if not present
        if 'date' not in item:
            item['date'] = datetime.now().isoformat()
        
        # Add to history
        self.config['history'].append(item)
        
        # Limit history size
        max_history_items = 100
        if len(self.config['history']) > max_history_items:
            self.config['history'] = self.config['history'][-max_history_items:]
        
        # Save config
        self._save_config_file()
        logger.info(f"Added history item: {item.get('type')} - {item.get('date')}")
    
    def delete_history_item(self, index: int) -> bool:
        """
        Delete a history item by index
        
        Args:
            index: Index of the item to delete
            
        Returns:
            bool: True if successful
        """
        try:
            if 'history' in self.config and 0 <= index < len(self.config['history']):
                # Get item for logging
                item = self.config['history'][index]
                
                # Remove item
                self.config['history'].pop(index)
                
                # Save config
                self._save_config_file()
                logger.info(f"Deleted history item at index {index}: {item.get('type')} - {item.get('date')}")
                return True
            else:
                logger.warning(f"Invalid history index: {index}")
                return False
        except Exception as e:
            logger.error(f"Error deleting history item: {e}")
            return False
    
    def get_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """
        Get the list of scheduled tasks
        
        Returns:
            List of scheduled task entries
        """
        return self.config.get('scheduled_tasks', [])
    
    def add_scheduled_task(self, task: Dict[str, Any]):
        """
        Add a scheduled task
        
        Args:
            task: Task dictionary to add
        """
        # Ensure scheduled_tasks list exists
        if 'scheduled_tasks' not in self.config:
            self.config['scheduled_tasks'] = []
        
        # Add task
        self.config['scheduled_tasks'].append(task)
        
        # Save config
        self._save_config_file()
        logger.info(f"Added scheduled task: {task.get('name')} ({task.get('task_type')})")
    
    def remove_scheduled_task(self, task_id: str) -> bool:
        """
        Remove a scheduled task by ID
        
        Args:
            task_id: ID of the task to remove
            
        Returns:
            bool: True if successful
        """
        try:
            if 'scheduled_tasks' in self.config:
                # Find task by ID (name)
                for i, task in enumerate(self.config['scheduled_tasks']):
                    if task.get('name') == task_id:
                        # Remove task
                        removed_task = self.config['scheduled_tasks'].pop(i)
                        
                        # Save config
                        self._save_config_file()
                        logger.info(f"Removed scheduled task: {removed_task.get('name')} ({removed_task.get('task_type')})")
                        return True
            
            logger.warning(f"Task ID not found: {task_id}")
            return False
        except Exception as e:
            logger.error(f"Error removing scheduled task: {e}")
            return False
    
    def update_scheduled_task(self, task_id: str, updated_task: Dict[str, Any]) -> bool:
        """
        Update an existing scheduled task
        
        Args:
            task_id: ID of the task to update
            updated_task: Updated task dictionary
            
        Returns:
            bool: True if successful
        """
        try:
            if 'scheduled_tasks' in self.config:
                # Find task by ID (name)
                for i, task in enumerate(self.config['scheduled_tasks']):
                    if task.get('name') == task_id:
                        # Update task
                        self.config['scheduled_tasks'][i] = updated_task
                        
                        # Save config
                        self._save_config_file()
                        logger.info(f"Updated scheduled task: {updated_task.get('name')} ({updated_task.get('task_type')})")
                        return True
            
            logger.warning(f"Task ID not found for update: {task_id}")
            return False
        except Exception as e:
            logger.error(f"Error updating scheduled task: {e}")
            return False
    
    def add_search_term_to_history(self, term: str):
        """
        Add a search term to the search history
        
        Args:
            term: Search term to add
        """
        if 'search_history' not in self.config:
            self.config['search_history'] = []
        
        # Remove if already exists to avoid duplicates
        if term in self.config['search_history']:
            self.config['search_history'].remove(term)
        
        # Add to beginning of history
        self.config['search_history'].insert(0, term)
        
        # Limit search history size
        max_search_history = 20
        if len(self.config['search_history']) > max_search_history:
            self.config['search_history'] = self.config['search_history'][:max_search_history]
        
        # Save config
        self._save_config_file()
        logger.debug(f"Added term to search history: {term}")