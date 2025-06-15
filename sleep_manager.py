"""
Enhanced Sleep Manager for Minecraft Server Manager
"""

import time
import threading
import logging
import psutil
from error_handler import ErrorHandler, ErrorSeverity

class SleepManager:
    """Enhanced sleep/wake management with better detection and recovery"""
    
    def __init__(self, gui_instance):
        self.gui = gui_instance
        self.last_check_time = time.time()
        self.wake_detection_active = False
        self.wake_thread = None
        self.error_handler = ErrorHandler()
        self.consecutive_wake_events = 0
        self.wake_threshold = 30  # seconds gap to consider as wake event
        
    def start_wake_detection(self):
        """Start monitoring for wake-up events"""
        if not self.wake_detection_active and self.gui.config.get("wake_detection_enabled", True):
            self.wake_detection_active = True
            self.last_check_time = time.time()
            self.wake_thread = threading.Thread(target=self._wake_detection_loop, daemon=True)
            self.wake_thread.start()
            logging.info("Enhanced wake detection started")
    
    def stop_wake_detection(self):
        """Stop monitoring for wake-up events"""
        self.wake_detection_active = False
        if self.wake_thread:
            self.wake_thread.join(timeout=1)
        logging.info("Wake detection stopped")
    
    def _wake_detection_loop(self):
        """Enhanced wake detection loop with multiple detection methods"""
        while self.wake_detection_active:
            try:
                current_time = time.time()
                time_diff = current_time - self.last_check_time
                
                # Method 1: Time jump detection
                if time_diff > self.wake_threshold:
                    self.consecutive_wake_events += 1
                    logging.info(f"Potential wake-up detected via time jump: {time_diff:.1f}s (event #{self.consecutive_wake_events})")
                    
                    # Require multiple consecutive events to avoid false positives
                    if self.consecutive_wake_events >= 2:
                        self._handle_wake_up("time_jump", time_diff)
                        self.consecutive_wake_events = 0
                else:
                    self.consecutive_wake_events = 0
                
                # Method 2: System uptime check (Windows/Linux)
                self._check_system_uptime()
                
                self.last_check_time = current_time
                time.sleep(5)
                
            except Exception as e:
                self.error_handler.handle_error(e, "wake_detection_loop", ErrorSeverity.LOW)
                time.sleep(10)
    
    def _check_system_uptime(self):
        """Check system uptime for signs of recent boot/wake"""
        try:
            boot_time = psutil.boot_time()
            current_time = time.time()
            uptime = current_time - boot_time
            
            # If system has been up for less than 10 minutes, it might have just woken up
            if uptime < 600:  # 10 minutes
                logging.info(f"System uptime is low ({uptime:.1f}s), possible recent wake/boot")
                # Additional logic could be added here
                
        except Exception as e:
            # Not critical, just log and continue
            logging.debug(f"Could not check system uptime: {e}")
    
    def _handle_wake_up(self, detection_method: str, details: float = None):
        """Enhanced wake-up event handling"""
        try:
            if not self.gui.config.get("auto_restart_after_wake", True):
                logging.info("Auto-restart after wake is disabled")
                return
            
            logging.info(f"System wake-up confirmed via {detection_method}, checking server status...")
            
            # Wait a moment for system to stabilize
            time.sleep(5)
            
            # Perform comprehensive server health check
            server_status = self._perform_comprehensive_health_check()
            
            if server_status['action_needed']:
                self.gui.root.after(0, lambda: self._execute_recovery_action(server_status))
            else:
                self.gui.root.after(0, lambda: self.gui.status_var.set("System woke up - All services OK"))
                
        except Exception as e:
            self.error_handler.handle_error(e, "handle_wake_up", ErrorSeverity.MEDIUM)
    
    def _perform_comprehensive_health_check(self) -> dict:
        """Perform comprehensive health check after wake-up"""
        status = {
            'server_running': False,
            'server_responsive': False,
            'playit_running': False,
            'action_needed': False,
            'recommended_action': 'none',
            'details': {}
        }
        
        try:
            # Check if server process exists
            status['server_running'] = self.gui.process_manager.is_server_running()
            
            if status['server_running']:
                # Check server responsiveness
                responsiveness = self._check_server_responsiveness_detailed()
                status['server_responsive'] = responsiveness['responsive']
                status['details']['server'] = responsiveness
                
                if not status['server_responsive']:
                    status['action_needed'] = True
                    status['recommended_action'] = 'restart_unresponsive'
            else:
                status['action_needed'] = True
                status['recommended_action'] = 'restart_crashed'
            
            # Check Playit.gg status
            status['playit_running'] = self.gui.process_manager.is_playit_running()
            
            # Additional checks
            status['details']['memory_usage'] = self._check_memory_usage()
            status['details']['system_load'] = self._check_system_load()
            
            return status
            
        except Exception as e:
            self.error_handler.handle_error(e, "comprehensive_health_check", ErrorSeverity.MEDIUM)
            return {
                'server_running': False,
                'action_needed': True,
                'recommended_action': 'full_restart',
                'error': str(e)
            }
    
    def _check_server_responsiveness_detailed(self, timeout=15) -> dict:
        """Detailed server responsiveness check"""
        responsiveness = {
            'responsive': False,
            'process_status': 'unknown',
            'memory_ok': False,
            'cpu_ok': False,
            'threads_ok': False
        }
        
        try:
            if not self.gui.process_manager.server_process:
                responsiveness['process_status'] = 'no_process'
                return responsiveness
            
            try:
                process = psutil.Process(self.gui.process_manager.server_process.pid)
                
                # Check process status
                proc_status = process.status()
                responsiveness['process_status'] = proc_status
                
                if proc_status in [psutil.STATUS_RUNNING, psutil.STATUS_SLEEPING]:
                    # Check memory usage (not too high)
                    memory_percent = process.memory_percent()
                    responsiveness['memory_ok'] = memory_percent < 90
                    
                    # Check CPU usage (should be reasonable after wake)
                    cpu_percent = process.cpu_percent(interval=1)
                    responsiveness['cpu_ok'] = cpu_percent < 95
                    
                    # Check thread count (reasonable number)
                    num_threads = process.num_threads()
                    responsiveness['threads_ok'] = 5 < num_threads < 200
                    
                    # Overall responsiveness
                    responsiveness['responsive'] = (
                        responsiveness['memory_ok'] and
                        responsiveness['cpu_ok'] and
                        responsiveness['threads_ok']
                    )
                else:
                    logging.warning(f"Server process in abnormal state: {proc_status}")
                    responsiveness['responsive'] = False
                
            except psutil.NoSuchProcess:
                responsiveness['process_status'] = 'not_found'
                responsiveness['responsive'] = False
            except psutil.AccessDenied:
                responsiveness['process_status'] = 'access_denied'
                responsiveness['responsive'] = True  # Assume OK if we can't check
                
        except Exception as e:
            self.error_handler.handle_error(e, "check_server_responsiveness", ErrorSeverity.LOW)
            responsiveness['error'] = str(e)
        
        return responsiveness
    
    def _check_memory_usage(self) -> dict:
        """Check system memory usage"""
        try:
            memory = psutil.virtual_memory()
            return {
                'percent_used': memory.percent,
                'available_gb': memory.available / 1024 / 1024 / 1024,
                'status': 'ok' if memory.percent < 85 else 'high'
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def _check_system_load(self) -> dict:
        """Check system load"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            return {
                'cpu_percent': cpu_percent,
                'status': 'ok' if cpu_percent < 80 else 'high'
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def _execute_recovery_action(self, server_status: dict):
        """Execute appropriate recovery action based on server status"""
        try:
            action = server_status['recommended_action']
            
            if action == 'restart_unresponsive':
                self._restart_unresponsive_server(server_status)
            elif action == 'restart_crashed':
                self._restart_crashed_server()
            elif action == 'full_restart':
                self._full_system_restart()
            else:
                logging.info("No recovery action needed")
                
        except Exception as e:
            self.error_handler.handle_error(e, "execute_recovery_action", ErrorSeverity.MEDIUM)
    
    def _restart_unresponsive_server(self, server_status: dict):
        """Restart server that's unresponsive after wake-up"""
        try:
            logging.info("Restarting unresponsive server after wake-up...")
            self.gui.status_var.set("Restarting unresponsive server...")
            
            # Try graceful restart first
            success = self.gui.process_manager.restart_server()
            
            if success:
                self.gui.status_var.set("Server restarted after wake-up")
                logging.info("Server successfully restarted after wake-up")
                
                # Wait and verify restart
                time.sleep(5)
                if self.gui.process_manager.is_server_running():
                    logging.info("Server restart verified successful")
                else:
                    logging.warning("Server restart may have failed")
            else:
                self.gui.status_var.set("Failed to restart server after wake-up")
                logging.error("Failed to restart server after wake-up")
                
        except Exception as e:
            self.error_handler.handle_error(e, "restart_unresponsive_server", ErrorSeverity.MEDIUM)
    
    def _restart_crashed_server(self):
        """Restart server that crashed during sleep"""
        try:
            logging.info("Restarting crashed server after wake-up...")
            self.gui.status_var.set("Restarting crashed server...")
            
            # Start server
            if hasattr(self.gui, 'server_jar_path') and self.gui.server_jar_path:
                if self.gui.config.get("hide_server_console", False):
                    success = self.gui.process_manager.start_server_hidden(self.gui.server_jar_path)
                else:
                    success = self.gui.process_manager.start_server(self.gui.server_jar_path)
                
                if success:
                    self.gui.status_var.set("Server restarted after wake-up (was crashed)")
                    logging.info("Crashed server successfully restarted after wake-up")
                else:
                    self.gui.status_var.set("Failed to restart crashed server")
                    logging.error("Failed to restart crashed server after wake-up")
            else:
                logging.error("No server JAR path available for restart")
                self.gui.status_var.set("Cannot restart server - no JAR path")
                
        except Exception as e:
            self.error_handler.handle_error(e, "restart_crashed_server", ErrorSeverity.MEDIUM)
    
    def _full_system_restart(self):
        """Perform full system restart of all managed services"""
        try:
            logging.info("Performing full system restart after wake-up...")
            self.gui.status_var.set("Full system restart in progress...")
            
            # Stop all processes
            self.gui.process_manager.stop_all_processes()
            time.sleep(3)
            
            # Restart server if path available
            if hasattr(self.gui, 'server_jar_path') and self.gui.server_jar_path:
                if self.gui.config.get("hide_server_console", False):
                    server_success = self.gui.process_manager.start_server_hidden(self.gui.server_jar_path)
                else:
                    server_success = self.gui.process_manager.start_server(self.gui.server_jar_path)
            else:
                server_success = False
            
            # Restart Playit.gg if configured and path available
            playit_success = False
            if (self.gui.config.get("auto_start_playit", False) and 
                hasattr(self.gui, 'playit_path') and self.gui.playit_path):
                playit_success = self.gui.process_manager.start_playit(self.gui.playit_path)
            
            # Update status
            if server_success:
                self.gui.status_var.set("Full system restart completed successfully")
                logging.info("Full system restart completed successfully")
            else:
                self.gui.status_var.set("Full system restart completed with issues")
                logging.warning("Full system restart completed but server start failed")
                
        except Exception as e:
            self.error_handler.handle_error(e, "full_system_restart", ErrorSeverity.MEDIUM)
    
    def get_wake_statistics(self) -> dict:
        """Get wake detection statistics"""
        return {
            'wake_detection_active': self.wake_detection_active,
            'last_check_time': self.last_check_time,
            'consecutive_wake_events': self.consecutive_wake_events,
            'wake_threshold_seconds': self.wake_threshold
        }
