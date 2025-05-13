"""
UI Components Module
-------------------
Contains all UI-related components and functions for the Zepto scraper application.
Provides a clean, modern interface using ttk with enhanced styling.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, font
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Union

# Set up logging
logger = logging.getLogger("ZeptoScraper.UI")

# ---------------------------
# Theme & Style Configuration
# ---------------------------
def setup_theme(root, theme_name="arc"):
    """
    Setup theme and global styles for the application
    
    Args:
        root: The root window
        theme_name: The theme to use ("arc", "equilux", "heritage", etc.)
    """
    style = ttk.Style(root)
    
    # Define the Heritage theme colors
    HERITAGE_GREEN = "#008736"      # Heritage green from logo
    HERITAGE_RED = "#E31E24"        # Heritage red from logo
    HERITAGE_DARK_GREEN = "#006628" # Darker shade for hover effects
    HERITAGE_BG = "#ffffff"         # White background for better contrast
    HERITAGE_TEXT = "#000000"       # Black text for maximum readability
    HERITAGE_ACCENT = "#FFD700"     # Gold accent color
    HERITAGE_LIGHT_GRAY = "#f0f0f0" # Light gray for alternate rows
    
    # Try to use ttkthemes if available
    try:
        from ttkthemes import ThemedTk, ThemedStyle
        if not isinstance(root, ThemedTk):
            style = ThemedStyle(root)
        
        # If heritage theme is selected, create custom theme
        if theme_name == "heritage":
            # Use a clean base theme as starting point for Heritage theme
            style.set_theme("arc")
            
            # Configure all elements for the Heritage theme
            style.configure(".", font=('Helvetica', 10))
            style.configure("TFrame", background=HERITAGE_BG)
            style.configure("TLabelframe", background=HERITAGE_BG)
            style.configure("TLabelframe.Label", foreground=HERITAGE_GREEN, background=HERITAGE_BG, font=('Helvetica', 12, 'bold'))
            style.configure("TLabel", foreground=HERITAGE_TEXT, background=HERITAGE_BG, font=('Helvetica', 11))
            # Ensure button text is always visible with good contrast
            style.configure("TButton", foreground=HERITAGE_TEXT, background="#e0e0e0", padding=5, font=('Helvetica', 10, 'bold'))
            style.map("TButton", 
                foreground=[('active', '#000000'), ('disabled', '#707070')],
                background=[('active', '#d0d0d0'), ('pressed', HERITAGE_GREEN), ('disabled', '#f0f0f0')])
            
            # Primary button style (green)
            style.configure("Primary.TButton", foreground="white", background=HERITAGE_GREEN, font=('Helvetica', 11, 'bold'))
            style.map("Primary.TButton", 
                foreground=[('active', 'white'), ('disabled', '#e0e0e0')],
                background=[('active', '#00a040'), ('pressed', '#006020'), ('disabled', '#80c090')])
                
            # Entry fields with better contrast
            style.configure("TEntry", foreground=HERITAGE_TEXT, background="white", fieldbackground="white", insertcolor=HERITAGE_TEXT)
            style.map("TEntry", 
                fieldbackground=[('focus', '#f0f8ff')])
            
            # Danger button style (red)
            style.configure("Danger.TButton", foreground="white", background=HERITAGE_RED)
            style.map("Danger.TButton", 
                foreground=[('active', 'white'), ('disabled', '#e0e0e0')],
                background=[('active', '#ff3030'), ('pressed', '#b01010'), ('disabled', '#f08080')]
            )
            
            # Notebook (tabs) styling
            style.configure("TNotebook", background=HERITAGE_BG)
            style.configure("TNotebook.Tab", background="#e0e0e0", padding=[12, 6], font=('Helvetica', 10, 'bold'))
            style.map("TNotebook.Tab",
                background=[('selected', HERITAGE_GREEN), ('active', '#d0d0d0')],
                foreground=[('selected', 'white'), ('!selected', '#000000')]
            )
            
            # Entry field styling
            style.configure("TEntry", fieldbackground="white", foreground=HERITAGE_TEXT)
            
            # Listbox styling
            root.option_add("*TCombobox*Listbox.background", "white")
            root.option_add("*TCombobox*Listbox.foreground", HERITAGE_TEXT)
            
            # Combobox styling
            style.configure("TCombobox", 
                fieldbackground="white", 
                background=HERITAGE_BG, 
                foreground=HERITAGE_TEXT,
                arrowcolor=HERITAGE_GREEN
            )
            
            # Checkbutton styling
            style.configure("TCheckbutton", background=HERITAGE_BG, foreground=HERITAGE_TEXT)
            style.map("TCheckbutton", 
                indicatorcolor=[('selected', HERITAGE_GREEN), ('active', HERITAGE_GREEN)]
            )
            
            # Progress bar styling
            style.configure("Horizontal.TProgressbar", 
                troughcolor=HERITAGE_BG, 
                background=HERITAGE_GREEN
            )
            
            # Headers and special elements
            style.configure("Header.TLabel", 
                foreground=HERITAGE_GREEN, 
                background=HERITAGE_BG, 
                font=('Helvetica', 14, 'bold')
            )
            
            # Make all other widgets match the theme
            for widget in ["TRadiobutton", "TMenubutton", "TPanedwindow", "TScale"]:
                style.configure(widget, background=HERITAGE_BG, foreground=HERITAGE_TEXT)
            
            logger.info(f"Applied custom Heritage theme")
        else:
            # Apply the selected theme if not heritage
            style.set_theme(theme_name)
            logger.info(f"Applied {theme_name} theme")
            
            # Add green highlights to selected tabs even in other themes
            style.map("TNotebook.Tab",
                background=[("selected", HERITAGE_GREEN)],
                foreground=[("selected", "white")])
    except ImportError:
        # If ttkthemes is not available, use built-in themes
        logger.warning("ttkthemes not available, using built-in themes")
        
        if theme_name == "heritage":
            # Create a custom heritage-like theme using ttk built-in themes
            style.theme_use("clam")
            
            # Apply similar styling as above but with ttk built-in capabilities
            style.configure("TButton", foreground=HERITAGE_TEXT, background=HERITAGE_BG, padding=5)
            style.configure("TFrame", background=HERITAGE_BG)
            style.configure("TLabel", foreground=HERITAGE_TEXT, background=HERITAGE_BG)
            style.configure("TLabelframe", background=HERITAGE_BG)
            style.configure("TLabelframe.Label", foreground=HERITAGE_GREEN, background=HERITAGE_BG)
            
            # Add primary button style
            style.configure("Primary.TButton", foreground="white", background=HERITAGE_GREEN)
            
            # Add danger button style
            style.configure("Danger.TButton", foreground="white", background=HERITAGE_RED)
            
            logger.info("Applied custom Heritage theme using ttk built-in theme")
        else:
            # Use a built-in theme
            try:
                style.theme_use(theme_name)
                logger.info(f"Applied built-in theme: {theme_name}")
            except tk.TclError:
                # If theme doesn't exist, use default
                logger.warning(f"Theme {theme_name} not found, using default theme")
                style.theme_use("clam")
    
    # Common style configurations
    style.configure("Header.TLabel", font=('Helvetica', 12, 'bold'))
    style.configure("Title.TLabel", font=('Helvetica', 14, 'bold'))
    style.configure("Info.TLabel", foreground="#2196F3")
    style.configure("Success.TLabel", foreground=HERITAGE_GREEN if theme_name == "heritage" else "#4CAF50")
    style.configure("Warning.TLabel", foreground="#FF9800")
    style.configure("Error.TLabel", foreground=HERITAGE_RED if theme_name == "heritage" else "#F44336")
    
    # Customize notebook appearance
    style.configure("TNotebook", padding=2)
    
    # Make log areas use monospace font
    custom_fixed_font = font.Font(family="Courier", size=10)
    
    # Configure treeview for better visibility
    style.configure("Treeview.Heading", font=('Helvetica', 10, 'bold'))
    style.configure("Treeview", font=('Helvetica', 10), rowheight=22)
    
    logger.debug(f"Applied theme: {theme_name} with custom styles")

# ---------------------------
# Main UI Construction
# ---------------------------
def create_main_frame(root):
    """Create the main application frame"""
    main_frame = ttk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    return main_frame

def create_tabs(parent_frame):
    """Create and return the tab control and tab frames"""
    # Create notebook (tab control)
    notebook = ttk.Notebook(parent_frame)
    notebook.pack(fill=tk.BOTH, expand=True)
    
    # Create individual tab frames
    search_tab = ttk.Frame(notebook)
    category_tab = ttk.Frame(notebook)
    schedule_tab = ttk.Frame(notebook)
    history_tab = ttk.Frame(notebook)
    settings_tab = ttk.Frame(notebook)
    
    # Add tabs to notebook
    notebook.add(search_tab, text="Search Scraper")
    notebook.add(category_tab, text="Category Scraper")
    notebook.add(schedule_tab, text="Schedule Tasks")
    notebook.add(history_tab, text="History")
    notebook.add(settings_tab, text="Settings")
    
    # Return the tab frames
    return {
        "notebook": notebook,
        "search_tab": search_tab,
        "category_tab": category_tab,
        "schedule_tab": schedule_tab,
        "history_tab": history_tab,
        "settings_tab": settings_tab
    }

# ---------------------------
# Tab-specific UI Components
# ---------------------------
def create_search_tab(parent, start_func, stop_func):
    """Create the search-based scraping tab"""
    # Create frames
    top_frame = ttk.Frame(parent)
    top_frame.pack(fill=tk.X, padx=5, pady=5)
    
    search_frame = ttk.LabelFrame(top_frame, text="Search Configuration")
    search_frame.pack(fill=tk.X, padx=5, pady=5)
    
    # Search term input
    ttk.Label(search_frame, text="Search Term:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
    search_term = tk.StringVar()
    term_entry = ttk.Entry(search_frame, textvariable=search_term, width=40)
    term_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
    
    # Location input
    ttk.Label(search_frame, text="Locations (comma-separated):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
    locations = tk.StringVar(value="Bangalore")
    ttk.Entry(search_frame, textvariable=locations, width=40).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
    
    # Max products
    ttk.Label(search_frame, text="Max Products:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
    max_products = tk.StringVar(value="100")
    ttk.Entry(search_frame, textvariable=max_products, width=10).grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
    
    # Output directory
    ttk.Label(search_frame, text="Output Directory:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
    output_dir = tk.StringVar(value="./results")
    dir_frame = ttk.Frame(search_frame)
    dir_frame.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)
    ttk.Entry(dir_frame, textvariable=output_dir, width=30).pack(side=tk.LEFT)
    ttk.Button(dir_frame, text="Browse", command=lambda: select_directory(output_dir)).pack(side=tk.LEFT, padx=5)
    
    # Headless mode
    headless_mode = tk.BooleanVar(value=False)
    ttk.Checkbutton(search_frame, text="Run in Headless Mode", variable=headless_mode).grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)
    
    # Buttons
    btn_frame = ttk.Frame(top_frame)
    btn_frame.pack(fill=tk.X, padx=5, pady=10)
    
    search_button = ttk.Button(btn_frame, text="Start Scraping", command=start_func, style="Primary.TButton")
    search_button.pack(side=tk.LEFT, padx=5)
    
    stop_button = ttk.Button(btn_frame, text="Stop Scraping", command=stop_func, state=tk.DISABLED)
    stop_button.pack(side=tk.LEFT, padx=5)
    
    # Progress bar
    progress_frame = ttk.Frame(top_frame)
    progress_frame.pack(fill=tk.X, padx=5, pady=5)
    
    ttk.Label(progress_frame, text="Progress:").pack(side=tk.LEFT, padx=5)
    progress_bar = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
    progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
    
    # Results area
    results_frame = ttk.LabelFrame(parent, text="Results")
    results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # Log area with enhanced styling and better readability
    log_area = tk.Text(results_frame, wrap=tk.WORD, font="TkFixedFont", 
                      background="#f8f8f8", padx=5, pady=5,
                      spacing1=2, spacing2=2, spacing3=3)
    log_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    log_scrollbar = ttk.Scrollbar(results_frame, command=log_area.yview)
    log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    log_area.config(yscrollcommand=log_scrollbar.set)
    
    # Export buttons frame
    export_frame = ttk.Frame(parent)
    export_frame.pack(fill=tk.X, padx=5, pady=5)
    
    export_excel_btn = ttk.Button(export_frame, text="Export to Excel", state=tk.DISABLED)
    export_excel_btn.pack(side=tk.LEFT, padx=5)
    
    export_csv_btn = ttk.Button(export_frame, text="Export to CSV", state=tk.DISABLED)
    export_csv_btn.pack(side=tk.LEFT, padx=5)
    
    export_comparison_btn = ttk.Button(export_frame, text="Export Location Comparison", state=tk.DISABLED)
    export_comparison_btn.pack(side=tk.LEFT, padx=5)
    
    # Return components
    return {
        "search_term": search_term,
        "locations": locations,
        "max_products": max_products,
        "output_dir": output_dir,
        "headless_mode": headless_mode,
        "search_button": search_button,
        "stop_button": stop_button,
        "progress_bar": progress_bar,
        "log_area": log_area,
        "export_excel_btn": export_excel_btn,
        "export_csv_btn": export_csv_btn,
        "export_comparison_btn": export_comparison_btn
    }

def create_category_tab(parent, start_func, stop_func):
    """Create the category-based scraping tab"""
    try:
        # Import category URLs from V6
        from attached_assets.V6 import CATEGORY_URLS
        
        # Create frames
        top_frame = ttk.Frame(parent)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        category_frame = ttk.LabelFrame(top_frame, text="Category Configuration")
        category_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Category selection
        ttk.Label(category_frame, text="Category:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        category_var = tk.StringVar()
        
        # Category list with select all option
        category_list_frame = ttk.Frame(category_frame)
        category_list_frame.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # List all categories with checkboxes
        categories = sorted(list(CATEGORY_URLS.keys()))
        category_vars = {}
        
        # Add "Select All" checkbox
        all_categories_var = tk.BooleanVar(value=False)
        
        # Define toggle function for "Select All" checkbox
        def toggle_all_categories():
            """Toggle all category checkboxes based on the "Select All" checkbox state"""
            checked = all_categories_var.get()
            for var in category_vars.values():
                var.set(checked)
        
        all_cb = ttk.Checkbutton(category_list_frame, text="Select All Categories", 
                                 variable=all_categories_var, command=toggle_all_categories)
        all_cb.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)
        
        # Add individual category checkboxes
        for i, category in enumerate(categories):
            var = tk.BooleanVar(value=False)
            category_vars[category] = var
            cb = ttk.Checkbutton(category_list_frame, text=category, variable=var)
            cb.grid(row=i//2 + 1, column=i%2, padx=5, pady=2, sticky=tk.W)
        
        # Location input
        ttk.Label(category_frame, text="Locations (comma-separated):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        locations = tk.StringVar(value="Bangalore")
        ttk.Entry(category_frame, textvariable=locations, width=40).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Max products
        ttk.Label(category_frame, text="Max Products per Category:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        max_products = tk.StringVar(value="50")
        ttk.Entry(category_frame, textvariable=max_products, width=10).grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Output directory
        ttk.Label(category_frame, text="Output Directory:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        output_dir = tk.StringVar(value="./results")
        dir_frame = ttk.Frame(category_frame)
        dir_frame.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(dir_frame, textvariable=output_dir, width=30).pack(side=tk.LEFT)
        ttk.Button(dir_frame, text="Browse", command=lambda: select_directory(output_dir)).pack(side=tk.LEFT, padx=5)
        
        # Headless mode
        headless_mode = tk.BooleanVar(value=False)
        ttk.Checkbutton(category_frame, text="Run in Headless Mode", variable=headless_mode).grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)
        
        # Buttons
        btn_frame = ttk.Frame(top_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=10)
        
        start_button = ttk.Button(btn_frame, text="Start Category Scraping", command=start_func, style="Primary.TButton")
        start_button.pack(side=tk.LEFT, padx=5)
        
        stop_button = ttk.Button(btn_frame, text="Stop Scraping", command=stop_func, state=tk.DISABLED)
        stop_button.pack(side=tk.LEFT, padx=5)
        
        # Progress bar
        progress_frame = ttk.Frame(top_frame)
        progress_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(progress_frame, text="Progress:").pack(side=tk.LEFT, padx=5)
        progress_bar = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Results area
        results_frame = ttk.LabelFrame(parent, text="Results")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Log area
        log_area = tk.Text(results_frame, wrap=tk.WORD, font="TkFixedFont")
        log_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        log_scrollbar = ttk.Scrollbar(results_frame, command=log_area.yview)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        log_area.config(yscrollcommand=log_scrollbar.set)
        
        # Export buttons frame
        export_frame = ttk.Frame(parent)
        export_frame.pack(fill=tk.X, padx=5, pady=5)
        
        export_excel_btn = ttk.Button(export_frame, text="Export to Excel", state=tk.DISABLED)
        export_excel_btn.pack(side=tk.LEFT, padx=5)
        
        export_csv_btn = ttk.Button(export_frame, text="Export to CSV", state=tk.DISABLED)
        export_csv_btn.pack(side=tk.LEFT, padx=5)
        
        export_comparison_btn = ttk.Button(export_frame, text="Export Location Comparison", state=tk.DISABLED)
        export_comparison_btn.pack(side=tk.LEFT, padx=5)
        
        # Return components
        return {
            "category_vars": category_vars,
            "all_categories_var": all_categories_var,
            "locations": locations,
            "max_products": max_products,
            "output_dir": output_dir,
            "headless_mode": headless_mode,
            "start_button": start_button,
            "stop_button": stop_button,
            "progress_bar": progress_bar,
            "log_area": log_area,
            "export_excel_btn": export_excel_btn,
            "export_csv_btn": export_csv_btn,
            "export_comparison_btn": export_comparison_btn
        }
    except ImportError:
        # If V6.py not found
        error_label = ttk.Label(parent, text="Error: V6.py module not found. Category scraping not available.", style="Error.TLabel")
        error_label.pack(padx=20, pady=20)
        return {"error": True}

def create_schedule_tab(parent, add_func, remove_func, get_tasks_func):
    """Create the scheduling tab with Heritage Foods branding"""
    # Heritage colors
    HERITAGE_GREEN = "#008736"
    HERITAGE_RED = "#E31E24"
    
    # Title header
    header_frame = ttk.Frame(parent)
    header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
    
    header_icon = "🕒"
    header_label = ttk.Label(header_frame, text=f"{header_icon} Automated Data Collection", 
                          font=("Helvetica", 14, "bold"), foreground=HERITAGE_GREEN)
    header_label.pack(side=tk.LEFT, padx=5)
    
    desc_label = ttk.Label(header_frame, text="Schedule tasks to run automatically at specified times", 
                        font=("Helvetica", 10))
    desc_label.pack(side=tk.LEFT, padx=15)
    
    # Create frames
    top_frame = ttk.Frame(parent)
    top_frame.pack(fill=tk.X, padx=10, pady=10)
    
    # Schedule configuration
    schedule_frame = ttk.LabelFrame(top_frame, text="Schedule Configuration")
    schedule_frame.pack(fill=tk.X, padx=5, pady=5)
    
    # Task name
    ttk.Label(schedule_frame, text="Task Name:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
    task_name = tk.StringVar()
    ttk.Entry(schedule_frame, textvariable=task_name, width=30).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
    
    # Task type (search or category)
    ttk.Label(schedule_frame, text="Task Type:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
    task_type = tk.StringVar(value="search")
    
    type_frame = ttk.Frame(schedule_frame)
    type_frame.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
    
    ttk.Radiobutton(type_frame, text="Search Term", variable=task_type, value="search").pack(side=tk.LEFT, padx=5)
    ttk.Radiobutton(type_frame, text="Category", variable=task_type, value="category").pack(side=tk.LEFT, padx=5)
    
    # Search term / Category (depending on type)
    search_term_frame = ttk.Frame(schedule_frame)
    search_term_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)
    
    ttk.Label(search_term_frame, text="Search Term:").pack(side=tk.LEFT, padx=5)
    search_term = tk.StringVar()
    ttk.Entry(search_term_frame, textvariable=search_term, width=30).pack(side=tk.LEFT, padx=5)
    
    # Categories frame will be shown when type=category
    category_frame = ttk.Frame(schedule_frame)
    
    try:
        # Import category URLs from V6
        from attached_assets.V6 import CATEGORY_URLS
        categories = sorted(list(CATEGORY_URLS.keys()))
        
        ttk.Label(category_frame, text="Categories:").pack(side=tk.LEFT, padx=5)
        categories_var = tk.StringVar()
        ttk.Combobox(category_frame, textvariable=categories_var, values=categories, width=25).pack(side=tk.LEFT, padx=5)
    except ImportError:
        ttk.Label(category_frame, text="Error: V6.py not found. Categories not available.").pack(padx=5, pady=5)
    
    # Toggle between search term and category frames based on task type
    def toggle_task_type(*args):
        if task_type.get() == "search":
            category_frame.grid_forget()
            search_term_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)
        else:  # category
            search_term_frame.grid_forget()
            category_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)
    
    task_type.trace("w", toggle_task_type)
    
    # Schedule frequency
    ttk.Label(schedule_frame, text="Frequency:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
    frequency = tk.StringVar(value="once")
    
    freq_frame = ttk.Frame(schedule_frame)
    freq_frame.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)
    
    ttk.Radiobutton(freq_frame, text="Once", variable=frequency, value="once").pack(side=tk.LEFT, padx=5)
    ttk.Radiobutton(freq_frame, text="Daily", variable=frequency, value="daily").pack(side=tk.LEFT, padx=5)
    ttk.Radiobutton(freq_frame, text="Weekly", variable=frequency, value="weekly").pack(side=tk.LEFT, padx=5)
    ttk.Radiobutton(freq_frame, text="Monthly", variable=frequency, value="monthly").pack(side=tk.LEFT, padx=5)
    
    # Time
    ttk.Label(schedule_frame, text="Time (HH:MM):").grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
    time_value = tk.StringVar(value="12:00")
    ttk.Entry(schedule_frame, textvariable=time_value, width=10).grid(row=4, column=1, padx=5, pady=5, sticky=tk.W)
    
    # Locations
    ttk.Label(schedule_frame, text="Locations:").grid(row=5, column=0, padx=5, pady=5, sticky=tk.W)
    locations = tk.StringVar(value="Bangalore")
    ttk.Entry(schedule_frame, textvariable=locations, width=30).grid(row=5, column=1, padx=5, pady=5, sticky=tk.W)
    
    # Output directory
    ttk.Label(schedule_frame, text="Output Directory:").grid(row=6, column=0, padx=5, pady=5, sticky=tk.W)
    output_dir = tk.StringVar(value="./results")
    
    dir_frame = ttk.Frame(schedule_frame)
    dir_frame.grid(row=6, column=1, padx=5, pady=5, sticky=tk.W)
    
    ttk.Entry(dir_frame, textvariable=output_dir, width=20).pack(side=tk.LEFT, padx=5)
    ttk.Button(dir_frame, text="Browse", command=lambda: select_directory(output_dir)).pack(side=tk.LEFT, padx=5)
    
    # Buttons
    btn_frame = ttk.Frame(top_frame)
    btn_frame.pack(fill=tk.X, padx=5, pady=10)
    
    add_btn = ttk.Button(btn_frame, text="Add Schedule", command=add_func, style="Primary.TButton")
    add_btn.pack(side=tk.LEFT, padx=5)
    
    remove_btn = ttk.Button(btn_frame, text="Remove Schedule", command=remove_func)
    remove_btn.pack(side=tk.LEFT, padx=5)
    
    # Separator for visual clarity
    ttk.Separator(parent, orient="horizontal").pack(fill=tk.X, padx=10, pady=5)
    
    # Scheduled tasks section header
    tasks_header_frame = ttk.Frame(parent)
    tasks_header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
    
    tasks_icon = "📋"
    tasks_header = ttk.Label(tasks_header_frame, text=f"{tasks_icon} Scheduled Tasks", 
                           font=("Helvetica", 12, "bold"), foreground=HERITAGE_GREEN)
    tasks_header.pack(side=tk.LEFT, padx=5)
    
    # Scheduled tasks list with improved styling
    scheduled_frame = ttk.LabelFrame(parent, text="Active Scheduled Tasks")
    scheduled_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    # Create a styled frame for the treeview
    tree_frame = ttk.Frame(scheduled_frame)
    tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # Create a treeview with Heritage colors
    style = ttk.Style()
    style.map('Treeview', background=[('selected', HERITAGE_GREEN)])
    
    tasks_list = ttk.Treeview(tree_frame, columns=("id", "name", "type", "frequency", "time", "location"), 
                             show="headings", height=10)
    
    tasks_list.heading("id", text="ID")
    tasks_list.heading("name", text="Task Name")
    tasks_list.heading("type", text="Type")
    tasks_list.heading("frequency", text="Frequency")
    tasks_list.heading("time", text="Time")
    tasks_list.heading("location", text="Locations")
    
    tasks_list.column("id", width=40, anchor=tk.CENTER)
    tasks_list.column("name", width=150)
    tasks_list.column("type", width=80, anchor=tk.CENTER)
    tasks_list.column("frequency", width=80, anchor=tk.CENTER)
    tasks_list.column("time", width=80, anchor=tk.CENTER)
    tasks_list.column("location", width=150)
    
    tasks_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    tasks_scrollbar = ttk.Scrollbar(tree_frame, command=tasks_list.yview)
    tasks_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    tasks_list.config(yscrollcommand=tasks_scrollbar.set)
    
    # Instructions
    instruction_frame = ttk.Frame(scheduled_frame)
    instruction_frame.pack(fill=tk.X, padx=5, pady=5)
    
    info_icon = "ℹ️"
    ttk.Label(instruction_frame, 
              text=f"{info_icon} Tasks will run automatically in the background at scheduled times",
              font=("Helvetica", 9, "italic")).pack(anchor=tk.W, pady=2)
    
    # Update tasks list
    def update_tasks_list():
        # Clear existing items
        for item in tasks_list.get_children():
            tasks_list.delete(item)
        
        # Add tasks
        tasks = get_tasks_func()
        
        # Style for alternate rows
        tasks_list.tag_configure('odd_row', background='#f5f5f5')
        tasks_list.tag_configure('even_row', background='#ffffff')
        
        if not tasks:
            # Show a placeholder message when no tasks exist
            tasks_list.insert("", "end", values=("--", "No scheduled tasks", "--", "--", "--", "--"), tags=('odd_row',))
        else:
            for idx, task in enumerate(tasks):
                task_id = task.get("id", "")
                name = task.get("name", "")
                task_type = task.get("task_type", "")
                freq = task.get("frequency", "")
                time = task.get("time", "")
                
                # Get locations from task params
                locations = "All"
                if task.get("task_params", {}).get("locations"):
                    locations = ", ".join(task.get("task_params", {}).get("locations", []))[:30]
                    if len(locations) > 30:
                        locations = locations[:27] + "..."
                
                # Use alternating row colors
                row_tag = 'odd_row' if idx % 2 else 'even_row'
                
                tasks_list.insert("", "end", values=(task_id, name, task_type, freq, time, locations), tags=(row_tag,))
    
    # Initial update
    update_tasks_list()
    
    # Return components
    return {
        "task_name": task_name,
        "task_type": task_type,
        "search_term": search_term,
        "categories_var": categories_var if 'categories_var' in locals() else None,
        "frequency": frequency,
        "time_value": time_value,
        "locations": locations,
        "output_dir": output_dir,
        "add_btn": add_btn,
        "remove_btn": remove_btn,
        "tasks_list": tasks_list,
        "update_tasks_list": update_tasks_list
    }

def create_history_tab(parent, view_func, delete_func, rerun_func):
    """Create the history tab"""
    # History list
    history_frame = ttk.LabelFrame(parent, text="Scraping History")
    history_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    history_list = ttk.Treeview(history_frame, columns=("id", "date", "type", "term", "results"), 
                              show="headings", height=10)
    
    history_list.heading("id", text="ID")
    history_list.heading("date", text="Date")
    history_list.heading("type", text="Type")
    history_list.heading("term", text="Search Term/Category")
    history_list.heading("results", text="Results")
    
    history_list.column("id", width=50)
    history_list.column("date", width=150)
    history_list.column("type", width=100)
    history_list.column("term", width=150)
    history_list.column("results", width=100)
    
    history_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    history_scrollbar = ttk.Scrollbar(history_frame, command=history_list.yview)
    history_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    history_list.config(yscrollcommand=history_scrollbar.set)
    
    # Buttons
    btn_frame = ttk.Frame(parent)
    btn_frame.pack(fill=tk.X, padx=5, pady=5)
    
    view_btn = ttk.Button(btn_frame, text="View Details", command=view_func)
    view_btn.pack(side=tk.LEFT, padx=5)
    
    rerun_btn = ttk.Button(btn_frame, text="Rerun Task", command=rerun_func, style="Primary.TButton")
    rerun_btn.pack(side=tk.LEFT, padx=5)
    
    delete_btn = ttk.Button(btn_frame, text="Delete", command=delete_func, style="Danger.TButton")
    delete_btn.pack(side=tk.LEFT, padx=5)
    
    # Return components
    return {
        "history_list": history_list,
        "view_btn": view_btn,
        "rerun_btn": rerun_btn,
        "delete_btn": delete_btn
    }

def create_settings_tab(parent, save_settings_func, apply_theme_func=None):
    """Create the settings tab"""
    # Create frames
    settings_frame = ttk.LabelFrame(parent, text="Application Settings")
    settings_frame.pack(fill=tk.X, padx=5, pady=5)
    
    # Theme settings
    theme_frame = ttk.LabelFrame(settings_frame, text="Appearance")
    theme_frame.pack(fill=tk.X, padx=5, pady=5)
    
    # Add Heritage branding
    title_frame = ttk.Frame(theme_frame)
    title_frame.grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W)
    
    try:
        logo_img = tk.PhotoImage(file="icons/heritage_logo.png")
        # Resize if needed
        logo_img = logo_img.subsample(3, 3)  # Reduce size more for settings panel
        logo_label = ttk.Label(title_frame, image=logo_img)
        logo_label.image = logo_img  # Keep reference to prevent garbage collection
        logo_label.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Add title and version
        text_frame = ttk.Frame(title_frame)
        text_frame.pack(side=tk.LEFT, padx=10)
        
        app_label = ttk.Label(text_frame, text="Heritage Foods Zepto Scraper", 
                            font=("Helvetica", 12, "bold"), foreground="#008736")
        app_label.pack(anchor="w")
        
        version_label = ttk.Label(text_frame, text="Version 3.0.0", font=("Helvetica", 9))
        version_label.pack(anchor="w")
        
        desc_label = ttk.Label(text_frame, text="Price tracking across multiple locations",
                             font=("Helvetica", 9, "italic"))
        desc_label.pack(anchor="w")
    except tk.TclError:
        # Logo file not found or error loading
        ttk.Label(theme_frame, text="Heritage Foods Zepto Scraper", 
               font=("Helvetica", 12, "bold"), foreground="#008736").grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W)
    
    # Add separator
    ttk.Separator(theme_frame, orient="horizontal").grid(row=1, column=0, columnspan=3, sticky="ew", padx=5, pady=10)
    
    ttk.Label(theme_frame, text="UI Theme:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
    
    # Get available themes
    theme_var = tk.StringVar(value="heritage")
    
    # Try to get available ttkthemes
    try:
        from ttkthemes import ThemedStyle
        style = ThemedStyle(parent)
        themes = list(style.get_themes())
        themes.append("heritage")  # Add our custom theme
    except ImportError:
        # Fallback to default ttk themes
        themes = ["clam", "alt", "default", "classic", "heritage"]
    
    theme_combo = ttk.Combobox(theme_frame, textvariable=theme_var, values=themes, width=20)
    theme_combo.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
    
    # Theme apply button
    if apply_theme_func:
        apply_theme_btn = ttk.Button(theme_frame, text="Apply Theme", 
                                    command=lambda: apply_theme_func(theme_var.get()),
                                    style="Primary.TButton")
        apply_theme_btn.grid(row=2, column=2, padx=5, pady=5, sticky=tk.W)
        
        # Add theme preview
        ttk.Label(theme_frame, text="Heritage theme features branded colors and improved contrast").grid(
            row=3, column=0, columnspan=3, padx=5, pady=(0, 5), sticky=tk.W)
    
    # Rate limiter settings
    rate_frame = ttk.LabelFrame(settings_frame, text="Rate Limiting")
    rate_frame.pack(fill=tk.X, padx=5, pady=5)
    
    ttk.Label(rate_frame, text="Minimum Delay Between Requests (seconds):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
    min_delay = tk.StringVar(value="1.0")
    ttk.Entry(rate_frame, textvariable=min_delay, width=10).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
    
    ttk.Label(rate_frame, text="Maximum Delay Between Requests (seconds):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
    max_delay = tk.StringVar(value="3.0")
    ttk.Entry(rate_frame, textvariable=max_delay, width=10).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
    
    ttk.Label(rate_frame, text="Requests Per Minute Limit:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
    rpm_limit = tk.StringVar(value="20")
    ttk.Entry(rate_frame, textvariable=rpm_limit, width=10).grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
    
    # Browser settings
    browser_frame = ttk.LabelFrame(settings_frame, text="Browser Settings")
    browser_frame.pack(fill=tk.X, padx=5, pady=5)
    
    ttk.Label(browser_frame, text="Browser Type:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
    browser_type = tk.StringVar(value="chrome")
    browser_combo = ttk.Combobox(browser_frame, textvariable=browser_type, values=["chrome", "firefox", "edge"], width=15)
    browser_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
    browser_combo.current(0)
    
    default_headless = tk.BooleanVar(value=False)
    ttk.Checkbutton(browser_frame, text="Default to Headless Mode", variable=default_headless).grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)
    
    # Default locations
    location_frame = ttk.LabelFrame(settings_frame, text="Default Locations")
    location_frame.pack(fill=tk.X, padx=5, pady=5)
    
    ttk.Label(location_frame, text="Default Locations (comma-separated):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
    default_locations = tk.StringVar(value="Bangalore")
    ttk.Entry(location_frame, textvariable=default_locations, width=40).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
    
    # Separator
    ttk.Separator(parent, orient="horizontal").pack(fill=tk.X, padx=5, pady=10)
    
    # Info text
    info_frame = ttk.Frame(parent)
    info_frame.pack(fill=tk.X, padx=10, pady=5)
    
    info_icon = "ℹ️"
    ttk.Label(info_frame, text=f"{info_icon} Settings will be applied to new scraping tasks", 
             font=("Helvetica", 9, "italic")).pack(anchor=tk.W)
    
    # Buttons
    btn_frame = ttk.Frame(parent)
    btn_frame.pack(fill=tk.X, padx=5, pady=10)
    
    save_btn = ttk.Button(btn_frame, text="Save Settings", command=save_settings_func, style="Primary.TButton")
    save_btn.pack(side=tk.LEFT, padx=5)
    
    reset_btn = ttk.Button(btn_frame, text="Reset to Defaults")
    reset_btn.pack(side=tk.LEFT, padx=5)
    
    # Add version info at the bottom
    version_frame = ttk.Frame(parent)
    version_frame.pack(fill=tk.X, pady=10)
    
    current_year = datetime.now().year
    version_text = f"Heritage Foods Zepto Scraper v3.0.0 © {current_year}"
    version_label = ttk.Label(version_frame, text=version_text, font=("Helvetica", 8), foreground="#666666")
    version_label.pack(side=tk.RIGHT, padx=10)
    
    # Return components
    return {
        "theme": theme_var,
        "min_delay": min_delay,
        "max_delay": max_delay,
        "rpm_limit": rpm_limit,
        "browser_type": browser_type,
        "default_headless": default_headless,
        "default_locations": default_locations,
        "save_btn": save_btn,
        "reset_btn": reset_btn
    }

# ---------------------------
# Utility Functions
# ---------------------------
def select_directory(dir_var):
    """Open directory selection dialog and update the variable"""
    directory = filedialog.askdirectory(initialdir=dir_var.get())
    if directory:
        dir_var.set(directory)

def show_notification(root, title, message, error=False):
    """Show a notification message with a nice visual style"""
    if error:
        messagebox.showerror(title, message)
    else:
        messagebox.showinfo(title, message)

def show_progress(root, title, progress, can_cancel=True, cancel_callback=None):
    """
    Show or update a progress dialog
    
    Returns the toplevel window, which can be updated or destroyed
    """
    # Create progress window
    progress_window = tk.Toplevel(root)
    progress_window.title(title)
    progress_window.geometry("300x150")
    progress_window.resizable(False, False)
    progress_window.transient(root)
    progress_window.grab_set()
    
    # Center window
    root_x = root.winfo_rootx()
    root_y = root.winfo_rooty()
    root_width = root.winfo_width()
    root_height = root.winfo_height()
    
    window_width = 300
    window_height = 150
    
    x = root_x + (root_width // 2) - (window_width // 2)
    y = root_y + (root_height // 2) - (window_height // 2)
    
    progress_window.geometry(f"+{x}+{y}")
    
    # Progress display
    ttk.Label(progress_window, text=title, font=('Helvetica', 12, 'bold')).pack(pady=(15, 5))
    
    # Progress variable
    progress_var = tk.DoubleVar(value=progress)
    
    # Progress bar
    progress_bar = ttk.Progressbar(progress_window, orient=tk.HORIZONTAL, 
                                 length=250, mode='determinate', variable=progress_var)
    progress_bar.pack(pady=10, padx=20)
    
    # Percentage label
    percent_label = ttk.Label(progress_window, text=f"{int(progress)}%")
    percent_label.pack(pady=5)
    
    # Define update function
    def update_percent(*args):
        percent = int(progress_var.get())
        percent_label.config(text=f"{percent}%")
    
    # Register trace on progress variable
    progress_var.trace_add("write", update_percent)
    
    # Cancel button
    if can_cancel and cancel_callback:
        ttk.Button(progress_window, text="Cancel", command=lambda: [cancel_callback(), progress_window.destroy()]).pack(pady=10)
    
    # Update function
    def update_progress(value):
        progress_var.set(value)
        progress_window.update_idletasks()
    
    # Add update method to the window
    progress_window.update_progress = update_progress
    
    return progress_window

def show_help_dialog(root):
    """Show a help dialog with application information and Heritage Foods branding"""
    # Set Heritage colors
    HERITAGE_GREEN = "#008736"
    HERITAGE_RED = "#E31E24"
    
    help_window = tk.Toplevel(root)
    help_window.title("Heritage Foods Zepto Scraper - Help")
    help_window.geometry("650x450")
    help_window.transient(root)
    help_window.grab_set()
    
    # Center window
    root_x = root.winfo_rootx()
    root_y = root.winfo_rooty()
    root_width = root.winfo_width()
    root_height = root.winfo_height()
    
    window_width = 650
    window_height = 450
    
    x = root_x + (root_width // 2) - (window_width // 2)
    y = root_y + (root_height // 2) - (window_height // 2)
    
    help_window.geometry(f"+{x}+{y}")
    
    # Header with title
    header_frame = ttk.Frame(help_window)
    header_frame.pack(fill=tk.X, padx=10, pady=10)
    
    title_label = ttk.Label(header_frame, text="Heritage Foods Zepto Scraper - Help Guide", 
                          font=('Helvetica', 14, 'bold'), foreground=HERITAGE_GREEN)
    title_label.pack(side=tk.LEFT, padx=10)
    
    current_year = datetime.now().year
    version_label = ttk.Label(header_frame, text=f"Version 3.0.0 © {current_year}", 
                            font=('Helvetica', 9), foreground="#666666")
    version_label.pack(side=tk.RIGHT, padx=10)
    
    # Separator
    ttk.Separator(help_window, orient="horizontal").pack(fill=tk.X, padx=10)
    
    # Create notebook for help topics
    notebook = ttk.Notebook(help_window)
    notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # About tab
    about_frame = ttk.Frame(notebook)
    notebook.add(about_frame, text="About")
    
    # About content with scrollable frame
    about_canvas = tk.Canvas(about_frame)
    about_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    about_scrollbar = ttk.Scrollbar(about_frame, orient="vertical", command=about_canvas.yview)
    about_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    about_canvas.configure(yscrollcommand=about_scrollbar.set)
    about_canvas.bind('<Configure>', lambda e: about_canvas.configure(scrollregion=about_canvas.bbox("all")))
    
    about_content = ttk.Frame(about_canvas)
    about_canvas.create_window((0, 0), window=about_content, anchor="nw")
    
    ttk.Label(about_content, text="Heritage Foods Zepto Scraper", 
            font=('Helvetica', 16, 'bold'), foreground=HERITAGE_GREEN).pack(pady=(15, 5))
    ttk.Label(about_content, text="Version 3.0.0").pack(pady=2)
    ttk.Label(about_content, text="An advanced solution for scraping product data from Zepto").pack(pady=2)
    ttk.Label(about_content, text="Enhanced for Heritage Foods price monitoring operations.").pack(pady=2)
    
    ttk.Separator(about_content, orient="horizontal").pack(fill=tk.X, padx=20, pady=15)
    
    desc_text = """
    This tool allows Heritage Foods to monitor competitor pricing across multiple
    locations in India, enabling strategic pricing decisions and market analysis.
    
    The application features a modern user interface with Heritage Foods branding
    and provides comprehensive data extraction capabilities optimized for Zepto's
    e-commerce platform.
    
    Data collected includes product names, brand information, pricing details,
    discount percentages, and availability across different locations.
    """
    
    desc_label = ttk.Label(about_content, text=desc_text, wraplength=550, justify="left")
    desc_label.pack(padx=20, pady=10, fill=tk.X)
    
    # Features tab
    features_frame = ttk.Frame(notebook)
    notebook.add(features_frame, text="Features")
    
    # Features content with scrollable frame
    features_canvas = tk.Canvas(features_frame)
    features_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    features_scrollbar = ttk.Scrollbar(features_frame, orient="vertical", command=features_canvas.yview)
    features_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    features_canvas.configure(yscrollcommand=features_scrollbar.set)
    features_canvas.bind('<Configure>', lambda e: features_canvas.configure(scrollregion=features_canvas.bbox("all")))
    
    features_content = ttk.Frame(features_canvas)
    features_canvas.create_window((0, 0), window=features_content, anchor="nw")
    
    ttk.Label(features_content, text="Key Features", 
            font=('Helvetica', 14, 'bold'), foreground=HERITAGE_GREEN).pack(pady=(15, 10), padx=20, anchor="w")
    
    # Features in a more organized format
    features = [
        ("Search-based scraping", "Extract products based on specific search terms"),
        ("Category-based scraping", "Extract products from predefined categories"),
        ("Multi-location support", "Compare prices across different cities and regions"),
        ("Task scheduling", "Set up automated data collection at specific times"),
        ("Detailed product extraction", "Brand, MRP, discount%, description and more"),
        ("Export capabilities", "Export to Excel, CSV with custom formatting"),
        ("Price comparison", "Compare prices across locations with visualization"),
        ("Rate limiting", "Avoid being blocked with intelligent request timing"),
        ("History tracking", "Keep records of all scraping operations"),
        ("Heritage Foods branding", "Customized UI with corporate identity"),
    ]
    
    for idx, (title, desc) in enumerate(features):
        feature_frame = ttk.Frame(features_content)
        feature_frame.pack(fill=tk.X, padx=20, pady=5)
        
        # Change background color for alternate rows
        bg_color = "#f5f5f5" if idx % 2 == 0 else "#ffffff"
        
        # Feature title with bullet
        ttk.Label(feature_frame, text=f"• {title}", 
                font=('Helvetica', 11, 'bold')).pack(side=tk.LEFT, padx=(0, 10))
        
        # Feature description
        ttk.Label(feature_frame, text=desc).pack(side=tk.LEFT)
    
    # Usage tab
    usage_frame = ttk.Frame(notebook)
    notebook.add(usage_frame, text="Usage Guide")
    
    # Usage content with scrollable frame
    usage_canvas = tk.Canvas(usage_frame)
    usage_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    usage_scrollbar = ttk.Scrollbar(usage_frame, orient="vertical", command=usage_canvas.yview)
    usage_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    usage_canvas.configure(yscrollcommand=usage_scrollbar.set)
    usage_canvas.bind('<Configure>', lambda e: usage_canvas.configure(scrollregion=usage_canvas.bbox("all")))
    
    usage_content = ttk.Frame(usage_canvas)
    usage_canvas.create_window((0, 0), window=usage_content, anchor="nw")
    
    ttk.Label(usage_content, text="How to Use", 
            font=('Helvetica', 14, 'bold'), foreground=HERITAGE_GREEN).pack(pady=(15, 10), padx=20, anchor="w")
    
    # Search tab usage
    ttk.Label(usage_content, text="Search Tab", 
            font=('Helvetica', 12, 'bold')).pack(pady=(10, 5), padx=20, anchor="w")
    
    search_steps = [
        "Enter a search term (e.g., 'milk', 'bread', 'rice')",
        "Specify locations separated by commas (e.g., 'Bangalore, Mumbai, Delhi')",
        "Set the maximum number of products to scrape (leave empty for all)",
        "Choose an output directory for results",
        "Click 'Start Scraping' to begin the data collection process",
        "Monitor progress in the log area below",
        "When complete, use the Export buttons to save results"
    ]
    
    for idx, step in enumerate(search_steps):
        ttk.Label(usage_content, text=f"{idx+1}. {step}").pack(pady=2, padx=30, anchor="w")
    
    # Category tab usage
    ttk.Label(usage_content, text="Category Tab", 
            font=('Helvetica', 12, 'bold')).pack(pady=(15, 5), padx=20, anchor="w")
    
    category_steps = [
        "Select one or more product categories to scrape",
        "Specify locations separated by commas",
        "Set the maximum number of products per category",
        "Choose an output directory for results",
        "Click 'Start Category Scraping' to begin",
        "When complete, use the Export buttons to save results"
    ]
    
    for idx, step in enumerate(category_steps):
        ttk.Label(usage_content, text=f"{idx+1}. {step}").pack(pady=2, padx=30, anchor="w")
    
    # Schedule tab usage
    ttk.Label(usage_content, text="Schedule Tab", 
            font=('Helvetica', 12, 'bold')).pack(pady=(15, 5), padx=20, anchor="w")
    
    schedule_steps = [
        "Choose the task type (Search Term or Category)",
        "Enter the search term or select categories",
        "Set the frequency (Once, Daily, Weekly, Monthly)",
        "Select the time for the task to run",
        "Configure other parameters as needed",
        "Click 'Add Schedule' to create the scheduled task",
        "Tasks will run automatically even if the application is closed"
    ]
    
    for idx, step in enumerate(schedule_steps):
        ttk.Label(usage_content, text=f"{idx+1}. {step}").pack(pady=2, padx=30, anchor="w")
    
    # Troubleshooting tab
    troubleshooting_frame = ttk.Frame(notebook)
    notebook.add(troubleshooting_frame, text="Troubleshooting")
    
    # Troubleshooting content with scrollable frame
    ts_canvas = tk.Canvas(troubleshooting_frame)
    ts_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    ts_scrollbar = ttk.Scrollbar(troubleshooting_frame, orient="vertical", command=ts_canvas.yview)
    ts_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    ts_canvas.configure(yscrollcommand=ts_scrollbar.set)
    ts_canvas.bind('<Configure>', lambda e: ts_canvas.configure(scrollregion=ts_canvas.bbox("all")))
    
    ts_content = ttk.Frame(ts_canvas)
    ts_canvas.create_window((0, 0), window=ts_content, anchor="nw")
    
    ttk.Label(ts_content, text="Common Issues and Solutions", 
            font=('Helvetica', 14, 'bold'), foreground=HERITAGE_GREEN).pack(pady=(15, 10), padx=20, anchor="w")
    
    issues = [
        ("Browser Not Found", "Make sure Chrome or Firefox is installed on your system. The application uses these browsers for scraping."),
        ("Too Many Requests (429)", "The scraper is being rate-limited. Try adjusting request delay in Settings or use fewer locations."),
        ("No Results Found", "Check that your search term is spelled correctly or try a different search term."),
        ("Location Not Available", "Some locations may not be available on Zepto. Try a major city like Bangalore, Mumbai, or Delhi."),
        ("Scheduled Tasks Not Running", "Ensure the application is running for scheduled tasks to execute."),
        ("Export Errors", "Check that the output directory exists and you have write permissions.")
    ]
    
    for title, desc in issues:
        issue_frame = ttk.Frame(ts_content)
        issue_frame.pack(fill=tk.X, padx=20, pady=5)
        
        ttk.Label(issue_frame, text=title, 
                font=('Helvetica', 11, 'bold')).pack(anchor="w")
        ttk.Label(issue_frame, text=desc, 
                wraplength=550).pack(anchor="w", padx=20, pady=3)
    
    # Footer with close button
    footer_frame = ttk.Frame(help_window)
    footer_frame.pack(fill=tk.X, padx=10, pady=10)
    
    support_text = "For additional support, contact the Heritage Foods IT department."
    ttk.Label(footer_frame, text=support_text, font=('Helvetica', 9, 'italic')).pack(side=tk.LEFT, padx=10)
    
    close_button = ttk.Button(footer_frame, text="Close", command=help_window.destroy)
    close_button.pack(side=tk.RIGHT, padx=10)
    
    # Make the window modal
    help_window.focus_set()
    help_window.grab_set()