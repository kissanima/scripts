#!/usr/bin/env python3
"""
Enhanced Minecraft Server Manager - Main Entry Point
Includes comprehensive error handling and recovery with modular GUI
"""

import sys
import os
import logging
import traceback
import tkinter as tk
from pathlib import Path

# Add the current directory to Python path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def check_core_files():
    """Check if all core files exist"""
    required_files = [
        'config.py',
        'themes.py', 
        'constants.py',
        'error_handler.py',
        'process_manager.py',
        'server_properties_manager.py',
        'gui/__init__.py',
        'gui/main_window.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not (current_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print("ERROR: Missing required files:")
        for file in missing_files:
            print(f"  - {file}")
        print("\nPlease ensure all files are in the correct locations.")
        return False
    
    return True

# Import our modules with better error handling
try:
    # Check files first
    if not check_core_files():
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Import core modules
    from themes import get_theme, get_status_color, get_theme_names
    from constants import APP_NAME, VERSION, LOGS_DIR, BACKUPS_DIR, ERROR_REPORTS_DIR
    from error_handler import ErrorHandler
    from gui import MinecraftServerGUI
    
except ImportError as e:
    print(f"Failed to import required modules: {e}")
    print("Please ensure all required files are in the correct directories.")
    print(f"Current directory: {current_dir}")
    print("\nTrying to diagnose the issue...")
    
    # Try to import each module individually to identify the problem
    modules_to_test = [
        ('themes', 'themes.py'),
        ('constants', 'constants.py'), 
        ('error_handler', 'error_handler.py'),
        ('config', 'config.py'),
        ('gui', 'gui/__init__.py')
    ]
    
    for module_name, file_path in modules_to_test:
        try:
            __import__(module_name)
            print(f"✓ {module_name} - OK")
        except ImportError as ie:
            print(f"✗ {module_name} - FAILED: {ie}")
    
    input("\nPress Enter to exit...")
    sys.exit(1)

def setup_directories():
    """Create necessary application directories"""
    try:
        directories = [LOGS_DIR, BACKUPS_DIR, ERROR_REPORTS_DIR]
        
        for directory in directories:
            directory.mkdir(exist_ok=True)
            
        # Create temp directory
        temp_dir = Path.cwd() / "temp"
        temp_dir.mkdir(exist_ok=True)
        
        logging.info("Application directories created successfully")
        
    except Exception as e:
        print(f"Failed to create directories: {e}")
        logging.error(f"Failed to create directories: {e}")

def setup_logging():
    """Setup application logging"""
    try:
        log_file = LOGS_DIR / "server_manager.log"
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Log startup
        logging.info(f"Starting {APP_NAME} v{VERSION}")
        logging.info(f"Python version: {sys.version}")
        logging.info(f"Working directory: {Path.cwd()}")
        
    except Exception as e:
        print(f"Failed to setup logging: {e}")

def setup_global_exception_handler():
    """Setup global exception handler for unhandled exceptions"""
    def handle_exception(exc_type, exc_value, exc_traceback):
        # Don't catch KeyboardInterrupt
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        try:
            error_handler = ErrorHandler()
            error_report = error_handler.create_error_report(exc_value)
            error_handler.save_error_report(error_report)
            
            logging.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
            
            # Try to show error dialog if GUI is available
            try:
                root = tk.Tk()
                root.withdraw()
                from tkinter import messagebox
                messagebox.showerror(
                    "Critical Error", 
                    f"An unexpected error occurred:\n\n{exc_value}\n\nError details saved to logs.\n\nThe application will now exit."
                )
                root.destroy()
            except:
                # If GUI fails, just print the error
                print(f"Critical error: {exc_value}")
                
        except Exception as e:
            # Last resort error handling
            print(f"Critical error in exception handler: {e}")
            print(f"Original error: {exc_value}")
    
    sys.excepthook = handle_exception

def check_dependencies():
    """Check if all required dependencies are available"""
    required_modules = [
        'tkinter',
        'threading', 
        'json',
        'subprocess',
        'pathlib',
        'datetime',
        'logging'
    ]
    
    optional_modules = [
        ('PIL', 'Pillow - for enhanced UI icons'),
        ('psutil', 'psutil - for system monitoring'),
        ('pystray', 'pystray - for system tray functionality')
    ]
    
    missing_required = []
    missing_optional = []
    
    # Check required modules
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_required.append(module)
    
    # Check optional modules
    for module, description in optional_modules:
        try:
            __import__(module)
        except ImportError:
            missing_optional.append((module, description))
    
    if missing_required:
        print(f"ERROR: Missing required modules: {', '.join(missing_required)}")
        print("Please install the required modules and try again.")
        return False
    
    if missing_optional:
        print("WARNING: Missing optional modules:")
        for module, desc in missing_optional:
            print(f"  - {desc}")
        print("Some features may not be available.\n")
    
    return True

def check_system_requirements():
    """Check system requirements"""
    try:
        # Check Python version
        if sys.version_info < (3, 7):
            print(f"ERROR: Python 3.7 or higher is required. You have {sys.version}")
            return False
        
        # Check if running on supported OS
        import platform
        os_name = platform.system()
        if os_name not in ['Windows', 'Linux', 'Darwin']:
            print(f"WARNING: Untested operating system: {os_name}")
        
        # Check available disk space (at least 100MB)
        import shutil
        free_space = shutil.disk_usage(Path.cwd()).free
        if free_space < 100 * 1024 * 1024:  # 100MB
            print("WARNING: Low disk space available")
        
        return True
        
    except Exception as e:
        print(f"WARNING: Could not check system requirements: {e}")
        return True  # Continue anyway

def print_startup_info():
    """Print startup information"""
    print(f"")
    print(f"╔══════════════════════════════════════════════════════════════╗")
    print(f"║                                                              ║")
    print(f"║        🎮 Enhanced Minecraft Server Manager v{VERSION:<10}      ║")
    print(f"║                                                              ║")
    print(f"║  A comprehensive server management tool with modern UI       ║")
    print(f"║                                                              ║")
    print(f"╚══════════════════════════════════════════════════════════════╝")
    print(f"")
    print(f"Working Directory: {Path.cwd()}")
    print(f"")

def main():
    """Main entry point for the application"""
    try:
        # Print startup information
        print_startup_info()
        
        # Check system requirements
        print("Checking system requirements...")
        if not check_system_requirements():
            print("System requirements check failed.")
            input("Press Enter to exit...")
            sys.exit(1)
        
        # Check dependencies
        print("Checking dependencies...")
        if not check_dependencies():
            input("Press Enter to exit...")
            sys.exit(1)
        
        print("✓ All checks passed")
        print("")
        
        # Setup global exception handling
        setup_global_exception_handler()
        
        # Create application directories
        print("Setting up application directories...")
        setup_directories()
        
        # Setup logging
        print("Initializing logging system...")
        setup_logging()
        
        print("Starting GUI application...")
        print("=" * 60)
        
        # Start the GUI application
        app = MinecraftServerGUI()
        app.run()
        
        # If we get here, the app closed normally
        logging.info("Application closed normally")
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        logging.info("Application interrupted by user (Ctrl+C)")
        
    except Exception as e:
        error_msg = f"Failed to start application: {e}"
        print(f"\nERROR: {error_msg}")
        print(f"Traceback: {traceback.format_exc()}")
        
        try:
            logging.error(error_msg)
            logging.error(traceback.format_exc())
        except:
            pass
        
        input("Press Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    # Check for command line arguments
    if len(sys.argv) > 1:
        if "--help" in sys.argv or "-h" in sys.argv:
            print(f"{APP_NAME} v{VERSION}")
            print("\nUsage:")
            print("  python main.py              - Start the application")
            print("  python main.py --help        - Show this help message")
            sys.exit(0)
    
    # Run the main application
    main()
