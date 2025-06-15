"""
Main window for the Minecraft Server Manager GUI - With Working Console Capture
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


class MinecraftServerGUI:
    """Main GUI application for Minecraft Server Manager with Working Console Capture"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} v{VERSION}")
        
        # Set professional window size and make it responsive
        self.setup_window_properties()
        
        # Initialize core components
        self.error_handler = ErrorHandler()
        self.config = Config()
        self.server_properties_manager = ServerPropertiesManager(self.error_handler)
        
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
        
        # Load saved paths and start managers
        self.load_saved_paths()
        self.start_managers()
        
         # Check for first-time setup AFTER everything is loaded
        self.root.after(2000, self.check_first_time_setup)  # 2 second delay
        
        # Setup window protocol
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        logging.info("Enhanced Minecraft Server Manager initialized")
        
        
    
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
        """Create all tabs with professional styling"""
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
            
            # Update all tabs safely
            for tab_name, tab in self.tabs.items():
                try:
                    if hasattr(tab, 'update_theme'):
                        tab.update_theme()
                except Exception as tab_error:
                    logging.warning(f"Failed to update theme for tab {tab_name}: {tab_error}")
            
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
        """Browse for server JAR file and save the path"""
        try:
            logging.info("Opening server JAR file dialog...")
            
            # Get initial directory - try last used directory first
            initial_dir = os.getcwd()
            last_jar = self.config.get("last_server_jar", "")
            if last_jar and os.path.exists(os.path.dirname(last_jar)):
                initial_dir = os.path.dirname(last_jar)
            
            filename = filedialog.askopenfilename(
                title="Select Minecraft Server JAR",
                filetypes=[
                    ("JAR files", "*.jar"),
                    ("All files", "*.*")
                ],
                initialdir=initial_dir
            )
            
            if filename:
                logging.info(f"User selected file: {filename}")
                
                # Validate the file exists
                if not os.path.exists(filename):
                    messagebox.showerror("Error", f"Selected file does not exist: {filename}")
                    return
                
                # Validate it's a JAR file
                if not filename.lower().endswith('.jar'):
                    if not messagebox.askyesno("Warning", 
                        f"Selected file doesn't have .jar extension: {os.path.basename(filename)}\n\nContinue anyway?"):
                        return
                
                # Set the path
                self.server_jar_path = filename
                logging.info(f"Server JAR path set to: {self.server_jar_path}")
                
                # Save to config immediately
                try:
                    self.config.set("last_server_jar", filename)
                    save_success = self.config.save_config()
                    if save_success:
                        logging.info("Server JAR path saved to config")
                    else:
                        logging.warning("Failed to save server JAR path to config")
                except Exception as save_error:
                    logging.error(f"Error saving config: {save_error}")
                
                # Update server control tab UI
                try:
                    if 'server_control' in self.tabs:
                        server_control_tab = self.tabs['server_control']
                        if hasattr(server_control_tab, 'server_jar_var'):
                            server_control_tab.server_jar_var.set(filename)
                            logging.info("Updated server control tab display")
                        else:
                            logging.warning("Server control tab doesn't have server_jar_var")
                    else:
                        logging.warning("Server control tab not found")
                except Exception as ui_error:
                    logging.error(f"Error updating UI: {ui_error}")
                
                # Update footer
                try:
                    if hasattr(self, 'footer') and self.footer:
                        self.footer.update_status(f"Selected: {os.path.basename(filename)}")
                    else:
                        logging.warning("Footer not available")
                except Exception as footer_error:
                    logging.error(f"Error updating footer: {footer_error}")
                
                logging.info("Server JAR selection completed successfully")
            else:
                logging.info("User cancelled file selection")
                
        except Exception as e:
            error_msg = f"Failed to select server JAR file: {str(e)}"
            logging.error(error_msg)
            logging.error(f"Exception details: {type(e).__name__}: {e}")
            
            # Show error to user
            messagebox.showerror("File Selection Error", error_msg)
            
            # Update status
            if hasattr(self, 'footer') and self.footer:
                self.footer.update_status("Failed to select server JAR")

    def browse_playit(self):
        """Browse for Playit.gg executable and save the path"""
        try:
            logging.info("Opening Playit.gg file dialog...")
            
            # Get initial directory
            initial_dir = os.getcwd()
            last_playit = self.config.get("last_playit_path", "")
            if last_playit and os.path.exists(os.path.dirname(last_playit)):
                initial_dir = os.path.dirname(last_playit)
            
            # Different file types based on OS
            if os.name == 'nt':  # Windows
                filetypes = [
                    ("Executable files", "*.exe"),
                    ("All files", "*.*")
                ]
            else:  # Unix/Linux/macOS
                filetypes = [
                    ("All files", "*.*"),
                    ("Executable files", "*")
                ]
            
            filename = filedialog.askopenfilename(
                title="Select Playit.gg Executable",
                filetypes=filetypes,
                initialdir=initial_dir
            )
            
            if filename:
                logging.info(f"User selected Playit.gg file: {filename}")
                
                # Validate the file exists
                if not os.path.exists(filename):
                    messagebox.showerror("Error", f"Selected file does not exist: {filename}")
                    return
                
                # Set the path
                self.playit_path = filename
                logging.info(f"Playit.gg path set to: {self.playit_path}")
                
                # Save to config immediately
                try:
                    self.config.set("last_playit_path", filename)
                    save_success = self.config.save_config()
                    if save_success:
                        logging.info("Playit.gg path saved to config")
                    else:
                        logging.warning("Failed to save Playit.gg path to config")
                except Exception as save_error:
                    logging.error(f"Error saving config: {save_error}")
                
                # Update server control tab UI
                try:
                    if 'server_control' in self.tabs:
                        server_control_tab = self.tabs['server_control']
                        if hasattr(server_control_tab, 'playit_var'):
                            server_control_tab.playit_var.set(filename)
                            logging.info("Updated server control tab Playit.gg display")
                        else:
                            logging.warning("Server control tab doesn't have playit_var")
                    else:
                        logging.warning("Server control tab not found")
                except Exception as ui_error:
                    logging.error(f"Error updating Playit.gg UI: {ui_error}")
                
                # Update footer
                try:
                    if hasattr(self, 'footer') and self.footer:
                        self.footer.update_status(f"Selected: {os.path.basename(filename)}")
                    else:
                        logging.warning("Footer not available")
                except Exception as footer_error:
                    logging.error(f"Error updating footer: {footer_error}")
                
                logging.info("Playit.gg selection completed successfully")
            else:
                logging.info("User cancelled Playit.gg file selection")
                
        except Exception as e:
            error_msg = f"Failed to select Playit.gg file: {str(e)}"
            logging.error(error_msg)
            logging.error(f"Exception details: {type(e).__name__}: {e}")
            
            # Show error to user
            messagebox.showerror("File Selection Error", error_msg)
            
            # Update status
            if hasattr(self, 'footer') and self.footer:
                self.footer.update_status("Failed to select Playit.gg")

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
        """Load previously saved file paths and update UI"""
        try:
            # Load server JAR path
            last_jar = self.config.get("last_server_jar", "")
            if last_jar and os.path.exists(last_jar):
                self.server_jar_path = last_jar
                # Update server control tab if it exists
                if 'server_control' in self.tabs:
                    self.tabs['server_control'].server_jar_var.set(last_jar)
                logging.info(f"Loaded saved server JAR: {last_jar}")
            
            # Load Playit.gg path
            last_playit = self.config.get("last_playit_path", "")
            if last_playit and os.path.exists(last_playit):
                self.playit_path = last_playit
                # Update server control tab if it exists
                if 'server_control' in self.tabs:
                    self.tabs['server_control'].playit_var.set(last_playit)
                logging.info(f"Loaded saved Playit.gg: {last_playit}")
                
        except Exception as e:
            self.error_handler.handle_error(e, "load_saved_paths", ErrorSeverity.LOW)
    
    def on_closing(self):
        """Handle window closing"""
        if messagebox.askokcancel("Quit", "Do you want to quit? This will stop all running processes."):
            self.cleanup_and_exit()
    
    def cleanup_and_exit(self):
        """Clean up and exit"""
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
                font=('Segoe UI', 12, 'bold'),
                padx=30,
                pady=12,
                relief='flat',
                cursor='hand2'
            )
            setup_btn.pack(pady=5)
            
            # Manual setup button
            manual_btn = tk.Button(
                buttons_frame,
                text="📁 Browse for Existing Server",
                command=lambda: self.start_manual_from_welcome(welcome),
                bg=theme['bg_tertiary'],
                fg=theme['text_primary'],
                font=('Segoe UI', 10),
                padx=25,
                pady=8,
                relief='flat',
                cursor='hand2'
            )
            manual_btn.pack(pady=5)
            
        else:  # existing server
            # Go to server control button
            control_btn = tk.Button(
                buttons_frame,
                text="🎮 Go to Server Control",
                command=lambda: self.go_to_server_control(welcome),
                bg=theme['success'],
                fg='white',
                font=('Segoe UI', 12, 'bold'),
                padx=30,
                pady=12,
                relief='flat',
                cursor='hand2'
            )
            control_btn.pack(pady=5)
        
        # Skip section (at bottom)
        skip_frame = tk.Frame(content_frame, bg=theme['bg_primary'])
        skip_frame.pack(fill="x", pady=(20, 10))
        
        skip_btn = tk.Button(
            skip_frame,
            text="Skip for now",
            command=lambda: self.skip_welcome(welcome),
            bg=theme['bg_primary'],
            fg=theme['text_muted'],
            font=('Segoe UI', 8),
            relief='flat',
            cursor='hand2',
            bd=0
        )
        skip_btn.pack()
        
        # Bind mousewheel to canvas for scrolling
        def _on_mousewheel(event):
            main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        welcome.bind("<MouseWheel>", _on_mousewheel)
        
        # Prevent closing without action
        welcome.protocol("WM_DELETE_WINDOW", lambda: self.skip_welcome(welcome))
        
        # Force update to ensure everything is visible
        welcome.update_idletasks()
        main_canvas.update_idletasks()


    def start_setup_from_welcome(self, welcome_dialog):
        """Start setup wizard from improved welcome - WITH ERROR HANDLING"""
        try:
            logging.info("Starting setup wizard from welcome dialog")
            welcome_dialog.destroy()
            
            # Small delay to ensure dialog closes properly
            self.root.after(100, self._show_setup_wizard_delayed)
            
        except Exception as e:
            logging.error(f"Error starting setup from welcome: {e}")
            welcome_dialog.destroy()
            messagebox.showerror("Error", f"Could not start setup wizard: {e}")

    def _show_setup_wizard_delayed(self):
        """Show setup wizard with delay - prevents timing issues"""
        try:
            self.show_setup_wizard()
        except Exception as e:
            logging.error(f"Error showing setup wizard: {e}")
            messagebox.showerror("Setup Wizard Error", f"Failed to open setup wizard: {e}")
            # Fallback - go to server control tab
            self._fallback_to_server_control()

    def show_setup_wizard(self):
        """Show the server setup wizard with improved debugging"""
        try:
            # Debug first
            print("Attempting to import setup wizard...")
            
            # Try the import
            from .dialogs.setup_wizard import ServerSetupWizard
            
            print("Import successful, creating wizard...")
            
            # Store wizard reference in case we need to access it later
            self.current_wizard = ServerSetupWizard(self.root, self.theme_manager, self)
            print("Setup wizard created successfully")
            
        except ImportError as ie:
            print(f"Import error: {ie}")
            logging.error(f"Setup wizard import error: {ie}")
            
            # Show detailed error to user
            error_msg = (
                f"Setup wizard import failed: {ie}\n\n"
                f"This usually means:\n"
                f"• Missing gui/dialogs/__init__.py file\n"
                f"• setup_wizard.py has syntax errors\n"
                f"• Wrong folder structure\n\n"
                f"Would you like to use simple setup instead?"
            )
            
            result = messagebox.askyesno("Import Error", error_msg)
            if result:
                self._simple_setup_fallback()
                
        except Exception as e:
            print(f"Other error: {e}")
            logging.error(f"Setup wizard error: {e}")
            messagebox.showerror("Setup Wizard Error", f"Failed to open setup wizard: {e}")
            self._simple_setup_fallback()

    def _fallback_to_server_control(self):
        """Fallback method to go to server control tab"""
        try:
            # Switch to server control tab
            for i in range(self.notebook.index("end")):
                tab_text = self.notebook.tab(i, "text")
                if "Server Control" in tab_text or "🎮" in tab_text:
                    self.notebook.select(i)
                    break
            
            self.footer.update_status("Setup wizard not available - use manual setup in Server Control tab")
            
            # Show helpful instructions
            messagebox.showinfo(
                "Manual Setup Instructions",
                "📋 To set up your server manually:\n\n"
                "1. Click 'Browse' next to 'Server JAR'\n"
                "2. Select your Minecraft server JAR file\n"
                "3. Configure any settings you want\n"
                "4. Click 'Start Server'\n\n"
                "The server will create worlds automatically on first run!"
            )
            
        except Exception as e:
            logging.error(f"Fallback error: {e}")
            self.footer.update_status("Please use the Server Control tab to set up your server")

    def start_manual_from_welcome(self, welcome_dialog):
        """Start manual setup from welcome - FIXED VERSION"""
        try:
            logging.info("Starting manual setup from welcome")
            welcome_dialog.destroy()
            
            # Go to server control tab
            self._fallback_to_server_control()
            
        except Exception as e:
            logging.error(f"Error starting manual setup: {e}")
            try:
                welcome_dialog.destroy()
            except:
                pass
            messagebox.showerror("Error", f"Could not start manual setup: {e}")

    def go_to_server_control(self, welcome_dialog):
        """Go directly to server control for ready servers - FIXED VERSION"""
        try:
            logging.info("Going to server control from welcome")
            welcome_dialog.destroy()
            
            # Switch to server control tab
            for i in range(self.notebook.index("end")):
                tab_text = self.notebook.tab(i, "text")
                if "Server Control" in tab_text or "🎮" in tab_text:
                    self.notebook.select(i)
                    break
            
            self.footer.update_status("Your server is ready! Click 'Start Server' to begin.")
            
        except Exception as e:
            logging.error(f"Error going to server control: {e}")
            try:
                welcome_dialog.destroy()
            except:
                pass
            messagebox.showerror("Error", f"Could not open server control: {e}")

    def skip_welcome(self, welcome_dialog):
        """Skip welcome with confirmation - FIXED VERSION"""
        try:
            # Ask for confirmation
            response = messagebox.askyesno(
                "Skip Setup", 
                "Are you sure you want to skip the welcome setup?\n\n"
                "You can always access setup options from the Server Control tab."
            )
            
            if response:
                logging.info("User skipped welcome setup")
                welcome_dialog.destroy()
                self.footer.update_status("Welcome skipped - access setup from Server Control tab when ready")
            # If they say no, just stay on the welcome dialog
            
        except Exception as e:
            logging.error(f"Error skipping welcome: {e}")
            # Force close the dialog anyway
            try:
                welcome_dialog.destroy()
            except:
                pass
            self.footer.update_status("Welcome closed - use Server Control tab for setup")
            
    def debug_setup_wizard(self):
        """Debug setup wizard import issues"""
        import os
        import sys
        
        print("=== SETUP WIZARD DEBUG ===")
        
        # Check current directory
        current_dir = os.path.dirname(__file__)
        print(f"Current directory: {current_dir}")
        
        # Check for dialogs folder
        dialogs_dir = os.path.join(current_dir, 'dialogs')
        print(f"Dialogs folder exists: {os.path.exists(dialogs_dir)}")
        
        if os.path.exists(dialogs_dir):
            print(f"Files in dialogs: {os.listdir(dialogs_dir)}")
            
            # Check for specific files
            init_file = os.path.join(dialogs_dir, '__init__.py')
            wizard_file = os.path.join(dialogs_dir, 'setup_wizard.py')
            
            print(f"__init__.py exists: {os.path.exists(init_file)}")
            print(f"setup_wizard.py exists: {os.path.exists(wizard_file)}")
            
            # Check file contents briefly
            if os.path.exists(wizard_file):
                try:
                    with open(wizard_file, 'r') as f:
                        first_lines = f.readlines()[:5]
                    print("First few lines of setup_wizard.py:")
                    for line in first_lines:
                        print(f"  {line.strip()}")
                except Exception as e:
                    print(f"Error reading setup_wizard.py: {e}")
        
        # Try the import and see what happens
        print("\nTrying import...")
        try:
            from .dialogs.setup_wizard import ServerSetupWizard
            print("✅ Import successful!")
            return True
        except ImportError as e:
            print(f"❌ Import error: {e}")
            return False
        except Exception as e:
            print(f"❌ Other error: {e}")
            return False

    # Call this method to debug
    # self.debug_setup_wizard()




