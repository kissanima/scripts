"""
Health tab implementation with real-time monitoring and diagnostics
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import logging
import os
from datetime import datetime, timedelta
from .base_tab import BaseTab
from ..components.status_card import StatusCard
from ..components.modern_widgets import ModernButton

# Try to import psutil for system monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

class HealthProgressBar(tk.Frame):
    """Health-aware progress bar with color coding"""
    
    def __init__(self, parent, width=200, height=20, theme_manager=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.width = width
        self.height = height
        self.theme_manager = theme_manager
        self.progress = 0
        self.max_value = 100
        self.text = "0%"
        self.status = "good"  # good, warning, critical
        
        self.setup_progress_bar()
    
    def setup_progress_bar(self):
        """Setup health progress bar"""
        if self.theme_manager:
            theme = self.theme_manager.get_current_theme()
        else:
            from themes import get_theme
            theme = get_theme('dark')
        
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
        
        # Create canvas
        self.canvas = tk.Canvas(
            self,
            width=self.width-2,
            height=self.height-2,
            bg=theme['bg_tertiary'],
            highlightthickness=0,
            bd=0
        )
        self.canvas.pack(fill="both", expand=True, padx=1, pady=1)
        
        # Progress rectangle
        self.progress_rect = self.canvas.create_rectangle(
            0, 0, 0, self.height-2,
            fill=theme['health_good'],
            outline=""
        )
        
        # Text overlay
        self.text_item = self.canvas.create_text(
            (self.width-2) // 2, (self.height-2) // 2,
            text=self.text,
            fill=theme['text_primary'],
            font=('Segoe UI', 9, 'bold')
        )
    
    def set_progress(self, value, max_value=100, text=None, status="good"):
        """Set progress with health status"""
        self.progress = max(0, min(value, max_value))
        self.max_value = max_value
        self.status = status
        
        if text is not None:
            self.text = text
        else:
            self.text = f"{value:.1f}%"
        
        self.update_display()
    
    def update_display(self):
        """Update progress bar display with health colors"""
        if self.theme_manager:
            theme = self.theme_manager.get_current_theme()
            
            # Choose color based on status
            if self.status == "critical":
                color = theme['health_critical']
            elif self.status == "warning":
                color = theme['health_warning']
            else:
                color = theme['health_good']
            
            # Update progress width
            if self.max_value > 0:
                progress_width = int((self.progress / self.max_value) * (self.width - 2))
                self.canvas.coords(self.progress_rect, 0, 0, progress_width, self.height-2)
            else:
                self.canvas.coords(self.progress_rect, 0, 0, 0, self.height-2)
            
            # Update colors and text
            self.canvas.itemconfig(self.progress_rect, fill=color)
            self.canvas.itemconfig(self.text_item, text=self.text)

class HealthTab(BaseTab):
    """Health monitoring tab with real-time system and server monitoring"""
    
    def __init__(self, parent, theme_manager, main_window):
        self.main_window = main_window
        super().__init__(parent, theme_manager)
        
        # Health monitoring
        self.monitoring_active = True
        self.health_data = {
            'cpu_percent': 0,
            'memory_percent': 0,
            'memory_used_gb': 0,
            'memory_total_gb': 0,
            'disk_percent': 0,
            'disk_free_gb': 0,
            'server_memory_mb': 0,
            'server_cpu_percent': 0,
            'uptime_seconds': 0,
            'last_update': None
        }
        
        # UI components
        self.system_cpu_bar = None
        self.system_memory_bar = None
        self.disk_usage_bar = None
        self.server_memory_bar = None
        self.server_cpu_bar = None
        self.health_status_label = None
        self.alerts_text = None
        self.system_info_text = None
        
        self.create_content()
        self.start_health_monitoring()
    
    def create_content(self):
        """Create health monitoring content"""
        theme = self.theme_manager.get_current_theme()
        
        content = tk.Frame(self.tab_frame, bg=theme['bg_primary'])
        content.pack(fill="both", expand=True, padx=theme['padding_large'], pady=theme['padding_large'])
        
        # Configure main grid
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(0, weight=0)
        content.grid_rowconfigure(1, weight=1)
        content.grid_rowconfigure(2, weight=1)
        
        # Health status overview
        status_card = StatusCard(content, "System Health Overview", "❤️", self.theme_manager)
        status_card.card_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, theme['margin_medium']))
        
        status_content = status_card.get_content_frame()
        
        # Overall health status
        status_frame = tk.Frame(status_content, bg=theme['bg_card'])
        status_frame.pack(fill="x", padx=theme['padding_medium'], pady=theme['padding_medium'])
        
        status_left = tk.Frame(status_frame, bg=theme['bg_card'])
        status_left.pack(side="left", fill="both", expand=True)
        
        self.health_status_label = tk.Label(
            status_left,
            text="🟢 System Health: EXCELLENT",
            bg=theme['bg_card'],
            fg=theme['health_excellent'],
            font=('Segoe UI', theme['font_size_large'], 'bold')
        )
        self.health_status_label.pack(anchor="w")
        
        self.last_check_label = tk.Label(
            status_left,
            text="Last checked: Never",
            bg=theme['bg_card'],
            fg=theme['text_secondary'],
            font=('Segoe UI', theme['font_size_small'])
        )
        self.last_check_label.pack(anchor="w")
        
        # Quick actions
        status_right = tk.Frame(status_frame, bg=theme['bg_card'])
        status_right.pack(side="right")
        
        ModernButton(status_right, "🔄 Refresh", self.refresh_health_data, "secondary", self.theme_manager, "small").pack(side="left", padx=(0, theme['margin_small']))
        ModernButton(status_right, "📊 Full Report", self.generate_health_report, "primary", self.theme_manager, "small").pack(side="left")
        
        # System resources card
        system_card = StatusCard(content, "System Resources", "💻", self.theme_manager)
        system_card.card_frame.grid(row=1, column=0, sticky="nsew", padx=(0, theme['margin_small']))
        
        system_content = system_card.get_content_frame()
        
        # System metrics
        system_frame = tk.Frame(system_content, bg=theme['bg_card'])
        system_frame.pack(fill="both", expand=True, padx=theme['padding_medium'], pady=theme['padding_medium'])
        
        # CPU Usage
        cpu_frame = tk.Frame(system_frame, bg=theme['bg_card'])
        cpu_frame.pack(fill="x", pady=(0, theme['margin_medium']))
        
        tk.Label(cpu_frame, text="🖥️ CPU Usage:", bg=theme['bg_card'], 
                 fg=theme['text_primary'], font=('Segoe UI', theme['font_size_normal'], 'bold')).pack(anchor="w")
        
        self.system_cpu_bar = HealthProgressBar(cpu_frame, width=250, height=24, theme_manager=self.theme_manager)
        self.system_cpu_bar.pack(anchor="w", pady=(theme['margin_small'], 0))
        
        # Memory Usage
        memory_frame = tk.Frame(system_frame, bg=theme['bg_card'])
        memory_frame.pack(fill="x", pady=(0, theme['margin_medium']))
        
        tk.Label(memory_frame, text="💾 Memory Usage:", bg=theme['bg_card'], 
                 fg=theme['text_primary'], font=('Segoe UI', theme['font_size_normal'], 'bold')).pack(anchor="w")
        
        self.system_memory_bar = HealthProgressBar(memory_frame, width=250, height=24, theme_manager=self.theme_manager)
        self.system_memory_bar.pack(anchor="w", pady=(theme['margin_small'], 0))
        
        # Disk Usage
        disk_frame = tk.Frame(system_frame, bg=theme['bg_card'])
        disk_frame.pack(fill="x", pady=(0, theme['margin_medium']))
        
        tk.Label(disk_frame, text="💿 Disk Usage:", bg=theme['bg_card'], 
                 fg=theme['text_primary'], font=('Segoe UI', theme['font_size_normal'], 'bold')).pack(anchor="w")
        
        self.disk_usage_bar = HealthProgressBar(disk_frame, width=250, height=24, theme_manager=self.theme_manager)
        self.disk_usage_bar.pack(anchor="w", pady=(theme['margin_small'], 0))
        
        # System info
        info_label = tk.Label(
            system_frame,
            text="📈 Real-time system monitoring • Updates every 5 seconds",
            bg=theme['bg_card'],
            fg=theme['text_secondary'],
            font=('Segoe UI', theme['font_size_small'])
        )
        info_label.pack(anchor="w", pady=(theme['margin_medium'], 0))
        
        # Server performance card
        server_card = StatusCard(content, "Server Performance", "🎮", self.theme_manager)
        server_card.card_frame.grid(row=1, column=1, sticky="nsew", padx=(theme['margin_small'], 0))
        
        server_content = server_card.get_content_frame()
        
        # Server metrics
        server_frame = tk.Frame(server_content, bg=theme['bg_card'])
        server_frame.pack(fill="both", expand=True, padx=theme['padding_medium'], pady=theme['padding_medium'])
        
        # Server status
        server_status_frame = tk.Frame(server_frame, bg=theme['bg_card'])
        server_status_frame.pack(fill="x", pady=(0, theme['margin_medium']))
        
        self.server_status_label = tk.Label(
            server_status_frame,
            text="🔴 Server: Offline",
            bg=theme['bg_card'],
            fg=theme['text_muted'],
            font=('Segoe UI', theme['font_size_normal'], 'bold')
        )
        self.server_status_label.pack(anchor="w")
        
        # Server Memory
        server_mem_frame = tk.Frame(server_frame, bg=theme['bg_card'])
        server_mem_frame.pack(fill="x", pady=(0, theme['margin_medium']))
        
        tk.Label(server_mem_frame, text="🎯 Server Memory:", bg=theme['bg_card'], 
                 fg=theme['text_primary'], font=('Segoe UI', theme['font_size_normal'], 'bold')).pack(anchor="w")
        
        self.server_memory_bar = HealthProgressBar(server_mem_frame, width=250, height=24, theme_manager=self.theme_manager)
        self.server_memory_bar.pack(anchor="w", pady=(theme['margin_small'], 0))
        
        # Server CPU
        server_cpu_frame = tk.Frame(server_frame, bg=theme['bg_card'])
        server_cpu_frame.pack(fill="x", pady=(0, theme['margin_medium']))
        
        tk.Label(server_cpu_frame, text="⚡ Server CPU:", bg=theme['bg_card'], 
                 fg=theme['text_primary'], font=('Segoe UI', theme['font_size_normal'], 'bold')).pack(anchor="w")
        
        self.server_cpu_bar = HealthProgressBar(server_cpu_frame, width=250, height=24, theme_manager=self.theme_manager)
        self.server_cpu_bar.pack(anchor="w", pady=(theme['margin_small'], 0))
        
        # Server uptime
        self.uptime_label = tk.Label(
            server_frame,
            text="⏱️ Uptime: --",
            bg=theme['bg_card'],
            fg=theme['text_secondary'],
            font=('Segoe UI', theme['font_size_small'])
        )
        self.uptime_label.pack(anchor="w")
        
        # Health alerts card
        alerts_card = StatusCard(content, "Health Alerts & Recommendations", "⚠️", self.theme_manager)
        alerts_card.card_frame.grid(row=2, column=0, sticky="nsew", padx=(0, theme['margin_small']))
        
        alerts_content = alerts_card.get_content_frame()
        
        # Alerts text area
        alerts_frame = tk.Frame(alerts_content, bg=theme['bg_card'])
        alerts_frame.pack(fill="both", expand=True, padx=theme['padding_medium'], pady=theme['padding_medium'])
        
        self.alerts_text = tk.Text(
            alerts_frame,
            bg=theme['bg_card'],
            fg=theme['text_primary'],
            font=('Segoe UI', theme['font_size_small']),
            relief='flat',
            borderwidth=0,
            wrap=tk.WORD,
            height=8,
            state=tk.DISABLED
        )
        self.alerts_text.pack(fill="both", expand=True)
        
        # Configure text tags for alerts
        self.setup_alert_tags()
        
        # System information card
        sysinfo_card = StatusCard(content, "System Information", "📋", self.theme_manager)
        sysinfo_card.card_frame.grid(row=2, column=1, sticky="nsew", padx=(theme['margin_small'], 0))
        
        sysinfo_content = sysinfo_card.get_content_frame()
        
        # System info text area
        sysinfo_frame = tk.Frame(sysinfo_content, bg=theme['bg_card'])
        sysinfo_frame.pack(fill="both", expand=True, padx=theme['padding_medium'], pady=theme['padding_medium'])
        
        self.system_info_text = tk.Text(
            sysinfo_frame,
            bg=theme['bg_card'],
            fg=theme['text_primary'],
            font=('Consolas', theme['font_size_small']),
            relief='flat',
            borderwidth=0,
            wrap=tk.WORD,
            height=8,
            state=tk.DISABLED
        )
        self.system_info_text.pack(fill="both", expand=True)
        
        # Register components
        self.register_widget(status_card)
        self.register_widget(system_card)
        self.register_widget(server_card)
        self.register_widget(alerts_card)
        self.register_widget(sysinfo_card)
        
        # Initial data load
        self.refresh_health_data()
        self.update_system_info()
    
    def setup_alert_tags(self):
        """Setup text tags for different alert types"""
        theme = self.theme_manager.get_current_theme()
        
        self.alerts_text.tag_configure("info", foreground=theme['info'])
        self.alerts_text.tag_configure("warning", foreground=theme['warning'])
        self.alerts_text.tag_configure("critical", foreground=theme['error'])
        self.alerts_text.tag_configure("good", foreground=theme['success'])
        self.alerts_text.tag_configure("header", foreground=theme['accent'], font=('Segoe UI', 10, 'bold'))
    
    def start_health_monitoring(self):
        """Start continuous health monitoring"""
        def monitoring_loop():
            while self.monitoring_active:
                try:
                    if hasattr(self, 'main_window') and self.main_window.root:
                        self.main_window.root.after(0, self.refresh_health_data)
                    time.sleep(5)  # Update every 5 seconds
                except:
                    break
        
        monitor_thread = threading.Thread(target=monitoring_loop, daemon=True)
        monitor_thread.start()
    
    def refresh_health_data(self):
        """Refresh all health monitoring data"""
        try:
            # Update system resources
            self.update_system_resources()
            
            # Update server performance
            self.update_server_performance()
            
            # Update health alerts
            self.update_health_alerts()
            
            # Update overall health status
            self.update_overall_health_status()
            
            # Update last check time
            self.health_data['last_update'] = datetime.now()
            if hasattr(self, 'last_check_label'):
                self.last_check_label.configure(text=f"Last checked: {self.health_data['last_update'].strftime('%H:%M:%S')}")
            
        except Exception as e:
            logging.error(f"Error refreshing health data: {e}")
    
    def update_system_resources(self):
        """Update system resource monitoring"""
        try:
            if PSUTIL_AVAILABLE:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=0.1)
                cpu_status = "good" if cpu_percent < 70 else "warning" if cpu_percent < 90 else "critical"
                
                # Memory usage
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                memory_status = "good" if memory_percent < 80 else "warning" if memory_percent < 95 else "critical"
                
                # Disk usage
                disk = psutil.disk_usage('.' if os.name != 'nt' else 'C:')
                disk_percent = (disk.used / disk.total) * 100
                disk_status = "good" if disk_percent < 85 else "warning" if disk_percent < 95 else "critical"
                
                # Update health data
                self.health_data.update({
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory_percent,
                    'memory_used_gb': memory.used / 1024 / 1024 / 1024,
                    'memory_total_gb': memory.total / 1024 / 1024 / 1024,
                    'disk_percent': disk_percent,
                    'disk_free_gb': disk.free / 1024 / 1024 / 1024
                })
                
                # Update progress bars
                if self.system_cpu_bar:
                    self.system_cpu_bar.set_progress(
                        cpu_percent, 100, 
                        f"CPU: {cpu_percent:.1f}%", 
                        cpu_status
                    )
                
                if self.system_memory_bar:
                    memory_text = f"RAM: {self.health_data['memory_used_gb']:.1f}GB / {self.health_data['memory_total_gb']:.1f}GB ({memory_percent:.1f}%)"
                    self.system_memory_bar.set_progress(
                        memory_percent, 100,
                        memory_text,
                        memory_status
                    )
                
                if self.disk_usage_bar:
                    disk_text = f"Disk: {disk_percent:.1f}% used ({self.health_data['disk_free_gb']:.1f}GB free)"
                    self.disk_usage_bar.set_progress(
                        disk_percent, 100,
                        disk_text,
                        disk_status
                    )
            else:
                # Fallback without psutil
                if self.system_cpu_bar:
                    self.system_cpu_bar.set_progress(0, 100, "CPU: Not available", "warning")
                if self.system_memory_bar:
                    self.system_memory_bar.set_progress(0, 100, "Memory: Not available", "warning")
                if self.disk_usage_bar:
                    self.disk_usage_bar.set_progress(0, 100, "Disk: Not available", "warning")
        
        except Exception as e:
            logging.error(f"Error updating system resources: {e}")
    
    def update_server_performance(self):
        """Update server performance monitoring"""
        try:
            is_running = self.main_window.process_manager.is_server_running()
            
            if is_running:
                server_status = self.main_window.process_manager.get_server_status()
                
                
                
                # Update server status
                if self.server_status_label:
                    self.server_status_label.configure(
                        text="🟢 Server: Online",
                        fg=self.theme_manager.get_current_theme()['success']
                    )
                
                # Server memory
                memory_mb = server_status.get('memory', 0)
                max_memory = self.main_window.config.get('max_memory', '2G')
                
                if max_memory.endswith('G'):
                    max_memory_mb = int(max_memory[:-1]) * 1024
                elif max_memory.endswith('M'):
                    max_memory_mb = int(max_memory[:-1])
                else:
                    max_memory_mb = 2048
                
                memory_percent = (memory_mb / max_memory_mb) * 100 if max_memory_mb > 0 else 0
                memory_status = "good" if memory_percent < 80 else "warning" if memory_percent < 95 else "critical"
                
                # Server CPU
                cpu_percent = server_status.get('cpu', 0)
                cpu_status = "good" if cpu_percent < 70 else "warning" if cpu_percent < 90 else "critical"
                
                # Update progress bars
                if self.server_memory_bar:
                    memory_text = f"Server: {memory_mb:.0f}MB / {max_memory_mb}MB ({memory_percent:.1f}%)"
                    self.server_memory_bar.set_progress(memory_percent, 100, memory_text, memory_status)
                
                if self.server_cpu_bar:
                    self.server_cpu_bar.set_progress(cpu_percent, 100, f"Server CPU: {cpu_percent:.1f}%", cpu_status)
                
                # Uptime
                if 'uptime' in server_status:
                    uptime_seconds = server_status['uptime']
                    hours = int(uptime_seconds // 3600)
                    minutes = int((uptime_seconds % 3600) // 60)
                    uptime_text = f"⏱️ Uptime: {hours}h {minutes}m"
                else:
                    uptime_text = "⏱️ Uptime: Unknown"
                
                if self.uptime_label:
                    self.uptime_label.configure(text=uptime_text)
                
                # Update health data
                self.health_data.update({
                    'server_memory_mb': memory_mb,
                    'server_cpu_percent': cpu_percent,
                    'uptime_seconds': uptime_seconds if 'uptime' in server_status else 0
                })
                
            else:
                # Server offline
                if self.server_status_label:
                    self.server_status_label.configure(
                        text="🔴 Server: Offline",
                        fg=self.theme_manager.get_current_theme()['text_muted']
                    )
                
                if self.server_memory_bar:
                    self.server_memory_bar.set_progress(0, 100, "Server Offline", "warning")
                
                if self.server_cpu_bar:
                    self.server_cpu_bar.set_progress(0, 100, "Server Offline", "warning")
                
                if self.uptime_label:
                    self.uptime_label.configure(text="⏱️ Uptime: Server offline")
                
                self.health_data.update({
                    'server_memory_mb': 0,
                    'server_cpu_percent': 0,
                    'uptime_seconds': 0
                })
        
        except Exception as e:
            logging.error(f"Error updating server performance: {e}")
    
    def update_health_alerts(self):
        """Update health alerts and recommendations"""
        try:
            if not self.alerts_text:
                return
            
            self.alerts_text.configure(state=tk.NORMAL)
            self.alerts_text.delete(1.0, tk.END)
            
            alerts = []
            recommendations = []
            
            # System alerts
            if self.health_data.get('cpu_percent', 0) > 90:
                alerts.append(("🔥 HIGH CPU USAGE", f"System CPU at {self.health_data['cpu_percent']:.1f}%", "critical"))
            elif self.health_data.get('cpu_percent', 0) > 70:
                alerts.append(("⚠️ Elevated CPU Usage", f"System CPU at {self.health_data['cpu_percent']:.1f}%", "warning"))
            
            if self.health_data.get('memory_percent', 0) > 95:
                alerts.append(("🚨 CRITICAL MEMORY USAGE", f"System memory at {self.health_data['memory_percent']:.1f}%", "critical"))
            elif self.health_data.get('memory_percent', 0) > 80:
                alerts.append(("⚠️ High Memory Usage", f"System memory at {self.health_data['memory_percent']:.1f}%", "warning"))
            
            if self.health_data.get('disk_percent', 0) > 95:
                alerts.append(("💿 DISK SPACE CRITICAL", f"Only {self.health_data['disk_free_gb']:.1f}GB free", "critical"))
            elif self.health_data.get('disk_percent', 0) > 85:
                alerts.append(("💿 Low Disk Space", f"{self.health_data['disk_free_gb']:.1f}GB free", "warning"))
            
            # Server alerts
            server_memory_percent = 0
            if self.main_window.process_manager.is_server_running():
                max_memory = self.main_window.config.get('max_memory', '2G')
                if max_memory.endswith('G'):
                    max_memory_mb = int(max_memory[:-1]) * 1024
                else:
                    max_memory_mb = 2048
                
                server_memory_percent = (self.health_data.get('server_memory_mb', 0) / max_memory_mb) * 100
                
                if server_memory_percent > 95:
                    alerts.append(("🎮 SERVER MEMORY CRITICAL", f"Server using {server_memory_percent:.1f}% of allocated memory", "critical"))
                elif server_memory_percent > 80:
                    alerts.append(("🎮 High Server Memory", f"Server using {server_memory_percent:.1f}% of allocated memory", "warning"))
            
            # Recommendations
            if self.health_data.get('memory_percent', 0) > 85:
                recommendations.append("💡 Consider closing unnecessary applications to free up memory")
            
            if server_memory_percent > 85:
                recommendations.append("💡 Consider increasing server memory allocation in settings")
            
            if self.health_data.get('disk_percent', 0) > 90:
                recommendations.append("💡 Clean up old backups and temporary files")
            
            if not self.main_window.process_manager.is_server_running():
                recommendations.append("ℹ️ Server is offline - start the server to monitor performance")
            
            # Display alerts
            if alerts:
                self.insert_alert_text("🚨 ACTIVE ALERTS\n", "header")
                for title, desc, level in alerts:
                    self.insert_alert_text(f"{title}\n", level)
                    self.insert_alert_text(f"   {desc}\n\n", "info")
            else:
                self.insert_alert_text("✅ NO ACTIVE ALERTS\n", "good")
                self.insert_alert_text("All systems operating normally\n\n", "info")
            
            # Display recommendations
            if recommendations:
                self.insert_alert_text("💡 RECOMMENDATIONS\n", "header")
                for rec in recommendations:
                    self.insert_alert_text(f"{rec}\n", "info")
            
            if not PSUTIL_AVAILABLE:
                self.insert_alert_text("\n⚠️ LIMITED MONITORING\n", "warning")
                self.insert_alert_text("Install 'psutil' for full system monitoring capabilities", "info")
            
            self.alerts_text.configure(state=tk.DISABLED)
            
        except Exception as e:
            logging.error(f"Error updating health alerts: {e}")
    
    def insert_alert_text(self, text, tag):
        """Insert text with specified alert tag"""
        start_pos = self.alerts_text.index(tk.INSERT)
        self.alerts_text.insert(tk.INSERT, text)
        end_pos = self.alerts_text.index(tk.INSERT)
        self.alerts_text.tag_add(tag, start_pos, end_pos)
    
    def update_overall_health_status(self):
        """Update overall health status indicator"""
        try:
            if not self.health_status_label:
                return
            
            theme = self.theme_manager.get_current_theme()
            
            # Determine overall health
            critical_issues = 0
            warning_issues = 0
            
            # Check system resources
            if self.health_data.get('cpu_percent', 0) > 90 or self.health_data.get('memory_percent', 0) > 95:
                critical_issues += 1
            elif self.health_data.get('cpu_percent', 0) > 70 or self.health_data.get('memory_percent', 0) > 80:
                warning_issues += 1
            
            if self.health_data.get('disk_percent', 0) > 95:
                critical_issues += 1
            elif self.health_data.get('disk_percent', 0) > 85:
                warning_issues += 1
            
            # Determine status
            if critical_issues > 0:
                status_text = "🔴 System Health: CRITICAL"
                status_color = theme['health_critical']
            elif warning_issues > 0:
                status_text = "🟡 System Health: WARNING"
                status_color = theme['health_warning']
            else:
                status_text = "🟢 System Health: EXCELLENT"
                status_color = theme['health_excellent']
            
            self.health_status_label.configure(text=status_text, fg=status_color)
            
        except Exception as e:
            logging.error(f"Error updating overall health status: {e}")
    
    def update_system_info(self):
        """Update system information display"""
        try:
            if not self.system_info_text:
                return
            
            self.system_info_text.configure(state=tk.NORMAL)
            self.system_info_text.delete(1.0, tk.END)
            
            info_text = "SYSTEM INFORMATION\n"
            info_text += "=" * 30 + "\n\n"
            
            if PSUTIL_AVAILABLE:
                # CPU info
                info_text += f"CPU Cores: {psutil.cpu_count()} ({psutil.cpu_count(logical=False)} physical)\n"
                info_text += f"CPU Frequency: {psutil.cpu_freq().current:.0f} MHz\n\n"
                
                # Memory info
                memory = psutil.virtual_memory()
                info_text += f"Total Memory: {memory.total / 1024**3:.1f} GB\n"
                info_text += f"Available Memory: {memory.available / 1024**3:.1f} GB\n\n"
                
                # Disk info
                disk = psutil.disk_usage('.' if os.name != 'nt' else 'C:')
                info_text += f"Total Disk Space: {disk.total / 1024**3:.1f} GB\n"
                info_text += f"Free Disk Space: {disk.free / 1024**3:.1f} GB\n\n"
                
                # Boot time
                boot_time = datetime.fromtimestamp(psutil.boot_time())
                info_text += f"System Boot Time: {boot_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                
                uptime = datetime.now() - boot_time
                info_text += f"System Uptime: {uptime.days} days, {uptime.seconds//3600} hours\n\n"
            else:
                info_text += "System monitoring not available\n"
                info_text += "Install 'psutil' for detailed system info\n\n"
            
            # Java info
            java_path = self.main_window.config.get("java_path", "java")
            info_text += f"Java Path: {java_path}\n"
            
            # Server info
            if hasattr(self.main_window, 'server_jar_path') and self.main_window.server_jar_path:
                info_text += f"Server JAR: {os.path.basename(self.main_window.server_jar_path)}\n"
                server_dir = os.path.dirname(self.main_window.server_jar_path)
                info_text += f"Server Directory: {server_dir}\n"
            
            max_memory = self.main_window.config.get('max_memory', '2G')
            info_text += f"Max Server Memory: {max_memory}\n"
            
            self.system_info_text.insert(1.0, info_text)
            self.system_info_text.configure(state=tk.DISABLED)
            
        except Exception as e:
            logging.error(f"Error updating system info: {e}")
    
    def generate_health_report(self):
        """Generate a comprehensive health report"""
        try:
            report = "MINECRAFT SERVER HEALTH REPORT\n"
            report += "=" * 40 + "\n"
            report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            # System summary
            report += "SYSTEM SUMMARY\n"
            report += "-" * 20 + "\n"
            report += f"CPU Usage: {self.health_data.get('cpu_percent', 0):.1f}%\n"
            report += f"Memory Usage: {self.health_data.get('memory_percent', 0):.1f}%\n"
            report += f"Disk Usage: {self.health_data.get('disk_percent', 0):.1f}%\n"
            report += f"Available Memory: {self.health_data.get('memory_total_gb', 0) - self.health_data.get('memory_used_gb', 0):.1f} GB\n"
            report += f"Free Disk Space: {self.health_data.get('disk_free_gb', 0):.1f} GB\n\n"
            
            # Server summary
            report += "SERVER SUMMARY\n"
            report += "-" * 20 + "\n"
            if self.main_window.process_manager.is_server_running():
                report += f"Status: Online\n"
                report += f"Memory Usage: {self.health_data.get('server_memory_mb', 0):.0f} MB\n"
                report += f"CPU Usage: {self.health_data.get('server_cpu_percent', 0):.1f}%\n"
                
                uptime_hours = self.health_data.get('uptime_seconds', 0) / 3600
                report += f"Uptime: {uptime_hours:.1f} hours\n"
            else:
                report += "Status: Offline\n"
            
            report += f"\nMax Allocated Memory: {self.main_window.config.get('max_memory', '2G')}\n"
            
            # Recommendations
            report += "\nRECOMMENDATIONS\n"
            report += "-" * 20 + "\n"
            
            if self.health_data.get('memory_percent', 0) > 80:
                report += "• Consider closing unnecessary applications\n"
            if self.health_data.get('disk_percent', 0) > 85:
                report += "• Clean up old files and backups\n"
            if self.health_data.get('server_memory_mb', 0) > 0:
                max_memory = self.main_window.config.get('max_memory', '2G')
                if max_memory.endswith('G'):
                    max_mb = int(max_memory[:-1]) * 1024
                    if (self.health_data['server_memory_mb'] / max_mb) > 0.9:
                        report += "• Consider increasing server memory allocation\n"
            
            if not any([self.health_data.get('memory_percent', 0) > 80,
                       self.health_data.get('disk_percent', 0) > 85]):
                report += "• System is running optimally\n"
            
            messagebox.showinfo("Health Report", report)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate health report: {e}")
    
    def update_theme(self):
        """Update health tab theme"""
        super().update_theme()
        
        # Update progress bars
        if hasattr(self, 'system_cpu_bar') and self.system_cpu_bar:
            self.system_cpu_bar.update_theme()
        if hasattr(self, 'system_memory_bar') and self.system_memory_bar:
            self.system_memory_bar.update_theme()
        if hasattr(self, 'disk_usage_bar') and self.disk_usage_bar:
            self.disk_usage_bar.update_theme()
        if hasattr(self, 'server_memory_bar') and self.server_memory_bar:
            self.server_memory_bar.update_theme()
        if hasattr(self, 'server_cpu_bar') and self.server_cpu_bar:
            self.server_cpu_bar.update_theme()
        
        # Update text widgets
        theme = self.theme_manager.get_current_theme()
        if hasattr(self, 'alerts_text') and self.alerts_text:
            self.alerts_text.configure(bg=theme['bg_card'], fg=theme['text_primary'])
            self.setup_alert_tags()
        
        if hasattr(self, 'system_info_text') and self.system_info_text:
            self.system_info_text.configure(bg=theme['bg_card'], fg=theme['text_primary'])
    
    def cleanup(self):
        """Cleanup health monitoring resources"""
        self.monitoring_active = False
