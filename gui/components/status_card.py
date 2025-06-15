"""
Status card component with professional styling
"""

import tkinter as tk

class StatusCard:
    """Reusable status card component with professional proportions"""
    
    def __init__(self, parent, title, icon="📊", theme_manager=None):
        self.parent = parent
        self.title = title
        self.icon = icon
        self.theme_manager = theme_manager
        self.card_frame = None
        self.content_frame = None
        self.create_card()
    
    def create_card(self):
        """Create the status card with professional styling"""
        if not self.theme_manager:
            from themes import get_theme
            theme = get_theme('dark')
        else:
            theme = self.theme_manager.get_current_theme()
        
        # Main card frame with professional styling
        self.card_frame = tk.Frame(
            self.parent,
            bg=theme['bg_card'],
            relief='solid',
            bd=1,
            highlightbackground=theme['border'],
            highlightthickness=1
        )
        
        # Card header with proper proportions
        header = tk.Frame(self.card_frame, bg=theme['bg_tertiary'], height=40)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        header_content = tk.Frame(header, bg=theme['bg_tertiary'])
        header_content.pack(fill="both", expand=True, 
                           padx=theme['padding_medium'], 
                           pady=theme['padding_small'])
        
        # Icon with proper spacing
        icon_label = tk.Label(
            header_content,
            text=self.icon,
            font=('Segoe UI', theme['font_size_header']),
            bg=theme['bg_tertiary'],
            fg=theme['accent']
        )
        icon_label.pack(side="left")
        
        # Title with professional typography
        title_label = tk.Label(
            header_content,
            text=self.title,
            font=('Segoe UI', theme['font_size_large'], 'bold'),
            bg=theme['bg_tertiary'],
            fg=theme['text_primary']
        )
        title_label.pack(side="left", padx=(theme['padding_small'], 0))
        
        # Content area with proper spacing
        self.content_frame = tk.Frame(self.card_frame, bg=theme['bg_card'])
        
        return self.card_frame
    
    def get_content_frame(self):
        """Get the content frame for adding widgets"""
        if self.content_frame:
            self.content_frame.pack(fill="both", expand=True)
        return self.content_frame
    
    def pack(self, **kwargs):
        """Pack the card frame"""
        if self.card_frame:
            self.card_frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Grid the card frame"""
        if self.card_frame:
            self.card_frame.grid(**kwargs)
    
    def update_theme(self):
        """Update card theme"""
        if not self.theme_manager:
            return
            
        theme = self.theme_manager.get_current_theme()
        
        def update_widget_theme(widget):
            if isinstance(widget, tk.Frame):
                if widget == self.card_frame:
                    widget.configure(bg=theme['bg_card'], highlightbackground=theme['border'])
                elif widget.cget('height') == 40:  # Header frame
                    widget.configure(bg=theme['bg_tertiary'])
                else:
                    widget.configure(bg=theme['bg_card'])
            elif isinstance(widget, tk.Label):
                if widget.cget('text') == self.icon:
                    widget.configure(bg=theme['bg_tertiary'], fg=theme['accent'])
                elif widget.cget('text') == self.title:
                    widget.configure(bg=theme['bg_tertiary'], fg=theme['text_primary'])
                else:
                    widget.configure(bg=theme['bg_card'], fg=theme['text_primary'])
            
            for child in widget.winfo_children():
                update_widget_theme(child)
        
        if self.card_frame:
            update_widget_theme(self.card_frame)
