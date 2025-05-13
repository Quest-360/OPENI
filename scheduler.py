"""
Scheduler Module
---------------
Provides functionality for scheduling scraping tasks using APScheduler.
Handles one-time, daily, weekly, and monthly schedules.
"""
import logging
import threading
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
import time
import os

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

# Set up logging
logger = logging.getLogger("ZeptoScraper.Scheduler")

class ScheduleManager:
    """Manages scheduled scraping tasks and their execution"""
    
    def __init__(self, scraper, config_manager):
        """
        Initialize the Schedule Manager
        
        Args:
            scraper: The ZeptoScraper instance to use for executing tasks
            config_manager: ConfigManager instance for saving/loading schedules
        """
        self.scraper = scraper
        self.config_manager = config_manager
        self.scheduler = BackgroundScheduler()
        self.active_jobs = {}
        self.is_running = False
    
    def start_service(self):
        """Start the scheduler service"""
        if not self.is_running:
            try:
                self.scheduler.start()
                self.is_running = True
                logger.info("Scheduler service started")
                
                # Restore saved schedules
                self._restore_schedules()
            except Exception as e:
                logger.error(f"Failed to start scheduler service: {e}")
    
    def stop_service(self):
        """Stop the scheduler service"""
        if self.is_running:
            try:
                self.scheduler.shutdown()
                self.is_running = False
                logger.info("Scheduler service stopped")
            except Exception as e:
                logger.error(f"Error shutting down scheduler service: {e}")
    
    def add_task(self, name: str, task_type: str, frequency: str, time_value: str, 
                task_params: Dict[str, Any]) -> bool:
        """
        Add a new scheduled task
        
        Args:
            name: Name of the task
            task_type: "search" or "category"
            frequency: "once", "daily", "weekly", or "monthly"
            time_value: Time in "HH:MM" format
            task_params: Dictionary of task-specific parameters
            
        Returns:
            bool: True if task was successfully added
        """
        try:
            # Create task dictionary
            task = {
                "name": name,
                "task_type": task_type,
                "frequency": frequency,
                "time": time_value,
                "params": task_params
            }
            
            # Parse time
            hour, minute = map(int, time_value.split(':'))
            
            # Create trigger based on frequency
            if frequency == "once":
                # One-time schedule
                run_date = datetime.now().replace(hour=hour, minute=minute)
                if run_date < datetime.now():
                    # If the time has already passed today, schedule for tomorrow
                    run_date = run_date + timedelta(days=1)
                
                trigger = DateTrigger(run_date=run_date)
                task["next_run"] = run_date.strftime("%Y-%m-%d %H:%M")
            
            elif frequency == "daily":
                # Daily schedule
                trigger = CronTrigger(hour=hour, minute=minute)
                task["next_run"] = f"Daily at {hour:02d}:{minute:02d}"
            
            elif frequency == "weekly":
                # Weekly schedule
                current_weekday = datetime.now().weekday()
                trigger = CronTrigger(day_of_week=current_weekday, hour=hour, minute=minute)
                weekday_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][current_weekday]
                task["next_run"] = f"Weekly on {weekday_name} at {hour:02d}:{minute:02d}"
            
            elif frequency == "monthly":
                # Monthly schedule
                current_day = datetime.now().day
                trigger = CronTrigger(day=current_day, hour=hour, minute=minute)
                task["next_run"] = f"Monthly on day {current_day} at {hour:02d}:{minute:02d}"
            
            else:
                logger.error(f"Invalid frequency: {frequency}")
                return False
            
            # Add specific task parameters based on type
            if task_type == "search":
                # For search tasks
                job = self.scheduler.add_job(
                    self._run_search_scrape,
                    trigger=trigger,
                    args=[
                        task_params.get("term", ""),
                        task_params.get("output_dir", "./results"),
                        task_params.get("max_products", None)
                    ],
                    id=name,
                    replace_existing=True
                )
                task["term"] = task_params.get("term", "")
            
            else:  # category
                # For category tasks
                categories = [task_params.get("term")] if task_params.get("term") != "ALL" else list(self.scraper.CATEGORY_URLS.keys())
                job = self.scheduler.add_job(
                    self._run_category_scrape,
                    trigger=trigger,
                    args=[
                        categories,
                        task_params.get("output_dir", "./results"),
                        task_params.get("pdp_scrape", False)
                    ],
                    id=name,
                    replace_existing=True
                )
                task["categories"] = categories
            
            # Store job reference
            self.active_jobs[name] = job
            
            # Save task to configuration
            self.config_manager.add_scheduled_task(task)
            
            logger.info(f"Added scheduled task: {name} ({task_type}) - {frequency}")
            return True
        
        except Exception as e:
            logger.error(f"Error adding scheduled task: {e}")
            return False
    
    def remove_task(self, task_id: str) -> bool:
        """
        Remove a scheduled task
        
        Args:
            task_id: ID of the task to remove
            
        Returns:
            bool: True if task was successfully removed
        """
        try:
            # Remove job from scheduler
            if task_id in self.active_jobs:
                self.scheduler.remove_job(task_id)
                del self.active_jobs[task_id]
            
            # Remove from configuration
            success = self.config_manager.remove_scheduled_task(task_id)
            
            if success:
                logger.info(f"Removed scheduled task: {task_id}")
            
            return success
        
        except Exception as e:
            logger.error(f"Error removing scheduled task: {e}")
            return False
    
    def get_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """
        Get a list of all scheduled tasks
        
        Returns:
            List of task dictionaries
        """
        return self.config_manager.get_scheduled_tasks()
    
    def _restore_schedules(self):
        """Restore saved schedules from config"""
        tasks = self.config_manager.get_scheduled_tasks()
        for task in tasks:
            try:
                name = task["name"]
                task_type = task["task_type"]
                frequency = task["frequency"]
                time_value = task["time"]
                params = task["params"]
                
                # Add the task to the scheduler
                success = self.add_task(name, task_type, frequency, time_value, params)
                
                if success:
                    logger.info(f"Restored scheduled task: {name}")
                else:
                    logger.warning(f"Failed to restore scheduled task: {name}")
            
            except Exception as e:
                logger.error(f"Error restoring scheduled task: {e}")
    
    def _run_search_scrape(self, search_term, output_dir="./results", max_products=None):
        """Run a search-based scrape task"""
        try:
            logger.info(f"Running scheduled search scrape for term: {search_term}")
            
            # Make sure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            # Run the search scrape
            if hasattr(self.scraper, "run_search_scrape"):
                # Use the application's method if available
                config = self.config_manager.load_config()
                locations = config.get("default_locations", "Bangalore").split(",")
                self.scraper.run_search_scrape(search_term, locations, output_dir, max_products)
            else:
                # Fallback to direct import
                from attached_assets.V6 import scrape_by_search_term
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = os.path.join(output_dir, f"zepto_search_{search_term.replace(' ', '_')}_{timestamp}.xlsx")
                
                products = scrape_by_search_term(search_term, max_products=max_products)
                
                # Export results (simplified for scheduled task)
                import pandas as pd
                df = pd.DataFrame([p.to_dict() for p in products])
                df.to_excel(output_file, index=False)
                
                logger.info(f"Scheduled search scrape completed with {len(products)} products")
                
                # Add to history
                history_item = {
                    "date": datetime.now().isoformat(),
                    "type": "search",
                    "term": search_term,
                    "product_count": len(products),
                    "output_file": output_file,
                    "status": "success",
                    "scheduled": True
                }
                self.config_manager.add_history_item(history_item)
        
        except Exception as e:
            logger.error(f"Error in scheduled search scrape: {e}")
            
            # Add failed task to history
            history_item = {
                "date": datetime.now().isoformat(),
                "type": "search",
                "term": search_term,
                "product_count": 0,
                "status": "error",
                "error": str(e),
                "scheduled": True
            }
            self.config_manager.add_history_item(history_item)
    
    def _run_category_scrape(self, categories, output_dir="./results", pdp_scrape=False):
        """Run a category-based scrape task"""
        try:
            logger.info(f"Running scheduled category scrape for: {', '.join(categories)}")
            
            # Make sure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            # Run the category scrape
            if hasattr(self.scraper, "run_category_scrape"):
                # Use the application's method if available
                config = self.config_manager.load_config()
                locations = config.get("default_locations", "Bangalore").split(",")
                self.scraper.run_category_scrape(categories, locations, output_dir, pdp_scrape)
            else:
                # Fallback to direct import
                from attached_assets.V6 import scrape_category, CATEGORY_URLS
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                all_products = []
                
                for category in categories:
                    category_url = CATEGORY_URLS.get(category)
                    if not category_url:
                        logger.warning(f"No URL found for category: {category}")
                        continue
                    
                    # Scrape the category
                    products = scrape_category(category_url, pdp_scrape=pdp_scrape)
                    for product in products:
                        product.category = category
                    
                    all_products.extend(products)
                
                # Export results (simplified for scheduled task)
                output_file = os.path.join(output_dir, f"zepto_category_scrape_{timestamp}.xlsx")
                
                import pandas as pd
                df = pd.DataFrame([p.to_dict() for p in all_products])
                df.to_excel(output_file, index=False)
                
                logger.info(f"Scheduled category scrape completed with {len(all_products)} products")
                
                # Add to history
                history_item = {
                    "date": datetime.now().isoformat(),
                    "type": "category",
                    "categories": categories,
                    "product_count": len(all_products),
                    "output_file": output_file,
                    "status": "success",
                    "scheduled": True
                }
                self.config_manager.add_history_item(history_item)
        
        except Exception as e:
            logger.error(f"Error in scheduled category scrape: {e}")
            
            # Add failed task to history
            history_item = {
                "date": datetime.now().isoformat(),
                "type": "category",
                "categories": categories,
                "product_count": 0,
                "status": "error",
                "error": str(e),
                "scheduled": True
            }
            self.config_manager.add_history_item(history_item)