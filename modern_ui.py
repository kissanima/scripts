"""
Modern UI styling and components
"""

import tkinter as tk
from tkinter import ttk
from themes import get_theme

class ModernStyle:
    """Modern styling for tkinter widgets"""
    
    def __init__(self, theme_name='dark'):
        self.theme_name = theme_name
        self.theme = get_theme(theme_name)
        self.style = ttk.Style()
        self.setup_styles()
    
    def update_theme(self, theme_name):
        """Update the current theme"""
        self.theme_name = theme_name
        self.theme = get_theme(theme_name)
        self.setup_styles()
    
    def setup_styles(self):
        """Setup all modern styles"""
        theme = self.theme
        
        # Configure notebook (tabs)
        self.style.theme_use('clam')
        
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
                ('selected', 'white' if theme['accent'] == theme['accent'] else theme['text_primary'])
            ]
        )
        
        # Configure frames
        self.style.configure(
            'Modern.TFrame',
            background=theme['bg_secondary'],
            borderwidth=1,
            relief='solid'
        )
        
        self.style.configure(
            'Card.TFrame',
            background=theme['bg_card'],
            borderwidth=1,
            relief='solid'
        )
        
        # Configure labels
        self.style.configure(
            'Modern.TLabel',
            background=theme['bg_secondary'],
            foreground=theme['text_primary'],
            font=('Segoe UI', 10)
        )
        
        self.style.configure(
            'Title.TLabel',
            background=theme['bg_secondary'],
            foreground=theme['text_primary'],
            font=('Segoe UI', 14, 'bold')
        )
        
        self.style.configure(
            'Subtitle.TLabel',
            background=theme['bg_secondary'],
            foreground=theme['text_secondary'],
            font=('Segoe UI', 11)
        )
        
        # Configure buttons
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
        
        # Configure entries
        self.style.configure(
            'Modern.TEntry',
            fieldbackground=theme['input_bg'],
            foreground=theme['text_primary'],
            bordercolor=theme['input_border'],
            focuscolor=theme['border_focus'],
            font=('Segoe UI', 10),
            borderwidth=1
        )
        
        # Configure combobox
        self.style.configure(
            'Modern.TCombobox',
            fieldbackground=theme['input_bg'],
            foreground=theme['text_primary'],
            bordercolor=theme['input_border'],
            focuscolor=theme['border_focus'],
            font=('Segoe UI', 10),
            borderwidth=1
        )
        
        # Configure treeview
        self.style.configure(
            'Modern.Treeview',
            background=theme['bg_card'],
            foreground=theme['text_primary'],
            fieldbackground=theme['bg_card'],
            borderwidth=1,
            font=('Segoe UI', 10)
        )
        
        self.style.configure(
            'Modern.Treeview.Heading',
            background=theme['bg_tertiary'],
            foreground=theme['text_primary'],
            font=('Segoe UI', 10, 'bold')
        )

def create_card_frame(parent, style_manager):
    """Create a modern card-style frame"""
    theme = style_manager.theme
    
    frame = tk.Frame(
        parent,
        bg=theme['bg_card'],
        relief='solid',
        bd=1,
        highlightbackground=theme['border'],
        highlightthickness=1
    )
    return frame

def create_modern_button(parent, text, command=None, style_type='primary'):
    """Create a modern styled button"""
    # Get current theme from a global or pass it as parameter
    theme = get_theme('dark')  # Default, should be dynamic
    
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

def create_status_badge(parent, text, status_type='info'):
    """Create a status badge"""
    theme = get_theme('dark')  # Should be dynamic
    
    colors = {
        'success': theme['success'],
        'warning': theme['warning'],
        'error': theme['error'],
        'info': theme['info']
    }
    
    color = colors.get(status_type, colors['info'])
    
    badge = tk.Label(
        parent,
        text=text,
        bg=color,
        fg='white',
        font=('Segoe UI', 9, 'bold'),
        padx=8,
        pady=2
    )
    
    return badge
