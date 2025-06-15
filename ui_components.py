"""
Custom UI Components with Minecraft-inspired styling
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageDraw, ImageTk
import math

# Import the theme functions at the top
try:
    from themes import get_theme, get_all_theme_names
except ImportError:
    # Fallback if themes module not available
    def get_theme(theme_name='minecraft_classic'):
        return {
            'bg_primary': '#2F2F2F',
            'bg_secondary': '#3E3E3E',
            'bg_tertiary': '#4A4A4A',
            'bg_card': '#383838',
            'accent_primary': '#55FF55',
            'accent_secondary': '#5555FF',
            'accent_tertiary': '#FFAA00',
            'success': '#55FF55',
            'warning': '#FFAA00',
            'error': '#FF5555',
            'info': '#55AAFF',
            'text_primary': '#FFFFFF',
            'text_secondary': '#CCCCCC',
            'text_muted': '#999999',
            'text_accent': '#55FF55',
            'console_bg': '#0F0F0F',
            'console_text': '#00FF41',
            'console_error': '#FF5555',
            'console_warning': '#FFAA00',
            'button_bg': '#55AA55',
            'button_hover': '#66BB66',
            'button_active': '#44AA44',
            'button_disabled': '#555555',
            'entry_bg': '#2A2A2A',
            'entry_border': '#55AA55',
            'entry_focus': '#66BB66',
            'frame_border': '#55AA55',
            'separator': '#444444',
            'health_excellent': '#00FF00',
            'health_good': '#55FF55',
            'health_warning': '#FFAA00',
            'health_critical': '#FF5555',
            'health_unknown': '#888888',
            'glow_color': '#55FF5522',
            'shadow_color': '#00000044',
            'tab_active': '#55AA55',
            'tab_inactive': '#333333',
            'tab_hover': '#44AA44',
        }

# Global theme reference - will be set by main application
_current_theme_name = 'minecraft_classic'
_theme_callback = None

def set_current_theme(theme_name):
    """Set the current theme for all components"""
    global _current_theme_name
    _current_theme_name = theme_name

def set_theme_callback(callback):
    """Set callback function to get current theme from main app"""
    global _theme_callback
    _theme_callback = callback

def get_current_theme():
    """Get the current theme"""
    if _theme_callback:
        return _theme_callback()
    return get_theme(_current_theme_name)

class MinecraftButton(tk.Button):
    """Custom button with Minecraft-style appearance"""
    
    def __init__(self, parent, text="", command=None, style="default", **kwargs):
        self.style_type = style
        super().__init__(parent, text=text, command=command, **kwargs)
        self.setup_style()
        self.bind_events()
    
    def setup_style(self):
        """Setup Minecraft-style appearance"""
        theme = get_current_theme()
        
        style_configs = {
            'default': {
                'bg': theme['button_bg'],
                'fg': theme['text_primary'],
                'activebackground': theme['button_hover'],
                'activeforeground': theme['text_primary'],
                'relief': 'raised',
                'bd': 2,
                'font': ('Segoe UI', 10, 'bold'),
                'cursor': 'hand2'
            },
            'accent': {
                'bg': theme['accent_primary'],
                'fg': theme['bg_primary'],
                'activebackground': theme['accent_secondary'],
                'activeforeground': theme['bg_primary'],
                'relief': 'raised',
                'bd': 2,
                'font': ('Segoe UI', 10, 'bold'),
                'cursor': 'hand2'
            },
            'danger': {
                'bg': theme['error'],
                'fg': theme['text_primary'],
                'activebackground': theme['error'],
                'activeforeground': theme['text_primary'],
                'relief': 'raised',
                'bd': 2,
                'font': ('Segoe UI', 10, 'bold'),
                'cursor': 'hand2'
            }
        }
        
        config = style_configs.get(self.style_type, style_configs['default'])
        self.configure(**config)
    
    def bind_events(self):
        """Bind hover and click events"""
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        self.bind("<ButtonRelease-1>", self.on_release)
    
    def on_enter(self, event):
        """Handle mouse enter"""
        theme = get_current_theme()
        if self.style_type == 'default':
            self.configure(bg=theme['button_hover'])
        elif self.style_type == 'accent':
            self.configure(bg=theme['accent_secondary'])
        elif self.style_type == 'danger':
            # Slightly darker red on hover
            self.configure(bg='#CC4444')
    
    def on_leave(self, event):
        """Handle mouse leave"""
        theme = get_current_theme()
        if self.style_type == 'default':
            self.configure(bg=theme['button_bg'])
        elif self.style_type == 'accent':
            self.configure(bg=theme['accent_primary'])
        elif self.style_type == 'danger':
            self.configure(bg=theme['error'])
    
    def on_click(self, event):
        """Handle mouse click"""
        self.configure(relief='sunken')
    
    def on_release(self, event):
        """Handle mouse release"""
        self.configure(relief='raised')
    
    def update_theme(self):
        """Update button theme"""
        self.setup_style()

class MinecraftFrame(tk.Frame):
    """Custom frame with Minecraft-style border and background"""
    
    def __init__(self, parent, title="", style="default", **kwargs):
        super().__init__(parent, **kwargs)
        self.title = title
        self.style_type = style
        self.title_frame = None
        self.setup_style()
        
        if title:
            self.create_title_bar()
    
    def setup_style(self):
        """Setup frame styling"""
        theme = get_current_theme()
        
        style_configs = {
            'default': {
                'bg': theme['bg_secondary'],
                'relief': 'raised',
                'bd': 2
            },
            'card': {
                'bg': theme['bg_card'],
                'relief': 'raised',
                'bd': 1
            },
            'console': {
                'bg': theme['console_bg'],
                'relief': 'sunken',
                'bd': 2
            }
        }
        
        config = style_configs.get(self.style_type, style_configs['default'])
        self.configure(**config)
    
    def create_title_bar(self):
        """Create a title bar for the frame"""
        theme = get_current_theme()
        
        self.title_frame = tk.Frame(self, bg=theme['accent_primary'], height=25)
        self.title_frame.pack(fill="x", side="top")
        self.title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            self.title_frame, 
            text=self.title, 
            bg=theme['accent_primary'],
            fg=theme['bg_primary'],
            font=('Segoe UI', 10, 'bold')
        )
        title_label.pack(side="left", padx=10, pady=3)
    
    def update_theme(self):
        """Update frame theme"""
        self.setup_style()
        if self.title_frame:
            theme = get_current_theme()
            self.title_frame.configure(bg=theme['accent_primary'])
            for child in self.title_frame.winfo_children():
                if isinstance(child, tk.Label):
                    child.configure(bg=theme['accent_primary'], fg=theme['bg_primary'])

class StatusIndicator(tk.Canvas):
    """Visual status indicator with Minecraft-style colors"""
    
    def __init__(self, parent, size=20, **kwargs):
        super().__init__(parent, width=size, height=size, **kwargs)
        self.size = size
        self.status = "unknown"
        self.setup_canvas()
        self.update_visual()
    
    def setup_canvas(self):
        """Setup canvas styling"""
        theme = get_current_theme()
        self.configure(
            bg=theme['bg_secondary'],
            highlightthickness=0,
            relief='flat'
        )
    
    def set_status(self, status):
        """Set the status and update visual"""
        self.status = status
        self.update_visual()
    
    def update_visual(self):
        """Update the visual representation"""
        self.delete("all")
        theme = get_current_theme()
        
        color = {
            'running': theme['health_good'],
            'stopped': theme['text_muted'],
            'warning': theme['health_warning'],
            'error': theme['health_critical'],
            'unknown': theme['health_unknown']
        }.get(self.status, theme['health_unknown'])
        
        # Draw main indicator circle
        margin = 2
        self.create_oval(
            margin, margin, 
            self.size - margin, self.size - margin,
            fill=color, outline=theme['bg_tertiary'], width=1
        )
        
        # Add pulsing effect for active status
        if self.status == 'running':
            self.create_oval(
                margin + 3, margin + 3,
                self.size - margin - 3, self.size - margin - 3,
                fill="", outline=theme['health_excellent'], width=1
            )
    
    def update_theme(self):
        """Update indicator theme"""
        self.setup_canvas()
        self.update_visual()

class ProgressBarMinecraft(tk.Canvas):
    """Custom progress bar with Minecraft-style appearance"""
    
    def __init__(self, parent, width=200, height=20, **kwargs):
        super().__init__(parent, width=width, height=height, **kwargs)
        self.width = width
        self.height = height
        self.progress = 0
        self.max_value = 100
        self.setup_canvas()
        self.update_progress()
    
    def setup_canvas(self):
        """Setup canvas styling"""
        theme = get_current_theme()
        self.configure(
            bg=theme['bg_tertiary'],
            highlightthickness=0,
            relief='sunken',
            bd=1
        )
    
    def set_progress(self, value, max_value=100):
        """Set progress value"""
        self.progress = max(0, min(value, max_value))
        self.max_value = max_value
        self.update_progress()
    
    def update_progress(self):
        """Update progress bar visual"""
        self.delete("all")
        theme = get_current_theme()
        
        # Calculate progress width
        progress_width = (self.progress / self.max_value) * (self.width - 4) if self.max_value > 0 else 0
        
        # Draw background
        self.create_rectangle(
            2, 2, self.width - 2, self.height - 2,
            fill=theme['bg_primary'], outline=""
        )
        
        # Draw progress fill
        if progress_width > 0:
            # Color based on progress level
            progress_percent = (self.progress / self.max_value) * 100
            if progress_percent >= 80:
                color = theme['health_excellent']
            elif progress_percent >= 60:
                color = theme['health_good']
            elif progress_percent >= 40:
                color = theme['health_warning']
            else:
                color = theme['health_critical']
            
            self.create_rectangle(
                2, 2, 2 + progress_width, self.height - 2,
                fill=color, outline=""
            )
            
            # Add shine effect (if glow_color is available)
            if 'glow_color' in theme:
                shine_width = progress_width * 0.3
                self.create_rectangle(
                    2, 2, 2 + shine_width, 2 + (self.height - 4) * 0.4,
                    fill=theme['glow_color'], outline=""
                )
    
    def update_theme(self):
        """Update progress bar theme"""
        self.setup_canvas()
        self.update_progress()

class MinecraftNotification(tk.Toplevel):
    """Minecraft-style notification popup"""
    
    def __init__(self, parent, message, notification_type="info", duration=3000):
        super().__init__(parent)
        self.message = message
        self.notification_type = notification_type
        self.duration = duration
        
        self.setup_window()
        self.create_content()
        self.show_notification()
        
        if duration > 0:
            self.after(duration, self.fade_out)
    
    def setup_window(self):
        """Setup notification window"""
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        
        # Position in top-right corner
        try:
            screen_width = self.winfo_screenwidth()
            x_pos = screen_width - 320
        except:
            x_pos = 100
            
        self.geometry("300x80+{}+{}".format(x_pos, 20))
    
    def create_content(self):
        """Create notification content"""
        theme = get_current_theme()
        
        # Set colors based on notification type
        colors = {
            'info': theme['info'],
            'success': theme['success'],
            'warning': theme['warning'],
            'error': theme['error']
        }
        
        bg_color = colors.get(self.notification_type, theme['info'])
        
        self.configure(bg=bg_color)
        
        # Create main frame
        main_frame = tk.Frame(self, bg=bg_color, padx=15, pady=10)
        main_frame.pack(fill="both", expand=True)
        
        # Notification icon (simple text for now)
        icons = {
            'info': 'ℹ',
            'success': '✓',
            'warning': '⚠',
            'error': '✗'
        }
        
        icon_label = tk.Label(
            main_frame,
            text=icons.get(self.notification_type, 'ℹ'),
            font=('Segoe UI', 16, 'bold'),
            bg=bg_color,
            fg=theme['text_primary']
        )
        icon_label.pack(side="left", padx=(0, 10))
        
        # Message
        message_label = tk.Label(
            main_frame,
            text=self.message,
            font=('Segoe UI', 10),
            bg=bg_color,
            fg=theme['text_primary'],
            wraplength=200,
            justify="left"
        )
        message_label.pack(side="left", fill="both", expand=True)
    
    def show_notification(self):
        """Show notification with slide-in effect"""
        # Simple show for now - could add animations
        self.deiconify()
    
    def fade_out(self):
        """Fade out and destroy notification"""
        # Simple destroy for now - could add fade animation
        try:
            self.destroy()
        except:
            pass

def create_minecraft_style():
    """Create and configure ttk styles for Minecraft theme"""
    style = ttk.Style()
    
    # This would be called from the main application to set up styles
    # Custom styling for ttk widgets to match Minecraft theme
    
    theme = get_current_theme()
    
    # Configure Notebook (tabs)
    style.configure(
        'Minecraft.TNotebook',
        background=theme['bg_primary'],
        borderwidth=0
    )
    
    style.configure(
        'Minecraft.TNotebook.Tab',
        background=theme['tab_inactive'],
        foreground=theme['text_primary'],
        padding=[20, 8],
        font=('Segoe UI', 10, 'bold')
    )
    
    style.map(
        'Minecraft.TNotebook.Tab',
        background=[
            ('active', theme['tab_hover']),
            ('selected', theme['tab_active'])
        ],
        foreground=[
            ('selected', theme['text_primary'])
        ]
    )
    
    return style

# Icon creation utilities
def create_minecraft_icon(icon_type, size=16):
    """Create simple Minecraft-style icons"""
    try:
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        if icon_type == 'server':
            # Simple server icon (cube)
            draw.rectangle([2, 2, size-2, size-2], fill='#55AA55', outline='#000000')
            draw.rectangle([4, 4, size-4, size-4], fill='#66BB66')
        
        elif icon_type == 'health':
            # Health heart icon
            draw.polygon([
                (size//2, size-2), (2, size//2), (size//4, 2),
                (size//2, size//4), (3*size//4, 2), (size-2, size//2)
            ], fill='#FF5555')
        
        elif icon_type == 'backup':
            # Chest icon
            draw.rectangle([2, 4, size-2, size-2], fill='#8B4513', outline='#000000')
            draw.rectangle([4, 2, size-4, 6], fill='#A0522D')
            draw.rectangle([size//2-1, 3, size//2+1, 5], fill='#FFD700')
        
        elif icon_type == 'settings':
            # Gear icon
            draw.ellipse([4, 4, size-4, size-4], fill='#888888', outline='#000000')
            draw.ellipse([6, 6, size-6, size-6], fill='#AAAAAA')
        
        elif icon_type == 'console':
            # Terminal icon
            draw.rectangle([2, 2, size-2, size-2], fill='#000000', outline='#55AA55')
            draw.text((4, 4), '>', fill='#55AA55')
        
        elif icon_type == 'dashboard':
            # Dashboard icon
            draw.rectangle([2, 2, size//2, size//2], fill='#55AA55')
            draw.rectangle([size//2+1, 2, size-2, size//2], fill='#5555AA')
            draw.rectangle([2, size//2+1, size//2, size-2], fill='#AA5555')
            draw.rectangle([size//2+1, size//2+1, size-2, size-2], fill='#AAAA55')
        
        return ImageTk.PhotoImage(image)
    
    except Exception as e:
        # Return None if image creation fails
        print(f"Warning: Could not create icon '{icon_type}': {e}")
        return None

# Theme update functions
def update_all_components_theme():
    """Update theme for all custom components"""
    # This would be called when theme changes to update all existing components
    pass
