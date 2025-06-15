"""
Enhanced Auto Shutdown Manager for Minecraft Server Manager
"""

import os
import subprocess
import time
import threading
import logging
from datetime import datetime
from error_handler import ErrorHandler, ErrorSeverity

class AutoShutdownManager:
    """Enhanced automatic shutdown with better error handling and cross-platform support"""
    
    def __init__(self, gui_instance):
        self.gui = gui_instance
        self.shutdown_active = False
        self.shutdown_thread = None
        self.error_handler = ErrorHandler()
        self.last_warning_time = None
        
    def start_shutdown_monitoring(self):
        """Start monitoring for scheduled shutdown"""
        if not self.shutdown_active and self.gui.config.get("auto_shutdown_enabled", False):
            self.shutdown_active = True
            self.shutdown_thread = threading.Thread(target=self._shutdown_monitoring_loop, daemon=True)
            self.shutdown_thread.start()
            logging.info("Auto-shutdown monitoring started")
    
    def stop_shutdown_monitoring(self):
        """Stop monitoring for scheduled shutdown"""
        self.shutdown_active = False
        if self.shutdown_thread:
            self.shutdown_thread.join(timeout=1)
        logging.info("Auto-shutdown monitoring stopped")
    
    def _shutdown_monitoring_loop(self):
        """Enhanced shutdown monitoring loop with warnings"""
        while self.shutdown_active:
            try:
                if not self.gui.config.get("auto_shutdown_enabled", False):
                    time.sleep(60)
                    continue
                
                target_time = self._get_target_shutdown_time()
                warning_minutes = self.gui.config.get("shutdown_warning_minutes", 5)
                
                if target_time:
                    now = datetime.now()
                    current_time = f"{now.hour:02d}:{now.minute:02d}"
                    
                    # Calculate warning time
                    warning_time = self._calculate_warning_time(target_time, warning_minutes)
                    
                    # Check for warning time
                    if current_time == warning_time and self.last_warning_time != current_time:
                        self._send_shutdown_warning(warning_minutes)
                        self.last_warning_time = current_time
                    
                    # Check for shutdown time
                    if current_time == target_time:
                        logging.info(f"Shutdown time reached: {target_time}")
                        self._execute_safe_shutdown()
                        break
                    
                    # Log status periodically
                    if now.minute % 30 == 0 and now.second < 30:
                        status = f"Shutdown scheduled for: {target_time} (Current: {current_time})"
                        if warning_time:
                            status += f", Warning at: {warning_time}"
                        logging.info(status)
                
                time.sleep(30)
                
            except Exception as e:
                self.error_handler.handle_error(e, "shutdown_monitoring", ErrorSeverity.MEDIUM)
                time.sleep(60)
        
        logging.info("Auto-shutdown monitoring thread ended")
    
    def _get_target_shutdown_time(self):
        """Get the target shutdown time in HH:MM format"""
        try:
            hour = self.gui.config.get("shutdown_hour", 12)
            minute = self.gui.config.get("shutdown_minute", 0)
            ampm = self.gui.config.get("shutdown_ampm", "AM")
            
            # Convert to 24-hour format
            if ampm == "PM" and hour != 12:
                hour += 12
            elif ampm == "AM" and hour == 12:
                hour = 0
            
            # Validate hour and minute
            if not (0 <= hour <= 23) or not (0 <= minute <= 59):
                raise ValueError(f"Invalid time: {hour}:{minute}")
            
            return f"{hour:02d}:{minute:02d}"
            
        except Exception as e:
            self.error_handler.handle_error(e, "get_shutdown_time", ErrorSeverity.MEDIUM)
            return None
    
    def _calculate_warning_time(self, target_time: str, warning_minutes: int) -> str:
        """Calculate warning time based on target time and warning minutes"""
        try:
            if not target_time or warning_minutes <= 0:
                return None
            
            # Parse target time
            hour, minute = map(int, target_time.split(':'))
            
            # Subtract warning minutes
            total_minutes = hour * 60 + minute - warning_minutes
            
            if total_minutes < 0:
                total_minutes += 24 * 60  # Handle day rollover
            
            warning_hour = total_minutes // 60
            warning_minute = total_minutes % 60
            
            return f"{warning_hour:02d}:{warning_minute:02d}"
            
        except Exception as e:
            self.error_handler.handle_error(e, "calculate_warning_time", ErrorSeverity.LOW)
            return None
    
    def _send_shutdown_warning(self, minutes: int):
        """Send shutdown warning"""
        try:
            warning_msg = f"System will shutdown in {minutes} minutes!"
            logging.warning(warning_msg)
            
            # Update GUI status
            if hasattr(self.gui, 'status_var'):
                self.gui.status_var.set(f"Shutdown warning: {minutes} minutes remaining")
            
            # Send warning to server if running
            if self.gui.process_manager.is_server_running():
                server_warning = f"say [SYSTEM] Server will shutdown in {minutes} minutes!"
                self.gui.process_manager.send_server_command(server_warning)
            
        except Exception as e:
            self.error_handler.handle_error(e, "shutdown_warning", ErrorSeverity.LOW)
    
    def _execute_safe_shutdown(self):
        """Execute shutdown with comprehensive error handling"""
        try:
            logging.info("=== EXECUTING SAFE SHUTDOWN ===")
            
            # Update GUI status
            if hasattr(self.gui, 'status_var'):
                self.gui.status_var.set("Executing scheduled shutdown...")
            
            # Stop services if configured
            if self.gui.config.get("shutdown_stop_server", True):
                self._stop_services_safely()
            
            # Wait a moment for services to stop
            time.sleep(3)
            
            # Execute platform-specific shutdown
            success = self._execute_platform_shutdown()
            
            if success:
                logging.info("Shutdown command executed successfully")
                # Close application
                self.gui.cleanup_and_exit()
            else:
                logging.error("Failed to execute shutdown command")
                if hasattr(self.gui, 'status_var'):
                    self.gui.status_var.set("Shutdown failed - check logs")
            
        except Exception as e:
            self.error_handler.handle_error(e, "safe_shutdown", ErrorSeverity.CRITICAL)
    
    def _stop_services_safely(self):
        """Stop server and related services safely"""
        try:
            # Send final warning to players
            if self.gui.process_manager.is_server_running():
                logging.info("Sending final shutdown notice to players...")
                self.gui.process_manager.send_server_command("say [SYSTEM] Server shutting down NOW!")
                time.sleep(2)
                
                logging.info("Stopping Minecraft server before shutdown...")
                success = self.gui.process_manager.stop_server(timeout=15)
                if not success:
                    logging.warning("Server stop failed or timed out")
            
            # Stop Playit.gg
            if self.gui.process_manager.is_playit_running():
                logging.info("Stopping Playit.gg before shutdown...")
                self.gui.process_manager.stop_playit()
            
        except Exception as e:
            self.error_handler.handle_error(e, "stop_services", ErrorSeverity.MEDIUM)
    
    def _execute_platform_shutdown(self) -> bool:
        """Execute shutdown command based on platform"""
        try:
            import platform
            system = platform.system().lower()
            
            if system == "windows":
                return self._shutdown_windows()
            elif system == "linux":
                return self._shutdown_linux()
            elif system == "darwin":  # macOS
                return self._shutdown_macos()
            else:
                logging.error(f"Unsupported platform for shutdown: {system}")
                return False
                
        except Exception as e:
            self.error_handler.handle_error(e, "platform_shutdown", ErrorSeverity.CRITICAL)
            return False
    
    def _shutdown_windows(self) -> bool:
        """Execute Windows shutdown"""
        try:
            # Use subprocess for better control and security
            result = subprocess.run(
                ["shutdown", "/s", "/t", "1"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logging.info("Windows shutdown command executed successfully")
                return True
            else:
                logging.error(f"Windows shutdown failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logging.error("Windows shutdown command timed out")
            return False
        except Exception as e:
            self.error_handler.handle_error(e, "windows_shutdown", ErrorSeverity.CRITICAL)
            return False
    
    def _shutdown_linux(self) -> bool:
        """Execute Linux shutdown"""
        try:
            # Try different shutdown commands
            commands = [
                ["sudo", "shutdown", "-h", "now"],
                ["systemctl", "poweroff"],
                ["shutdown", "-h", "now"]
            ]
            
            for cmd in commands:
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode == 0:
                        logging.info(f"Linux shutdown successful with command: {' '.join(cmd)}")
                        return True
                        
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
            
            logging.error("All Linux shutdown commands failed")
            return False
            
        except Exception as e:
            self.error_handler.handle_error(e, "linux_shutdown", ErrorSeverity.CRITICAL)
            return False
    
    def _shutdown_macos(self) -> bool:
        """Execute macOS shutdown"""
        try:
            result = subprocess.run(
                ["sudo", "shutdown", "-h", "now"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logging.info("macOS shutdown command executed successfully")
                return True
            else:
                logging.error(f"macOS shutdown failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logging.error("macOS shutdown command timed out")
            return False
        except Exception as e:
            self.error_handler.handle_error(e, "macos_shutdown", ErrorSeverity.CRITICAL)
            return False
    
    def test_shutdown_permissions(self) -> dict:
        """Test if shutdown permissions are available"""
        try:
            import platform
            system = platform.system().lower()
            
            result = {"platform": system, "can_shutdown": False, "method": None, "error": None}
            
            if system == "windows":
                # Test Windows shutdown command
                try:
                    test_result = subprocess.run(
                        ["shutdown", "/?"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    result["can_shutdown"] = test_result.returncode == 0
                    result["method"] = "shutdown.exe"
                except:
                    result["error"] = "shutdown.exe not accessible"
            
            elif system in ["linux", "darwin"]:
                # Test sudo permissions
                try:
                    test_result = subprocess.run(
                        ["sudo", "-n", "true"],
                        capture_output=True,
                        timeout=5
                    )
                    result["can_shutdown"] = test_result.returncode == 0
                    result["method"] = "sudo"
                    if test_result.returncode != 0:
                        result["error"] = "sudo permissions required"
                except:
                    result["error"] = "sudo not available"
            
            return result
            
        except Exception as e:
            return {
                "platform": "unknown",
                "can_shutdown": False,
                "method": None,
                "error": str(e)
            }
    
    def cancel_shutdown(self) -> bool:
        """Cancel pending shutdown"""
        try:
            self.shutdown_active = False
            logging.info("Shutdown cancelled by user")
            
            if hasattr(self.gui, 'status_var'):
                self.gui.status_var.set("Shutdown cancelled")
            
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, "cancel_shutdown", ErrorSeverity.LOW)
            return False
