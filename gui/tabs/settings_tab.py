"""
Settings tab implementation
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from .base_tab import BaseTab
from ..components.status_card import StatusCard
from ..components.modern_widgets import ModernButton
from ..utils.ui_helpers import UIHelpers

class SettingsTab(BaseTab):
    """Settings tab with all configuration options"""
    
    def __init__(self, parent, theme_manager, main_window):
        self.main_window = main_window
        super().__init__(parent, theme_manager)
        
        # Initialize all setting variables
        self.init_setting_variables()
        self.create_content()
        self.load_settings_to_ui()
    
    def init_setting_variables(self):
        """Initialize all setting variables"""
        config = self.main_window.config
        
        # Java settings
        self.java_path_var = tk.StringVar(value=config.get("java_path", "java"))
        self.max_memory_var = tk.StringVar(value=config.get("max_memory", "2G"))
        self.min_memory_var = tk.StringVar(value=config.get("min_memory", ""))
        
        # Auto-start settings
        self.auto_start_server_var = tk.BooleanVar(value=config.get("auto_start_server", False))
        self.auto_start_playit_var = tk.BooleanVar(value=config.get("auto_start_playit", False))
        self.hide_server_console_var = tk.BooleanVar(value=config.get("hide_server_console", False))
        
        # Virtual desktop settings
        self.move_to_desktop2_var = tk.BooleanVar(value=config.get("move_to_desktop2_first", True))
        self.virtual_desktop_var = tk.IntVar(value=config.get("virtual_desktop", 1))
        
        # Wake detection settings
        self.wake_detection_var = tk.BooleanVar(value=config.get("wake_detection_enabled", True))
        self.auto_restart_wake_var = tk.BooleanVar(value=config.get("auto_restart_after_wake", True))
        
        # Auto-shutdown settings
        self.auto_shutdown_var = tk.BooleanVar(value=config.get("auto_shutdown_enabled", False))
        self.shutdown_hour_var = tk.StringVar(value=str(config.get("shutdown_hour", 12)))
        self.shutdown_minute_var = tk.StringVar(value=str(config.get("shutdown_minute", 0)).zfill(2))
        self.shutdown_ampm_var = tk.StringVar(value=config.get("shutdown_ampm", "AM"))
        self.shutdown_stop_server_var = tk.BooleanVar(value=config.get("shutdown_stop_server", True))
        self.shutdown_warning_var = tk.IntVar(value=config.get("shutdown_warning_minutes", 5))
        
        # Console settings
        self.console_font_size_var = tk.IntVar(value=config.get("console_font_size", 10))
        self.console_max_lines_var = tk.IntVar(value=config.get("server_log_max_lines", 1000))
        
        # Monitoring settings
        self.health_monitoring_var = tk.BooleanVar(value=config.get("health_monitoring_enabled", True))
        self.memory_optimization_var = tk.BooleanVar(value=config.get("memory_optimization_enabled", True))
        
        # Backup settings
        self.auto_backup_var = tk.BooleanVar(value=config.get("auto_backup", True))
        self.backup_interval_var = tk.DoubleVar(value=config.get("backup_interval", 3600) / 3600)
        self.max_backups_var = tk.IntVar(value=config.get("max_backup_count", 10))
        self.pause_server_backup_var = tk.BooleanVar(value=config.get("pause_server_for_backup", False))
        
        # Network settings
        self.server_port_var = tk.IntVar(value=config.get("server_port", 25565))
        
        # Advanced settings
        self.log_level_var = tk.StringVar(value=config.get("log_level", "INFO"))
    
    def create_content(self):
        """Create settings content with scrollable area"""
        theme = self.theme_manager.get_current_theme()
        
        # Create scrollable canvas
        canvas = tk.Canvas(self.tab_frame, bg=theme['bg_primary'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.tab_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=theme['bg_primary'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Add padding
        content = tk.Frame(scrollable_frame, bg=theme['bg_primary'])
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Java settings card
        self.create_java_settings_card(content)
        
        # Auto-start settings card
        self.create_autostart_settings_card(content)
        
        # Virtual desktop settings card (if available)
        if self.main_window.vd_manager.available:
            self.create_virtual_desktop_card(content)
        
        # Wake detection settings card
        self.create_wake_detection_card(content)
        
        # Auto-shutdown settings card
        self.create_auto_shutdown_card(content)
        
        # Console settings card
        self.create_console_settings_card(content)
        
        # Monitoring settings card
        self.create_monitoring_settings_card(content)
        
        # Backup settings card
        self.create_backup_settings_card(content)
        
        # Network settings card
        self.create_network_settings_card(content)
        
        # Advanced settings card
        self.create_advanced_settings_card(content)
        
        # Save buttons
        self.create_save_buttons(content)
        
        # Pack scrollable components
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel
        canvas.bind("<MouseWheel>", self._on_mousewheel)
    
    def create_java_settings_card(self, parent):
        """Create Java settings card"""
        theme = self.theme_manager.get_current_theme()
        
        java_card = StatusCard(parent, "Java Configuration", "☕", self.theme_manager)
        java_card.pack(fill="x", pady=(0, 15))
        
        java_content = java_card.get_content_frame()
        
        settings_frame = tk.Frame(java_content, bg=theme['bg_card'])
        settings_frame.pack(fill="x", padx=15, pady=15)
        
        # Java path
        java_row = tk.Frame(settings_frame, bg=theme['bg_card'])
        java_row.pack(fill="x", pady=(0, 10))
        
        tk.Label(java_row, text="Java Path:", bg=theme['bg_card'], 
                 fg=theme['text_primary'], width=15, anchor="w").pack(side="left")
        
        java_entry = UIHelpers.create_modern_entry(java_row, self.java_path_var, theme)
        java_entry.pack(side="left", fill="x", expand=True, padx=(10, 10))
        
        ModernButton(java_row, "Test Java", self.test_java, "secondary", self.theme_manager).pack(side="right")
        
        # Memory settings
        memory_row = tk.Frame(settings_frame, bg=theme['bg_card'])
        memory_row.pack(fill="x", pady=(0, 10))
        
        tk.Label(memory_row, text="Max Memory:", bg=theme['bg_card'], 
                 fg=theme['text_primary'], width=15, anchor="w").pack(side="left")
        
        max_memory_entry = UIHelpers.create_modern_entry(memory_row, self.max_memory_var, theme, width=15)
        max_memory_entry.pack(side="left", padx=(10, 10))
        
        ModernButton(memory_row, "Optimize", self.optimize_memory, "secondary", self.theme_manager).pack(side="left")
        
        # Min memory
        min_memory_row = tk.Frame(settings_frame, bg=theme['bg_card'])
        min_memory_row.pack(fill="x")
        
        tk.Label(min_memory_row, text="Min Memory:", bg=theme['bg_card'], 
                 fg=theme['text_primary'], width=15, anchor="w").pack(side="left")
        
        min_memory_entry = UIHelpers.create_modern_entry(min_memory_row, self.min_memory_var, theme, width=15)
        min_memory_entry.pack(side="left", padx=(10, 0))
        
        self.register_widget(java_card)
    
    def create_autostart_settings_card(self, parent):
        """Create auto-start settings card"""
        theme = self.theme_manager.get_current_theme()
        
        autostart_card = StatusCard(parent, "Auto-start Options", "🚀", self.theme_manager)
        autostart_card.pack(fill="x", pady=(0, 15))
        
        autostart_content = autostart_card.get_content_frame()
        
        settings_frame = tk.Frame(autostart_content, bg=theme['bg_card'])
        settings_frame.pack(fill="x", padx=15, pady=15)
        
        # Checkboxes
        server_check = tk.Checkbutton(
            settings_frame, 
            text="Auto-start server on launch",
            variable=self.auto_start_server_var,
            bg=theme['bg_card'],
            fg=theme['text_primary'],
            selectcolor=theme['input_bg'],
            activebackground=theme['bg_card'],
            activeforeground=theme['text_primary']
        )
        server_check.pack(anchor="w", pady=2)
        
        playit_check = tk.Checkbutton(
            settings_frame,
            text="Auto-start Playit.gg on launch", 
            variable=self.auto_start_playit_var,
            bg=theme['bg_card'],
            fg=theme['text_primary'],
            selectcolor=theme['input_bg'],
            activebackground=theme['bg_card'],
            activeforeground=theme['text_primary']
        )
        playit_check.pack(anchor="w", pady=2)
        
        console_check = tk.Checkbutton(
            settings_frame,
            text="Hide server console window", 
            variable=self.hide_server_console_var,
            bg=theme['bg_card'],
            fg=theme['text_primary'],
            selectcolor=theme['input_bg'],
            activebackground=theme['bg_card'],
            activeforeground=theme['text_primary']
        )
        console_check.pack(anchor="w", pady=2)
        
        self.register_widget(autostart_card)
    
    def create_virtual_desktop_card(self, parent):
        """Create virtual desktop settings card"""
        theme = self.theme_manager.get_current_theme()
        
        vd_card = StatusCard(parent, "Virtual Desktop Settings", "🖥️", self.theme_manager)
        vd_card.pack(fill="x", pady=(0, 15))
        
        vd_content = vd_card.get_content_frame()
        
        settings_frame = tk.Frame(vd_content, bg=theme['bg_card'])
        settings_frame.pack(fill="x", padx=15, pady=15)
        
        # Move to desktop 2 checkbox
        desktop2_check = tk.Checkbutton(
            settings_frame,
            text="Move to Desktop 2 first", 
            variable=self.move_to_desktop2_var,
            bg=theme['bg_card'],
            fg=theme['text_primary'],
            selectcolor=theme['input_bg'],
            activebackground=theme['bg_card'],
            activeforeground=theme['text_primary']
        )
        desktop2_check.pack(anchor="w", pady=2)
        
        # Desktop selection
        desktop_row = tk.Frame(settings_frame, bg=theme['bg_card'])
        desktop_row.pack(fill="x", pady=(10, 0))
        
        tk.Label(desktop_row, text="Target Virtual Desktop:", bg=theme['bg_card'], 
                 fg=theme['text_primary']).pack(side="left")
        
        desktop_spinbox = tk.Spinbox(
            desktop_row, 
            from_=1, 
            to=self.main_window.vd_manager.get_desktop_count(), 
            width=5, 
            textvariable=self.virtual_desktop_var,
            bg=theme['input_bg'],
            fg=theme['text_primary']
        )
        desktop_spinbox.pack(side="left", padx=5)
        
        tk.Label(desktop_row, text=f"(Available: {self.main_window.vd_manager.get_desktop_count()})", 
                 bg=theme['bg_card'], fg=theme['text_secondary']).pack(side="left", padx=5)
        
        self.register_widget(vd_card)
    
    def create_wake_detection_card(self, parent):
        """Create wake detection settings card"""
        theme = self.theme_manager.get_current_theme()
        
        wake_card = StatusCard(parent, "Wake Detection Settings", "😴", self.theme_manager)
        wake_card.pack(fill="x", pady=(0, 15))
        
        wake_content = wake_card.get_content_frame()
        
        settings_frame = tk.Frame(wake_content, bg=theme['bg_card'])
        settings_frame.pack(fill="x", padx=15, pady=15)
        
        wake_check = tk.Checkbutton(
            settings_frame,
            text="Enable wake detection", 
            variable=self.wake_detection_var,
            bg=theme['bg_card'],
            fg=theme['text_primary'],
            selectcolor=theme['input_bg'],
            activebackground=theme['bg_card'],
            activeforeground=theme['text_primary']
        )
        wake_check.pack(anchor="w", pady=2)
        
        restart_check = tk.Checkbutton(
            settings_frame,
            text="Auto-restart server after wake-up", 
            variable=self.auto_restart_wake_var,
            bg=theme['bg_card'],
            fg=theme['text_primary'],
            selectcolor=theme['input_bg'],
            activebackground=theme['bg_card'],
            activeforeground=theme['text_primary']
        )
        restart_check.pack(anchor="w", pady=2)
        
        self.register_widget(wake_card)
    
    def create_auto_shutdown_card(self, parent):
        """Create auto-shutdown settings card"""
        theme = self.theme_manager.get_current_theme()
        
        shutdown_card = StatusCard(parent, "Auto-shutdown Settings", "⏰", self.theme_manager)
        shutdown_card.pack(fill="x", pady=(0, 15))
        
        shutdown_content = shutdown_card.get_content_frame()
        
        settings_frame = tk.Frame(shutdown_content, bg=theme['bg_card'])
        settings_frame.pack(fill="x", padx=15, pady=15)
        
        # Enable checkbox
        shutdown_check = tk.Checkbutton(
            settings_frame,
            text="Enable auto-shutdown", 
            variable=self.auto_shutdown_var,
            bg=theme['bg_card'],
            fg=theme['text_primary'],
            selectcolor=theme['input_bg'],
            activebackground=theme['bg_card'],
            activeforeground=theme['text_primary']
        )
        shutdown_check.pack(anchor="w", pady=2)
        
        # Time selection
        time_frame = tk.Frame(settings_frame, bg=theme['bg_card'])
        time_frame.pack(fill="x", pady=5)
        
        tk.Label(time_frame, text="Shutdown time:", bg=theme['bg_card'], 
                 fg=theme['text_primary']).pack(side="left")
        
        hour_combo = ttk.Combobox(time_frame, textvariable=self.shutdown_hour_var, 
                                 values=[str(i) for i in range(1, 13)], width=3, style='Modern.TCombobox')
        hour_combo.pack(side="left", padx=5)
        
        tk.Label(time_frame, text=":", bg=theme['bg_card'], fg=theme['text_primary']).pack(side="left")
        
        minute_combo = ttk.Combobox(time_frame, textvariable=self.shutdown_minute_var, 
                                   values=[str(i).zfill(2) for i in range(0, 60, 5)], width=3, style='Modern.TCombobox')
        minute_combo.pack(side="left", padx=5)
        
        ampm_combo = ttk.Combobox(time_frame, textvariable=self.shutdown_ampm_var, 
                                 values=["AM", "PM"], width=3, style='Modern.TCombobox')
        ampm_combo.pack(side="left", padx=5)
        
        # Additional options
        stop_server_check = tk.Checkbutton(
            settings_frame,
            text="Stop server before shutdown", 
            variable=self.shutdown_stop_server_var,
            bg=theme['bg_card'],
            fg=theme['text_primary'],
            selectcolor=theme['input_bg'],
            activebackground=theme['bg_card'],
            activeforeground=theme['text_primary']
        )
        stop_server_check.pack(anchor="w", pady=2)
        
        # Warning time
        warning_frame = tk.Frame(settings_frame, bg=theme['bg_card'])
        warning_frame.pack(fill="x", pady=5)
        
        tk.Label(warning_frame, text="Warning time (minutes):", bg=theme['bg_card'], 
                 fg=theme['text_primary']).pack(side="left")
        
        warning_spinbox = tk.Spinbox(warning_frame, from_=1, to=60, width=5, 
                                    textvariable=self.shutdown_warning_var,
                                    bg=theme['input_bg'], fg=theme['text_primary'])
        warning_spinbox.pack(side="left", padx=5)
        
        self.register_widget(shutdown_card)
    
    def create_console_settings_card(self, parent):
        """Create console settings card"""
        theme = self.theme_manager.get_current_theme()
        
        console_card = StatusCard(parent, "Console Settings", "💻", self.theme_manager)
        console_card.pack(fill="x", pady=(0, 15))
        
        console_content = console_card.get_content_frame()
        
        settings_frame = tk.Frame(console_content, bg=theme['bg_card'])
        settings_frame.pack(fill="x", padx=15, pady=15)
        
        # Font size
        font_frame = tk.Frame(settings_frame, bg=theme['bg_card'])
        font_frame.pack(fill="x", pady=2)
        
        tk.Label(font_frame, text="Font Size:", bg=theme['bg_card'], 
                 fg=theme['text_primary'], width=15, anchor="w").pack(side="left")
        
        font_spinbox = tk.Spinbox(font_frame, from_=8, to=16, width=5, 
                                 textvariable=self.console_font_size_var,
                                 bg=theme['input_bg'], fg=theme['text_primary'])
        font_spinbox.pack(side="left", padx=5)
        
        # Max lines
        lines_frame = tk.Frame(settings_frame, bg=theme['bg_card'])
        lines_frame.pack(fill="x", pady=2)
        
        tk.Label(lines_frame, text="Max Lines:", bg=theme['bg_card'], 
                 fg=theme['text_primary'], width=15, anchor="w").pack(side="left")
        
        lines_spinbox = tk.Spinbox(lines_frame, from_=100, to=5000, width=8, 
                                  textvariable=self.console_max_lines_var,
                                  bg=theme['input_bg'], fg=theme['text_primary'])
        lines_spinbox.pack(side="left", padx=5)
        
        self.register_widget(console_card)
    
    def create_monitoring_settings_card(self, parent):
        """Create monitoring settings card"""
        theme = self.theme_manager.get_current_theme()
        
        monitoring_card = StatusCard(parent, "Monitoring Settings", "📊", self.theme_manager)
        monitoring_card.pack(fill="x", pady=(0, 15))
        
        monitoring_content = monitoring_card.get_content_frame()
        
        settings_frame = tk.Frame(monitoring_content, bg=theme['bg_card'])
        settings_frame.pack(fill="x", padx=15, pady=15)
        
        health_check = tk.Checkbutton(
            settings_frame,
            text="Enable health monitoring", 
            variable=self.health_monitoring_var,
            bg=theme['bg_card'],
            fg=theme['text_primary'],
            selectcolor=theme['input_bg'],
            activebackground=theme['bg_card'],
            activeforeground=theme['text_primary']
        )
        health_check.pack(anchor="w", pady=2)
        
        memory_check = tk.Checkbutton(
            settings_frame,
            text="Enable memory optimization", 
            variable=self.memory_optimization_var,
            bg=theme['bg_card'],
            fg=theme['text_primary'],
            selectcolor=theme['input_bg'],
            activebackground=theme['bg_card'],
            activeforeground=theme['text_primary']
        )
        memory_check.pack(anchor="w", pady=2)
        
        self.register_widget(monitoring_card)
    
    def create_backup_settings_card(self, parent):
        """Create backup settings card"""
        theme = self.theme_manager.get_current_theme()
        
        backup_card = StatusCard(parent, "Backup Settings", "💾", self.theme_manager)
        backup_card.pack(fill="x", pady=(0, 15))
        
        backup_content = backup_card.get_content_frame()
        
        settings_frame = tk.Frame(backup_content, bg=theme['bg_card'])
        settings_frame.pack(fill="x", padx=15, pady=15)
        
        # Auto backup checkbox
        auto_backup_check = tk.Checkbutton(
            settings_frame,
            text="Enable automatic backups", 
            variable=self.auto_backup_var,
            bg=theme['bg_card'],
            fg=theme['text_primary'],
            selectcolor=theme['input_bg'],
            activebackground=theme['bg_card'],
            activeforeground=theme['text_primary']
        )
        auto_backup_check.pack(anchor="w", pady=2)
        
        # Backup interval
        interval_frame = tk.Frame(settings_frame, bg=theme['bg_card'])
        interval_frame.pack(fill="x", pady=5)
        
        tk.Label(interval_frame, text="Backup interval (hours):", bg=theme['bg_card'], 
                 fg=theme['text_primary']).pack(side="left")
        
        interval_spinbox = tk.Spinbox(interval_frame, from_=0.5, to=24, increment=0.5, width=10, 
                                     textvariable=self.backup_interval_var,
                                     bg=theme['input_bg'], fg=theme['text_primary'])
        interval_spinbox.pack(side="left", padx=5)
        
        # Max backups
        max_frame = tk.Frame(settings_frame, bg=theme['bg_card'])
        max_frame.pack(fill="x", pady=5)
        
        tk.Label(max_frame, text="Maximum backups to keep:", bg=theme['bg_card'], 
                 fg=theme['text_primary']).pack(side="left")
        
        max_spinbox = tk.Spinbox(max_frame, from_=1, to=50, width=10, 
                                textvariable=self.max_backups_var,
                                bg=theme['input_bg'], fg=theme['text_primary'])
        max_spinbox.pack(side="left", padx=5)
        
        # Pause server option
        pause_check = tk.Checkbutton(
            settings_frame,
            text="Pause server during backup (safer but causes lag)", 
            variable=self.pause_server_backup_var,
            bg=theme['bg_card'],
            fg=theme['text_primary'],
            selectcolor=theme['input_bg'],
            activebackground=theme['bg_card'],
            activeforeground=theme['text_primary']
        )
        pause_check.pack(anchor="w", pady=2)
        
        self.register_widget(backup_card)
    
    def create_network_settings_card(self, parent):
        """Create network settings card"""
        theme = self.theme_manager.get_current_theme()
        
        network_card = StatusCard(parent, "Network Settings", "🌐", self.theme_manager)
        network_card.pack(fill="x", pady=(0, 15))
        
        network_content = network_card.get_content_frame()
        
        settings_frame = tk.Frame(network_content, bg=theme['bg_card'])
        settings_frame.pack(fill="x", padx=15, pady=15)
        
        # Server port
        port_frame = tk.Frame(settings_frame, bg=theme['bg_card'])
        port_frame.pack(fill="x", pady=2)
        
        tk.Label(port_frame, text="Server Port:", bg=theme['bg_card'], 
                 fg=theme['text_primary'], width=15, anchor="w").pack(side="left")
        
        port_spinbox = tk.Spinbox(port_frame, from_=1024, to=65535, width=10, 
                                 textvariable=self.server_port_var,
                                 bg=theme['input_bg'], fg=theme['text_primary'])
        port_spinbox.pack(side="left", padx=5)
        
        self.register_widget(network_card)
    
    def create_advanced_settings_card(self, parent):
        """Create advanced settings card"""
        theme = self.theme_manager.get_current_theme()
        
        advanced_card = StatusCard(parent, "Advanced Settings", "⚙️", self.theme_manager)
        advanced_card.pack(fill="x", pady=(0, 15))
        
        advanced_content = advanced_card.get_content_frame()
        
        settings_frame = tk.Frame(advanced_content, bg=theme['bg_card'])
        settings_frame.pack(fill="x", padx=15, pady=15)
        
        # Log level
        log_frame = tk.Frame(settings_frame, bg=theme['bg_card'])
        log_frame.pack(fill="x", pady=2)
        
        tk.Label(log_frame, text="Log Level:", bg=theme['bg_card'], 
                 fg=theme['text_primary'], width=15, anchor="w").pack(side="left")
        
        log_combo = ttk.Combobox(log_frame, textvariable=self.log_level_var, 
                                values=["DEBUG", "INFO", "WARNING", "ERROR"], 
                                state="readonly", width=10, style='Modern.TCombobox')
        log_combo.pack(side="left", padx=5)
        
        self.register_widget(advanced_card)
    
    def create_save_buttons(self, parent):
        """Create save and action buttons"""
        theme = self.theme_manager.get_current_theme()
        
        buttons_frame = tk.Frame(parent, bg=theme['bg_primary'])
        buttons_frame.pack(fill="x", pady=(20, 0))
        
        ModernButton(buttons_frame, "Save Settings", self.save_settings, "success", self.theme_manager).pack(side="left", padx=(0, 10))
        ModernButton(buttons_frame, "Reset to Defaults", self.reset_to_defaults, "danger", self.theme_manager).pack(side="left", padx=(0, 10))
        ModernButton(buttons_frame, "Export Settings", self.export_settings, "secondary", self.theme_manager).pack(side="left", padx=(0, 10))
        ModernButton(buttons_frame, "Import Settings", self.import_settings, "secondary", self.theme_manager).pack(side="left")
    
    def load_settings_to_ui(self):
        """Load settings from config to UI variables"""
        # This is already done in init_setting_variables
        pass
    
    def save_settings(self):
        """Save all settings"""
        try:
            config = self.main_window.config
            
            # Java settings
            config.set("java_path", self.java_path_var.get())
            config.set("max_memory", self.max_memory_var.get())
            config.set("min_memory", self.min_memory_var.get())
            
            # Auto-start settings
            config.set("auto_start_server", self.auto_start_server_var.get())
            config.set("auto_start_playit", self.auto_start_playit_var.get())
            config.set("hide_server_console", self.hide_server_console_var.get())
            
            # Virtual desktop settings
            if hasattr(self, 'move_to_desktop2_var'):
                config.set("move_to_desktop2_first", self.move_to_desktop2_var.get())
            if hasattr(self, 'virtual_desktop_var'):
                config.set("virtual_desktop", self.virtual_desktop_var.get())
            
            # Wake detection settings
            config.set("wake_detection_enabled", self.wake_detection_var.get())
            config.set("auto_restart_after_wake", self.auto_restart_wake_var.get())
            
            # Auto-shutdown settings
            config.set("auto_shutdown_enabled", self.auto_shutdown_var.get())
            config.set("shutdown_hour", int(self.shutdown_hour_var.get()))
            config.set("shutdown_minute", int(self.shutdown_minute_var.get()))
            config.set("shutdown_ampm", self.shutdown_ampm_var.get())
            config.set("shutdown_stop_server", self.shutdown_stop_server_var.get())
            config.set("shutdown_warning_minutes", self.shutdown_warning_var.get())
            
            # Console settings
            config.set("console_font_size", self.console_font_size_var.get())
            config.set("server_log_max_lines", self.console_max_lines_var.get())
            
            # Monitoring settings
            config.set("health_monitoring_enabled", self.health_monitoring_var.get())
            config.set("memory_optimization_enabled", self.memory_optimization_var.get())
            
            # Backup settings
            config.set("auto_backup", self.auto_backup_var.get())
            config.set("backup_interval", int(self.backup_interval_var.get() * 3600))
            config.set("max_backup_count", self.max_backups_var.get())
            config.set("pause_server_for_backup", self.pause_server_backup_var.get())
            
            # Network settings
            config.set("server_port", self.server_port_var.get())
            
            # Advanced settings
            config.set("log_level", self.log_level_var.get())
            
            # Save to file
            success = config.save_config()
            
            if success:
                messagebox.showinfo("Success", "Settings saved successfully!")
                self.main_window.footer.update_status("Settings saved successfully")
            else:
                messagebox.showerror("Error", "Failed to save settings")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        try:
            if messagebox.askokcancel("Reset Settings", "Reset all settings to defaults?\n\nThis cannot be undone."):
                self.main_window.config.reset_to_defaults()
                self.init_setting_variables()  # Reload variables with defaults
                messagebox.showinfo("Success", "Settings reset to defaults")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reset settings: {e}")
    
    def export_settings(self):
        """Export settings to file"""
        try:
            filename = filedialog.asksaveasfilename(
                title="Export Settings",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                import shutil
                shutil.copy2(self.main_window.config.config_path, filename)
                messagebox.showinfo("Success", f"Settings exported to {filename}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export settings: {e}")
    
    def import_settings(self):
        """Import settings from file"""
        try:
            filename = filedialog.askopenfilename(
                title="Import Settings",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                if messagebox.askokcancel("Import Settings", "Import settings from file?\n\nCurrent settings will be overwritten."):
                    import shutil
                    shutil.copy2(filename, self.main_window.config.config_path)
                    
                    # Reload config and update UI
                    self.main_window.config = self.main_window.config.__class__()
                    self.init_setting_variables()
                    
                    messagebox.showinfo("Success", "Settings imported successfully")
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import settings: {e}")
    
    def test_java(self):
        """Test Java installation"""
        try:
            import subprocess
            java_path = self.java_path_var.get()
            
            result = subprocess.run([java_path, "-version"], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                version_info = result.stderr or result.stdout
                messagebox.showinfo("Java Test", f"Java is working!\n\n{version_info}")
            else:
                messagebox.showerror("Java Test Failed", f"Java test failed: {result.stderr}")
                
        except Exception as e:
            messagebox.showerror("Java Test Failed", f"Java test failed: {e}")
    
    def optimize_memory(self):
        """Optimize memory settings based on system"""
        try:
            if hasattr(self.main_window, 'memory_manager'):
                suggestions = self.main_window.memory_manager.optimize_memory_settings()
                
                if messagebox.askokcancel(
                    "Memory Optimization", 
                    f"Suggested settings:\nMax Memory: {suggestions['suggested_max_memory']}\nMin Memory: {suggestions['suggested_min_memory']}\n\n{suggestions['reason']}\n\nApply these settings?"
                ):
                    self.max_memory_var.set(suggestions['suggested_max_memory'])
                    self.min_memory_var.set(suggestions['suggested_min_memory'])
            else:
                messagebox.showinfo("Info", "Memory optimization feature not available")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to optimize memory settings: {e}")
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        try:
            event.widget.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except:
            pass
