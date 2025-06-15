"""
Memory Management for Minecraft Server Manager
"""

import gc
import logging
import threading
import time
import os
from pathlib import Path
from typing import Dict, Any, List, Callable

# Try to import psutil, with fallback if not available
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not available. Some memory monitoring features will be limited.")

from error_handler import ErrorHandler, ErrorSeverity

class MemoryManager:
    """Enhanced memory management with monitoring and optimization"""
    
    def __init__(self):
        self.error_handler = ErrorHandler()
        self.monitoring_active = False
        self.monitor_thread = None
        self.cleanup_callbacks = []
        self.memory_stats = {}
        
    def start_monitoring(self):
        """Start memory monitoring"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            logging.info("Memory monitoring started")
    
    def stop_monitoring(self):
        """Stop memory monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
        logging.info("Memory monitoring stopped")
    
    def register_cleanup_callback(self, callback: Callable):
        """Register a cleanup callback"""
        self.cleanup_callbacks.append(callback)
    
    def _monitor_loop(self):
        """Memory monitoring loop"""
        while self.monitoring_active:
            try:
                self._update_memory_stats()
                
                # Check if cleanup is needed
                if self._should_cleanup():
                    self.cleanup_memory()
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.error_handler.handle_error(e, "memory_monitor", ErrorSeverity.LOW)
                time.sleep(60)
    
    def _update_memory_stats(self):
        """Update memory statistics"""
        try:
            if PSUTIL_AVAILABLE:
                # Process memory
                process = psutil.Process()
                process_memory = process.memory_info()
                
                # System memory
                system_memory = psutil.virtual_memory()
                
                self.memory_stats = {
                    'process_memory_mb': process_memory.rss / 1024 / 1024,
                    'process_memory_percent': process.memory_percent(),
                    'system_memory_percent': system_memory.percent,
                    'system_available_mb': system_memory.available / 1024 / 1024,
                    'last_update': time.time()
                }
            else:
                # Fallback without psutil
                self.memory_stats = {
                    'process_memory_mb': 0,
                    'process_memory_percent': 0,
                    'system_memory_percent': 0,
                    'system_available_mb': 0,
                    'last_update': time.time(),
                    'note': 'Limited monitoring - psutil not available'
                }
            
        except Exception as e:
            self.error_handler.handle_error(e, "update_memory_stats", ErrorSeverity.LOW)
    
    def _should_cleanup(self) -> bool:
        """Check if memory cleanup is needed"""
        if not self.memory_stats:
            return False
        
        # Cleanup if process uses more than 500MB or system memory > 85%
        return (self.memory_stats.get('process_memory_mb', 0) > 500 or
                self.memory_stats.get('system_memory_percent', 0) > 85)
    
    def cleanup_memory(self):
        """Perform memory cleanup"""
        try:
            logging.info("Performing memory cleanup...")
            
            # Run registered cleanup callbacks
            for callback in self.cleanup_callbacks:
                try:
                    callback()
                except Exception as e:
                    self.error_handler.handle_error(e, "cleanup_callback", ErrorSeverity.LOW)
            
            # Force garbage collection
            gc.collect()
            
            logging.info("Memory cleanup completed")
            
        except Exception as e:
            self.error_handler.handle_error(e, "cleanup_memory", ErrorSeverity.MEDIUM)
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get current memory statistics"""
        self._update_memory_stats()
        return self.memory_stats.copy()
    
    def optimize_memory_settings(self) -> Dict[str, str]:
        """Suggest optimal memory settings"""
        try:
            if PSUTIL_AVAILABLE:
                system_memory = psutil.virtual_memory()
                total_gb = system_memory.total / 1024 / 1024 / 1024
                
                if total_gb >= 16:
                    suggested_max = "4G"
                    suggested_min = "2G"
                    reason = "High memory system detected"
                elif total_gb >= 8:
                    suggested_max = "3G"
                    suggested_min = "1G"
                    reason = "Medium memory system detected"
                elif total_gb >= 4:
                    suggested_max = "2G"
                    suggested_min = "512M"
                    reason = "Low memory system detected"
                else:
                    suggested_max = "1G"
                    suggested_min = "256M"
                    reason = "Very low memory system detected"
                
                return {
                    'suggested_max_memory': suggested_max,
                    'suggested_min_memory': suggested_min,
                    'reason': reason,
                    'system_memory_gb': f"{total_gb:.1f}"
                }
            else:
                # Fallback suggestions without psutil
                return {
                    'suggested_max_memory': '2G',
                    'suggested_min_memory': '512M',
                    'reason': 'Default settings (psutil not available for system detection)',
                    'system_memory_gb': 'Unknown'
                }
            
        except Exception as e:
            self.error_handler.handle_error(e, "optimize_memory_settings", ErrorSeverity.LOW)
            return {
                'suggested_max_memory': '2G',
                'suggested_min_memory': '512M',
                'reason': 'Default settings (could not detect system memory)',
                'system_memory_gb': 'Unknown'
            }

class LogManager:
    """Log file management and cleanup"""
    
    def __init__(self):
        self.registered_logs = []
        self.max_log_size = 10 * 1024 * 1024  # 10MB
        
    def register_log_file(self, log_path: str):
        """Register a log file for management"""
        self.registered_logs.append(log_path)
    
    def cleanup_logs(self):
        """Clean up log files"""
        for log_path in self.registered_logs:
            try:
                log_file = Path(log_path)
                if log_file.exists():
                    size = log_file.stat().st_size
                    if size > self.max_log_size:
                        self._rotate_log(log_path)
            except Exception as e:
                logging.error(f"Failed to cleanup log {log_path}: {e}")
    
    def _rotate_log(self, log_path: str):
        """Rotate a log file"""
        try:
            log_file = Path(log_path)
            backup_file = log_file.with_suffix(f"{log_file.suffix}.old")
            
            if backup_file.exists():
                backup_file.unlink()
            
            log_file.rename(backup_file)
            logging.info(f"Rotated log file: {log_path}")
            
        except Exception as e:
            logging.error(f"Failed to rotate log {log_path}: {e}")

class TextWidgetManager:
    """Manages text widgets to prevent memory leaks"""
    
    def __init__(self):
        self.widgets = []
    
    def register_widget(self, widget, max_lines: int = 1000):
        """Register a text widget for management"""
        self.widgets.append({
            'widget': widget,
            'max_lines': max_lines
        })
    
    def cleanup_widgets(self):
        """Clean up text widgets"""
        for widget_info in self.widgets:
            try:
                widget = widget_info['widget']
                max_lines = widget_info['max_lines']
                
                # Get current line count
                content = widget.get('1.0', 'end-1c')
                lines = content.split('\n')
                
                if len(lines) > max_lines:
                    # Keep only the last max_lines
                    new_content = '\n'.join(lines[-max_lines:])
                    widget.delete('1.0', 'end')
                    widget.insert('1.0', new_content)
                    
            except Exception as e:
                logging.error(f"Failed to cleanup text widget: {e}")
