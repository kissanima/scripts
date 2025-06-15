"""
Enhanced Configuration management for Minecraft Server Manager
Includes input validation and security improvements
"""

import os
import sys
import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, Union
from constants import CONFIG_FILE, APP_DIR, DEFAULT_JAVA_PATH, DEFAULT_MAX_MEMORY, DEFAULT_SERVER_PORT, DEFAULT_LOG_LEVEL
from error_handler import ErrorHandler, ErrorSeverity, ErrorCategory

class ConfigValidator:
    """Validates configuration values for security and correctness"""
    
    @staticmethod
    def validate_java_path(path: str) -> bool:
        """Validate Java executable path"""
        if not path:
            return False
        
        # Allow 'java' as default
        if path == 'java':
            return True
        
        # Check if it's a valid file path
        if not os.path.isfile(path):
            return False
        
        # Check if it's a Java executable
        if not path.lower().endswith(('java', 'java.exe')):
            return False
        
        return True
    
    @staticmethod
    def validate_memory_setting(memory: str) -> bool:
        """Validate memory allocation format"""
        if not memory:
            return True  # Empty is allowed
        
        pattern = r'^\d+[GMKgmk]?$'
        return bool(re.match(pattern, memory))
    
    @staticmethod
    def validate_port(port: Union[int, str]) -> bool:
        """Validate server port"""
        try:
            port_int = int(port)
            return 1024 <= port_int <= 65535
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_file_path(path: str) -> str:
        """Validate and sanitize file path"""
        if not path:
            return path
        
        # Resolve path and ensure it's within allowed directories
        try:
            resolved_path = os.path.realpath(path)
            
            # Check if path is within current working directory or its subdirectories
            cwd = os.path.realpath(os.getcwd())
            if not resolved_path.startswith(cwd):
                # Allow paths in common program directories
                allowed_prefixes = [
                    "C:\\Program Files",
                    "C:\\Program Files (x86)",
                    "/usr/bin",
                    "/usr/local/bin"
                ]
                
                if not any(resolved_path.startswith(prefix) for prefix in allowed_prefixes):
                    raise ValueError(f"Path outside allowed directories: {path}")
            
            return resolved_path
        except Exception as e:
            raise ValueError(f"Invalid path: {e}")

class Config:
    """Enhanced configuration management class with validation and security"""
    
    def __init__(self, config_path: str = CONFIG_FILE):
        self.error_handler = ErrorHandler()
        self.validator = ConfigValidator()
        self.config_path = self.get_config_path(config_path)
        
        self.default_config = {
            "java_path": DEFAULT_JAVA_PATH,
            "min_memory": "",
            "max_memory": DEFAULT_MAX_MEMORY,
            "server_port": DEFAULT_SERVER_PORT,
            "auto_backup": True,
            "backup_interval": 3600,
            "max_backup_count": 10,
            "log_level": DEFAULT_LOG_LEVEL,
            "virtual_desktop": 1,
            "auto_start_server": False,
            "auto_start_playit": False,
            "move_to_desktop2_first": True,
            "hide_server_console": False,
            "auto_restart_after_wake": True,
            "wake_detection_enabled": True,
            "ui_theme": "dark",
            "server_log_max_lines": 1000,
            "console_font_size": 10,
            "auto_shutdown_enabled": False,
            "shutdown_hour": 12,
            "shutdown_minute": 0,
            "shutdown_ampm": "AM",
            "shutdown_stop_server": True,
            "shutdown_warning_minutes": 5,
            "pause_server_for_backup": False,
            "health_monitoring_enabled": True,
            "health_check_interval": 30,
            "memory_optimization_enabled": True,
            "last_server_jar": "",
            "last_playit_path": ""
        }
        
        self.config = self.load_config()
    
    def get_config_path(self, config_filename: str) -> Path:
        """Get the correct config file path"""
        try:
            config_path = APP_DIR / config_filename
            return config_path
        except Exception as e:
            fallback_path = Path.cwd() / config_filename
            print(f"Error determining config path: {e}, using fallback: {fallback_path}")
            return fallback_path
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file with validation"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                
                # Validate loaded configuration
                validated_config = self.validate_config(loaded_config)
                
                # Merge with defaults for any missing keys
                merged_config = {**self.default_config, **validated_config}
                
                # Save back to ensure all new default keys are added
                self.save_config(merged_config)
                return merged_config
            else:
                self.save_config(self.default_config)
                return self.default_config.copy()
                
        except Exception as e:
            error_info = self.error_handler.handle_error(
                e, 
                "config_load", 
                ErrorSeverity.MEDIUM
            )
            logging.error(f"Failed to load config: {error_info['message']}")
            
            # Return default config as fallback
            return self.default_config.copy()
    
    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate entire configuration"""
        validated_config = {}
        
        for key, value in config.items():
            try:
                validated_value = self.validate_config_value(key, value)
                validated_config[key] = validated_value
            except ValueError as e:
                logging.warning(f"Invalid config value for {key}: {e}. Using default.")
                if key in self.default_config:
                    validated_config[key] = self.default_config[key]
        
        return validated_config
    
    def validate_config_value(self, key: str, value: Any) -> Any:
        """Validate a single configuration value"""
        # Java path validation
        if key == "java_path":
            if not self.validator.validate_java_path(str(value)):
                raise ValueError(f"Invalid Java path: {value}")
            return str(value)
        
        # Memory validation
        elif key in ["min_memory", "max_memory"]:
            if not self.validator.validate_memory_setting(str(value)):
                raise ValueError(f"Invalid memory format: {value}")
            return str(value)
        
        # Port validation
        elif key == "server_port":
            if not self.validator.validate_port(value):
                raise ValueError(f"Invalid port: {value}")
            return int(value)
        
        # File path validation
        elif key in ["last_server_jar", "last_playit_path"]:
            if value and isinstance(value, str):
                try:
                    return self.validator.validate_file_path(value)
                except ValueError:
                    # If validation fails, clear the path
                    return ""
            return str(value) if value else ""
        
        # Boolean validation
        elif isinstance(self.default_config.get(key), bool):
            return bool(value)
        
        # Integer validation
        elif isinstance(self.default_config.get(key), int):
            try:
                return int(value)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid integer value: {value}")
        
        # String validation
        elif isinstance(self.default_config.get(key), str):
            return str(value)
        
        # Default: return as-is
        return value
    
    def save_config(self, config: Dict[str, Any] = None) -> bool:
        """Save configuration to file with validation"""
        try:
            config_to_save = config or self.config
            
            # Validate before saving
            validated_config = self.validate_config(config_to_save)
            
            # Ensure the directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to temporary file first, then rename (atomic operation)
            temp_path = self.config_path.with_suffix('.tmp')
            
            with open(temp_path, 'w') as f:
                json.dump(validated_config, f, indent=4)
            
            # Rename temp file to actual config file
            if self.config_path.exists():
                self.config_path.unlink()
            temp_path.rename(self.config_path)
            
            return True
            
        except Exception as e:
            error_info = self.error_handler.handle_error(
                e, 
                "config_save", 
                ErrorSeverity.MEDIUM
            )
            logging.error(f"Failed to save config: {error_info['message']}")
            return False
    
    def get(self, key: str, default=None):
        """Get configuration value with validation"""
        value = self.config.get(key, default)
        
        # Re-validate critical values when accessed
        if key in ["java_path", "server_port", "max_memory", "min_memory"]:
            try:
                return self.validate_config_value(key, value)
            except ValueError:
                # Return default if validation fails
                return self.default_config.get(key, default)
        
        return value
    
    def set(self, key: str, value: Any) -> bool:
        """Set configuration value with validation"""
        try:
            validated_value = self.validate_config_value(key, value)
            self.config[key] = validated_value
            return True
        except ValueError as e:
            logging.error(f"Failed to set config {key}={value}: {e}")
            return False
    
    def reset_to_defaults(self):
        """Reset configuration to default values"""
        self.config = self.default_config.copy()
        self.save_config()
        logging.info("Configuration reset to defaults")
    
    def backup_config(self) -> str:
        """Create a backup of current configuration"""
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.config_path.with_name(f"config_backup_{timestamp}.json")
            
            with open(backup_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            
            logging.info(f"Configuration backed up to: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            logging.error(f"Failed to backup configuration: {e}")
            return ""
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration"""
        return {
            'java_path': self.config.get('java_path', 'Not set'),
            'memory_allocation': f"{self.config.get('min_memory', 'Auto')}-{self.config.get('max_memory', '2G')}",
            'server_port': self.config.get('server_port', DEFAULT_SERVER_PORT),
            'auto_backup': self.config.get('auto_backup', False),
            'backup_interval_hours': self.config.get('backup_interval', 3600) / 3600,
            'health_monitoring': self.config.get('health_monitoring_enabled', False),
            'memory_optimization': self.config.get('memory_optimization_enabled', False),
            'config_file': str(self.config_path)
        }
        
    def set_and_save(self, key: str, value: Any) -> bool:
        """Set a configuration value and immediately save to file"""
        try:
            self.set(key, value)
            return self.save_config()
        except Exception as e:
            logging.error(f"Failed to set and save config {key}: {e}")
            return False

