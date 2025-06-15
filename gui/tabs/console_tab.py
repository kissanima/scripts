"""
Console tab implementation
"""

import tkinter as tk
from .base_tab import BaseTab
from ..components.status_card import StatusCard
from ..components.modern_widgets import ModernButton, ModernEntry

class ConsoleTab(BaseTab):
    """Console tab for server output and command input"""
    
    def __init__(self, parent, theme_manager, main_window):
        self.main_window = main_window
        super().__init__(parent, theme_manager)
        self.console_text = None
        self.command_entry = None
        self.command_history = []
        self.history_index = -1
        self.create_content()
    
    def create_content(self):
        """Create console content"""
        theme = self.theme_manager.get_current_theme()
        
        content = tk.Frame(self.tab_frame, bg=theme['bg_primary'])
        content.pack(fill="both", expand=True, padx=theme['padding_large'], pady=theme['padding_large'])
        
        # Console output card
        console_card = StatusCard(content, "Server Console", "💻", self.theme_manager)
        console_card.pack(fill="both", expand=True, pady=(0, theme['margin_medium']))
        
        console_content = console_card.get_content_frame()
        
        # Console text widget with scrollbar
        console_frame = tk.Frame(console_content, bg=theme['bg_card'])
        console_frame.pack(fill="both", expand=True, padx=theme['padding_medium'], pady=theme['padding_medium'])
        
        self.console_text = tk.Text(
            console_frame,
            bg=theme['console_bg'],
            fg=theme['console_text'],
            font=('Consolas', theme['font_size_normal']),
            relief='flat',
            borderwidth=0,
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        
        console_scrollbar = tk.Scrollbar(console_frame, orient="vertical", command=self.console_text.yview)
        self.console_text.configure(yscrollcommand=console_scrollbar.set)
        
        self.console_text.pack(side="left", fill="both", expand=True)
        console_scrollbar.pack(side="right", fill="y")
        
        # Console controls
        controls_frame = tk.Frame(console_content, bg=theme['bg_card'])
        controls_frame.pack(fill="x", padx=theme['padding_medium'], pady=(0, theme['padding_medium']))
        
        # Auto-scroll checkbox
        self.auto_scroll_var = tk.BooleanVar(value=True)
        auto_scroll_check = tk.Checkbutton(
            controls_frame,
            text="Auto-scroll",
            variable=self.auto_scroll_var,
            bg=theme['bg_card'],
            fg=theme['text_secondary'],
            selectcolor=theme['input_bg'],
            activebackground=theme['bg_card'],
            font=('Segoe UI', theme['font_size_small'])
        )
        auto_scroll_check.pack(side="left")
        
        # Console action buttons
        console_buttons = tk.Frame(controls_frame, bg=theme['bg_card'])
        console_buttons.pack(side="right")
        
        ModernButton(console_buttons, "Clear", self.clear_console, "secondary", self.theme_manager, "small").pack(side="left", padx=(0, theme['margin_small']))
        ModernButton(console_buttons, "Save Log", self.save_console_log, "secondary", self.theme_manager, "small").pack(side="left")
        
        # Command input area
        input_card = StatusCard(content, "Command Input", "⌨️", self.theme_manager)
        input_card.pack(fill="x")
        
        input_content = input_card.get_content_frame()
        
        # Command input frame
        input_frame = tk.Frame(input_content, bg=theme['bg_card'])
        input_frame.pack(fill="x", padx=theme['padding_medium'], pady=theme['padding_medium'])
        
        # Command label
        cmd_label = tk.Label(input_frame, text="Command:", bg=theme['bg_card'], 
                            fg=theme['text_primary'], font=('Segoe UI', theme['font_size_normal'], 'bold'))
        cmd_label.pack(side="left")
        
        # Command entry
        self.command_entry = ModernEntry(input_frame, self.theme_manager)
        self.command_entry.pack(side="left", fill="x", expand=True, padx=(theme['padding_small'], theme['padding_small']))
        self.command_entry.bind("<Return>", self.send_command)
        self.command_entry.bind("<Up>", self.command_history_up)
        self.command_entry.bind("<Down>", self.command_history_down)
        
        # Send button
        ModernButton(input_frame, "Send", self.send_command, "primary", self.theme_manager, "normal").pack(side="right")
        
        # Quick commands
        quick_commands_frame = tk.Frame(input_content, bg=theme['bg_card'])
        quick_commands_frame.pack(fill="x", padx=theme['padding_medium'], pady=(0, theme['padding_medium']))
        
        quick_label = tk.Label(quick_commands_frame, text="Quick Commands:", bg=theme['bg_card'], 
                              fg=theme['text_secondary'], font=('Segoe UI', theme['font_size_small']))
        quick_label.pack(side="left")
        
        quick_buttons = tk.Frame(quick_commands_frame, bg=theme['bg_card'])
        quick_buttons.pack(side="left", padx=(theme['padding_small'], 0))
        
        quick_commands = ["save-all", "list", "weather clear", "time set day", "gamemode creative", "stop"]
        for cmd in quick_commands:
            ModernButton(quick_buttons, cmd, lambda c=cmd: self.send_quick_command(c), "secondary", self.theme_manager, "small").pack(side="left", padx=(0, theme['margin_small']))
        
        # Register components
        self.register_widget(console_card)
        self.register_widget(input_card)
        
        # Add welcome message
        self.add_console_message("=== Minecraft Server Console ===", "info")
        self.add_console_message("Server console output will appear here", "info")
        self.add_console_message("Type commands below to interact with the server", "info")
    
    def send_command(self, event=None):
        """Send command to server"""
        command = self.command_entry.get().strip()
        if not command:
            return
        
        # Add to history
        if command not in self.command_history:
            self.command_history.append(command)
            if len(self.command_history) > 50:  # Limit history
                self.command_history = self.command_history[-25:]
        
        self.history_index = -1
        
        # Clear entry
        self.command_entry.delete(0, tk.END)
        
        # Add command to console
        self.add_console_message(f"> {command}", "command")
        
        # Send to main window
        if hasattr(self.main_window, 'send_command'):
            self.main_window.send_command()
        else:
            self.add_console_message("Command sent (server interface not connected)", "warning")
    
    def send_quick_command(self, command):
        """Send a quick command"""
        self.command_entry.delete(0, tk.END)
        self.command_entry.insert(0, command)
        self.send_command()
    
    def command_history_up(self, event):
        """Navigate command history up"""
        if self.command_history and self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            command = self.command_history[-(self.history_index + 1)]
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, command)
    
    def command_history_down(self, event):
        """Navigate command history down"""
        if self.command_history and self.history_index > 0:
            self.history_index -= 1
            command = self.command_history[-(self.history_index + 1)]
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, command)
        elif self.history_index == 0:
            self.history_index = -1
            self.command_entry.delete(0, tk.END)
    
    def add_console_message(self, message, msg_type="normal"):
        """Add message to console"""
        if not self.console_text:
            return
        
        theme = self.theme_manager.get_current_theme()
        colors = {
            "normal": theme['console_text'],
            "info": theme['console_info'],
            "warning": theme['console_warning'],
            "error": theme['console_error'],
            "command": theme['accent']
        }
        
        self.console_text.configure(state=tk.NORMAL)
        
        # Insert message with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}\n"
        
        self.console_text.insert(tk.END, full_message)
        
        # Color the message
        start_line = self.console_text.index(tk.END + "-2l")
        end_line = self.console_text.index(tk.END + "-1l")
        
        # Create tag for this message type if it doesn't exist
        tag_name = f"msg_{msg_type}"
        self.console_text.tag_configure(tag_name, foreground=colors.get(msg_type, colors["normal"]))
        self.console_text.tag_add(tag_name, start_line, end_line)
        
        self.console_text.configure(state=tk.DISABLED)
        
        # Auto-scroll if enabled
        if self.auto_scroll_var.get():
            self.console_text.see(tk.END)
    
    def clear_console(self):
        """Clear the console"""
        self.console_text.configure(state=tk.NORMAL)
        self.console_text.delete(1.0, tk.END)
        self.console_text.configure(state=tk.DISABLED)
        self.add_console_message("Console cleared", "info")
    
    def save_console_log(self):
        """Save console log to file"""
        try:
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                title="Save Console Log",
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            if filename:
                with open(filename, 'w') as f:
                    f.write(self.console_text.get(1.0, tk.END))
                self.add_console_message(f"Log saved to {filename}", "info")
        except Exception as e:
            self.add_console_message(f"Failed to save log: {e}", "error")
    
    def get_console_widget(self):
        """Get console text widget for external updates"""
        return self.console_text
    
    def get_command_entry(self):
        """Get command entry widget"""
        return self.command_entry
