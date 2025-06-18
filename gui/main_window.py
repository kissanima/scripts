"""
Main window for the Minecraft Server Manager GUI - With Working Console Capture and MOD MANAGEMENT
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import logging
import threading
import time
from constants import APP_NAME, VERSION

# Import managers and components
from config import Config
from process_manager import ProcessManager
from virtual_desktop_manager import VirtualDesktopManager
from auto_shutdown_manager import AutoShutdownManager
from sleep_manager import SleepManager
from error_handler import ErrorHandler, ErrorSeverity
from memory_manager import MemoryManager, LogManager, TextWidgetManager
from health_monitor import ServerHealthMonitor
from backup_manager import BackupManager
from server_properties_manager import ServerPropertiesManager

# Import MOD MANAGEMENT components
try:
    from mod_manager import ModManager
    from mod_backup_manager import ModBackupManager
    from mod_dependency_resolver import ModDependencyResolver
    from mod_update_checker import ModUpdateChecker
    from mod_config_manager import ModConfigManager
    from mod_downloader import ModDownloader
    MOD_MANAGEMENT_AVAILABLE = True
    logging.info("✅ Mod management modules imported successfully")
except ImportError as e:
    MOD_MANAGEMENT_AVAILABLE = False
    logging.warning(f"⚠️ Mod management not available: {e}")
    # Create dummy classes to prevent errors
    ModManager = None
    ModBackupManager = None
    ModDependencyResolver = None
    ModUpdateChecker = None
    ModConfigManager = None
    ModDownloader = None

# Import GUI components
from .utils.theme_manager import ThemeManager
from .components.header import ModernHeader
from .components.footer import ModernFooter
from .tabs.dashboard_tab import DashboardTab
from .tabs.server_control_tab import ServerControlTab
from .tabs.console_tab import ConsoleTab
from .tabs.backup_tab import BackupTab
from .tabs.health_tab import HealthTab
from .tabs.settings_tab import SettingsTab
from .tabs.server_properties_tab import ServerPropertiesTab

# Import MOD MANAGEMENT GUI components
try:
    from .tabs.mods_tab import ModsTab
    MODS_TAB_AVAILABLE = True
    logging.info("✅ Mods tab imported successfully")
except ImportError as e:
    MODS_TAB_AVAILABLE = False
    ModsTab = None
    logging.warning(f"⚠️ Mods tab not available: {e}")

class MinecraftServerGUI:
    """Main GUI application for Minecraft Server Manager with Working Console Capture and MOD MANAGEMENT"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} v{VERSION}")
        self.mod_management_enabled = False  # Default to False
        # Set professional window size and make it responsive
        self.setup_window_properties()
        
        # Initialize core components
        self.error_handler = ErrorHandler()
        self.config = Config()
        self.server_properties_manager = ServerPropertiesManager(self.error_handler)
        
        # Initialize MOD MANAGEMENT components
        self.initialize_mod_management()
        
        # Initialize managers
        self.process_manager = ProcessManager(self.config)
        self.vd_manager = VirtualDesktopManager("VirtualDesktopAccessor.dll")
        
        # Initialize enhanced managers
        self.memory_manager = MemoryManager()
        self.log_manager = LogManager()
        self.text_widget_manager = TextWidgetManager()
        self.health_monitor = ServerHealthMonitor(self.process_manager, self.config)
        self.backup_manager = BackupManager(self.process_manager, self.config)
        self.auto_shutdown_manager = AutoShutdownManager(self)
        self.sleep_manager = SleepManager(self)
        
        
        # Initialize theme manager
        self.theme_manager = ThemeManager(self.config)
        
        # Initialize variables
        self.server_jar_path = ""
        self.playit_path = ""
        
        # Console monitoring
        self.monitoring_active = True
        self.log_reading_thread = None
        
        # GUI components
        self.header = None
        self.footer = None
        self.notebook = None
        self.tabs = {}
        
        # Apply theme and create GUI
        self.apply_theme()
        self.create_professional_gui()
        self.setup_callbacks()
        
        # FIXED: Load saved paths with delay to ensure UI is ready
        self.root.after(500, self.load_saved_paths)  # 500ms delay
        self.start_managers()
        
        # Check for first-time setup AFTER everything is loaded
        self.root.after(2000, self.check_first_time_setup)  # 2 second delay
        
        # Setup window protocol
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        logging.info("Enhanced Minecraft Server Manager with Mod Management initialized")
    
    def initialize_mod_management(self):
        """Initialize all mod management components"""
        if not MOD_MANAGEMENT_AVAILABLE:
            logging.warning("Mod management components not available - skipping initialization")
            self.mod_management_enabled = False
            return
        
        try:
            logging.info("Initializing mod management system...")
            
            # Core mod manager
            self.modmanager = ModManager(
                self.config,                            # positional: config
                self.error_handler,                     # positional: error_handler  
                self.get_current_server_directory() 
            )
            
            # Backup manager
            self.modbackupmanager = ModBackupManager(
                modmanager=self.modmanager,
                config=self.config
            )
            
            # Dependency resolver
            self.moddependencyresolver = ModDependencyResolver(
                modmanager=self.modmanager,
                config=self.config
            )
            
            # Update checker
            self.modupdatechecker = ModUpdateChecker(
                modmanager=self.modmanager,
                config=self.config
            )
            
            # Config manager
            self.modconfigmanager = ModConfigManager(
                modmanager=self.modmanager,
                config=self.config
            )
            
            # Downloader
            self.moddownloader = ModDownloader(
                modmanager=self.modmanager,
                config=self.config
            )
            
            # Connect backup manager to mod manager
            self.modmanager.backupmanager = self.modbackupmanager
            
            # Register mod management callbacks
            self.setup_mod_callbacks()
            
            self.mod_management_enabled = True
            logging.info("✅ Mod management system initialized successfully")
            
        except Exception as e:
            logging.error(f"❌ Error initializing mod management: {e}")
            self.error_handler.handle_error(e, "mod_management_init", ErrorSeverity.MEDIUM)
            
            # Set fallback values
            self.mod_management_enabled = False
            self.modmanager = None
            self.modbackupmanager = None
            self.moddependencyresolver = None
            self.modupdatechecker = None
            self.modconfigmanager = None
            self.moddownloader = None
            self.mod_management_enabled = False
    
    def setup_mod_callbacks(self):
        """Setup mod management callbacks"""
        try:
            if not self.mod_management_enabled:
                return
            
            # Register mod operation callbacks - FIXED method names
            if hasattr(self.modmanager, 'register_install_callback'):
                self.modmanager.register_install_callback(self.on_mod_operation)
            
            # Register update callbacks
            if hasattr(self.modupdatechecker, 'register_completion_callback'):
                self.modupdatechecker.register_completion_callback(self.on_mod_updates_checked)
            
            # Register download callbacks
            if hasattr(self.moddownloader, 'register_download_completed_callback'):
                self.moddownloader.register_download_completed_callback(self.on_mod_download_completed)
            
            logging.info("Mod management callbacks registered")
            
        except Exception as e:
            logging.error(f"Error setting up mod callbacks: {e}")

    
    def get_current_server_directory(self) -> str:
        """Get the current server directory for mod management"""
        try:
            # Try to get from server JAR path
            if hasattr(self, 'server_jar_path') and self.server_jar_path:
                return os.path.dirname(self.server_jar_path)
            
            # Try to get from process manager
            if hasattr(self, 'process_manager') and self.process_manager:
                if hasattr(self.process_manager, 'serverdir'):
                    return self.process_manager.serverdir
            
            # Try to get from config
            last_jar = self.config.get("last_server_jar", "")
            if last_jar and os.path.exists(last_jar):
                return os.path.dirname(last_jar)
            
            # Default to current working directory
            return os.getcwd()
            
        except Exception as e:
            logging.error(f"Error getting server directory: {e}")
            return os.getcwd()
    
    def update_server_directory_for_mods(self, new_server_dir: str):
        """Update server directory for mod management components"""
        try:
            if not self.mod_management_enabled:
                return
            
            logging.info(f"Updating mod management server directory to: {new_server_dir}")
            
            # Update mod manager
            if self.modmanager:
                self.modmanager.set_server_directory(new_server_dir)
            
            # Update config manager paths
            if self.modconfigmanager:
                self.modconfigmanager.setup_directories()
            
            # Refresh mods tab if it exists
            if hasattr(self, 'mods_tab') and self.mods_tab:
                self.root.after(1000, self.mods_tab.refresh_mods)  # Delay to let directory update complete
            
            logging.info("Mod management server directory updated successfully")
            
        except Exception as e:
            logging.error(f"Error updating server directory for mods: {e}")
    
    def setup_window_properties(self):
        """Setup professional window properties"""
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate optimal window size (70% of screen, but within reasonable bounds)
        optimal_width = min(max(int(screen_width * 0.7), 1200), 1600)
        optimal_height = min(max(int(screen_height * 0.8), 800), 1000)
        
        # Center the window
        x = (screen_width - optimal_width) // 2
        y = (screen_height - optimal_height) // 2
        
        self.root.geometry(f"{optimal_width}x{optimal_height}+{x}+{y}")
        self.root.minsize(1000, 700)  # Minimum size for usability
        
        # Make window resizable with proper scaling
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Set window icon if available
        try:
            self.root.iconname(APP_NAME)
        except:
            pass
    
    def apply_theme(self):
        """Apply current theme to root window"""
        theme = self.theme_manager.get_current_theme()
        self.root.configure(bg=theme['bg_primary'])
    
    def create_professional_gui(self):
        """Create professional GUI with consistent grid layout"""
        theme = self.theme_manager.get_current_theme()
        
        # Main container with professional padding
        main_container = tk.Frame(self.root, bg=theme['bg_primary'])
        main_container.pack(fill="both", expand=True, padx=theme['padding_large'], pady=theme['padding_large'])
        
        # Configure main container for grid layout
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_rowconfigure(1, weight=1)  # Content area should expand
        
        # Header (fixed height) - using grid
        self.header = ModernHeader(main_container, self.theme_manager, VERSION)
        self.header.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, theme['margin_medium']))
        self.header.bind_theme_change(self.on_theme_change)
        
        # Content area (expandable) - using grid
        content_frame = tk.Frame(main_container, bg=theme['bg_primary'])
        content_frame.grid(row=1, column=0, sticky="nsew")
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        
        # Create professional notebook
        self.notebook = ttk.Notebook(content_frame, style='Modern.TNotebook')
        self.notebook.grid(row=0, column=0, sticky="nsew")
        
        # Create tabs
        self.create_tabs()
        
        # Footer (fixed height) - using grid
        self.footer = ModernFooter(main_container, self.theme_manager)
        self.footer.footer_frame.grid(row=2, column=0, sticky="ew", pady=(theme['margin_medium'], 0))
    
    def create_tabs(self):
        """Create all tabs with professional styling including MODS TAB"""
        try:
            # Dashboard tab
            self.tabs['dashboard'] = DashboardTab(self.notebook, self.theme_manager, self)
            self.tabs['dashboard'].add_to_notebook(self.notebook, "🏠 Dashboard")
            
            # Server Control tab
            self.tabs['server_control'] = ServerControlTab(self.notebook, self.theme_manager, self)
            self.tabs['server_control'].add_to_notebook(self.notebook, "🎮 Server Control")
            
            # Console tab
            self.tabs['console'] = ConsoleTab(self.notebook, self.theme_manager, self)
            self.tabs['console'].add_to_notebook(self.notebook, "💻 Console")
            
            # MOD MANAGEMENT TAB - Add after console
            if self.mod_management_enabled and MODS_TAB_AVAILABLE:
                try:
                    logging.info("Creating ModsTab...")
                    
                    # Create mods tab with detailed debugging
                    self.mods_tab = ModsTab(
                        self.notebook,      # parent
                        self.theme_manager, # theme_manager  
                        self               # main_window (self)
                    )
                    
                    logging.info("ModsTab created successfully, getting frame...")
                    
                    # Get frame safely
                    try:
                        mods_frame = self.mods_tab.get_frame()
                        logging.info(f"Got mods frame: {type(mods_frame)}")
                        
                        if mods_frame:
                            # Add to notebook
                            self.notebook.add(mods_frame, text="🔧 Mods")
                            self.tabs['mods'] = self.mods_tab
                            logging.info("✅ Mods tab added successfully")
                        else:
                            logging.error("❌ Mods frame is None")
                            
                    except Exception as frame_error:
                        logging.error(f"❌ Error getting mods frame: {frame_error}")
                        import traceback
                        traceback.print_exc()
                    
                except Exception as mod_tab_error:
                    logging.error(f"❌ Failed to create mods tab: {mod_tab_error}")
                    import traceback
                    traceback.print_exc()
                    
                    # Safe footer update
                    if hasattr(self, 'footer') and self.footer:
                        try:
                            self.footer.update_status("Mods tab unavailable - check logs for details")
                        except:
                            logging.warning("Could not update footer status")
            else:
                logging.warning(f"⚠️ Mods tab not available (enabled: {self.mod_management_enabled}, available: {MODS_TAB_AVAILABLE})")
                if hasattr(self, 'footer') and self.footer:
                    try:
                        self.footer.update_status("Mods tab disabled - mod management not available")
                    except:
                        logging.warning("Could not update footer status")
            
            # Backup tab
            self.tabs['backup'] = BackupTab(self.notebook, self.theme_manager, self)
            self.tabs['backup'].add_to_notebook(self.notebook, "💾 Backups")
            
            # Health tab
            self.tabs['health'] = HealthTab(self.notebook, self.theme_manager, self)
            self.tabs['health'].add_to_notebook(self.notebook, "❤️ Health")
            
            # Server Properties tab
            self.tabs['properties'] = ServerPropertiesTab(self.notebook, self.theme_manager, self)
            self.tabs['properties'].add_to_notebook(self.notebook, "📝 Properties")
            
            # Settings tab
            self.tabs['settings'] = SettingsTab(self.notebook, self.theme_manager, self)
            self.tabs['settings'].add_to_notebook(self.notebook, "⚙️ Settings")
            
            # Start server log reading thread AFTER console tab is created
            self.log_reading_thread = threading.Thread(target=self.read_server_logs, daemon=True)
            self.log_reading_thread.start()
            logging.info("Log reading thread started")
            
        except Exception as e:
            error_info = self.error_handler.handle_error(e, "create_tabs", ErrorSeverity.MEDIUM)
            messagebox.showerror("Tab Creation Error", f"Failed to create tabs: {error_info['message']}")
    
    # MOD MANAGEMENT CALLBACK METHODS
    def on_mod_operation(self, operation: str, modinfo, message: str):
        """Handle mod operation notifications"""
        try:
            logging.info(f"Mod operation: {operation} - {modinfo.name if modinfo else 'Unknown'}")
            
            if hasattr(self, 'footer') and self.footer:
                if operation == "installed":
                    self.footer.update_status(f"✅ Mod installed: {modinfo.name}")
                elif operation == "removed":
                    self.footer.update_status(f"🗑️ Mod removed: {modinfo.name}")
                elif operation == "enabled":
                    self.footer.update_status(f"✅ Mod enabled: {modinfo.name}")
                elif operation == "disabled":
                    self.footer.update_status(f"⏸️ Mod disabled: {modinfo.name}")
                else:
                    self.footer.update_status(f"🔧 Mod {operation}: {modinfo.name if modinfo else 'Unknown'}")
            
            # Refresh mods tab if it exists
            if hasattr(self, 'mods_tab') and self.mods_tab:
                if hasattr(self.mods_tab, 'refresh_mods'):
                    self.root.after(1000, self.mods_tab.refresh_mods)
                else:
                    print("Mods tab doesn't have refresh_mods method")

                
        except Exception as e:
            logging.error(f"Error handling mod operation callback: {e}")
    
    def on_mod_updates_checked(self, updates_info):
        """Handle mod update check completion"""
        try:
            update_count = len([u for u in updates_info.values() if u.update_status.value == "update_available"])
            
            if update_count > 0:
                if hasattr(self, 'footer') and self.footer:
                    self.footer.update_status(f"📦 {update_count} mod update(s) available")
                
                # Show notification if enabled
                if self.config.get_mod_setting("notification_on_updates", True):
                    messagebox.showinfo(
                        "Mod Updates Available",
                        f"{update_count} mod update(s) are available!\n\nCheck the Mods tab for details."
                    )
            else:
                if hasattr(self, 'footer') and self.footer:
                    self.footer.update_status("✅ All mods are up to date")
                    
        except Exception as e:
            logging.error(f"Error handling mod updates callback: {e}")
    
    def on_mod_download_completed(self, download_task):
        """Handle mod download completion"""
        try:
            if download_task.status.value == "completed":
                if hasattr(self, 'footer') and self.footer:
                    self.footer.update_status(f"📥 Downloaded: {download_task.mod_name}")
                
                # Auto-install if enabled
                if self.config.get_mod_setting("auto_install_after_download", True):
                    self.footer.update_status(f"🔧 Auto-installing: {download_task.mod_name}")
            else:
                if hasattr(self, 'footer') and self.footer:
                    self.footer.update_status(f"❌ Download failed: {download_task.mod_name}")
                    
        except Exception as e:
            logging.error(f"Error handling mod download callback: {e}")
    
    def read_server_logs(self):
        """Read server logs in real-time - WORKING VERSION from old code"""
        logging.info("Starting server log reading thread")
        
        while self.monitoring_active:
            try:
                if not self.monitoring_active:
                    break
                    
                if (self.process_manager.is_server_running() and 
                    self.process_manager.server_process and 
                    self.process_manager.server_process.stdout):
                    
                    line = self.process_manager.server_process.stdout.readline()
                    if line and self.monitoring_active:
                        line = line.strip()
                        if line:  # Only process non-empty lines
                            # Use thread-safe GUI update
                            if self.root and 'console' in self.tabs:
                                self.root.after(0, lambda l=line: self.append_server_log(l))
                    else:
                        time.sleep(0.1)
                else:
                    time.sleep(0.5)
                    
            except Exception as e:
                if self.monitoring_active:
                    logging.error(f"Error reading server logs: {e}")
                time.sleep(1)
        
        logging.info("Log reading thread exited")
    
    def append_server_log(self, text):
        """Append text to server log display with colors - WORKING VERSION"""
        try:
            console_tab = self.tabs.get('console')
            if console_tab and hasattr(console_tab, 'add_console_message'):
                # Determine message type based on content
                text = text.strip()
                if not text:
                    return
                
                # Color coding based on log level
                if '[INFO]' in text or 'INFO' in text:
                    console_tab.add_console_message(text, 'info')
                elif '[WARN]' in text or 'WARN' in text:
                    console_tab.add_console_message(text, 'warning')
                elif '[ERROR]' in text or 'ERROR' in text or 'Exception' in text:
                    console_tab.add_console_message(text, 'error')
                elif text.startswith('>'):
                    console_tab.add_console_message(text, 'command')
                else:
                    console_tab.add_console_message(text, 'normal')
                    
                # Update server status based on log content
                self._update_server_status_from_log(text)
                    
        except Exception as e:
            logging.error(f"Error appending server log: {e}")
    
    def _update_server_status_from_log(self, line: str):
        """Update server status based on log output"""
        try:
            line_lower = line.lower()
            
            if "done" in line_lower and ("for help" in line_lower or "help or tab" in line_lower):
                self.process_manager.server_status['status'] = 'running'
                if hasattr(self, 'header') and self.header:
                    self.header.update_server_status("Running", self.theme_manager.get_current_theme()['success'])
                if hasattr(self, 'footer') and self.footer:
                    self.footer.update_status("Server is ready for players")
                logging.info("Server is now ready for players")
                
                # Switch to console tab to show the "ready" message
                if 'console' in self.tabs:
                    for i in range(self.notebook.index("end")):
                        if self.notebook.tab(i, "text") == "💻 Console":
                            self.notebook.select(i)
                            break
                            
            elif "stopping server" in line_lower or "stopping the server" in line_lower:
                self.process_manager.server_status['status'] = 'stopping'
                if hasattr(self, 'header') and self.header:
                    self.header.update_server_status("Stopping", self.theme_manager.get_current_theme()['warning'])
                if hasattr(self, 'footer') and self.footer:
                    self.footer.update_status("Server is stopping...")
                logging.info("Server is stopping")
                
            elif ("loading" in line_lower and "spawn area" in line_lower) or "preparing spawn area" in line_lower:
                self.process_manager.server_status['status'] = 'loading'
                if hasattr(self, 'header') and self.header:
                    self.header.update_server_status("Loading", self.theme_manager.get_current_theme()['warning'])
                if hasattr(self, 'footer') and self.footer:
                    self.footer.update_status("Server is loading world...")
                    
            elif "joined the game" in line_lower:
                if hasattr(self, 'footer') and self.footer:
                    player_name = line.split()[0] if line.split() else "Player"
                    self.footer.update_status(f"{player_name} joined the game")
                    
            elif "left the game" in line_lower:
                if hasattr(self, 'footer') and self.footer:
                    player_name = line.split()[0] if line.split() else "Player"
                    self.footer.update_status(f"{player_name} left the game")
            
        except Exception as e:
            logging.error(f"Error updating server status: {e}")
    
    def setup_callbacks(self):
        """Setup callbacks and event handlers"""
        # Register cleanup callbacks
        self.memory_manager.register_cleanup_callback(self.cleanup_console_memory)
        
        # Register health callback
        self.health_monitor.register_health_callback(self.on_health_update)
        
        # Register backup callbacks
        self.backup_manager.register_backup_callback(self.on_backup_event)
    
    def start_managers(self):
        """Start all managers"""
        try:
            if self.config.get("memory_optimization_enabled", True):
                self.memory_manager.start_monitoring()
            
            if self.config.get("health_monitoring_enabled", True):
                self.health_monitor.start_monitoring()
            
            self.backup_manager.start_auto_backup()
            self.sleep_manager.start_wake_detection()
            self.auto_shutdown_manager.start_shutdown_monitoring()
            
            logging.info("All managers started successfully")
            
        except Exception as e:
            error_info = self.error_handler.handle_error(e, "start_managers", ErrorSeverity.HIGH)
            messagebox.showerror("Manager Startup Error", f"Failed to start managers: {error_info['message']}")
    
    def on_theme_change(self, event=None):
        """Handle theme change with proper error handling"""
        try:
            new_theme = self.header.theme_var.get()
            self.theme_manager.change_theme(new_theme)
            
            # Update all components safely
            self.apply_theme()
            
            if self.header and hasattr(self.header, 'update_theme'):
                self.header.update_theme()
            
            if self.footer and hasattr(self.footer, 'update_theme'):
                self.footer.update_theme()
            
            # Update all tabs safely (including mods tab)
            for tab_name, tab in self.tabs.items():
                try:
                    if hasattr(tab, 'update_theme'):
                        tab.update_theme()
                except Exception as tab_error:
                    logging.warning(f"Failed to update theme for tab {tab_name}: {tab_error}")
            
            # Update mods tab specifically
            if hasattr(self, 'mods_tab') and self.mods_tab:
                try:
                    if hasattr(self.mods_tab, 'update_theme'):
                        self.mods_tab.update_theme()
                except Exception as mods_theme_error:
                    logging.warning(f"Failed to update theme for mods tab: {mods_theme_error}")
            
            if self.footer:
                self.footer.update_status(f"Theme changed to {new_theme}")
            
        except Exception as e:
            error_info = self.error_handler.handle_error(e, "theme_change", ErrorSeverity.LOW)
            messagebox.showerror("Theme Error", f"Failed to change theme: {error_info['message']}")
    
    # Server control methods
    def start_server(self):
        """Start the server with proper console integration"""
        try:
            if not self.server_jar_path:
                messagebox.showerror("Error", "Please select a server JAR file first")
                return
            
            success = self.process_manager.start_server(self.server_jar_path)
            if success:
                self.footer.update_status("Server started successfully")
                self.header.update_server_status("Starting", self.theme_manager.get_current_theme()['warning'])
                
                # Notify dashboard
                self.notify_dashboard_change()
                
                # Update mod management with server directory
                if self.mod_management_enabled:
                    server_dir = os.path.dirname(self.server_jar_path)
                    self.update_server_directory_for_mods(server_dir)
                
                # Switch to console tab to show output
                if 'console' in self.tabs:
                    for i in range(self.notebook.index("end")):
                        if self.notebook.tab(i, "text") == "💻 Console":
                            self.notebook.select(i)
                            break
                
                # Add startup message to console
                console_tab = self.tabs.get('console')
                if console_tab and hasattr(console_tab, 'add_console_message'):
                    console_tab.add_console_message("=== SERVER STARTING ===", "info")
                    console_tab.add_console_message(f"JAR: {os.path.basename(self.server_jar_path)}", "info")
                    console_tab.add_console_message("Waiting for server output...", "info")
            else:
                self.footer.update_status("Failed to start server")
                
        except Exception as e:
            error_info = self.error_handler.handle_error(e, "start_server", ErrorSeverity.HIGH)
            messagebox.showerror("Server Error", f"Failed to start server: {error_info['message']}")
    
    def stop_server(self):
        """Stop the server"""
        try:
            success = self.process_manager.stop_server()
            if success:
                self.footer.update_status("Server stopped successfully")
                self.header.update_server_status("Stopped", self.theme_manager.get_current_theme()['text_muted'])
                
                # Notify dashboard
                self.notify_dashboard_change()
                
                # Add stop message to console
                console_tab = self.tabs.get('console')
                if console_tab and hasattr(console_tab, 'add_console_message'):
                    console_tab.add_console_message("=== SERVER STOPPED ===", "info")
            else:
                self.footer.update_status("Failed to stop server")
                
        except Exception as e:
            error_info = self.error_handler.handle_error(e, "stop_server", ErrorSeverity.MEDIUM)
            messagebox.showerror("Server Error", f"Failed to stop server: {error_info['message']}")
    
    def restart_server(self):
        """Restart the server"""
        try:
            console_tab = self.tabs.get('console')
            if console_tab and hasattr(console_tab, 'add_console_message'):
                console_tab.add_console_message("=== RESTARTING SERVER ===", "info")
            
            success = self.process_manager.restart_server()
            if success:
                self.footer.update_status("Server restarted successfully")
            else:
                self.footer.update_status("Failed to restart server")
                
        except Exception as e:
            error_info = self.error_handler.handle_error(e, "restart_server", ErrorSeverity.HIGH)
            messagebox.showerror("Server Error", f"Failed to restart server: {error_info['message']}")
    
    def start_playit(self):
        """Start Playit.gg"""
        try:
            if not self.playit_path:
                messagebox.showerror("Error", "Please select Playit.gg executable first")
                return
            
            success = self.process_manager.start_playit(self.playit_path)
            if success:
                self.footer.update_status("Playit.gg started successfully")
                
                # Add message to console
                console_tab = self.tabs.get('console')
                if console_tab and hasattr(console_tab, 'add_console_message'):
                    console_tab.add_console_message("=== PLAYIT.GG STARTED ===", "info")
            else:
                self.footer.update_status("Failed to start Playit.gg")
                
        except Exception as e:
            error_info = self.error_handler.handle_error(e, "start_playit", ErrorSeverity.MEDIUM)
            messagebox.showerror("Playit Error", f"Failed to start Playit.gg: {error_info['message']}")
    
    def stop_playit(self):
        """Stop Playit.gg"""
        try:
            success = self.process_manager.stop_playit()
            if success:
                self.footer.update_status("Playit.gg stopped successfully")
                
                # Add message to console
                console_tab = self.tabs.get('console')
                if console_tab and hasattr(console_tab, 'add_console_message'):
                    console_tab.add_console_message("=== PLAYIT.GG STOPPED ===", "info")
            else:
                self.footer.update_status("Failed to stop Playit.gg")
                
        except Exception as e:
            error_info = self.error_handler.handle_error(e, "stop_playit", ErrorSeverity.MEDIUM)
            messagebox.showerror("Playit Error", f"Failed to stop Playit.gg: {error_info['message']}")
    
    def browse_server_jar(self):
        """Browse for server JAR file with immediate saving"""
        try:
            filename = filedialog.askopenfilename(
                title="Select Minecraft Server JAR",
                filetypes=[("JAR files", "*.jar"), ("All files", "*.*")],
                initialdir=os.getcwd()
            )
            
            if filename:
                # Update main window
                self.server_jar_path = filename
                
                # Save to config IMMEDIATELY
                self.config.set("last_server_jar", filename)
                self.config.save_config()
                
                # Update ALL UI components
                self.update_all_jar_references(filename)
                
                # Update mod management server directory
                if self.mod_management_enabled:
                    server_dir = os.path.dirname(filename)
                    self.update_server_directory_for_mods(server_dir)
                
                # Update footer
                jar_name = os.path.basename(filename)
                self.footer.update_status(f"Server JAR selected: {jar_name}")
                
                logging.info(f"Server JAR path saved: {filename}")
                
                # Auto-load server properties
                self.auto_load_server_properties()
                
                # Notify dashboard of JAR change
                self.notify_dashboard_change()
                
        except Exception as e:
            logging.error(f"Error browsing server JAR: {e}")
            messagebox.showerror("Error", f"Failed to select server JAR: {e}")

    def browse_playit(self):
        """Browse for Playit.gg executable with immediate saving"""
        try:
            filetypes = [("Executable files", "*.exe"), ("All files", "*.*")] if os.name == 'nt' else [("All files", "*.*")]
            
            filename = filedialog.askopenfilename(
                title="Select Playit.gg Executable",
                filetypes=filetypes,
                initialdir=os.getcwd()
            )
            
            if filename:
                # Update main window
                self.playit_path = filename
                
                # Save to config IMMEDIATELY
                self.config.set("last_playit_path", filename)
                self.config.save_config()
                
                # Update ALL UI components
                self.update_all_playit_references(filename)
                
                # Update footer
                playit_name = os.path.basename(filename)
                self.footer.update_status(f"Playit.gg selected: {playit_name}")
                
                logging.info(f"Playit.gg path saved: {filename}")
                
        except Exception as e:
            logging.error(f"Error browsing Playit.gg: {e}")
            messagebox.showerror("Error", f"Failed to select Playit.gg: {e}")

    def update_all_jar_references(self, jar_path):
        """FIXED: Update JAR path in ALL UI components with better validation"""
        try:
            # Update server control tab with validation
            if 'server_control' in self.tabs:
                tab = self.tabs['server_control']
                
                # Check if tab is fully initialized
                if (hasattr(tab, 'server_jar_var') and 
                    hasattr(tab.server_jar_var, 'set')):
                    try:
                        tab.server_jar_var.set(jar_path)
                        logging.info("Updated server control JAR display")
                    except tk.TclError as e:
                        logging.warning(f"UI not ready for JAR update: {e}")
                        # Retry after a delay
                        self.root.after(1000, lambda: self.update_all_jar_references(jar_path))
                        return
                
                # Update main window reference
                if hasattr(tab, 'main_window'):
                    tab.main_window.server_jar_path = jar_path
            
            # Update dashboard if needed
            if 'dashboard' in self.tabs:
                if hasattr(self.tabs['dashboard'], 'update_server_info'):
                    self.tabs['dashboard'].update_server_info()
            
            # Update properties tab if needed
            if 'properties' in self.tabs:
                if hasattr(self.tabs['properties'], 'update_server_path'):
                    self.tabs['properties'].update_server_path()
                    
            logging.info("All JAR references updated successfully")
            
        except Exception as e:
            logging.error(f"Error updating JAR references: {e}")
            # Retry once after delay
            self.root.after(2000, lambda: self.update_all_jar_references(jar_path))

    def update_all_playit_references(self, playit_path):
        """FIXED: Update Playit.gg path in ALL UI components with better validation"""
        try:
            # Update server control tab
            if 'server_control' in self.tabs:
                tab = self.tabs['server_control']
                
                if (hasattr(tab, 'playit_var') and 
                    hasattr(tab.playit_var, 'set')):
                    try:
                        tab.playit_var.set(playit_path)
                        logging.info("Updated server control Playit.gg display")
                    except tk.TclError as e:
                        logging.warning(f"UI not ready for Playit.gg update: {e}")
                        # Retry after a delay
                        self.root.after(1000, lambda: self.update_all_playit_references(playit_path))
                        return
                
                if hasattr(tab, 'main_window'):
                    tab.main_window.playit_path = playit_path
            
            logging.info("All Playit.gg references updated successfully")
            
        except Exception as e:
            logging.error(f"Error updating Playit.gg references: {e}")
            # Retry once after delay
            self.root.after(2000, lambda: self.update_all_playit_references(playit_path))

    def send_command(self, event=None):
        """Send command to server - WORKING VERSION"""
        try:
            console_tab = self.tabs.get('console')
            if console_tab and console_tab.command_entry:
                command = console_tab.command_entry.get().strip()
                if command and self.process_manager.is_server_running():
                    success = self.process_manager.send_server_command(command)
                    if success:
                        console_tab.command_entry.delete(0, tk.END)
                        # Add command to console display
                        console_tab.add_console_message(f"> {command}", "command")
                            
        except Exception as e:
            error_info = self.error_handler.handle_error(e, "send_command", ErrorSeverity.MEDIUM)
            messagebox.showerror("Command Error", f"Failed to send command: {error_info['message']}")
    
    # Placeholder methods for missing functionality
    def create_manual_backup(self):
        """Create manual backup"""
        self.footer.update_status("Creating backup...")
        try:
            if hasattr(self, 'backup_manager') and self.server_jar_path:
                server_dir = os.path.dirname(self.server_jar_path)
                self.backup_manager.create_backup(server_dir, backup_type='manual')
                self.footer.update_status("Backup created successfully")
            else:
                self.footer.update_status("No server directory available for backup")
        except Exception as e:
            self.footer.update_status("Backup failed")
            error_info = self.error_handler.handle_error(e, "create_manual_backup", ErrorSeverity.MEDIUM)
            messagebox.showerror("Backup Error", f"Failed to create backup: {error_info['message']}")
    
    def run_system_check(self):
        """Run system check"""
        self.footer.update_status("Running system check...")
        # Add actual system check logic here
        self.footer.update_status("System check completed")
    
    # Callback methods
    def on_health_update(self, health_status):
        """Handle health status updates"""
        pass
    
    def on_backup_event(self, event_type, data):
        """Handle backup events"""
        pass
    
    def cleanup_console_memory(self):
        """Clean up console memory"""
        pass
    
    def load_saved_paths(self):
        """FIXED: Load saved file paths and update ALL UI components with better validation"""
        
        self.debug_jar_persistence()
        try:
            # Load JAR path
            last_jar = self.config.get("last_server_jar", "")
            if last_jar and os.path.exists(last_jar):
                self.server_jar_path = last_jar
                self.update_all_jar_references(last_jar)
                
                # Update mod management server directory
                if self.mod_management_enabled:
                    server_dir = os.path.dirname(last_jar)
                    self.update_server_directory_for_mods(server_dir)
                
                logging.info(f"Loaded and applied server JAR path: {last_jar}")
                
                # Auto-load properties on startup too
                self.root.after(2000, self.auto_load_server_properties)  # 2 second delay for startup
                
            elif last_jar:
                # Path exists in config but file is missing
                logging.warning(f"Saved JAR path no longer exists: {last_jar}")
                self.config.set("last_server_jar", "")  # Clear invalid path
                self.config.save_config()
            
            # Load Playit.gg path
            last_playit = self.config.get("last_playit_path", "")
            if last_playit and os.path.exists(last_playit):
                self.playit_path = last_playit
                self.update_all_playit_references(last_playit)
                logging.info(f"Loaded and applied Playit.gg path: {last_playit}")
            elif last_playit:
                # Path exists in config but file is missing
                logging.warning(f"Saved Playit.gg path no longer exists: {last_playit}")
                self.config.set("last_playit_path", "")  # Clear invalid path
                self.config.save_config()
            
            # Force UI update after loading
            self.root.after(100, self.force_ui_update)
            
        except Exception as e:
            logging.error(f"Error loading saved paths: {e}")
    
    def force_ui_update(self):
        """Force update all UI components with current paths"""
        try:
            if hasattr(self, 'server_jar_path') and self.server_jar_path:
                self.update_all_jar_references(self.server_jar_path)
            
            if hasattr(self, 'playit_path') and self.playit_path:
                self.update_all_playit_references(self.playit_path)
                
            logging.info("UI force update completed")
            
        except Exception as e:
            logging.error(f"Error in force UI update: {e}")
    
    def on_closing(self):
        """Handle window closing"""
        if messagebox.askokcancel("Quit", "Do you want to quit? This will stop all running processes."):
            self.cleanup_and_exit()
    
    def cleanup_and_exit(self):
        """Clean up and exit - INCLUDING MOD MANAGEMENT"""
        try:
            logging.info("Shutting down...")
            
            # Stop monitoring FIRST
            self.monitoring_active = False
            
            # Wait for log reading thread to finish
            if self.log_reading_thread and self.log_reading_thread.is_alive():
                self.log_reading_thread.join(timeout=2)
            
            # Stop all managers
            self.memory_manager.stop_monitoring()
            self.health_monitor.stop_monitoring()
            self.backup_manager.stop_auto_backup()
            self.sleep_manager.stop_wake_detection()
            self.auto_shutdown_manager.stop_shutdown_monitoring()
            
            # Stop MOD MANAGEMENT components
            if self.mod_management_enabled:
                try:
                    if self.moddownloader:
                        self.moddownloader.shutdown()
                    
                    # Save mod management data
                    if self.modmanager:
                        self.modmanager.save_database()
                    if self.modbackupmanager:
                        self.modbackupmanager.savebackupindex()
                    if self.modupdatechecker:
                        self.modupdatechecker.save_update_cache()
                    if self.modconfigmanager:
                        self.modconfigmanager.save_config_database()
                    
                    logging.info("Mod management components shut down successfully")
                except Exception as mod_cleanup_error:
                    logging.error(f"Error shutting down mod management: {mod_cleanup_error}")
            
            # Stop all processes
            self.process_manager.stop_all_processes()
            
            logging.info("Cleanup completed")
            
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")
        
        finally:
            self.root.quit()
            self.root.destroy()
    
    def run(self):
        """Run the GUI application"""
        try:
            self.root.mainloop()
        except Exception as e:
            error_info = self.error_handler.handle_error(e, "gui_main_loop", ErrorSeverity.CRITICAL)
            logging.critical(f"Critical error in main loop: {error_info}")
            raise

    def _simple_setup_fallback(self):
        """Simple setup fallback when wizard fails"""
        try:
            result = messagebox.askyesno(
                "🛠️ Simple Setup",
                "Let's set up your server with a simple process.\n\n"
                "Do you have a Minecraft server JAR file ready?"
            )
            
            if result:
                filename = filedialog.askopenfilename(
                    title="Select Minecraft Server JAR",
                    filetypes=[("JAR files", "*.jar"), ("All files", "*.*")],
                    initialdir=os.getcwd()
                )
                
                if filename:
                    # Quick setup
                    self.server_jar_path = filename
                    self.config.set("last_server_jar", filename)
                    self.config.set("setup_wizard_completed", True)
                    self.config.save_config()
                    
                    # Update UI
                    if 'server_control' in self.tabs:
                        self.tabs['server_control'].server_jar_var.set(filename)
                    
                    # Update mod management
                    if self.mod_management_enabled:
                        server_dir = os.path.dirname(filename)
                        self.update_server_directory_for_mods(server_dir)
                    
                    messagebox.showinfo(
                        "✅ Setup Complete",
                        f"Server JAR selected: {os.path.basename(filename)}\n\n"
                        "Your server is ready! Go to Server Control tab to start it."
                    )
                    
                    # Go to server control
                    for i in range(self.notebook.index("end")):
                        if "Control" in self.notebook.tab(i, "text"):
                            self.notebook.select(i)
                            break
            else:
                messagebox.showinfo(
                    "Download JAR",
                    "Download a Minecraft server JAR from:\n"
                    "• minecraft.net/download/server\n"
                    "• papermc.io/downloads\n"
                    "Then try setup again!"
                )
                
        except Exception as e:
            logging.error(f"Simple setup fallback error: {e}")
            messagebox.showerror("Setup Error", f"Setup failed: {e}")
            
    def check_first_time_setup(self):
        """Check if this is a first-time setup and offer wizard"""
        try:
            # Check if welcome dialog has already been shown
            if self.config.get("welcome_dialog_shown", False):
                return  # Exit early if welcome was already shown
            
            # Check multiple indicators of first-time setup
            needs_setup = False
            
            # Check 1: No server JAR configured
            if not self.server_jar_path:
                needs_setup = True
            
            # Check 2: Configured JAR doesn't exist
            elif not os.path.exists(self.server_jar_path):
                needs_setup = True
            
            # Check 3: No world folder in server directory
            elif self.server_jar_path:
                server_dir = os.path.dirname(self.server_jar_path)
                world_exists = any(
                    os.path.exists(os.path.join(server_dir, world_name))
                    for world_name in ['world', 'world_nether', 'world_the_end']
                )
                if not world_exists:
                    needs_setup = True
            
            # Check 4: Never run setup wizard before
            if not self.config.get("setup_wizard_completed", False):
                needs_setup = True
            
            # If setup is needed, show welcome dialog
            if needs_setup:
                self.root.after(1000, self.show_first_time_welcome)  # Delay to let UI load
                
        except Exception as e:
            logging.error(f"Error checking first-time setup: {e}")
    
    def show_first_time_welcome(self):
        """Show improved first-time welcome with PROPER SIZING"""
        theme = self.theme_manager.get_current_theme()
        
        # Create welcome dialog with LARGER SIZE
        welcome = tk.Toplevel(self.root)
        welcome.title("🎮 Welcome to Minecraft Server Manager")
        welcome.geometry("700x600")  # Increased from 600x500
        welcome.transient(self.root)
        welcome.grab_set()
        welcome.resizable(True, True)  # Make it resizable for debugging
        
        # Center the window
        welcome.update_idletasks()
        x = (welcome.winfo_screenwidth() // 2) - (700 // 2)
        y = (welcome.winfo_screenheight() // 2) - (600 // 2)
        welcome.geometry(f"700x600+{x}+{y}")
        
        welcome.configure(bg=theme['bg_primary'])
        
        # Create scrollable content area
        main_canvas = tk.Canvas(welcome, bg=theme['bg_primary'], highlightthickness=0)
        scrollbar = tk.Scrollbar(welcome, orient="vertical", command=main_canvas.yview)
        scrollable_frame = tk.Frame(main_canvas, bg=theme['bg_primary'])
        
        # Configure scrolling
        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Main content with proper padding
        content_frame = tk.Frame(scrollable_frame, bg=theme['bg_primary'])
        content_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Welcome header
        header_frame = tk.Frame(content_frame, bg=theme['bg_primary'])
        header_frame.pack(fill="x", pady=(0, 20))
        
        # Large welcome title
        welcome_title = tk.Label(
            header_frame,
            text="🎮 Welcome!",
            bg=theme['bg_primary'],
            fg=theme['accent'],
            font=('Segoe UI', 20, 'bold')  # Reduced font size
        )
        welcome_title.pack()
        
        # Friendly subtitle
        welcome_subtitle = tk.Label(
            header_frame,
            text="Let's get your Minecraft server up and running",
            bg=theme['bg_primary'],
            fg=theme['text_primary'],
            font=('Segoe UI', 11)
        )
        welcome_subtitle.pack(pady=(5, 0))
        
        # MOD MANAGEMENT STATUS - NEW SECTION
        if self.mod_management_enabled:
            mod_status_frame = tk.Frame(content_frame, bg=theme['success'], relief='solid', bd=1)
            mod_status_frame.pack(fill="x", pady=(0, 10))
            
            mod_status_content = tk.Frame(mod_status_frame, bg=theme['success'])
            mod_status_content.pack(padx=10, pady=5)
            
            mod_status_label = tk.Label(
                mod_status_content,
                text="🔧 Mod Management: ENABLED - Full mod support available!",
                bg=theme['success'],
                fg='white',
                font=('Segoe UI', 9, 'bold')
            )
            mod_status_label.pack()
        
        # Status message
        status_frame = tk.Frame(content_frame, bg=theme['bg_card'], relief='solid', bd=1)
        status_frame.pack(fill="x", pady=(0, 20))
        
        status_content = tk.Frame(status_frame, bg=theme['bg_card'])
        status_content.pack(padx=15, pady=10)  # Reduced padding
        
        # Check server status (simplified)
        has_server = (hasattr(self, 'server_jar_path') and 
                      self.server_jar_path and 
                      os.path.exists(self.server_jar_path))
        
        if has_server:
            status_msg = "🎯 Server detected! Ready to manage your server."
            status_color = theme['success']
            action_type = "manage"
        else:
            status_msg = "🚀 No server detected. Let's create your first server!"
            status_color = theme['info']
            action_type = "create"
        
        status_label = tk.Label(
            status_content,
            text=status_msg,
            bg=theme['bg_card'],
            fg=status_color,
            font=('Segoe UI', 10, 'bold')
        )
        status_label.pack()
        
        # Main action section
        action_frame = tk.Frame(content_frame, bg=theme['bg_primary'])
        action_frame.pack(fill="x", pady=(0, 20))
        
        if action_type == "create":
            # First-time server creation
            action_title = tk.Label(
                action_frame,
                text="🧙‍♂️ Create Your First Server",
                bg=theme['bg_primary'],
                fg=theme['text_primary'],
                font=('Segoe UI', 14, 'bold')
            )
            action_title.pack(pady=(0, 10))
            
            action_desc = tk.Label(
                action_frame,
                text="Our setup will guide you through creating a new Minecraft server.\n\n"
                     "What you'll need: A Minecraft server JAR file\n"
                     "Time needed: About 5 minutes\n\n"
                     "We'll help you configure settings and generate your world!",
                bg=theme['bg_primary'],
                fg=theme['text_secondary'],
                font=('Segoe UI', 9),
                justify='left'
            )
            action_desc.pack(pady=(0, 15))
            
            # Add mod management info if available
            if self.mod_management_enabled:
                mod_info = tk.Label(
                    action_frame,
                    text="🔧 BONUS: Full mod management is available!\n"
                         "Install mods, manage dependencies, check for updates, and more!",
                    bg=theme['bg_primary'],
                    fg=theme['accent'],
                    font=('Segoe UI', 9, 'italic'),
                    justify='left'
                )
                mod_info.pack(pady=(5, 0))
            
        else:  # manage existing
            action_title = tk.Label(
                action_frame,
                text="🎮 Server Ready!",
                bg=theme['bg_primary'],
                fg=theme['text_primary'],
                font=('Segoe UI', 14, 'bold')
            )
            action_title.pack(pady=(0, 10))
            
            action_desc = tk.Label(
                action_frame,
                text="Your server is ready to use!\n\n"
                     "You can start your server, configure settings,\n"
                     "monitor performance, and create backups.",
                bg=theme['bg_primary'],
                fg=theme['text_secondary'],
                font=('Segoe UI', 9),
                justify='left'
            )
            action_desc.pack(pady=(0, 15))
            
            # Add mod management info if available
            if self.mod_management_enabled:
                mod_info = tk.Label(
                    action_frame,
                    text="🔧 PLUS: Use the Mods tab to install and manage mods!\n"
                         "Browse online repositories, auto-update, and more!",
                    bg=theme['bg_primary'],
                    fg=theme['accent'],
                    font=('Segoe UI', 9, 'italic'),
                    justify='left'
                )
                mod_info.pack(pady=(5, 0))
        
        # BUTTONS SECTION - Fixed layout
        buttons_frame = tk.Frame(content_frame, bg=theme['bg_primary'])
        buttons_frame.pack(fill="x", pady=10)
        
        if action_type == "create":
            # Setup Wizard button (primary)
            setup_btn = tk.Button(
                buttons_frame,
                text="🚀 Start Setup Wizard",
                command=lambda: self.start_setup_from_welcome(welcome),
                bg=theme['accent'],
                fg='white',
                font=('Segoe UI', 11, 'bold'),
                padx=20,
                pady=8,
                cursor='hand2',
                relief='flat'
            )
            setup_btn.pack(pady=(0, 10))
            
            # Quick Setup button (secondary)
            quick_btn = tk.Button(
                buttons_frame,
                text="⚡ Quick Setup (Browse for JAR)",
                command=lambda: self.quick_setup_from_welcome(welcome),
                bg=theme['bg_card'],
                fg=theme['text_primary'],
                font=('Segoe UI', 10),
                padx=15,
                pady=6,
                cursor='hand2',
                relief='flat'
            )
            quick_btn.pack(pady=(0, 5))
        
        else:  # manage existing
            # Go to Server Control button
            control_btn = tk.Button(
                buttons_frame,
                text="🎮 Go to Server Control",
                command=lambda: self.go_to_server_control_from_welcome(welcome),
                bg=theme['accent'],
                fg='white',
                font=('Segoe UI', 11, 'bold'),
                padx=20,
                pady=8,
                cursor='hand2',
                relief='flat'
            )
            control_btn.pack(pady=(0, 10))
            
            # Go to Mods tab button (if available)
            if self.mod_management_enabled:
                mods_btn = tk.Button(
                    buttons_frame,
                    text="🔧 Manage Mods",
                    command=lambda: self.go_to_mods_tab_from_welcome(welcome),
                    bg=theme['success'],
                    fg='white',
                    font=('Segoe UI', 10),
                    padx=15,
                    pady=6,
                    cursor='hand2',
                    relief='flat'
                )
                mods_btn.pack(pady=(0, 5))
        
        # Skip button (always available)
        skip_btn = tk.Button(
            buttons_frame,
            text="Skip and explore on my own",
            command=lambda: self.skip_welcome(welcome),
            bg=theme['bg_primary'],
            fg=theme['text_muted'],
            font=('Segoe UI', 9),
            pady=5,
            cursor='hand2',
            relief='flat',
            bd=0
        )
        skip_btn.pack(pady=5)
        
        # Feature highlights section
        features_frame = tk.Frame(content_frame, bg=theme['bg_primary'])
        features_frame.pack(fill="x", pady=(20, 0))
        
        features_title = tk.Label(
            features_frame,
            text="✨ What's Included",
            bg=theme['bg_primary'],
            fg=theme['text_primary'],
            font=('Segoe UI', 12, 'bold')
        )
        features_title.pack(pady=(0, 10))
        
        # Features list with better layout
        features_list = [
            "🎮 Easy server control (start, stop, restart)",
            "💻 Live console with command input",
            "💾 Automatic and manual backups",
            "❤️ Server health monitoring",
            "⚙️ Server properties management",
            "🎨 Multiple themes (dark, light, blue)"
        ]
        
        # Add mod management features if available
        if self.mod_management_enabled:
            features_list.extend([
                "🔧 Complete mod management system",
                "📦 Install mods from online repositories", 
                "🔄 Automatic mod updates",
                "🔗 Smart dependency resolution",
                "⚙️ Mod configuration editing"
            ])
        
        for feature in features_list:
            feature_label = tk.Label(
                features_frame,
                text=feature,
                bg=theme['bg_primary'],
                fg=theme['text_secondary'],
                font=('Segoe UI', 9),
                anchor='w'
            )
            feature_label.pack(anchor='w', pady=1)
        
        # Bind mouse wheel scrolling
        def bind_mousewheel(widget):
            widget.bind("<MouseWheel>", lambda e: main_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
            for child in widget.winfo_children():
                bind_mousewheel(child)
        
        bind_mousewheel(scrollable_frame)
        
        # Set focus to window
        welcome.focus_set()
        
        # Mark welcome as shown
        self.config.set("welcome_dialog_shown", True)
        self.config.save_config()
    
    def start_setup_from_welcome(self, welcome_window):
        """Start setup wizard from welcome dialog"""
        try:
            welcome_window.destroy()
            self._simple_setup_fallback()  # Use simple setup for now
        except Exception as e:
            logging.error(f"Error starting setup from welcome: {e}")
    
    def quick_setup_from_welcome(self, welcome_window):
        """Quick setup from welcome dialog"""
        try:
            welcome_window.destroy()
            self.browse_server_jar()
            if self.server_jar_path:
                self.config.set("setup_wizard_completed", True)
                self.config.save_config()
                messagebox.showinfo(
                    "Setup Complete",
                    "Quick setup completed! Your server is ready to start."
                )
        except Exception as e:
            logging.error(f"Error in quick setup: {e}")
    
    def go_to_server_control_from_welcome(self, welcome_window):
        """Go to server control tab from welcome"""
        try:
            welcome_window.destroy()
            # Find and select server control tab
            for i in range(self.notebook.index("end")):
                if "Control" in self.notebook.tab(i, "text"):
                    self.notebook.select(i)
                    break
        except Exception as e:
            logging.error(f"Error going to server control: {e}")
    
    def go_to_mods_tab_from_welcome(self, welcome_window):
        """Go to mods tab from welcome"""
        try:
            welcome_window.destroy()
            # Find and select mods tab
            for i in range(self.notebook.index("end")):
                if "Mods" in self.notebook.tab(i, "text"):
                    self.notebook.select(i)
                    break
        except Exception as e:
            logging.error(f"Error going to mods tab: {e}")
    
    def skip_welcome(self, welcome_window):
        """Skip welcome dialog"""
        try:
            welcome_window.destroy()
            self.config.set("setup_wizard_completed", True)
            self.config.save_config()
        except Exception as e:
            logging.error(f"Error skipping welcome: {e}")
            
    def auto_load_server_properties(self):
        """Automatically load server properties after JAR selection"""
        try:
            # Check if properties tab exists and is initialized
            if 'properties' in self.tabs:
                properties_tab = self.tabs['properties']
                
                # Give the UI a moment to update, then load properties
                self.root.after(500, self._delayed_properties_load)
                
            else:
                logging.warning("Properties tab not available for auto-loading")
                
        except Exception as e:
            logging.error(f"Error in auto-load server properties: {e}")

    def _delayed_properties_load(self):
        """Delayed properties loading to ensure UI is ready"""
        try:
            if 'properties' in self.tabs:
                properties_tab = self.tabs['properties']
                
                # Check if the tab has the load_properties method
                if hasattr(properties_tab, 'load_properties'):
                    
                    # Call the load_properties method
                    properties_tab.load_properties()
                    
                    # Update footer with success message
                    if hasattr(self, 'footer') and self.footer:
                        self.footer.update_status("✅ Server properties loaded automatically")
                    
                    logging.info("✅ Server properties auto-loaded successfully")
                    
                else:
                    logging.warning("Properties tab doesn't have load_properties method")
                    
        except Exception as e:
            # Don't show error dialogs for auto-loading - just log
            logging.warning(f"Could not auto-load server properties: {e}")
            
            if hasattr(self, 'footer') and self.footer:
                self.footer.update_status("⚠️ Could not auto-load properties - load manually if needed")
    
    def debug_jar_persistence(self):
        """Debug JAR file persistence issues"""
        print("🔍 JAR PERSISTENCE DEBUG")
        
        try:
            # Check current state
            print(f"Current server_jar_path: {getattr(self, 'server_jar_path', 'NOT SET')}")
            
            # Check config value
            config_jar = self.config.get("last_server_jar", "")
            print(f"Config last_server_jar: '{config_jar}'")
            
            # Check if config file exists
            config_file = self.config.config_file
            print(f"Config file: {config_file}")
            print(f"Config file exists: {os.path.exists(config_file)}")
            
            # Check file validation
            if config_jar:
                print(f"Config JAR file exists: {os.path.exists(config_jar)}")
                try:
                    validated_path = self.config.validate_file_path(config_jar)
                    print(f"Validated path: '{validated_path}'")
                except Exception as validation_error:
                    print(f"Validation error: {validation_error}")
            
            # Check setup wizard status
            setup_completed = self.config.get("setup_wizard_completed", False)
            welcome_shown = self.config.get("welcome_dialog_shown", False)
            print(f"Setup wizard completed: {setup_completed}")
            print(f"Welcome dialog shown: {welcome_shown}")
            
        except Exception as e:
            print(f"Debug error: {e}")
    
    def notify_dashboard_change(self):
        """Notify dashboard of state changes"""
        try:
            if hasattr(self, 'tabs') and 'dashboard' in self.tabs:
                dashboard_tab = self.tabs['dashboard']
                if hasattr(dashboard_tab, 'refresh_from_external_change'):
                    # Schedule refresh on main thread
                    self.root.after(100, dashboard_tab.refresh_from_external_change)
                    print("🔄 Notified dashboard of state change")
        except Exception as e:
            print(f"❌ Error notifying dashboard: {e}")

def run_gui():
    """Run the enhanced Minecraft Server Manager GUI with mod management"""
    try:
        # Set up logging for GUI
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('minecraft_server_manager.log'),
                logging.StreamHandler()
            ]
        )
        
        logging.info("Starting Enhanced Minecraft Server Manager with Mod Management...")
        
        # Create and run GUI
        app = MinecraftServerGUI()
        app.run()
        
    except Exception as e:
        logging.critical(f"Critical error starting GUI: {e}")
        import traceback
        traceback.print_exc()
        
        # Show error dialog if possible
        try:
            import tkinter.messagebox as msgbox
            msgbox.showerror(
                "Critical Error", 
                f"Failed to start Minecraft Server Manager:\n\n{str(e)}\n\nCheck the log file for details."
            )
        except:
            print(f"CRITICAL ERROR: {e}")
            




        



