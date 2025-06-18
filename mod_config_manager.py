"""
Mod Configuration Manager for Minecraft Server Manager
Handles mod configuration files, editing, and validation
"""
import os
import json
import logging
import shutil
import configparser
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import toml
import yaml

class ConfigFormat(Enum):
    """Supported configuration file formats"""
    JSON = "json"
    TOML = "toml"
    YAML = "yaml"
    PROPERTIES = "properties"
    CFG = "cfg"
    HOCON = "hocon"
    UNKNOWN = "unknown"

@dataclass
class ConfigFile:
    """Configuration file information"""
    filepath: str
    modid: str
    config_type: str  # server, client, common
    format: ConfigFormat
    last_modified: datetime
    backup_path: str = ""
    is_valid: bool = True
    error_message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'filepath': self.filepath,
            'modid': self.modid,
            'config_type': self.config_type,
            'format': self.format.value,
            'last_modified': self.last_modified.isoformat(),
            'backup_path': self.backup_path,
            'is_valid': self.is_valid,
            'error_message': self.error_message
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConfigFile':
        """Create from dictionary"""
        return cls(
            filepath=data['filepath'],
            modid=data['modid'],
            config_type=data['config_type'],
            format=ConfigFormat(data['format']),
            last_modified=datetime.fromisoformat(data['last_modified']),
            backup_path=data.get('backup_path', ''),
            is_valid=data.get('is_valid', True),
            error_message=data.get('error_message', '')
        )

class ModConfigManager:
    """Comprehensive mod configuration management system"""
    
    def __init__(self, modmanager, config):
        self.modmanager = modmanager
        self.config = config
        
        # Configuration tracking
        self.config_files: Dict[str, List[ConfigFile]] = {}  # modid -> list of config files
        self.config_cache = {}
        self.config_templates = {}
        
        # Paths
        self.config_dir = ""
        self.backup_dir = ""
        self.templates_dir = ""
        
        # Settings
        self.settings = {
            "auto_backup_on_change": True,
            "validate_on_save": True,
            "auto_detect_configs": True,
            "backup_retention_days": 30,
            "enable_config_templates": True,
            "auto_format_configs": False,
            "config_file_extensions": [".json", ".toml", ".yaml", ".yml", ".cfg", ".properties", ".conf"],
            "enable_syntax_highlighting": True
        }
        
        # File format handlers
        self.format_handlers = {
            ConfigFormat.JSON: self.handle_json_config,
            ConfigFormat.TOML: self.handle_toml_config,
            ConfigFormat.YAML: self.handle_yaml_config,
            ConfigFormat.PROPERTIES: self.handle_properties_config,
            ConfigFormat.CFG: self.handle_cfg_config
        }
        
        # Callbacks
        self.config_changed_callbacks = []
        self.validation_callbacks = []
        
        self.initialize()
    
    def initialize(self):
        """Initialize the config manager"""
        try:
            self.setup_directories()
            self.load_config_database()
            self.load_config_templates()
            
            if self.settings["auto_detect_configs"]:
                self.scan_config_files()
            
            logging.info("ModConfigManager initialized")
        except Exception as e:
            logging.error(f"Failed to initialize ModConfigManager: {e}")
    
    def setup_directories(self):
        """Set up configuration directories"""
        if hasattr(self.modmanager, 'config_dir'):  # FIXED: was configdir
            self.config_dir = self.modmanager.config_dir
        
        if hasattr(self.modmanager, 'mod_data_dir'):  # FIXED: was moddatadir
            self.backup_dir = os.path.join(self.modmanager.mod_data_dir, "config_backups")
            self.templates_dir = os.path.join(self.modmanager.mod_data_dir, "config_templates")
        
        # Create directories
        for directory in [self.backup_dir, self.templates_dir]:
            if directory:
                os.makedirs(directory, exist_ok=True)
    
    def load_config_database(self):
        """Load configuration database"""
        try:
            database_file = os.path.join(
                self.modmanager.mod_data_dir,  # FIXED: was moddatadir
                "config_database.json"
            )
            
            if os.path.exists(database_file):
                with open(database_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Convert data back to ConfigFile objects
                for modid, config_data_list in data.items():
                    config_files = []
                    for config_data in config_data_list:
                        try:
                            config_file = ConfigFile.from_dict(config_data)
                            config_files.append(config_file)
                        except Exception as e:
                            logging.error(f"Error loading config file data: {e}")
                    
                    if config_files:
                        self.config_files[modid] = config_files
                
                logging.info(f"Loaded config database with {len(self.config_files)} mod configurations")
        
        except Exception as e:
            logging.error(f"Failed to load config database: {e}")
            self.config_files = {}
    
    def save_config_database(self):
        """Save configuration database"""
        try:
            database_file = os.path.join(
                self.modmanager.mod_data_dir,  # FIXED: was moddatadir
                "config_database.json"
            )
            
            # Convert ConfigFile objects to serializable dict
            data = {}
            for modid, config_files in self.config_files.items():
                data[modid] = [cf.to_dict() for cf in config_files]
            
            os.makedirs(os.path.dirname(database_file), exist_ok=True)
            with open(database_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logging.info("Config database saved")
        
        except Exception as e:
            logging.error(f"Failed to save config database: {e}")
    
    def load_config_templates(self):
        """Load configuration templates"""
        try:
            if not os.path.exists(self.templates_dir):
                return
            
            for filename in os.listdir(self.templates_dir):
                if filename.endswith('.json'):
                    template_path = os.path.join(self.templates_dir, filename)
                    try:
                        with open(template_path, 'r', encoding='utf-8') as f:
                            template_data = json.load(f)
                        
                        modid = os.path.splitext(filename)[0]
                        self.config_templates[modid] = template_data
                        
                    except Exception as e:
                        logging.error(f"Error loading config template {filename}: {e}")
            
            logging.info(f"Loaded {len(self.config_templates)} config templates")
        
        except Exception as e:
            logging.error(f"Failed to load config templates: {e}")
    
    def scan_config_files(self):
        """Scan for mod configuration files"""
        try:
            if not os.path.exists(self.config_dir):
                return
            
            logging.info("Scanning for mod configuration files...")
            
            # Clear existing config files
            self.config_files.clear()
            
            # Scan config directory
            for root, dirs, files in os.walk(self.config_dir):
                for file in files:
                    if any(file.endswith(ext) for ext in self.settings["config_file_extensions"]):
                        filepath = os.path.join(root, file)
                        self.analyze_config_file(filepath)
            
            # Update mod info with config file information
            self.update_mod_config_info()
            
            # Save database
            self.save_config_database()
            
            logging.info(f"Config scan completed. Found {sum(len(configs) for configs in self.config_files.values())} config files")
        
        except Exception as e:
            logging.error(f"Error scanning config files: {e}")
    
    def analyze_config_file(self, filepath: str):
        """Analyze a configuration file and determine its mod association"""
        try:
            filename = os.path.basename(filepath)
            file_ext = os.path.splitext(filename)[1].lower()
            
            # Determine format
            config_format = self.detect_config_format(filepath, file_ext)
            
            # Determine mod association
            modid = self.determine_mod_association(filepath, filename)
            
            # Determine config type (server, client, common)
            config_type = self.determine_config_type(filepath, filename)
            
            # Create config file entry
            config_file = ConfigFile(
                filepath=filepath,
                modid=modid,
                config_type=config_type,
                format=config_format,
                last_modified=datetime.fromtimestamp(os.path.getmtime(filepath))
            )
            
            # Validate the config file
            config_file.is_valid, config_file.error_message = self.validate_config_file(config_file)
            
            # Add to tracking
            if modid not in self.config_files:
                self.config_files[modid] = []
            
            self.config_files[modid].append(config_file)
            
        except Exception as e:
            logging.error(f"Error analyzing config file {filepath}: {e}")
    
    def detect_config_format(self, filepath: str, file_ext: str) -> ConfigFormat:
        """Detect the format of a configuration file"""
        format_map = {
            '.json': ConfigFormat.JSON,
            '.toml': ConfigFormat.TOML,
            '.yaml': ConfigFormat.YAML,
            '.yml': ConfigFormat.YAML,
            '.properties': ConfigFormat.PROPERTIES,
            '.cfg': ConfigFormat.CFG,
            '.conf': ConfigFormat.CFG
        }
        
        return format_map.get(file_ext, ConfigFormat.UNKNOWN)
    
    def determine_mod_association(self, filepath: str, filename: str) -> str:
        """Determine which mod a config file belongs to"""
        # Extract potential mod ID from filename
        base_name = os.path.splitext(filename)[0]
        
        # Common patterns
        if '-' in base_name:
            # Handle patterns like "modname-server.toml"
            potential_modid = base_name.split('-')[0]
        else:
            # Use full base name
            potential_modid = base_name
        
        # Check against installed mods - FIXED: attribute name
        if hasattr(self.modmanager, 'installed_mods'):
            installed_mods = self.modmanager.installed_mods
            
            # Exact match
            if potential_modid in installed_mods:
                return potential_modid
            
            # Fuzzy match
            for modid, modinfo in installed_mods.items():
                if (modid.lower().replace('_', '').replace('-', '') == 
                    potential_modid.lower().replace('_', '').replace('-', '')):
                    return modid
                
                # Check mod name similarity
                if (modinfo.name.lower().replace(' ', '').replace('_', '').replace('-', '') == 
                    potential_modid.lower().replace('_', '').replace('-', '')):
                    return modid
        
        # Return potential modid if no match found
        return potential_modid
    
    def determine_config_type(self, filepath: str, filename: str) -> str:
        """Determine the type of configuration (server, client, common)"""
        filename_lower = filename.lower()
        
        if 'server' in filename_lower:
            return 'server'
        elif 'client' in filename_lower:
            return 'client'
        elif 'common' in filename_lower:
            return 'common'
        else:
            # Default to common
            return 'common'
    
    def validate_config_file(self, config_file: ConfigFile) -> Tuple[bool, str]:
        """Validate a configuration file"""
        try:
            if not os.path.exists(config_file.filepath):
                return False, "File does not exist"
            
            # Try to parse the file based on its format
            handler = self.format_handlers.get(config_file.format)
            if handler:
                success, error = handler(config_file.filepath, 'validate')
                return success, error
            
            return True, ""
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def update_mod_config_info(self):
        """Update mod info with configuration file information"""
        try:
            if not hasattr(self.modmanager, 'installed_mods'):  # FIXED: attribute name
                return
            
            for modid, modinfo in self.modmanager.installed_mods.items():
                if modid in self.config_files:
                    modinfo.hasconfig = True
                    modinfo.configfiles = [cf.filepath for cf in self.config_files[modid]]
                else:
                    modinfo.hasconfig = False
                    modinfo.configfiles = []
            
            # Save updated mod database - FIXED: method name
            if hasattr(self.modmanager, 'save_database'):
                self.modmanager.save_database()
                
        except Exception as e:
            logging.error(f"Error updating mod config info: {e}")
    
    def read_config_file(self, config_file: ConfigFile) -> Tuple[bool, Union[Dict, str], str]:
        """Read and parse a configuration file"""
        try:
            handler = self.format_handlers.get(config_file.format)
            if handler:
                return handler(config_file.filepath, 'read')
            else:
                # Fallback to reading as text
                with open(config_file.filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                return True, content, ""
            
        except Exception as e:
            return False, {}, f"Read error: {str(e)}"
    
    def write_config_file(self, config_file: ConfigFile, content: Union[Dict, str]) -> Tuple[bool, str]:
        """Write content to a configuration file"""
        try:
            # Create backup if enabled
            if self.settings["auto_backup_on_change"]:
                self.create_config_backup(config_file)
            
            handler = self.format_handlers.get(config_file.format)
            if handler:
                success, error = handler(config_file.filepath, 'write', content)
            else:
                # Fallback to writing as text
                with open(config_file.filepath, 'w', encoding='utf-8') as f:
                    f.write(str(content))
                success, error = True, ""
            
            if success:
                # Update last modified time
                config_file.last_modified = datetime.now()
                
                # Validate if enabled
                if self.settings["validate_on_save"]:
                    config_file.is_valid, config_file.error_message = self.validate_config_file(config_file)
                
                # Save database
                self.save_config_database()
                
                # Notify callbacks
                self.notify_config_changed(config_file)
            
            return success, error
            
        except Exception as e:
            return False, f"Write error: {str(e)}"
    
    def create_config_backup(self, config_file: ConfigFile) -> str:
        """Create a backup of a configuration file"""
        try:
            if not os.path.exists(config_file.filepath):
                return ""
            
            # Generate backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.basename(config_file.filepath)
            backup_filename = f"{filename}_{timestamp}.bak"
            backup_path = os.path.join(self.backup_dir, config_file.modid, backup_filename)
            
            # Create backup directory
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # Copy file
            shutil.copy2(config_file.filepath, backup_path)
            
            # Update config file backup path
            config_file.backup_path = backup_path
            
            logging.info(f"Created config backup: {backup_path}")
            return backup_path
            
        except Exception as e:
            logging.error(f"Error creating config backup: {e}")
            return ""
    
    def restore_config_backup(self, config_file: ConfigFile, backup_path: str = None) -> Tuple[bool, str]:
        """Restore a configuration file from backup"""
        try:
            restore_path = backup_path or config_file.backup_path
            
            if not restore_path or not os.path.exists(restore_path):
                return False, "Backup file not found"
            
            # Create backup of current file before restore
            current_backup = self.create_config_backup(config_file)
            
            # Restore from backup
            shutil.copy2(restore_path, config_file.filepath)
            
            # Update file info
            config_file.last_modified = datetime.now()
            config_file.is_valid, config_file.error_message = self.validate_config_file(config_file)
            
            # Save database
            self.save_config_database()
            
            # Notify callbacks
            self.notify_config_changed(config_file)
            
            return True, f"Config restored from backup. Current version backed up to: {current_backup}"
            
        except Exception as e:
            return False, f"Restore error: {str(e)}"
    
    def get_config_backups(self, config_file: ConfigFile) -> List[Tuple[str, datetime]]:
        """Get list of available backups for a config file"""
        backups = []
        
        try:
            backup_dir = os.path.join(self.backup_dir, config_file.modid)
            if not os.path.exists(backup_dir):
                return backups
            
            filename_base = os.path.basename(config_file.filepath)
            
            for backup_file in os.listdir(backup_dir):
                if backup_file.startswith(filename_base) and backup_file.endswith('.bak'):
                    backup_path = os.path.join(backup_dir, backup_file)
                    backup_time = datetime.fromtimestamp(os.path.getmtime(backup_path))
                    backups.append((backup_path, backup_time))
            
            # Sort by modification time (newest first)
            backups.sort(key=lambda x: x[1], reverse=True)
            
        except Exception as e:
            logging.error(f"Error getting config backups: {e}")
        
        return backups
    
    def cleanup_old_backups(self):
        """Clean up old configuration backups"""
        try:
            if not os.path.exists(self.backup_dir):
                return
            
            cutoff_date = datetime.now() - timedelta(days=self.settings["backup_retention_days"])
            removed_count = 0
            
            for modid_dir in os.listdir(self.backup_dir):
                mod_backup_dir = os.path.join(self.backup_dir, modid_dir)
                if not os.path.isdir(mod_backup_dir):
                    continue
                
                for backup_file in os.listdir(mod_backup_dir):
                    backup_path = os.path.join(mod_backup_dir, backup_file)
                    
                    if os.path.isfile(backup_path):
                        backup_time = datetime.fromtimestamp(os.path.getmtime(backup_path))
                        
                        if backup_time < cutoff_date:
                            os.remove(backup_path)
                            removed_count += 1
            
            logging.info(f"Cleaned up {removed_count} old config backups")
            
        except Exception as e:
            logging.error(f"Error cleaning up config backups: {e}")
    
    # Format-specific handlers
    def handle_json_config(self, filepath: str, operation: str, content: Union[Dict, str] = None) -> Tuple[bool, Union[Dict, str]]:
        """Handle JSON configuration files"""
        try:
            if operation == 'validate' or operation == 'read':
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return True, data if operation == 'read' else ""
            
            elif operation == 'write' and content is not None:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(content, f, indent=2, ensure_ascii=False)
                return True, ""
            
            return False, "Invalid operation"
            
        except json.JSONDecodeError as e:
            return False, f"JSON parse error: {str(e)}"
        except Exception as e:
            return False, f"JSON handling error: {str(e)}"
    
    def handle_toml_config(self, filepath: str, operation: str, content: Union[Dict, str] = None) -> Tuple[bool, Union[Dict, str]]:
        """Handle TOML configuration files"""
        try:
            if operation == 'validate' or operation == 'read':
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = toml.load(f)
                return True, data if operation == 'read' else ""
            
            elif operation == 'write' and content is not None:
                with open(filepath, 'w', encoding='utf-8') as f:
                    toml.dump(content, f)
                return True, ""
            
            return False, "Invalid operation"
            
        except Exception as e:
            return False, f"TOML handling error: {str(e)}"
    
    def handle_yaml_config(self, filepath: str, operation: str, content: Union[Dict, str] = None) -> Tuple[bool, Union[Dict, str]]:
        """Handle YAML configuration files"""
        try:
            if operation == 'validate' or operation == 'read':
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                return True, data if operation == 'read' else ""
            
            elif operation == 'write' and content is not None:
                with open(filepath, 'w', encoding='utf-8') as f:
                    yaml.dump(content, f, default_flow_style=False, allow_unicode=True)
                return True, ""
            
            return False, "Invalid operation"
            
        except Exception as e:
            return False, f"YAML handling error: {str(e)}"
    
    def handle_properties_config(self, filepath: str, operation: str, content: Union[Dict, str] = None) -> Tuple[bool, Union[Dict, str]]:
        """Handle Properties configuration files"""
        try:
            if operation == 'validate' or operation == 'read':
                config = configparser.ConfigParser()
                config.read(filepath, encoding='utf-8')
                
                # Convert to dict
                data = {}
                for section in config.sections():
                    data[section] = dict(config[section])
                
                return True, data if operation == 'read' else ""
            
            elif operation == 'write' and content is not None:
                config = configparser.ConfigParser()
                
                for section, values in content.items():
                    config.add_section(section)
                    for key, value in values.items():
                        config.set(section, key, str(value))
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    config.write(f)
                
                return True, ""
            
            return False, "Invalid operation"
            
        except Exception as e:
            return False, f"Properties handling error: {str(e)}"
    
    def handle_cfg_config(self, filepath: str, operation: str, content: Union[Dict, str] = None) -> Tuple[bool, Union[Dict, str]]:
        """Handle CFG configuration files"""
        try:
            # CFG files are often custom format, treat as text for now
            if operation == 'validate' or operation == 'read':
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = f.read()
                return True, data if operation == 'read' else ""
            
            elif operation == 'write' and content is not None:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(str(content))
                return True, ""
            
            return False, "Invalid operation"
            
        except Exception as e:
            return False, f"CFG handling error: {str(e)}"
    
    def get_mod_configs(self, modid: str) -> List[ConfigFile]:
        """Get all configuration files for a specific mod"""
        return self.config_files.get(modid, [])
    
    def get_all_configs(self) -> Dict[str, List[ConfigFile]]:
        """Get all configuration files"""
        return self.config_files.copy()
    
    def get_config_statistics(self) -> Dict[str, Any]:
        """Get configuration statistics"""
        total_configs = sum(len(configs) for configs in self.config_files.values())
        mods_with_configs = len(self.config_files)
        
        # Count by format
        format_counts = {}
        valid_configs = 0
        
        for configs in self.config_files.values():
            for config in configs:
                format_name = config.format.value
                format_counts[format_name] = format_counts.get(format_name, 0) + 1
                
                if config.is_valid:
                    valid_configs += 1
        
        return {
            "total_config_files": total_configs,
            "mods_with_configs": mods_with_configs,
            "valid_configs": valid_configs,
            "invalid_configs": total_configs - valid_configs,
            "format_breakdown": format_counts,
            "auto_backup_enabled": self.settings["auto_backup_on_change"],
            "templates_available": len(self.config_templates)
        }
    
    def notify_config_changed(self, config_file: ConfigFile):
        """Notify callbacks when config changes"""
        for callback in self.config_changed_callbacks:
            try:
                callback(config_file)
            except Exception as e:
                logging.error(f"Error in config changed callback: {e}")
    
    def register_config_changed_callback(self, callback):
        """Register config changed callback"""
        self.config_changed_callbacks.append(callback)
    
    def register_validation_callback(self, callback):
        """Register validation callback"""
        self.validation_callbacks.append(callback)
