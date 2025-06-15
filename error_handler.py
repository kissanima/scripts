"""
Enhanced Error Handler for Minecraft Server Manager
"""

import logging
import traceback
import sys
import os
import json
import platform
import psutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from enum import Enum

# Import constants with fallbacks
try:
    from constants import ERROR_LOG_FILE, ERROR_REPORTS_DIR, MAX_ERROR_REPORTS
except ImportError:
    # Fallback constants if constants.py is incomplete
    ERROR_LOG_FILE = Path("logs") / "errors.log"
    ERROR_REPORTS_DIR = Path("error_reports")
    MAX_ERROR_REPORTS = 50

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories for better organization"""
    SERVER_STARTUP = "server_startup"
    SERVER_SHUTDOWN = "server_shutdown"
    FILE_OPERATION = "file_operation"
    NETWORK_ERROR = "network_error"
    CONFIGURATION_ERROR = "configuration_error"
    SYSTEM_ERROR = "system_error"
    GUI_ERROR = "gui_error"
    BACKUP_ERROR = "backup_error"
    HEALTH_CHECK_ERROR = "health_check_error"
    UNKNOWN = "unknown"

class ErrorHandler:
    """Enhanced error handling with recovery suggestions and reporting"""
    
    def __init__(self):
        self.setup_error_logging()
        self.error_count = 0
        self.error_reports = []
        
        # Ensure error reports directory exists
        ERROR_REPORTS_DIR.mkdir(exist_ok=True)
        
        # Recovery suggestions database
        self.recovery_suggestions = {
            "server_startup": {
                "FileNotFoundError": {
                    "recovery": "Check if the server JAR file exists and is accessible",
                    "details": "Verify the server JAR path in settings"
                },
                "PermissionError": {
                    "recovery": "Run the application as administrator or check file permissions",
                    "details": "The application may need elevated privileges"
                },
                "java": {
                    "recovery": "Install Java or check Java path in settings",
                    "details": "Java is required to run Minecraft servers"
                }
            },
            "file_operation": {
                "PermissionError": {
                    "recovery": "Check file permissions or run as administrator",
                    "details": "The application may not have permission to access the file"
                },
                "FileNotFoundError": {
                    "recovery": "Verify the file path exists",
                    "details": "The specified file or directory was not found"
                }
            },
            "network_error": {
                "ConnectionError": {
                    "recovery": "Check internet connection or firewall settings",
                    "details": "Network connectivity issues detected"
                },
                "TimeoutError": {
                    "recovery": "Check network connection or try again later",
                    "details": "The network request timed out"
                }
            }
        }
    
    def setup_error_logging(self):
        """Setup dedicated error logging"""
        try:
            # Ensure logs directory exists
            ERROR_LOG_FILE.parent.mkdir(exist_ok=True)
            
            # Create error logger
            self.error_logger = logging.getLogger('error_handler')
            self.error_logger.setLevel(logging.ERROR)
            
            # Create file handler for errors
            error_handler = logging.FileHandler(ERROR_LOG_FILE)
            error_handler.setLevel(logging.ERROR)
            
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            error_handler.setFormatter(formatter)
            
            # Add handler to logger
            if not self.error_logger.handlers:
                self.error_logger.addHandler(error_handler)
                
        except Exception as e:
            print(f"Failed to setup error logging: {e}")
    
    def handle_error(self, error: Exception, context: str = "", severity: ErrorSeverity = ErrorSeverity.MEDIUM) -> Dict[str, Any]:
        """
        Handle an error with enhanced reporting and recovery suggestions
        
        Args:
            error: The exception that occurred
            context: Context where the error occurred
            severity: Severity level of the error
            
        Returns:
            Dictionary containing error information and recovery suggestions
        """
        try:
            self.error_count += 1
            
            # Create error information
            error_info = {
                'id': self.error_count,
                'timestamp': datetime.now().isoformat(),
                'type': type(error).__name__,
                'message': str(error),
                'context': context,
                'severity': severity.value,
                'traceback': traceback.format_exc(),
                'system_info': self.get_system_info(),
                'recovery': self.get_recovery_suggestion(error, context)
            }
            
            # Log the error
            self.error_logger.error(f"[{context}] {error_info['type']}: {error_info['message']}")
            
            # Store error report
            self.error_reports.append(error_info)
            
            # Limit error reports in memory
            if len(self.error_reports) > MAX_ERROR_REPORTS:
                self.error_reports = self.error_reports[-MAX_ERROR_REPORTS//2:]
            
            # Save critical errors to file
            if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
                self.save_error_report(error_info)
            
            return error_info
            
        except Exception as e:
            # Fallback error handling
            fallback_info = {
                'message': f"Error in error handler: {e}. Original error: {error}",
                'type': 'ErrorHandlerFailure',
                'severity': 'critical',
                'recovery': {'recovery': 'Restart the application', 'details': 'The error handler itself failed'}
            }
            
            try:
                print(f"CRITICAL: Error handler failed: {e}")
                print(f"Original error: {error}")
            except:
                pass
            
            return fallback_info
    
    def get_recovery_suggestion(self, error: Exception, context: str) -> Dict[str, str]:
        """Get recovery suggestion for an error"""
        try:
            error_type = type(error).__name__
            error_message = str(error).lower()
            
            # Check context-specific suggestions
            category_suggestions = self.recovery_suggestions.get(context, {})
            
            # Check by error type
            if error_type in category_suggestions:
                return category_suggestions[error_type]
            
            # Check by keywords in error message
            for keyword, suggestion in category_suggestions.items():
                if keyword.lower() in error_message:
                    return suggestion
            
            # Generic suggestions based on error type
            generic_suggestions = {
                'FileNotFoundError': {
                    'recovery': 'Check if the file or directory exists',
                    'details': 'Verify the file path is correct and accessible'
                },
                'PermissionError': {
                    'recovery': 'Check file permissions or run as administrator',
                    'details': 'The application may need elevated privileges'
                },
                'ConnectionError': {
                    'recovery': 'Check internet connection and firewall settings',
                    'details': 'Network connectivity issues detected'
                },
                'TimeoutError': {
                    'recovery': 'Try the operation again or check system performance',
                    'details': 'The operation took too long to complete'
                },
                'ValueError': {
                    'recovery': 'Check input values and configuration settings',
                    'details': 'Invalid value provided to the operation'
                },
                'ImportError': {
                    'recovery': 'Install missing dependencies or check Python installation',
                    'details': 'Required module or package is missing'
                }
            }
            
            if error_type in generic_suggestions:
                return generic_suggestions[error_type]
            
            # Default suggestion
            return {
                'recovery': 'Try restarting the application or check the logs for more details',
                'details': f'An unexpected {error_type} occurred'
            }
            
        except Exception as e:
            return {
                'recovery': 'Restart the application',
                'details': f'Could not generate recovery suggestion: {e}'
            }
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information for error reports"""
        try:
            return {
                'platform': platform.platform(),
                'python_version': sys.version,
                'cpu_count': psutil.cpu_count(),
                'memory_total': psutil.virtual_memory().total,
                'memory_available': psutil.virtual_memory().available,
                'disk_usage': psutil.disk_usage('/').percent if os.path.exists('/') else psutil.disk_usage('C:').percent,
                'working_directory': str(Path.cwd())
            }
        except Exception as e:
            return {
                'error': f'Could not gather system info: {e}',
                'platform': platform.system() if hasattr(platform, 'system') else 'unknown'
            }
    
    def save_error_report(self, error_info: Dict[str, Any]) -> str:
        """Save detailed error report to file"""
        try:
            timestamp = error_info['timestamp'].replace(':', '-').replace('.', '-')
            report_file = ERROR_REPORTS_DIR / f"error_report_{timestamp}.json"
            
            with open(report_file, 'w') as f:
                json.dump(error_info, f, indent=2, default=str)
            
            logging.info(f"Error report saved: {report_file}")
            return str(report_file)
            
        except Exception as e:
            logging.error(f"Failed to save error report: {e}")
            return ""
    
    def create_error_report(self, error: Exception) -> Dict[str, Any]:
        """Create a comprehensive error report"""
        return {
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'system_info': self.get_system_info(),
            'recent_errors': self.error_reports[-5:] if self.error_reports else []
        }
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics"""
        if not self.error_reports:
            return {'total_errors': 0}
        
        # Count by severity
        severity_counts = {}
        type_counts = {}
        
        for error in self.error_reports:
            severity = error.get('severity', 'unknown')
            error_type = error.get('type', 'unknown')
            
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            type_counts[error_type] = type_counts.get(error_type, 0) + 1
        
        return {
            'total_errors': len(self.error_reports),
            'by_severity': severity_counts,
            'by_type': type_counts,
            'most_recent': self.error_reports[-1]['timestamp'] if self.error_reports else None
        }
    
    def clear_error_reports(self):
        """Clear error reports from memory"""
        self.error_reports.clear()
        logging.info("Error reports cleared")
