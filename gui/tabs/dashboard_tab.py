"""
Dashboard tab implementation with colored status and progress bar values
"""

import tkinter as tk
import threading
import time
import os
from datetime import datetime, timedelta
from .base_tab import BaseTab
from ..components.status_card import StatusCard
from ..components.modern_widgets import ModernProgressBar, ModernButton

class EnhancedProgressBar(tk.Frame):
    """Progress bar with text value inside"""
    
    def __init__(self, parent, width=200, height=20, theme_manager=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.width = width
        self.height = height
        self.theme_manager = theme_manager
        self.progress = 0
        self.max_value = 100
        self.text = "0%"
        
        self.setup_progress_bar()
    
    def setup_progress_bar(self):
        """Setup progress bar with text overlay"""
        if self.theme_manager:
            theme = self.theme_manager.get_current_theme()
        else:
            from themes import get_theme
            theme = get_theme('dark')
        
        # Configure frame
        self.configure(
            bg=theme['bg_tertiary'],
            height=self.height,
            width=self.width,
            relief='solid',
            bd=1,
            highlightthickness=1,
            highlightbackground=theme['border']
        )
        self.pack_propagate(False)
        
        # Create canvas for progress bar and text
        self.canvas = tk.Canvas(
            self,
            width=self.width-2,
            height=self.height-2,
            bg=theme['bg_tertiary'],
            highlightthickness=0,
            bd=0
        )
        self.canvas.pack(fill="both", expand=True, padx=1, pady=1)
        
        # Create progress rectangle
        self.progress_rect = self.canvas.create_rectangle(
            0, 0, 0, self.height-2,
            fill=theme['accent'],
            outline=""
        )
        
        # Create text overlay
        self.text_item = self.canvas.create_text(
            (self.width-2) // 2, (self.height-2) // 2,
            text=self.text,
            fill=theme['text_primary'],
            font=('Segoe UI', 9, 'bold')
        )
    
    def set_progress(self, value, max_value=100, text=None):
        """Set progress value and optional text"""
        self.progress = max(0, min(value, max_value))
        self.max_value = max_value
        
        if text is not None:
            self.text = text
        else:
            self.text = f"{value:.1f}%"
        
        self.update_display()
    
    def update_display(self):
        """Update progress bar display"""
        if self.max_value > 0:
            progress_width = int((self.progress / self.max_value) * (self.width - 2))
            self.canvas.coords(self.progress_rect, 0, 0, progress_width, self.height-2)
        else:
            self.canvas.coords(self.progress_rect, 0, 0, 0, self.height-2)
        
        # Update text
        self.canvas.itemconfig(self.text_item, text=self.text)
    
    def update_theme(self):
        """Update progress bar theme"""
        if self.theme_manager:
            theme = self.theme_manager.get_current_theme()
            self.configure(bg=theme['bg_tertiary'], highlightbackground=theme['border'])
            self.canvas.configure(bg=theme['bg_tertiary'])
            self.canvas.itemconfig(self.progress_rect, fill=theme['accent'])
            self.canvas.itemconfig(self.text_item, fill=theme['text_primary'])

class DashboardTab(BaseTab):
    """Dashboard tab with colored status and enhanced progress bars"""
    
    def __init__(self, parent, theme_manager, main_window):
        self.main_window = main_window
        super().__init__(parent, theme_manager)
        
        # Dashboard widgets
        self.server_status_text = None
        self.memory_progress = None
        self.cpu_progress = None
        self.uptime_label = None
        self.players_label = None
        
        # Update tracking
        self.update_active = True
        self.last_update = 0
        
        self.create_content()
        self.start_dashboard_updates()
    
    def create_content(self):
        """Create dashboard content with colored status and enhanced progress bars"""
        theme = self.theme_manager.get_current_theme()
        
        # Content with padding
        content = tk.Frame(self.tab_frame, bg=theme['bg_primary'])
        content.pack(fill="both", expand=True, padx=theme['padding_large'], pady=theme['padding_large'])
        
        # Configure grid
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(0, weight=1)
        content.grid_rowconfigure(1, weight=0)
        
        # Top row - Status and Performance
        top_row = tk.Frame(content, bg=theme['bg_primary'])
        top_row.grid(row=0, column=0, columnspan=2, sticky="nsew", pady=(0, theme['margin_medium']))
        top_row.grid_columnconfigure(0, weight=1)
        top_row.grid_columnconfigure(1, weight=1)
        
        # Server status card with colored text
        server_card = StatusCard(top_row, "Server Status", "🖥️", self.theme_manager)
        server_card.card_frame.grid(row=0, column=0, sticky="nsew", padx=(0, theme['margin_small']))
        
        server_content = server_card.get_content_frame()
        
        # Colored text widget
        self.server_status_text = tk.Text(
            server_content,
            height=8,
            bg=theme['bg_card'],
            fg=theme['text_primary'],
            font=('Consolas', theme['font_size_normal']),
            relief='flat',
            borderwidth=0,
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.server_status_text.pack(fill="both", expand=True, padx=theme['padding_medium'], pady=theme['padding_medium'])
        
        # Configure text tags for colors
        self.setup_status_text_colors()
        
        # Performance card with enhanced progress bars
        perf_card = StatusCard(top_row, "Performance & Info", "📊", self.theme_manager)
        perf_card.card_frame.grid(row=0, column=1, sticky="nsew", padx=(theme['margin_small'], 0))
        
        perf_content = perf_card.get_content_frame()
        
        # Performance metrics container
        metrics_container = tk.Frame(perf_content, bg=theme['bg_card'])
        metrics_container.pack(fill="both", expand=True, padx=theme['padding_medium'], pady=theme['padding_medium'])
        
        # Memory usage with value inside bar
        memory_frame = tk.Frame(metrics_container, bg=theme['bg_card'])
        memory_frame.pack(fill="x", pady=(0, theme['margin_medium']))
        
        tk.Label(memory_frame, text="Memory Usage:", bg=theme['bg_card'], 
                 fg=theme['text_primary'], font=('Segoe UI', theme['font_size_normal'], 'bold')).pack(anchor="w")
        
        memory_container = tk.Frame(memory_frame, bg=theme['bg_card'])
        memory_container.pack(fill="x", pady=(theme['margin_small'], 0))
        
        self.memory_progress = EnhancedProgressBar(memory_container, width=200, height=24, theme_manager=self.theme_manager)
        self.memory_progress.pack(anchor="w")
        
        # CPU usage with value inside bar
        cpu_frame = tk.Frame(metrics_container, bg=theme['bg_card'])
        cpu_frame.pack(fill="x", pady=(0, theme['margin_medium']))
        
        tk.Label(cpu_frame, text="CPU Usage:", bg=theme['bg_card'], 
                 fg=theme['text_primary'], font=('Segoe UI', theme['font_size_normal'], 'bold')).pack(anchor="w")
        
        cpu_container = tk.Frame(cpu_frame, bg=theme['bg_card'])
        cpu_container.pack(fill="x", pady=(theme['margin_small'], 0))
        
        self.cpu_progress = EnhancedProgressBar(cpu_container, width=200, height=24, theme_manager=self.theme_manager)
        self.cpu_progress.pack(anchor="w")
        
        # Server info section
        info_frame = tk.Frame(metrics_container, bg=theme['bg_card'])
        info_frame.pack(fill="x", pady=(theme['margin_medium'], 0))
        
        tk.Label(info_frame, text="Server Information:", bg=theme['bg_card'], 
                 fg=theme['text_primary'], font=('Segoe UI', theme['font_size_normal'], 'bold')).pack(anchor="w")
        
        # Info labels
        info_content = tk.Frame(info_frame, bg=theme['bg_card'])
        info_content.pack(fill="x", pady=(theme['margin_small'], 0))
        
        self.uptime_label = tk.Label(info_content, text="Uptime: --", bg=theme['bg_card'], 
                                    fg=theme['text_secondary'], font=('Segoe UI', theme['font_size_small']))
        self.uptime_label.pack(anchor="w")
        
        self.players_label = tk.Label(info_content, text="Players: 0/20", bg=theme['bg_card'], 
                                     fg=theme['text_secondary'], font=('Segoe UI', theme['font_size_small']))
        self.players_label.pack(anchor="w")
        
        self.port_label = tk.Label(info_content, text="Port: 25565", bg=theme['bg_card'], 
                                  fg=theme['text_secondary'], font=('Segoe UI', theme['font_size_small']))
        self.port_label.pack(anchor="w")
        
        # Quick actions card (spans both columns)
        actions_card = StatusCard(content, "Quick Actions", "⚡", self.theme_manager)
        actions_card.card_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        
        actions_content = actions_card.get_content_frame()
        
        # Action buttons grid
        buttons_container = tk.Frame(actions_content, bg=theme['bg_card'])
        buttons_container.pack(padx=theme['padding_medium'], pady=theme['padding_medium'])
        
        # Row 1 - Server Controls
        row1 = tk.Frame(buttons_container, bg=theme['bg_card'])
        row1.pack(pady=(0, theme['margin_small']))
        
        self.start_btn = ModernButton(row1, "🚀 Start Server", self.start_server, "success", self.theme_manager, "normal")
        self.start_btn.pack(side="left", padx=(0, theme['margin_small']))
        
        self.stop_btn = ModernButton(row1, "🛑 Stop Server", self.stop_server, "danger", self.theme_manager, "normal")
        self.stop_btn.pack(side="left", padx=(0, theme['margin_small']))
        
        self.restart_btn = ModernButton(row1, "🔄 Restart Server", self.restart_server, "primary", self.theme_manager, "normal")
        self.restart_btn.pack(side="left")
        
        # Row 2 - Additional Actions
        row2 = tk.Frame(buttons_container, bg=theme['bg_card'])
        row2.pack()
        
        ModernButton(row2, "💾 Create Backup", self.create_backup, "secondary", self.theme_manager, "normal").pack(side="left", padx=(0, theme['margin_small']))
        ModernButton(row2, "📊 System Check", self.system_check, "secondary", self.theme_manager, "normal").pack(side="left", padx=(0, theme['margin_small']))
        ModernButton(row2, "🔧 Open Console", self.open_console, "secondary", self.theme_manager, "normal").pack(side="left")
        
        # Register components for theme updates
        self.register_widget(server_card)
        self.register_widget(perf_card)
        self.register_widget(actions_card)
        self.register_widget(self.memory_progress)
        self.register_widget(self.cpu_progress)
        
        # DELAYED INITIAL UPDATE - wait for main window to fully initialize
        self.main_window.root.after(1000, self.force_dashboard_refresh)
    
    def setup_status_text_colors(self):
        """Setup color tags for status text"""
        theme = self.theme_manager.get_current_theme()
        
        # Define color tags
        self.server_status_text.tag_configure("title", foreground=theme['accent'], font=('Consolas', 11, 'bold'))
        self.server_status_text.tag_configure("running", foreground=theme['success'], font=('Consolas', 10, 'bold'))
        self.server_status_text.tag_configure("stopped", foreground=theme['error'], font=('Consolas', 10, 'bold'))
        self.server_status_text.tag_configure("warning", foreground=theme['warning'], font=('Consolas', 10, 'bold'))
        self.server_status_text.tag_configure("info", foreground=theme['info'])
        self.server_status_text.tag_configure("value", foreground=theme['accent_light'])
        self.server_status_text.tag_configure("label", foreground=theme['text_secondary'])
        self.server_status_text.tag_configure("normal", foreground=theme['text_primary'])
    
    def start_dashboard_updates(self):
        """Start dashboard auto-updates"""
        def update_loop():
            while self.update_active:
                try:
                    if hasattr(self, 'main_window') and self.main_window.root:
                        self.main_window.root.after(0, self.update_dashboard_data)
                    time.sleep(3)  # Update every 2 seconds
                except:
                    break
        
        update_thread = threading.Thread(target=update_loop, daemon=True)
        update_thread.start()
    
    def update_dashboard_data(self):
        """Update all dashboard data with throttling and error handling"""
        import time
        import logging

        # Throttle updates - don't update more than once per second
        if hasattr(self, '_last_gui_update'):
            if time.time() - self._last_gui_update < 1.0:
                return  # Skip this update

        self._last_gui_update = time.time()

        try:
            # Update server status text with colors
            self.update_colored_server_status()

            # Update performance metrics with values in bars
            self.update_enhanced_performance_metrics()

            # Update server information
            self.update_server_info()

            # Update button states
            self.update_button_states()

        except Exception as e:
            logging.error(f"Error updating dashboard: {e}")

    
    def update_colored_server_status(self):
        """Update server status with colored text"""
        try:
            is_running = self.main_window.process_manager.is_server_running()
            
            # Clear and prepare text widget
            if self.server_status_text:
                self.server_status_text.configure(state=tk.NORMAL)
                self.server_status_text.delete(1.0, tk.END)
                
                # Title
                self.insert_colored_text("=== SERVER STATUS ===\n\n", "title")
                
                if is_running:
                    server_status = self.main_window.process_manager.get_server_status()
                    
                    # Status
                    self.insert_colored_text("🟢 Status: ", "label")
                    self.insert_colored_text("RUNNING\n", "running")
                    
                    # PID
                    self.insert_colored_text("📍 PID: ", "label")
                    self.insert_colored_text(f"{server_status.get('pid', 'Unknown')}\n", "value")
                    
                    # Memory info
                    memory_mb = server_status.get('memory', 0)
                    if memory_mb:
                        self.insert_colored_text("💾 Memory: ", "label")
                        self.insert_colored_text(f"{memory_mb:.1f} MB\n", "value")
                    
                    # Uptime
                    if 'uptime' in server_status:
                        uptime_seconds = server_status['uptime']
                        hours = int(uptime_seconds // 3600)
                        minutes = int((uptime_seconds % 3600) // 60)
                        self.insert_colored_text("⏱️ Uptime: ", "label")
                        self.insert_colored_text(f"{hours}h {minutes}m\n", "value")
                    
                    self.insert_colored_text("\n", "normal")
                    self.insert_colored_text("✅ Server is ready for connections\n", "info")
                    
                    # JAR info
                    if self.main_window.server_jar_path:
                        jar_name = os.path.basename(self.main_window.server_jar_path)
                        self.insert_colored_text("📦 JAR: ", "label")
                        self.insert_colored_text(f"{jar_name}\n", "normal")
                
                else:
                    # Server stopped
                    self.insert_colored_text("🔴 Status: ", "label")
                    self.insert_colored_text("STOPPED\n\n", "stopped")
                    
                    self.insert_colored_text("❌ Server is not running\n\n", "warning")
                    
                    if self.main_window.server_jar_path:
                        jar_name = os.path.basename(self.main_window.server_jar_path)
                        self.insert_colored_text("📦 Selected JAR: ", "label")
                        self.insert_colored_text(f"{jar_name}\n", "normal")
                    else:
                        self.insert_colored_text("⚠️ No server JAR selected\n", "warning")
                        self.insert_colored_text("Go to Server Control tab to select a JAR file", "info")
                
                self.server_status_text.configure(state=tk.DISABLED)
                
        except Exception as e:
            print(f"Error updating colored server status: {e}")
    
    def insert_colored_text(self, text, tag):
        """Insert text with specified color tag"""
        start_pos = self.server_status_text.index(tk.INSERT)
        self.server_status_text.insert(tk.INSERT, text)
        end_pos = self.server_status_text.index(tk.INSERT)
        self.server_status_text.tag_add(tag, start_pos, end_pos)
    
    def update_enhanced_performance_metrics(self):
        """Update performance progress bars with values inside"""
        try:
            if self.main_window.process_manager.is_server_running():
                # Get real server status
                server_status = self.main_window.process_manager.get_server_status()
                
                # Memory usage
                memory_mb = server_status.get('memory', 0)
                max_memory = self.main_window.config.get('max_memory', '2G')
                
                # Parse max memory (e.g., "2G" -> 2048 MB)
                if max_memory.endswith('G'):
                    max_memory_mb = int(max_memory[:-1]) * 1024
                elif max_memory.endswith('M'):
                    max_memory_mb = int(max_memory[:-1])
                else:
                    max_memory_mb = 2048  # Default
                
                memory_percent = (memory_mb / max_memory_mb) * 100 if max_memory_mb > 0 else 0
                memory_text = f"{memory_mb:.0f}MB / {max_memory_mb}MB ({memory_percent:.1f}%)"
                
                # CPU usage
                cpu_percent = server_status.get('cpu', 0)
                cpu_text = f"{cpu_percent:.1f}%"
                
                # Update enhanced progress bars
                if self.memory_progress:
                    self.memory_progress.set_progress(min(memory_percent, 100), 100, memory_text)
                
                if self.cpu_progress:
                    self.cpu_progress.set_progress(min(cpu_percent, 100), 100, cpu_text)
            else:
                # Server not running - reset to 0
                if self.memory_progress:
                    self.memory_progress.set_progress(0, 100, "Server Offline")
                
                if self.cpu_progress:
                    self.cpu_progress.set_progress(0, 100, "Server Offline")
                    
        except Exception as e:
            print(f"Error updating enhanced performance metrics: {e}")
    
    def update_server_info(self):
        """Update server information labels"""
        try:
            is_running = self.main_window.process_manager.is_server_running()
            
            if is_running:
                server_status = self.main_window.process_manager.get_server_status()
                
                # Uptime
                if 'uptime' in server_status:
                    uptime_seconds = server_status['uptime']
                    hours = int(uptime_seconds // 3600)
                    minutes = int((uptime_seconds % 3600) // 60)
                    uptime_text = f"⏱️ Uptime: {hours}h {minutes}m"
                else:
                    uptime_text = "⏱️ Uptime: Unknown"
                
                # Players (placeholder - would need server query)
                players_text = "👥 Players: --/--"
                
            else:
                uptime_text = "⏱️ Uptime: Server stopped"
                players_text = "👥 Players: Server offline"
            
            # Port
            port = self.main_window.config.get('server_port', 25565)
            port_text = f"🌐 Port: {port}"
            
            # Update labels
            if self.uptime_label:
                self.uptime_label.configure(text=uptime_text)
            if self.players_label:
                self.players_label.configure(text=players_text)
            if self.port_label:
                self.port_label.configure(text=port_text)
                
        except Exception as e:
            print(f"Error updating server info: {e}")
    
    def update_button_states(self):
        """Update button enabled/disabled states based on server status"""
        try:
            is_running = self.main_window.process_manager.is_server_running()
            has_jar = bool(self.main_window.server_jar_path)
            
            # Enable/disable buttons based on state
            if hasattr(self, 'start_btn'):
                if is_running or not has_jar:
                    self.start_btn.configure(state=tk.DISABLED)
                else:
                    self.start_btn.configure(state=tk.NORMAL)
            
            if hasattr(self, 'stop_btn'):
                if is_running:
                    self.stop_btn.configure(state=tk.NORMAL)
                else:
                    self.stop_btn.configure(state=tk.DISABLED)
            
            if hasattr(self, 'restart_btn'):
                if is_running:
                    self.restart_btn.configure(state=tk.NORMAL)
                else:
                    self.restart_btn.configure(state=tk.DISABLED)
                    
        except Exception as e:
            print(f"Error updating button states: {e}")
    
    # Button action methods
    def start_server(self):
        """Start server from dashboard"""
        self.main_window.start_server()
    
    def stop_server(self):
        """Stop server from dashboard"""
        self.main_window.stop_server()
    
    def restart_server(self):
        """Restart server from dashboard"""
        self.main_window.restart_server()
    
    def create_backup(self):
        """Create backup from dashboard"""
        self.main_window.create_manual_backup()
    
    def system_check(self):
        """Run system check from dashboard"""
        self.main_window.run_system_check()
    
    def open_console(self):
        """Switch to console tab"""
        try:
            # Find and select console tab
            for i in range(self.main_window.notebook.index("end")):
                if "Console" in self.main_window.notebook.tab(i, "text"):
                    self.main_window.notebook.select(i)
                    break
        except Exception as e:
            print(f"Error switching to console: {e}")
    
    def update_theme(self):
        """Update dashboard theme"""
        super().update_theme()
        
        # Update text widget colors
        if self.server_status_text:
            theme = self.theme_manager.get_current_theme()
            self.server_status_text.configure(
                bg=theme['bg_card'],
                fg=theme['text_primary']
            )
            # Reconfigure color tags
            self.setup_status_text_colors()
    
    def cleanup(self):
        """Cleanup dashboard resources"""
        self.update_active = False
        
    def force_dashboard_refresh(self):
        """Force immediate dashboard refresh"""
        try:
            print("🔄 Force refreshing dashboard state...")
            
            # Debug current state
            jar_path = getattr(self.main_window, 'server_jar_path', None)
            print(f"🔍 JAR path: {jar_path}")
            
            is_running = False
            if hasattr(self.main_window, 'process_manager'):
                is_running = self.main_window.process_manager.is_server_running()
                print(f"🔍 Server running: {is_running}")
            
            # Force update all dashboard data
            self.update_dashboard_data()
            
            print("✅ Dashboard force refresh completed")
            
        except Exception as e:
            print(f"❌ Error in force dashboard refresh: {e}")

    def refresh_from_external_change(self):
        """Called when external changes happen (JAR selected, server started, etc.)"""
        try:
            # Immediate update
            self.update_dashboard_data()
            print("🔄 Dashboard updated from external change")
        except Exception as e:
            print(f"❌ Error refreshing from external change: {e}")

