"""
UI Helper functions
"""

import tkinter as tk

class UIHelpers:
    """Static helper methods for UI operations"""
    
    @staticmethod
    def create_modern_button(parent, text, command=None, style_type='primary', theme=None):
        """Create a modern styled button"""
        if not theme:
            from themes import get_theme
            theme = get_theme('dark')
        
        colors = {
            'primary': {
                'bg': theme['accent'],
                'hover': theme['accent_hover'],
                'fg': 'white'
            },
            'success': {
                'bg': theme['success'],
                'hover': '#45a049',
                'fg': 'white'
            },
            'danger': {
                'bg': theme['error'],
                'hover': '#da2c2c',
                'fg': 'white'
            },
            'secondary': {
                'bg': theme['bg_tertiary'],
                'hover': theme['bg_hover'],
                'fg': theme['text_primary']
            }
        }
        
        color_config = colors.get(style_type, colors['primary'])
        
        button = tk.Button(
            parent,
            text=text,
            command=command,
            bg=color_config['bg'],
            fg=color_config['fg'],
            font=('Segoe UI', 10),
            relief='flat',
            borderwidth=0,
            padx=20,
            pady=10,
            cursor='hand2'
        )
        
        # Add hover effects
        def on_enter(e):
            button.configure(bg=color_config['hover'])
        
        def on_leave(e):
            button.configure(bg=color_config['bg'])
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        
        return button
    
    @staticmethod
    def create_modern_entry(parent, textvariable=None, theme=None, **kwargs):
        """Create a modern styled entry"""
        if not theme:
            from themes import get_theme
            theme = get_theme('dark')
        
        entry = tk.Entry(
            parent,
            textvariable=textvariable,
            bg=theme['input_bg'],
            fg=theme['text_primary'],
            relief='solid',
            bd=1,
            font=('Segoe UI', 10),
            **kwargs
        )
        
        return entry
    
    @staticmethod
    def create_section_frame(parent, theme=None):
        """Create a section frame with modern styling"""
        if not theme:
            from themes import get_theme
            theme = get_theme('dark')
        
        frame = tk.Frame(
            parent,
            bg=theme['bg_card'],
            relief='solid',
            bd=1,
            highlightbackground=theme['border'],
            highlightthickness=1
        )
        
        return frame
