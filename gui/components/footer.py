"""
Modern footer component - Fixed Layout
"""

import tkinter as tk

class ModernFooter:
    """Modern footer with status and system info - Grid Layout"""
    
    def __init__(self, parent, theme_manager):
        self.parent = parent
        self.theme_manager = theme_manager
        self.footer_frame = None
        self.status_var = None
        self.memory_label = None
        # Note: Don't call create_footer here - let the parent handle layout
        self.create_footer_frame()
    
    def create_footer_frame(self):
        """Create the footer frame without packing it"""
        theme = self.theme_manager.get_current_theme()
        
        self.footer_frame = tk.Frame(self.parent, bg=theme['bg_secondary'], height=40)
        # Don't pack here - let parent handle with grid
        
        self.create_footer_content()
    
    def create_footer_content(self):
        """Create footer content inside the frame"""
        theme = self.theme_manager.get_current_theme()
        
        footer_content = tk.Frame(self.footer_frame, bg=theme['bg_secondary'])
        footer_content.pack(fill="both", expand=True, padx=theme['padding_large'], pady=theme['padding_small'])
        
        # Status text
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        
        status_label = tk.Label(
            footer_content,
            textvariable=self.status_var,
            font=('Segoe UI', theme['font_size_normal']),
            bg=theme['bg_secondary'],
            fg=theme['text_primary']
        )
        status_label.pack(side="left")
        
        # Memory info
        self.memory_label = tk.Label(
            footer_content,
            text="Memory: --",
            font=('Segoe UI', theme['font_size_small']),
            bg=theme['bg_secondary'],
            fg=theme['text_secondary']
        )
        self.memory_label.pack(side="right")
    
    def update_status(self, status_text):
        """Update status text"""
        if self.status_var:
            self.status_var.set(status_text)
    
    def update_memory(self, memory_text):
        """Update memory display"""
        if self.memory_label:
            self.memory_label.configure(text=memory_text)
    
    def update_theme(self):
        """Update footer theme"""
        theme = self.theme_manager.get_current_theme()
        
        if self.footer_frame:
            self.footer_frame.configure(bg=theme['bg_secondary'])
            
            for widget in self.footer_frame.winfo_children():
                self._update_widget_theme(widget, theme)
    
    def _update_widget_theme(self, widget, theme):
        """Recursively update widget themes"""
        if isinstance(widget, (tk.Frame, tk.Label)):
            widget.configure(bg=theme['bg_secondary'])
            if isinstance(widget, tk.Label):
                if 'Memory:' in widget.cget('text'):
                    widget.configure(fg=theme['text_secondary'])
                else:
                    widget.configure(fg=theme['text_primary'])
        
        for child in widget.winfo_children():
            self._update_widget_theme(child, theme)
