"""
Base tab class
"""

import tkinter as tk

class BaseTab:
    """Base class for all tabs"""
    
    def __init__(self, parent, theme_manager, **kwargs):
        self.parent = parent
        self.theme_manager = theme_manager
        self.tab_frame = None
        self.widgets = []  # Track widgets for theme updates
        
        # Create the main tab frame
        self.create_tab_frame()
    
    def create_tab_frame(self):
        """Create the main tab frame"""
        theme = self.theme_manager.get_current_theme()
        self.tab_frame = tk.Frame(self.parent, bg=theme['bg_primary'])
    
    def get_frame(self):
        """Get the tab frame"""
        return self.tab_frame
    
    def add_to_notebook(self, notebook, text):
        """Add this tab to a notebook"""
        notebook.add(self.tab_frame, text=text)
    
    def register_widget(self, widget):
        """Register a widget for theme updates"""
        self.widgets.append(widget)
    
    def update_theme(self):
        """Update theme for all widgets in this tab"""
        theme = self.theme_manager.get_current_theme()
        
        if self.tab_frame:
            self.tab_frame.configure(bg=theme['bg_primary'])
        
        # Update all registered widgets
        for widget in self.widgets:
            if hasattr(widget, 'update_theme'):
                widget.update_theme()
    
    def create_content(self):
        """Create tab content - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement create_content()")
