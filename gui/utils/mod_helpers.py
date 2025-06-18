"""
Mod Helper Functions for Minecraft Server Manager
Provides utility functions for mod operations and UI helpers
"""
import os
import json
import shutil
import hashlib
import subprocess
import platform
import webbrowser
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, filedialog

class ModHelpers:
    """Collection of helper functions for mod operations"""
    
    @staticmethod
    def validate_mod_file(filepath: str) -> Tuple[bool, str]:
        """Validate if file is a valid mod file"""
        try:
            if not os.path.exists(filepath):
                return False, "File does not exist"
            
            if not filepath.lower().endswith('.jar'):
                return False, "Only .jar files are supported"
            
            # Check file size (reasonable limits)
            file_size = os.path.getsize(filepath)
            if file_size == 0:
                return False, "File is empty"
            
            if file_size > 500 * 1024 * 1024:  # 500MB limit
                return False, "File is too large (over 500MB)"
            
            # Try to open as zip to verify it's not corrupted
            import zipfile
            try:
                with zipfile.ZipFile(filepath, 'r') as zf:
                    # Check for common mod files
                    files = zf.namelist()
                    has_mod_files = any(
                        fname in files for fname in [
                            'fabric.mod.json',
                            'META-INF/mods.toml',
                            'mcmod.info',
                            'quilt.mod.json'
                        ]
                    )
                    
                    if not has_mod_files:
                        return False, "File does not appear to be a valid mod"
            
            except zipfile.BadZipFile:
                return False, "File is corrupted or not a valid JAR file"
            
            return True, "Valid mod file"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    @staticmethod
    def calculate_file_hash(filepath: str, algorithm: str = 'sha256') -> str:
        """Calculate file hash for integrity checking"""
        try:
            if algorithm == 'sha256':
                hasher = hashlib.sha256()
            elif algorithm == 'md5':
                hasher = hashlib.md5()
            else:
                raise ValueError(f"Unsupported hash algorithm: {algorithm}")
            
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)
            
            return hasher.hexdigest()
            
        except Exception as e:
            print(f"Error calculating hash: {e}")
            return ""
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"
    
    @staticmethod
    def format_date(date_obj: datetime) -> str:
        """Format datetime for display"""
        if not date_obj:
            return "Unknown"
        
        now = datetime.now()
        diff = now - date_obj
        
        if diff.days == 0:
            if diff.seconds < 3600:  # Less than 1 hour
                minutes = diff.seconds // 60
                return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            else:  # Less than 1 day
                hours = diff.seconds // 3600
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.days == 1:
            return "Yesterday"
        elif diff.days < 7:
            return f"{diff.days} days ago"
        else:
            return date_obj.strftime("%Y-%m-%d")
    
    @staticmethod
    def open_file_location(filepath: str) -> bool:
        """Open file location in system file manager"""
        try:
            if not os.path.exists(filepath):
                return False
            
            system = platform.system()
            
            if system == "Windows":
                subprocess.run(["explorer", "/select,", filepath], check=True)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", "-R", filepath], check=True)
            elif system == "Linux":
                # Try different file managers
                file_managers = ["nautilus", "dolphin", "thunar", "nemo", "pcmanfm"]
                folder = os.path.dirname(filepath)
                
                for fm in file_managers:
                    try:
                        subprocess.run([fm, folder], check=True)
                        break
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue
                else:
                    # Fallback to xdg-open
                    subprocess.run(["xdg-open", folder], check=True)
            
            return True
            
        except Exception as e:
            print(f"Error opening file location: {e}")
            return False
    
    @staticmethod
    def open_url(url: str) -> bool:
        """Open URL in default browser"""
        try:
            webbrowser.open(url)
            return True
        except Exception as e:
            print(f"Error opening URL: {e}")
            return False
    
    @staticmethod
    def copy_file_safe(source: str, destination: str) -> Tuple[bool, str]:
        """Safely copy file with error handling"""
        try:
            # Ensure destination directory exists
            dest_dir = os.path.dirname(destination)
            os.makedirs(dest_dir, exist_ok=True)
            
            # Copy file
            shutil.copy2(source, destination)
            
            # Verify copy
            if os.path.exists(destination):
                source_size = os.path.getsize(source)
                dest_size = os.path.getsize(destination)
                
                if source_size == dest_size:
                    return True, "File copied successfully"
                else:
                    return False, "File copy verification failed - size mismatch"
            else:
                return False, "File copy failed - destination not found"
                
        except PermissionError:
            return False, "Permission denied - check file permissions"
        except OSError as e:
            return False, f"System error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    @staticmethod
    def create_backup_filename(original_path: str, backup_dir: str) -> str:
        """Create unique backup filename"""
        filename = os.path.basename(original_path)
        name, ext = os.path.splitext(filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        backup_filename = f"{name}_backup_{timestamp}{ext}"
        return os.path.join(backup_dir, backup_filename)
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for cross-platform compatibility"""
        # Characters not allowed in filenames
        invalid_chars = '<>:"/\\|?*'
        
        # Replace invalid characters with underscores
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Remove leading/trailing spaces and dots
        filename = filename.strip(' .')
        
        # Ensure filename is not empty
        if not filename:
            filename = "untitled"
        
        # Limit length (most filesystems have 255 char limit)
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:200-len(ext)] + ext
        
        return filename
    
    @staticmethod
    def export_mod_list(mod_list: List[Dict], filepath: str, format_type: str = 'json') -> Tuple[bool, str]:
        """Export mod list to file in various formats"""
        try:
            if format_type.lower() == 'json':
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(mod_list, f, indent=2, ensure_ascii=False, default=str)
            
            elif format_type.lower() == 'txt':
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write("Minecraft Server Mod List\n")
                    f.write("=" * 50 + "\n\n")
                    
                    for mod in mod_list:
                        f.write(f"Name: {mod.get('name', 'Unknown')}\n")
                        f.write(f"Version: {mod.get('version', 'Unknown')}\n")
                        f.write(f"Author: {mod.get('author', 'Unknown')}\n")
                        f.write(f"Status: {'Enabled' if mod.get('enabled', False) else 'Disabled'}\n")
                        f.write(f"File: {mod.get('filename', 'Unknown')}\n")
                        if mod.get('description'):
                            f.write(f"Description: {mod['description']}\n")
                        f.write("\n" + "-" * 30 + "\n\n")
            
            elif format_type.lower() == 'csv':
                import csv
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    if mod_list:
                        writer = csv.DictWriter(f, fieldnames=mod_list[0].keys())
                        writer.writeheader()
                        writer.writerows(mod_list)
            
            elif format_type.lower() == 'html':
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>Minecraft Server Mod List</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .enabled { color: green; }
        .disabled { color: red; }
    </style>
</head>
<body>
    <h1>Minecraft Server Mod List</h1>
    <table>
        <tr>
            <th>Name</th>
            <th>Version</th>
            <th>Author</th>
            <th>Status</th>
            <th>Description</th>
        </tr>
""")
                    
                    for mod in mod_list:
                        status_class = "enabled" if mod.get('enabled', False) else "disabled"
                        status_text = "Enabled" if mod.get('enabled', False) else "Disabled"
                        
                        f.write(f"""
        <tr>
            <td>{mod.get('name', 'Unknown')}</td>
            <td>{mod.get('version', 'Unknown')}</td>
            <td>{mod.get('author', 'Unknown')}</td>
            <td class="{status_class}">{status_text}</td>
            <td>{mod.get('description', '')[:100]}{'...' if len(mod.get('description', '')) > 100 else ''}</td>
        </tr>""")
                    
                    f.write("""
    </table>
</body>
</html>""")
            
            else:
                return False, f"Unsupported format: {format_type}"
            
            return True, f"Mod list exported successfully to {filepath}"
            
        except Exception as e:
            return False, f"Export failed: {str(e)}"
    
    @staticmethod
    def create_mod_shortcut(mod_path: str, shortcut_dir: str) -> Tuple[bool, str]:
        """Create desktop shortcut for mod (Windows only)"""
        try:
            if platform.system() != "Windows":
                return False, "Shortcuts only supported on Windows"
            
            import win32com.client
            
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut_path = os.path.join(shortcut_dir, f"{os.path.basename(mod_path)}.lnk")
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = mod_path
            shortcut.WorkingDirectory = os.path.dirname(mod_path)
            shortcut.IconLocation = mod_path
            shortcut.save()
            
            return True, f"Shortcut created: {shortcut_path}"
            
        except ImportError:
            return False, "pywin32 package required for shortcut creation"
        except Exception as e:
            return False, f"Shortcut creation failed: {str(e)}"
    
    @staticmethod
    def get_mod_icon(mod_path: str) -> Optional[str]:
        """Extract mod icon if available"""
        try:
            import zipfile
            from PIL import Image
            import tempfile
            
            with zipfile.ZipFile(mod_path, 'r') as zf:
                # Common icon locations in mods
                icon_paths = [
                    'icon.png',
                    'assets/icon.png',
                    'pack.png',
                    'logo.png'
                ]
                
                for icon_path in icon_paths:
                    if icon_path in zf.namelist():
                        # Extract icon to temporary file
                        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                            temp_file.write(zf.read(icon_path))
                            return temp_file.name
            
            return None
            
        except Exception as e:
            print(f"Error extracting mod icon: {e}")
            return None
    
    @staticmethod
    def show_confirmation_dialog(parent, title: str, message: str, 
                                icon: str = 'question') -> bool:
        """Show confirmation dialog with better formatting"""
        return messagebox.askyesno(title, message, icon=icon, parent=parent)
    
    @staticmethod
    def show_error_dialog(parent, title: str, message: str, details: str = None):
        """Show error dialog with optional details"""
        if details:
            # Create custom dialog with details
            dialog = tk.Toplevel(parent)
            dialog.title(title)
            dialog.geometry("500x300")
            dialog.transient(parent)
            dialog.grab_set()
            
            # Center dialog
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
            y = (dialog.winfo_screenheight() // 2) - (300 // 2)
            dialog.geometry(f"500x300+{x}+{y}")
            
            # Main message
            tk.Label(
                dialog,
                text=message,
                font=('Segoe UI', 10),
                wraplength=450,
                justify='left'
            ).pack(pady=20, padx=20)
            
            # Details section
            details_frame = tk.LabelFrame(dialog, text="Details", font=('Segoe UI', 9))
            details_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
            
            details_text = tk.Text(
                details_frame,
                font=('Courier New', 8),
                wrap='word',
                state='disabled'
            )
            details_scrollbar = tk.Scrollbar(details_frame, command=details_text.yview)
            details_text.configure(yscrollcommand=details_scrollbar.set)
            
            details_text.pack(side='left', fill='both', expand=True, padx=5, pady=5)
            details_scrollbar.pack(side='right', fill='y', pady=5)
            
            # Insert details
            details_text.configure(state='normal')
            details_text.insert('1.0', details)
            details_text.configure(state='disabled')
            
            # Close button
            tk.Button(
                dialog,
                text="Close",
                command=dialog.destroy,
                font=('Segoe UI', 10),
                padx=20,
                pady=5
            ).pack(pady=(0, 20))
            
        else:
            messagebox.showerror(title, message, parent=parent)
    
    @staticmethod
    def select_multiple_files(title: str = "Select Files", 
                             filetypes: List[Tuple[str, str]] = None) -> List[str]:
        """Select multiple files with file dialog"""
        if filetypes is None:
            filetypes = [("JAR files", "*.jar"), ("All files", "*.*")]
        
        return list(filedialog.askopenfilenames(
            title=title,
            filetypes=filetypes,
            initialdir=os.path.expanduser("~/Downloads")
        ))
    
    @staticmethod
    def create_progress_dialog(parent, title: str = "Processing..."):
        """Create a progress dialog"""
        progress_dialog = tk.Toplevel(parent)
        progress_dialog.title(title)
        progress_dialog.geometry("400x150")
        progress_dialog.transient(parent)
        progress_dialog.grab_set()
        progress_dialog.resizable(False, False)
        
        # Center dialog
        progress_dialog.update_idletasks()
        x = (progress_dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (progress_dialog.winfo_screenheight() // 2) - (150 // 2)
        progress_dialog.geometry(f"400x150+{x}+{y}")
        
        # Progress bar
        from tkinter import ttk
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(
            progress_dialog,
            variable=progress_var,
            maximum=100,
            length=350,
            mode='determinate'
        )
        progress_bar.pack(pady=20)
        
        # Status label
        status_var = tk.StringVar(value="Initializing...")
        status_label = tk.Label(
            progress_dialog,
            textvariable=status_var,
            font=('Segoe UI', 9)
        )
        status_label.pack(pady=10)
        
        # Cancel button
        cancelled = [False]  # Use list to allow modification in nested function
        
        def cancel():
            cancelled[0] = True
            progress_dialog.destroy()
        
        cancel_btn = tk.Button(
            progress_dialog,
            text="Cancel",
            command=cancel,
            font=('Segoe UI', 9),
            padx=20,
            pady=5
        )
        cancel_btn.pack(pady=10)
        
        return {
            'dialog': progress_dialog,
            'progress_var': progress_var,
            'status_var': status_var,
            'cancelled': cancelled
        }
