"""
First-Time Server Setup Wizard for Minecraft Server Manager
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import threading
import time
import subprocess
import logging
from pathlib import Path

class ServerSetupWizard:
    """Complete first-time server setup wizard"""
    
    def __init__(self, parent, theme_manager, main_window):
        self.parent = parent
        self.theme_manager = theme_manager
        self.main_window = main_window
        
        # Wizard state
        self.current_step = 0
        self.total_steps = 6
        self.setup_data = {
            'jar_path': '',
            'server_dir': '',
            'server_name': 'My Minecraft Server',
            'server_port': 25565,
            'max_players': 20,
            'gamemode': 'survival',
            'difficulty': 'normal',
            'online_mode': True,
            'enable_whitelist': False,
            'max_memory': '2G',
            'setup_complete': False
        }
        
        # Progress tracking
        self.setup_process = None
        self.setup_thread = None
        self.progress_var = None
        self.status_var = None
        
        self.create_wizard()
    
    def create_wizard(self):
        """Create the setup wizard window"""
        self.wizard = tk.Toplevel(self.parent)
        self.wizard.title("🧙‍♂️ Minecraft Server Setup Wizard")
        self.wizard.geometry("800x700")
        self.wizard.transient(self.parent)
        self.wizard.grab_set()
        self.wizard.resizable(True, True)
        
        # Center the window
        self.wizard.update_idletasks()
        x = (self.wizard.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.wizard.winfo_screenheight() // 2) - (700 // 2)
        self.wizard.geometry(f"800x700+{x}+{y}")

        
        theme = self.theme_manager.get_current_theme()
        self.wizard.configure(bg=theme['bg_primary'])
        
        # Create wizard layout
        self.create_wizard_layout()
        
        # Show first step
        self.show_step(0)
        
        # Handle window close
        self.wizard.protocol("WM_DELETE_WINDOW", self.on_wizard_close)
    
    def create_wizard_layout(self):
        """Create the main wizard layout with guaranteed navigation buttons"""
        theme = self.theme_manager.get_current_theme()
        
        print("🔍 Starting create_wizard_layout...")
        
        # Header
        header_frame = tk.Frame(self.wizard, bg=theme.get('bg_secondary', '#e9ecef'), height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        header_content = tk.Frame(header_frame, bg=theme.get('bg_secondary', '#e9ecef'))
        header_content.pack(expand=True, pady=15)
        
        # Title
        self.title_label = tk.Label(
            header_content,
            text="🧙‍♂️ Welcome to Server Setup Wizard",
            bg=theme.get('bg_secondary', '#e9ecef'),
            fg=theme.get('accent', '#007bff'),
            font=('Segoe UI', 16, 'bold')
        )
        self.title_label.pack()
        
        # Subtitle
        self.subtitle_label = tk.Label(
            header_content,
            text="Let's set up your Minecraft server in just a few steps!",
            bg=theme.get('bg_secondary', '#e9ecef'),
            fg=theme.get('text_secondary', '#6c757d'),
            font=('Segoe UI', 10)
        )
        self.subtitle_label.pack()
        
        print("🔍 Header created")
        
        # Progress bar
        progress_frame = tk.Frame(self.wizard, bg=theme.get('bg_primary', 'white'))
        progress_frame.pack(fill="x", padx=20, pady=10)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=self.total_steps,
            length=660,
            mode='determinate'
        )
        self.progress_bar.pack()
        
        self.step_label = tk.Label(
            progress_frame,
            text=f"Step 1 of {self.total_steps}",
            bg=theme.get('bg_primary', 'white'),
            fg=theme.get('text_secondary', '#6c757d'),
            font=('Segoe UI', 9)
        )
        self.step_label.pack(pady=(5, 0))
        
        print("🔍 Progress bar created")
        
        # Content area - FIXED HEIGHT to leave room for navigation
        self.content_frame = tk.Frame(self.wizard, bg=theme.get('bg_primary', 'white'), height=350)
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.content_frame.pack_propagate(False)  # Don't let content resize the frame
        
        print("🔍 Content frame created")
        
        # GUARANTEED NAVIGATION BUTTONS - ALWAYS VISIBLE
        print("🔧 Creating navigation buttons...")
        
        # BEAUTIFUL Navigation frame with proper theming
        nav_frame = tk.Frame(
            self.wizard, 
            bg=theme.get('bg_secondary', '#343a40'),  # Dark elegant background
            relief='flat', 
            bd=0, 
            height=70
        )
        nav_frame.pack(fill="x", side="bottom", padx=0, pady=0)
        nav_frame.pack_propagate(False)

        # Add a subtle top border
        top_border = tk.Frame(nav_frame, bg=theme.get('border', '#dee2e6'), height=1)
        top_border.pack(fill="x")

        # Inner button container with matching background
        button_container = tk.Frame(nav_frame, bg=theme.get('bg_secondary', '#343a40'))
        button_container.pack(fill="both", expand=True, padx=20, pady=15)
        
        # Back button
        self.back_btn = tk.Button(
            button_container,
            text="← Back",
            command=self.previous_step,
            bg='#6c757d',
            fg='white',
            font=('Segoe UI', 11, 'bold'),
            padx=25,
            pady=8,
            relief='raised',
            bd=2,
            cursor='hand2',
            state=tk.DISABLED  # Initially disabled
        )
        self.back_btn.pack(side="left")
        
        # Cancel button
        self.cancel_btn = tk.Button(
            button_container,
            text="Cancel",
            command=self.on_wizard_close,
            bg='#dc3545',
            fg='white',
            font=('Segoe UI', 11, 'bold'),
            padx=25,
            pady=8,
            relief='raised',
            bd=2,
            cursor='hand2'
        )
        self.cancel_btn.pack(side="left", padx=(15, 0))
        
        # Next button
        self.next_btn = tk.Button(
            button_container,
            text="Next →",
            command=self.next_step,
            bg='#007bff',
            fg='white',
            font=('Segoe UI', 11, 'bold'),
            padx=30,
            pady=8,
            relief='raised',
            bd=2,
            cursor='hand2'
        )
        self.next_btn.pack(side="right")
        
        # Force update to ensure everything appears
        self.wizard.update_idletasks()
        
        print("✅ Navigation buttons created successfully!")
        print(f"Back button exists: {hasattr(self, 'back_btn')}")
        print(f"Next button exists: {hasattr(self, 'next_btn')}")
        print(f"Cancel button exists: {hasattr(self, 'cancel_btn')}")
        
        # Add button hover effects
        self.setup_button_hover_effects()
        
        print("🔍 create_wizard_layout completed")

    def setup_button_hover_effects(self):
        """Add hover effects to navigation buttons"""
        try:
            # Back button hover effect
            def back_enter(e):
                if self.back_btn['state'] != 'disabled':
                    self.back_btn.configure(bg='#5a6268')
            
            def back_leave(e):
                if self.back_btn['state'] != 'disabled':
                    self.back_btn.configure(bg='#6c757d')
            
            self.back_btn.bind("<Enter>", back_enter)
            self.back_btn.bind("<Leave>", back_leave)
            
            # Cancel button hover effect
            def cancel_enter(e):
                self.cancel_btn.configure(bg='#c82333')
            
            def cancel_leave(e):
                self.cancel_btn.configure(bg='#dc3545')
            
            self.cancel_btn.bind("<Enter>", cancel_enter)
            self.cancel_btn.bind("<Leave>", cancel_leave)
            
            # Next button hover effect
            def next_enter(e):
                self.next_btn.configure(bg='#0056b3')
            
            def next_leave(e):
                self.next_btn.configure(bg='#007bff')
            
            self.next_btn.bind("<Enter>", next_enter)
            self.next_btn.bind("<Leave>", next_leave)
            
            print("✅ Button hover effects added")
            
        except Exception as e:
            print(f"Warning: Could not add hover effects: {e}")

    def show_step(self, step_num):
        """Show specific wizard step"""
        print(f"🔍 Showing step {step_num}")
        
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Update progress
        self.current_step = step_num
        self.progress_var.set(step_num + 1)
        self.step_label.configure(text=f"Step {step_num + 1} of {self.total_steps}")
        
        # Show step content
        if step_num == 0:
            self.show_welcome_step()
        elif step_num == 1:
            self.show_jar_selection_step()
        elif step_num == 2:
            self.show_basic_config_step()
        elif step_num == 3:
            self.show_advanced_config_step()
        elif step_num == 4:
            self.show_initial_setup_step()
        elif step_num == 5:
            self.show_completion_step()
        
        # Update navigation buttons
        self.update_navigation_buttons()
        
        print(f"✅ Step {step_num} displayed")

    def update_navigation_buttons(self):
        """Update navigation button states"""
        try:
            # Back button - enabled if not on first step
            if hasattr(self, 'back_btn'):
                if self.current_step > 0:
                    self.back_btn.configure(state=tk.NORMAL)
                else:
                    self.back_btn.configure(state=tk.DISABLED)
            
            # Next button text and state
            if hasattr(self, 'next_btn'):
                if self.current_step == self.total_steps - 1:
                    self.next_btn.configure(text="Finish & Close")
                else:
                    self.next_btn.configure(text="Next →")
            
            print(f"✅ Navigation buttons updated for step {self.current_step}")
            
        except Exception as e:
            print(f"Error updating navigation buttons: {e}")

    def next_step(self):
        """Go to next step"""
        print(f"🔍 Next step clicked from step {self.current_step}")
        
        if self.current_step < self.total_steps - 1:
            # Validate current step before proceeding
            if self.validate_current_step():
                self.show_step(self.current_step + 1)
        else:
            # Last step - finish wizard
            self.finish_wizard()

    def previous_step(self):
        """Go to previous step"""
        print(f"🔍 Previous step clicked from step {self.current_step}")
        
        if self.current_step > 0:
            self.show_step(self.current_step - 1)

    def on_wizard_close(self):
        """Handle wizard window close"""
        print("🔍 Cancel/Close clicked")
        
        if messagebox.askyesno("Cancel Setup", "Are you sure you want to cancel the server setup?"):
            self.wizard.destroy()

    def validate_current_step(self):
        """Validate current step before proceeding"""
        if self.current_step == 1:  # JAR selection step
            if not self.setup_data.get('jar_path'):
                messagebox.showerror("Error", "Please select a server JAR file")
                return False
            if not os.path.exists(self.setup_data['jar_path']):
                messagebox.showerror("Error", "Selected JAR file does not exist")
                return False
        
        return True

    def finish_wizard(self):
        """Finish the wizard"""
        print("🔍 Finishing wizard...")
        
        try:
            # Mark setup as completed
            self.main_window.config.set("setup_wizard_completed", True)
            self.main_window.config.save_config()
            
            messagebox.showinfo("Setup Complete", "Server setup completed successfully!")
            self.wizard.destroy()
            
        except Exception as e:
            print(f"Error finishing wizard: {e}")
            messagebox.showerror("Error", f"Error completing setup: {e}")


    def add_button_hover_effects(self):
        """Add hover effects to navigation buttons"""
        def on_enter(button, color):
            def handler(event):
                button.configure(bg=color)
            return handler
        
        def on_leave(button, color):
            def handler(event):
                button.configure(bg=color)
            return handler
        
        # Back button hover
        self.back_btn.bind("<Enter>", on_enter(self.back_btn, '#5a6268'))
        self.back_btn.bind("<Leave>", on_leave(self.back_btn, '#6c757d'))
        
        # Cancel button hover
        self.cancel_btn.bind("<Enter>", on_enter(self.cancel_btn, '#c82333'))
        self.cancel_btn.bind("<Leave>", on_leave(self.cancel_btn, '#dc3545'))
        
        # Next button hover
        self.next_btn.bind("<Enter>", on_enter(self.next_btn, '#0056b3'))
        self.next_btn.bind("<Leave>", on_leave(self.next_btn, '#007bff'))

    
    def show_step(self, step_num):
        """Show specific wizard step"""
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Update progress
        self.current_step = step_num
        self.progress_var.set(step_num + 1)
        self.step_label.configure(text=f"Step {step_num + 1} of {self.total_steps}")
        
        # Show step content
        if step_num == 0:
            self.show_welcome_step()
        elif step_num == 1:
            self.show_jar_selection_step()
        elif step_num == 2:
            self.show_basic_config_step()
        elif step_num == 3:
            self.show_advanced_config_step()
        elif step_num == 4:
            self.show_initial_setup_step()
        elif step_num == 5:
            self.show_completion_step()
        
        # Update navigation buttons
        self.update_navigation_buttons()
    
    def show_welcome_step(self):
        """Step 0: Welcome and introduction"""
        theme = self.theme_manager.get_current_theme()
        
        self.title_label.configure(text="🧙‍♂️ Welcome to Server Setup Wizard")
        self.subtitle_label.configure(text="Let's set up your Minecraft server in just a few steps!")
        
        content = tk.Frame(self.content_frame, bg=theme['bg_primary'])
        content.pack(fill="both", expand=True)
        
        # Welcome message
        welcome_text = """🎮 This wizard will help you create a new Minecraft server from scratch!

Here's what we'll do together:

🔸 Step 1: Select your server JAR file
🔸 Step 2: Configure basic server settings
🔸 Step 3: Set advanced options
🔸 Step 4: Initialize the server and accept EULA
🔸 Step 5: Generate the world and complete setup

⚡ The entire process takes about 2-3 minutes and will:
• Automatically handle EULA acceptance
• Create all necessary server files
• Generate the Minecraft world
• Configure optimal settings for your system

🚀 Ready to create your server? Click "Next" to begin!"""
        
        text_widget = tk.Text(
            content,
            bg=theme['bg_card'],
            fg=theme['text_primary'],
            font=('Segoe UI', 11),
            relief='flat',
            bd=0,
            wrap=tk.WORD,
            padx=20,
            pady=20,
            state=tk.DISABLED
        )
        text_widget.pack(fill="both", expand=True)
        
        text_widget.configure(state=tk.NORMAL)
        text_widget.insert("1.0", welcome_text)
        text_widget.configure(state=tk.DISABLED)
    
    def show_jar_selection_step(self):
        """Step 1: JAR file selection"""
        theme = self.theme_manager.get_current_theme()
        
        self.title_label.configure(text="📁 Select Server JAR File")
        self.subtitle_label.configure(text="Choose your Minecraft server JAR file")
        
        content = tk.Frame(self.content_frame, bg=theme['bg_primary'])
        content.pack(fill="both", expand=True, pady=20)
        
        # JAR selection
        jar_frame = tk.Frame(content, bg=theme['bg_card'], relief='solid', bd=1)
        jar_frame.pack(fill="x", padx=20, pady=10)
        
        jar_content = tk.Frame(jar_frame, bg=theme['bg_card'])
        jar_content.pack(fill="x", padx=20, pady=20)
        
        tk.Label(
            jar_content,
            text="🎯 Server JAR File:",
            bg=theme['bg_card'],
            fg=theme['text_primary'],
            font=('Segoe UI', 12, 'bold')
        ).pack(anchor="w")
        
        jar_input_frame = tk.Frame(jar_content, bg=theme['bg_card'])
        jar_input_frame.pack(fill="x", pady=(10, 0))
        
        self.jar_path_var = tk.StringVar(value=self.setup_data['jar_path'])
        jar_entry = tk.Entry(
            jar_input_frame,
            textvariable=self.jar_path_var,
            bg=theme['input_bg'],
            fg=theme['text_primary'],
            font=('Segoe UI', 10),
            relief='flat',
            bd=5
        )
        jar_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        browse_btn = tk.Button(
            jar_input_frame,
            text="📁 Browse",
            command=self.browse_jar_file,
            bg=theme['accent'],
            fg='white',
            font=('Segoe UI', 10),
            padx=20,
            pady=5,
            relief='flat',
            cursor='hand2'
        )
        browse_btn.pack(side="right")
        
        # Info
        info_text = """💡 Tips for selecting your server JAR:

• Download from official Minecraft website or trusted sources
• Paper, Spigot, and Fabric servers are supported
• Make sure you have the correct version for your needs
• The JAR file will be copied to a new server directory"""
        
        info_label = tk.Label(
            content,
            text=info_text,
            bg=theme['bg_primary'],
            fg=theme['text_secondary'],
            font=('Segoe UI', 9),
            justify="left",
            anchor="nw"
        )
        info_label.pack(anchor="w", padx=20, pady=10)
    
    def show_basic_config_step(self):
        """Step 2: Basic configuration"""
        theme = self.theme_manager.get_current_theme()
        
        self.title_label.configure(text="⚙️ Basic Server Configuration")
        self.subtitle_label.configure(text="Configure essential server settings")
        
        content = tk.Frame(self.content_frame, bg=theme['bg_primary'])
        content.pack(fill="both", expand=True, pady=20)
        
        # Configuration form
        config_frame = tk.Frame(content, bg=theme['bg_card'], relief='solid', bd=1)
        config_frame.pack(fill="both", expand=True, padx=20)
        
        config_content = tk.Frame(config_frame, bg=theme['bg_card'])
        config_content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Server name
        self.create_config_field(config_content, "🏷️ Server Name:", "server_name", "text")
        
        # Port
        self.create_config_field(config_content, "🌐 Server Port:", "server_port", "number")
        
        # Max players
        self.create_config_field(config_content, "👥 Max Players:", "max_players", "number")
        
        # Gamemode
        self.create_config_field(config_content, "🎮 Default Gamemode:", "gamemode", "choice", 
                                ["survival", "creative", "adventure", "spectator"])
        
        # Difficulty
        self.create_config_field(config_content, "⚔️ Difficulty:", "difficulty", "choice",
                                ["peaceful", "easy", "normal", "hard"])
        
        # Max memory
        self.create_config_field(config_content, "💾 Max Memory:", "max_memory", "choice",
                                ["1G", "2G", "3G", "4G", "6G", "8G"])
    
    def show_advanced_config_step(self):
        """Step 3: Advanced configuration"""
        theme = self.theme_manager.get_current_theme()
        
        self.title_label.configure(text="🔧 Advanced Configuration")
        self.subtitle_label.configure(text="Optional settings for your server")
        
        content = tk.Frame(self.content_frame, bg=theme['bg_primary'])
        content.pack(fill="both", expand=True, pady=20)
        
        # Configuration form
        config_frame = tk.Frame(content, bg=theme['bg_card'], relief='solid', bd=1)
        config_frame.pack(fill="both", expand=True, padx=20)
        
        config_content = tk.Frame(config_frame, bg=theme['bg_card'])
        config_content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Online mode
        self.create_config_field(config_content, "🔐 Online Mode (Requires Premium Accounts):", "online_mode", "bool")
        
        # Whitelist
        self.create_config_field(config_content, "📋 Enable Whitelist:", "enable_whitelist", "bool")
        
        # Info about settings
        info_text = """ℹ️ Advanced Settings Explained:

🔐 Online Mode: 
   • ON: Only premium Minecraft accounts can join (recommended)
   • OFF: Cracked clients can join (use with Playit.gg for global access)

📋 Whitelist:
   • ON: Only approved players can join (you add them manually)
   • OFF: Anyone can join the server (less secure but easier for friends)"""
        
        info_label = tk.Label(
            content,
            text=info_text,
            bg=theme['bg_primary'],
            fg=theme['text_secondary'],
            font=('Segoe UI', 9),
            justify="left",
            anchor="nw"
        )
        info_label.pack(anchor="w", padx=20, pady=10)
    
    def show_initial_setup_step(self):
        """Step 4: Initial server setup and EULA"""
        theme = self.theme_manager.get_current_theme()
        
        self.title_label.configure(text="🚀 Initializing Server")
        self.subtitle_label.configure(text="Setting up server files and accepting EULA")
        
        content = tk.Frame(self.content_frame, bg=theme['bg_primary'])
        content.pack(fill="both", expand=True, pady=20)
        
        # Progress display
        progress_frame = tk.Frame(content, bg=theme['bg_card'], relief='solid', bd=1)
        progress_frame.pack(fill="both", expand=True, padx=20)
        
        progress_content = tk.Frame(progress_frame, bg=theme['bg_card'])
        progress_content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Status
        self.status_var = tk.StringVar(value="Ready to begin setup...")
        status_label = tk.Label(
            progress_content,
            textvariable=self.status_var,
            bg=theme['bg_card'],
            fg=theme['text_primary'],
            font=('Segoe UI', 12, 'bold')
        )
        status_label.pack(pady=10)
        
        # Progress bar for setup
        self.setup_progress_var = tk.DoubleVar()
        self.setup_progress = ttk.Progressbar(
            progress_content,
            variable=self.setup_progress_var,
            maximum=100,
            length=600,
            mode='determinate'
        )
        self.setup_progress.pack(pady=10)
        
        # Console output
        console_label = tk.Label(
            progress_content,
            text="📜 Setup Log:",
            bg=theme['bg_card'],
            fg=theme['text_primary'],
            font=('Segoe UI', 10, 'bold')
        )
        console_label.pack(anchor="w", pady=(20, 5))
        
        self.setup_console = tk.Text(
            progress_content,
            bg=theme['console_bg'],
            fg=theme['console_text'],
            font=('Consolas', 9),
            relief='flat',
            bd=0,
            wrap=tk.WORD,
            height=10,
            state=tk.DISABLED
        )
        self.setup_console.pack(fill="both", expand=True)
        
        # EULA notice
        eula_frame = tk.Frame(content, bg=theme['bg_primary'])
        eula_frame.pack(fill="x", padx=20, pady=10)
        
        eula_text = "⚖️ By proceeding, you agree to the Minecraft EULA (https://account.mojang.com/documents/minecraft_eula)"
        eula_label = tk.Label(
            eula_frame,
            text=eula_text,
            bg=theme['bg_primary'],
            fg=theme['warning'],
            font=('Segoe UI', 9),
            wraplength=600
        )
        eula_label.pack()
        
        # Auto-start setup if not already running
        if not hasattr(self, 'setup_started'):
            self.wizard.after(1000, self.start_server_setup)
            self.setup_started = True
    
    def show_completion_step(self):
        """Step 5: Setup completion"""
        theme = self.theme_manager.get_current_theme()
        
        self.title_label.configure(text="🎉 Setup Complete!")
        self.subtitle_label.configure(text="Your Minecraft server is ready to use!")
        
        content = tk.Frame(self.content_frame, bg=theme['bg_primary'])
        content.pack(fill="both", expand=True, pady=20)
        
        # Success message
        success_frame = tk.Frame(content, bg=theme['bg_card'], relief='solid', bd=1)
        success_frame.pack(fill="both", expand=True, padx=20)
        
        success_content = tk.Frame(success_frame, bg=theme['bg_card'])
        success_content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Success icon and message
        success_msg = tk.Label(
            success_content,
            text="✅ Server setup completed successfully!",
            bg=theme['bg_card'],
            fg=theme['success'],
            font=('Segoe UI', 14, 'bold')
        )
        success_msg.pack(pady=10)
        
        # Summary
        summary_text = f"""📋 Setup Summary:
        
🎯 Server Name: {self.setup_data['server_name']}
📁 Location: {self.setup_data['server_dir']}
🌐 Port: {self.setup_data['server_port']}
👥 Max Players: {self.setup_data['max_players']}
🎮 Gamemode: {self.setup_data['gamemode'].title()}
⚔️ Difficulty: {self.setup_data['difficulty'].title()}
💾 Memory: {self.setup_data['max_memory']}
🔐 Online Mode: {'Yes' if self.setup_data['online_mode'] else 'No'}

🎉 Your server is now ready to start!"""
        
        summary_label = tk.Label(
            success_content,
            text=summary_text,
            bg=theme['bg_card'],
            fg=theme['text_primary'],
            font=('Segoe UI', 10),
            justify="left",
            anchor="nw"
        )
        summary_label.pack(anchor="w", pady=10)
        
        # Next steps
        next_steps = """🚀 What's Next:
        
1. Click "Finish" to close this wizard
2. Your server will be automatically selected in the Server Control tab
3. Click "Start Server" to begin your Minecraft world
4. Share your server IP with friends to let them join!

💡 Pro Tip: Check the Health tab to monitor your server's performance."""
        
        next_label = tk.Label(
            content,
            text=next_steps,
            bg=theme['bg_primary'],
            fg=theme['text_secondary'],
            font=('Segoe UI', 9),
            justify="left",
            anchor="nw"
        )
        next_label.pack(anchor="w", padx=20, pady=10)
    
    def create_config_field(self, parent, label_text, config_key, field_type, choices=None):
        """Create a configuration field"""
        theme = self.theme_manager.get_current_theme()
        
        field_frame = tk.Frame(parent, bg=theme['bg_card'])
        field_frame.pack(fill="x", pady=5)
        
        # Label
        label = tk.Label(
            field_frame,
            text=label_text,
            bg=theme['bg_card'],
            fg=theme['text_primary'],
            font=('Segoe UI', 10),
            width=25,
            anchor="w"
        )
        label.pack(side="left")
        
        # Input field
        if field_type == "text" or field_type == "number":
            var = tk.StringVar(value=str(self.setup_data[config_key]))
            entry = tk.Entry(
                field_frame,
                textvariable=var,
                bg=theme['input_bg'],
                fg=theme['text_primary'],
                font=('Segoe UI', 10),
                relief='flat',
                bd=3,
                width=20
            )
            entry.pack(side="left", padx=10)
            entry.bind('<KeyRelease>', lambda e: self.update_config_value(config_key, var.get(), field_type))
            
        elif field_type == "bool":
            var = tk.BooleanVar(value=self.setup_data[config_key])
            check = tk.Checkbutton(
                field_frame,
                variable=var,
                bg=theme['bg_card'],
                fg=theme['text_primary'],
                selectcolor=theme['input_bg'],
                activebackground=theme['bg_card'],
                command=lambda: self.update_config_value(config_key, var.get(), field_type)
            )
            check.pack(side="left", padx=10)
            
        elif field_type == "choice" and choices:
            var = tk.StringVar(value=str(self.setup_data[config_key]))
            combo = ttk.Combobox(
                field_frame,
                textvariable=var,
                values=choices,
                state="readonly",
                width=18
            )
            combo.pack(side="left", padx=10)
            combo.bind("<<ComboboxSelected>>", lambda e: self.update_config_value(config_key, var.get(), field_type))
    
    def update_config_value(self, key, value, field_type):
        """Update configuration value"""
        try:
            if field_type == "number":
                self.setup_data[key] = int(value) if value.isdigit() else self.setup_data[key]
            elif field_type == "bool":
                self.setup_data[key] = bool(value)
            else:
                self.setup_data[key] = value
        except ValueError:
            pass  # Keep original value if conversion fails
    
    def browse_jar_file(self):
        """Browse for JAR file"""
        try:
            filename = filedialog.askopenfilename(
                title="Select Minecraft Server JAR",
                filetypes=[("JAR files", "*.jar"), ("All files", "*.*")],
                initialdir=os.getcwd()
            )
            if filename:
                self.jar_path_var.set(filename)
                self.setup_data['jar_path'] = filename
                
                # Suggest server directory
                jar_name = os.path.splitext(os.path.basename(filename))[0]
                suggested_dir = os.path.join(os.path.dirname(filename), f"{jar_name}_server")
                self.setup_data['server_dir'] = suggested_dir
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to select JAR file: {e}")
    
    def start_server_setup(self):
        """Start the server setup process"""
        if not self.setup_data['jar_path']:
            self.add_console_message("❌ No JAR file selected!")
            return
        
        self.setup_thread = threading.Thread(target=self._perform_setup, daemon=True)
        self.setup_thread.start()
    
    def _perform_setup(self):
        """Perform the actual server setup"""
        try:
            # Step 1: Create server directory
            self.update_setup_status("Creating server directory...", 10)
            server_dir = self.setup_data['server_dir']
            os.makedirs(server_dir, exist_ok=True)
            
            # Step 2: Copy JAR file
            self.update_setup_status("Copying server JAR...", 20)
            import shutil
            jar_dest = os.path.join(server_dir, "server.jar")
            shutil.copy2(self.setup_data['jar_path'], jar_dest)
            
            # Step 3: Initial server run to generate files
            self.update_setup_status("Running initial server setup...", 30)
            self._run_initial_server(jar_dest, server_dir)
            
            # Step 4: Accept EULA
            self.update_setup_status("Accepting EULA...", 50)
            self._accept_eula(server_dir)
            
            # Step 5: Configure server.properties
            self.update_setup_status("Configuring server properties...", 60)
            self._configure_server_properties(server_dir)
            
            # Step 6: Final server start for world generation
            self.update_setup_status("Generating world (this may take a moment)...", 70)
            self._generate_world(jar_dest, server_dir)
            
            # Step 7: Complete
            self.update_setup_status("Setup complete!", 100)
            
            # Update main window with new server
            self.wizard.after(0, self._finalize_setup)
            
        except Exception as e:
            self.update_setup_status(f"Setup failed: {str(e)}", 0)
            self.add_console_message(f"❌ Setup failed: {str(e)}")
    
    def _run_initial_server(self, jar_path, server_dir):
        """Run server initially to generate files"""
        java_path = self.main_window.config.get("java_path", "java")
        cmd = [java_path, "-jar", "server.jar", "nogui"]
        
        self.add_console_message("🚀 Running initial server setup...")
        
        process = subprocess.Popen(
            cmd,
            cwd=server_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        
        # Wait for process to complete (should exit quickly due to EULA)
        try:
            process.wait(timeout=30)
            self.add_console_message("✅ Initial setup completed")
        except subprocess.TimeoutExpired:
            process.kill()
            self.add_console_message("⚠️ Initial setup timed out, continuing...")
    
    def _accept_eula(self, server_dir):
        """Accept the EULA"""
        eula_path = os.path.join(server_dir, "eula.txt")
        
        try:
            with open(eula_path, 'w') as f:
                f.write("# Minecraft EULA acceptance\n")
                f.write("# Accepted automatically by Server Setup Wizard\n")
                f.write(f"# {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("eula=true\n")
            
            self.add_console_message("✅ EULA accepted")
            
        except Exception as e:
            raise Exception(f"Failed to accept EULA: {e}")
    
    def _configure_server_properties(self, server_dir):
        """Configure server.properties with user settings"""
        properties_path = os.path.join(server_dir, "server.properties")
        
        try:
            # Read existing properties
            properties = {}
            if os.path.exists(properties_path):
                with open(properties_path, 'r') as f:
                    for line in f:
                        if '=' in line and not line.startswith('#'):
                            key, value = line.strip().split('=', 1)
                            properties[key] = value
            
            # Update with user settings
            properties.update({
                'server-port': str(self.setup_data['server_port']),
                'max-players': str(self.setup_data['max_players']),
                'gamemode': self.setup_data['gamemode'],
                'difficulty': self.setup_data['difficulty'],
                'online-mode': str(self.setup_data['online_mode']).lower(),
                'white-list': str(self.setup_data['enable_whitelist']).lower(),
                'motd': self.setup_data['server_name']
            })
            
            # Write properties
            with open(properties_path, 'w') as f:
                f.write("# Minecraft Server Properties\n")
                f.write(f"# Generated by Server Setup Wizard on {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                for key, value in properties.items():
                    f.write(f"{key}={value}\n")
            
            self.add_console_message("✅ Server properties configured")
            
        except Exception as e:
            raise Exception(f"Failed to configure properties: {e}")
    
    def _generate_world(self, jar_path, server_dir):
        """Generate the world by running the server briefly"""
        java_path = self.main_window.config.get("java_path", "java")
        max_memory = self.setup_data['max_memory']
        
        cmd = [java_path, f"-Xmx{max_memory}", "-jar", "server.jar", "nogui"]
        
        self.add_console_message("🌍 Generating world...")
        
        process = subprocess.Popen(
            cmd,
            cwd=server_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        
        # Monitor output for world generation completion
        world_generated = False
        start_time = time.time()
        
        while time.time() - start_time < 120:  # 2 minute timeout
            try:
                line = process.stdout.readline()
                if line:
                    if "Done" in line and ("help" in line or "For help" in line):
                        world_generated = True
                        break
                elif process.poll() is not None:
                    break
                time.sleep(0.1)
            except:
                break
        
        # Stop the server
        try:
            if process.poll() is None:
                process.stdin.write("stop\n")
                process.stdin.flush()
                process.wait(timeout=30)
        except:
            process.kill()
        
        if world_generated:
            self.add_console_message("✅ World generated successfully")
        else:
            self.add_console_message("⚠️ World generation may not be complete")
    
    def _finalize_setup(self):
        """Finalize the setup and update main window"""
        try:
            # Update main window with new server
            jar_path = os.path.join(self.setup_data['server_dir'], "server.jar")
            self.main_window.server_jar_path = jar_path
            
            # Update configuration with new server settings
            self.main_window.config.set("last_server_jar", jar_path)
            self.main_window.config.set("max_memory", self.setup_data['max_memory'])
            
            # Mark setup wizard as completed - NEW ADDITION
            self.main_window.config.set("setup_wizard_completed", True)
            
            # Save all configuration changes
            self.main_window.config.save_config()
            
            # Update server control tab with new JAR path
            if 'server_control' in self.main_window.tabs:
                self.main_window.tabs['server_control'].server_jar_var.set(jar_path)
                
                # Also update the main window's internal path tracking
                self.main_window.tabs['server_control'].main_window.server_jar_path = jar_path
            
            # Update footer with success message
            self.main_window.footer.update_status(f"New server created: {self.setup_data['server_name']}")
            
            # Mark setup as complete in wizard data
            self.setup_data['setup_complete'] = True
            
            # Log successful completion
            logging.info(f"Server setup completed successfully: {self.setup_data['server_name']}")
            logging.info(f"Server location: {self.setup_data['server_dir']}")
            
            # Update console with completion message
            self.add_console_message("🎉 Server setup completed successfully!")
            self.add_console_message(f"📁 Server location: {self.setup_data['server_dir']}")
            self.add_console_message("✅ Ready to start your Minecraft server!")
            
            # Enable finish button and change its text
            self.next_btn.configure(
                text="🎉 Finish & Close", 
                command=self.finish_wizard,
                state=tk.NORMAL
            )
            
            # Update navigation buttons to reflect completion
            self.update_navigation_buttons()
            
        except Exception as e:
            error_msg = f"Finalization error: {e}"
            logging.error(error_msg)
            self.add_console_message(f"❌ {error_msg}")
            
            # Show error to user but don't completely fail
            try:
                messagebox.showerror("Setup Error", f"Setup completed but with errors: {error_msg}")
            except:
                pass  # Don't let messagebox errors crash the finalization

    
    def update_setup_status(self, status, progress):
        """Update setup status and progress"""
        def update():
            self.status_var.set(status)
            self.setup_progress_var.set(progress)
        
        self.wizard.after(0, update)
    
    def add_console_message(self, message):
        """Add message to setup console"""
        def add_msg():
            if hasattr(self, 'setup_console'):
                self.setup_console.configure(state=tk.NORMAL)
                self.setup_console.insert(tk.END, f"{time.strftime('%H:%M:%S')} {message}\n")
                self.setup_console.see(tk.END)
                self.setup_console.configure(state=tk.DISABLED)
        
        self.wizard.after(0, add_msg)
    
    def next_step(self):
        """Go to next step"""
        if self.current_step < self.total_steps - 1:
            # Validate current step
            if self.validate_current_step():
                self.show_step(self.current_step + 1)
    
    def previous_step(self):
        """Go to previous step"""
        if self.current_step > 0:
            self.show_step(self.current_step - 1)
    
    def validate_current_step(self):
        """Validate current step before proceeding"""
        if self.current_step == 1:  # JAR selection
            if not self.setup_data['jar_path']:
                messagebox.showerror("Error", "Please select a server JAR file")
                return False
            if not os.path.exists(self.setup_data['jar_path']):
                messagebox.showerror("Error", "Selected JAR file does not exist")
                return False
        
        return True
    
    def update_navigation_buttons(self):
        """Update navigation button states"""
        # Back button
        self.back_btn.configure(state=tk.NORMAL if self.current_step > 0 else tk.DISABLED)
        
        # Next button
        if self.current_step == self.total_steps - 1:
            if self.setup_data.get('setup_complete', False):
                self.next_btn.configure(text="Finish & Close", command=self.finish_wizard)
            else:
                self.next_btn.configure(state=tk.DISABLED)
        else:
            self.next_btn.configure(text="Next →", command=self.next_step, state=tk.NORMAL)
    
    def finish_wizard(self):
        """Finish the wizard"""
        self.main_window.footer.update_status("Server setup completed successfully!")
        messagebox.showinfo("Setup Complete", "Your Minecraft server has been set up successfully!\n\nYou can now start your server from the Server Control tab.")
        self.wizard.destroy()
    
    def on_wizard_close(self):
        """Handle wizard window close"""
        if self.current_step < self.total_steps - 1:
            if messagebox.askyesno("Cancel Setup", "Are you sure you want to cancel the server setup?"):
                self.wizard.destroy()
        else:
            self.wizard.destroy()
            
    def debug_buttons(self):
        """Debug navigation buttons"""
        print("=== BUTTON DEBUG ===")
        print(f"Back button exists: {hasattr(self, 'back_btn')}")
        print(f"Cancel button exists: {hasattr(self, 'cancel_btn')}")
        print(f"Next button exists: {hasattr(self, 'next_btn')}")
        
        if hasattr(self, 'next_btn'):
            print(f"Next button visible: {self.next_btn.winfo_viewable()}")
            print(f"Next button size: {self.next_btn.winfo_width()}x{self.next_btn.winfo_height()}")
            print(f"Next button position: {self.next_btn.winfo_x()},{self.next_btn.winfo_y()}")

    # Call this in show_step method:
    # self.debug_buttons()

