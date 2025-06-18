# gui/components/modcard.py
"""Individual mod display card component"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable, Dict, Any

class ModCard:
    """Individual mod card for grid/list display"""
    
    def __init__(self, parent, mod_info, theme_manager, callbacks=None):
        self.parent = parent
        self.mod_info = mod_info
        self.theme_manager = theme_manager
        self.callbacks = callbacks or {}
        
        # UI state
        self.frame = None
        self.selected = False
        self.hover = False
        
        # UI components
        self.name_label = None
        self.status_frame = None
        self.details_frame = None
        self.button_frame = None
        self.toggle_btn = None
        self.favorite_btn = None
        
        self.create_card()
    
    def create_card(self):
        """Create the mod card UI"""
        theme = self.theme_manager.get_current_theme()
        
        # Main card frame with hover effects
        self.frame = tk.Frame(
            self.parent,
            bg=theme.get('bg_secondary', '#f8f9fa'),
            relief='solid',
            bd=1,
            padx=12,
            pady=10,
            cursor='hand2'
        )
        
        # Header section
        self.create_header(theme)
        
        # Details section
        self.create_details(theme)
        
        # Action buttons
        self.create_actions(theme)
        
        # Bind events
        self.bind_events()
    
    def create_header(self, theme):
        """Create the card header with mod name and status"""
        header_frame = tk.Frame(self.frame, bg=theme.get('bg_secondary', '#f8f9fa'))
        header_frame.pack(fill='x', pady=(0, 8))
        
        # Mod name (clickable for details)
        self.name_label = tk.Label(
            header_frame,
            text=self.mod_info.name,
            font=('Segoe UI', 12, 'bold'),
            bg=theme.get('bg_secondary', '#f8f9fa'),
            fg=theme.get('text_primary', '#212529'),
            cursor='hand2',
            anchor='w'
        )
        self.name_label.pack(side='left', fill='x', expand=True)
        
        # Status indicators
        self.status_frame = tk.Frame(header_frame, bg=theme.get('bg_secondary', '#f8f9fa'))
        self.status_frame.pack(side='right')
        
        self.update_status_indicators(theme)
    
    def update_status_indicators(self, theme):
        """Update status indicator badges"""
        # Clear existing indicators
        for widget in self.status_frame.winfo_children():
            widget.destroy()
        
        # Enabled/Disabled status
        if self.mod_info.is_enabled:
            status_badge = tk.Label(
                self.status_frame,
                text="ENABLED",
                font=('Segoe UI', 8, 'bold'),
                bg='#28a745',
                fg='white',
                padx=6,
                pady=2
            )
        else:
            status_badge = tk.Label(
                self.status_frame,
                text="DISABLED",
                font=('Segoe UI', 8, 'bold'),
                bg='#6c757d',
                fg='white',
                padx=6,
                pady=2
            )
        status_badge.pack(side='right', padx=(4, 0))
        
        # Special indicators
        if self.mod_info.update_available:
            update_badge = tk.Label(
                self.status_frame,
                text="UPDATE",
                font=('Segoe UI', 8, 'bold'),
                bg='#007bff',
                fg='white',
                padx=6,
                pady=2
            )
            update_badge.pack(side='right', padx=(4, 0))
        
        if self.mod_info.is_favorite:
            fav_badge = tk.Label(
                self.status_frame,
                text="★",
                font=('Segoe UI', 10, 'bold'),
                bg='#ffc107',
                fg='white',
                padx=6,
                pady=2
            )
            fav_badge.pack(side='right', padx=(4, 0))
        
        if self.mod_info.is_essential:
            essential_badge = tk.Label(
                self.status_frame,
                text="CORE",
                font=('Segoe UI', 8, 'bold'),
                bg='#fd7e14',
                fg='white',
                padx=6,
                pady=2
            )
            essential_badge.pack(side='right', padx=(4, 0))
    
    def create_details(self, theme):
        """Create the details section"""
        self.details_frame = tk.Frame(self.frame, bg=theme.get('bg_secondary', '#f8f9fa'))
        self.details_frame.pack(fill='x', pady=(0, 8))
        
        # Version and author info
        info_text = f"v{self.mod_info.version}"
        if self.mod_info.author:
            info_text += f" • by {self.mod_info.author}"
        
        tk.Label(
            self.details_frame,
            text=info_text,
            font=('Segoe UI', 9),
            bg=theme.get('bg_secondary', '#f8f9fa'),
            fg=theme.get('text_secondary', '#6c757d'),
            anchor='w'
        ).pack(side='left', fill='x', expand=True)
        
        # Mod loader badge
        if self.mod_info.mod_loader:
            loader_color = self.get_loader_color()
            loader_badge = tk.Label(
                self.details_frame,
                text=self.mod_info.mod_loader.value.upper(),
                font=('Segoe UI', 8, 'bold'),
                bg=loader_color,
                fg='white',
                padx=6,
                pady=2
            )
            loader_badge.pack(side='right')
        
        # Description (if available and not too long)
        if self.mod_info.description:
            desc_text = self.mod_info.description
            if len(desc_text) > 120:
                desc_text = desc_text[:117] + "..."
            
            desc_label = tk.Label(
                self.frame,
                text=desc_text,
                font=('Segoe UI', 8),
                bg=theme.get('bg_secondary', '#f8f9fa'),
                fg=theme.get('text_secondary', '#6c757d'),
                wraplength=280,
                justify='left',
                anchor='w'
            )
            desc_label.pack(fill='x', pady=(0, 8))
    
    def create_actions(self, theme):
        """Create action buttons"""
        self.button_frame = tk.Frame(self.frame, bg=theme.get('bg_secondary', '#f8f9fa'))
        self.button_frame.pack(fill='x')
        
        # Toggle enable/disable button
        toggle_text = "Disable" if self.mod_info.is_enabled else "Enable"
        toggle_color = "#dc3545" if self.mod_info.is_enabled else "#28a745"
        
        self.toggle_btn = tk.Button(
            self.button_frame,
            text=toggle_text,
            font=('Segoe UI', 9),
            bg=toggle_color,
            fg='white',
            padx=12,
            pady=4,
            relief='flat',
            cursor='hand2',
            command=self.toggle_mod
        )
        self.toggle_btn.pack(side='left', padx=(0, 8))
        
        # More actions button
        more_btn = tk.Button(
            self.button_frame,
            text="⋯",
            font=('Segoe UI', 12, 'bold'),
            bg=theme.get('accent', '#007bff'),
            fg='white',
            padx=8,
            pady=4,
            relief='flat',
            cursor='hand2',
            command=self.show_context_menu
        )
        more_btn.pack(side='left', padx=(0, 8))
        
        # Favorite button
        fav_text = "★" if self.mod_info.is_favorite else "☆"
        fav_color = "#ffc107" if self.mod_info.is_favorite else "#6c757d"
        
        self.favorite_btn = tk.Button(
            self.button_frame,
            text=fav_text,
            font=('Segoe UI', 12),
            bg=fav_color,
            fg='white',
            padx=8,
            pady=4,
            relief='flat',
            cursor='hand2',
            command=self.toggle_favorite
        )
        self.favorite_btn.pack(side='right')
        
        # File size info
        if self.mod_info.file_size > 0:
            size_mb = self.mod_info.file_size / (1024 * 1024)
            size_text = f"{size_mb:.1f} MB"
            
            tk.Label(
                self.button_frame,
                text=size_text,
                font=('Segoe UI', 8),
                bg=theme.get('bg_secondary', '#f8f9fa'),
                fg=theme.get('text_secondary', '#6c757d')
            ).pack(side='right', padx=(8, 8))
    
    def bind_events(self):
        """Bind mouse and keyboard events"""
        # Card selection
        self.frame.bind('<Button-1>', self.on_click)
        self.frame.bind('<Control-Button-1>', self.on_ctrl_click)
        self.frame.bind('<Double-Button-1>', self.on_double_click)
        
        # Hover effects
        self.frame.bind('<Enter>', self.on_enter)
        self.frame.bind('<Leave>', self.on_leave)
        
        # Name click for details
        self.name_label.bind('<Button-1>', self.on_name_click)
        
        # Recursive binding for all child widgets
        self.bind_recursive(self.frame)
    
    def bind_recursive(self, widget):
        """Recursively bind events to all child widgets"""
        widget.bind('<Button-1>', self.on_click)
        widget.bind('<Control-Button-1>', self.on_ctrl_click)
        widget.bind('<Enter>', self.on_enter)
        widget.bind('<Leave>', self.on_leave)
        
        for child in widget.winfo_children():
            if isinstance(child, (tk.Label, tk.Frame)):
                self.bind_recursive(child)
    
    def get_loader_color(self):
        """Get color for mod loader badge"""
        colors = {
            'forge': '#1f2937',
            'fabric': '#f59e0b',
            'quilt': '#8b5cf6',
            'vanilla': '#6b7280',
            'unknown': '#9ca3af'
        }
        loader_name = self.mod_info.mod_loader.value.lower() if self.mod_info.mod_loader else 'unknown'
        return colors.get(loader_name, '#9ca3af')
    
    # Event handlers
    def on_click(self, event):
        """Handle card click"""
        if event.state & 0x0004:  # Ctrl key
            self.on_ctrl_click(event)
        else:
            self.call_callback('on_card_select', self.mod_info.mod_id, False)
    
    def on_ctrl_click(self, event):
        """Handle Ctrl+click for multi-selection"""
        self.call_callback('on_card_select', self.mod_info.mod_id, True)
    
    def on_double_click(self, event):
        """Handle double-click to show details"""
        self.show_mod_details()
    
    def on_name_click(self, event):
        """Handle clicking mod name"""
        event.stopPropagation()
        self.show_mod_details()
    
    def on_enter(self, event):
        """Handle mouse enter (hover start)"""
        if not self.hover:
            self.hover = True
            # Get theme-appropriate hover color
            theme = self.theme_manager.get_current_theme()
            hover_color = theme.get('hover_bg', theme.get('bg_secondary', '#f0f0f0'))
            self.frame.configure(bg=hover_color)

    
    def on_leave(self, event):
        """Handle mouse leave (hover end)"""
        if self.hover:
            self.hover = False
            # Get theme-appropriate background color
            theme = self.theme_manager.get_current_theme()
            if self.selected:
                bg_color = theme.get('selected_bg', theme.get('accent_color', '#0078d4'))
            else:
                bg_color = theme.get('card_bg', theme.get('bg_primary', 'white'))
            self.frame.configure(bg=bg_color)

    
    # Action methods
    def toggle_mod(self):
        """Toggle mod enabled/disabled state"""
        self.call_callback('on_mod_toggle', self.mod_info.mod_id)
    
    def toggle_favorite(self):
        """Toggle favorite status"""
        self.call_callback('on_mod_favorite', self.mod_info.mod_id)
    
    def show_mod_details(self):
        """Show mod details dialog"""
        self.call_callback('on_mod_details', self.mod_info)
    
    def show_context_menu(self):
        """Show context menu with more actions"""
        menu = tk.Menu(self.frame, tearoff=0)
        
        # Add menu items
        menu.add_command(label="Show Details", command=self.show_mod_details)
        menu.add_separator()
        
        if self.mod_info.is_enabled:
            menu.add_command(label="Disable", command=self.toggle_mod)
        else:
            menu.add_command(label="Enable", command=self.toggle_mod)
        
        fav_text = "Remove from Favorites" if self.mod_info.is_favorite else "Add to Favorites"
        menu.add_command(label=fav_text, command=self.toggle_favorite)
        
        menu.add_separator()
        menu.add_command(label="Show in Folder", command=self.show_in_folder)
        menu.add_command(label="Remove Mod", command=self.remove_mod)
        
        # Show menu at cursor
        try:
            menu.tk_popup(self.frame.winfo_rootx() + 10, self.frame.winfo_rooty() + 10)
        finally:
            menu.grab_release()
    
    def show_in_folder(self):
        """Show mod file in explorer"""
        self.call_callback('on_show_in_folder', self.mod_info.filepath)
    
    def remove_mod(self):
        """Remove the mod with confirmation"""
        if messagebox.askyesno(
            "Remove Mod",
            f"Are you sure you want to remove '{self.mod_info.name}'?\n\nThis will delete the mod file permanently.",
            icon='warning'
        ):
            self.call_callback('on_mod_remove', self.mod_info.mod_id)
    
    # Selection methods
    def select(self):
        """Select this card"""
        self.selected = True
        theme = self.theme_manager.get_current_theme()
        self.frame.configure(
            bg=theme.get('selected_bg', '#cce5ff'),
            relief='solid',
            bd=2
        )
    
    def deselect(self):
        """Deselect this card"""
        self.selected = False
        theme = self.theme_manager.get_current_theme()
        bg_color = theme.get('hover_bg', '#e9ecef') if self.hover else theme.get('bg_secondary', '#f8f9fa')
        self.frame.configure(
            bg=bg_color,
            relief='solid',
            bd=1
        )
    
    # Update methods
    def update_display(self, updated_mod_info):
        """Update card display with new mod info"""
        self.mod_info = updated_mod_info
        
        # Update name
        self.name_label.configure(text=self.mod_info.name)
        
        # Update status indicators
        theme = self.theme_manager.get_current_theme()
        self.update_status_indicators(theme)
        
        # Update toggle button
        toggle_text = "Disable" if self.mod_info.is_enabled else "Enable"
        toggle_color = "#dc3545" if self.mod_info.is_enabled else "#28a745"
        self.toggle_btn.configure(text=toggle_text, bg=toggle_color)
        
        # Update favorite button
        fav_text = "★" if self.mod_info.is_favorite else "☆"
        fav_color = "#ffc107" if self.mod_info.is_favorite else "#6c757d"
        self.favorite_btn.configure(text=fav_text, bg=fav_color)
    
    # Utility methods
    def call_callback(self, callback_name, *args):
        """Safely call a callback if it exists"""
        if callback_name in self.callbacks and callable(self.callbacks[callback_name]):
            try:
                self.callbacks[callback_name](*args)
            except Exception as e:
                print(f"Error in callback {callback_name}: {e}")
    
    def pack(self, **kwargs):
        """Pack the card frame"""
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Grid the card frame"""
        self.frame.grid(**kwargs)
    
    def destroy(self):
        """Destroy the card"""
        if self.frame:
            self.frame.destroy()
