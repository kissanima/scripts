"""
Modern header component - Fixed Layout
"""

import tkinter as tk
from tkinter import ttk

class ModernHeader:
    """Modern header with title and status indicators - Grid Layout"""
    
    def __init__(self, parent, theme_manager, version="1.0.0"):
        self.parent = parent
        self.theme_manager = theme_manager
        self.version = version
        self.header_frame = None
        self.server_status_label = None
        self.theme_combo = None
        self.theme_var = None
        self.create_header_frame()
    
    def create_header_frame(self):
        """Create the header frame without packing it"""
        theme = self.theme_manager.get_current_theme()
        
        self.header_frame = tk.Frame(self.parent, bg=theme['bg_secondary'], height=80)
        # Don't pack here - let parent handle with grid
        
        self.create_header_content()
    
    def create_header_content(self):
        """Create header content inside the frame"""
        theme = self.theme_manager.get_current_theme()
        
        # Header content
        header_content = tk.Frame(self.header_frame, bg=theme['bg_secondary'])
        header_content.pack(fill="both", expand=True, padx=theme['padding_large'], pady=theme['padding_medium'])
        
        # Title section
        title_frame = tk.Frame(header_content, bg=theme['bg_secondary'])
        title_frame.pack(side="left", fill="y")
        
        title_label = tk.Label(
            title_frame,
            text="🎮 Minecraft Server Manager",
            font=('Segoe UI', theme['font_size_header'], 'bold'),
            bg=theme['bg_secondary'],
            fg=theme['text_primary']
        )
        title_label.pack(anchor="w")
        
        subtitle_label = tk.Label(
            title_frame,
            text=f"Version {self.version} • Modern Interface",
            font=('Segoe UI', theme['font_size_normal']),
            bg=theme['bg_secondary'],
            fg=theme['text_secondary']
        )
        subtitle_label.pack(anchor="w")
        
        # Status section
        status_frame = tk.Frame(header_content, bg=theme['bg_secondary'])
        status_frame.pack(side="right", fill="y")
        
        # Server status
        self.server_status_label = tk.Label(
            status_frame,
            text="● Server: Stopped",
            font=('Segoe UI', theme['font_size_normal']),
            bg=theme['bg_secondary'],
            fg=theme['text_muted']
        )
        self.server_status_label.pack(anchor="e")
        
        # Theme selector
        theme_frame = tk.Frame(status_frame, bg=theme['bg_secondary'])
        theme_frame.pack(anchor="e", pady=(theme['margin_small'], 0))
        
        tk.Label(
            theme_frame,
            text="Theme:",
            font=('Segoe UI', theme['font_size_small']),
            bg=theme['bg_secondary'],
            fg=theme['text_secondary']
        ).pack(side="left")
        
        self.theme_var = tk.StringVar(value=self.theme_manager.current_theme_name)
        self.theme_combo = ttk.Combobox(
            theme_frame,
            textvariable=self.theme_var,
            values=self.theme_manager.get_theme_names(),
            state="readonly",
            width=10,
            style='Modern.TCombobox'
        )
        self.theme_combo.pack(side="left", padx=(theme['margin_small'], 0))
    
    def update_server_status(self, status, color=None):
        """Update server status display"""
        theme = self.theme_manager.get_current_theme()
        if not color:
            color = theme['text_muted']
        
        if self.server_status_label:
            self.server_status_label.configure(text=f"● Server: {status}", fg=color)
    
    def bind_theme_change(self, callback):
        """Bind theme change event"""
        if self.theme_combo:
            self.theme_combo.bind("<<ComboboxSelected>>", callback)
    
    def update_theme(self):
        """Update header theme"""
        theme = self.theme_manager.get_current_theme()
        
        def update_widget_theme(widget, bg_key='bg_secondary'):
            if isinstance(widget, (tk.Frame, tk.Label)):
                widget.configure(bg=theme[bg_key])
                if isinstance(widget, tk.Label):
                    # Determine text color based on widget purpose
                    text = widget.cget('text')
                    if 'Server:' in text:
                        widget.configure(fg=theme['text_muted'])
                    elif 'Theme:' in text:
                        widget.configure(fg=theme['text_secondary'])
                    elif 'Version' in text:
                        widget.configure(fg=theme['text_secondary'])
                    else:
                        widget.configure(fg=theme['text_primary'])
        
        # Recursively update all widgets
        def update_all_widgets(widget):
            update_widget_theme(widget)
            for child in widget.winfo_children():
                update_all_widgets(child)
        
        if self.header_frame:
            update_all_widgets(self.header_frame)
