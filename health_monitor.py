"""
Health monitoring for Minecraft Server Manager
"""

import time
import threading
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Callable
from datetime import datetime

# Try to import psutil, with fallback if not available
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not available. Health monitoring features will be limited.")

from error_handler import ErrorHandler, ErrorSeverity

class ServerHealthMonitor:
    """Enhanced server health monitoring"""
    
    def __init__(self, process_manager, config):
        self.process_manager = process_manager
        self.config = config
        self.error_handler = ErrorHandler()
        self.monitoring_active = False
        self.monitor_thread = None
        self.health_callbacks = []
        self.alerts = []
        self.health_history = []
        
    def start_monitoring(self):
        """Start health monitoring"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            logging.info("Health monitoring started")
    
    def stop_monitoring(self):
        """Stop health monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
        logging.info("Health monitoring stopped")
    
    def register_health_callback(self, callback: Callable):
        """Register a health status callback"""
        self.health_callbacks.append(callback)
    
    def _monitor_loop(self):
        """Health monitoring loop"""
        while self.monitoring_active:
            try:
                health_status = self.check_server_health()
                
                # Notify callbacks
                for callback in self.health_callbacks:
                    try:
                        callback(health_status)
                    except Exception as e:
                        self.error_handler.handle_error(e, "health_callback", ErrorSeverity.LOW)
                
                # Store history
                self.health_history.append(health_status)
                
                # Limit history size
                if len(self.health_history) > 100:
                    self.health_history = self.health_history[-50:]
                
                time.sleep(self.config.get("health_check_interval", 30))
                
            except Exception as e:
                self.error_handler.handle_error(e, "health_monitor", ErrorSeverity.LOW)
                time.sleep(60)
    
    def check_server_health(self) -> Dict[str, Any]:
        """Check server health and return status"""
        try:
            health_status = {
                'timestamp': datetime.now().isoformat(),
                'overall_status': 'unknown',
                'metrics': {},
                'issues': []
            }
            
            # Check if server is running
            if self.process_manager.is_server_running():
                # Get detailed server metrics
                server_status = self.process_manager.get_server_status()
                health_status['metrics']['process'] = server_status
                
                # Check resource usage
                resource_metrics = self._check_system_resources()
                health_status['metrics']['resources'] = resource_metrics
                
                # Determine overall status
                health_status['overall_status'] = self._determine_overall_status(
                    server_status, resource_metrics
                )
                
                # Check for issues
                issues = self._check_for_issues(server_status, resource_metrics)
                health_status['issues'] = issues
                
                # Generate alerts if needed
                self._generate_alerts(issues)
                
            else:
                health_status['overall_status'] = 'stopped'
                health_status['metrics']['process'] = {'status': 'stopped'}
            
            return health_status
            
        except Exception as e:
            self.error_handler.handle_error(e, "check_server_health", ErrorSeverity.MEDIUM)
            return {
                'timestamp': datetime.now().isoformat(),
                'overall_status': 'error',
                'error': str(e)
            }
    
    def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        try:
            if PSUTIL_AVAILABLE:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                
                # Memory usage
                memory = psutil.virtual_memory()
                
                # Disk usage
                disk = psutil.disk_usage('.' if os.name != 'nt' else 'C:')
                
                return {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available_gb': memory.available / 1024 / 1024 / 1024,
                    'disk_percent': (disk.used / disk.total) * 100,
                    'disk_free_gb': disk.free / 1024 / 1024 / 1024
                }
            else:
                # Fallback without psutil
                return {
                    'cpu_percent': 0,
                    'memory_percent': 0,
                    'memory_available_gb': 0,
                    'disk_percent': 0,
                    'disk_free_gb': 0,
                    'note': 'Limited monitoring - psutil not available'
                }
            
        except Exception as e:
            self.error_handler.handle_error(e, "check_system_resources", ErrorSeverity.LOW)
            return {}
    
    def _determine_overall_status(self, server_status: Dict, resource_metrics: Dict) -> str:
        """Determine overall health status"""
        try:
            if server_status.get('status') != 'running':
                return 'critical'
            
            # Check memory usage
            server_memory = server_status.get('memory_percent', 0)
            system_memory = resource_metrics.get('memory_percent', 0)
            
            if server_memory > 90 or system_memory > 95:
                return 'critical'
            elif server_memory > 75 or system_memory > 85:
                return 'warning'
            
            # Check CPU usage
            cpu_usage = resource_metrics.get('cpu_percent', 0)
            if cpu_usage > 95:
                return 'critical'
            elif cpu_usage > 80:
                return 'warning'
            
            # Check disk space
            disk_usage = resource_metrics.get('disk_percent', 0)
            if disk_usage > 95:
                return 'critical'
            elif disk_usage > 85:
                return 'warning'
            
            return 'good'
            
        except Exception as e:
            self.error_handler.handle_error(e, "determine_overall_status", ErrorSeverity.LOW)
            return 'unknown'
    
    def _check_for_issues(self, server_status: Dict, resource_metrics: Dict) -> List[str]:
        """Check for specific issues"""
        issues = []
        
        try:
            # Memory issues
            server_memory = server_status.get('memory_percent', 0)
            if server_memory > 90:
                issues.append(f"High server memory usage: {server_memory:.1f}%")
            
            system_memory = resource_metrics.get('memory_percent', 0)
            if system_memory > 90:
                issues.append(f"High system memory usage: {system_memory:.1f}%")
            
            # CPU issues
            cpu_usage = resource_metrics.get('cpu_percent', 0)
            if cpu_usage > 90:
                issues.append(f"High CPU usage: {cpu_usage:.1f}%")
            
            # Disk space issues
            disk_usage = resource_metrics.get('disk_percent', 0)
            if disk_usage > 90:
                issues.append(f"Low disk space: {disk_usage:.1f}% used")
            
            # Server-specific checks
            if server_status.get('threads', 0) > 200:
                issues.append(f"High thread count: {server_status['threads']}")
            
        except Exception as e:
            self.error_handler.handle_error(e, "check_for_issues", ErrorSeverity.LOW)
            issues.append("Error checking for issues")
        
        return issues
    
    def _generate_alerts(self, issues: List[str]):
        """Generate alerts for issues"""
        for issue in issues:
            alert = {
                'timestamp': datetime.now(),
                'severity': 'warning',
                'message': issue
            }
            self.alerts.append(alert)
        
        # Limit alerts history
        if len(self.alerts) > 50:
            self.alerts = self.alerts[-25:]
    
    def get_current_health(self) -> Dict[str, Any]:
        """Get current health status"""
        if self.health_history:
            return self.health_history[-1]
        return None
    
    def get_recent_alerts(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        return self.alerts[-count:] if self.alerts else []
    
    def clear_alerts(self):
        """Clear all alerts"""
        self.alerts.clear()
    
    def get_health_summary(self, hours: int = 24) -> str:
        """Get health summary for the last N hours"""
        try:
            if not self.health_history:
                return "No health data available"
            
            cutoff_time = datetime.now().timestamp() - (hours * 3600)
            recent_history = [
                h for h in self.health_history 
                if datetime.fromisoformat(h['timestamp']).timestamp() > cutoff_time
            ]
            
            if not recent_history:
                return f"No health data for the last {hours} hours"
            
            # Count status occurrences
            status_counts = {}
            for entry in recent_history:
                status = entry['overall_status']
                status_counts[status] = status_counts.get(status, 0) + 1
            
            total_checks = len(recent_history)
            summary = f"Health summary for last {hours} hours ({total_checks} checks):\n"
            
            for status, count in status_counts.items():
                percentage = (count / total_checks) * 100
                summary += f"- {status.title()}: {count} ({percentage:.1f}%)\n"
            
            return summary
            
        except Exception as e:
            self.error_handler.handle_error(e, "get_health_summary", ErrorSeverity.LOW)
            return f"Error generating health summary: {e}"
