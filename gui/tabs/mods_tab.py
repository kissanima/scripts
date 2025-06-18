"""
Mods Management Tab for Minecraft Server Manager
Complete mod management interface with modern UI
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime

from gui.components.mod_card import ModCard
from gui.components.mod_grid import ModGrid
from gui.components.mod_installer import ModInstaller
from gui.components.mod_profile_manager import ModProfileManager

from gui.utils.mod_api_client import ModAPIClient

from mod_manager import ModManager, ModCategory, ModLoaderType, ModSide

class ModsTab:
    """Complete mods management tab with modern interface"""
    
    def __init__(self, parent, theme_manager, main_window):
        self.parent = parent
        self.theme_manager = theme_manager
        self.main_window = main_window
        
        # Initialize mod manager
        self.mod_manager = None
        self.api_client = ModAPIClient()
        
        # UI components
        self.main_frame = None
        self.toolbar_frame = None
        self.content_frame = None
        self.sidebar_frame = None
        self.mod_grid = None
        self.search_var = None
        self.category_var = None
        self.loader_var = None
        self.status_var = None
        
        # State
        self.current_view = "grid"  # grid, list, details
        self.selected_mods = set()
        self.filter_settings = {}
        self.sort_settings = {"field": "name", "reverse": False}
        
        # Initialize
        self.create_content()
        self.setup_mod_manager()
        
    def add_to_notebook(self, notebook, text):
        """Add this tab to the notebook"""
        notebook.add(self.parent, text=text)
    
    def create_content(self):
        """Create the main mods tab content"""
        theme = self.theme_manager.get_current_theme()
        
        # Main container
        self.main_frame = tk.Frame(self.parent, bg=theme['bg_primary'])
        self.main_frame.pack(fill="both", expand=True)
        
        # Create toolbar
        self.create_toolbar()
        
        # Create main content area
        content_container = tk.Frame(self.main_frame, bg=theme['bg_primary'])
        content_container.pack(fill="both", expand=True, padx=theme['padding_medium'], pady=(0, theme['padding_medium']))
        
        # Create sidebar and content area
        self.create_sidebar(content_container)
        self.create_content_area(content_container)
        
        # Create status bar
        self.create_status_bar()
    
    def create_toolbar(self):
        """Create the toolbar with mod management controls"""
        theme = self.theme_manager.get_current_theme()
        
        self.toolbar_frame = tk.Frame(self.main_frame, bg=theme['bg_secondary'], height=60)
        self.toolbar_frame.pack(fill="x", padx=theme['padding_medium'], pady=theme['padding_medium'])
        self.toolbar_frame.pack_propagate(False)
        
        # Toolbar content
        toolbar_content = tk.Frame(self.toolbar_frame, bg=theme['bg_secondary'])
        toolbar_content.pack(fill="both", expand=True, padx=theme['padding_medium'], pady=theme['padding_small'])
        
        # Left side - Main actions
        left_frame = tk.Frame(toolbar_content, bg=theme['bg_secondary'])
        left_frame.pack(side="left", fill="y")
        
        # Install mod button
        install_btn = tk.Button(
            left_frame,
            text="📁 Install Mod",
            command=self.install_mod_dialog,
            bg=theme['accent'],
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            padx=15,
            pady=8,
            relief='flat',
            cursor='hand2'
        )
        install_btn.pack(side="left", padx=(0, 10))
        
        # Browse online button
        browse_btn = tk.Button(
            left_frame,
            text="🌐 Browse Online",
            command=self.browse_online_mods,
            bg=theme['info'],
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            padx=15,
            pady=8,
            relief='flat',
            cursor='hand2'
        )
        browse_btn.pack(side="left", padx=(0, 10))
        
        # Scan mods button
        scan_btn = tk.Button(
            left_frame,
            text="🔍 Scan Mods",
            command=self.scan_mods,
            bg=theme['warning'],
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            padx=15,
            pady=8,
            relief='flat',
            cursor='hand2'
        )
        scan_btn.pack(side="left", padx=(0, 10))
        
        # Separator
        separator = tk.Frame(left_frame, bg=theme['border'], width=2)
        separator.pack(side="left", fill="y", padx=10)
        
        # Batch actions
        batch_frame = tk.Frame(left_frame, bg=theme['bg_secondary'])
        batch_frame.pack(side="left", fill="y")
        
        tk.Label(
            batch_frame,
            text="Batch:",
            bg=theme['bg_secondary'],
            fg=theme['text_secondary'],
            font=('Segoe UI', 9)
        ).pack(side="left", padx=(0, 5))
        
        enable_all_btn = tk.Button(
            batch_frame,
            text="Enable All",
            command=lambda: self.batch_action("enable"),
            bg=theme['success'],
            fg='white',
            font=('Segoe UI', 9),
            padx=10,
            pady=5,
            relief='flat',
            cursor='hand2'
        )
        enable_all_btn.pack(side="left", padx=(0, 5))
        
        disable_all_btn = tk.Button(
            batch_frame,
            text="Disable All",
            command=lambda: self.batch_action("disable"),
            bg=theme['error'],
            fg='white',
            font=('Segoe UI', 9),
            padx=10,
            pady=5,
            relief='flat',
            cursor='hand2'
        )
        disable_all_btn.pack(side="left", padx=(0, 5))
        
        update_all_btn = tk.Button(
            batch_frame,
            text="Update All",
            command=lambda: self.batch_action("update"),
            bg=theme['info'],
            fg='white',
            font=('Segoe UI', 9),
            padx=10,
            pady=5,
            relief='flat',
            cursor='hand2'
        )
        update_all_btn.pack(side="left")
        
        # Right side - Search and view controls
        right_frame = tk.Frame(toolbar_content, bg=theme['bg_secondary'])
        right_frame.pack(side="right", fill="y")
        
        # Search
        search_frame = tk.Frame(right_frame, bg=theme['bg_secondary'])
        search_frame.pack(side="right", fill="y", padx=(0, 15))
        
        tk.Label(
            search_frame,
            text="🔍",
            bg=theme['bg_secondary'],
            fg=theme['text_secondary'],
            font=('Segoe UI', 12)
        ).pack(side="left", padx=(0, 5))
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.on_search_changed)
        
        search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            bg=theme['input_bg'],
            fg=theme['text_primary'],
            font=('Segoe UI', 10),
            relief='flat',
            bd=5,
            width=20
        )
        search_entry.pack(side="left")
        
        # View mode buttons
        view_frame = tk.Frame(right_frame, bg=theme['bg_secondary'])
        view_frame.pack(side="right", fill="y")
        
        grid_btn = tk.Button(
            view_frame,
            text="⊞",
            command=lambda: self.change_view("grid"),
            bg=theme['accent'] if self.current_view == "grid" else theme['button_bg'],
            fg='white',
            font=('Segoe UI', 12, 'bold'),
            width=3,
            pady=5,
            relief='flat',
            cursor='hand2'
        )
        grid_btn.pack(side="left", padx=(0, 2))
        
        list_btn = tk.Button(
            view_frame,
            text="☰",
            command=lambda: self.change_view("list"),
            bg=theme['accent'] if self.current_view == "list" else theme['button_bg'],
            fg='white',
            font=('Segoe UI', 12, 'bold'),
            width=3,
            pady=5,
            relief='flat',
            cursor='hand2'
        )
        list_btn.pack(side="left")
    
    def create_sidebar(self, parent):
        """Create the sidebar with filters and categories"""
        theme = self.theme_manager.get_current_theme()
        
        self.sidebar_frame = tk.Frame(parent, bg=theme['bg_card'], width=250, relief='solid', bd=1)
        self.sidebar_frame.pack(side="left", fill="y", padx=(0, theme['padding_medium']))
        self.sidebar_frame.pack_propagate(False)
        
        # Sidebar content
        sidebar_content = tk.Frame(self.sidebar_frame, bg=theme['bg_card'])
        sidebar_content.pack(fill="both", expand=True, padx=theme['padding_medium'], pady=theme['padding_medium'])
        
        # Filters section
        self.create_filters_section(sidebar_content)
        
        # Statistics section
        self.create_statistics_section(sidebar_content)
        
        # Profiles section
        self.create_profiles_section(sidebar_content)
    
    def create_filters_section(self, parent):
        """Create the filters section in sidebar"""
        theme = self.theme_manager.get_current_theme()
        
        # Filters header
        filters_header = tk.Label(
            parent,
            text="🎛️ Filters",
            bg=theme['bg_card'],
            fg=theme['text_primary'],
            font=('Segoe UI', 12, 'bold')
        )
        filters_header.pack(anchor="w", pady=(0, 10))
        
        # Category filter
        category_frame = tk.Frame(parent, bg=theme['bg_card'])
        category_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(
            category_frame,
            text="Category:",
            bg=theme['bg_card'],
            fg=theme['text_secondary'],
            font=('Segoe UI', 9)
        ).pack(anchor="w")
        
        self.category_var = tk.StringVar(value="All")
        category_combo = ttk.Combobox(
            category_frame,
            textvariable=self.category_var,
            values=["All"] + [cat.value.title().replace('_', ' ') for cat in ModCategory],
            state="readonly",
            font=('Segoe UI', 9),
            width=25
        )
        category_combo.pack(fill="x", pady=(2, 0))
        category_combo.bind("<<ComboboxSelected>>", self.on_filter_changed)
        
        # Mod loader filter
        loader_frame = tk.Frame(parent, bg=theme['bg_card'])
        loader_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(
            loader_frame,
            text="Mod Loader:",
            bg=theme['bg_card'],
            fg=theme['text_secondary'],
            font=('Segoe UI', 9)
        ).pack(anchor="w")
        
        self.loader_var = tk.StringVar(value="All")
        loader_combo = ttk.Combobox(
            loader_frame,
            textvariable=self.loader_var,
            values=["All"] + [loader.value.title() for loader in ModLoaderType if loader != ModLoaderType.UNKNOWN],
            state="readonly",
            font=('Segoe UI', 9),
            width=25
        )
        loader_combo.pack(fill="x", pady=(2, 0))
        loader_combo.bind("<<ComboboxSelected>>", self.on_filter_changed)
        
        # Status filter
        status_frame = tk.Frame(parent, bg=theme['bg_card'])
        status_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(
            status_frame,
            text="Status:",
            bg=theme['bg_card'],
            fg=theme['text_secondary'],
            font=('Segoe UI', 9)
        ).pack(anchor="w")
        
        self.status_var = tk.StringVar(value="All")
        status_combo = ttk.Combobox(
            status_frame,
            textvariable=self.status_var,
            values=["All", "Enabled", "Disabled", "Outdated", "Favorites", "Essential"],
            state="readonly",
            font=('Segoe UI', 9),
            width=25
        )
        status_combo.pack(fill="x", pady=(2, 0))
        status_combo.bind("<<ComboboxSelected>>", self.on_filter_changed)
        
        # Clear filters button
        clear_btn = tk.Button(
            parent,
            text="Clear Filters",
            command=self.clear_filters,
            bg=theme['button_bg'],
            fg=theme['text_primary'],
            font=('Segoe UI', 9),
            padx=10,
            pady=5,
            relief='flat',
            cursor='hand2'
        )
        clear_btn.pack(fill="x", pady=(5, 0))
    
    def create_statistics_section(self, parent):
        """Create the statistics section in sidebar"""
        theme = self.theme_manager.get_current_theme()
        
        # Add separator
        separator = tk.Frame(parent, bg=theme['border'], height=1)
        separator.pack(fill="x", pady=15)
        
        # Statistics header
        stats_header = tk.Label(
            parent,
            text="📊 Statistics",
            bg=theme['bg_card'],
            fg=theme['text_primary'],
            font=('Segoe UI', 12, 'bold')
        )
        stats_header.pack(anchor="w", pady=(0, 10))
        
        # Statistics content
        self.stats_frame = tk.Frame(parent, bg=theme['bg_card'])
        self.stats_frame.pack(fill="x")
        
        # Will be populated by update_statistics()
        self.update_statistics()
    
    def create_profiles_section(self, parent):
        """Create the profiles section in sidebar"""
        theme = self.theme_manager.get_current_theme()
        
        # Add separator
        separator = tk.Frame(parent, bg=theme['border'], height=1)
        separator.pack(fill="x", pady=15)
        
        # Profiles header
        profiles_header = tk.Label(
            parent,
            text="👤 Profiles",
            bg=theme['bg_card'],
            fg=theme['text_primary'],
            font=('Segoe UI', 12, 'bold')
        )
        profiles_header.pack(anchor="w", pady=(0, 10))
        
        # Current profile
        self.current_profile_label = tk.Label(
            parent,
            text="Current: Default",
            bg=theme['bg_card'],
            fg=theme['text_secondary'],
            font=('Segoe UI', 9)
        )
        self.current_profile_label.pack(anchor="w", pady=(0, 5))
        
        # Profile buttons
        profile_buttons_frame = tk.Frame(parent, bg=theme['bg_card'])
        profile_buttons_frame.pack(fill="x")
        
        manage_profiles_btn = tk.Button(
            profile_buttons_frame,
            text="Manage Profiles",
            command=self.manage_profiles,
            bg=theme['button_bg'],
            fg=theme['text_primary'],
            font=('Segoe UI', 9),
            padx=10,
            pady=5,
            relief='flat',
            cursor='hand2'
        )
        manage_profiles_btn.pack(fill="x", pady=(0, 5))
        
        save_profile_btn = tk.Button(
            profile_buttons_frame,
            text="Save Current as Profile",
            command=self.save_current_profile,
            bg=theme['accent'],
            fg='white',
            font=('Segoe UI', 9),
            padx=10,
            pady=5,
            relief='flat',
            cursor='hand2'
        )
        save_profile_btn.pack(fill="x")
    
    def create_content_area(self, parent):
        """Create the main content area for mod display"""
        theme = self.theme_manager.get_current_theme()
        
        self.content_frame = tk.Frame(parent, bg=theme['bg_primary'])
        self.content_frame.pack(side="left", fill="both", expand=True)
        
        # Create proper callbacks dictionary
        grid_callbacks = {
            'on_mods_updated': self.on_mods_updated,
            'on_selection_changed': self.on_selection_changed,
            'on_mod_toggle': self.on_mod_toggle,
            'on_mod_remove': self.on_mod_remove,
            'on_mod_favorite': self.on_mod_favorite,
            'on_mod_details': self.on_mod_details,
            'on_show_in_folder': self.on_show_in_folder,
            'on_bulk_remove': self.on_bulk_remove,
            'on_view_mode_changed': self.on_view_mode_changed
        }

        # Create mod grid component
        self.mod_grid = ModGrid(self.content_frame, self.theme_manager, grid_callbacks) 
        
        # ADD THIS - Pack the ModGrid frame into its parent:
        self.mod_grid.pack(fill='both', expand=True)  # ✅ This makes it fill the available space
        
        # Load mods if manager is ready
        if self.mod_manager:
            self.refresh_mod_display()
    
    def create_status_bar(self):
        """Create the status bar at bottom"""
        theme = self.theme_manager.get_current_theme()
        
        status_frame = tk.Frame(self.main_frame, bg=theme['bg_secondary'], height=25)
        status_frame.pack(fill="x", side="bottom")
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(
            status_frame,
            text="Ready",
            bg=theme['bg_secondary'],
            fg=theme['text_secondary'],
            font=('Segoe UI', 9),
            anchor="w"
        )
        self.status_label.pack(side="left", fill="x", expand=True, padx=10, pady=3)
        
        # Progress indicator
        self.progress_var = tk.StringVar()
        self.progress_label = tk.Label(
            status_frame,
            textvariable=self.progress_var,
            bg=theme['bg_secondary'],
            fg=theme['text_secondary'],
            font=('Segoe UI', 9)
        )
        self.progress_label.pack(side="right", padx=10, pady=3)
    
    def setup_mod_manager(self):
        """Use the main window's mod manager instead of creating a new one"""
        try:
            # Use the main window's mod manager if available
            if (hasattr(self.main_window, 'modmanager') and 
                self.main_window.modmanager and 
                hasattr(self.main_window, 'mod_management_enabled') and 
                self.main_window.mod_management_enabled):
                
                self.mod_manager = self.main_window.modmanager
                print(f"✅ Using main mod manager with server dir: {self.mod_manager.server_dir}")
                print(f"✅ Mods directory: {self.mod_manager.mods_dir}")
                
                # Register callbacks if needed
                if hasattr(self.mod_manager, 'register_scan_callback'):
                    self.mod_manager.register_scan_callback(self.on_scan_progress)
                
                # Refresh display with existing mods
                self.refresh_mod_display()
                
            else:
                print("❌ Main mod manager not available")
                self.mod_manager = None
                
        except Exception as e:
            print(f"❌ Error setting up mod manager: {e}")
            self.mod_manager = None
    
    # === Event Handlers ===
    
    def on_search_changed(self, *args):
        """Handle search text change"""
        self.refresh_mod_display()
    
    def on_filter_changed(self, event=None):
        """Handle filter change"""
        self.refresh_mod_display()
    
    def on_scan_progress(self, status, progress, message):
        """Handle mod scan progress updates - THREAD SAFE"""
        try:
            # Schedule GUI updates on main thread
            if hasattr(self, 'main_window') and self.main_window and hasattr(self.main_window, 'root'):
                if status == "completed":
                    # Refresh the mod display when scan completes
                    self.main_window.root.after(0, lambda: self._scan_completed(message))
                elif status == "error":
                    self.main_window.root.after(0, lambda: self._scan_error(message))
                elif status == "progress":
                    self.main_window.root.after(0, lambda: self._scan_progress(progress, message))
        except Exception as e:
            print(f"Error in scan progress callback: {e}")

    def _scan_completed(self, message):
        """Handle scan completion on main thread"""
        try:
            print(f"🎉 _scan_completed called with: {message}")
            
            # Update status
            if hasattr(self, 'status_label') and self.status_label:
                self.status_label.configure(text=f"Scan complete: {message}")
                print("✅ Status label updated")
            else:
                print("❌ No status_label found")
            
            # Check if we have mod manager
            if hasattr(self, 'mod_manager') and self.mod_manager:
                mod_count = len(self.mod_manager.installed_mods)
                print(f"🔍 Mod manager has {mod_count} mods before refresh")
            
            # Refresh the mod display
            print("🔄 Calling refresh_mod_display()...")
            self.refresh_mod_display()
            
        except Exception as e:
            print(f"❌ Error in _scan_completed: {e}")
            import traceback
            traceback.print_exc()



    def update_scan_status(self, message):
        """Thread-safe status update"""
        try:
            if hasattr(self, 'status_label') and self.status_label:
                self.status_label.configure(text=message)
        except Exception as e:
            print(f"Error updating scan status: {e}")
            
    def _scan_error(self, message):
        """Handle scan error on main thread"""
        try:
            if hasattr(self, 'status_label') and self.status_label:
                self.status_label.configure(text=f"Scan error: {message}")
        except Exception as e:
            print(f"Error updating scan error: {e}")

    def _scan_progress(self, progress, message):
        """Handle scan progress on main thread"""
        try:
            if hasattr(self, 'status_label') and self.status_label:
                self.status_label.configure(text=f"Scanning: {message} ({progress}%)")
        except Exception as e:
            print(f"Error updating scan progress: {e}")

    
    def on_mod_changed(self, action, mod_info, message):
        """Handle mod install/remove events"""
        self.status_label.configure(text=f"Mod {action}: {mod_info.name}")
        self.refresh_mod_display()
        self.update_statistics()
    
    # === Main Actions ===
    
    def install_mod_dialog(self):
        """Open mod installation dialog"""
        if not self.mod_manager:
            messagebox.showwarning("No Server", "Please select a server JAR file first")
            return
        
        # File dialog for mod selection
        file_path = filedialog.askopenfilename(
            title="Select Mod File",
            filetypes=[("JAR files", "*.jar"), ("All files", "*.*")],
            initialdir=os.path.expanduser("~/Downloads")
        )
        
        if file_path:
            # Create installer dialog
            installer = ModInstaller(self.parent, self.theme_manager, self.mod_manager, file_path)
            
            # Wait for installation to complete
            self.parent.wait_window(installer.dialog)
            
            # Refresh display
            self.refresh_mod_display()
            self.update_statistics()
    
    def browse_online_mods(self):
        """Open online mod browser"""
        messagebox.showinfo("Coming Soon", "Online mod browsing will be available in a future update!")
        # TODO: Implement online mod browser
    
    def scan_mods(self):
        """Trigger mod scan"""
        if not self.mod_manager:
            messagebox.showwarning("No Server", "Please select a server JAR file first")
            return
        
        def scan_thread():
            self.mod_manager.scan_mods(force_rescan=True)
        
        threading.Thread(target=scan_thread, daemon=True).start()
    
    def batch_action(self, action):
        """Perform batch action on mods"""
        if not self.mod_manager:
            return
        
        if action == "enable":
            self.batch_enable_mods()
        elif action == "disable":
            self.batch_disable_mods()
        elif action == "update":
            self.batch_update_mods()
    
    def batch_enable_mods(self):
        """Enable all disabled mods"""
        disabled_mods = [mod_id for mod_id, mod_info in self.mod_manager.installed_mods.items() if not mod_info.is_enabled]
        
        if not disabled_mods:
            messagebox.showinfo("No Action Needed", "All mods are already enabled")
            return
        
        if messagebox.askyesno("Confirm", f"Enable {len(disabled_mods)} disabled mods?"):
            success_count = 0
            for mod_id in disabled_mods:
                success, _ = self.mod_manager.enable_mod(mod_id)
                if success:
                    success_count += 1
            
            self.status_label.configure(text=f"Enabled {success_count} mods")
            self.refresh_mod_display()
    
    def batch_disable_mods(self):
        """Disable all enabled mods"""
        enabled_mods = [mod_id for mod_id, mod_info in self.mod_manager.installed_mods.items() if mod_info.is_enabled and not mod_info.is_essential]
        
        if not enabled_mods:
            messagebox.showinfo("No Action Needed", "No non-essential mods to disable")
            return
        
        if messagebox.askyesno("Confirm", f"Disable {len(enabled_mods)} enabled mods?\n\nEssential mods will be skipped."):
            success_count = 0
            for mod_id in enabled_mods:
                success, _ = self.mod_manager.disable_mod(mod_id)
                if success:
                    success_count += 1
            
            self.status_label.configure(text=f"Disabled {success_count} mods")
            self.refresh_mod_display()
    
    def batch_update_mods(self):
        """Update all outdated mods"""
        outdated_mods = [mod_info for mod_info in self.mod_manager.installed_mods.values() if mod_info.update_available]
        
        if not outdated_mods:
            messagebox.showinfo("Up to Date", "All mods are up to date")
            return
        
        messagebox.showinfo("Coming Soon", f"Batch update for {len(outdated_mods)} mods will be available soon!")
        # TODO: Implement batch update
    
    def clear_filters(self):
        """Clear all filters"""
        self.search_var.set("")
        self.category_var.set("All")
        self.loader_var.set("All")
        self.status_var.set("All")
        self.refresh_mod_display()
    
    def change_view(self, view_mode):
        """Change the view mode"""
        self.current_view = view_mode
        self.refresh_mod_display()
        
        # Update view buttons (this would be implemented with proper button references)
        # For now, just refresh the display
    
    def manage_profiles(self):
        """Open profile management dialog"""
        if not self.mod_manager:
            return
        
        profile_manager = ModProfileManager(self.parent, self.theme_manager, self.mod_manager)
        self.parent.wait_window(profile_manager.dialog)
        
        # Update profile display
        self.update_profile_display()
    
    def save_current_profile(self):
        """Save current mod configuration as new profile"""
        if not self.mod_manager:
            return
        
        # Simple input dialog for profile name
        profile_name = tk.simpledialog.askstring("New Profile", "Enter profile name:")
        if profile_name:
            success = self.mod_manager.create_profile(profile_name, f"Profile created on {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            if success:
                self.status_label.configure(text=f"Profile '{profile_name}' created")
                self.update_profile_display()
            else:
                messagebox.showerror("Error", "Failed to create profile (name might already exist)")
    
    # === Display Updates ===
    
    def refresh_mod_display(self):
        """Refresh the mod display with detailed debugging"""
        try:
            print("=" * 50)
            print("🔄 REFRESH MOD DISPLAY DEBUG")
            
            # Check mod manager
            if hasattr(self, 'mod_manager') and self.mod_manager:
                print(f"✅ ModsTab has mod_manager: {self.mod_manager}")
                
                # Check installed mods
                mods = self.mod_manager.installed_mods
                print(f"📊 Mod manager has {len(mods)} installed mods")
                
                if mods:
                    print("🔍 First 3 mods:")
                    for i, (mod_id, mod_info) in enumerate(list(mods.items())[:3]):
                        print(f"  {i+1}. {mod_info.name} (ID: {mod_id})")
                        print(f"     Version: {mod_info.version}")
                        print(f"     Enabled: {mod_info.is_enabled}")
                        print(f"     File: {mod_info.file_path}")
                else:
                    print("❌ No mods in mod_manager.installed_mods")
                
                # Check mod grid
                if hasattr(self, 'mod_grid') and self.mod_grid:
                    print(f"✅ ModsTab has mod_grid: {self.mod_grid}")
                    
                    # Try to update mod grid
                    print("🎯 Calling mod_grid.update_mods()...")
                    try:
                        mod_list = list(mods.values())
                        print(f"📝 Converting to list: {len(mod_list)} mods")
                        
                        self.mod_grid.update_mods(mod_list)
                        print("✅ mod_grid.update_mods() completed successfully")
                        
                        # Check if mod grid has the mods now
                        if hasattr(self.mod_grid, 'mods'):
                            print(f"🔍 mod_grid.mods count: {len(getattr(self.mod_grid, 'mods', []))}")
                        
                    except Exception as grid_error:
                        print(f"❌ Error in mod_grid.update_mods(): {grid_error}")
                        import traceback
                        traceback.print_exc()
                        
                else:
                    print("❌ ModsTab has no mod_grid")
                    print(f"🔍 Available attributes: {[attr for attr in dir(self) if 'grid' in attr.lower()]}")
            else:
                print("❌ ModsTab has no mod_manager")
                print(f"🔍 Available attributes: {[attr for attr in dir(self) if 'mod' in attr.lower()]}")
            
            print("=" * 50)
            
        except Exception as e:
            print(f"❌ Error in refresh_mod_display: {e}")
            import traceback
            traceback.print_exc()

    
    def get_filtered_mods(self):
        """Get mods based on current filters"""
        if not self.mod_manager:
            return []
        
        # Start with all mods
        mods = list(self.mod_manager.installed_mods.values())
        
        # Apply search filter
        search_text = self.search_var.get().lower().strip()
        if search_text:
            mods = [mod for mod in mods if 
                   search_text in mod.name.lower() or
                   search_text in mod.description.lower() or
                   search_text in mod.author.lower() or
                   any(search_text in tag.lower() for tag in mod.tags)]
        
        # Apply category filter
        category = self.category_var.get()
        if category != "All":
            category_enum = None
            for cat in ModCategory:
                if cat.value.title().replace('_', ' ') == category:
                    category_enum = cat
                    break
            if category_enum:
                mods = [mod for mod in mods if mod.category == category_enum]
        
        # Apply loader filter
        loader = self.loader_var.get()
        if loader != "All":
            loader_enum = None
            for load in ModLoaderType:
                if load.value.title() == loader:
                    loader_enum = load
                    break
            if loader_enum:
                mods = [mod for mod in mods if mod.mod_loader == loader_enum]
        
        # Apply status filter
        status = self.status_var.get()
        if status == "Enabled":
            mods = [mod for mod in mods if mod.is_enabled]
        elif status == "Disabled":
            mods = [mod for mod in mods if not mod.is_enabled]
        elif status == "Outdated":
            mods = [mod for mod in mods if mod.update_available]
        elif status == "Favorites":
            mods = [mod for mod in mods if mod.is_favorite]
        elif status == "Essential":
            mods = [mod for mod in mods if mod.is_essential]
        
        # Apply sorting
        sort_field = self.sort_settings["field"]
        reverse = self.sort_settings["reverse"]
        
        if sort_field == "name":
            mods.sort(key=lambda x: x.name.lower(), reverse=reverse)
        elif sort_field == "author":
            mods.sort(key=lambda x: x.author.lower(), reverse=reverse)
        elif sort_field == "category":
            mods.sort(key=lambda x: x.category.value, reverse=reverse)
        elif sort_field == "install_date":
            mods.sort(key=lambda x: x.install_date or datetime.min, reverse=reverse)
        elif sort_field == "size":
            mods.sort(key=lambda x: x.file_size, reverse=reverse)
        
        return mods
    
    def update_statistics(self):
        """Update the statistics display"""
        if not self.mod_manager:
            return
        
        theme = self.theme_manager.get_current_theme()
        
        # Clear existing stats
        for widget in self.stats_frame.winfo_children():
            widget.destroy()
        
        # Get statistics
        stats = self.mod_manager.get_mod_statistics()
        
        # Create statistic items
        stat_items = [
            ("Total Mods", stats["total_mods"]),
            ("Enabled", stats["enabled_mods"]),
            ("Disabled", stats["disabled_mods"]),
            ("Outdated", stats["outdated_mods"]),
            ("Favorites", stats["favorite_mods"]),
            ("Size", f"{stats['total_size_mb']} MB")
        ]
        
        for label, value in stat_items:
            stat_frame = tk.Frame(self.stats_frame, bg=theme['bg_card'])
            stat_frame.pack(fill="x", pady=1)
            
            tk.Label(
                stat_frame,
                text=f"{label}:",
                bg=theme['bg_card'],
                fg=theme['text_secondary'],
                font=('Segoe UI', 8),
                anchor="w"
            ).pack(side="left")
            
            tk.Label(
                stat_frame,
                text=str(value),
                bg=theme['bg_card'],
                fg=theme['text_primary'],
                font=('Segoe UI', 8, 'bold'),
                anchor="e"
            ).pack(side="right")
    
    def update_profile_display(self):
        """Update the profile display"""
        if not self.mod_manager:
            return
        
        current_profile = self.mod_manager.current_profile
        self.current_profile_label.configure(text=f"Current: {current_profile}")
    
    def update_theme(self):
        """Update theme for all components"""
        # This would be called when theme changes
        theme = self.theme_manager.get_current_theme()
        
        # Update main frame
        self.main_frame.configure(bg=theme['bg_primary'])
        
        # Update toolbar
        self.toolbar_frame.configure(bg=theme['bg_secondary'])
        
        # Update sidebar
        self.sidebar_frame.configure(bg=theme['bg_card'])
        
        # Update content
        self.content_frame.configure(bg=theme['bg_primary'])
        
        # Update mod grid
        if self.mod_grid:
            self.mod_grid.update_theme()
            
    def get_frame(self):
        """Get the main tab frame"""
        if hasattr(self, 'main_frame'):
            return self.main_frame
        elif hasattr(self, 'content_frame'):
            return self.content_frame
        elif hasattr(self, 'tab_container'):
            return self.tab_container
        else:
            # Debug: print available attributes
            attrs = [attr for attr in dir(self) if not attr.startswith('_') and 'frame' in attr.lower()]
            print(f"Available frame attributes: {attrs}")
            return None
    
    
    def on_mods_updated(self, count):
        """Handle mods updated callback"""
        try:
            if hasattr(self, 'status_label') and self.status_label:
                self.status_label.configure(text=f"Showing {count} mods")
        except Exception as e:
            print(f"Error updating mods count: {e}")

    def on_selection_changed(self, selected_mod_ids):
        """Handle mod selection changes"""
        try:
            count = len(selected_mod_ids)
            # Update any selection UI here
            print(f"Selection changed: {count} mods selected")
        except Exception as e:
            print(f"Error handling selection change: {e}")

    def on_mod_toggle(self, modid):
        """Handle mod enable/disable toggle"""
        print(f"Toggle mod: {modid}")

    def on_mod_remove(self, modid):
        """Handle mod removal"""
        print(f"Remove mod: {modid}")

    def on_mod_favorite(self, modid):
        """Handle favorite toggle"""
        print(f"Toggle favorite: {modid}")

    def on_mod_details(self, modinfo):
        """Handle show mod details"""
        print(f"Show details for: {modinfo.name}")

    def on_show_in_folder(self, filepath):
        """Handle show in folder"""
        print(f"Show in folder: {filepath}")

    def on_bulk_remove(self, mod_ids):
        """Handle bulk removal"""
        print(f"Bulk remove: {len(mod_ids)} mods")

    def on_view_mode_changed(self, mode):
        """Handle view mode change"""
        print(f"View mode changed to: {mode}")
        
    def refresh_mods(self):
        """Refresh the mod display"""
        try:
            print("Refreshing mods display...")
            
            # If you have a mod grid, refresh it
            if hasattr(self, 'mod_grid') and self.mod_grid:
                # Get mods from mod manager
                if hasattr(self, 'mod_manager') and self.mod_manager:
                    # Trigger a refresh of the mod display
                    self.refresh_mod_display()
                else:
                    print("No mod manager available")
            else:
                print("No mod grid available")
                
        except Exception as e:
            print(f"Error refreshing mods: {e}")



