"""
Enhanced Process Manager for Minecraft Server Manager
Using the working console capture approach from the original code
"""

import subprocess
import threading
import time
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from error_handler import ErrorHandler, ErrorSeverity

class ProcessManager:
    """Enhanced process management with working console capture"""
    
    def __init__(self, config):
        self.config = config
        self.error_handler = ErrorHandler()
        
        # Process tracking
        self.server_process: Optional[subprocess.Popen] = None
        self.playit_process: Optional[subprocess.Popen] = None
        
        # Process monitoring
        self.monitoring_active = False
        self.monitor_thread = None
        
        self._cached_server_pid = None
        self._last_pid_scan = 0
        self._pid_cache_duration = 10  # Cache PID for 10 seconds

        
        # Server status
        self.server_status = {
            'status': 'stopped',
            'pid': None,
            'start_time': None,
            'memory_mb': 0,
            'memory_percent': 0,
            'threads': 0
        }
    
    def start_server(self, jar_path: str) -> bool:
        """Start Minecraft server with working console capture"""
        if self.is_server_running():
            logging.info("Server is already running")
            return False
        
        if not os.path.exists(jar_path):
            logging.error(f"Server jar not found: {jar_path}")
            return False
        
        try:
            # Build Java command - using the working format from old code
            java_command = [
                self.config.get("java_path", "java"),
                f"-Xmx{self.config.get('max_memory', '2G')}",
                "-jar", jar_path,
                "nogui"
            ]
            
            # Add Xms if different from Xmx
            min_memory = self.config.get('min_memory', '')
            if min_memory and min_memory != self.config.get('max_memory', '2G'):
                java_command.insert(2, f"-Xms{min_memory}")
            
            # Check if console should be hidden
            hide_console = self.config.get("hide_server_console", False)
            
            if hide_console:
                # Start server without console window
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                
                self.server_process = subprocess.Popen(
                    java_command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    cwd=os.path.dirname(jar_path),
                    startupinfo=startupinfo,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                # Start the server process with console - using the WORKING approach
                self.server_process = subprocess.Popen(
                    java_command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    cwd=os.path.dirname(jar_path),
                    creationflags=subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NEW_PROCESS_GROUP
                )
            
            # Update server status
            self.server_status.update({
                'status': 'starting',
                'pid': self.server_process.pid,
                'start_time': time.time()
            })
            
            # Start process monitoring
            self.start_process_monitoring()
            
            # Save the server path for future use
            self.config.set("last_server_jar", jar_path)
            self.config.save_config()
            
            logging.info(f"Server started with PID: {self.server_process.pid}")
            logging.info(f"Java command: {' '.join(java_command)}")
            return True
            
        except Exception as e:
            error_info = self.error_handler.handle_error(e, "start_server", ErrorSeverity.HIGH)
            logging.error(f"Failed to start server: {error_info['message']}")
            return False
    
    def stop_server(self) -> bool:
        """Stop server gracefully"""
        if not self.is_server_running():
            logging.info("No server process to stop")
            return True
        
        try:
            if self.server_process.poll() is None:
                try:
                    if self.server_process.stdin:
                        self.server_process.stdin.write("stop\n")
                        self.server_process.stdin.flush()
                        time.sleep(5)
                except:
                    pass
                
                if self.server_process.poll() is None:
                    self.server_process.terminate()
                    
                    try:
                        self.server_process.wait(timeout=30)
                    except subprocess.TimeoutExpired:
                        logging.warning("Server didn't stop gracefully, forcing shutdown")
                        self.server_process.kill()
                        self.server_process.wait()
            
            # Update status
            self.server_status.update({
                'status': 'stopped',
                'pid': None,
                'start_time': None
            })
            
            # Stop monitoring
            self.stop_process_monitoring()
            
            logging.info("Server stopped successfully")
            return True
            
        except Exception as e:
            error_info = self.error_handler.handle_error(e, "stop_server", ErrorSeverity.MEDIUM)
            logging.error(f"Failed to stop server: {error_info['message']}")
            return False
    
    def restart_server(self) -> bool:
        """Restart the server"""
        try:
            last_jar = self.config.get("last_server_jar", "")
            if not last_jar:
                logging.error("No server JAR path saved for restart")
                return False
            
            if self.is_server_running():
                if not self.stop_server():
                    return False
                time.sleep(2)
            
            return self.start_server(last_jar)
            
        except Exception as e:
            error_info = self.error_handler.handle_error(e, "restart_server", ErrorSeverity.HIGH)
            logging.error(f"Failed to restart server: {error_info['message']}")
            return False
    
    def send_server_command(self, command: str) -> bool:
        """Send command to server"""
        try:
            if not self.is_server_running():
                return False
            
            if not self.server_process.stdin:
                return False
            
            self.server_process.stdin.write(command + "\n")
            self.server_process.stdin.flush()
            
            logging.info(f"Command sent to server: {command}")
            return True
            
        except Exception as e:
            error_info = self.error_handler.handle_error(e, "send_server_command", ErrorSeverity.MEDIUM)
            logging.error(f"Failed to send command: {error_info['message']}")
            return False
    
    def start_playit(self, playit_path: str) -> bool:
        """Start Playit.gg process"""
        if self.is_playit_running():
            logging.info("Playit.gg is already running")
            return False
        
        if not os.path.exists(playit_path):
            logging.error(f"Playit.gg not found: {playit_path}")
            return False
        
        try:
            # Start Playit.gg without console window
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            self.playit_process = subprocess.Popen(
                [playit_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            
            # Save the playit path for future use
            self.config.set("last_playit_path", playit_path)
            self.config.save_config()
            
            logging.info(f"Playit.gg started with PID: {self.playit_process.pid}")
            return True
            
        except Exception as e:
            error_info = self.error_handler.handle_error(e, "start_playit", ErrorSeverity.MEDIUM)
            logging.error(f"Failed to start Playit.gg: {error_info['message']}")
            return False
    
    def stop_playit(self) -> bool:
        """Stop Playit.gg process"""
        if not self.is_playit_running():
            logging.info("No Playit.gg process to stop")
            return True
        
        try:
            if self.playit_process.poll() is None:
                self.playit_process.terminate()
                
                try:
                    self.playit_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    logging.warning("Playit.gg didn't stop gracefully, forcing shutdown")
                    self.playit_process.kill()
                    self.playit_process.wait()
            
            logging.info("Playit.gg stopped successfully")
            self.playit_process = None
            return True
            
        except Exception as e:
            error_info = self.error_handler.handle_error(e, "stop_playit", ErrorSeverity.MEDIUM)
            logging.error(f"Failed to stop Playit.gg: {error_info['message']}")
            return False
    
    def start_process_monitoring(self):
        """Start monitoring server process"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitor_thread.start()
            logging.info("Process monitoring started")
    
    def stop_process_monitoring(self):
        """Stop monitoring server process"""
        self.monitoring_active = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1)
        logging.info("Process monitoring stopped")
    
    def _monitoring_loop(self):
        """Process monitoring loop"""
        try:
            import psutil
            PSUTIL_AVAILABLE = True
        except ImportError:
            PSUTIL_AVAILABLE = False
            logging.warning("psutil not available for process monitoring")
        
        while self.monitoring_active:
            try:
                if self.server_process and PSUTIL_AVAILABLE:
                    try:
                        process = psutil.Process(self.server_process.pid)
                        memory_info = process.memory_info()
                        
                        self.server_status.update({
                            'memory_mb': memory_info.rss / 1024 / 1024,
                            'memory_percent': process.memory_percent(),
                            'threads': process.num_threads()
                        })
                        
                        # Update status based on process state
                        if process.status() == psutil.STATUS_RUNNING:
                            if self.server_status['status'] == 'starting':
                                # Check if server is actually ready by looking for specific log patterns
                                # This will be updated by the log reading thread
                                pass
                        
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        # Process no longer exists
                        if self.server_status['status'] != 'stopped':
                            self.server_status['status'] = 'stopped'
                
                time.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                logging.error(f"Monitoring error: {e}")
                time.sleep(10)
    
    def is_server_running(self) -> bool:
        """Check if server is currently running"""
        return self.server_process is not None and self.server_process.poll() is None
    
    def is_playit_running(self) -> bool:
        """Check if Playit.gg is currently running"""
        return self.playit_process is not None and self.playit_process.poll() is None
    
    def get_server_status(self) -> Dict[str, Any]:
        """Get server status with reduced CPU monitoring frequency"""
        if not self.is_server_running():
            return {"status": "stopped", "pid": None, "memory": None, "cpu": None}
        
        try:
            import psutil
            
            real_server_pid = self.find_real_server_process()
            
            if real_server_pid:
                process = psutil.Process(real_server_pid)
                memory_mb = process.memory_info().rss / 1024 / 1024
                
                # REDUCED CPU monitoring frequency - every 5 seconds instead of 1
                if not hasattr(self, '_last_cpu_time') or time.time() - self._last_cpu_time > 5.0:
                    raw_cpu_percent = process.cpu_percent(interval=None)  # Non-blocking
                    self._last_cpu_time = time.time()
                    
                    # Normalize CPU
                    cpu_cores = psutil.cpu_count()
                    normalized_cpu = min(raw_cpu_percent / cpu_cores, 100.0)
                    self._cached_cpu = normalized_cpu
                else:
                    normalized_cpu = getattr(self, '_cached_cpu', 0.0)
                
                return {
                    "status": self.server_status['status'],
                    "pid": real_server_pid,
                    "memory": memory_mb,
                    "cpu": normalized_cpu,
                    "uptime": time.time() - process.create_time()
                }
                
        except Exception as e:
            logging.error(f"Failed to get server status: {e}")
            return {"status": "error", "pid": None, "memory": 0, "cpu": 0}



    
    def stop_all_processes(self) -> bool:
        """Stop all managed processes"""
        success = True
        
        if self.is_server_running():
            success &= self.stop_server()
        
        if self.is_playit_running():
            success &= self.stop_playit()
        
        return success
    
            
    def find_real_server_process(self):
        """Find server process with caching to reduce CPU usage"""
        import time
        
        # Use cached PID if recent
        if (self._cached_server_pid and 
            time.time() - self._last_pid_scan < self._pid_cache_duration):
            try:
                # Verify cached PID still exists
                import psutil
                process = psutil.Process(self._cached_server_pid)
                if process.is_running():
                    return self._cached_server_pid
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Scan for new PID
        try:
            import psutil
            
            best_candidate = None
            highest_memory = 0
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info']):
                try:
                    if 'java' in proc.info['name'].lower():
                        cmdline_str = ' '.join(proc.info['cmdline']).lower()
                        memory_mb = proc.info['memory_info'].rss / 1024 / 1024
                        
                        server_indicators = ['server.jar', 'nogui', 'fabric-server', 'forge-server']
                        is_server = any(indicator in cmdline_str for indicator in server_indicators)
                        
                        if is_server and memory_mb > highest_memory:
                            highest_memory = memory_mb
                            best_candidate = proc.info['pid']
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Cache the result
            self._cached_server_pid = best_candidate
            self._last_pid_scan = time.time()
            
            return best_candidate
            
        except Exception as e:
            logging.error(f"Error finding real server process: {e}")
            return None

    def update_server_tracking(self):
        """Update tracking to monitor the correct server process"""
        try:
            real_server_pid = self.find_real_server_process()
            
            if real_server_pid and real_server_pid != (self.server_process.pid if self.server_process else None):
                logging.info(f"Switching server tracking from PID {self.server_process.pid if self.server_process else 'None'} to PID {real_server_pid}")
                
                # Create a mock process object with the correct PID
                import subprocess
                
                # Update our tracking
                if self.server_process:
                    old_pid = self.server_process.pid
                    # We can't change the PID of existing process, so we'll handle this in get_server_status
                    self.real_server_pid = real_server_pid
                    logging.info(f"Now monitoring real server PID {real_server_pid} instead of launcher PID {old_pid}")
                
        except Exception as e:
            logging.error(f"Error updating server tracking: {e}")


