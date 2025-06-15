"""
Modern styled widgets with professional proportions
"""

import tkinter as tk

class ModernProgressBar(tk.Frame):
    """Modern progress bar widget with professional styling"""
    
    def __init__(self, parent, width=200, height=12, theme_manager=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.width = width
        self.height = height
        self.theme_manager = theme_manager
        self.progress = 0
        self.max_value = 100
        
        self.setup_progress_bar()
    
    def setup_progress_bar(self):
        """Setup the progress bar with professional styling"""
        if self.theme_manager:
            theme = self.theme_manager.get_current_theme()
        else:
            from themes import get_theme
            theme = get_theme('dark')
        
        # Create container with rounded appearance
        self.configure(
            bg=theme['bg_tertiary'], 
            height=self.height, 
            width=self.width,
            relief='flat',
            bd=1,
            highlightthickness=1,
            highlightbackground=theme['border']
        )
        self.pack_propagate(False)
        
        # Progress fill
        self.fill_frame = tk.Frame(
            self, 
            bg=theme['accent'], 
            height=self.height-2,
            relief='flat'
        )
        self.fill_frame.pack(side="left", padx=1, pady=1)
    
    def set_progress(self, value, max_value=100):
        """Set progress value (0-max_value)"""
        self.progress = max(0, min(value, max_value))
        self.max_value = max_value
        self.update_progress()
    
    def update_progress(self):
        """Update progress bar visual"""
        if self.max_value > 0:
            progress_width = int((self.progress / self.max_value) * (self.width - 4))
            self.fill_frame.configure(width=max(0, progress_width))
        else:
            self.fill_frame.configure(width=0)
    
    def update_theme(self):
        """Update progress bar theme"""
        if self.theme_manager:
            theme = self.theme_manager.get_current_theme()
            self.configure(bg=theme['bg_tertiary'], highlightbackground=theme['border'])
            self.fill_frame.configure(bg=theme['accent'])

class ModernButton(tk.Button):
    """Modern styled button widget with professional proportions"""
    
    def __init__(self, parent, text="", command=None, style_type='primary', theme_manager=None, size='normal', **kwargs):
        self.style_type = style_type
        self.theme_manager = theme_manager
        self.size = size
        
        # Get theme colors
        if theme_manager:
            theme = theme_manager.get_current_theme()
        else:
            from themes import get_theme
            theme = get_theme('dark')
        
        self.colors = self._get_button_colors(theme)
        self.sizing = self._get_button_sizing(theme)
        
        super().__init__(
            parent,
            text=text,
            command=command,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=('Segoe UI', theme['font_size_normal'], 'normal'),
            relief='flat',
            borderwidth=0,
            padx=self.sizing['padx'],
            pady=self.sizing['pady'],
            height=self.sizing['height'],
            cursor='hand2',
            **kwargs
        )
        
        self.bind_events()
    
    def _get_button_colors(self, theme):
        """Get button colors based on style type"""
        color_schemes = {
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
        
        return color_schemes.get(self.style_type, color_schemes['primary'])
    
    def _get_button_sizing(self, theme):
        """Get button sizing based on size parameter"""
        if self.size == 'small':
            return {
                'padx': theme['padding_small'],
                'pady': theme['padding_small'] // 2,
                'height': 1
            }
        elif self.size == 'large':
            return {
                'padx': theme['padding_large'],
                'pady': theme['padding_medium'],
                'height': 2
            }
        else:  # normal
            return {
                'padx': theme['padding_medium'],
                'pady': theme['padding_small'],
                'height': 1
            }
    
    def bind_events(self):
        """Bind hover events"""
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
    
    def on_enter(self, event):
        """Handle mouse enter"""
        self.configure(bg=self.colors['hover'])
    
    def on_leave(self, event):
        """Handle mouse leave"""
        self.configure(bg=self.colors['bg'])
    
    def update_theme(self):
        """Update button theme"""
        if self.theme_manager:
            theme = self.theme_manager.get_current_theme()
            self.colors = self._get_button_colors(theme)
            self.configure(bg=self.colors['bg'], fg=self.colors['fg'])

class ModernEntry(tk.Entry):
    """Modern styled entry widget with professional appearance"""
    
    def __init__(self, parent, theme_manager=None, **kwargs):
        self.theme_manager = theme_manager
        
        if theme_manager:
            theme = theme_manager.get_current_theme()
        else:
            from themes import get_theme
            theme = get_theme('dark')
        
        super().__init__(
            parent,
            bg=theme['input_bg'],
            fg=theme['text_primary'],
            insertbackground=theme['text_primary'],
            relief='solid',
            bd=1,
            highlightthickness=1,
            highlightbackground=theme['input_border'],
            highlightcolor=theme['border_focus'],
            font=('Segoe UI', theme['font_size_normal']),
            **kwargs
        )
        
        # Set proper height
        self.configure(justify='left')
    
    def update_theme(self):
        """Update entry theme"""
        if self.theme_manager:
            theme = self.theme_manager.get_current_theme()
            self.configure(
                bg=theme['input_bg'],
                fg=theme['text_primary'],
                insertbackground=theme['text_primary'],
                highlightbackground=theme['input_border'],
                highlightcolor=theme['border_focus']
            )

class ModernLabel(tk.Label):
    """Modern styled label with consistent typography"""
    
    def __init__(self, parent, text="", style='normal', theme_manager=None, **kwargs):
        self.theme_manager = theme_manager
        self.label_style = style
        
        if theme_manager:
            theme = theme_manager.get_current_theme()
        else:
            from themes import get_theme
            theme = get_theme('dark')
        
        # Get font and color based on style
        font_config = self._get_font_config(theme)
        color_config = self._get_color_config(theme)
        
        super().__init__(
            parent,
            text=text,
            bg=theme['bg_secondary'],
            fg=color_config,
            font=font_config,
            **kwargs
        )
    
    def _get_font_config(self, theme):
        """Get font configuration based on style"""
        font_configs = {
            'header': ('Segoe UI', theme['font_size_header'], 'bold'),
            'subheader': ('Segoe UI', theme['font_size_large'], 'bold'),
            'normal': ('Segoe UI', theme['font_size_normal'], 'normal'),
            'small': ('Segoe UI', theme['font_size_small'], 'normal'),
            'muted': ('Segoe UI', theme['font_size_normal'], 'normal')
        }
        return font_configs.get(self.label_style, font_configs['normal'])
    
    def _get_color_config(self, theme):
        """Get color configuration based on style"""
        color_configs = {
            'header': theme['text_primary'],
            'subheader': theme['text_primary'],
            'normal': theme['text_primary'],
            'small': theme['text_secondary'],
            'muted': theme['text_muted']
        }
        return color_configs.get(self.label_style, color_configs['normal'])
    
    def update_theme(self):
        """Update label theme"""
        if self.theme_manager:
            theme = self.theme_manager.get_current_theme()
            font_config = self._get_font_config(theme)
            color_config = self._get_color_config(theme)
            self.configure(
                bg=theme['bg_secondary'],
                fg=color_config,
                font=font_config
            )
