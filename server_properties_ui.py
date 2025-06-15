"""
Server Properties UI for Minecraft Server Manager
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
from typing import Dict, Any
from server_properties_manager import ServerPropertiesManager
from error_handler import ErrorHandler, ErrorSeverity

class ServerPropertiesUI:
    """UI for editing server.properties"""
    
    def __init__(self, parent_notebook, server_properties_manager: ServerPropertiesManager, error_handler: ErrorHandler):
        self.parent_notebook = parent_notebook
        self.properties_manager = server_properties_manager
        self.error_handler = error_handler
        self.widgets = {}  # Store widget references
        self.modified = False
        
        # Create the main tab
        self.create_properties_tab()
    
    def create_properties_tab(self):
        """Create the server properties configuration tab"""
        # Create main frame
        self.properties_frame = ttk.Frame(self.parent_notebook)
        self.parent_notebook.add(self.properties_frame, text="Server Properties")
        
        # Create toolbar
        self.create_toolbar()
        
        # Create scrollable content area
        self.create_scrollable_content()
        
        # Create property sections
        self.create_property_sections()
        
        # Create status bar
        self.create_status_bar()
    
    def create_toolbar(self):
        """Create toolbar with action buttons"""
        toolbar_frame = ttk.Frame(self.properties_frame)
        toolbar_frame.pack(fill="x", padx=10, pady=5)
        
        # Load/Save buttons
        ttk.Button(toolbar_frame, text="Load Properties", command=self.load_properties).pack(side="left", padx=5)
        ttk.Button(toolbar_frame, text="Save Properties", command=self.save_properties).pack(side="left", padx=5)
        ttk.Button(toolbar_frame, text="Reset to Defaults", command=self.reset_to_defaults).pack(side="left", padx=5)
        
        # Separator
        ttk.Separator(toolbar_frame, orient="vertical").pack(side="left", fill="y", padx=10)
        
        # Import/Export buttons
        ttk.Button(toolbar_frame, text="Export", command=self.export_properties).pack(side="left", padx=5)
        ttk.Button(toolbar_frame, text="Import", command=self.import_properties).pack(side="left", padx=5)
        
        # Help button
        ttk.Button(toolbar_frame, text="Help", command=self.show_help).pack(side="right", padx=5)
        
        # Status indicator
        self.modified_label = ttk.Label(toolbar_frame, text="", foreground="orange")
        self.modified_label.pack(side="right", padx=10)
    
    def create_scrollable_content(self):
        """Create scrollable content area"""
        # Create canvas and scrollbar
        self.canvas = tk.Canvas(self.properties_frame)
        self.scrollbar = ttk.Scrollbar(self.properties_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
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
        self.canvas.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=5)
        self.scrollbar.pack(side="right", fill="y", pady=5, padx=(0, 10))
    
    def create_property_sections(self):
        """Create property input sections organized by category"""
        self.widgets = {}
        
        for category_name, category_info in self.properties_manager.property_definitions.items():
            # Create category frame
            category_frame = ttk.LabelFrame(
                self.scrollable_frame, 
                text=category_info['name'], 
                padding="10"
            )
            category_frame.pack(fill="x", padx=10, pady=5)
            
            # Create property widgets for this category
            for prop_key, prop_def in category_info['properties'].items():
                self.create_property_widget(category_frame, prop_key, prop_def)
    
    def create_property_widget(self, parent, prop_key: str, prop_def: Dict[str, Any]):
        """Create a widget for a single property"""
        # Create frame for this property
        prop_frame = ttk.Frame(parent)
        prop_frame.pack(fill="x", pady=2)
        
        # Create label with description
        label_text = prop_key.replace('-', ' ').title()
        label = ttk.Label(prop_frame, text=label_text, width=25, anchor="w")
        label.pack(side="left", padx=(0, 10))
        
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
        self.widgets[prop_key] = widget
        
        # Add description tooltip/label
        if 'description' in prop_def:
            desc_label = ttk.Label(prop_frame, text=f"({prop_def['description']})", 
                                 foreground="gray", font=("TkDefaultFont", 8))
            desc_label.pack(side="right", padx=(10, 0))
    
    def create_boolean_widget(self, parent, prop_key: str):
        """Create a boolean (checkbox) widget"""
        var = tk.BooleanVar()
        widget = ttk.Checkbutton(parent, variable=var, command=lambda: self.on_property_changed(prop_key))
        widget.pack(side="left")
        
        # Store the variable with the widget for easy access
        widget.var = var
        return widget
    
    def create_choice_widget(self, parent, prop_key: str, choices: list):
        """Create a choice (combobox) widget"""
        var = tk.StringVar()
        widget = ttk.Combobox(parent, textvariable=var, values=choices, state="readonly", width=20)
        widget.pack(side="left")
        widget.bind("<<ComboboxSelected>>", lambda e: self.on_property_changed(prop_key))
        
        widget.var = var
        return widget
    
    def create_integer_widget(self, parent, prop_key: str, prop_def: Dict[str, Any]):
        """Create an integer (spinbox) widget"""
        var = tk.StringVar()
        
        # Get range if specified
        from_val = prop_def.get('range', (0, 999999))[0]
        to_val = prop_def.get('range', (0, 999999))[1]
        
        widget = ttk.Spinbox(parent, textvariable=var, from_=from_val, to=to_val, width=15)
        widget.pack(side="left")
        widget.bind("<KeyRelease>", lambda e: self.on_property_changed(prop_key))
        widget.bind("<<Increment>>", lambda e: self.on_property_changed(prop_key))
        widget.bind("<<Decrement>>", lambda e: self.on_property_changed(prop_key))
        
        widget.var = var
        return widget
    
    def create_string_widget(self, parent, prop_key: str):
        """Create a string (entry) widget"""
        var = tk.StringVar()
        widget = ttk.Entry(parent, textvariable=var, width=30)
        widget.pack(side="left")
        widget.bind("<KeyRelease>", lambda e: self.on_property_changed(prop_key))
        
        widget.var = var
        return widget
    
    def create_status_bar(self):
        """Create status bar"""
        status_frame = ttk.Frame(self.properties_frame)
        status_frame.pack(fill="x", padx=10, pady=5)
        
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Load server properties to begin editing")
        
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.pack(side="left")
        
        # Validation status
        self.validation_var = tk.StringVar()
        validation_label = ttk.Label(status_frame, textvariable=self.validation_var, foreground="red")
        validation_label.pack(side="right")
    
    def load_properties(self):
        """Load properties from file"""
        try:
            # This should be called from the main GUI with the server jar path
            # For now, we'll check if properties are already loaded
            if not hasattr(self, '_server_jar_path'):
                messagebox.showwarning("Warning", "Please select a server JAR file first in the main tab")
                return
            
            success = self.properties_manager.load_properties(self._server_jar_path)
            
            if success:
                self.populate_widgets()
                self.status_var.set("Properties loaded successfully")
                self.modified = False
                self.update_modified_indicator()
            else:
                self.status_var.set("Failed to load properties")
                
        except Exception as e:
            error_info = self.error_handler.handle_error(e, "load_properties_ui", ErrorSeverity.MEDIUM)
            messagebox.showerror("Load Error", f"Failed to load properties: {error_info['message']}")
    
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
            error_info = self.error_handler.handle_error(e, "save_properties_ui", ErrorSeverity.HIGH)
            messagebox.showerror("Save Error", f"Failed to save properties: {error_info['message']}")
    
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
            error_info = self.error_handler.handle_error(e, "reset_properties_ui", ErrorSeverity.MEDIUM)
            messagebox.showerror("Reset Error", f"Failed to reset properties: {error_info['message']}")
    
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
            error_info = self.error_handler.handle_error(e, "export_properties_ui", ErrorSeverity.MEDIUM)
            messagebox.showerror("Export Error", f"Failed to export properties: {error_info['message']}")
    
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
                    # Load properties from selected file
                    temp_manager = ServerPropertiesManager(self.error_handler)
                    temp_manager.properties_file_path = filename
                    
                    # Read the file manually since it might not be in server directory
                    temp_manager.properties = {}
                    with open(filename, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#') and '=' in line:
                                key, value = line.split('=', 1)
                                temp_manager.properties[key.strip()] = value.strip()
                    
                    # Copy to our manager
                    self.properties_manager.properties = temp_manager.properties.copy()
                    self.populate_widgets()
                    self.modified = True
                    self.update_modified_indicator()
                    messagebox.showinfo("Success", "Properties imported successfully")
                    
        except Exception as e:
            error_info = self.error_handler.handle_error(e, "import_properties_ui", ErrorSeverity.MEDIUM)
            messagebox.showerror("Import Error", f"Failed to import properties: {error_info['message']}")
    
    def populate_widgets(self):
        """Populate widgets with current property values"""
        try:
            for prop_key, widget in self.widgets.items():
                value = self.properties_manager.get_property(prop_key)
                
                if hasattr(widget, 'var'):
                    prop_info = self.properties_manager.get_property_info(prop_key)
                    
                    if prop_info and prop_info['type'] == 'bool':
                        widget.var.set(value.lower() == 'true')
                    else:
                        widget.var.set(value)
                        
        except Exception as e:
            self.error_handler.handle_error(e, "populate_widgets", ErrorSeverity.LOW)
    
    def update_properties_from_widgets(self):
        """Update properties manager with current widget values"""
        try:
            for prop_key, widget in self.widgets.items():
                if hasattr(widget, 'var'):
                    value = widget.var.get()
                    
                    prop_info = self.properties_manager.get_property_info(prop_key)
                    if prop_info and prop_info['type'] == 'bool':
                        value = 'true' if value else 'false'
                    
                    self.properties_manager.set_property(prop_key, str(value))
                    
        except Exception as e:
            self.error_handler.handle_error(e, "update_properties_from_widgets", ErrorSeverity.LOW)
    
    def validate_all_properties(self) -> bool:
        """Validate all property values"""
        try:
            all_valid = True
            validation_errors = []
            
            for prop_key, widget in self.widgets.items():
                if hasattr(widget, 'var'):
                    value = widget.var.get()
                    
                    prop_info = self.properties_manager.get_property_info(prop_key)
                    if prop_info and prop_info['type'] == 'bool':
                        value = 'true' if value else 'false'
                    
                    is_valid, error_msg = self.properties_manager.validate_property(prop_key, str(value))
                    
                    if not is_valid:
                        all_valid = False
                        validation_errors.append(f"{prop_key}: {error_msg}")
            
            if validation_errors:
                self.validation_var.set(f"Validation errors: {len(validation_errors)}")
                # Could show detailed errors in a dialog
            else:
                self.validation_var.set("")
            
            return all_valid
            
        except Exception as e:
            self.error_handler.handle_error(e, "validate_all_properties", ErrorSeverity.LOW)
            return False
    
    def on_property_changed(self, prop_key: str):
        """Handle property value change"""
        try:
            self.modified = True
            self.update_modified_indicator()
            
            # Validate the changed property
            widget = self.widgets[prop_key]
            if hasattr(widget, 'var'):
                value = widget.var.get()
                
                prop_info = self.properties_manager.get_property_info(prop_key)
                if prop_info and prop_info['type'] == 'bool':
                    value = 'true' if value else 'false'
                
                is_valid, error_msg = self.properties_manager.validate_property(prop_key, str(value))
                
                if not is_valid:
                    self.validation_var.set(f"{prop_key}: {error_msg}")
                else:
                    self.validation_var.set("")
                    
        except Exception as e:
            self.error_handler.handle_error(e, "on_property_changed", ErrorSeverity.LOW)
    
    def update_modified_indicator(self):
        """Update the modified indicator"""
        if self.modified:
            self.modified_label.config(text="● Modified", foreground="orange")
        else:
            self.modified_label.config(text="", foreground="black")
    
    def set_server_jar_path(self, server_jar_path: str):
        """Set the server JAR path for loading properties"""
        self._server_jar_path = server_jar_path
        if server_jar_path:
            # Automatically load properties when server JAR is set
            self.load_properties()
    
    def show_help(self):
        """Show help dialog"""
        help_text = """Server Properties Help

This interface allows you to configure your Minecraft server properties in an organized way.

Categories:
• Basic Server Settings: Core server configuration like port, max players, MOTD
• World & Gameplay Settings: World generation, gamemode, difficulty, PvP settings  
• Performance Settings: View distance, memory, network optimization
• Advanced Settings: Command blocks, RCON, monitoring, permissions
• Nether & End Settings: Enable/disable dimensions and flight
• Resource Pack Settings: Configure server resource packs

Tips:
• Load Properties: Loads current server.properties from your server directory
• Save Properties: Saves changes to server.properties (restart server to apply)
• Reset to Defaults: Resets all values to Minecraft defaults
• Export/Import: Share or backup your server configuration

Important Notes:
• Server must be restarted for most changes to take effect
• Some changes (like world settings) only apply to new worlds
• Always backup your server before making major changes
• Online mode should be enabled for public servers
"""
        
        help_window = tk.Toplevel(self.properties_frame)
        help_window.title("Server Properties Help")
        help_window.geometry("600x500")
        help_window.transient(self.properties_frame)
        
        text_widget = tk.Text(help_window, wrap=tk.WORD, padx=10, pady=10)
        scrollbar = ttk.Scrollbar(help_window, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.insert(1.0, help_text)
        text_widget.config(state=tk.DISABLED)
        
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
