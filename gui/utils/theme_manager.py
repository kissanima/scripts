"""
Theme management for the GUI
"""

import tkinter as tk
from tkinter import ttk
from themes import get_theme, get_theme_names

class ThemeManager:
    """Manages theme switching and application"""
    
    def __init__(self, config):
        self.config = config
        self.current_theme_name = config.get("ui_theme", "dark")
        self.current_theme = get_theme(self.current_theme_name)
        self.style = ttk.Style()
        self.setup_styles()
    
    def setup_styles(self):
        """Setup TTK styles for current theme"""
        theme = self.current_theme
        
        # Use clam theme as base
        self.style.theme_use('clam')
        
        # Configure notebook (tabs)
        self.style.configure(
            'Modern.TNotebook',
            background=theme['bg_primary'],
            borderwidth=0,
            tabmargins=[0, 0, 0, 0]
        )
        
        self.style.configure(
            'Modern.TNotebook.Tab',
            background=theme['bg_secondary'],
            foreground=theme['text_secondary'],
            padding=[20, 12],
            font=('Segoe UI', 10),
            borderwidth=0
        )
        
        self.style.map(
            'Modern.TNotebook.Tab',
            background=[
                ('active', theme['bg_hover']),
                ('selected', theme['accent'])
            ],
            foreground=[
                ('selected', 'white')
            ]
        )
        
        # Configure other TTK widgets
        self.style.configure(
            'Modern.TFrame',
            background=theme['bg_secondary'],
            borderwidth=1,
            relief='solid'
        )
        
        self.style.configure(
            'Modern.TLabel',
            background=theme['bg_secondary'],
            foreground=theme['text_primary'],
            font=('Segoe UI', 10)
        )
        
        self.style.configure(
            'Modern.TButton',
            background=theme['button_bg'],
            foreground='white',
            font=('Segoe UI', 10),
            padding=[15, 8],
            borderwidth=0
        )
        
        self.style.map(
            'Modern.TButton',
            background=[('active', theme['button_hover'])]
        )
        
        self.style.configure(
            'Modern.TEntry',
            fieldbackground=theme['input_bg'],
            foreground=theme['text_primary'],
            bordercolor=theme['input_border'],
            focuscolor=theme['border_focus'],
            font=('Segoe UI', 10),
            borderwidth=1
        )
        
        self.style.configure(
            'Modern.TCombobox',
            fieldbackground=theme['input_bg'],
            foreground=theme['text_primary'],
            bordercolor=theme['input_border'],
            focuscolor=theme['border_focus'],
            font=('Segoe UI', 10),
            borderwidth=1
        )
    
    def change_theme(self, theme_name):
        """Change to a different theme"""
        self.current_theme_name = theme_name
        self.current_theme = get_theme(theme_name)
        self.config.set("ui_theme", theme_name)
        self.setup_styles()
    
    def get_current_theme(self):
        """Get current theme dictionary"""
        return self.current_theme
    
    def get_theme_names(self):
        """Get available theme names"""
        return get_theme_names()
