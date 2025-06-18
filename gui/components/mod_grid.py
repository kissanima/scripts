# gui/components/modgrid.py
"""Grid view component for displaying mods"""
import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Callable, Optional, Set
from .mod_card import ModCard

class ModGrid:
    """Grid container for mod cards with scrolling and selection"""
    
    def __init__(self, parent, theme_manager, callbacks=None):
        self.parent = parent
        self.theme_manager = theme_manager  # Fixed: store as theme_manager
        self.callbacks = callbacks or {}
        
        # State
        self.mod_cards: Dict[str, ModCard] = {}
        self.selected_mods: Set[str] = set()
        self.view_mode = 'grid'  # 'grid' or 'list'
        self.sort_by = 'name'  # 'name', 'author', 'size', 'date'
        self.sort_reverse = False
        
        # UI components
        self.frame = None
        self.canvas = None
        self.scrollbar = None
        self.content_frame = None
        self.canvas_window = None
        
        # Layout settings
        self.card_width = 320
        self.card_height = 160
        self.padding = 10
        
        self.create_grid()
    
    def create_grid(self):
        """Create the scrollable grid container"""
        theme = self.theme_manager.get_current_theme()
        
        # Main container
        self.frame = tk.Frame(self.parent, bg=theme.get('bg_primary', 'white'))
        
        # Create canvas with scrollbar
        canvas_frame = tk.Frame(self.frame, bg=theme.get('bg_primary', 'white'))
        canvas_frame.pack(fill='both', expand=True)
        
        self.canvas = tk.Canvas(
            canvas_frame,
            bg=theme.get('bg_primary', 'white'),
            highlightthickness=0,
            relief='flat'
        )
        
        self.scrollbar = ttk.Scrollbar(
            canvas_frame,
            orient='vertical',
            command=self.canvas.yview
        )
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Content frame inside canvas
        self.content_frame = tk.Frame(self.canvas, bg=theme.get('bg_primary', 'white'))
        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.content_frame,
            anchor='nw'
        )
        
        # Pack canvas and scrollbar
        self.canvas.pack(side='left', fill='both', expand=True)
        self.scrollbar.pack(side='right', fill='y')
        
        # Bind events
        self.content_frame.bind('<Configure>', self.on_frame_configure)
        self.canvas.bind('<Configure>', self.on_canvas_configure)
        self.canvas.bind('<MouseWheel>', self.on_mousewheel)
        self.canvas.bind('<Button-1>', self.on_canvas_click)
        
        # Keyboard bindings
        self.canvas.bind('<Key>', self.on_key_press)
        self.canvas.focus_set()
    
    def on_frame_configure(self, event):
        """Handle content frame size changes"""
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
    
    def on_canvas_configure(self, event):
        """Handle canvas size changes"""
        # Update content frame width to match canvas
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)
        
        # Trigger layout update if needed
        self.update_layout()
    
    def on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def on_canvas_click(self, event):
        """Handle clicking on empty canvas area"""
        self.clear_selection()
    
    def on_key_press(self, event):
        """Handle keyboard shortcuts"""
        if event.keysym == 'a' and event.state & 0x0004:  # Ctrl+A
            self.select_all()
        elif event.keysym == 'Delete':
            self.delete_selected()
        elif event.keysym == 'Escape':
            self.clear_selection()
    
    def update_mods(self, mod_list):
        """Update the mod grid with new mods - FIXED GEOMETRY MANAGEMENT"""
        try:
            print(f"🎯 ModGrid.update_mods() called with {len(mod_list)} mods")
            
            # Use content_frame as parent container
            parent_container = self.content_frame
            print("✅ Using content_frame as parent container")
            
            # Clear existing mods first
            self.clear_mods()
            print("🧹 Cleared existing mods")
            
            # Store the mod list
            self.mods = mod_list[:]
            print(f"📝 Stored {len(self.mods)} mods in self.mods")
            
            # Initialize mod_cards as dict
            self.mod_cards = {}
            
            # Create mod cards
            print("🎨 Creating mod cards...")
            
            for i, mod_info in enumerate(mod_list):
                try:
                    print(f"  Creating card {i+1}: {mod_info.name}")
                    
                    # Create mod card with CORRECT parameter names
                    mod_card = ModCard(
                        parent=parent_container,
                        mod_info=mod_info,
                        theme_manager=self.theme_manager,
                        callbacks=self.callbacks
                    )
                    
                    print(f"  ✅ Created card for {mod_info.name}")
                    
                    # DON'T PACK HERE - let layout methods handle geometry
                    # mod_card.pack(fill='x', padx=5, pady=2)  # ← REMOVE THIS LINE
                    
                    # Store reference using mod_id as key
                    self.mod_cards[mod_info.mod_id] = mod_card
                    
                except Exception as card_error:
                    print(f"  ❌ Error creating card for {mod_info.name}: {card_error}")
                    import traceback
                    traceback.print_exc()
            
            # CRITICAL: Update display and canvas scroll region
            print("🔄 Updating display and canvas...")
            
            # Update the content frame first
            parent_container.update_idletasks()
            print("🔄 Updated content frame")
            
            # Apply initial layout (this will pack or grid the cards properly)
            self.update_layout()
            print("🔄 Applied layout to mod cards")
            
            # Force canvas to recognize new content
            if hasattr(self, 'canvas') and self.canvas:
                self.canvas.update_idletasks()
                self.canvas.after_idle(self._final_canvas_update)
                
                bbox = self.canvas.bbox("all")
                if bbox:
                    self.canvas.configure(scrollregion=bbox)
                    print(f"🔄 Set canvas scrollregion to: {bbox}")
                else:
                    self.canvas.configure(scrollregion=(0, 0, 0, len(mod_list) * 100))
                    print("🔄 Set fallback scrollregion")
                
                self.canvas.yview_moveto(0)
                print("🔄 Scrolled to top")
            
            print(f"🎉 SUCCESS! Created {len(self.mod_cards)} mod cards and updated canvas")
            
        except Exception as e:
            print(f"❌ Error in ModGrid.update_mods(): {e}")
            import traceback
            traceback.print_exc()

    
    def _final_canvas_update(self):
        """Final canvas update after content settles"""
        try:
            if hasattr(self, 'canvas') and self.canvas:
                self.canvas.update_idletasks()
                bbox = self.canvas.bbox("all")
                if bbox:
                    self.canvas.configure(scrollregion=bbox)
                    print(f"🔄 Final canvas update - scrollregion: {bbox}")
                else:
                    print("🔄 Final canvas update - no bbox found")
        except Exception as e:
            print(f"❌ Final canvas update error: {e}")
    
    def sort_mods(self, mod_list: List):
        """Sort mods based on current sort settings"""
        def sort_key(mod):
            if self.sort_by == 'name':
                return mod.name.lower()
            elif self.sort_by == 'author':
                return (mod.author or 'zzz').lower()
            elif self.sort_by == 'size':
                return mod.file_size
            elif self.sort_by == 'date':
                return mod.lastmodified or 0
            else:
                return mod.name.lower()
        
        return sorted(mod_list, key=sort_key, reverse=self.sort_reverse)
    
    def add_mod_card(self, mod_info):
        """Add a single mod card"""
        callbacks = {
            'on_card_select': self.on_card_select,
            'on_mod_toggle': self.on_mod_toggle,
            'on_mod_remove': self.on_mod_remove,
            'on_mod_favorite': self.on_mod_favorite,
            'on_mod_details': self.on_mod_details,
            'on_show_in_folder': self.on_show_in_folder,
        }
        
        card = ModCard(
            self.content_frame,
            mod_info,
            self.theme_manager,
            callbacks
        )
        
        self.mod_cards[mod_info.mod_id] = card
    
    def clear_mods(self):
        """Clear all mod cards"""
        try:
            if hasattr(self, 'mod_cards') and self.mod_cards:
                print(f"🧹 Clearing {len(self.mod_cards)} existing mod cards")
                
                # Handle dict (which is correct for this class)
                if isinstance(self.mod_cards, dict):
                    for card in self.mod_cards.values():
                        if hasattr(card, 'destroy'):
                            card.destroy()
                    self.mod_cards.clear()
                elif isinstance(self.mod_cards, list):
                    for card in self.mod_cards:
                        if hasattr(card, 'destroy'):
                            card.destroy()
                    self.mod_cards.clear()
                
                print("✅ Mod cards cleared")
            else:
                print("🔄 No mod cards to clear, initializing empty dict")
                self.mod_cards = {}
                
        except Exception as e:
            print(f"❌ Error clearing mod cards: {e}")
            self.mod_cards = {}  # Reset to empty dict
    
    def update_layout(self):
        """Update the grid layout based on current view mode"""
        if not self.mod_cards:
            return
        
        if self.view_mode == 'grid':
            self.layout_grid()
        else:
            self.layout_list()
        
        # Update scroll region
        self.content_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
    
    def layout_grid(self):
        """Layout cards in grid format - FIXED"""
        canvas_width = self.canvas.winfo_width()
        if canvas_width <= 1:  # Not yet rendered
            self.parent.after(100, self.update_layout)
            return
        
        # Calculate columns
        available_width = canvas_width - 20  # Account for padding
        columns = max(1, available_width // (self.card_width + self.padding))
        
        # Grid the cards
        row = 0
        col = 0
        
        for card in self.mod_cards.values():
            # IMPORTANT: Remove from pack manager first if it was packed
            try:
                card.pack_forget()  # Remove from pack
            except:
                pass
            
            # Grid the card
            card.grid(
                row=row,
                column=col,
                padx=self.padding//2,
                pady=self.padding//2,
                sticky='new'
            )
            
            col += 1
            if col >= columns:
                col = 0
                row += 1
        
        # Configure column weights for equal distribution
        for i in range(columns):
            self.content_frame.grid_columnconfigure(i, weight=1, minsize=self.card_width)

    
    def layout_list(self):
        """Layout cards in list format"""
        # Clear grid configuration
        for card in self.mod_cards.values():
            card.frame.grid_forget()
        
        # Pack in list format
        for card in self.mod_cards.values():
            card.frame.pack(
                fill='x',
                padx=self.padding,
                pady=self.padding//2,
                expand=False
            )
    
    def set_view_mode(self, mode: str):
        """Set the view mode ('grid' or 'list')"""
        if mode in ['grid', 'list'] and mode != self.view_mode:
            self.view_mode = mode
            self.update_layout()
            self.call_callback('on_view_mode_changed', mode)
    
    def set_sort_options(self, sort_by: str, reverse: bool = False):
        """Set sorting options and refresh display"""
        if sort_by != self.sort_by or reverse != self.sort_reverse:
            self.sort_by = sort_by
            self.sort_reverse = reverse
            
            # Re-sort and update if we have mods
            if self.mod_cards:
                mod_list = [card.mod_info for card in self.mod_cards.values()]
                self.update_mods(mod_list)
    
    # Selection methods
    def on_card_select(self, mod_id: str, multi_select: bool):
        """Handle card selection"""
        if not multi_select:
            self.clear_selection()
        
        if mod_id in self.selected_mods:
            self.deselect_mod(mod_id)
        else:
            self.select_mod(mod_id)
    
    def select_mod(self, mod_id: str):
        """Select a mod card"""
        if mod_id in self.mod_cards:
            self.selected_mods.add(mod_id)
            self.mod_cards[mod_id].select()
            self.call_callback('on_selection_changed', list(self.selected_mods))
    
    def deselect_mod(self, mod_id: str):
        """Deselect a mod card"""
        if mod_id in self.selected_mods:
            self.selected_mods.remove(mod_id)
            if mod_id in self.mod_cards:
                self.mod_cards[mod_id].deselect()
            self.call_callback('on_selection_changed', list(self.selected_mods))
    
    def clear_selection(self):
        """Clear all selections"""
        for mod_id in list(self.selected_mods):
            self.deselect_mod(mod_id)
    
    def select_all(self):
        """Select all mod cards"""
        for mod_id in self.mod_cards:
            if mod_id not in self.selected_mods:
                self.select_mod(mod_id)
    
    def get_selected_mods(self) -> List[str]:
        """Get list of selected mod IDs"""
        return list(self.selected_mods)
    
    def get_selected_count(self) -> int:
        """Get number of selected mods"""
        return len(self.selected_mods)
    
    # Card update methods
    def update_mod_card(self, mod_id: str, updated_mod_info):
        """Update a specific mod card"""
        if mod_id in self.mod_cards:
            self.mod_cards[mod_id].update_display(updated_mod_info)
    
    def remove_mod_card(self, mod_id: str):
        """Remove a mod card from display"""
        if mod_id in self.mod_cards:
            self.mod_cards[mod_id].destroy()
            del self.mod_cards[mod_id]
            self.selected_mods.discard(mod_id)
            self.update_layout()
    
    def refresh_card(self, mod_id: str):
        """Refresh a specific card's display"""
        if mod_id in self.mod_cards:
            card = self.mod_cards[mod_id]
            card.update_display(card.mod_info)
    
    # Callback handlers for card events
    def on_mod_toggle(self, mod_id: str):
        """Handle mod toggle request"""
        self.call_callback('on_mod_toggle', mod_id)
    
    def on_mod_remove(self, mod_id: str):
        """Handle mod removal request"""
        self.call_callback('on_mod_remove', mod_id)
    
    def on_mod_favorite(self, mod_id: str):
        """Handle favorite toggle request"""
        self.call_callback('on_mod_favorite', mod_id)
    
    def on_mod_details(self, mod_info):
        """Handle mod details request"""
        self.call_callback('on_mod_details', mod_info)
    
    def on_show_in_folder(self, filepath: str):
        """Handle show in folder request"""
        self.call_callback('on_show_in_folder', filepath)
    
    def delete_selected(self):
        """Delete all selected mods"""
        if self.selected_mods:
            selected_list = list(self.selected_mods)
            self.call_callback('on_bulk_remove', selected_list)
    
    # Filter methods
    def filter_mods(self, filter_func):
        """Filter visible mods based on a function"""
        for mod_id, card in self.mod_cards.items():
            if filter_func(card.mod_info):
                card.frame.grid() if self.view_mode == 'grid' else card.frame.pack()
            else:
                card.frame.grid_remove() if self.view_mode == 'grid' else card.frame.pack_forget()
    
    def search_mods(self, query: str):
        """Search mods by name, author, or description"""
        if not query:
            # Show all mods
            self.filter_mods(lambda mod: True)
            return
        
        query_lower = query.lower()
        
        def matches_query(mod):
            return (query_lower in mod.name.lower() or
                   (mod.author and query_lower in mod.author.lower()) or
                   (mod.description and query_lower in mod.description.lower()) or
                   query_lower in mod.mod_id.lower())
        
        self.filter_mods(matches_query)
    
    # Utility methods
    def call_callback(self, callback_name, *args):
        """Safely call a callback if it exists"""
        if callback_name in self.callbacks and callable(self.callbacks[callback_name]):
            try:
                self.callbacks[callback_name](*args)
            except Exception as e:
                print(f"Error in callback {callback_name}: {e}")
    
    def pack(self, **kwargs):
        """Pack the grid frame"""
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Grid the grid frame"""
        self.frame.grid(**kwargs)
    
    def get_mod_count(self) -> int:
        """Get total number of mods"""
        return len(self.mod_cards)
    
    def get_enabled_count(self) -> int:
        """Get number of enabled mods"""
        return sum(1 for card in self.mod_cards.values() if card.mod_info.is_enabled)
    
    def scroll_to_mod(self, mod_id: str):
        """Scroll to show a specific mod"""
        if mod_id in self.mod_cards:
            card = self.mod_cards[mod_id]
            # Calculate card position and scroll to it
            card.frame.update_idletasks()
            y = card.frame.winfo_y()
            canvas_height = self.canvas.winfo_height()
            total_height = self.content_frame.winfo_reqheight()
            
            if total_height > canvas_height:
                scroll_position = y / total_height
                self.canvas.yview_moveto(scroll_position)
    
    def debug_container_attributes(self):
        """Find the correct container attribute"""
        print("🔍 MOD GRID CONTAINER ATTRIBUTES:")
        
        # Check for common container attribute names
        container_names = [
            'scrollable_frame', 'content_frame', 'main_frame', 'grid_frame', 
            'container', 'inner_frame', 'canvas_frame', 'mod_container',
            'frame', 'parent_frame', 'display_frame'
        ]
        
        found_containers = []
        
        for attr_name in container_names:
            if hasattr(self, attr_name):
                attr_value = getattr(self, attr_name)
                print(f"✅ {attr_name}: {attr_value}")
                found_containers.append(attr_name)
            else:
                print(f"❌ {attr_name}: Not found")
        
        # Show all attributes that contain 'frame'
        all_frame_attrs = [attr for attr in dir(self) if 'frame' in attr.lower() and not attr.startswith('_')]
        print(f"🔍 All frame-related attributes: {all_frame_attrs}")
        
        # Show all widget-like attributes
        widget_attrs = []
        for attr in dir(self):
            if not attr.startswith('_'):
                try:
                    value = getattr(self, attr)
                    if hasattr(value, 'pack') or hasattr(value, 'grid') or hasattr(value, 'place'):
                        widget_attrs.append(attr)
                except:
                    pass
        
        print(f"🎯 Widget-like attributes: {widget_attrs}")
        
        return found_containers
    
            
    def fix_canvas_sizing(self):
        """Fix canvas sizing issues"""
        try:
            print("🔧 Fixing canvas sizing...")
            
            # Force all parent containers to update first
            current = self.frame
            while current:
                current.update_idletasks()
                parent = current.winfo_parent()
                if parent:
                    current = self.frame.nametowidget(parent)
                else:
                    break
            
            # Get the frame's actual size
            frame_width = self.frame.winfo_width()
            frame_height = self.frame.winfo_height()
            print(f"📐 Frame size: {frame_width}x{frame_height}")
            
            # If frame is too small, set minimum size
            if frame_width <= 1 or frame_height <= 1:
                print("🔧 Frame too small, setting minimum size...")
                self.frame.configure(width=800, height=600)
                self.frame.update_idletasks()
                frame_width = self.frame.winfo_width()
                frame_height = self.frame.winfo_height()
                print(f"📐 Frame size after fix: {frame_width}x{frame_height}")
            
            # Update canvas size
            if hasattr(self, 'canvas') and self.canvas:
                self.canvas.update_idletasks()
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()
                print(f"📐 Canvas size: {canvas_width}x{canvas_height}")
                
                # If canvas is still too small, force size
                if canvas_width <= 1 or canvas_height <= 1:
                    print("🔧 Canvas too small, forcing size...")
                    self.canvas.configure(width=frame_width-20, height=frame_height-20)
                    self.canvas.update_idletasks()
                    canvas_width = self.canvas.winfo_width()
                    canvas_height = self.canvas.winfo_height()
                    print(f"📐 Canvas size after fix: {canvas_width}x{canvas_height}")
                
                # Set canvas window width to match canvas
                if hasattr(self, 'canvas_window') and self.canvas_window:
                    self.canvas.itemconfig(self.canvas_window, width=canvas_width)
                    print(f"🔧 Set canvas window width to: {canvas_width}")
            
            # Final updates
            self.content_frame.update_idletasks()
            if hasattr(self, 'canvas'):
                self.canvas.configure(scrollregion=self.canvas.bbox("all"))
                self.canvas.yview_moveto(0)
            
            print("✅ Canvas sizing fix completed")
            
        except Exception as e:
            print(f"❌ Canvas sizing fix error: {e}")
            
            
    

