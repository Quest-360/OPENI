"""
Enhanced Zepto E-commerce Scraper
---------------------------------
A complete solution for scraping product data from Zepto with an enhanced UI,
scheduling capabilities, rate limiting avoidance, and optimized performance.

Version: 3.0.0
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import os
import re
import logging
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Union, Callable

# Import original scraper core functionality 
from attached_assets.V6 import (
    # Constants
    CATEGORY_URLS, DEFAULT_TIMEOUT, DEFAULT_MAX_SCROLLS, DEFAULT_SCROLL_PAUSE,
    
    # Core scraper classes and functions
    Product, WebDriverWait, By, EC, enhanced_scroll, enrich_from_pdp,
    scrape_site as scrape_by_search_term, scrape_category,
    set_location, Options, webdriver,
    
    # Export utilities
    export_to_excel, export_to_csv, create_location_comparison
)

# Import modules for enhanced functionality
import ui_components
from rate_limiter import RateLimiter
from config_manager import ConfigManager
from scheduler import ScheduleManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("zepto_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ZeptoScraper")

class EnhancedZeptoScraperApp:
    def __init__(self, root):
        # Initialize the application window
        self.root = root
        self.root.title("Heritage Foods - Zepto Scraper")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Set application icon
        try:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons", "heritage_logo.png")
            if os.path.exists(icon_path):
                icon_image = tk.PhotoImage(file=icon_path)
                root.iconphoto(True, icon_image)
                # Store the image reference to prevent garbage collection
                self.icon_image = icon_image
        except Exception as e:
            logger.warning(f"Could not load application icon: {e}")
        
        # Initialize managers
        self.config_manager = ConfigManager()
        self.rate_limiter = RateLimiter()
        self.scheduler = ScheduleManager(self, self.config_manager)
        
        # Get theme from config if exists, otherwise use Heritage theme
        config = self.config_manager.load_config()
        ui_config = config.get("ui", {})
        self.current_theme = ui_config.get("theme", "heritage")
        
        # Set up UI components
        ui_components.setup_theme(self.root, theme_name=self.current_theme)
        
        # Add Heritage logo header before the main frame
        try:
            from PIL import Image, ImageTk
            
            header_frame = ttk.Frame(self.root)
            header_frame.pack(fill=tk.X, padx=10, pady=5)
            
            # Load the Heritage logo
            logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons", "heritage_logo.png")
            if os.path.exists(logo_path):
                # Open and resize the image to a reasonable size
                logo_img = Image.open(logo_path)
                # Use LANCZOS if available (Pillow >= 9.1.0) or ANTIALIAS for older versions
                # Fallback to a numeric value if constants aren't available
                resize_method = getattr(Image, 'LANCZOS', getattr(Image, 'ANTIALIAS', 3))
                logo_img = logo_img.resize((120, 60), resize_method)
                logo_photo = ImageTk.PhotoImage(logo_img)
                
                # Create label with logo
                logo_label = ttk.Label(header_frame, image=logo_photo)
                logo_label.image = logo_photo  # Keep a reference
                logo_label.pack(side=tk.LEFT, padx=5)
                
                # Add title next to logo
                title_label = ttk.Label(header_frame, text="Zepto Price Scraper", 
                                       font=("Helvetica", 16, "bold"), 
                                       foreground="#008736")  # Heritage green
                title_label.pack(side=tk.LEFT, padx=10)
                
                # Add version on the right
                version_label = ttk.Label(header_frame, text="v3.0.0", 
                                         font=("Helvetica", 10), 
                                         foreground="#666666")
                version_label.pack(side=tk.RIGHT, padx=5)
        except Exception as e:
            logger.warning(f"Could not load Heritage logo in header: {e}")
        
        self.main_frame = ui_components.create_main_frame(self.root)
        self.tabs = ui_components.create_tabs(self.main_frame)
        
        # Initialize the tabs
        self.init_search_tab()
        self.init_category_tab()
        self.init_schedule_tab()
        self.init_history_tab()
        self.init_settings_tab()
        
        # Set up menu bar
        self.create_menu()
        
        # Load configuration
        self.load_config()
        
        # Initialize flags and data
        self.stop_requested = False
        self.scraping_active = False
        self.data = []
        
        # Start scheduler service
        self.scheduler.start_service()
        
        # Set up app closing handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        logger.info("Application initialized")
    
    def create_menu(self):
        """Create application menu bar"""
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exit", command=self.on_closing)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Open Results Folder", command=self.open_results_folder)
        tools_menu.add_command(label="Clear History", command=self.clear_history)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Help", command=lambda: ui_components.show_help_dialog(self.root))
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def open_results_folder(self):
        """Open the results folder in file explorer"""
        results_dir = self.search_components.get("output_dir").get()
        
        # Make sure directory exists
        os.makedirs(results_dir, exist_ok=True)
        
        # Open folder in file explorer
        try:
            import subprocess
            if os.name == 'nt':  # Windows
                os.startfile(results_dir)
            elif os.name == 'posix':  # Linux/macOS
                subprocess.Popen(['xdg-open', results_dir])
        except Exception as e:
            logger.error(f"Error opening results folder: {e}")
            messagebox.showerror("Error", f"Could not open results folder: {e}")
    
    def clear_history(self):
        """Clear the scraping history"""
        if messagebox.askyesno("Confirm Clear History", "Are you sure you want to clear all scraping history?"):
            try:
                # Get current configuration
                config = self.config_manager.load_config()
                
                # Clear history
                config["history"] = []
                
                # Save updated configuration
                self.config_manager.save_config(config)
                
                # Update history list
                self.update_history_list()
                
                messagebox.showinfo("History Cleared", "Scraping history has been cleared.")
            except Exception as e:
                logger.error(f"Error clearing history: {e}")
                messagebox.showerror("Error", f"Could not clear history: {e}")
    
    def show_about(self):
        """Show about dialog with Heritage Foods branding"""
        about_text = """
        Heritage Foods Zepto Scraper
        Version 3.0.0
        
        An advanced tool for scraping Zepto e-commerce data with:
        • Heritage Foods branded UI with improved visibility
        • Search and category-based scraping
        • Task scheduling for automated data collection
        • Rate limiting and 429 error prevention
        • Complete data extraction (brand, MRP, discount%)
        • Result comparison across multiple locations
        • Export to Excel and CSV with enhanced formatting
        
        Created for Heritage Foods price monitoring operations.
        Copyright © 2025 Heritage Foods Ltd.
        """
        
        try:
            # Create a custom about dialog with logo
            about_window = tk.Toplevel(self.root)
            about_window.title("About Heritage Foods Zepto Scraper")
            about_window.geometry("500x450")
            about_window.resizable(False, False)
            about_window.transient(self.root)  # Set as transient to main window
            about_window.grab_set()  # Make modal
            
            # Set Herirage colors
            HERITAGE_GREEN = "#008736"
            HERITAGE_RED = "#E31E24"
            
            # Header with logo
            header_frame = ttk.Frame(about_window)
            header_frame.pack(fill=tk.X, padx=20, pady=20)
            
            # Try to add logo
            try:
                from PIL import Image, ImageTk
                
                logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons", "heritage_logo.png")
                if os.path.exists(logo_path):
                    # Open and resize the image
                    logo_img = Image.open(logo_path)
                    # Use a compatible resize method
                    resize_method = getattr(Image, 'LANCZOS', getattr(Image, 'ANTIALIAS', 3))
                    logo_img = logo_img.resize((150, 75), resize_method)
                    logo_photo = ImageTk.PhotoImage(logo_img)
                    
                    # Create label with logo
                    logo_label = ttk.Label(header_frame, image=logo_photo)
                    logo_label.image = logo_photo  # Keep a reference
                    logo_label.pack(pady=10)
            except Exception as e:
                logger.warning(f"Could not load logo in about dialog: {e}")
            
            # Add title
            title_label = ttk.Label(header_frame, text="Heritage Foods Zepto Scraper", 
                                  font=("Helvetica", 16, "bold"), foreground=HERITAGE_GREEN)
            title_label.pack(pady=5)
            
            version_label = ttk.Label(header_frame, text="Version 3.0.0", font=("Helvetica", 10))
            version_label.pack()
            
            # Separator
            ttk.Separator(about_window, orient="horizontal").pack(fill=tk.X, padx=20, pady=10)
            
            # Content
            content_frame = ttk.Frame(about_window)
            content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            feature_label = ttk.Label(content_frame, text="Features:", font=("Helvetica", 12, "bold"))
            feature_label.pack(anchor="w", pady=(0, 5))
            
            features = [
                "• Heritage Foods branded UI with improved visibility",
                "• Search and category-based scraping",
                "• Task scheduling for automated data collection",
                "• Rate limiting and 429 error prevention",
                "• Complete data extraction (brand, MRP, discount%)",
                "• Result comparison across multiple locations",
                "• Export to Excel and CSV with enhanced formatting"
            ]
            
            for feature in features:
                feature_item = ttk.Label(content_frame, text=feature, wraplength=450)
                feature_item.pack(anchor="w", padx=10, pady=2)
            
            # Copyright
            ttk.Separator(about_window, orient="horizontal").pack(fill=tk.X, padx=20, pady=10)
            copyright_label = ttk.Label(about_window, text=f"Copyright © 2025 Heritage Foods Ltd.", 
                                      font=("Helvetica", 9))
            copyright_label.pack(pady=5)
            
            # Close button
            close_button = ttk.Button(about_window, text="Close", command=about_window.destroy)
            close_button.pack(pady=10)
            
            # Center the window on the screen
            about_window.update_idletasks()
            width = about_window.winfo_width()
            height = about_window.winfo_height()
            x = (about_window.winfo_screenwidth() // 2) - (width // 2)
            y = (about_window.winfo_screenheight() // 2) - (height // 2)
            about_window.geometry(f"{width}x{height}+{x}+{y}")
            
            # Make window modal
            about_window.focus_set()
            about_window.wait_window()
            
        except Exception as e:
            # Fallback to simple dialog if custom one fails
            logger.error(f"Error showing custom about dialog: {e}")
            messagebox.showinfo("About Heritage Foods Zepto Scraper", about_text)
    
    def init_search_tab(self):
        """Initialize the search-based scraping tab"""
        self.search_components = ui_components.create_search_tab(
            self.tabs["search_tab"], 
            self.start_search_scrape,
            self.stop_scrape
        )
        
        # Add export button handlers
        self.search_components["export_excel_btn"].configure(command=lambda: self.export_results('excel'))
        self.search_components["export_csv_btn"].configure(command=lambda: self.export_results('csv'))
        self.search_components["export_comparison_btn"].configure(command=self.export_comparison)
    
    def init_category_tab(self):
        """Initialize the category-based scraping tab"""
        self.category_components = ui_components.create_category_tab(
            self.tabs["category_tab"],
            self.start_category_scrape,
            self.stop_scrape
        )
        
        # Add export button handlers
        self.category_components["export_excel_btn"].configure(command=lambda: self.export_category_results('excel'))
        self.category_components["export_csv_btn"].configure(command=lambda: self.export_category_results('csv'))
        self.category_components["export_comparison_btn"].configure(command=self.export_category_comparison)
    
    def init_schedule_tab(self):
        """Initialize the scheduling tab"""
        self.schedule_components = ui_components.create_schedule_tab(
            self.tabs["schedule_tab"],
            self.add_schedule,
            self.remove_schedule,
            self.scheduler.get_scheduled_tasks
        )
    
    def init_history_tab(self):
        """Initialize the history tab"""
        self.history_components = ui_components.create_history_tab(
            self.tabs["history_tab"],
            self.view_history_item,
            self.delete_history_item,
            self.rerun_history_item
        )
        
        # Update history list
        self.update_history_list()
    
    def init_settings_tab(self):
        """Initialize the settings tab"""
        self.settings_components = ui_components.create_settings_tab(
            self.tabs["settings_tab"],
            self.save_settings,
            self.apply_theme
        )
        
        # Configure reset button
        self.settings_components["reset_btn"].configure(command=self.reset_settings)
    
    def apply_theme(self, theme_name):
        """Apply the selected theme"""
        ui_components.setup_theme(self.root, theme_name=theme_name)
        self.current_theme = theme_name
        messagebox.showinfo("Theme Changed", f"Applied {theme_name} theme. Save settings to make it permanent.")
    
    def load_config(self):
        """Load saved configuration settings"""
        config = self.config_manager.load_config()
        
        # Load theme settings
        ui_config = config.get("ui", {})
        theme = ui_config.get("theme", "heritage")
        self.settings_components["theme"].set(theme)
        
        # Load rate limiter settings
        rate_config = config.get("rate_limiter", {})
        self.settings_components["min_delay"].set(str(rate_config.get("min_delay", 1.0)))
        self.settings_components["max_delay"].set(str(rate_config.get("max_delay", 3.0)))
        self.settings_components["rpm_limit"].set(str(rate_config.get("rpm_limit", 20)))
        
        # Load browser settings
        browser_config = config.get("browser", {})
        self.settings_components["browser_type"].set(browser_config.get("type", "chrome"))
        self.settings_components["default_headless"].set(browser_config.get("headless", False))
        
        # Load default locations
        self.settings_components["default_locations"].set(config.get("default_locations", "Bangalore"))
        
        # Apply rate limiter configuration
        self.rate_limiter.configure(
            min_delay=float(self.settings_components["min_delay"].get()),
            max_delay=float(self.settings_components["max_delay"].get()),
            rpm_limit=int(self.settings_components["rpm_limit"].get())
        )
        
        logger.info("Configuration loaded")
    
    def save_settings(self):
        """Save current settings to configuration file"""
        try:
            # Get form values
            min_delay = float(self.settings_components["min_delay"].get())
            max_delay = float(self.settings_components["max_delay"].get())
            rpm_limit = int(self.settings_components["rpm_limit"].get())
            browser_type = self.settings_components["browser_type"].get()
            default_headless = self.settings_components["default_headless"].get()
            default_locations = self.settings_components["default_locations"].get()
            
            # Validate settings
            if min_delay < 0 or max_delay < 0 or rpm_limit < 1:
                messagebox.showerror("Invalid Settings", "Delay and rate limit values must be positive numbers.")
                return
            
            if min_delay > max_delay:
                messagebox.showerror("Invalid Settings", "Minimum delay cannot be greater than maximum delay.")
                return
            
            # Create config dict
            config = {
                "rate_limiter": {
                    "min_delay": min_delay,
                    "max_delay": max_delay,
                    "rpm_limit": rpm_limit
                },
                "browser": {
                    "type": browser_type,
                    "headless": default_headless
                },
                "default_locations": default_locations,
                "ui": {
                    "theme": self.settings_components["theme"].get()
                }
            }
            
            # Save config
            self.config_manager.save_config(config)
            
            # Apply rate limiter configuration
            self.rate_limiter.configure(
                min_delay=min_delay,
                max_delay=max_delay,
                rpm_limit=rpm_limit
            )
            
            messagebox.showinfo("Settings Saved", "Your settings have been saved successfully.")
            logger.info("Settings saved")
        except ValueError:
            messagebox.showerror("Invalid Settings", "Please enter valid numeric values for delay and rate limit settings.")
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            messagebox.showerror("Error", f"Failed to save settings: {e}")
    
    def reset_settings(self):
        """Reset settings to defaults"""
        if messagebox.askyesno("Confirm Reset", "Are you sure you want to reset all settings to defaults?"):
            # Set default values
            self.settings_components["min_delay"].set("1.0")
            self.settings_components["max_delay"].set("3.0")
            self.settings_components["rpm_limit"].set("20")
            self.settings_components["browser_type"].set("chrome")
            self.settings_components["default_headless"].set(False)
            self.settings_components["default_locations"].set("Bangalore")
            
            # Save defaults
            self.save_settings()
    
    def start_search_scrape(self):
        """Start scraping based on search term"""
        # Validate inputs
        term = self.search_components["search_term"].get().strip()
        if not term:
            messagebox.showerror("Error", "Please enter a search term")
            return
        
        # Parse locations
        locations = [loc.strip() for loc in self.search_components["locations"].get().split(",") if loc.strip()]
        if not locations:
            messagebox.showerror("Error", "Please enter at least one location")
            return
        
        # Parse max products
        try:
            max_products = int(self.search_components["max_products"].get()) if self.search_components["max_products"].get() else None
        except ValueError:
            messagebox.showerror("Error", "Max products must be a number")
            return
        
        # Get output directory
        output_dir = self.search_components["output_dir"].get()
        os.makedirs(output_dir, exist_ok=True)
        
        # Update UI state
        self.search_components["search_button"].config(state=tk.DISABLED)
        self.search_components["stop_button"].config(state=tk.NORMAL)
        self.search_components["progress_bar"]["value"] = 0
        
        # Clear log
        self.search_components["log_area"].delete(1.0, tk.END)
        self.search_components["log_area"].insert(tk.END, f"Starting search for: {term}\n")
        if len(locations) == 1:
            self.search_components["log_area"].insert(tk.END, f"Location: {locations[0]}\n")
        else:
            self.search_components["log_area"].insert(tk.END, f"Locations: {', '.join(locations)}\n")
        
        if max_products:
            self.search_components["log_area"].insert(tk.END, f"Max products: {max_products}\n")
        
        self.search_components["log_area"].insert(tk.END, "Initializing scraper...\n\n")
        self.search_components["log_area"].see(tk.END)
        
        # Reset stopping flag
        self.stop_requested = False
        self.scraping_active = True
        
        # Start scraping in a separate thread
        threading.Thread(
            target=self.run_search_scrape,
            args=(term, locations, output_dir, max_products),
            daemon=True
        ).start()
    
    def run_search_scrape(self, search_term, locations, output_dir, max_products):
        """Run the search term scraping in a background thread"""
        try:
            # Record start time
            start_time = time.time()
            
            # Define a progress callback function
            def progress_callback(percent):
                self.search_components["progress_bar"]["value"] = percent
            
            # Initialize results container
            results_dict = {}
            
            # Scrape each location
            for idx, location in enumerate(locations):
                # Calculate progress offset for this location
                base_progress = int((idx / len(locations)) * 100)
                progress_scale = 100 / len(locations)
                
                # Create a scaled progress callback
                def loc_progress_callback(percent):
                    scaled_percent = base_progress + (percent * progress_scale / 100)
                    progress_callback(scaled_percent)
                
                # Log location start
                self.search_components["log_area"].insert(tk.END, f"\n🔍 Location {idx+1}/{len(locations)}: {location}\n")
                self.search_components["log_area"].see(tk.END)
                
                # Check if scraping should stop
                if self.stop_requested:
                    self.search_components["log_area"].insert(tk.END, "Scraping stopped by user\n")
                    break
                
                # Perform the scrape for this location
                try:
                    # Use the existing scrape_by_search_term function from V6
                    location_results = scrape_by_search_term(
                        "https://www.zeptonow.com", # base_url
                        search_term, 
                        location=location,
                        max_products=max_products,
                        progress_callback=loc_progress_callback,
                        headless=self.search_components["headless_mode"].get()
                    )
                    
                    # Add location to each product for tracking
                    for product in location_results:
                        product.store_name = location
                    
                    # Store results
                    results_dict[location] = location_results
                    
                    # Log success
                    self.search_components["log_area"].insert(tk.END, f"✅ Found {len(location_results)} products in {location}\n")
                    self.search_components["log_area"].see(tk.END)
                except Exception as e:
                    self.search_components["log_area"].insert(tk.END, f"❌ Error scraping {location}: {str(e)}\n")
                    results_dict[location] = []
            
            # Combine all results
            all_products = []
            for location, products in results_dict.items():
                all_products.extend(products)
            
            # Save results
            if all_products:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = os.path.join(output_dir, f"zepto_search_{search_term.replace(' ', '_')}_{timestamp}.xlsx")
                
                # Export to Excel
                export_to_excel(all_products, output_file, results_dict)
                
                # Log completion
                elapsed_time = time.time() - start_time
                self.search_components["log_area"].insert(tk.END, f"\n✅ Scraping completed in {elapsed_time:.1f} seconds\n")
                self.search_components["log_area"].insert(tk.END, f"📊 Found {len(all_products)} products across {len(locations)} locations\n")
                self.search_components["log_area"].insert(tk.END, f"💾 Results saved to: {output_file}\n")
                
                # Save to history
                history_item = {
                    "date": datetime.now().isoformat(),
                    "type": "search",
                    "term": search_term,
                    "locations": locations,
                    "product_count": len(all_products),
                    "output_file": output_file,
                    "status": "success"
                }
                self.config_manager.add_history_item(history_item)
                self.update_history_list()
                
                # Enable export buttons
                self.search_components["export_excel_btn"].config(state=tk.NORMAL)
                self.search_components["export_csv_btn"].config(state=tk.NORMAL)
                
                # Save data for exports
                self.data = all_products
                self.location_results = results_dict
                
                # Enable comparison export if multiple locations
                if len(locations) > 1:
                    self.search_components["export_comparison_btn"].config(state=tk.NORMAL)
                    self.search_components["log_area"].insert(tk.END, "\n📊 You can export a location comparison to analyze price differences.\n")
                else:
                    self.search_components["export_comparison_btn"].config(state=tk.DISABLED)
            else:
                self.search_components["log_area"].insert(tk.END, "\n⚠️ No products found\n")
                
                # Save to history
                history_item = {
                    "date": datetime.now().isoformat(),
                    "type": "search",
                    "term": search_term,
                    "locations": locations,
                    "product_count": 0,
                    "status": "no_results"
                }
                self.config_manager.add_history_item(history_item)
                self.update_history_list()
        
        except Exception as e:
            # Log error
            self.search_components["log_area"].insert(tk.END, f"\n❌ Error during scraping: {str(e)}\n")
            import traceback
            self.search_components["log_area"].insert(tk.END, traceback.format_exc())
            
            # Save to history
            history_item = {
                "date": datetime.now().isoformat(),
                "type": "search",
                "term": search_term,
                "locations": locations,
                "product_count": 0,
                "status": "error",
                "error": str(e)
            }
            self.config_manager.add_history_item(history_item)
            self.update_history_list()
        
        finally:
            # Re-enable buttons
            self.search_components["search_button"].config(state=tk.NORMAL)
            self.search_components["stop_button"].config(state=tk.DISABLED)
            self.scraping_active = False
            
            # Ensure log is visible
            self.search_components["log_area"].see(tk.END)
    
    def start_category_scrape(self):
        """Start scraping based on category"""
        # Get selected categories
        selected_categories = []
        for category, var in self.category_components["category_vars"].items():
            if var.get():
                selected_categories.append(category)
        
        if not selected_categories:
            messagebox.showerror("Error", "Please select at least one category")
            return
        
        # Parse locations
        locations = [loc.strip() for loc in self.category_components["locations"].get().split(",") if loc.strip()]
        if not locations:
            messagebox.showerror("Error", "Please enter at least one location")
            return
        
        # Parse max products
        try:
            max_products = int(self.category_components["max_products"].get()) if self.category_components["max_products"].get() else None
        except ValueError:
            messagebox.showerror("Error", "Max products must be a number")
            return
        
        # Get output directory
        output_dir = self.category_components["output_dir"].get()
        os.makedirs(output_dir, exist_ok=True)
        
        # Update UI state
        self.category_components["start_button"].config(state=tk.DISABLED)
        self.category_components["stop_button"].config(state=tk.NORMAL)
        self.category_components["progress_bar"]["value"] = 0
        
        # Clear log
        self.category_components["log_area"].delete(1.0, tk.END)
        self.category_components["log_area"].insert(tk.END, f"Starting scrape for {len(selected_categories)} categories: {', '.join(selected_categories)}\n")
        
        if len(locations) == 1:
            self.category_components["log_area"].insert(tk.END, f"Location: {locations[0]}\n")
        else:
            self.category_components["log_area"].insert(tk.END, f"Locations: {', '.join(locations)}\n")
        
        if max_products:
            self.category_components["log_area"].insert(tk.END, f"Max products per category: {max_products}\n")
        
        self.category_components["log_area"].insert(tk.END, "Initializing scraper...\n\n")
        self.category_components["log_area"].see(tk.END)
        
        # Reset stopping flag
        self.stop_requested = False
        self.scraping_active = True
        
        # Start scraping in a separate thread
        threading.Thread(
            target=self.run_category_scrape,
            args=(selected_categories, locations, output_dir, max_products),
            daemon=True
        ).start()
    
    def run_category_scrape(self, categories, locations, output_dir, max_products):
        """Run the category scraping in a background thread"""
        try:
            # Record start time
            start_time = time.time()
            
            # Define a progress callback function
            def progress_callback(percent):
                self.category_components["progress_bar"]["value"] = percent
            
            # Initialize results container
            # Structure: {category: {location: [products]}}
            results_dict = {}
            
            # Calculate total number of category-location combinations
            total_combinations = len(categories) * len(locations)
            combination_idx = 0
            
            # Scrape each category for each location
            for category in categories:
                # Get category URL
                category_url = CATEGORY_URLS.get(category)
                if not category_url:
                    self.category_components["log_area"].insert(tk.END, f"⚠️ No URL found for category: {category}, skipping\n")
                    continue
                
                results_dict[category] = {}
                
                for location in locations:
                    # Check if scraping should stop
                    if self.stop_requested:
                        self.category_components["log_area"].insert(tk.END, "Scraping stopped by user\n")
                        break
                    
                    # Calculate progress for this combination
                    combination_idx += 1
                    base_progress = int((combination_idx - 1) / total_combinations * 100)
                    progress_scale = 100 / total_combinations
                    
                    # Create a scaled progress callback
                    def combo_progress_callback(percent):
                        scaled_percent = base_progress + (percent * progress_scale / 100)
                        progress_callback(scaled_percent)
                    
                    # Log combination start
                    self.category_components["log_area"].insert(tk.END, f"\n📂 Category: {category} | 🔍 Location: {location}\n")
                    self.category_components["log_area"].see(tk.END)
                    
                    # Perform the scrape for this combination
                    try:
                        # Use the existing scrape_category function from V6
                        # First set up a driver with the location
                        chrome_options = Options()
                        if self.category_components["headless_mode"].get():
                            chrome_options.add_argument("--headless")
                        
                        driver = webdriver.Chrome(options=chrome_options)
                        try:
                            # Set location first
                            driver.get("https://www.zeptonow.com")
                            set_location(driver, location)
                            
                            # Then call scrape_category with the driver
                            category_products = scrape_category(
                                driver,
                                category_url,
                                progress_callback=combo_progress_callback,
                                max_products=max_products
                            )
                            
                            # Make sure each product has ALL important PDP data
                            # (brand, product mode, MRP, discount, etc.)
                            # In some cases the V6.py scraper might not get all PDP data
                            for product in category_products:
                                # Check for missing important fields
                                missing_fields = []
                                
                                if not product.brand:
                                    missing_fields.append("brand")
                                if not product.product_type:
                                    missing_fields.append("product_type")
                                if not product.mrp:
                                    missing_fields.append("mrp") 
                                if not product.discount_percent and product.price and product.strikeoff_price:
                                    missing_fields.append("discount_percent")
                                    
                                # Enrich if any important fields are missing
                                if missing_fields:
                                    try:
                                        self.category_components["log_area"].insert(tk.END, f"  → Enriching PDP data for {product.name} (missing: {', '.join(missing_fields)})...\n")
                                        enrich_from_pdp(driver, product)
                                        
                                        # Calculate discount percentage if it's still missing but we have prices
                                        if not product.discount_percent and product.price and product.strikeoff_price:
                                            try:
                                                # Clean price strings and convert to float
                                                price_str = re.sub(r'[^\d.]', '', product.price)
                                                strikeoff_str = re.sub(r'[^\d.]', '', product.strikeoff_price)
                                                
                                                price = float(price_str)
                                                strikeoff = float(strikeoff_str)
                                                
                                                if strikeoff > 0:
                                                    discount = ((strikeoff - price) / strikeoff) * 100
                                                    product.discount_percent = str(round(discount))
                                                    product.discount_amount = str(round(strikeoff - price, 2))
                                            except Exception as calc_err:
                                                self.category_components["log_area"].insert(tk.END, f"  ⚠ Could not calculate discount: {str(calc_err)}\n")
                                    except Exception as e:
                                        self.category_components["log_area"].insert(tk.END, f"  ⚠ Failed to get complete PDP data: {str(e)}\n")
                        finally:
                            driver.quit()
                        
                        # Add category and location to each product
                        for product in category_products:
                            product.category = category
                            product.store_name = location
                        
                        # Store results
                        results_dict[category][location] = category_products
                        
                        # Log success
                        self.category_components["log_area"].insert(tk.END, f"✅ Found {len(category_products)} products in {location}\n")
                        self.category_components["log_area"].see(tk.END)
                    except Exception as e:
                        self.category_components["log_area"].insert(tk.END, f"❌ Error scraping {category} in {location}: {str(e)}\n")
                        results_dict[category][location] = []
            
            # Combine all results into a flat list
            all_products = []
            for category, location_dict in results_dict.items():
                for location, products in location_dict.items():
                    all_products.extend(products)
            
            # Save results
            if all_products:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = os.path.join(output_dir, f"zepto_category_scrape_{timestamp}.xlsx")
                
                # Export to Excel with multiple sheets
                if len(categories) == 1 and len(locations) == 1:
                    # Single category and location - simple export
                    export_to_excel(all_products, output_file)
                else:
                    # Multiple categories or locations - use sheet-based export
                    sheet_data = {}
                    
                    for category, location_dict in results_dict.items():
                        for location, products in location_dict.items():
                            if len(products) > 0:
                                sheet_name = f"{category[:20]}_{location[:10]}"
                                sheet_data[sheet_name] = products
                    
                    # Export with sheets
                    export_to_excel(all_products, output_file, sheet_data)
                
                # Log completion
                elapsed_time = time.time() - start_time
                self.category_components["log_area"].insert(tk.END, f"\n✅ Scraping completed in {elapsed_time:.1f} seconds\n")
                self.category_components["log_area"].insert(tk.END, f"📊 Found {len(all_products)} products across {len(categories)} categories and {len(locations)} locations\n")
                self.category_components["log_area"].insert(tk.END, f"💾 Results saved to: {output_file}\n")
                
                # Save to history
                history_item = {
                    "date": datetime.now().isoformat(),
                    "type": "category",
                    "categories": categories,
                    "locations": locations,
                    "product_count": len(all_products),
                    "output_file": output_file,
                    "status": "success"
                }
                self.config_manager.add_history_item(history_item)
                self.update_history_list()
                
                # Enable export buttons
                self.category_components["export_excel_btn"].config(state=tk.NORMAL)
                self.category_components["export_csv_btn"].config(state=tk.NORMAL)
                
                # Save data for exports
                self.data = all_products
                self.cat_location_results = results_dict
                
                # Enable comparison export if multiple locations
                if len(locations) > 1:
                    self.category_components["export_comparison_btn"].config(state=tk.NORMAL)
                    self.category_components["log_area"].insert(tk.END, "\n📊 You can export a location comparison to analyze price differences.\n")
                else:
                    self.category_components["export_comparison_btn"].config(state=tk.DISABLED)
            else:
                self.category_components["log_area"].insert(tk.END, "\n⚠️ No products found\n")
                
                # Save to history
                history_item = {
                    "date": datetime.now().isoformat(),
                    "type": "category",
                    "categories": categories,
                    "locations": locations,
                    "product_count": 0,
                    "status": "no_results"
                }
                self.config_manager.add_history_item(history_item)
                self.update_history_list()
        
        except Exception as e:
            # Log error
            self.category_components["log_area"].insert(tk.END, f"\n❌ Error during scraping: {str(e)}\n")
            import traceback
            self.category_components["log_area"].insert(tk.END, traceback.format_exc())
            
            # Save to history
            history_item = {
                "date": datetime.now().isoformat(),
                "type": "category",
                "categories": categories,
                "locations": locations,
                "product_count": 0,
                "status": "error",
                "error": str(e)
            }
            self.config_manager.add_history_item(history_item)
            self.update_history_list()
        
        finally:
            # Re-enable buttons
            self.category_components["start_button"].config(state=tk.NORMAL)
            self.category_components["stop_button"].config(state=tk.DISABLED)
            self.scraping_active = False
            
            # Ensure log is visible
            self.category_components["log_area"].see(tk.END)
    
    def stop_scrape(self):
        """Stop the current scraping operation"""
        self.stop_requested = True
        logger.info("User requested to stop scraping")
    
    def export_results(self, export_type):
        """Export search results to Excel or CSV"""
        if not hasattr(self, 'data') or not self.data:
            messagebox.showerror("Error", "No data to export")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if export_type == 'excel':
            filename = filedialog.asksaveasfilename(
                defaultextension='.xlsx',
                filetypes=[('Excel files', '*.xlsx')],
                initialfile=f"zepto_products_{timestamp}.xlsx"
            )
            if filename:
                try:
                    # Check if we have location-specific results
                    location_results = getattr(self, 'location_results', None)
                    
                    if export_to_excel(self.data, filename, location_results):
                        messagebox.showinfo("Success", f"Data exported to {filename}")
                        self.search_components["log_area"].insert(tk.END, f"✅ Data exported to {filename}\n")
                        
                        # If we have multiple locations, mention the per-location sheets
                        if location_results and len(location_results) > 1:
                            self.search_components["log_area"].insert(tk.END, f"📊 Each location's data is in a separate sheet in the Excel file.\n")
                        
                        self.search_components["log_area"].see(tk.END)
                    else:
                        messagebox.showerror("Error", "Failed to export data")
                except Exception as e:
                    logger.error(f"Error exporting to Excel: {e}")
                    messagebox.showerror("Error", f"Failed to export: {e}")
        
        elif export_type == 'csv':
            filename = filedialog.asksaveasfilename(
                defaultextension='.csv',
                filetypes=[('CSV files', '*.csv')],
                initialfile=f"zepto_products_{timestamp}.csv"
            )
            if filename:
                try:
                    # Check if we have location-specific results
                    location_results = getattr(self, 'location_results', None)
                    
                    if export_to_csv(self.data, filename, location_results):
                        messagebox.showinfo("Success", f"Data exported to {filename}")
                        self.search_components["log_area"].insert(tk.END, f"✅ Data exported to {filename}\n")
                        
                        # If we have multiple locations, mention the per-location files
                        if location_results and len(location_results) > 1:
                            self.search_components["log_area"].insert(tk.END, f"📊 Each location's data is also exported to separate CSV files.\n")
                        
                        self.search_components["log_area"].see(tk.END)
                    else:
                        messagebox.showerror("Error", "Failed to export data")
                except Exception as e:
                    logger.error(f"Error exporting to CSV: {e}")
                    messagebox.showerror("Error", f"Failed to export: {e}")
    
    def export_category_results(self, export_type):
        """Export category results to Excel or CSV with all required fields"""
        if not hasattr(self, 'data') or not self.data:
            messagebox.showerror("Error", "No data to export")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if export_type == 'excel':
            filename = filedialog.asksaveasfilename(
                defaultextension='.xlsx',
                filetypes=[('Excel files', '*.xlsx')],
                initialfile=f"zepto_category_products_{timestamp}.xlsx"
            )
            if filename:
                try:
                    # Use the category-location specific results
                    if export_to_excel(self.data, filename, self.cat_location_results):
                        messagebox.showinfo("Success", f"Data exported to {filename}")
                        self.category_components["log_area"].insert(tk.END, f"✅ Category data exported to {filename}\n")
                        
                        # If we have multiple categories or locations, mention the sheets
                        categories = list(self.cat_location_results.keys())
                        locations = set()
                        for cat_dict in self.cat_location_results.values():
                            locations.update(cat_dict.keys())
                            
                        if len(categories) > 1 or len(locations) > 1:
                            self.category_components["log_area"].insert(tk.END, f"📊 Data for each category-location combination is in separate sheets\n")
                        
                        self.category_components["log_area"].see(tk.END)
                    else:
                        messagebox.showerror("Error", "Failed to export data")
                except Exception as e:
                    logger.error(f"Error exporting to Excel: {e}")
                    messagebox.showerror("Error", f"Failed to export: {e}")
        
        elif export_type == 'csv':
            filename = filedialog.asksaveasfilename(
                defaultextension='.csv',
                filetypes=[('CSV files', '*.csv')],
                initialfile=f"zepto_category_products_{timestamp}.csv"
            )
            if filename:
                try:
                    if export_to_csv(self.data, filename, self.cat_location_results):
                        messagebox.showinfo("Success", f"Data exported to {filename}")
                        self.category_components["log_area"].insert(tk.END, f"✅ Category data exported to {filename}\n")
                        
                        # If we have multiple categories or locations, mention separate files
                        categories = list(self.cat_location_results.keys())
                        locations = set()
                        for cat_dict in self.cat_location_results.values():
                            locations.update(cat_dict.keys())
                            
                        if len(categories) > 1 or len(locations) > 1:
                            self.category_components["log_area"].insert(tk.END, f"📊 Separate CSV files created for each category-location combination\n")
                        
                        self.category_components["log_area"].see(tk.END)
                    else:
                        messagebox.showerror("Error", "Failed to export data")
                except Exception as e:
                    logger.error(f"Error exporting to CSV: {e}")
                    messagebox.showerror("Error", f"Failed to export: {e}")
    
    def export_comparison(self):
        """Export location comparison for search results"""
        if not hasattr(self, 'location_results') or not self.location_results or len(self.location_results) <= 1:
            messagebox.showinfo("Information", "Need data from at least 2 locations to create a comparison")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = filedialog.asksaveasfilename(
            defaultextension='.xlsx',
            filetypes=[('Excel files', '*.xlsx')],
            initialfile=f"zepto_location_comparison_{timestamp}.xlsx"
        )
        
        if filename:
            try:
                if create_location_comparison(self.location_results, filename):
                    messagebox.showinfo("Success", f"Location comparison exported to {filename}")
                    self.search_components["log_area"].insert(tk.END, f"✅ Location comparison exported to {filename}\n")
                    self.search_components["log_area"].see(tk.END)
                else:
                    messagebox.showerror("Error", "Failed to create location comparison")
            except Exception as e:
                logger.error(f"Error creating location comparison: {e}")
                messagebox.showerror("Error", f"Failed to create comparison: {e}")
    
    def export_category_comparison(self):
        """Export location comparison for category results"""
        if not hasattr(self, 'cat_location_results'):
            messagebox.showinfo("Information", "No category data available for comparison")
            return
        
        # Flatten location results from category structure
        # {category: {location: [products]}} -> {location: [products]}
        flat_results = {}
        for category, location_dict in self.cat_location_results.items():
            for location, products in location_dict.items():
                if location not in flat_results:
                    flat_results[location] = []
                flat_results[location].extend(products)
        
        if len(flat_results) <= 1:
            messagebox.showinfo("Information", "Need data from at least 2 locations to create a comparison")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = filedialog.asksaveasfilename(
            defaultextension='.xlsx',
            filetypes=[('Excel files', '*.xlsx')],
            initialfile=f"zepto_category_comparison_{timestamp}.xlsx"
        )
        
        if filename:
            try:
                if create_location_comparison(flat_results, filename):
                    messagebox.showinfo("Success", f"Location comparison exported to {filename}")
                    self.category_components["log_area"].insert(tk.END, f"✅ Location comparison exported to {filename}\n")
                    self.category_components["log_area"].see(tk.END)
                else:
                    messagebox.showerror("Error", "Failed to create location comparison")
            except Exception as e:
                logger.error(f"Error creating location comparison: {e}")
                messagebox.showerror("Error", f"Failed to create comparison: {e}")
    
    def add_schedule(self):
        """Add a new scheduled task"""
        # Validate inputs
        task_name = self.schedule_components["task_name"].get().strip()
        if not task_name:
            messagebox.showerror("Error", "Please enter a task name")
            return
        
        task_type = self.schedule_components["task_type"].get()
        term = self.schedule_components["term_var"].get().strip()
        if not term:
            messagebox.showerror("Error", f"Please enter a {'search term' if task_type == 'search' else 'category'}")
            return
        
        # Parse locations
        locations = [loc.strip() for loc in self.schedule_components["locations"].get().split(",") if loc.strip()]
        if not locations:
            messagebox.showerror("Error", "Please enter at least one location")
            return
        
        # Parse max products
        try:
            max_products = int(self.schedule_components["max_products"].get()) if self.schedule_components["max_products"].get() else None
        except ValueError:
            messagebox.showerror("Error", "Max products must be a number")
            return
        
        # Get output directory
        output_dir = self.schedule_components["output_dir"].get()
        os.makedirs(output_dir, exist_ok=True)
        
        # Parse frequency and time
        frequency = self.schedule_components["frequency"].get()
        time_str = self.schedule_components["schedule_time"].get().strip()
        
        # Validate time format
        if not re.match(r"^\d{1,2}:\d{2}$", time_str):
            messagebox.showerror("Error", "Time must be in HH:MM format")
            return
        
        # Create task parameters
        task_params = {
            "term": term,
            "locations": locations,
            "max_products": max_products,
            "output_dir": output_dir,
            "headless": self.schedule_components["headless"].get(),
            "pdp_scrape": True if task_type == "category" else False  # Only relevant for category scraping
        }
        
        # Add task to scheduler
        success = self.scheduler.add_task(
            name=task_name,
            task_type=task_type,
            frequency=frequency,
            time_value=time_str,
            task_params=task_params
        )
        
        if success:
            messagebox.showinfo("Task Scheduled", f"Task '{task_name}' has been scheduled successfully.")
            # Clear inputs
            self.schedule_components["task_name"].set("")
            self.schedule_components["term_var"].set("")
            # Update task list
            self.schedule_components["update_tasks_list"]()
        else:
            messagebox.showerror("Error", "Failed to schedule task. Check the logs for details.")
    
    def remove_schedule(self):
        """Remove a scheduled task"""
        # Get selected task
        selected = self.schedule_components["tasks_tree"].selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a task to remove")
            return
        
        # Confirm with user
        if not messagebox.askyesno("Confirm", "Are you sure you want to remove the selected scheduled task?"):
            return
        
        # Get task ID from selected item
        task_id = self.schedule_components["tasks_tree"].item(selected[0], "values")[0]  # Assuming task name is unique and serves as ID
        
        # Remove task from scheduler
        success = self.scheduler.remove_task(task_id)
        
        if success:
            messagebox.showinfo("Task Removed", f"Task '{task_id}' has been removed.")
            # Update task list
            self.schedule_components["update_tasks_list"]()
        else:
            messagebox.showerror("Error", f"Failed to remove task '{task_id}'. Check the logs for details.")
    
    def update_history_list(self):
        """Update the list of history items"""
        # Clear the tree
        for item in self.history_components["history_list"].get_children():
            self.history_components["history_list"].delete(item)
        
        # Get history items
        history_items = self.config_manager.get_history()
        
        # Add items to the tree (newest first)
        for item in reversed(history_items):
            date = item['date'].replace('T', ' ').split('.')[0]  # Format ISO date
            
            # Determine term/category text
            if item['type'] == 'search':
                term = item.get('term', '')
            else:  # category
                categories = item.get('categories', [])
                if len(categories) == 1:
                    term = categories[0]
                else:
                    term = f"{len(categories)} categories"
            
            self.history_components["history_list"].insert("", "end", values=(
                date,
                item['type'],
                term,
                item.get('product_count', 0),
                item['status']
            ))
    
    def view_history_item(self):
        """View details of a history item"""
        # Get selected item
        selected = self.history_components["history_list"].selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a history item to view")
            return
        
        # Get history index from selected item
        item_idx = int(self.history_components["history_list"].index(selected[0]))
        
        # Get history items
        history_items = self.config_manager.get_history()
        reversed_items = list(reversed(history_items))
        
        if item_idx < len(reversed_items):
            item = reversed_items[item_idx]
            
            # Create a details window
            details_window = tk.Toplevel(self.root)
            details_window.title(f"History Item - {item['date']}")
            details_window.geometry("600x400")
            details_window.minsize(500, 300)
            
            # Make details window modal
            details_window.transient(self.root)
            details_window.grab_set()
            
            # Create a text widget for details
            details_text = tk.Text(details_window, wrap=tk.WORD, font="TkFixedFont")
            details_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(details_text, command=details_text.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            details_text.config(yscrollcommand=scrollbar.set)
            
            # Insert item details
            details_text.insert(tk.END, f"Date: {item['date']}\n")
            details_text.insert(tk.END, f"Type: {item['type']}\n")
            
            if item['type'] == "search":
                details_text.insert(tk.END, f"Search Term: {item['term']}\n")
            else:  # category
                if len(item['categories']) == 1:
                    details_text.insert(tk.END, f"Category: {item['categories'][0]}\n")
                else:
                    details_text.insert(tk.END, f"Categories: {', '.join(item['categories'])}\n")
            
            if 'locations' in item:
                details_text.insert(tk.END, f"Locations: {', '.join(item['locations'])}\n")
            
            details_text.insert(tk.END, f"Products Found: {item.get('product_count', 0)}\n")
            details_text.insert(tk.END, f"Status: {item['status']}\n")
            
            if 'output_file' in item:
                details_text.insert(tk.END, f"Output File: {item['output_file']}\n")
            
            if 'error' in item:
                details_text.insert(tk.END, f"\nError: {item['error']}\n")
            
            # Add a "Close" button
            ttk.Button(details_window, text="Close", command=details_window.destroy).pack(pady=10)
            
            # Add a "Open File" button if there's an output file
            if 'output_file' in item and os.path.exists(item['output_file']):
                ttk.Button(details_window, text="Open File", 
                           command=lambda f=item['output_file']: os.startfile(f)).pack(pady=5)
            
            # Make details non-editable
            details_text.config(state=tk.DISABLED)
            
            # Wait for the window to be closed
            self.root.wait_window(details_window)
    
    def delete_history_item(self):
        """Delete a history item"""
        # Get selected item
        selected = self.history_components["history_list"].selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a history item to delete")
            return
        
        # Confirm with user
        if not messagebox.askyesno("Confirm", "Are you sure you want to delete this history item?"):
            return
        
        # Get history index from selected item
        item_idx = int(self.history_components["history_list"].index(selected[0]))
        
        # Get history items for the actual index
        history_items = self.config_manager.get_history()
        actual_idx = len(history_items) - 1 - item_idx
        
        # Delete history item
        success = self.config_manager.delete_history_item(actual_idx)
        
        if success:
            # Update history list
            self.update_history_list()
            messagebox.showinfo("Deleted", "History item deleted successfully")
        else:
            messagebox.showerror("Error", "Failed to delete history item")
    
    def rerun_history_item(self):
        """Rerun a task from history"""
        # Get selected item
        selected = self.history_components["history_list"].selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a history item to rerun")
            return
        
        # Get history index from selected item
        item_idx = int(self.history_components["history_list"].index(selected[0]))
        
        # Get history items
        history_items = self.config_manager.get_history()
        reversed_items = list(reversed(history_items))
        
        if item_idx < len(reversed_items):
            item = reversed_items[item_idx]
            
            # Switch to appropriate tab
            if item['type'] == "search":
                self.tabs["notebook"].select(0)  # Search tab
                
                # Set search parameters
                self.search_components["search_term"].set(item.get('term', ''))
                if 'locations' in item:
                    self.search_components["locations"].set(','.join(item['locations']))
                
                if 'max_products' in item:
                    self.search_components["max_products"].set(str(item['max_products']))
                
                # Focus on search button
                self.search_components["search_button"].focus_set()
                
                # Inform user
                messagebox.showinfo("Task Loaded", "Search parameters have been loaded. Click 'Start Scraping' to run.")
            else:  # category
                self.tabs["notebook"].select(1)  # Category tab
                
                # Reset category selections
                for category, var in self.category_components["category_vars"].items():
                    var.set(False)
                
                # Set category parameters
                if 'categories' in item:
                    # Set selected categories
                    for category in item['categories']:
                        if category in self.category_components["category_vars"]:
                            self.category_components["category_vars"][category].set(True)
                
                if 'locations' in item:
                    self.category_components["locations"].set(','.join(item['locations']))
                
                if 'max_products' in item:
                    self.category_components["max_products"].set(str(item['max_products']))
                
                # Focus on category button
                self.category_components["category_button"].focus_set()
                
                # Inform user
                messagebox.showinfo("Task Loaded", "Category parameters have been loaded. Click 'Start Category Scrape' to run.")
    
    def on_closing(self):
        """Handle application closing"""
        # Check if scraping is active
        if self.scraping_active:
            if not messagebox.askyesno("Confirm Exit", "Scraping is in progress. Are you sure you want to exit?"):
                return
        
        # Stop scheduler
        self.scheduler.stop_service()
        
        # Close application
        self.root.destroy()

# ---------------------------
# Main entry point
# ---------------------------
def main():
    root = tk.Tk()
    app = EnhancedZeptoScraperApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()