"""
Mod Installation Dialog for Minecraft Server Manager
Provides guided mod installation with validation and options
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import threading
from typing import Optional, Dict, Any, List
import webbrowser

class ModInstaller:
    """Advanced mod installation dialog with validation and options"""
    
    def __init__(self, parent, modmanager, thememanager, source_path: str = None):
        self.parent = parent
        self.modmanager = modmanager
        self.thememanager = thememanager
        self.source_path = source_path
        
        # State
        self.modinfo = None
        self.conflicts = []
        self.dependencies = []
        self.install_options = {
            'enable_immediately': True,
            'install_dependencies': True,
            'create_backup': True,
            'overwrite_existing': False,
            'validate_compatibility': True
        }
        
        # UI components
        self.dialog = None
        self.progress_var = None
        self.status_var = None
        self.install_btn = None
        
        # Result
        self.result = False
        
        self.create_dialog()
        if self.source_path:
            self.load_mod_info()
    
    def create_dialog(self):
        """Create the installation dialog"""
        theme = self.thememanager.get_current_theme()
        
        # Create dialog window
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Mod Installer")
        self.dialog.geometry("700x650")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (700 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (650 // 2)
        self.dialog.geometry(f"700x650+{x}+{y}")
        
        self.dialog.configure(bg=theme.get('bg_primary', 'white'))
        
        # Create sections
        self.create_header()
        self.create_file_selection()
        self.create_mod_information()
        self.create_compatibility_check()
        self.create_installation_options()
        self.create_progress_section()
        self.create_buttons()
        
        # Handle window close
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_cancel)
    
    def create_header(self):
        """Create the dialog header"""
        theme = self.thememanager.get_current_theme()
        
        header_frame = tk.Frame(
            self.dialog, 
            bg=theme.get('bg_secondary', 'lightblue'), 
            height=70
        )
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        header_content = tk.Frame(header_frame, bg=theme.get('bg_secondary', 'lightblue'))
        header_content.pack(expand=True, pady=15)
        
        tk.Label(
            header_content,
            text="Mod Installer",
            font=('Segoe UI', 18, 'bold'),
            bg=theme.get('bg_secondary', 'lightblue'),
            fg=theme.get('accent', 'darkblue')
        ).pack()
        
        tk.Label(
            header_content,
            text="Install and configure mods for your server",
            font=('Segoe UI', 10),
            bg=theme.get('bg_secondary', 'lightblue'),
            fg=theme.get('text_primary', 'black')
        ).pack()
    
    def create_file_selection(self):
        """Create file selection section"""
        theme = self.thememanager.get_current_theme()
        
        main_frame = tk.Frame(self.dialog, bg=theme.get('bg_primary', 'white'))
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        file_frame = tk.LabelFrame(
            main_frame,
            text="📁 Select Mod File",
            font=('Segoe UI', 11, 'bold'),
            bg=theme.get('bg_primary', 'white'),
            fg=theme.get('text_primary', 'black'),
            pady=10
        )
        file_frame.pack(fill='x', pady=(0, 15))
        
        file_content = tk.Frame(file_frame, bg=theme.get('bg_primary', 'white'))
        file_content.pack(fill='x', padx=15, pady=10)
        
        # File path entry
        self.file_var = tk.StringVar(value=self.source_path or "")
        file_entry = tk.Entry(
            file_content,
            textvariable=self.file_var,
            font=('Segoe UI', 10),
            state='readonly',
            width=60,
            bg='white'
        )
        file_entry.pack(side='left', fill='x', expand=True)
        
        # Browse button
        browse_btn = tk.Button(
            file_content,
            text="Browse...",
            command=self.browse_file,
            font=('Segoe UI', 10),
            bg=theme.get('accent', 'blue'),
            fg='white',
            padx=20,
            pady=6,
            cursor='hand2',
            relief='flat'
        )
        browse_btn.pack(side='right', padx=(15, 0))
        
        # Drag and drop hint
        hint_label = tk.Label(
            file_frame,
            text="💡 Tip: You can also drag and drop .jar files here",
            font=('Segoe UI', 9, 'italic'),
            bg=theme.get('bg_primary', 'white'),
            fg=theme.get('text_secondary', 'gray')
        )
        hint_label.pack(pady=(5, 10))
        
        # Store main frame reference for other sections
        self.main_frame = main_frame
    
    def create_mod_information(self):
        """Create mod information section"""
        theme = self.thememanager.get_current_theme()
        
        info_frame = tk.LabelFrame(
            self.main_frame,
            text="📋 Mod Information",
            font=('Segoe UI', 11, 'bold'),
            bg=theme.get('bg_primary', 'white'),
            fg=theme.get('text_primary', 'black'),
            pady=10
        )
        info_frame.pack(fill='x', pady=(0, 15))
        
        # Create notebook for organized info display
        notebook = ttk.Notebook(info_frame)
        notebook.pack(fill='both', expand=True, padx=15, pady=10)
        
        # Basic info tab
        basic_frame = tk.Frame(notebook, bg=theme.get('bg_primary', 'white'))
        notebook.add(basic_frame, text="Basic Info")
        
        self.info_text = tk.Text(
            basic_frame,
            height=6,
            font=('Segoe UI', 9),
            bg=theme.get('bg_secondary', 'lightgray'),
            fg=theme.get('text_primary', 'black'),
            state='disabled',
            wrap='word',
            relief='flat',
            padx=10,
            pady=10
        )
        self.info_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Dependencies tab
        deps_frame = tk.Frame(notebook, bg=theme.get('bg_primary', 'white'))
        notebook.add(deps_frame, text="Dependencies")
        
        self.deps_text = tk.Text(
            deps_frame,
            height=6,
            font=('Segoe UI', 9),
            bg=theme.get('bg_secondary', 'lightgray'),
            fg=theme.get('text_primary', 'black'),
            state='disabled',
            wrap='word',
            relief='flat',
            padx=10,
            pady=10
        )
        self.deps_text.pack(fill='both', expand=True, padx=5, pady=5)
    
    def create_compatibility_check(self):
        """Create compatibility check section"""
        theme = self.thememanager.get_current_theme()
        
        compat_frame = tk.LabelFrame(
            self.main_frame,
            text="⚠️ Compatibility Check",
            font=('Segoe UI', 11, 'bold'),
            bg=theme.get('bg_primary', 'white'),
            fg=theme.get('text_primary', 'black'),
            pady=10
        )
        compat_frame.pack(fill='x', pady=(0, 15))
        
        self.compat_text = tk.Text(
            compat_frame,
            height=4,
            font=('Segoe UI', 9),
            bg=theme.get('bg_secondary', 'lightgray'),
            fg=theme.get('text_primary', 'black'),
            state='disabled',
            wrap='word',
            relief='flat',
            padx=10,
            pady=10
        )
        self.compat_text.pack(fill='both', expand=True, padx=15, pady=10)
    
    def create_installation_options(self):
        """Create installation options section"""
        theme = self.thememanager.get_current_theme()
        
        options_frame = tk.LabelFrame(
            self.main_frame,
            text="⚙️ Installation Options",
            font=('Segoe UI', 11, 'bold'),
            bg=theme.get('bg_primary', 'white'),
            fg=theme.get('text_primary', 'black'),
            pady=10
        )
        options_frame.pack(fill='x', pady=(0, 15))
        
        options_content = tk.Frame(options_frame, bg=theme.get('bg_primary', 'white'))
        options_content.pack(fill='x', padx=15, pady=10)
        
        # Create checkboxes for options
        self.option_vars = {}
        
        options = [
            ('enable_immediately', '✅ Enable mod immediately after installation'),
            ('install_dependencies', '🔗 Automatically install missing dependencies'),
            ('create_backup', '💾 Create backup before installation'),
            ('validate_compatibility', '🔍 Validate mod compatibility'),
            ('overwrite_existing', '⚠️ Overwrite existing mod if present')
        ]
        
        # Create options in two columns
        left_col = tk.Frame(options_content, bg=theme.get('bg_primary', 'white'))
        left_col.pack(side='left', fill='both', expand=True)
        
        right_col = tk.Frame(options_content, bg=theme.get('bg_primary', 'white'))
        right_col.pack(side='right', fill='both', expand=True)
        
        for i, (key, text) in enumerate(options):
            var = tk.BooleanVar(value=self.install_options[key])
            self.option_vars[key] = var
            
            parent_col = left_col if i < 3 else right_col
            
            cb = tk.Checkbutton(
                parent_col,
                text=text,
                variable=var,
                font=('Segoe UI', 9),
                bg=theme.get('bg_primary', 'white'),
                fg=theme.get('text_primary', 'black'),
                selectcolor=theme.get('bg_secondary', 'lightgray'),
                anchor='w'
            )
            cb.pack(anchor='w', pady=3, padx=10)
    
    def create_progress_section(self):
        """Create progress section"""
        theme = self.thememanager.get_current_theme()
        
        progress_frame = tk.Frame(self.main_frame, bg=theme.get('bg_primary', 'white'))
        progress_frame.pack(fill='x', pady=(0, 15))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            length=660,
            mode='determinate',
            style='Horizontal.TProgressbar'
        )
        progress_bar.pack(pady=(0, 8))
        
        # Status label
        self.status_var = tk.StringVar(value="Ready to install")
        status_label = tk.Label(
            progress_frame,
            textvariable=self.status_var,
            font=('Segoe UI', 9),
            bg=theme.get('bg_primary', 'white'),
            fg=theme.get('text_secondary', 'gray')
        )
        status_label.pack()
    
    def create_buttons(self):
        """Create buttons section"""
        theme = self.thememanager.get_current_theme()
        
        button_frame = tk.Frame(self.dialog, bg=theme.get('bg_primary', 'white'))
        button_frame.pack(fill='x', pady=20)
        
        # Button container for centering
        button_container = tk.Frame(button_frame, bg=theme.get('bg_primary', 'white'))
        button_container.pack()
        
        # Cancel button
        cancel_btn = tk.Button(
            button_container,
            text="Cancel",
            command=self.on_cancel,
            font=('Segoe UI', 11),
            bg='#6c757d',
            fg='white',
            padx=25,
            pady=10,
            cursor='hand2',
            relief='flat'
        )
        cancel_btn.pack(side='left', padx=(0, 15))
        
        # Advanced options button
        advanced_btn = tk.Button(
            button_container,
            text="Advanced...",
            command=self.show_advanced_options,
            font=('Segoe UI', 11),
            bg='#17a2b8',
            fg='white',
            padx=25,
            pady=10,
            cursor='hand2',
            relief='flat'
        )
        advanced_btn.pack(side='left', padx=(0, 15))
        
        # Install button
        self.install_btn = tk.Button(
            button_container,
            text="Install Mod",
            command=self.start_installation,
            font=('Segoe UI', 11, 'bold'),
            bg='#28a745',
            fg='white',
            padx=30,
            pady=10,
            cursor='hand2',
            relief='flat',
            state='disabled'
        )
        self.install_btn.pack(side='left')
    
    def browse_file(self):
        """Browse for mod file"""
        filepath = filedialog.askopenfilename(
            title="Select Mod File",
            filetypes=[
                ("JAR files", "*.jar"),
                ("All files", "*.*")
            ],
            initialdir=os.path.expanduser("~/Downloads")
        )
        
        if filepath:
            self.file_var.set(filepath)
            self.source_path = filepath
            self.load_mod_info()
    
    def load_mod_info(self):
        """Load and display mod information"""
        if not self.source_path or not os.path.exists(self.source_path):
            self.update_info_display("Please select a valid mod file")
            self.install_btn.configure(state='disabled')
            return
        
        def load_thread():
            try:
                self.status_var.set("Analyzing mod file...")
                self.progress_var.set(20)
                
                # Extract mod information using scanner
                from mod_scanner import ModScanner
                scanner = ModScanner()
                self.modinfo = scanner.extractmodinfo(self.source_path)
                
                self.progress_var.set(50)
                
                if self.modinfo:
                    # Check for conflicts
                    self.status_var.set("Checking for conflicts...")
                    self.conflicts = self.check_conflicts()
                    
                    self.progress_var.set(75)
                    
                    # Check dependencies
                    self.status_var.set("Analyzing dependencies...")
                    self.dependencies = self.check_dependencies()
                    
                    self.progress_var.set(100)
                    
                    # Update display on main thread
                    self.dialog.after(0, self.update_all_displays)
                else:
                    self.dialog.after(0, lambda: self.update_info_display("Could not extract mod information from file"))
                
                self.status_var.set("Analysis complete" if self.modinfo else "Analysis failed")
                
            except Exception as e:
                self.dialog.after(0, lambda: self.update_info_display(f"Error analyzing mod: {str(e)}"))
                self.status_var.set("Analysis failed")
        
        # Reset progress
        self.progress_var.set(0)
        
        # Start analysis in background thread
        threading.Thread(target=load_thread, daemon=True).start()
    
    def check_conflicts(self):
        """Check for mod conflicts"""
        conflicts = []
        
        if not self.modinfo or not hasattr(self.modmanager, 'installedmods'):
            return conflicts
        
        for existing_mod in self.modmanager.installedmods.values():
            # Check for same mod ID
            if existing_mod.modid == self.modinfo.modid:
                conflicts.append(f"Mod with same ID already installed: {existing_mod.name}")
            
            # Check explicit conflicts
            if hasattr(self.modinfo, 'conflicts') and existing_mod.modid in self.modinfo.conflicts:
                conflicts.append(f"Conflicting mod: {existing_mod.name}")
            
            if hasattr(existing_mod, 'conflicts') and self.modinfo.modid in existing_mod.conflicts:
                conflicts.append(f"Conflicting mod: {existing_mod.name}")
        
        return conflicts
    
    def check_dependencies(self):
        """Check mod dependencies"""
        dependencies = []
        
        if not self.modinfo or not hasattr(self.modinfo, 'dependencies'):
            return dependencies
        
        installed_mods = set()
        if hasattr(self.modmanager, 'installedmods'):
            installed_mods = set(self.modmanager.installedmods.keys())
        
        for dep in self.modinfo.dependencies:
            if dep not in installed_mods:
                dependencies.append(dep)
        
        return dependencies
    
    def update_all_displays(self):
        """Update all information displays"""
        if not self.modinfo:
            return
        
        # Update basic info
        self.update_basic_info()
        
        # Update dependencies
        self.update_dependencies_info()
        
        # Update compatibility check
        self.update_compatibility_info()
        
        # Enable/disable install button
        can_install = len(self.conflicts) == 0
        self.install_btn.configure(
            state='normal' if can_install else 'disabled',
            text="Install Mod" if can_install else "Cannot Install"
        )
    
    def update_basic_info(self):
        """Update basic mod information display"""
        if not self.modinfo:
            return
        
        info_lines = [
            f"📦 Name: {self.modinfo.name}",
            f"🏷️ Version: {self.modinfo.version}",
            f"👤 Author: {self.modinfo.author or 'Unknown'}",
            f"🆔 Mod ID: {self.modinfo.modid}",
            f"🔧 Loader: {self.modinfo.modloader.value.title() if hasattr(self.modinfo, 'modloader') and self.modinfo.modloader else 'Unknown'}",
            f"📊 Size: {self.modinfo.filesize / 1024 / 1024:.2f} MB",
            "",
            "📝 Description:",
            self.modinfo.description or "No description available."
        ]
        
        info_text = '\n'.join(info_lines)
        
        self.info_text.configure(state='normal')
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, info_text)
        self.info_text.configure(state='disabled')
    
    def update_dependencies_info(self):
        """Update dependencies information"""
        if hasattr(self.modinfo, 'dependencies') and self.modinfo.dependencies:
            deps_lines = ["🔗 Required Dependencies:"]
            
            for dep in self.modinfo.dependencies:
                status = "✅ Installed" if dep not in self.dependencies else "❌ Missing"
                deps_lines.append(f"  • {dep} - {status}")
            
            if self.dependencies:
                deps_lines.extend([
                    "",
                    "⚠️ Missing Dependencies:",
                    "These dependencies will be automatically installed if the option is enabled."
                ])
        else:
            deps_lines = ["✅ No dependencies required"]
        
        deps_text = '\n'.join(deps_lines)
        
        self.deps_text.configure(state='normal')
        self.deps_text.delete(1.0, tk.END)
        self.deps_text.insert(1.0, deps_text)
        self.deps_text.configure(state='disabled')
    
    def update_compatibility_info(self):
        """Update compatibility check information"""
        compat_lines = []
        
        if self.conflicts:
            compat_lines.extend([
                "❌ CONFLICTS DETECTED:",
                ""
            ])
            for conflict in self.conflicts:
                compat_lines.append(f"  • {conflict}")
            compat_lines.append("")
            compat_lines.append("⚠️ Installation cannot proceed with conflicts present.")
        else:
            compat_lines.extend([
                "✅ No conflicts detected",
                "✅ Mod appears compatible with current setup"
            ])
            
            if self.dependencies:
                compat_lines.extend([
                    "",
                    f"📋 {len(self.dependencies)} missing dependencies will be installed"
                ])
        
        compat_text = '\n'.join(compat_lines)
        
        self.compat_text.configure(state='normal')
        self.compat_text.delete(1.0, tk.END)
        self.compat_text.insert(1.0, compat_text)
        self.compat_text.configure(state='disabled')
    
    def update_info_display(self, text):
        """Update the basic info text widget"""
        self.info_text.configure(state='normal')
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, text)
        self.info_text.configure(state='disabled')
    
    def show_advanced_options(self):
        """Show advanced installation options dialog"""
        advanced_window = tk.Toplevel(self.dialog)
        advanced_window.title("Advanced Installation Options")
        advanced_window.geometry("400x300")
        advanced_window.transient(self.dialog)
        advanced_window.grab_set()
        
        # Center the window
        advanced_window.update_idletasks()
        x = (advanced_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (advanced_window.winfo_screenheight() // 2) - (300 // 2)
        advanced_window.geometry(f"400x300+{x}+{y}")
        
        theme = self.thememanager.get_current_theme()
        advanced_window.configure(bg=theme.get('bg_primary', 'white'))
        
        # Advanced options content
        tk.Label(
            advanced_window,
            text="Advanced Installation Options",
            font=('Segoe UI', 14, 'bold'),
            bg=theme.get('bg_primary', 'white'),
            fg=theme.get('text_primary', 'black')
        ).pack(pady=20)
        
        # Placeholder for future advanced options
        tk.Label(
            advanced_window,
            text="Additional options will be available here:\n\n"
                  "• Custom installation directory\n"
                  "• Mod profile selection\n"
                  "• Version compatibility override\n"
                  "• Custom dependency resolution",
            font=('Segoe UI', 10),
            bg=theme.get('bg_primary', 'white'),
            fg=theme.get('text_secondary', 'gray'),
            justify='left'
        ).pack(pady=20)
        
        tk.Button(
            advanced_window,
            text="Close",
            command=advanced_window.destroy,
            font=('Segoe UI', 10),
            bg=theme.get('accent', 'blue'),
            fg='white',
            padx=20,
            pady=8,
            cursor='hand2',
            relief='flat'
        ).pack(pady=20)
    
    def start_installation(self):
        """Start the mod installation process"""
        if not self.modinfo:
            messagebox.showerror("Error", "No valid mod selected")
            return
        
        if self.conflicts:
            messagebox.showerror("Error", "Cannot install mod with conflicts")
            return
        
        # Update options from checkboxes
        for key, var in self.option_vars.items():
            self.install_options[key] = var.get()
        
        # Disable install button
        self.install_btn.configure(state='disabled', text="Installing...")
        
        def install_thread():
            try:
                self.status_var.set("Installing mod...")
                self.progress_var.set(10)
                
                # Install dependencies first if enabled
                if self.install_options['install_dependencies'] and self.dependencies:
                    self.status_var.set("Installing dependencies...")
                    self.progress_var.set(30)
                    # TODO: Implement dependency installation
                
                # Create backup if enabled
                if self.install_options['create_backup']:
                    self.status_var.set("Creating backup...")
                    self.progress_var.set(50)
                    # TODO: Create backup
                
                # Install the mod
                self.status_var.set("Installing mod files...")
                self.progress_var.set(70)
                
                success, message = self.modmanager.installmod(
                    self.source_path,
                    self.modinfo,
                    self.install_options['enable_immediately']
                )
                
                self.progress_var.set(100)
                
                if success:
                    self.status_var.set("Installation completed successfully!")
                    self.result = True
                    self.dialog.after(1000, self.on_success)
                else:
                    self.status_var.set(f"Installation failed: {message}")
                    self.dialog.after(0, lambda: messagebox.showerror("Installation Failed", message))
                    self.install_btn.configure(state='normal', text="Install Mod")
                
            except Exception as e:
                error_msg = str(e)
                self.status_var.set(f"Installation error: {error_msg}")
                self.dialog.after(0, lambda: messagebox.showerror("Installation Error", error_msg))
                self.install_btn.configure(state='normal', text="Install Mod")
        
        threading.Thread(target=install_thread, daemon=True).start()
    
    def on_success(self):
        """Handle successful installation"""
        messagebox.showinfo("Success", f"Mod '{self.modinfo.name}' installed successfully!")
        self.dialog.destroy()
    
    def on_cancel(self):
        """Handle cancel/close"""
        self.result = False
        self.dialog.destroy()
    
    def show(self):
        """Show the dialog and return result"""
        self.dialog.wait_window()
        return self.result
