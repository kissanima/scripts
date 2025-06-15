"""
Backup tab implementation with world-only backup and server management
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import threading
import time
import logging
from datetime import datetime
from .base_tab import BaseTab
from ..components.status_card import StatusCard
from ..components.modern_widgets import ModernButton, ModernEntry

class BackupTab(BaseTab):
    """Backup tab with world-only backup and server stop/start functionality"""
    
    def __init__(self, parent, theme_manager, main_window):
        self.main_window = main_window
        super().__init__(parent, theme_manager)
        
        # Backup settings
        self.stop_server_var = tk.BooleanVar()
        self.backup_in_progress = False
        
        # UI components
        self.backup_list = None
        self.backup_status_label = None
        self.create_backup_btn = None
        self.restore_backup_btn = None
        self.delete_backup_btn = None
        
        self.create_content()
        self.load_backup_settings()
        self.refresh_backup_list()
    
    def create_content(self):
        """Create backup tab content"""
        theme = self.theme_manager.get_current_theme()
        
        content = tk.Frame(self.tab_frame, bg=theme['bg_primary'])
        content.pack(fill="both", expand=True, padx=theme['padding_large'], pady=theme['padding_large'])
        
        # Configure main grid
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(1, weight=1)
        
        # Backup settings card
        settings_card = StatusCard(content, "Backup Settings", "⚙️", self.theme_manager)
        settings_card.card_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, theme['margin_medium']))
        
        settings_content = settings_card.get_content_frame()
        
        # Settings container
        settings_frame = tk.Frame(settings_content, bg=theme['bg_card'])
        settings_frame.pack(fill="x", padx=theme['padding_medium'], pady=theme['padding_medium'])
        
        # Stop server checkbox
        stop_server_frame = tk.Frame(settings_frame, bg=theme['bg_card'])
        stop_server_frame.pack(fill="x", pady=(0, theme['margin_small']))
        
        stop_server_check = tk.Checkbutton(
            stop_server_frame,
            text="🛑 Stop server during backup (recommended for world integrity)",
            variable=self.stop_server_var,
            bg=theme['bg_card'],
            fg=theme['text_primary'],
            selectcolor=theme['input_bg'],
            activebackground=theme['bg_card'],
            activeforeground=theme['text_primary'],
            font=('Segoe UI', theme['font_size_normal']),
            command=self.on_stop_server_changed
        )
        stop_server_check.pack(anchor="w")
        
        # Backup info
        info_frame = tk.Frame(settings_frame, bg=theme['bg_card'])
        info_frame.pack(fill="x", pady=(theme['margin_small'], 0))
        
        info_text = "💾 Backup Type: World folders only (world, world_nether, world_the_end)\n" \
                   "🚀 Auto-restart: Server will restart automatically after backup (if stopped)\n" \
                   "⚡ Quick backup: Only essential world data is backed up for faster operation"
        
        info_label = tk.Label(
            info_frame,
            text=info_text,
            bg=theme['bg_card'],
            fg=theme['text_secondary'],
            font=('Segoe UI', theme['font_size_small']),
            justify="left",
            anchor="w"
        )
        info_label.pack(anchor="w")
        
        # Create backup card
        create_card = StatusCard(content, "Create Backup", "💾", self.theme_manager)
        create_card.card_frame.grid(row=1, column=0, sticky="nsew", padx=(0, theme['margin_small']))
        
        create_content = create_card.get_content_frame()
        
        # Create backup form
        create_frame = tk.Frame(create_content, bg=theme['bg_card'])
        create_frame.pack(fill="both", expand=True, padx=theme['padding_medium'], pady=theme['padding_medium'])
        
        # Backup name input
        name_frame = tk.Frame(create_frame, bg=theme['bg_card'])
        name_frame.pack(fill="x", pady=(0, theme['margin_medium']))
        
        tk.Label(name_frame, text="Backup Name:", bg=theme['bg_card'], 
                 fg=theme['text_primary'], font=('Segoe UI', theme['font_size_normal'], 'bold')).pack(anchor="w")
        
        self.backup_name_var = tk.StringVar()
        backup_name_entry = ModernEntry(name_frame, self.theme_manager, textvariable=self.backup_name_var)
        backup_name_entry.pack(fill="x", pady=(theme['margin_small'], 0))
        
        # Set default name
        default_name = f"world_backup_{datetime.now().strftime('%Y%m%d_%H%M')}"
        self.backup_name_var.set(default_name)
        
        # Description input
        desc_frame = tk.Frame(create_frame, bg=theme['bg_card'])
        desc_frame.pack(fill="x", pady=(0, theme['margin_medium']))
        
        tk.Label(desc_frame, text="Description (optional):", bg=theme['bg_card'], 
                 fg=theme['text_primary'], font=('Segoe UI', theme['font_size_normal'], 'bold')).pack(anchor="w")
        
        self.backup_desc_var = tk.StringVar()
        backup_desc_entry = ModernEntry(desc_frame, self.theme_manager, textvariable=self.backup_desc_var)
        backup_desc_entry.pack(fill="x", pady=(theme['margin_small'], 0))
        
        # Create backup button
        button_frame = tk.Frame(create_frame, bg=theme['bg_card'])
        button_frame.pack(fill="x", pady=(theme['margin_medium'], 0))
        
        self.create_backup_btn = ModernButton(
            button_frame, 
            "💾 Create World Backup", 
            self.create_world_backup, 
            "success", 
            self.theme_manager, 
            "normal"
        )
        self.create_backup_btn.pack(fill="x")
        
        # Status label
        self.backup_status_label = tk.Label(
            create_frame,
            text="Ready to create backup",
            bg=theme['bg_card'],
            fg=theme['text_secondary'],
            font=('Segoe UI', theme['font_size_small'])
        )
        self.backup_status_label.pack(pady=(theme['margin_small'], 0))
        
        # Backup list card
        list_card = StatusCard(content, "Existing Backups", "📂", self.theme_manager)
        list_card.card_frame.grid(row=1, column=1, sticky="nsew", padx=(theme['margin_small'], 0))
        
        list_content = list_card.get_content_frame()
        
        # Backup list
        list_frame = tk.Frame(list_content, bg=theme['bg_card'])
        list_frame.pack(fill="both", expand=True, padx=theme['padding_medium'], pady=theme['padding_medium'])
        
        # List with scrollbar
        list_container = tk.Frame(list_frame, bg=theme['bg_card'])
        list_container.pack(fill="both", expand=True, pady=(0, theme['margin_medium']))
        
        # Create treeview for backup list
        columns = ('Name', 'Date', 'Size')
        self.backup_list = ttk.Treeview(list_container, columns=columns, show='tree headings', height=10)
        
        # Configure columns
        self.backup_list.heading('#0', text='Type', anchor='w')
        self.backup_list.heading('Name', text='Name', anchor='w')
        self.backup_list.heading('Date', text='Date', anchor='w')
        self.backup_list.heading('Size', text='Size', anchor='w')
        
        self.backup_list.column('#0', width=60, minwidth=50)
        self.backup_list.column('Name', width=200, minwidth=100)
        self.backup_list.column('Date', width=120, minwidth=100)
        self.backup_list.column('Size', width=80, minwidth=70)
        
        # Scrollbar for list
        backup_scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.backup_list.yview)
        self.backup_list.configure(yscrollcommand=backup_scrollbar.set)
        
        self.backup_list.pack(side="left", fill="both", expand=True)
        backup_scrollbar.pack(side="right", fill="y")
        
        # Backup management buttons
        buttons_frame = tk.Frame(list_frame, bg=theme['bg_card'])
        buttons_frame.pack(fill="x")
        
        button_row1 = tk.Frame(buttons_frame, bg=theme['bg_card'])
        button_row1.pack(fill="x", pady=(0, theme['margin_small']))
        
        self.restore_backup_btn = ModernButton(
            button_row1, 
            "🔄 Restore Backup", 
            self.restore_selected_backup, 
            "primary", 
            self.theme_manager, 
            "normal"
        )
        self.restore_backup_btn.pack(side="left", padx=(0, theme['margin_small']))
        
        self.delete_backup_btn = ModernButton(
            button_row1, 
            "🗑️ Delete Backup", 
            self.delete_selected_backup, 
            "danger", 
            self.theme_manager, 
            "normal"
        )
        self.delete_backup_btn.pack(side="left")
        
        button_row2 = tk.Frame(buttons_frame, bg=theme['bg_card'])
        button_row2.pack(fill="x")
        
        ModernButton(
            button_row2, 
            "🔄 Refresh List", 
            self.refresh_backup_list, 
            "secondary", 
            self.theme_manager, 
            "small"
        ).pack(side="left", padx=(0, theme['margin_small']))
        
        ModernButton(
            button_row2, 
            "📁 Open Backup Folder", 
            self.open_backup_folder, 
            "secondary", 
            self.theme_manager, 
            "small"
        ).pack(side="left")
        
        # Bind list selection
        self.backup_list.bind('<<TreeviewSelect>>', self.on_backup_selected)
        
        # Register components
        self.register_widget(settings_card)
        self.register_widget(create_card)
        self.register_widget(list_card)
        
        # Initial button states
        self.update_backup_button_states()
    
    def load_backup_settings(self):
        """Load backup settings from config"""
        try:
            stop_server = self.main_window.config.get("stop_server_for_backup", True)
            self.stop_server_var.set(stop_server)
        except Exception as e:
            logging.error(f"Error loading backup settings: {e}")
    
    def on_stop_server_changed(self):
        """Handle stop server checkbox change"""
        try:
            stop_server = self.stop_server_var.get()
            self.main_window.config.set("stop_server_for_backup", stop_server)
            self.main_window.config.save_config()
            logging.info(f"Stop server for backup setting changed to: {stop_server}")
        except Exception as e:
            logging.error(f"Error saving stop server setting: {e}")
    
    def create_world_backup(self):
        """Create a world-only backup with server management"""
        if self.backup_in_progress:
            messagebox.showwarning("Backup in Progress", "A backup is already in progress. Please wait.")
            return
        
        # Validate server directory
        if not hasattr(self.main_window, 'server_jar_path') or not self.main_window.server_jar_path:
            messagebox.showerror("Error", "Please select a server JAR file first in the Server Control tab")
            return
        
        server_dir = os.path.dirname(self.main_window.server_jar_path)
        if not os.path.exists(server_dir):
            messagebox.showerror("Error", f"Server directory not found: {server_dir}")
            return
        
        # Check for world folders
        world_folders = self.find_world_folders(server_dir)
        if not world_folders:
            messagebox.showerror("Error", "No world folders found in server directory")
            return
        
        # Get backup details
        backup_name = self.backup_name_var.get().strip()
        if not backup_name:
            messagebox.showerror("Error", "Please enter a backup name")
            return
        
        backup_desc = self.backup_desc_var.get().strip()
        
        # Confirm backup
        world_list = "\n".join([f"• {folder}" for folder in world_folders])
        confirm_msg = f"Create world backup?\n\nName: {backup_name}\n\nWorld folders to backup:\n{world_list}\n\n"
        
        if self.stop_server_var.get():
            confirm_msg += "⚠️ Server will be stopped during backup and restarted afterward."
        else:
            confirm_msg += "ℹ️ Server will continue running during backup."
        
        if not messagebox.askyesno("Confirm Backup", confirm_msg):
            return
        
        # Start backup in thread
        self.backup_in_progress = True
        self.update_backup_status("Starting backup...")
        self.update_backup_button_states()
        
        backup_thread = threading.Thread(
            target=self._perform_world_backup,
            args=(server_dir, world_folders, backup_name, backup_desc),
            daemon=True
        )
        backup_thread.start()
    
    def find_world_folders(self, server_dir):
        """Find world folders in server directory"""
        world_folders = []
        common_world_names = ['world', 'world_nether', 'world_the_end']
        
        for folder_name in os.listdir(server_dir):
            folder_path = os.path.join(server_dir, folder_name)
            if os.path.isdir(folder_path):
                # Check if it's a world folder
                if (folder_name in common_world_names or 
                    folder_name.startswith('world') or
                    self.is_world_folder(folder_path)):
                    world_folders.append(folder_name)
        
        return sorted(world_folders)
    
    def is_world_folder(self, folder_path):
        """Check if a folder is a Minecraft world folder"""
        world_files = ['level.dat', 'session.lock']
        world_folders = ['data', 'playerdata', 'region']
        
        # Check for world files
        for file_name in world_files:
            if os.path.exists(os.path.join(folder_path, file_name)):
                return True
        
        # Check for world folders
        for folder_name in world_folders:
            if os.path.exists(os.path.join(folder_path, folder_name)):
                return True
        
        return False
    
    def _perform_world_backup(self, server_dir, world_folders, backup_name, backup_desc):
        """Perform the actual world backup"""
        server_was_running = False
        
        try:
            # Step 1: Stop server if requested
            if self.stop_server_var.get() and self.main_window.process_manager.is_server_running():
                server_was_running = True
                self.main_window.root.after(0, lambda: self.update_backup_status("Stopping server..."))
                
                # Save world and stop server
                self.main_window.process_manager.send_server_command("save-all")
                time.sleep(2)  # Wait for save
                self.main_window.process_manager.send_server_command("save-off")
                time.sleep(1)
                
                success = self.main_window.process_manager.stop_server()
                if not success:
                    raise Exception("Failed to stop server")
                
                time.sleep(3)  # Wait for complete shutdown
            
            # Step 2: Create backup
            self.main_window.root.after(0, lambda: self.update_backup_status("Creating world backup..."))
            
            backup_info = self._create_world_backup_archive(server_dir, world_folders, backup_name, backup_desc)
            
            # Step 3: Restart server if it was running
            if server_was_running:
                self.main_window.root.after(0, lambda: self.update_backup_status("Restarting server..."))
                
                success = self.main_window.process_manager.start_server(self.main_window.server_jar_path)
                if success:
                    self.main_window.root.after(0, lambda: self.update_backup_status("Server restarted successfully"))
                else:
                    self.main_window.root.after(0, lambda: self.update_backup_status("Warning: Failed to restart server"))
            
            # Step 4: Complete
            self.main_window.root.after(0, lambda: self.update_backup_status(f"Backup created: {backup_name}"))
            self.main_window.root.after(0, self.refresh_backup_list)
            
            # Show success message
            size_mb = backup_info.get('size_mb', 0)
            success_msg = f"World backup created successfully!\n\n"
            success_msg += f"Name: {backup_name}\n"
            success_msg += f"Size: {size_mb:.1f} MB\n"
            success_msg += f"Worlds: {len(world_folders)} folder(s)\n"
            if server_was_running:
                success_msg += f"\nServer was stopped and restarted."
            
            self.main_window.root.after(0, lambda: messagebox.showinfo("Backup Complete", success_msg))
            
        except Exception as e:
            error_msg = f"Backup failed: {str(e)}"
            self.main_window.root.after(0, lambda: self.update_backup_status(error_msg))
            self.main_window.root.after(0, lambda: messagebox.showerror("Backup Failed", error_msg))
            
            # Try to restart server if it was stopped
            if server_was_running:
                try:
                    self.main_window.process_manager.start_server(self.main_window.server_jar_path)
                except:
                    pass
        
        finally:
            self.backup_in_progress = False
            self.main_window.root.after(0, self.update_backup_button_states)
    
    def _create_world_backup_archive(self, server_dir, world_folders, backup_name, backup_desc):
        """Create the actual backup archive"""
        import zipfile
        from pathlib import Path
        
        # Create backups directory
        backups_dir = Path(server_dir) / "backups"
        backups_dir.mkdir(exist_ok=True)
        
        # Create backup file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{backup_name}_{timestamp}.zip"
        backup_path = backups_dir / backup_filename
        
        total_size = 0
        
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add backup info
            backup_info = f"Backup Name: {backup_name}\n"
            backup_info += f"Description: {backup_desc}\n"
            backup_info += f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            backup_info += f"Type: World folders only\n"
            backup_info += f"Worlds: {', '.join(world_folders)}\n"
            
            zipf.writestr("backup_info.txt", backup_info)
            
            # Add world folders
            for world_folder in world_folders:
                world_path = Path(server_dir) / world_folder
                if world_path.exists():
                    for file_path in world_path.rglob('*'):
                        if file_path.is_file():
                            # Skip session lock files
                            if file_path.name == 'session.lock':
                                continue
                            
                            try:
                                arcname = file_path.relative_to(Path(server_dir))
                                zipf.write(file_path, arcname)
                                total_size += file_path.stat().st_size
                            except Exception as e:
                                logging.warning(f"Failed to backup file {file_path}: {e}")
        
        backup_size = backup_path.stat().st_size
        
        return {
            'name': backup_name,
            'filename': backup_filename,
            'path': str(backup_path),
            'size_bytes': backup_size,
            'size_mb': backup_size / 1024 / 1024,
            'original_size_bytes': total_size,
            'worlds': world_folders,
            'description': backup_desc,
            'created': datetime.now()
        }
    
    def refresh_backup_list(self):
        """Refresh the backup list"""
        try:
            # Clear existing items
            for item in self.backup_list.get_children():
                self.backup_list.delete(item)
            
            if not hasattr(self.main_window, 'server_jar_path') or not self.main_window.server_jar_path:
                return
            
            server_dir = os.path.dirname(self.main_window.server_jar_path)
            backups_dir = os.path.join(server_dir, "backups")
            
            if not os.path.exists(backups_dir):
                return
            
            # Get backup files
            backup_files = []
            for file_name in os.listdir(backups_dir):
                if file_name.endswith('.zip'):
                    file_path = os.path.join(backups_dir, file_name)
                    stat = os.stat(file_path)
                    
                    backup_files.append({
                        'name': file_name[:-4],  # Remove .zip extension
                        'filename': file_name,
                        'path': file_path,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime)
                    })
            
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: x['modified'], reverse=True)
            
            # Add to tree
            for backup in backup_files:
                size_mb = backup['size'] / 1024 / 1024
                size_str = f"{size_mb:.1f} MB"
                date_str = backup['modified'].strftime("%Y-%m-%d %H:%M")
                
                self.backup_list.insert('', 'end', text='🌍', values=(
                    backup['name'],
                    date_str,
                    size_str
                ))
            
            self.update_backup_button_states()
            
        except Exception as e:
            logging.error(f"Error refreshing backup list: {e}")
    
    def restore_selected_backup(self):
        """Restore the selected backup"""
        selection = self.backup_list.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a backup to restore")
            return
        
        item = self.backup_list.item(selection[0])
        backup_name = item['values'][0]
        
        # Confirm restore
        confirm_msg = f"Restore backup '{backup_name}'?\n\n"
        confirm_msg += "⚠️ This will:\n"
        confirm_msg += "• Stop the server (if running)\n"
        confirm_msg += "• Replace current world folders\n"
        confirm_msg += "• Create a backup of current worlds\n"
        confirm_msg += "• Restart the server\n\n"
        confirm_msg += "This action cannot be undone!"
        
        if not messagebox.askyesno("Confirm Restore", confirm_msg):
            return
        
        messagebox.showinfo("Restore", "Restore functionality will be implemented in the next update")
    
    def delete_selected_backup(self):
        """Delete the selected backup"""
        selection = self.backup_list.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a backup to delete")
            return
        
        item = self.backup_list.item(selection[0])
        backup_name = item['values'][0]
        
        if not messagebox.askyesno("Confirm Delete", f"Delete backup '{backup_name}'?\n\nThis action cannot be undone!"):
            return
        
        try:
            server_dir = os.path.dirname(self.main_window.server_jar_path)
            backup_filename = backup_name + ".zip"
            backup_path = os.path.join(server_dir, "backups", backup_filename)
            
            if os.path.exists(backup_path):
                os.remove(backup_path)
                messagebox.showinfo("Success", f"Backup '{backup_name}' deleted successfully")
                self.refresh_backup_list()
            else:
                messagebox.showerror("Error", "Backup file not found")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete backup: {e}")
    
    def open_backup_folder(self):
        """Open the backup folder in file explorer"""
        try:
            if not hasattr(self.main_window, 'server_jar_path') or not self.main_window.server_jar_path:
                messagebox.showwarning("Warning", "Please select a server JAR file first")
                return
            
            server_dir = os.path.dirname(self.main_window.server_jar_path)
            backups_dir = os.path.join(server_dir, "backups")
            
            if not os.path.exists(backups_dir):
                os.makedirs(backups_dir)
            
            # Open in file explorer
            import subprocess
            import platform
            
            if platform.system() == "Windows":
                os.startfile(backups_dir)
            elif platform.system() == "Darwin":  # macOS
                subprocess.Popen(["open", backups_dir])
            else:  # Linux
                subprocess.Popen(["xdg-open", backups_dir])
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open backup folder: {e}")
    
    def on_backup_selected(self, event):
        """Handle backup selection change"""
        self.update_backup_button_states()
    
    def update_backup_button_states(self):
        """Update backup button states"""
        try:
            has_selection = bool(self.backup_list.selection())
            
            if self.restore_backup_btn:
                self.restore_backup_btn.configure(state=tk.NORMAL if has_selection else tk.DISABLED)
            
            if self.delete_backup_btn:
                self.delete_backup_btn.configure(state=tk.NORMAL if has_selection else tk.DISABLED)
            
            if self.create_backup_btn:
                self.create_backup_btn.configure(state=tk.DISABLED if self.backup_in_progress else tk.NORMAL)
                
        except Exception as e:
            logging.error(f"Error updating backup button states: {e}")
    
    def update_backup_status(self, status_text):
        """Update backup status label"""
        if self.backup_status_label:
            self.backup_status_label.configure(text=status_text)
        
        # Also update footer
        if hasattr(self.main_window, 'footer') and self.main_window.footer:
            self.main_window.footer.update_status(status_text)
    
    def update_theme(self):
        """Update backup tab theme"""
        super().update_theme()
        
        # Update any theme-specific components here
        pass
