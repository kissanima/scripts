"""
Enhanced Virtual Desktop Manager for Minecraft Server Manager
"""

import os
import ctypes
import ctypes.wintypes as wintypes
import logging
from error_handler import ErrorHandler, ErrorSeverity

class VirtualDesktopManager:
    """Enhanced virtual desktop operations with better error handling"""
    
    def __init__(self, dll_path: str):
        self.vda = None
        self.available = False
        self.error_handler = ErrorHandler()
        
        try:
            if os.path.exists(dll_path):
                self.vda = ctypes.WinDLL(dll_path)
                self._setup_functions()
                self._test_functionality()
                self.available = True
                logging.info("Virtual Desktop Manager initialized successfully")
            else:
                logging.warning(f"VirtualDesktopAccessor.dll not found at {dll_path}")
        except Exception as e:
            self.error_handler.handle_error(e, "virtual_desktop_init", ErrorSeverity.LOW)
    
    def _setup_functions(self):
        """Setup DLL function signatures with error handling"""
        try:
            if self.vda:
                # Setup function signatures
                self.vda.GetDesktopCount.restype = ctypes.c_uint
                self.vda.CreateDesktop.restype = ctypes.c_void_p
                self.vda.GetCurrentDesktopNumber.restype = ctypes.c_uint
                self.vda.MoveWindowToDesktopNumber.argtypes = [wintypes.HWND, ctypes.c_uint]
                self.vda.MoveWindowToDesktopNumber.restype = None
                
                # Optional functions
                try:
                    self.vda.GoToDesktopNumber.argtypes = [ctypes.c_uint]
                    self.vda.GoToDesktopNumber.restype = None
                except AttributeError:
                    logging.info("GoToDesktopNumber function not available in DLL")
                
                try:
                    self.vda.GetDesktopName.argtypes = [ctypes.c_uint, ctypes.POINTER(ctypes.c_wchar_p)]
                    self.vda.GetDesktopName.restype = ctypes.c_int
                except AttributeError:
                    logging.info("GetDesktopName function not available in DLL")
                    
        except Exception as e:
            self.error_handler.handle_error(e, "virtual_desktop_setup", ErrorSeverity.LOW)
            raise
    
    def _test_functionality(self):
        """Test basic functionality to ensure DLL works"""
        try:
            if self.vda:
                # Test basic function call
                desktop_count = self.vda.GetDesktopCount()
                if desktop_count > 0:
                    logging.info(f"Virtual Desktop Manager test successful. Desktop count: {desktop_count}")
                else:
                    raise RuntimeError("Invalid desktop count returned")
        except Exception as e:
            self.error_handler.handle_error(e, "virtual_desktop_test", ErrorSeverity.LOW)
            raise
    
    def get_desktop_count(self) -> int:
        """Get the number of virtual desktops"""
        if not self.available or not self.vda:
            return 1
        
        try:
            return self.vda.GetDesktopCount()
        except Exception as e:
            self.error_handler.handle_error(e, "get_desktop_count", ErrorSeverity.LOW)
            return 1
    
    def get_current_desktop(self) -> int:
        """Get current desktop number"""
        if not self.available or not self.vda:
            return 0
        
        try:
            return self.vda.GetCurrentDesktopNumber()
        except Exception as e:
            self.error_handler.handle_error(e, "get_current_desktop", ErrorSeverity.LOW)
            return 0
    
    def move_window_to_desktop(self, hwnd: int, desktop_number: int) -> bool:
        """Move window to specified desktop with validation"""
        if not self.available or not self.vda:
            logging.info("Virtual Desktop Manager not available")
            return False
        
        try:
            # Validate desktop number
            desktop_count = self.get_desktop_count()
            if desktop_number < 0 or desktop_number >= desktop_count:
                logging.warning(f"Invalid desktop number: {desktop_number}. Available: 0-{desktop_count-1}")
                return False
            
            # Validate window handle
            if not self._is_valid_window_handle(hwnd):
                logging.warning(f"Invalid window handle: {hwnd}")
                return False
            
            self.vda.MoveWindowToDesktopNumber(hwnd, desktop_number)
            logging.info(f"Moved window {hwnd} to desktop {desktop_number}")
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, "move_window_to_desktop", ErrorSeverity.LOW)
            return False
    
    def switch_to_desktop(self, desktop_number: int) -> bool:
        """Switch to specified desktop with validation"""
        if not self.available or not self.vda:
            logging.info("Virtual Desktop Manager not available")
            return False
        
        try:
            # Validate desktop number
            desktop_count = self.get_desktop_count()
            if desktop_number < 0 or desktop_number >= desktop_count:
                logging.warning(f"Invalid desktop number: {desktop_number}. Available: 0-{desktop_count-1}")
                return False
            
            if hasattr(self.vda, 'GoToDesktopNumber'):
                self.vda.GoToDesktopNumber(desktop_number)
                logging.info(f"Switched to desktop {desktop_number}")
                return True
            else:
                logging.warning("GoToDesktopNumber function not available")
                return False
                
        except Exception as e:
            self.error_handler.handle_error(e, "switch_to_desktop", ErrorSeverity.LOW)
            return False
    
    def create_desktop(self) -> bool:
        """Create a new virtual desktop"""
        if not self.available or not self.vda:
            return False
        
        try:
            self.vda.CreateDesktop()
            logging.info("Created new virtual desktop")
            return True
        except Exception as e:
            self.error_handler.handle_error(e, "create_desktop", ErrorSeverity.LOW)
            return False
    
    def get_desktop_name(self, desktop_number: int) -> str:
        """Get the name of a desktop (if supported)"""
        if not self.available or not self.vda:
            return f"Desktop {desktop_number + 1}"
        
        try:
            if hasattr(self.vda, 'GetDesktopName'):
                name_ptr = ctypes.c_wchar_p()
                result = self.vda.GetDesktopName(desktop_number, ctypes.byref(name_ptr))
                if result == 0 and name_ptr.value:
                    return name_ptr.value
            
            # Fallback to generic name
            return f"Desktop {desktop_number + 1}"
            
        except Exception as e:
            self.error_handler.handle_error(e, "get_desktop_name", ErrorSeverity.LOW)
            return f"Desktop {desktop_number + 1}"
    
    def _is_valid_window_handle(self, hwnd: int) -> bool:
        """Validate window handle"""
        try:
            # Use Windows API to check if handle is valid
            import ctypes.wintypes as wintypes
            user32 = ctypes.windll.user32
            return user32.IsWindow(hwnd) != 0
        except Exception:
            return False
    
    def get_status(self) -> dict:
        """Get virtual desktop manager status"""
        return {
            'available': self.available,
            'desktop_count': self.get_desktop_count() if self.available else 0,
            'current_desktop': self.get_current_desktop() if self.available else 0,
            'dll_loaded': self.vda is not None
        }
