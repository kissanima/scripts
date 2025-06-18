"""
Enhanced Minecraft Server Manager v2.0 - With Complete MOD MANAGEMENT
Main entry point with comprehensive error handling, logging, and mod support
"""

import os
import sys
import logging
import traceback
from pathlib import Path
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import core modules
from constants import APP_NAME, VERSION, APP_DIR
from config import Config
from error_handler import ErrorHandler, ErrorSeverity

# MOD MANAGEMENT IMPORTS - With fallback handling
try:
    from mod_manager import ModManager
    from mod_backup_manager import ModBackupManager
    from mod_dependency_resolver import ModDependencyResolver
    from mod_update_checker import ModUpdateChecker
    from mod_config_manager import ModConfigManager
    from mod_downloader import ModDownloader
    MOD_MANAGEMENT_AVAILABLE = True
    print("✅ Mod management modules loaded successfully")
except ImportError as e:
    MOD_MANAGEMENT_AVAILABLE = False
    print(f"⚠️ Mod management not available: {e}")
    # Create dummy classes to prevent import errors
    ModManager = None
    ModBackupManager = None
    ModDependencyResolver = None
    ModUpdateChecker = None
    ModConfigManager = None
    ModDownloader = None

class MinecraftServerManager:
    """Main application class with comprehensive mod management integration"""
    
    def __init__(self):
        """Initialize the Minecraft Server Manager with full mod support"""
        self.setup_logging()
        self.error_handler = ErrorHandler()
        
        try:
            logging.info(f"Starting {APP_NAME} v{VERSION}")
            logging.info(f"Python version: {sys.version}")
            logging.info(f"Working directory: {os.getcwd()}")
            logging.info(f"App directory: {APP_DIR}")
            
            # Initialize core configuration
            self.config = Config()
            logging.info("✅ Configuration system initialized")
            
            # Validate environment
            self.validate_environment()
            
            # Initialize core managers
            self.initialize_core_managers()
            
            # Initialize MOD MANAGEMENT system
            self.initialize_mod_management()
            
            # Setup signal handlers
            self.setup_signal_handlers()
            
            logging.info("✅ Minecraft Server Manager initialized successfully")
            
        except Exception as e:
            self.handle_initialization_error(e)
            raise
    
    def setup_logging(self):
        """Setup comprehensive logging system"""
        try:
            # Ensure logs directory exists
            logs_dir = APP_DIR / "logs"
            logs_dir.mkdir(exist_ok=True)
            
            # Generate log filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d")
            log_file = logs_dir / f"minecraft_server_manager_{timestamp}.log"
            
            # Configure logging with both file and console handlers
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_file, encoding='utf-8'),
                    logging.StreamHandler(sys.stdout)
                ]
            )
            
            # Set specific log levels for different modules
            logging.getLogger('urllib3').setLevel(logging.WARNING)
            logging.getLogger('requests').setLevel(logging.WARNING)
            
            # Create mod management logger
            if MOD_MANAGEMENT_AVAILABLE:
                mod_logger = logging.getLogger('mod_management')
                mod_logger.setLevel(logging.INFO)
            
            print(f"✅ Logging initialized - Log file: {log_file}")
            
        except Exception as e:
            print(f"❌ Failed to setup logging: {e}")
            # Fallback to basic logging
            logging.basicConfig(level=logging.INFO)
    
    def validate_environment(self):
        """Validate the runtime environment"""
        try:
            logging.info("Validating environment...")
            
            # Check Python version
            if sys.version_info < (3, 8):
                raise RuntimeError(f"Python 3.8+ required, found {sys.version}")
            
            # Check required directories
            required_dirs = ['gui', 'gui/tabs', 'gui/components', 'gui/utils']
            missing_dirs = []
            
            for dir_name in required_dirs:
                if not os.path.exists(dir_name):
                    missing_dirs.append(dir_name)
            
            if missing_dirs:
                logging.warning(f"Missing directories: {missing_dirs}")
                # Create missing directories
                for dir_name in missing_dirs:
                    os.makedirs(dir_name, exist_ok=True)
                    logging.info(f"Created directory: {dir_name}")
            
            # Check file permissions
            test_file = APP_DIR / "permission_test.tmp"
            try:
                test_file.write_text("test")
                test_file.unlink()
                logging.info("✅ File permissions validated")
            except Exception as e:
                logging.error(f"❌ File permission error: {e}")
                raise RuntimeError("Insufficient file permissions")
            
            # Validate mod management requirements
            if MOD_MANAGEMENT_AVAILABLE:
                self.validate_mod_management_environment()
            
            logging.info("✅ Environment validation completed")
            
        except Exception as e:
            error_info = self.error_handler.handle_error(e, "environment_validation", ErrorSeverity.HIGH)
            logging.error(f"Environment validation failed: {error_info['message']}")
            raise
    
    def validate_mod_management_environment(self):
        """Validate mod management specific requirements"""
        try:
            logging.info("Validating mod management environment...")
            
            # Check required Python packages
            required_packages = ['requests', 'toml']
            missing_packages = []
            
            for package in required_packages:
                try:
                    __import__(package)
                except ImportError:
                    missing_packages.append(package)
            
            if missing_packages:
                logging.warning(f"Missing optional packages for mod management: {missing_packages}")
                logging.warning("Some mod features may be limited. Install with: pip install " + " ".join(missing_packages))
            
            # Check network connectivity for mod repositories (optional)
            try:
                import requests
                response = requests.get("https://api.modrinth.com/v2/", timeout=5)
                if response.status_code == 200:
                    logging.info("✅ Modrinth API connectivity verified")
            except Exception as e:
                logging.warning(f"Modrinth API not accessible: {e}")
            
            logging.info("✅ Mod management environment validated")
            
        except Exception as e:
            logging.warning(f"Mod management environment validation warning: {e}")
    
    def initialize_core_managers(self):
        """Initialize core application managers"""
        try:
            logging.info("Initializing core managers...")
            
            # These will be initialized when needed
            self.process_manager = None
            self.vd_manager = None
            self.health_monitor = None
            self.backup_manager = None
            self.auto_shutdown_manager = None
            self.sleep_manager = None
            
            logging.info("✅ Core managers prepared for initialization")
            
        except Exception as e:
            error_info = self.error_handler.handle_error(e, "core_managers_init", ErrorSeverity.HIGH)
            logging.error(f"Core managers initialization failed: {error_info['message']}")
            raise
    
    def initialize_mod_management(self):
        """Initialize comprehensive mod management system"""
        if not MOD_MANAGEMENT_AVAILABLE:
            logging.warning("⚠️ Mod management not available - skipping initialization")
            self.mod_management_enabled = False
            return
        
        try:
            logging.info("🔧 Initializing mod management system...")
            
            # Get current server directory
            server_dir = self.get_current_server_directory()
            
            # Core mod manager
            self.modmanager = ModManager(
                self.config,           # positional: config
                self.error_handler,    # positional: error_handler
                server_dir=server_dir,  # positional: server directory
            )
            logging.info("✅ ModManager initialized")
            
            # Backup manager
            self.modbackupmanager = ModBackupManager(
                modmanager=self.modmanager,
                config=self.config
            )
            logging.info("✅ ModBackupManager initialized")
            
            # Dependency resolver
            self.moddependencyresolver = ModDependencyResolver(
                modmanager=self.modmanager,
                config=self.config
            )
            logging.info("✅ ModDependencyResolver initialized")
            
            # Update checker
            self.modupdatechecker = ModUpdateChecker(
                modmanager=self.modmanager,
                config=self.config
            )
            logging.info("✅ ModUpdateChecker initialized")
            
            # Config manager
            self.modconfigmanager = ModConfigManager(
                modmanager=self.modmanager,
                config=self.config
            )
            logging.info("✅ ModConfigManager initialized")
            
            # Downloader
            self.moddownloader = ModDownloader(
                modmanager=self.modmanager,
                config=self.config
            )
            logging.info("✅ ModDownloader initialized")
            
            # Connect managers
            self.modmanager.backupmanager = self.modbackupmanager
            
            # Register callbacks
            self.setup_mod_management_callbacks()
            
            # Perform initial mod scan if enabled and server directory exists
            if (self.config.get_mod_setting("auto_scan_on_startup", True) and 
                server_dir and os.path.exists(server_dir)):
                logging.info("🔍 Performing initial mod scan...")
                self.modmanager.scan_mods()
            
            # Start update checking if enabled
            if self.config.get_mod_setting("check_updates_on_startup", False):
                logging.info("📦 Starting background update check...")
                import threading
                update_thread = threading.Thread(
                    target=self.modupdatechecker.check_for_updates,
                    daemon=True
                )
                update_thread.start()
            
            self.mod_management_enabled = True
            logging.info("🎉 Mod management system fully initialized!")
            
        except Exception as e:
            self.mod_management_enabled = False
            error_info = self.error_handler.handle_error(e, "mod_management_init", ErrorSeverity.MEDIUM)
            logging.error(f"❌ Mod management initialization failed: {error_info['message']}")
            
            # Set fallback values
            self.modmanager = None
            self.modbackupmanager = None
            self.moddependencyresolver = None
            self.modupdatechecker = None
            self.modconfigmanager = None
            self.moddownloader = None
            
            logging.warning("⚠️ Continuing without mod management features")
    
    def setup_mod_management_callbacks(self):
        """Setup mod management event callbacks"""
        try:
            # Register core callbacks
            if hasattr(self.modmanager, 'registerscancallback'):
                self.modmanager.register_scan_callback(self.on_mod_scan_progress)
            
            if hasattr(self.modmanager, 'registerinstallcallback'):
                self.modmanager.register_scan_callback(self.on_mod_operation)
            
            # Register update callbacks
            if hasattr(self.modupdatechecker, 'register_completion_callback'):
                self.modupdatechecker.register_completion_callback(self.on_mod_updates_checked)
            
            if hasattr(self.modupdatechecker, 'register_update_found_callback'):
                self.modupdatechecker.register_update_found_callback(self.on_mod_update_found)
            
            # Register download callbacks
            if hasattr(self.moddownloader, 'register_download_completed_callback'):
                self.moddownloader.register_download_completed_callback(self.on_mod_download_completed)
            
            if hasattr(self.moddownloader, 'register_global_progress_callback'):
                self.moddownloader.register_global_progress_callback(self.on_mod_download_progress)
            
            # Register backup callbacks
            if hasattr(self.modbackupmanager, 'registercompletioncallback'):
                self.modbackupmanager.registercompletioncallback(self.on_mod_backup_completed)
            
            logging.info("✅ Mod management callbacks registered")
            
        except Exception as e:
            logging.error(f"Error setting up mod management callbacks: {e}")
    
    def get_current_server_directory(self) -> str:
        """Get the current server directory for mod management"""
        try:
            # Try to get from config
            last_jar = self.config.get("last_server_jar", "")
            if last_jar and os.path.exists(last_jar):
                return os.path.dirname(last_jar)
            
            # Default to current working directory
            return os.getcwd()
            
        except Exception as e:
            logging.error(f"Error getting server directory: {e}")
            return os.getcwd()
    
    # MOD MANAGEMENT CALLBACK HANDLERS
    def on_mod_scan_progress(self, progress: int, message: str):
        """Handle mod scan progress updates"""
        logging.info(f"Mod scan: {progress}% - {message}")
    
    def on_mod_operation(self, operation: str, modinfo, message: str):
        """Handle mod operation notifications"""
        if modinfo:
            logging.info(f"Mod {operation}: {modinfo.name} - {message}")
        else:
            logging.info(f"Mod {operation}: {message}")
    
    def on_mod_updates_checked(self, updates_info):
        """Handle mod update check completion"""
        try:
            available_updates = [u for u in updates_info.values() 
                               if hasattr(u, 'update_status') and u.update_status.value == "update_available"]
            
            if available_updates:
                logging.info(f"📦 Found {len(available_updates)} mod update(s) available")
                for update in available_updates:
                    logging.info(f"  - {update.modid}: {update.current_version} → {update.latest_version}")
            else:
                logging.info("✅ All mods are up to date")
                
        except Exception as e:
            logging.error(f"Error processing mod update results: {e}")
    
    def on_mod_update_found(self, update_info):
        """Handle individual mod update found"""
        logging.info(f"📦 Update available for {update_info.modid}: {update_info.current_version} → {update_info.latest_version}")
    
    def on_mod_download_completed(self, download_task):
        """Handle mod download completion"""
        if hasattr(download_task, 'status') and download_task.status.value == "completed":
            logging.info(f"📥 Downloaded: {download_task.mod_name}")
        else:
            logging.error(f"❌ Download failed: {download_task.mod_name} - {download_task.error_message}")
    
    def on_mod_download_progress(self, download_task):
        """Handle mod download progress"""
        if hasattr(download_task, 'progress_percentage'):
            progress = download_task.progress_percentage
            if progress > 0 and progress % 25 == 0:  # Log every 25%
                logging.info(f"📥 Downloading {download_task.mod_name}: {progress:.1f}%")
    
    def on_mod_backup_completed(self, backup_type: str, backup_info, message: str):
        """Handle mod backup completion"""
        logging.info(f"💾 Mod backup completed ({backup_type}): {message}")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        try:
            import signal
            
            def signal_handler(signum, frame):
                logging.info(f"Received signal {signum}, initiating shutdown...")
                self.shutdown()
                sys.exit(0)
            
            # Handle common termination signals
            signal.signal(signal.SIGINT, signal_handler)
            if hasattr(signal, 'SIGTERM'):
                signal.signal(signal.SIGTERM, signal_handler)
            
            logging.info("✅ Signal handlers registered")
            
        except Exception as e:
            logging.warning(f"Could not setup signal handlers: {e}")
    
    def handle_initialization_error(self, error):
        """Handle initialization errors gracefully"""
        try:
            error_info = self.error_handler.handle_error(error, "initialization", ErrorSeverity.CRITICAL)
            
            error_msg = (
                f"Failed to initialize {APP_NAME}:\n\n"
                f"Error: {error_info['message']}\n"
                f"Context: {error_info['context']}\n"
                f"Time: {error_info['timestamp']}\n\n"
                f"Please check the log file for more details."
            )
            
            logging.critical(error_msg)
            print(f"\n❌ CRITICAL ERROR:\n{error_msg}")
            
            # Try to show GUI error dialog
            try:
                import tkinter as tk
                from tkinter import messagebox
                root = tk.Tk()
                root.withdraw()
                messagebox.showerror("Initialization Error", error_msg)
                root.destroy()
            except Exception:
                pass  # GUI not available
            
        except Exception as e:
            print(f"Error handling initialization error: {e}")
    
    def run(self):
        """Run the application"""
        try:
            logging.info("🚀 Starting GUI...")
            
            # Import and run GUI
            from gui.main_window import run_gui
            run_gui()
            
        except KeyboardInterrupt:
            logging.info("Application interrupted by user")
        except Exception as e:
            error_info = self.error_handler.handle_error(e, "main_run", ErrorSeverity.CRITICAL)
            logging.critical(f"Critical error in main run: {error_info['message']}")
            raise
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Gracefully shutdown the application"""
        try:
            logging.info("🔄 Shutting down Minecraft Server Manager...")
            
            # Shutdown mod management components
            if hasattr(self, 'mod_management_enabled') and self.mod_management_enabled:
                try:
                    logging.info("🔧 Shutting down mod management...")
                    
                    if hasattr(self, 'moddownloader') and self.moddownloader:
                        self.moddownloader.shutdown()
                    
                    # Save all mod management data
                    if hasattr(self, 'modmanager') and self.modmanager:
                        self.modmanager.save_database()
                    
                    if hasattr(self, 'modbackupmanager') and self.modbackupmanager:
                        self.modbackupmanager.savebackupindex()
                    
                    if hasattr(self, 'modupdatechecker') and self.modupdatechecker:
                        self.modupdatechecker.save_update_cache()
                    
                    if hasattr(self, 'modconfigmanager') and self.modconfigmanager:
                        self.modconfigmanager.save_config_database()
                    
                    logging.info("✅ Mod management shutdown completed")
                    
                except Exception as e:
                    logging.error(f"Error shutting down mod management: {e}")
            
            # Save configuration
            if hasattr(self, 'config') and self.config:
                self.config.save_config()
            
            logging.info("✅ Shutdown completed successfully")
            
        except Exception as e:
            logging.error(f"Error during shutdown: {e}")

def main():
    """Main entry point with comprehensive error handling"""
    try:
        print(f"🎮 Starting {APP_NAME} v{VERSION}")
        print("=" * 50)
        
        # Create and run the application
        app = MinecraftServerManager()
        app.run()
        
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        print("\nStacktrace:")
        traceback.print_exc()
        
        # Log the error if possible
        try:
            logging.critical(f"Fatal error in main(): {e}")
        except:
            pass
        
        input("\nPress Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main()
