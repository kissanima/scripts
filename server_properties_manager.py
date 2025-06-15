"""
Server Properties Management for Minecraft Server Manager
"""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from error_handler import ErrorHandler, ErrorSeverity

class ServerPropertiesManager:
    """Manages Minecraft server.properties file"""
    
    def __init__(self, error_handler: ErrorHandler):
        self.error_handler = error_handler
        self.properties = {}
        self.properties_file_path = None
        
        # Define property categories and their settings
        self.property_definitions = {
            'basic': {
                'name': 'Basic Server Settings',
                'properties': {
                    'server-port': {'type': 'int', 'default': 25565, 'range': (1024, 65535), 'description': 'Server port'},
                    'server-ip': {'type': 'str', 'default': '', 'description': 'Server IP (leave empty for all interfaces)'},
                    'max-players': {'type': 'int', 'default': 20, 'range': (1, 1000), 'description': 'Maximum players'},
                    'motd': {'type': 'str', 'default': 'A Minecraft Server', 'description': 'Message of the day'},
                    'online-mode': {'type': 'bool', 'default': True, 'description': 'Enable online mode (authentication)'},
                    'white-list': {'type': 'bool', 'default': False, 'description': 'Enable whitelist'},
                    'enforce-whitelist': {'type': 'bool', 'default': False, 'description': 'Enforce whitelist'}
                }
            },
            'world': {
                'name': 'World & Gameplay Settings',
                'properties': {
                    'level-name': {'type': 'str', 'default': 'world', 'description': 'World folder name'},
                    'level-seed': {'type': 'str', 'default': '', 'description': 'World seed (leave empty for random)'},
                    'level-type': {'type': 'choice', 'default': 'minecraft:normal', 
                                 'choices': ['minecraft:normal', 'minecraft:flat', 'minecraft:large_biomes', 'minecraft:amplified'], 
                                 'description': 'World type'},
                    'gamemode': {'type': 'choice', 'default': 'survival', 
                               'choices': ['survival', 'creative', 'adventure', 'spectator'], 
                               'description': 'Default gamemode'},
                    'difficulty': {'type': 'choice', 'default': 'easy', 
                                 'choices': ['peaceful', 'easy', 'normal', 'hard'], 
                                 'description': 'Game difficulty'},
                    'hardcore': {'type': 'bool', 'default': False, 'description': 'Enable hardcore mode'},
                    'pvp': {'type': 'bool', 'default': True, 'description': 'Enable PvP'},
                    'spawn-monsters': {'type': 'bool', 'default': True, 'description': 'Spawn hostile mobs'},
                    'spawn-protection': {'type': 'int', 'default': 16, 'range': (0, 100), 'description': 'Spawn protection radius'},
                    'generate-structures': {'type': 'bool', 'default': True, 'description': 'Generate structures (villages, dungeons, etc.)'}
                }
            },
            'performance': {
                'name': 'Performance Settings',
                'properties': {
                    'view-distance': {'type': 'int', 'default': 10, 'range': (3, 32), 'description': 'View distance in chunks'},
                    'simulation-distance': {'type': 'int', 'default': 10, 'range': (3, 32), 'description': 'Simulation distance in chunks'},
                    'max-tick-time': {'type': 'int', 'default': 60000, 'range': (1000, 300000), 'description': 'Max tick time (ms)'},
                    'max-world-size': {'type': 'int', 'default': 29999984, 'range': (1, 29999984), 'description': 'Max world size'},
                    'network-compression-threshold': {'type': 'int', 'default': 256, 'range': (-1, 1024), 'description': 'Network compression threshold'},
                    'player-idle-timeout': {'type': 'int', 'default': 0, 'range': (0, 9999), 'description': 'Player idle timeout (minutes, 0=disabled)'},
                    'max-chained-neighbor-updates': {'type': 'int', 'default': 1000000, 'range': (1000, 10000000), 'description': 'Max chained neighbor updates'},
                    'entity-broadcast-range-percentage': {'type': 'int', 'default': 100, 'range': (10, 1000), 'description': 'Entity broadcast range %'},
                    'use-native-transport': {'type': 'bool', 'default': True, 'description': 'Use native transport (Linux only)'},
                    'sync-chunk-writes': {'type': 'bool', 'default': True, 'description': 'Synchronize chunk writes'}
                }
            },
            'advanced': {
                'name': 'Advanced Settings',
                'properties': {
                    'enable-command-block': {'type': 'bool', 'default': False, 'description': 'Enable command blocks'},
                    'enable-rcon': {'type': 'bool', 'default': False, 'description': 'Enable RCON'},
                    'rcon.port': {'type': 'int', 'default': 25575, 'range': (1024, 65535), 'description': 'RCON port'},
                    'rcon.password': {'type': 'str', 'default': '', 'description': 'RCON password'},
                    'enable-query': {'type': 'bool', 'default': False, 'description': 'Enable server query'},
                    'query.port': {'type': 'int', 'default': 25565, 'range': (1024, 65535), 'description': 'Query port'},
                    'enable-jmx-monitoring': {'type': 'bool', 'default': False, 'description': 'Enable JMX monitoring'},
                    'enable-status': {'type': 'bool', 'default': True, 'description': 'Enable server status'},
                    'broadcast-console-to-ops': {'type': 'bool', 'default': True, 'description': 'Broadcast console to ops'},
                    'broadcast-rcon-to-ops': {'type': 'bool', 'default': True, 'description': 'Broadcast RCON to ops'},
                    'op-permission-level': {'type': 'int', 'default': 4, 'range': (1, 4), 'description': 'Operator permission level'},
                    'function-permission-level': {'type': 'int', 'default': 2, 'range': (1, 4), 'description': 'Function permission level'},
                    'force-gamemode': {'type': 'bool', 'default': False, 'description': 'Force gamemode'},
                    'hide-online-players': {'type': 'bool', 'default': False, 'description': 'Hide online players'},
                    'prevent-proxy-connections': {'type': 'bool', 'default': False, 'description': 'Prevent proxy connections'},
                    'enforce-secure-profile': {'type': 'bool', 'default': True, 'description': 'Enforce secure profile'},
                    'pause-when-empty-seconds': {'type': 'int', 'default': 60, 'range': (0, 3600), 'description': 'Pause when empty (seconds)'}
                }
            },
            'nether': {
                'name': 'Nether & End Settings',
                'properties': {
                    'allow-nether': {'type': 'bool', 'default': True, 'description': 'Allow nether'},
                    'allow-flight': {'type': 'bool', 'default': False, 'description': 'Allow flight'}
                }
            },
            'resource_pack': {
                'name': 'Resource Pack Settings',
                'properties': {
                    'resource-pack': {'type': 'str', 'default': '', 'description': 'Resource pack URL'},
                    'resource-pack-sha1': {'type': 'str', 'default': '', 'description': 'Resource pack SHA1 hash'},
                    'resource-pack-id': {'type': 'str', 'default': '', 'description': 'Resource pack ID'},
                    'resource-pack-prompt': {'type': 'str', 'default': '', 'description': 'Resource pack prompt message'},
                    'require-resource-pack': {'type': 'bool', 'default': False, 'description': 'Require resource pack'}
                }
            }
        }
    
    def load_properties(self, server_jar_path: str) -> bool:
        """Load server.properties from the server directory"""
        try:
            if not server_jar_path:
                return False
            
            server_dir = os.path.dirname(server_jar_path)
            self.properties_file_path = os.path.join(server_dir, 'server.properties')
            
            self.properties = {}
            
            if os.path.exists(self.properties_file_path):
                with open(self.properties_file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            self.properties[key.strip()] = value.strip()
            
            logging.info(f"Loaded {len(self.properties)} server properties")
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, "load_server_properties", ErrorSeverity.MEDIUM)
            return False
    
    def save_properties(self) -> bool:
        """Save server.properties to file"""
        try:
            if not self.properties_file_path:
                raise ValueError("No properties file path set")
            
            # Create backup of original file
            if os.path.exists(self.properties_file_path):
                backup_path = self.properties_file_path + '.backup'
                import shutil
                shutil.copy2(self.properties_file_path, backup_path)
            
            # Write properties file
            with open(self.properties_file_path, 'w', encoding='utf-8') as f:
                f.write(f"#Minecraft server properties\n")
                f.write(f"#{self._get_timestamp()}\n")
                
                # Write properties in organized order
                written_keys = set()
                
                for category_info in self.property_definitions.values():
                    for prop_key in category_info['properties'].keys():
                        if prop_key in self.properties:
                            f.write(f"{prop_key}={self.properties[prop_key]}\n")
                            written_keys.add(prop_key)
                
                # Write any additional properties not in our definitions
                for key, value in self.properties.items():
                    if key not in written_keys:
                        f.write(f"{key}={value}\n")
            
            logging.info(f"Saved server properties to {self.properties_file_path}")
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, "save_server_properties", ErrorSeverity.HIGH)
            return False
    
    def get_property(self, key: str) -> str:
        """Get a property value"""
        return self.properties.get(key, self._get_default_value(key))
    
    def set_property(self, key: str, value: str):
        """Set a property value"""
        self.properties[key] = str(value)
    
    def _get_default_value(self, key: str) -> str:
        """Get default value for a property"""
        for category_info in self.property_definitions.values():
            if key in category_info['properties']:
                default = category_info['properties'][key]['default']
                if isinstance(default, bool):
                    return 'true' if default else 'false'
                return str(default)
        return ''
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for properties file header"""
        from datetime import datetime
        return datetime.now().strftime("%a %b %d %H:%M:%S %Z %Y")
    
    def validate_property(self, key: str, value: str) -> tuple[bool, str]:
        """Validate a property value"""
        try:
            prop_def = None
            for category_info in self.property_definitions.values():
                if key in category_info['properties']:
                    prop_def = category_info['properties'][key]
                    break
            
            if not prop_def:
                return True, ""  # Unknown property, allow it
            
            prop_type = prop_def['type']
            
            if prop_type == 'bool':
                if value.lower() not in ['true', 'false']:
                    return False, "Must be 'true' or 'false'"
            
            elif prop_type == 'int':
                try:
                    int_value = int(value)
                    if 'range' in prop_def:
                        min_val, max_val = prop_def['range']
                        if not (min_val <= int_value <= max_val):
                            return False, f"Must be between {min_val} and {max_val}"
                except ValueError:
                    return False, "Must be a valid integer"
            
            elif prop_type == 'choice':
                if value not in prop_def['choices']:
                    return False, f"Must be one of: {', '.join(prop_def['choices'])}"
            
            return True, ""
            
        except Exception as e:
            return False, f"Validation error: {e}"
    
    def get_property_info(self, key: str) -> Optional[Dict[str, Any]]:
        """Get property definition info"""
        for category_info in self.property_definitions.values():
            if key in category_info['properties']:
                return category_info['properties'][key]
        return None
    
    def reset_to_defaults(self):
        """Reset all properties to their default values"""
        self.properties = {}
        for category_info in self.property_definitions.values():
            for prop_key, prop_def in category_info['properties'].items():
                default = prop_def['default']
                if isinstance(default, bool):
                    self.properties[prop_key] = 'true' if default else 'false'
                else:
                    self.properties[prop_key] = str(default)
    
    def export_properties(self, file_path: str) -> bool:
        """Export properties to a file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("# Exported Minecraft Server Properties\n")
                f.write(f"# {self._get_timestamp()}\n\n")
                
                for category_name, category_info in self.property_definitions.items():
                    f.write(f"# {category_info['name']}\n")
                    for prop_key in category_info['properties'].keys():
                        value = self.get_property(prop_key)
                        f.write(f"{prop_key}={value}\n")
                    f.write("\n")
            
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, "export_properties", ErrorSeverity.MEDIUM)
            return False
