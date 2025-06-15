"""
Server Properties tab implementation
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from .base_tab import BaseTab
from ..components.status_card import StatusCard
from ..components.modern_widgets import ModernButton, ModernEntry, ModernLabel

class ServerPropertiesTab(BaseTab):
    """Server properties configuration tab"""
    
    def __init__(self, parent, theme_manager, main_window):
        self.main_window = main_window
        super().__init__(parent, theme_manager)
        
        # Properties manager
        self.properties_manager = main_window.server_properties_manager
        
        # Track widgets for easy access
        self.property_widgets = {}
        self.modified = False
        
        self.create_content()
        self.load_properties()
    
    def create_content(self):
        """Create server properties content"""
        theme = self.theme_manager.get_current_theme()
        
        # Main content area with scrolling
        main_frame = tk.Frame(self.tab_frame, bg=theme['bg_primary'])
        main_frame.pack(fill="both", expand=True, padx=theme['padding_large'], pady=theme['padding_large'])
        
        # Toolbar
        self.create_toolbar(main_frame)
        
        # Scrollable content area
        self.create_scrollable_content(main_frame)
        
        # Status bar
        self.create_status_bar(main_frame)
    
    def create_toolbar(self, parent):
        """Create toolbar with action buttons"""
        theme = self.theme_manager.get_current_theme()
        
        toolbar_card = StatusCard(parent, "Server Properties Manager", "⚙️", self.theme_manager)
        toolbar_card.pack(fill="x", pady=(0, theme['margin_medium']))
        
        toolbar_content = toolbar_card.get_content_frame()
        
        # Toolbar buttons
        buttons_frame = tk.Frame(toolbar_content, bg=theme['bg_card'])
        buttons_frame.pack(fill="x", padx=theme['padding_medium'], pady=theme['padding_medium'])
        
        # Left side buttons
        left_buttons = tk.Frame(buttons_frame, bg=theme['bg_card'])
        left_buttons.pack(side="left")
        
        ModernButton(left_buttons, "Load Properties", self.load_properties, "primary", self.theme_manager, "normal").pack(side="left", padx=(0, theme['margin_small']))
        ModernButton(left_buttons, "Save Properties", self.save_properties, "success", self.theme_manager, "normal").pack(side="left", padx=(0, theme['margin_small']))
        ModernButton(left_buttons, "Reset to Defaults", self.reset_to_defaults, "danger", self.theme_manager, "normal").pack(side="left")
        
        # Right side buttons
        right_buttons = tk.Frame(buttons_frame, bg=theme['bg_card'])
        right_buttons.pack(side="right")
        
        ModernButton(right_buttons, "Export", self.export_properties, "secondary", self.theme_manager, "normal").pack(side="left", padx=(0, theme['margin_small']))
        ModernButton(right_buttons, "Import", self.import_properties, "secondary", self.theme_manager, "normal").pack(side="left", padx=(0, theme['margin_small']))
        ModernButton(right_buttons, "Help", self.show_help, "secondary", self.theme_manager, "normal").pack(side="left")
        
        # Status indicator
        self.modified_label = tk.Label(buttons_frame, text="", bg=theme['bg_card'], 
                                      fg=theme['warning'], font=('Segoe UI', theme['font_size_small']))
        self.modified_label.pack(side="right", padx=(theme['padding_medium'], 0))
        
        self.register_widget(toolbar_card)
    
    def create_scrollable_content(self, parent):
        """Create scrollable content area"""
        theme = self.theme_manager.get_current_theme()
        
        # Scrollable frame container
        scroll_container = tk.Frame(parent, bg=theme['bg_primary'])
        scroll_container.pack(fill="both", expand=True, pady=(0, theme['margin_medium']))
        
        # Create canvas and scrollbar
        self.canvas = tk.Canvas(scroll_container, bg=theme['bg_primary'], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=theme['bg_primary'])
        
        # Configure scrolling
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Bind mousewheel
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        
        # Pack canvas and scrollbar
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Create property sections
        self.create_property_sections()
    
    def create_property_sections(self):
        """Create property input sections organized by category"""
        theme = self.theme_manager.get_current_theme()
        
        # Get property definitions from the properties manager
        property_definitions = self.properties_manager.property_definitions
        
        for category_name, category_info in property_definitions.items():
            # Create category card
            category_card = StatusCard(
                self.scrollable_frame, 
                category_info['name'], 
                self._get_category_icon(category_name), 
                self.theme_manager
            )
            category_card.pack(fill="x", padx=theme['margin_small'], pady=theme['margin_small'])
            
            category_content = category_card.get_content_frame()
            
            # Create property grid
            props_frame = tk.Frame(category_content, bg=theme['bg_card'])
            props_frame.pack(fill="x", padx=theme['padding_medium'], pady=theme['padding_medium'])
            
            # Create property widgets for this category
            for prop_key, prop_def in category_info['properties'].items():
                self.create_property_widget(props_frame, prop_key, prop_def)
            
            self.register_widget(category_card)
    
    def _get_category_icon(self, category_name):
        """Get icon for category"""
        icons = {
            'basic': '🏠',
            'world': '🌍',
            'performance': '⚡',
            'advanced': '🔧',
            'nether': '🔥',
            'resource_pack': '📦'
        }
        return icons.get(category_name, '⚙️')
    
    def create_property_widget(self, parent, prop_key, prop_def):
        """Create a widget for a single property"""
        theme = self.theme_manager.get_current_theme()
        
        # Create frame for this property
        prop_frame = tk.Frame(parent, bg=theme['bg_card'])
        prop_frame.pack(fill="x", pady=theme['margin_small'])
        
        # Create label with description
        label_text = prop_key.replace('-', ' ').title()
        label = ModernLabel(prop_frame, label_text, 'normal', self.theme_manager)
        label.configure(width=25, anchor="w", bg=theme['bg_card'])
        label.pack(side="left")
        
        # Create appropriate input widget based on property type
        prop_type = prop_def['type']
        
        if prop_type == 'bool':
            widget = self.create_boolean_widget(prop_frame, prop_key)
        elif prop_type == 'choice':
            widget = self.create_choice_widget(prop_frame, prop_key, prop_def['choices'])
        elif prop_type == 'int':
            widget = self.create_integer_widget(prop_frame, prop_key, prop_def)
        else:  # str
            widget = self.create_string_widget(prop_frame, prop_key)
        
        # Store widget reference
        self.property_widgets[prop_key] = {
            'widget': widget,
            'type': prop_type,
            'definition': prop_def
        }
        
        # Add description tooltip/label
        if 'description' in prop_def:
            desc_label = ModernLabel(prop_frame, f"({prop_def['description']})", 'small', self.theme_manager)
            desc_label.configure(bg=theme['bg_card'])
            desc_label.pack(side="right", padx=(theme['padding_small'], 0))
    
    def create_boolean_widget(self, parent, prop_key):
        """Create a boolean (checkbox) widget"""
        theme = self.theme_manager.get_current_theme()
        
        var = tk.BooleanVar()
        widget = tk.Checkbutton(
            parent, 
            variable=var, 
            command=lambda: self.on_property_changed(prop_key),
            bg=theme['bg_card'],
            fg=theme['text_primary'],
            selectcolor=theme['input_bg'],
            activebackground=theme['bg_card'],
            activeforeground=theme['text_primary']
        )
        widget.pack(side="left", padx=(theme['padding_small'], 0))
        
        widget.var = var
        return widget
    
    def create_choice_widget(self, parent, prop_key, choices):
        """Create a choice (combobox) widget"""
        var = tk.StringVar()
        widget = ttk.Combobox(
            parent, 
            textvariable=var, 
            values=choices, 
            state="readonly", 
            width=20,
            style='Modern.TCombobox'
        )
        widget.pack(side="left", padx=(self.theme_manager.get_current_theme()['padding_small'], 0))
        widget.bind("<<ComboboxSelected>>", lambda e: self.on_property_changed(prop_key))
        
        widget.var = var
        return widget
    
    def create_integer_widget(self, parent, prop_key, prop_def):
        """Create an integer (spinbox) widget"""
        theme = self.theme_manager.get_current_theme()
        var = tk.StringVar()
        
        # Get range if specified
        from_val = prop_def.get('range', (0, 999999))[0]
        to_val = prop_def.get('range', (0, 999999))[1]
        
        widget = tk.Spinbox(
            parent, 
            textvariable=var, 
            from_=from_val, 
            to=to_val, 
            width=15,
            bg=theme['input_bg'],
            fg=theme['text_primary'],
            buttonbackground=theme['bg_tertiary'],
            relief='solid',
            bd=1
        )
        widget.pack(side="left", padx=(theme['padding_small'], 0))
        widget.bind("<KeyRelease>", lambda e: self.on_property_changed(prop_key))
        widget.bind("<<Increment>>", lambda e: self.on_property_changed(prop_key))
        widget.bind("<<Decrement>>", lambda e: self.on_property_changed(prop_key))
        
        widget.var = var
        return widget
    
    def create_string_widget(self, parent, prop_key):
        """Create a string (entry) widget"""
        var = tk.StringVar()
        widget = ModernEntry(parent, self.theme_manager, textvariable=var, width=30)
        widget.pack(side="left", padx=(self.theme_manager.get_current_theme()['padding_small'], 0))
        widget.bind("<KeyRelease>", lambda e: self.on_property_changed(prop_key))
        
        widget.var = var
        return widget
    
    def create_status_bar(self, parent):
        """Create status bar"""
        theme = self.theme_manager.get_current_theme()
        
        status_frame = tk.Frame(parent, bg=theme['bg_secondary'])
        status_frame.pack(fill="x")
        
        status_content = tk.Frame(status_frame, bg=theme['bg_secondary'])
        status_content.pack(fill="x", padx=theme['padding_medium'], pady=theme['padding_small'])
        
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Load server properties to begin editing")
        
        status_label = ModernLabel(status_content, "", 'normal', self.theme_manager)
        status_label.configure(textvariable=self.status_var, bg=theme['bg_secondary'])
        status_label.pack(side="left")
        
        # Validation status
        self.validation_var = tk.StringVar()
        validation_label = ModernLabel(status_content, "", 'normal', self.theme_manager)
        validation_label.configure(textvariable=self.validation_var, bg=theme['bg_secondary'], fg=theme['error'])
        validation_label.pack(side="right")
    
    def on_property_changed(self, prop_key):
        """Handle property value change"""
        self.modified = True
        self.update_modified_indicator()
        
        # Validate the property
        widget_info = self.property_widgets.get(prop_key)
        if widget_info:
            try:
                value = self.get_widget_value(widget_info['widget'], widget_info['type'])
                is_valid, error_msg = self.properties_manager.validate_property(prop_key, value)
                
                if is_valid:
                    self.validation_var.set("")
                else:
                    self.validation_var.set(f"{prop_key}: {error_msg}")
            except Exception as e:
                self.validation_var.set(f"Validation error: {e}")
    
    def get_widget_value(self, widget, widget_type):
        """Get value from widget based on type"""
        if widget_type == 'bool':
            return 'true' if widget.var.get() else 'false'
        else:
            return widget.var.get()
    
    def set_widget_value(self, widget, widget_type, value):
        """Set value to widget based on type"""
        if widget_type == 'bool':
            widget.var.set(value.lower() == 'true')
        else:
            widget.var.set(value)
    
    def update_modified_indicator(self):
        """Update the modified indicator"""
        if self.modified:
            self.modified_label.configure(text="● Modified")
        else:
            self.modified_label.configure(text="")
    
    def load_properties(self):
        """Load properties from server"""
        try:
            if not hasattr(self.main_window, 'server_jar_path') or not self.main_window.server_jar_path:
                messagebox.showwarning("Warning", "Please select a server JAR file first in the Server Control tab")
                return
            
            success = self.properties_manager.load_properties(self.main_window.server_jar_path)
            
            if success:
                self.populate_widgets()
                self.status_var.set("Properties loaded successfully")
                self.modified = False
                self.update_modified_indicator()
            else:
                self.status_var.set("Failed to load properties")
                
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load properties: {e}")
    
    def save_properties(self):
        """Save properties to file"""
        try:
            if not self.validate_all_properties():
                messagebox.showerror("Validation Error", "Please fix validation errors before saving")
                return
            
            # Update properties manager with current widget values
            self.update_properties_from_widgets()
            
            success = self.properties_manager.save_properties()
            
            if success:
                self.status_var.set("Properties saved successfully")
                self.modified = False
                self.update_modified_indicator()
                messagebox.showinfo("Success", "Server properties saved successfully!")
            else:
                self.status_var.set("Failed to save properties")
                messagebox.showerror("Error", "Failed to save properties")
                
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save properties: {e}")
    
    def populate_widgets(self):
        """Populate widgets with current property values"""
        try:
            for prop_key, widget_info in self.property_widgets.items():
                value = self.properties_manager.get_property(prop_key)
                self.set_widget_value(widget_info['widget'], widget_info['type'], value)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to populate widgets: {e}")
    
    def update_properties_from_widgets(self):
        """Update properties manager with widget values"""
        for prop_key, widget_info in self.property_widgets.items():
            try:
                value = self.get_widget_value(widget_info['widget'], widget_info['type'])
                self.properties_manager.set_property(prop_key, value)
            except Exception as e:
                print(f"Error updating property {prop_key}: {e}")
    
    def validate_all_properties(self):
        """Validate all property values"""
        for prop_key, widget_info in self.property_widgets.items():
            try:
                value = self.get_widget_value(widget_info['widget'], widget_info['type'])
                is_valid, error_msg = self.properties_manager.validate_property(prop_key, value)
                if not is_valid:
                    self.validation_var.set(f"{prop_key}: {error_msg}")
                    return False
            except Exception as e:
                self.validation_var.set(f"Validation error for {prop_key}: {e}")
                return False
        
        self.validation_var.set("")
        return True
    
    def reset_to_defaults(self):
        """Reset all properties to default values"""
        try:
            if messagebox.askokcancel("Reset to Defaults", 
                                    "This will reset all properties to their default values. Continue?"):
                self.properties_manager.reset_to_defaults()
                self.populate_widgets()
                self.modified = True
                self.update_modified_indicator()
                self.status_var.set("Properties reset to defaults")
                
        except Exception as e:
            messagebox.showerror("Reset Error", f"Failed to reset properties: {e}")
    
    def export_properties(self):
        """Export properties to file"""
        try:
            filename = filedialog.asksaveasfilename(
                title="Export Server Properties",
                defaultextension=".properties",
                filetypes=[("Properties files", "*.properties"), ("Text files", "*.txt"), ("All files", "*.*")]
            )
            
            if filename:
                self.update_properties_from_widgets()
                success = self.properties_manager.export_properties(filename)
                
                if success:
                    messagebox.showinfo("Success", f"Properties exported to {filename}")
                else:
                    messagebox.showerror("Error", "Failed to export properties")
                    
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export properties: {e}")
    
    def import_properties(self):
        """Import properties from file"""
        try:
            filename = filedialog.askopenfilename(
                title="Import Server Properties",
                filetypes=[("Properties files", "*.properties"), ("Text files", "*.txt"), ("All files", "*.*")]
            )
            
            if filename:
                if messagebox.askokcancel("Import Properties", 
                                        "This will overwrite current properties. Continue?"):
                    # Import logic would go here
                    messagebox.showinfo("Info", "Import functionality not implemented yet")
                    
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import properties: {e}")
    
    def show_help(self):
        """Show help information"""
        help_text = """Server Properties Help

This tab allows you to configure Minecraft server properties:

• Load Properties: Load server.properties from the selected server directory
• Save Properties: Save current settings to server.properties
• Reset to Defaults: Reset all values to their defaults
• Export/Import: Backup and restore property configurations

Property Categories:
• Basic: Core server settings (port, MOTD, max players)
• World: World generation and gameplay settings
• Performance: Memory and performance optimization
• Advanced: Technical server settings
• Nether: Nether world settings
• Resource Pack: Resource pack configuration

Changes are marked with "● Modified" and must be saved manually.
"""
        messagebox.showinfo("Help", help_text)
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        try:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except:
            pass
