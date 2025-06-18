"""
Mod Profile Manager for Minecraft Server Manager
Handles creation, editing, and management of mod profiles
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

class ModProfileManager:
    """Dialog for managing mod profiles"""
    
    def __init__(self, parent, modmanager, thememanager):
        self.parent = parent
        self.modmanager = modmanager
        self.thememanager = thememanager
        
        # Dialog window
        self.dialog = None
        self.result = None
        
        # UI components
        self.profiles_listbox = None
        self.profile_name_var = tk.StringVar()
        self.profile_desc_var = tk.StringVar()
        
        # Current profile data
        self.current_profiles = {}
        self.selected_profile = None
    
    def show_dialog(self):
        """Show the profile manager dialog"""
        try:
            self.create_dialog()
            self.load_profiles()
            self.dialog.wait_window()
            return self.result
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show profile manager: {str(e)}")
            return None
    
    def create_dialog(self):
        """Create the profile manager dialog"""
        theme = self.thememanager.get_current_theme()
        
        # Create dialog
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Mod Profile Manager")
        self.dialog.geometry("800x600")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        self.dialog.resizable(True, True)
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (600 // 2)
        self.dialog.geometry(f"800x600+{x}+{y}")
        
        self.dialog.configure(bg=theme.get('bg_primary', 'white'))
        
        # Create main layout
        self.create_main_layout()
        
        # Handle window close
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_cancel)
    
    def create_main_layout(self):
        """Create the main dialog layout"""
        theme = self.thememanager.get_current_theme()
        
        # Header
        header_frame = tk.Frame(self.dialog, bg=theme.get('bg_secondary', 'lightgray'), height=60)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        tk.Label(
            header_frame,
            text="🔧 Mod Profile Manager",
            font=('Segoe UI', 16, 'bold'),
            bg=theme.get('bg_secondary', 'lightgray'),
            fg=theme.get('text_primary', 'black')
        ).pack(pady=20)
        
        # Main content
        main_frame = tk.Frame(self.dialog, bg=theme.get('bg_primary', 'white'))
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Left panel - Profile list
        left_frame = tk.LabelFrame(
            main_frame,
            text="Profiles",
            font=('Segoe UI', 12, 'bold'),
            bg=theme.get('bg_primary', 'white'),
            fg=theme.get('text_primary', 'black')
        )
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # Profile listbox with scrollbar
        listbox_frame = tk.Frame(left_frame, bg=theme.get('bg_primary', 'white'))
        listbox_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.profiles_listbox = tk.Listbox(
            listbox_frame,
            font=('Segoe UI', 10),
            bg='white',
            fg=theme.get('text_primary', 'black'),
            selectmode='single'
        )
        self.profiles_listbox.pack(side='left', fill='both', expand=True)
        
        listbox_scrollbar = ttk.Scrollbar(listbox_frame, orient='vertical', command=self.profiles_listbox.yview)
        self.profiles_listbox.configure(yscrollcommand=listbox_scrollbar.set)
        listbox_scrollbar.pack(side='right', fill='y')
        
        # Bind selection event
        self.profiles_listbox.bind('<<ListboxSelect>>', self.on_profile_select)
        
        # Profile action buttons
        button_frame = tk.Frame(left_frame, bg=theme.get('bg_primary', 'white'))
        button_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        # Create buttons
        btn_new = tk.Button(
            button_frame,
            text="➕ New",
            command=self.create_new_profile,
            bg='#28a745',
            fg='white',
            font=('Segoe UI', 9),
            padx=10,
            pady=5,
            relief='flat'
        )
        btn_new.pack(side='left', padx=(0, 5))
        
        btn_duplicate = tk.Button(
            button_frame,
            text="📋 Duplicate",
            command=self.duplicate_profile,
            bg='#007bff',
            fg='white',
            font=('Segoe UI', 9),
            padx=10,
            pady=5,
            relief='flat'
        )
        btn_duplicate.pack(side='left', padx=(0, 5))
        
        btn_delete = tk.Button(
            button_frame,
            text="🗑️ Delete",
            command=self.delete_profile,
            bg='#dc3545',
            fg='white',
            font=('Segoe UI', 9),
            padx=10,
            pady=5,
            relief='flat'
        )
        btn_delete.pack(side='left', padx=(0, 5))
        
        # Right panel - Profile details
        right_frame = tk.LabelFrame(
            main_frame,
            text="Profile Details",
            font=('Segoe UI', 12, 'bold'),
            bg=theme.get('bg_primary', 'white'),
            fg=theme.get('text_primary', 'black')
        )
        right_frame.pack(side='right', fill='both', expand=True, padx=(10, 0))
        
        # Profile details form
        self.create_profile_details_form(right_frame)
        
        # Bottom buttons
        self.create_bottom_buttons()
    
    def create_profile_details_form(self, parent):
        """Create the profile details form"""
        theme = self.thememanager.get_current_theme()
        
        form_frame = tk.Frame(parent, bg=theme.get('bg_primary', 'white'))
        form_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Profile name
        tk.Label(
            form_frame,
            text="Profile Name:",
            font=('Segoe UI', 10, 'bold'),
            bg=theme.get('bg_primary', 'white'),
            fg=theme.get('text_primary', 'black')
        ).pack(anchor='w', pady=(0, 5))
        
        self.name_entry = tk.Entry(
            form_frame,
            textvariable=self.profile_name_var,
            font=('Segoe UI', 10),
            bg='white',
            fg=theme.get('text_primary', 'black'),
            relief='solid',
            bd=1
        )
        self.name_entry.pack(fill='x', pady=(0, 15))
        
        # Profile description
        tk.Label(
            form_frame,
            text="Description:",
            font=('Segoe UI', 10, 'bold'),
            bg=theme.get('bg_primary', 'white'),
            fg=theme.get('text_primary', 'black')
        ).pack(anchor='w', pady=(0, 5))
        
        self.desc_entry = tk.Entry(
            form_frame,
            textvariable=self.profile_desc_var,
            font=('Segoe UI', 10),
            bg='white',
            fg=theme.get('text_primary', 'black'),
            relief='solid',
            bd=1
        )
        self.desc_entry.pack(fill='x', pady=(0, 15))
        
        # Mod status summary
        summary_frame = tk.LabelFrame(
            form_frame,
            text="Current Mod Status",
            font=('Segoe UI', 10, 'bold'),
            bg=theme.get('bg_primary', 'white'),
            fg=theme.get('text_primary', 'black')
        )
        summary_frame.pack(fill='x', pady=(0, 15))
        
        self.summary_text = tk.Text(
            summary_frame,
            height=8,
            font=('Segoe UI', 9),
            bg='white',
            fg=theme.get('text_primary', 'black'),
            relief='solid',
            bd=1,
            state='disabled'
        )
        self.summary_text.pack(fill='x', padx=10, pady=10)
        
        # Profile actions
        actions_frame = tk.Frame(form_frame, bg=theme.get('bg_primary', 'white'))
        actions_frame.pack(fill='x', pady=(10, 0))
        
        save_btn = tk.Button(
            actions_frame,
            text="💾 Save Profile",
            command=self.save_current_profile,
            bg='#28a745',
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            padx=15,
            pady=8,
            relief='flat'
        )
        save_btn.pack(side='left', padx=(0, 10))
        
        load_btn = tk.Button(
            actions_frame,
            text="🔄 Load Profile",
            command=self.load_selected_profile,
            bg='#007bff',
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            padx=15,
            pady=8,
            relief='flat'
        )
        load_btn.pack(side='left')
    
    def create_bottom_buttons(self):
        """Create bottom dialog buttons"""
        theme = self.thememanager.get_current_theme()
        
        button_frame = tk.Frame(self.dialog, bg=theme.get('bg_primary', 'white'))
        button_frame.pack(fill='x', padx=20, pady=20)
        
        # Import/Export buttons
        import_btn = tk.Button(
            button_frame,
            text="📥 Import",
            command=self.import_profiles,
            bg='#6c757d',
            fg='white',
            font=('Segoe UI', 10),
            padx=15,
            pady=8,
            relief='flat'
        )
        import_btn.pack(side='left')
        
        export_btn = tk.Button(
            button_frame,
            text="📤 Export",
            command=self.export_profiles,
            bg='#6c757d',
            fg='white',
            font=('Segoe UI', 10),
            padx=15,
            pady=8,
            relief='flat'
        )
        export_btn.pack(side='left', padx=(10, 0))
        
        # Close button
        close_btn = tk.Button(
            button_frame,
            text="Close",
            command=self.on_cancel,
            bg='#6c757d',
            fg='white',
            font=('Segoe UI', 10),
            padx=20,
            pady=8,
            relief='flat'
        )
        close_btn.pack(side='right')
    
    def load_profiles(self):
        """Load profiles from mod manager"""
        try:
            if hasattr(self.modmanager, 'modprofiles'):
                self.current_profiles = self.modmanager.modprofiles.copy()
            else:
                self.current_profiles = {}
            
            # Update listbox
            self.profiles_listbox.delete(0, tk.END)
            for profile_name in self.current_profiles.keys():
                self.profiles_listbox.insert(tk.END, profile_name)
            
            # Update summary
            self.update_mod_summary()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load profiles: {str(e)}")
    
    def update_mod_summary(self):
        """Update the mod status summary"""
        try:
            summary_lines = []
            
            if hasattr(self.modmanager, 'installedmods'):
                total_mods = len(self.modmanager.installedmods)
                enabled_mods = len([m for m in self.modmanager.installedmods.values() if m.isenabled])
                disabled_mods = total_mods - enabled_mods
                
                summary_lines.extend([
                    f"Total Mods: {total_mods}",
                    f"Enabled: {enabled_mods}",
                    f"Disabled: {disabled_mods}",
                    "",
                    "Enabled Mods:"
                ])
                
                for mod in self.modmanager.installedmods.values():
                    if mod.isenabled:
                        summary_lines.append(f"  ✓ {mod.name}")
            else:
                summary_lines.append("No mods detected")
            
            # Update text widget
            self.summary_text.config(state='normal')
            self.summary_text.delete(1.0, tk.END)
            self.summary_text.insert(1.0, '\n'.join(summary_lines))
            self.summary_text.config(state='disabled')
            
        except Exception as e:
            print(f"Error updating mod summary: {e}")
    
    def on_profile_select(self, event):
        """Handle profile selection"""
        try:
            selection = self.profiles_listbox.curselection()
            if selection:
                profile_name = self.profiles_listbox.get(selection[0])
                self.selected_profile = profile_name
                
                if profile_name in self.current_profiles:
                    profile = self.current_profiles[profile_name]
                    self.profile_name_var.set(profile.name)
                    self.profile_desc_var.set(profile.description)
        except Exception as e:
            print(f"Error handling profile selection: {e}")
    
    def create_new_profile(self):
        """Create a new profile"""
        try:
            # Get profile name from user
            name = tk.simpledialog.askstring("New Profile", "Enter profile name:")
            if not name:
                return
            
            if name in self.current_profiles:
                messagebox.showerror("Error", "Profile name already exists")
                return
            
            # Create profile from current mod state
            if hasattr(self.modmanager, 'createprofile'):
                success = self.modmanager.createprofile(name, f"Profile created on {datetime.now().strftime('%Y-%m-%d %H:%M')}")
                if success:
                    self.load_profiles()
                    messagebox.showinfo("Success", f"Profile '{name}' created successfully")
                else:
                    messagebox.showerror("Error", "Failed to create profile")
            else:
                messagebox.showerror("Error", "Profile creation not supported")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create profile: {str(e)}")
    
    def duplicate_profile(self):
        """Duplicate the selected profile"""
        try:
            if not self.selected_profile:
                messagebox.showwarning("Warning", "Please select a profile to duplicate")
                return
            
            # Get new name
            new_name = tk.simpledialog.askstring("Duplicate Profile", f"Enter new name for copy of '{self.selected_profile}':")
            if not new_name:
                return
            
            if new_name in self.current_profiles:
                messagebox.showerror("Error", "Profile name already exists")
                return
            
            # Duplicate the profile
            original_profile = self.current_profiles[self.selected_profile]
            # Note: This is a simplified duplication - you'd need to implement proper profile duplication
            messagebox.showinfo("Info", "Profile duplication feature coming soon!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to duplicate profile: {str(e)}")
    
    def delete_profile(self):
        """Delete the selected profile"""
        try:
            if not self.selected_profile:
                messagebox.showwarning("Warning", "Please select a profile to delete")
                return
            
            if self.selected_profile == "default":
                messagebox.showerror("Error", "Cannot delete the default profile")
                return
            
            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete profile '{self.selected_profile}'?"):
                # Delete the profile
                if self.selected_profile in self.current_profiles:
                    del self.current_profiles[self.selected_profile]
                    self.load_profiles()
                    self.clear_form()
                    messagebox.showinfo("Success", f"Profile '{self.selected_profile}' deleted")
                    self.selected_profile = None
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete profile: {str(e)}")
    
    def save_current_profile(self):
        """Save current mod state as a profile"""
        try:
            name = self.profile_name_var.get().strip()
            if not name:
                messagebox.showerror("Error", "Please enter a profile name")
                return
            
            description = self.profile_desc_var.get().strip()
            
            if hasattr(self.modmanager, 'createprofile'):
                success = self.modmanager.createprofile(name, description, setascurrent=False)
                if success:
                    self.load_profiles()
                    messagebox.showinfo("Success", f"Profile '{name}' saved successfully")
                else:
                    messagebox.showerror("Error", "Failed to save profile")
            else:
                messagebox.showerror("Error", "Profile saving not supported")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save profile: {str(e)}")
    
    def load_selected_profile(self):
        """Load the selected profile"""
        try:
            if not self.selected_profile:
                messagebox.showwarning("Warning", "Please select a profile to load")
                return
            
            if messagebox.askyesno("Confirm Load", f"Load profile '{self.selected_profile}'? This will change your current mod configuration."):
                # Load the profile
                messagebox.showinfo("Info", "Profile loading feature coming soon!")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load profile: {str(e)}")
    
    def import_profiles(self):
        """Import profiles from file"""
        try:
            filename = filedialog.askopenfilename(
                title="Import Profiles",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                messagebox.showinfo("Info", "Profile import feature coming soon!")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import profiles: {str(e)}")
    
    def export_profiles(self):
        """Export profiles to file"""
        try:
            filename = filedialog.asksaveasfilename(
                title="Export Profiles",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                messagebox.showinfo("Info", "Profile export feature coming soon!")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export profiles: {str(e)}")
    
    def clear_form(self):
        """Clear the profile form"""
        self.profile_name_var.set("")
        self.profile_desc_var.set("")
        self.selected_profile = None
    
    def on_cancel(self):
        """Handle dialog cancellation"""
        self.result = None
        self.dialog.destroy()

# For backwards compatibility
class ModProfileManager:
    """Simplified mod profile manager for basic functionality"""
    
    def __init__(self, modmanager, thememanager):
        self.modmanager = modmanager
        self.thememanager = thememanager
    
    def show_dialog(self, parent):
        """Show a simple profile dialog"""
        try:
            messagebox.showinfo(
                "Mod Profiles", 
                "Mod Profile Manager\n\n"
                "This feature allows you to create and manage different mod configurations.\n\n"
                "Coming soon:\n"
                "• Create mod profiles\n"
                "• Switch between configurations\n"
                "• Import/export profiles\n"
                "• Backup and restore"
            )
            return None
        except Exception as e:
            messagebox.showerror("Error", f"Profile manager error: {str(e)}")
            return None
