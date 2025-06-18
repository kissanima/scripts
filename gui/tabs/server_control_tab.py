"""
Server control tab implementation with improved visible tooltip
"""

import tkinter as tk
from tkinter import messagebox
import os
import logging
from .base_tab import BaseTab
from ..components.status_card import StatusCard
from ..components.modern_widgets import ModernButton, ModernEntry

class ImprovedToolTip:
    """Enhanced tooltip with better visibility and positioning"""
    
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)
    
    def on_enter(self, event=None):
        """Show tooltip with better visibility"""
        if self.tooltip:
            return
        
        # Get better positioning - always on top and visible
        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + 30
        
        # Make sure tooltip appears on screen
        screen_width = self.widget.winfo_screenwidth()
        screen_height = self.widget.winfo_screenheight()
        
        # Adjust if tooltip would go off screen
        if x + 350 > screen_width:
            x = screen_width - 370
        if y + 200 > screen_height:
            y = y - 250
        
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_attributes("-topmost", True)  # Always on top
        
        # Make tooltip more visible with better styling
        frame = tk.Frame(
            self.tooltip, 
            bg="#1a1a1a", 
            relief="solid", 
            bd=2,
            highlightbackground="#007acc",
            highlightthickness=2  # Thicker border
        )
        frame.pack()
        
        # Add shadow effect by creating a slightly offset background
        shadow_frame = tk.Frame(
            self.tooltip,
            bg="#000000",
            relief="flat"
        )
        
        # Header with icon
        header = tk.Frame(frame, bg="#007acc", height=30)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        header_content = tk.Frame(header, bg="#007acc")
        header_content.pack(expand=True)
        
        tk.Label(
            header_content,
            text="🌐 Playit.gg Information",
            bg="#007acc",
            fg="white",
            font=("Segoe UI", 11, "bold")
        ).pack(pady=6)
        
        # Content with larger, more readable text
        content_frame = tk.Frame(frame, bg="#2d2d30")
        content_frame.pack(fill="both", padx=15, pady=15)
        
        # Make text larger and more readable
        content_text = """Playit.gg is a free tunneling service that allows your Minecraft server to be accessible from anywhere in the world.

🔧 How it works:
• Port forwards your server through their network
• Provides a public IP address that players can use
• Works with servers that have online-mode=false
• Allows cracked clients to connect (since online=false only works on LAN normally)

⚡ Benefits:
• No router configuration needed
• No port forwarding setup required
• Free to use
• Works behind firewalls and NAT
• Perfect for servers with online-mode=false

💡 Click for more detailed information"""
        
        text_label = tk.Label(
            content_frame,
            text=content_text,
            bg="#2d2d30",
            fg="#ffffff",
            font=("Segoe UI", 10),  # Larger font
            wraplength=320,
            justify="left",
            anchor="nw"
        )
        text_label.pack()
        
        # Position tooltip
        self.tooltip.geometry(f"+{x}+{y}")
        
        # Ensure it appears
        self.tooltip.update_idletasks()
        self.tooltip.lift()  # Bring to front
    
    def on_leave(self, event=None):
        """Hide tooltip"""
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

class ServerControlTab(BaseTab):
    """Server control tab with improved tooltip visibility"""
    
    def __init__(self, parent, theme_manager, main_window):
        self.main_window = main_window
        super().__init__(parent, theme_manager)
        self.server_jar_var = tk.StringVar()
        self.playit_var = tk.StringVar()
        self.auto_start_playit_var = tk.BooleanVar()
        self.jar_status = None
        self.playit_status = None
        self.create_content()
    
    def create_content(self):
        """Create server control content with improved tooltip"""
        theme = self.theme_manager.get_current_theme()
        
        content = tk.Frame(self.tab_frame, bg=theme['bg_primary'])
        content.pack(fill="both", expand=True, padx=theme['padding_large'], pady=theme['padding_large'])
        
        # File selection card
        file_card = StatusCard(content, "File Selection", "📁", self.theme_manager)
        file_card.pack(fill="x", pady=(0, theme['margin_large']))
        
        file_content = file_card.get_content_frame()
        
        # File paths container
        paths_frame = tk.Frame(file_content, bg=theme['bg_card'])
        paths_frame.pack(fill="x", padx=theme['padding_medium'], pady=theme['padding_medium'])
        
        # Server JAR selection
        jar_frame = tk.Frame(paths_frame, bg=theme['bg_card'])
        jar_frame.pack(fill="x", pady=(0, theme['margin_medium']))
        
        jar_label = tk.Label(jar_frame, text="Server JAR:", bg=theme['bg_card'], 
                            fg=theme['text_primary'], width=12, anchor="w",
                            font=('Segoe UI', theme['font_size_normal'], 'bold'))
        jar_label.pack(side="left")
        
        jar_entry = ModernEntry(jar_frame, self.theme_manager, textvariable=self.server_jar_var)
        jar_entry.pack(side="left", fill="x", expand=True, padx=(theme['padding_small'], theme['padding_small']))
        
        jar_browse_btn = ModernButton(jar_frame, "Browse", self.browse_server_jar, "secondary", self.theme_manager, "normal")
        jar_browse_btn.pack(side="right")
        
        # Status indicator for JAR
        self.jar_status = tk.Label(jar_frame, text="", bg=theme['bg_card'], 
                                  fg=theme['text_muted'], width=3)
        self.jar_status.pack(side="right", padx=(theme['padding_small'], 0))
        
        # Playit.gg selection with IMPROVED info button
        playit_frame = tk.Frame(paths_frame, bg=theme['bg_card'])
        playit_frame.pack(fill="x")
        
        # Playit.gg label with improved info button
        playit_header = tk.Frame(playit_frame, bg=theme['bg_card'])
        playit_header.pack(fill="x", pady=(0, theme['margin_small']))
        
        playit_label = tk.Label(playit_header, text="Playit.gg:", bg=theme['bg_card'], 
                               fg=theme['text_primary'], width=12, anchor="w",
                               font=('Segoe UI', theme['font_size_normal'], 'bold'))
        playit_label.pack(side="left")
        
        # IMPROVED info button - larger and more visible
        info_btn = tk.Button(
            playit_header, 
            text="ℹ️ Info", 
            bg=theme['accent'], 
            fg="white",
            font=('Segoe UI', 10, 'bold'),
            cursor="hand2", 
            relief="raised", 
            bd=2, 
            padx=8, 
            pady=2,
            activebackground=theme['accent_hover'],
            command=self.show_playit_info_dialog
        )
        info_btn.pack(side="left", padx=(10, 0))
        
        # Add IMPROVED tooltip to info button
        ImprovedToolTip(info_btn, "Hover for quick info, click for detailed explanation")
        
        # Playit.gg file selection
        playit_input_frame = tk.Frame(playit_frame, bg=theme['bg_card'])
        playit_input_frame.pack(fill="x")
        
        playit_entry = ModernEntry(playit_input_frame, self.theme_manager, textvariable=self.playit_var)
        playit_entry.pack(side="left", fill="x", expand=True, padx=(0, theme['padding_small']))
        
        playit_browse_btn = ModernButton(playit_input_frame, "Browse", self.browse_playit, "secondary", self.theme_manager, "normal")
        playit_browse_btn.pack(side="right")
        
        # Status indicator for Playit
        self.playit_status = tk.Label(playit_input_frame, text="", bg=theme['bg_card'], 
                                     fg=theme['text_muted'], width=3)
        self.playit_status.pack(side="right", padx=(theme['padding_small'], 0))
        
        # Auto-start Playit.gg checkbox with tooltip
        auto_start_frame = tk.Frame(paths_frame, bg=theme['bg_card'])
        auto_start_frame.pack(fill="x", pady=(theme['margin_small'], 0))
        
        auto_start_check = tk.Checkbutton(
            auto_start_frame,
            text="🚀 Auto-start Playit.gg when server starts",
            variable=self.auto_start_playit_var,
            bg=theme['bg_card'],
            fg=theme['text_primary'],
            selectcolor=theme['input_bg'],
            activebackground=theme['bg_card'],
            activeforeground=theme['text_primary'],
            font=('Segoe UI', theme['font_size_normal']),
            command=self.on_auto_start_changed
        )
        auto_start_check.pack(anchor="w", padx=(120, 0))
        
        # Add tooltip to checkbox
        ImprovedToolTip(auto_start_check, "When enabled, Playit.gg will automatically start 3 seconds after the server starts")
        
        # Server control card
        control_card = StatusCard(content, "Server Control", "🎮", self.theme_manager)
        control_card.pack(fill="x", pady=(0, theme['margin_large']))
        
        control_content = control_card.get_content_frame()
        
        # Control buttons
        control_buttons = tk.Frame(control_content, bg=theme['bg_card'])
        control_buttons.pack(padx=theme['padding_medium'], pady=theme['padding_medium'])
        
        # Main control buttons
        main_buttons = tk.Frame(control_buttons, bg=theme['bg_card'])
        main_buttons.pack(pady=(0, theme['margin_small']))
        
        ModernButton(main_buttons, "🚀 Start Server", self.start_server, "success", self.theme_manager, "normal").pack(side="left", padx=(0, theme['margin_small']))
        ModernButton(main_buttons, "🛑 Stop Server", self.stop_server, "danger", self.theme_manager, "normal").pack(side="left", padx=(0, theme['margin_small']))
        ModernButton(main_buttons, "🔄 Restart Server", self.restart_server, "primary", self.theme_manager, "normal").pack(side="left")
        
        # Additional buttons
        extra_buttons = tk.Frame(control_buttons, bg=theme['bg_card'])
        extra_buttons.pack()
        
        ModernButton(extra_buttons, "🔧 Test Java", self.test_java, "secondary", self.theme_manager, "small").pack(side="left", padx=(0, theme['margin_small']))
        ModernButton(extra_buttons, "📊 Check Status", self.check_server_status, "secondary", self.theme_manager, "small").pack(side="left")
        
        # Playit.gg control card
        playit_card = StatusCard(content, "Playit.gg Control", "🌐", self.theme_manager)
        playit_card.pack(fill="x")
        
        playit_content = playit_card.get_content_frame()
        
        # Playit.gg description
        playit_desc_frame = tk.Frame(playit_content, bg=theme['bg_card'])
        playit_desc_frame.pack(fill="x", padx=theme['padding_medium'], pady=(theme['padding_medium'], theme['margin_small']))
        
        playit_desc = tk.Label(
            playit_desc_frame,
            text="🌍 Playit.gg makes your server accessible worldwide • Perfect for online-mode=false servers • No port forwarding needed",
            bg=theme['bg_card'],
            fg=theme['text_secondary'],
            font=('Segoe UI', theme['font_size_small']),
            wraplength=600,
            justify="left"
        )
        playit_desc.pack(anchor="w")
        
        # Playit.gg buttons
        playit_buttons = tk.Frame(playit_content, bg=theme['bg_card'])
        playit_buttons.pack(padx=theme['padding_medium'], pady=(0, theme['padding_medium']))
        
        self.start_playit_btn = ModernButton(playit_buttons, "🌍 Start Playit.gg", self.start_playit, "primary", self.theme_manager, "normal")
        self.start_playit_btn.pack(side="left", padx=(0, theme['margin_small']))
        
        self.stop_playit_btn = ModernButton(playit_buttons, "⏹️ Stop Playit.gg", self.stop_playit, "secondary", self.theme_manager, "normal")
        self.stop_playit_btn.pack(side="left", padx=(0, theme['margin_small']))
        
        ModernButton(playit_buttons, "📋 Get Server Info", self.get_playit_info, "secondary", self.theme_manager, "small").pack(side="left")
        
        setup_buttons = tk.Frame(control_buttons, bg=theme['bg_card'])
        setup_buttons.pack(pady=(theme['margin_small'], 0))

        ModernButton(setup_buttons, "🧙‍♂️ Setup New Server", self.open_setup_wizard, "primary", self.theme_manager, "normal").pack(side="left")
        
        # Register components
        self.register_widget(file_card)
        self.register_widget(control_card)
        self.register_widget(playit_card)
        
        # Bind validation
        self.server_jar_var.trace('w', self.validate_server_jar)
        self.playit_var.trace('w', self.validate_playit_path)
        
        # Load saved paths and settings
        self.load_saved_paths()
        self.update_playit_button_states()
    
    def show_playit_info_dialog(self, event=None):
        """Show detailed Playit.gg information in a dialog"""
        info_text = """🌐 What is Playit.gg?

Playit.gg is a free tunneling service that allows your Minecraft server to be accessible from anywhere in the world.

🔧 How it works:
• Port forwards your server through their network
• Provides a public IP address that players can use
• Works with servers that have online-mode=false
• Allows cracked clients to connect (since online=false only works on LAN normally)

⚡ Benefits:
• No router configuration needed
• No port forwarding setup required
• Free to use
• Works behind firewalls and NAT
• Perfect for servers with online-mode=false

📋 Setup Instructions:
1. Download Playit.gg from playit.gg/download
2. Select the executable in the field above
3. Start your Minecraft server
4. Start Playit.gg (automatically or manually)
5. Follow the Playit.gg setup wizard
6. Share the provided IP with your friends

💡 Pro Tips:
• Set online-mode=false in server.properties for cracked clients
• Keep the Playit.gg window open while playing
• The service is completely free with no limitations"""
        
        # Show the info in a messagebox for simplicity
        messagebox.showinfo("Playit.gg Information", info_text)
    
    # Keep all the existing methods (load_saved_paths, start_server, etc.)
    def load_saved_paths(self):
        """Load saved file paths and settings into the UI"""
        try:
            # Load server JAR path
            last_jar = self.main_window.config.get("last_server_jar", "")
            if last_jar:
                self.server_jar_var.set(last_jar)
                self.main_window.server_jar_path = last_jar
                logging.info(f"Loaded server JAR path: {last_jar}")
            
            # Load Playit.gg path
            last_playit = self.main_window.config.get("last_playit_path", "")
            if last_playit:
                self.playit_var.set(last_playit)
                self.main_window.playit_path = last_playit
                logging.info(f"Loaded Playit.gg path: {last_playit}")
            
            # Load auto-start setting
            auto_start = self.main_window.config.get("auto_start_playit_with_server", False)
            self.auto_start_playit_var.set(auto_start)
            logging.info(f"Loaded auto-start Playit.gg setting: {auto_start}")
                
        except Exception as e:
            logging.error(f"Error loading saved paths: {e}")
    
    def on_auto_start_changed(self):
        """Handle auto-start checkbox change"""
        try:
            auto_start = self.auto_start_playit_var.get()
            self.main_window.config.set("auto_start_playit_with_server", auto_start)
            self.main_window.config.save_config()
            logging.info(f"Auto-start Playit.gg setting changed to: {auto_start}")
        except Exception as e:
            logging.error(f"Error saving auto-start setting: {e}")
    
    def start_server(self):
        """Start the server and optionally Playit.gg"""
        try:
            # Start the server first
            self.main_window.start_server()
            
            # Check if we should auto-start Playit.gg
            if (self.auto_start_playit_var.get() and 
                self.main_window.playit_path and 
                os.path.exists(self.main_window.playit_path)):
                
                # Wait a moment for server to start, then start Playit.gg
                self.main_window.root.after(3000, self.auto_start_playit)  # 3 second delay
                
        except Exception as e:
            logging.error(f"Error starting server: {e}")
            messagebox.showerror("Error", f"Failed to start server: {e}")
    
    def auto_start_playit(self):
        """Auto-start Playit.gg after server starts with better error handling"""
        try:
            # Double-check server is still running
            if not self.main_window.process_manager.is_server_running():
                logging.warning("Server not running, skipping Playit.gg auto-start")
                return
            
            # Check if Playit.gg is already running
            if self.main_window.process_manager.is_playit_running():
                logging.info("Playit.gg already running, skipping auto-start")
                return
            
            # Validate Playit.gg path again
            if not self.main_window.playit_path or not os.path.exists(self.main_window.playit_path):
                logging.error("Playit.gg path invalid, cannot auto-start")
                self.main_window.footer.update_status("Auto-start failed: Playit.gg path not found")
                return
            
            # Attempt to start Playit.gg
            success = self.main_window.start_playit()
            
            if success:
                self.main_window.footer.update_status("Server and Playit.gg started successfully")
                logging.info("Playit.gg auto-started successfully")
                
                # Add console message
                console_tab = self.main_window.tabs.get('console')
                if console_tab and hasattr(console_tab, 'add_console_message'):
                    console_tab.add_console_message("🌍 Playit.gg auto-started with server", "info")
            else:
                # Auto-start failed, offer retry
                self.main_window.footer.update_status("Playit.gg auto-start failed - check console for details")
                logging.error("Playit.gg auto-start failed")
                
                # Optional: Retry once after 5 seconds
                self.main_window.root.after(5000, self._retry_auto_start)
                
        except Exception as e:
            logging.error(f"Error in auto_start_playit: {e}")
            self.main_window.footer.update_status("Playit.gg auto-start error")

    def _retry_auto_start(self):
        """Retry auto-start once if it failed"""
        try:
            if (self.main_window.process_manager.is_server_running() and 
                not self.main_window.process_manager.is_playit_running()):
                
                logging.info("Retrying Playit.gg auto-start...")
                success = self.main_window.start_playit()
                
                if success:
                    self.main_window.footer.update_status("Playit.gg started successfully (retry)")
                    console_tab = self.main_window.tabs.get('console')
                    if console_tab and hasattr(console_tab, 'add_console_message'):
                        console_tab.add_console_message("🌍 Playit.gg started (retry)", "info")
                else:
                    logging.error("Playit.gg auto-start retry also failed")
                    
        except Exception as e:
            logging.error(f"Error in retry auto-start: {e}")

    
    def browse_server_jar(self):
        """Browse for server JAR file"""
        try:
            logging.info("Server control tab: Browse server JAR clicked")
            # Call main window method which handles saving
            self.main_window.browse_server_jar()
            
            # Additional validation and UI update
            if hasattr(self.main_window, 'server_jar_path') and self.main_window.server_jar_path:
                self.server_jar_var.set(self.main_window.server_jar_path)
                logging.info("Server control tab JAR path updated")
                
        except Exception as e:
            logging.error(f"Error browsing server JAR: {e}")
            messagebox.showerror("Error", f"Failed to browse for server JAR: {e}")

    def browse_playit(self):
        """Browse for Playit.gg executable"""
        try:
            logging.info("Server control tab: Browse Playit.gg clicked")
            # Call main window method which handles saving
            self.main_window.browse_playit()
            
            # Additional validation and UI update
            if hasattr(self.main_window, 'playit_path') and self.main_window.playit_path:
                self.playit_var.set(self.main_window.playit_path)
                logging.info("Server control tab Playit.gg path updated")
                
        except Exception as e:
            logging.error(f"Error browsing Playit.gg: {e}")
            messagebox.showerror("Error", f"Failed to browse for Playit.gg: {e}")

    
    def browse_playit(self):
        """Browse for Playit.gg executable"""
        try:
            logging.info("Server control tab: Browse Playit.gg clicked")
            self.main_window.browse_playit()
        except Exception as e:
            logging.error(f"Error browsing Playit.gg: {e}")
            messagebox.showerror("Error", f"Failed to browse for Playit.gg: {e}")
    
    def stop_server(self):
        """Stop the server"""
        try:
            self.main_window.stop_server()
        except Exception as e:
            logging.error(f"Error stopping server: {e}")
            messagebox.showerror("Error", f"Failed to stop server: {e}")
    
    def restart_server(self):
        """Restart the server"""
        try:
            self.main_window.restart_server()
        except Exception as e:
            logging.error(f"Error restarting server: {e}")
            messagebox.showerror("Error", f"Failed to restart server: {e}")
    
    def start_playit(self):
        """Start Playit.gg"""
        try:
            success = self.main_window.start_playit()
            if success:
                self.update_playit_button_states()
            return success
        except Exception as e:
            logging.error(f"Error starting Playit.gg: {e}")
            messagebox.showerror("Error", f"Failed to start Playit.gg: {e}")
            return False
    
    def stop_playit(self):
        """Stop Playit.gg"""
        try:
            success = self.main_window.stop_playit()
            if success:
                self.update_playit_button_states()
            return success
        except Exception as e:
            logging.error(f"Error stopping Playit.gg: {e}")
            messagebox.showerror("Error", f"Failed to stop Playit.gg: {e}")
            return False
    
    def get_playit_info(self):
        """Show Playit.gg information and status"""
        self.show_playit_info_dialog()
    
    def update_playit_button_states(self):
        """Update Playit.gg button states"""
        try:
            is_running = self.main_window.process_manager.is_playit_running()
            has_playit = bool(self.main_window.playit_path)
            
            if hasattr(self, 'start_playit_btn'):
                if is_running or not has_playit:
                    self.start_playit_btn.configure(state=tk.DISABLED)
                else:
                    self.start_playit_btn.configure(state=tk.NORMAL)
            
            if hasattr(self, 'stop_playit_btn'):
                if is_running:
                    self.stop_playit_btn.configure(state=tk.NORMAL)
                else:
                    self.stop_playit_btn.configure(state=tk.DISABLED)
                    
        except Exception as e:
            logging.error(f"Error updating Playit.gg button states: {e}")
    
    def validate_server_jar(self, *args):
        """Validate server JAR path"""
        try:
            path = self.server_jar_var.get()
            if path and os.path.exists(path) and path.endswith('.jar'):
                self.jar_status.configure(text="✓", fg=self.theme_manager.get_current_theme()['success'])
                self.main_window.server_jar_path = path
            elif path:
                self.jar_status.configure(text="✗", fg=self.theme_manager.get_current_theme()['error'])
            else:
                self.jar_status.configure(text="")
        except Exception as e:
            logging.error(f"Error validating server JAR: {e}")
    
    def validate_playit_path(self, *args):
        """Validate Playit.gg path"""
        try:
            path = self.playit_var.get()
            if path and os.path.exists(path):
                if os.name == 'nt' and path.endswith('.exe'):
                    self.playit_status.configure(text="✓", fg=self.theme_manager.get_current_theme()['success'])
                    self.main_window.playit_path = path
                elif os.name != 'nt':  # Unix/Linux/macOS
                    self.playit_status.configure(text="✓", fg=self.theme_manager.get_current_theme()['success'])
                    self.main_window.playit_path = path
                else:
                    self.playit_status.configure(text="✗", fg=self.theme_manager.get_current_theme()['error'])
            elif path:
                self.playit_status.configure(text="✗", fg=self.theme_manager.get_current_theme()['error'])
            else:
                self.playit_status.configure(text="")
            
            # Update button states when path changes
            self.update_playit_button_states()
        except Exception as e:
            logging.error(f"Error validating Playit.gg path: {e}")
    
    def test_java(self):
        """Test Java installation"""
        try:
            import subprocess
            java_path = self.main_window.config.get("java_path", "java")
            
            result = subprocess.run([java_path, "-version"], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                version_info = result.stderr or result.stdout
                messagebox.showinfo("Java Test", f"Java is working!\n\n{version_info}")
            else:
                messagebox.showerror("Java Test Failed", f"Java test failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            messagebox.showerror("Java Test Failed", "Java test timed out")
        except FileNotFoundError:
            messagebox.showerror("Java Test Failed", f"Java not found at: {java_path}")
        except Exception as e:
            messagebox.showerror("Java Test Failed", f"Java test failed: {e}")
    
    def check_server_status(self):
        """Check current server status"""
        try:
            if hasattr(self.main_window, 'process_manager'):
                is_running = self.main_window.process_manager.is_server_running()
                is_playit_running = self.main_window.process_manager.is_playit_running()
                server_status = self.main_window.process_manager.get_server_status()
                
                status_text = f"🖥️ Server Status: {'🟢 Running' if is_running else '🔴 Stopped'}\n"
                status_text += f"🌐 Playit.gg Status: {'🟢 Running' if is_playit_running else '🔴 Stopped'}\n"
                
                if is_running and server_status:
                    if server_status.get('pid'):
                        status_text += f"📍 Server PID: {server_status['pid']}\n"
                    if server_status.get('memory'):
                        status_text += f"💾 Memory: {server_status['memory']:.1f} MB\n"
                    if server_status.get('uptime'):
                        uptime = server_status['uptime']
                        hours = int(uptime // 3600)
                        minutes = int((uptime % 3600) // 60)
                        status_text += f"⏱️ Uptime: {hours}h {minutes}m"
                
                if self.auto_start_playit_var.get():
                    status_text += f"\n🚀 Auto-start Playit.gg: Enabled"
                
                messagebox.showinfo("Server Status", status_text)
            else:
                messagebox.showinfo("Server Status", "Process manager not available")
                
        except Exception as e:
            logging.error(f"Error checking server status: {e}")
            messagebox.showerror("Error", f"Failed to check server status: {e}")
    
    def update_theme(self):
        """Update tab theme"""
        super().update_theme()
        
        # Update status indicators
        theme = self.theme_manager.get_current_theme()
        if self.jar_status:
            current_text = self.jar_status.cget('text')
            if current_text == "✓":
                self.jar_status.configure(fg=theme['success'])
            elif current_text == "✗":
                self.jar_status.configure(fg=theme['error'])
            else:
                self.jar_status.configure(fg=theme['text_muted'])
        
        if self.playit_status:
            current_text = self.playit_status.cget('text')
            if current_text == "✓":
                self.playit_status.configure(fg=theme['success'])
            elif current_text == "✗":
                self.playit_status.configure(fg=theme['error'])
            else:
                self.playit_status.configure(fg=theme['text_muted'])
                
    def open_setup_wizard(self):
        """Open the server setup wizard"""
        self.main_window.show_setup_wizard()
