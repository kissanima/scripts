"""
Core Mod Management System for Minecraft Server Manager
Handles all mod operations including installation, removal, updates, and organization
"""

import os
import json
import shutil
import hashlib
import zipfile
import logging
import threading
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

class ModLoaderType(Enum):
    """Supported mod loader types"""
    FORGE = "forge"
    FABRIC = "fabric"
    QUILT = "quilt"
    VANILLA = "vanilla"
    UNKNOWN = "unknown"

class ModCategory(Enum):
    """Mod categories for organization"""
    PERFORMANCE = "performance"
    CONTENT = "content"
    UTILITY = "utility"
    WORLD_GEN = "world_generation"
    MAGIC = "magic"
    TECH = "technology"
    ADVENTURE = "adventure"
    DECORATION = "decoration"
    FOOD = "food"
    TRANSPORTATION = "transportation"
    API = "api"
    LIBRARY = "library"
    OTHER = "other"

class ModSide(Enum):
    """Mod side compatibility"""
    CLIENT = "client"
    SERVER = "server"
    BOTH = "both"
    UNKNOWN = "unknown"

@dataclass
class ModInfo:
    """Complete mod information structure"""
    # Basic Information
    mod_id: str
    name: str
    version: str
    filename: str
    file_path: str
    
    # Metadata
    author: str = ""
    description: str = ""
    website: str = ""
    source_url: str = ""
    mod_loader: ModLoaderType = ModLoaderType.UNKNOWN
    supported_versions: List[str] = None
    side: ModSide = ModSide.UNKNOWN
    
    # Organization
    category: ModCategory = ModCategory.OTHER
    tags: List[str] = None
    is_favorite: bool = False
    is_essential: bool = False
    user_notes: str = ""
    
    # Technical Details
    file_size: int = 0
    file_hash: str = ""
    dependencies: List[str] = None
    optional_dependencies: List[str] = None
    conflicts: List[str] = None
    
    # Installation Info
    install_date: datetime = None
    last_updated: datetime = None
    download_source: str = ""
    project_id: str = ""
    file_id: str = ""
    
    # Status
    is_enabled: bool = True
    has_config: bool = False
    config_files: List[str] = None
    update_available: bool = False
    latest_version: str = ""
    
    def __post_init__(self):
        if self.supported_versions is None:
            self.supported_versions = []
        if self.tags is None:
            self.tags = []
        if self.dependencies is None:
            self.dependencies = []
        if self.optional_dependencies is None:
            self.optional_dependencies = []
        if self.conflicts is None:
            self.conflicts = []
        if self.config_files is None:
            self.config_files = []
        if self.install_date is None:
            self.install_date = datetime.now()

@dataclass
class ModProfile:
    """Mod profile for different server configurations"""
    name: str
    description: str
    enabled_mods: List[str]
    disabled_mods: List[str]
    profile_config: Dict[str, Any]
    created_date: datetime
    last_used: datetime
    
    def __post_init__(self):
        if self.enabled_mods is None:
            self.enabled_mods = []
        if self.disabled_mods is None:
            self.disabled_mods = []
        if self.profile_config is None:
            self.profile_config = {}

class ModManager:
    """Enterprise-grade mod management system"""
    
    def __init__(self, config, error_handler, server_dir: str = None):
        self.config = config
        self.error_handler = error_handler
        self.server_dir = server_dir or ""
        
        # Core paths
        self.mods_dir = os.path.join(self.server_dir, "mods") if self.server_dir else ""
        self.config_dir = os.path.join(self.server_dir, "config") if self.server_dir else ""
        self.mod_data_dir = os.path.join(self.server_dir, "mod_manager_data")
        
        # Data storage
        self.mods_database_file = os.path.join(self.mod_data_dir, "mods_database.json")
        self.profiles_file = os.path.join(self.mod_data_dir, "mod_profiles.json")
        self.settings_file = os.path.join(self.mod_data_dir, "mod_settings.json")
        
        # In-memory data
        self.installed_mods: Dict[str, ModInfo] = {}
        self.mod_profiles: Dict[str, ModProfile] = {}
        self.current_profile: str = "default"
        
        # Settings
        self.settings = {
            "auto_backup": True,
            "check_updates": True,
            "update_check_interval": 24,  # hours
            "auto_install_dependencies": True,
            "backup_count": 10,
            "enable_mod_caching": True,
            "cache_size_limit": 1000,  # MB
            "scan_on_startup": True,
            "safe_mode": True,
            "mod_loader_type": ModLoaderType.UNKNOWN.value
        }
        
        # State
        self.is_scanning = False
        self.scan_progress = 0
        self.last_scan_time = None
        
        # Callbacks
        self.scan_callbacks = []
        self.update_callbacks = []
        self.install_callbacks = []
        
        # Initialize
        self.initialize()
    
    def initialize(self):
        """Initialize the mod manager"""
        try:
            # Create directories
            self.ensure_directories()
            
            # Load data
            self.load_settings()
            self.load_database()
            self.load_profiles()
            
            # Initial scan if enabled
            if self.settings.get("scan_on_startup", True) and self.server_dir:
                threading.Thread(target=self.scan_mods, daemon=True).start()
            
            logging.info("ModManager initialized successfully")
            
        except Exception as e:
            logging.error(f"Failed to initialize ModManager: {e}")
            raise
    
    def ensure_directories(self):
        """Ensure all required directories exist"""
        directories = [
            self.mod_data_dir,
            os.path.join(self.mod_data_dir, "backups"),
            os.path.join(self.mod_data_dir, "cache"),
            os.path.join(self.mod_data_dir, "temp")
        ]
        
        if self.server_dir:
            directories.extend([
                self.mods_dir,
                self.config_dir
            ])
        
        for directory in directories:
            if directory:
                os.makedirs(directory, exist_ok=True)
    
    # === Data Persistence ===
    
    def load_settings(self):
        """Load mod manager settings"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    self.settings.update(loaded_settings)
            
            logging.info("Mod settings loaded")
            
        except Exception as e:
            logging.error(f"Failed to load mod settings: {e}")
    
    def save_settings(self):
        """Save mod manager settings"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            
            logging.info("Mod settings saved")
            
        except Exception as e:
            logging.error(f"Failed to save mod settings: {e}")
    
    def load_database(self):
        """Load mods database"""
        try:
            if os.path.exists(self.mods_database_file):
                with open(self.mods_database_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.installed_mods = {}
                for mod_id, mod_data in data.items():
                    # Convert datetime strings back to datetime objects
                    if 'install_date' in mod_data and mod_data['install_date']:
                        mod_data['install_date'] = datetime.fromisoformat(mod_data['install_date'])
                    if 'last_updated' in mod_data and mod_data['last_updated']:
                        mod_data['last_updated'] = datetime.fromisoformat(mod_data['last_updated'])
                    
                    # Convert enums
                    if 'mod_loader' in mod_data:
                        mod_data['mod_loader'] = ModLoaderType(mod_data['mod_loader'])
                    if 'category' in mod_data:
                        mod_data['category'] = ModCategory(mod_data['category'])
                    if 'side' in mod_data:
                        mod_data['side'] = ModSide(mod_data['side'])
                    
                    self.installed_mods[mod_id] = ModInfo(**mod_data)
            
            logging.info(f"Loaded {len(self.installed_mods)} mods from database")
            
        except Exception as e:
            logging.error(f"Failed to load mods database: {e}")
            self.installed_mods = {}
    
    def save_database(self):
        """Save mods database"""
        try:
            data = {}
            for mod_id, mod_info in self.installed_mods.items():
                mod_data = asdict(mod_info)
                
                # Convert datetime objects to strings
                if mod_data['install_date']:
                    mod_data['install_date'] = mod_data['install_date'].isoformat()
                if mod_data['last_updated']:
                    mod_data['last_updated'] = mod_data['last_updated'].isoformat()
                
                # Convert enums to strings
                mod_data['mod_loader'] = mod_data['mod_loader'].value
                mod_data['category'] = mod_data['category'].value
                mod_data['side'] = mod_data['side'].value
                
                data[mod_id] = mod_data
            
            with open(self.mods_database_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logging.info("Mods database saved")
            
        except Exception as e:
            logging.error(f"Failed to save mods database: {e}")
    
    def load_profiles(self):
        """Load mod profiles"""
        try:
            if os.path.exists(self.profiles_file):
                with open(self.profiles_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.mod_profiles = {}
                for profile_name, profile_data in data.items():
                    # Convert datetime strings back to datetime objects
                    if 'created_date' in profile_data:
                        profile_data['created_date'] = datetime.fromisoformat(profile_data['created_date'])
                    if 'last_used' in profile_data:
                        profile_data['last_used'] = datetime.fromisoformat(profile_data['last_used'])
                    
                    self.mod_profiles[profile_name] = ModProfile(**profile_data)
            
            # Ensure default profile exists
            if "default" not in self.mod_profiles:
                self.create_profile("default", "Default mod configuration", set_as_current=True)
            
            logging.info(f"Loaded {len(self.mod_profiles)} mod profiles")
            
        except Exception as e:
            logging.error(f"Failed to load mod profiles: {e}")
            self.mod_profiles = {}
    
    def save_profiles(self):
        """Save mod profiles"""
        try:
            data = {}
            for profile_name, profile in self.mod_profiles.items():
                profile_data = asdict(profile)
                
                # Convert datetime objects to strings
                profile_data['created_date'] = profile_data['created_date'].isoformat()
                profile_data['last_used'] = profile_data['last_used'].isoformat()
                
                data[profile_name] = profile_data
            
            with open(self.profiles_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logging.info("Mod profiles saved")
            
        except Exception as e:
            logging.error(f"Failed to save mod profiles: {e}")
    
    # === Mod Scanning and Detection ===
    
    def scan_mods(self, force_rescan: bool = False) -> Dict[str, ModInfo]:
        """Scan for mods in the mods directory with detailed debugging"""
        print("=" * 50)
        print("🔍 MOD SCAN DEBUG")
        print(f"Server directory: {self.server_dir}")
        print(f"Mods directory: {self.mods_dir}")
        print(f"Mods dir exists: {os.path.exists(self.mods_dir) if self.mods_dir else 'No mods_dir set'}")
        
        if self.mods_dir and os.path.exists(self.mods_dir):
            try:
                all_files = os.listdir(self.mods_dir)
                print(f"All files in mods dir: {all_files}")
                
                jar_files = [f for f in all_files if f.lower().endswith(('.jar', '.jar.disabled'))]
                print(f"JAR files found: {jar_files}")
                
                if not jar_files:
                    print("❌ No JAR files found in mods directory")
                else:
                    print(f"✅ Found {len(jar_files)} potential mod files")
                    
            except Exception as e:
                print(f"❌ Error listing mods directory: {e}")
        else:
            print("❌ Mods directory doesn't exist or mods_dir is not set")
            
        print("=" * 50)
        """Scan mods directory and detect installed mods"""
        if self.is_scanning:
            logging.warning("Mod scan already in progress")
            return self.installed_mods
        
        if not self.mods_dir or not os.path.exists(self.mods_dir):
            logging.warning("Mods directory not found or not set")
            return {}
        
        try:
            self.is_scanning = True
            self.scan_progress = 0
            
            # Notify callbacks
            for callback in self.scan_callbacks:
                callback("started", 0, "Starting mod scan...")
            
            logging.info("Starting mod scan...")
            
            # Get all .jar files in mods directory
            jar_files = []
            for root, dirs, files in os.walk(self.mods_dir):
                for file in files:
                    if file.endswith('.jar'):
                        jar_files.append(os.path.join(root, file))
            
            total_files = len(jar_files)
            if total_files == 0:
                self.scan_progress = 100
                for callback in self.scan_callbacks:
                    callback("completed", 100, "No mod files found")
                return {}
            
            new_mods = {}
            updated_mods = []
            
            for i, jar_file in enumerate(jar_files):
                try:
                    self.scan_progress = int((i / total_files) * 100)
                    
                    # Notify callbacks
                    filename = os.path.basename(jar_file)
                    for callback in self.scan_callbacks:
                        callback("scanning", self.scan_progress, f"Scanning {filename}...")
                    
                    # Get file hash for change detection
                    file_hash = self.calculate_file_hash(jar_file)
                    
                    # Check if mod already exists and hasn't changed
                    existing_mod = None
                    for mod_info in self.installed_mods.values():
                        if mod_info.file_path == jar_file:
                            existing_mod = mod_info
                            break
                    
                    if existing_mod and existing_mod.file_hash == file_hash and not force_rescan:
                        new_mods[existing_mod.mod_id] = existing_mod
                        continue
                    
                    # Extract mod information
                    mod_info = self.extract_mod_info(jar_file)
                    if mod_info:
                        if existing_mod:
                            # Update existing mod
                            mod_info.install_date = existing_mod.install_date
                            mod_info.is_favorite = existing_mod.is_favorite
                            mod_info.is_essential = existing_mod.is_essential
                            mod_info.user_notes = existing_mod.user_notes
                            mod_info.tags = existing_mod.tags
                            updated_mods.append(mod_info.name)
                        
                        new_mods[mod_info.mod_id] = mod_info
                        
                        # Check for config files
                        self.detect_mod_config(mod_info)
                    
                except Exception as e:
                    logging.error(f"Error scanning mod {jar_file}: {e}")
                    continue
            
            # Update installed mods
            old_count = len(self.installed_mods)
            self.installed_mods = new_mods
            self.save_database()
            
            # Update scan time
            self.last_scan_time = datetime.now()
            
            # Log results
            new_count = len(new_mods)
            logging.info(f"Mod scan completed: {new_count} mods found, {len(updated_mods)} updated")
            
            # Notify callbacks
            for callback in self.scan_callbacks:
                callback("completed", 100, f"Found {new_count} mods")
            
            return self.installed_mods
            
        except Exception as e:
            logging.error(f"Error during mod scan: {e}")
            for callback in self.scan_callbacks:
                callback("error", self.scan_progress, f"Scan error: {str(e)}")
            return {}
        
        finally:
            self.is_scanning = False
    
    def extract_mod_info(self, jar_file: str) -> Optional[ModInfo]:
        """Extract mod information from JAR file"""
        try:
            with zipfile.ZipFile(jar_file, 'r') as zip_file:
                mod_info = ModInfo(
                    mod_id="",
                    name="",
                    version="",
                    filename=os.path.basename(jar_file),
                    file_path=jar_file,
                    file_size=os.path.getsize(jar_file),
                    file_hash=self.calculate_file_hash(jar_file)
                )
                
                # Try different mod metadata formats
                
                # 1. Try Fabric mod (fabric.mod.json)
                if self.extract_fabric_info(zip_file, mod_info):
                    mod_info.mod_loader = ModLoaderType.FABRIC
                    return mod_info
                
                # 2. Try Forge mod (META-INF/mods.toml or mcmod.info)
                if self.extract_forge_info(zip_file, mod_info):
                    mod_info.mod_loader = ModLoaderType.FORGE
                    return mod_info
                
                # 3. Try Quilt mod (quilt.mod.json)
                if self.extract_quilt_info(zip_file, mod_info):
                    mod_info.mod_loader = ModLoaderType.QUILT
                    return mod_info
                
                # 4. Fallback to filename parsing
                return self.parse_filename_info(mod_info)
                
        except Exception as e:
            logging.error(f"Error extracting mod info from {jar_file}: {e}")
            return None
    
    def extract_fabric_info(self, zip_file: zipfile.ZipFile, mod_info: ModInfo) -> bool:
        """Extract Fabric mod information"""
        try:
            fabric_json = zip_file.read('fabric.mod.json').decode('utf-8')
            fabric_data = json.loads(fabric_json)
            
            mod_info.mod_id = fabric_data.get('id', '')
            mod_info.name = fabric_data.get('name', mod_info.filename)
            mod_info.version = fabric_data.get('version', '')
            mod_info.description = fabric_data.get('description', '')
            mod_info.website = fabric_data.get('contact', {}).get('homepage', '')
            
            # Authors
            authors = fabric_data.get('authors', [])
            if authors:
                if isinstance(authors[0], dict):
                    mod_info.author = authors[0].get('name', '')
                else:
                    mod_info.author = str(authors[0])
            
            # Dependencies
            depends = fabric_data.get('depends', {})
            mod_info.dependencies = list(depends.keys())
            
            # Environment (side)
            environment = fabric_data.get('environment', '*')
            if environment == 'client':
                mod_info.side = ModSide.CLIENT
            elif environment == 'server':
                mod_info.side = ModSide.SERVER
            else:
                mod_info.side = ModSide.BOTH
            
            return True
            
        except (KeyError, json.JSONDecodeError, UnicodeDecodeError):
            return False
    
    def extract_forge_info(self, zip_file: zipfile.ZipFile, mod_info: ModInfo) -> bool:
        """Extract Forge mod information"""
        try:
            # Try modern Forge (mods.toml)
            try:
                mods_toml = zip_file.read('META-INF/mods.toml').decode('utf-8')
                return self.parse_forge_toml(mods_toml, mod_info)
            except KeyError:
                pass
            
            # Try legacy Forge (mcmod.info)
            try:
                mcmod_json = zip_file.read('mcmod.info').decode('utf-8')
                return self.parse_forge_mcmod(mcmod_json, mod_info)
            except KeyError:
                pass
            
            return False
            
        except Exception:
            return False
    
    def parse_forge_toml(self, toml_content: str, mod_info: ModInfo) -> bool:
        """Parse Forge mods.toml file"""
        try:
            # Simple TOML parsing for mod info
            lines = toml_content.split('\n')
            current_mod = {}
            
            for line in lines:
                line = line.strip()
                if line.startswith('modId'):
                    current_mod['modId'] = line.split('=')[1].strip().strip('"')
                elif line.startswith('version'):
                    current_mod['version'] = line.split('=')[1].strip().strip('"')
                elif line.startswith('displayName'):
                    current_mod['displayName'] = line.split('=')[1].strip().strip('"')
                elif line.startswith('description'):
                    current_mod['description'] = line.split('=')[1].strip().strip('"')
                elif line.startswith('authors'):
                    current_mod['authors'] = line.split('=')[1].strip().strip('"')
            
            if current_mod.get('modId'):
                mod_info.mod_id = current_mod['modId']
                mod_info.name = current_mod.get('displayName', mod_info.filename)
                mod_info.version = current_mod.get('version', '')
                mod_info.description = current_mod.get('description', '')
                mod_info.author = current_mod.get('authors', '')
                return True
            
            return False
            
        except Exception:
            return False
    
    def parse_forge_mcmod(self, json_content: str, mod_info: ModInfo) -> bool:
        """Parse legacy Forge mcmod.info file"""
        try:
            # Remove BOM if present
            if json_content.startswith('\ufeff'):
                json_content = json_content[1:]
            
            mcmod_data = json.loads(json_content)
            
            if isinstance(mcmod_data, list) and mcmod_data:
                mod_data = mcmod_data[0]
            elif isinstance(mcmod_data, dict):
                mod_data = mcmod_data
            else:
                return False
            
            mod_info.mod_id = mod_data.get('modid', '')
            mod_info.name = mod_data.get('name', mod_info.filename)
            mod_info.version = mod_data.get('version', '')
            mod_info.description = mod_data.get('description', '')
            mod_info.author = ', '.join(mod_data.get('authorList', []))
            mod_info.website = mod_data.get('url', '')
            
            return True
            
        except (json.JSONDecodeError, UnicodeDecodeError):
            return False
    
    def extract_quilt_info(self, zip_file: zipfile.ZipFile, mod_info: ModInfo) -> bool:
        """Extract Quilt mod information"""
        try:
            quilt_json = zip_file.read('quilt.mod.json').decode('utf-8')
            quilt_data = json.loads(quilt_json)
            
            # Quilt uses similar structure to Fabric
            mod_info.mod_id = quilt_data.get('quilt_loader', {}).get('id', '')
            mod_info.name = quilt_data.get('quilt_loader', {}).get('metadata', {}).get('name', mod_info.filename)
            mod_info.version = quilt_data.get('quilt_loader', {}).get('version', '')
            mod_info.description = quilt_data.get('quilt_loader', {}).get('metadata', {}).get('description', '')
            
            return True
            
        except (KeyError, json.JSONDecodeError, UnicodeDecodeError):
            return False
    
    def parse_filename_info(self, mod_info: ModInfo) -> ModInfo:
        """Parse mod info from filename as fallback"""
        filename = mod_info.filename
        name_without_ext = os.path.splitext(filename)[0]
        
        # Common patterns: modname-1.0.0.jar, modname_1.0.0.jar, modname-mc1.19.2-1.0.0.jar
        parts = name_without_ext.replace('_', '-').split('-')
        
        if len(parts) >= 2:
            # Assume first part is name, last part is version
            mod_info.name = parts[0]
            mod_info.version = parts[-1]
            mod_info.mod_id = parts[0].lower().replace(' ', '_')
        else:
            mod_info.name = name_without_ext
            mod_info.mod_id = name_without_ext.lower().replace(' ', '_')
            mod_info.version = "unknown"
        
        return mod_info
    
    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file"""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception:
            return ""
    
    def detect_mod_config(self, mod_info: ModInfo):
        """Detect configuration files for a mod"""
        if not self.config_dir or not os.path.exists(self.config_dir):
            return
        
        config_files = []
        mod_id_lower = mod_info.mod_id.lower()
        mod_name_lower = mod_info.name.lower().replace(' ', '_')
        
        # Common config file patterns
        patterns = [
            f"{mod_id_lower}.json",
            f"{mod_id_lower}.toml",
            f"{mod_id_lower}.cfg",
            f"{mod_name_lower}.json",
            f"{mod_name_lower}.toml",
            f"{mod_name_lower}.cfg",
            f"{mod_id_lower}-config.json",
            f"{mod_name_lower}-config.json"
        ]
        
        # Check for config files
        for root, dirs, files in os.walk(self.config_dir):
            for file in files:
                file_lower = file.lower()
                if any(pattern in file_lower for pattern in [mod_id_lower, mod_name_lower]):
                    config_files.append(os.path.join(root, file))
                
                # Check specific patterns
                for pattern in patterns:
                    if file_lower == pattern:
                        config_files.append(os.path.join(root, file))
        
        mod_info.config_files = config_files
        mod_info.has_config = len(config_files) > 0
    
    # === Mod Installation and Removal ===
    
    def install_mod(self, source_path: str, mod_info: ModInfo = None, enable_immediately: bool = True) -> Tuple[bool, str]:
        """Install a mod from source path"""
        try:
            if not os.path.exists(source_path):
                return False, "Source file does not exist"
            
            if not source_path.endswith('.jar'):
                return False, "Only .jar files are supported"
            
            # Ensure mods directory exists
            if not os.path.exists(self.mods_dir):
                os.makedirs(self.mods_dir, exist_ok=True)
            
            # Extract mod info if not provided
            if not mod_info:
                mod_info = self.extract_mod_info(source_path)
                if not mod_info:
                    return False, "Could not extract mod information"
            
            # Check for conflicts
            conflicts = self.check_mod_conflicts(mod_info)
            if conflicts:
                return False, f"Mod conflicts detected: {', '.join(conflicts)}"
            
            # Create backup if enabled
            if self.settings.get("auto_backup", True):
                self.create_backup("pre_install", f"Before installing {mod_info.name}")
            
            # Copy mod file
            target_path = os.path.join(self.mods_dir, mod_info.filename)
            
            # Handle filename conflicts
            counter = 1
            original_target = target_path
            while os.path.exists(target_path):
                name, ext = os.path.splitext(original_target)
                target_path = f"{name}_{counter}{ext}"
                counter += 1
            
            shutil.copy2(source_path, target_path)
            
            # Update mod info
            mod_info.file_path = target_path
            mod_info.filename = os.path.basename(target_path)
            mod_info.install_date = datetime.now()
            mod_info.is_enabled = enable_immediately
            mod_info.file_hash = self.calculate_file_hash(target_path)
            
            # Detect config files
            self.detect_mod_config(mod_info)
            
            # Install dependencies if enabled
            if self.settings.get("auto_install_dependencies", True):
                self.install_dependencies(mod_info)
            
            # Add to database
            self.installed_mods[mod_info.mod_id] = mod_info
            self.save_database()
            
            # Notify callbacks
            for callback in self.install_callbacks:
                callback("installed", mod_info, "Mod installed successfully")
            
            logging.info(f"Mod installed: {mod_info.name} v{mod_info.version}")
            return True, "Mod installed successfully"
            
        except Exception as e:
            logging.error(f"Error installing mod: {e}")
            return False, f"Installation failed: {str(e)}"
    
    def remove_mod(self, mod_id: str, remove_config: bool = False, create_backup: bool = True) -> Tuple[bool, str]:
        """Remove an installed mod"""
        try:
            if mod_id not in self.installed_mods:
                return False, "Mod not found"
            
            mod_info = self.installed_mods[mod_id]
            
            # Check if mod is essential
            if mod_info.is_essential:
                return False, "Cannot remove essential mod"
            
            # Check for dependents
            dependents = self.find_dependents(mod_id)
            if dependents:
                return False, f"Mod is required by: {', '.join(dependents)}"
            
            # Create backup if enabled
            if create_backup and self.settings.get("auto_backup", True):
                self.create_backup("pre_remove", f"Before removing {mod_info.name}")
            
            # Remove mod file
            if os.path.exists(mod_info.file_path):
                os.remove(mod_info.file_path)
            
            # Remove config files if requested
            if remove_config and mod_info.config_files:
                for config_file in mod_info.config_files:
                    if os.path.exists(config_file):
                        os.remove(config_file)
            
            # Remove from database
            del self.installed_mods[mod_id]
            self.save_database()
            
            # Notify callbacks
            for callback in self.install_callbacks:
                callback("removed", mod_info, "Mod removed successfully")
            
            logging.info(f"Mod removed: {mod_info.name}")
            return True, "Mod removed successfully"
            
        except Exception as e:
            logging.error(f"Error removing mod: {e}")
            return False, f"Removal failed: {str(e)}"
    
    def enable_mod(self, mod_id: str) -> Tuple[bool, str]:
        """Enable a disabled mod"""
        try:
            if mod_id not in self.installed_mods:
                return False, "Mod not found"
            
            mod_info = self.installed_mods[mod_id]
            
            if mod_info.is_enabled:
                return True, "Mod is already enabled"
            
            # Move from .disabled to .jar
            current_path = mod_info.file_path
            if current_path.endswith('.disabled'):
                new_path = current_path[:-9]  # Remove .disabled extension
                os.rename(current_path, new_path)
                mod_info.file_path = new_path
                mod_info.filename = os.path.basename(new_path)
            
            mod_info.is_enabled = True
            self.save_database()
            
            logging.info(f"Mod enabled: {mod_info.name}")
            return True, "Mod enabled successfully"
            
        except Exception as e:
            logging.error(f"Error enabling mod: {e}")
            return False, f"Enable failed: {str(e)}"
    
    def disable_mod(self, mod_id: str) -> Tuple[bool, str]:
        """Disable an enabled mod"""
        try:
            if mod_id not in self.installed_mods:
                return False, "Mod not found"
            
            mod_info = self.installed_mods[mod_id]
            
            if not mod_info.is_enabled:
                return True, "Mod is already disabled"
            
            # Check if mod is essential
            if mod_info.is_essential:
                return False, "Cannot disable essential mod"
            
            # Check for dependents
            dependents = self.find_dependents(mod_id)
            if dependents:
                return False, f"Mod is required by: {', '.join(dependents)}"
            
            # Rename to .disabled
            current_path = mod_info.file_path
            new_path = current_path + '.disabled'
            os.rename(current_path, new_path)
            
            mod_info.file_path = new_path
            mod_info.filename = os.path.basename(new_path)
            mod_info.is_enabled = False
            self.save_database()
            
            logging.info(f"Mod disabled: {mod_info.name}")
            return True, "Mod disabled successfully"
            
        except Exception as e:
            logging.error(f"Error disabling mod: {e}")
            return False, f"Disable failed: {str(e)}"
    
    # === Dependency Management ===
    
    def check_mod_conflicts(self, mod_info: ModInfo) -> List[str]:
        """Check for mod conflicts"""
        conflicts = []
        
        for existing_mod in self.installed_mods.values():
            # Check for same mod ID
            if existing_mod.mod_id == mod_info.mod_id:
                conflicts.append(f"Mod with same ID already installed: {existing_mod.name}")
            
            # Check explicit conflicts
            if mod_info.mod_id in existing_mod.conflicts:
                conflicts.append(f"Conflicting mod: {existing_mod.name}")
            
            if existing_mod.mod_id in mod_info.conflicts:
                conflicts.append(f"Conflicting mod: {existing_mod.name}")
        
        return conflicts
    
    def find_dependents(self, mod_id: str) -> List[str]:
        """Find mods that depend on the given mod"""
        dependents = []
        
        for mod_info in self.installed_mods.values():
            if mod_id in mod_info.dependencies:
                dependents.append(mod_info.name)
        
        return dependents
    
    def install_dependencies(self, mod_info: ModInfo):
        """Install missing dependencies for a mod"""
        # This would integrate with mod repositories to download dependencies
        # For now, just log what dependencies are needed
        missing_deps = []
        
        for dep_id in mod_info.dependencies:
            if dep_id not in self.installed_mods:
                missing_deps.append(dep_id)
        
        if missing_deps:
            logging.warning(f"Missing dependencies for {mod_info.name}: {', '.join(missing_deps)}")
    
    # === Profile Management ===
    
    def create_profile(self, name: str, description: str = "", set_as_current: bool = False) -> bool:
        """Create a new mod profile"""
        try:
            if name in self.mod_profiles:
                return False
            
            enabled_mods = [mod_id for mod_id, mod_info in self.installed_mods.items() if mod_info.is_enabled]
            disabled_mods = [mod_id for mod_id, mod_info in self.installed_mods.items() if not mod_info.is_enabled]
            
            profile = ModProfile(
                name=name,
                description=description,
                enabled_mods=enabled_mods,
                disabled_mods=disabled_mods,
                profile_config={},
                created_date=datetime.now(),
                last_used=datetime.now() if set_as_current else datetime.min
            )
            
            self.mod_profiles[name] = profile
            
            if set_as_current:
                self.current_profile = name
            
            self.save_profiles()
            
            logging.info(f"Profile created: {name}")
            return True
            
        except Exception as e:
            logging.error(f"Error creating profile: {e}")
            return False
    
    def apply_profile(self, profile_name: str) -> Tuple[bool, str]:
        """Apply a mod profile"""
        try:
            if profile_name not in self.mod_profiles:
                return False, "Profile not found"
            
            profile = self.mod_profiles[profile_name]
            
            # Create backup
            if self.settings.get("auto_backup", True):
                self.create_backup("pre_profile", f"Before applying profile {profile_name}")
            
            # Apply profile settings
            changes_made = 0
            
            for mod_id in self.installed_mods:
                current_enabled = self.installed_mods[mod_id].is_enabled
                should_be_enabled = mod_id in profile.enabled_mods
                
                if current_enabled != should_be_enabled:
                    if should_be_enabled:
                        success, _ = self.enable_mod(mod_id)
                    else:
                        success, _ = self.disable_mod(mod_id)
                    
                    if success:
                        changes_made += 1
            
            # Update profile last used
            profile.last_used = datetime.now()
            self.current_profile = profile_name
            self.save_profiles()
            
            logging.info(f"Profile applied: {profile_name} ({changes_made} changes)")
            return True, f"Profile applied successfully ({changes_made} mods changed)"
            
        except Exception as e:
            logging.error(f"Error applying profile: {e}")
            return False, f"Failed to apply profile: {str(e)}"
    
    def delete_profile(self, profile_name: str) -> bool:
        """Delete a mod profile"""
        try:
            if profile_name == "default":
                return False  # Cannot delete default profile
            
            if profile_name not in self.mod_profiles:
                return False
            
            del self.mod_profiles[profile_name]
            
            if self.current_profile == profile_name:
                self.current_profile = "default"
            
            self.save_profiles()
            
            logging.info(f"Profile deleted: {profile_name}")
            return True
            
        except Exception as e:
            logging.error(f"Error deleting profile: {e}")
            return False
    
    # === Backup Management ===
    
    def create_backup(self, backup_type: str = "manual", description: str = "") -> Tuple[bool, str]:
        """Create a backup of current mod configuration"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"mod_backup_{backup_type}_{timestamp}"
            backup_dir = os.path.join(self.mod_data_dir, "backups", backup_name)
            
            os.makedirs(backup_dir, exist_ok=True)
            
            # Backup mods directory
            if os.path.exists(self.mods_dir):
                mods_backup_dir = os.path.join(backup_dir, "mods")
                shutil.copytree(self.mods_dir, mods_backup_dir)
            
            # Backup config directory
            if os.path.exists(self.config_dir):
                config_backup_dir = os.path.join(backup_dir, "config")
                shutil.copytree(self.config_dir, config_backup_dir)
            
            # Backup mod manager data
            data_backup_dir = os.path.join(backup_dir, "mod_data")
            os.makedirs(data_backup_dir, exist_ok=True)
            
            for file in [self.mods_database_file, self.profiles_file, self.settings_file]:
                if os.path.exists(file):
                    shutil.copy2(file, data_backup_dir)
            
            # Create backup info file
            backup_info = {
                "timestamp": timestamp,
                "type": backup_type,
                "description": description,
                "mod_count": len(self.installed_mods),
                "enabled_mods": len([m for m in self.installed_mods.values() if m.is_enabled]),
                "current_profile": self.current_profile
            }
            
            with open(os.path.join(backup_dir, "backup_info.json"), 'w') as f:
                json.dump(backup_info, f, indent=2)
            
            # Clean up old backups
            self.cleanup_old_backups()
            
            logging.info(f"Backup created: {backup_name}")
            return True, backup_name
            
        except Exception as e:
            logging.error(f"Error creating backup: {e}")
            return False, str(e)
    
    def cleanup_old_backups(self):
        """Clean up old backups based on settings"""
        try:
            backup_limit = self.settings.get("backup_count", 10)
            backups_dir = os.path.join(self.mod_data_dir, "backups")
            
            if not os.path.exists(backups_dir):
                return
            
            # Get all backup directories
            backups = []
            for item in os.listdir(backups_dir):
                backup_path = os.path.join(backups_dir, item)
                if os.path.isdir(backup_path):
                    # Get creation time
                    creation_time = os.path.getctime(backup_path)
                    backups.append((creation_time, backup_path))
            
            # Sort by creation time (oldest first)
            backups.sort()
            
            # Remove excess backups
            while len(backups) > backup_limit:
                _, backup_path = backups.pop(0)
                shutil.rmtree(backup_path)
                logging.info(f"Removed old backup: {os.path.basename(backup_path)}")
            
        except Exception as e:
            logging.error(f"Error cleaning up backups: {e}")
    
    # === Search and Filter ===
    
    def search_mods(self, query: str, filters: Dict[str, Any] = None) -> List[ModInfo]:
        """Search installed mods with filters"""
        results = []
        query_lower = query.lower()
        
        for mod_info in self.installed_mods.values():
            # Text search
            if query:
                if not any(query_lower in field.lower() for field in [
                    mod_info.name, mod_info.description, mod_info.author,
                    ' '.join(mod_info.tags), mod_info.user_notes
                ]):
                    continue
            
            # Apply filters
            if filters:
                if 'category' in filters and mod_info.category != filters['category']:
                    continue
                
                if 'mod_loader' in filters and mod_info.mod_loader != filters['mod_loader']:
                    continue
                
                if 'enabled' in filters and mod_info.is_enabled != filters['enabled']:
                    continue
                
                if 'has_update' in filters and mod_info.update_available != filters['has_update']:
                    continue
                
                if 'favorite' in filters and mod_info.is_favorite != filters['favorite']:
                    continue
            
            results.append(mod_info)
        
        return results
    
    def get_mods_by_category(self) -> Dict[ModCategory, List[ModInfo]]:
        """Get mods organized by category"""
        categories = {}
        
        for category in ModCategory:
            categories[category] = []
        
        for mod_info in self.installed_mods.values():
            categories[mod_info.category].append(mod_info)
        
        return categories
    
    # === Statistics and Analytics ===
    
    def get_mod_statistics(self) -> Dict[str, Any]:
        """Get comprehensive mod statistics"""
        total_mods = len(self.installed_mods)
        enabled_mods = len([m for m in self.installed_mods.values() if m.is_enabled])
        disabled_mods = total_mods - enabled_mods
        
        # Category breakdown
        category_counts = {}
        for category in ModCategory:
            category_counts[category.value] = len([
                m for m in self.installed_mods.values() 
                if m.category == category
            ])
        
        # Mod loader breakdown
        loader_counts = {}
        for loader in ModLoaderType:
            loader_counts[loader.value] = len([
                m for m in self.installed_mods.values() 
                if m.mod_loader == loader
            ])
        
        # Update statistics
        outdated_mods = len([m for m in self.installed_mods.values() if m.update_available])
        
        # Size statistics
        total_size = sum(m.file_size for m in self.installed_mods.values())
        
        return {
            "total_mods": total_mods,
            "enabled_mods": enabled_mods,
            "disabled_mods": disabled_mods,
            "category_breakdown": category_counts,
            "loader_breakdown": loader_counts,
            "outdated_mods": outdated_mods,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "favorite_mods": len([m for m in self.installed_mods.values() if m.is_favorite]),
            "essential_mods": len([m for m in self.installed_mods.values() if m.is_essential]),
            "mods_with_config": len([m for m in self.installed_mods.values() if m.has_config]),
            "last_scan_time": self.last_scan_time.isoformat() if self.last_scan_time else None,
            "current_profile": self.current_profile,
            "total_profiles": len(self.mod_profiles)
        }
    
    # === Callback Management ===
    
    def register_scan_callback(self, callback):
        """Register callback for scan progress updates"""
        self.scan_callbacks.append(callback)
    
    def register_update_callback(self, callback):
        """Register callback for update notifications"""
        self.update_callbacks.append(callback)
    
    def register_install_callback(self, callback):
        """Register callback for install/remove events"""
        self.install_callbacks.append(callback)
    
    # === Utility Methods ===
    
    def get_mod_info(self, mod_id: str) -> Optional[ModInfo]:
        """Get mod information by ID"""
        return self.installed_mods.get(mod_id)
    
    def update_mod_info(self, mod_id: str, **kwargs) -> bool:
        """Update mod information"""
        if mod_id not in self.installed_mods:
            return False
        
        mod_info = self.installed_mods[mod_id]
        
        for key, value in kwargs.items():
            if hasattr(mod_info, key):
                setattr(mod_info, key, value)
        
        self.save_database()
        return True
    
    def export_mod_list(self, format_type: str = "json") -> str:
        """Export mod list in specified format"""
        if format_type == "json":
            mod_list = []
            for mod_info in self.installed_mods.values():
                mod_data = {
                    "name": mod_info.name,
                    "version": mod_info.version,
                    "mod_id": mod_info.mod_id,
                    "author": mod_info.author,
                    "filename": mod_info.filename,
                    "enabled": mod_info.is_enabled
                }
                mod_list.append(mod_data)
            
            return json.dumps(mod_list, indent=2)
        
        elif format_type == "text":
            lines = []
            for mod_info in self.installed_mods.values():
                status = "✓" if mod_info.is_enabled else "✗"
                lines.append(f"{status} {mod_info.name} v{mod_info.version} by {mod_info.author}")
            
            return "\n".join(lines)
        
        return ""
    
    def set_server_directory(self, server_dir: str):
        """Update server directory and reinitialize paths"""
        self.server_dir = server_dir
        self.mods_dir = os.path.join(server_dir, "mods")
        self.config_dir = os.path.join(server_dir, "config")
        self.mod_data_dir = os.path.join(server_dir, "mod_manager_data")
        
        # Update file paths
        self.mods_database_file = os.path.join(self.mod_data_dir, "mods_database.json")
        self.profiles_file = os.path.join(self.mod_data_dir, "mod_profiles.json")
        self.settings_file = os.path.join(self.mod_data_dir, "mod_settings.json")
        
        # Ensure directories and reload data
        self.ensure_directories()
        self.load_settings()
        self.load_database()
        self.load_profiles()
        
        # Trigger rescan
        if os.path.exists(self.mods_dir):
            threading.Thread(target=self.scan_mods, daemon=True).start()
            
        
    def register_install_callback(self, callback):
        """Register callback for mod installations"""
        if not hasattr(self, 'install_callbacks'):
            self.install_callbacks = []
        self.install_callbacks.append(callback)

    def save_database(self):
        """Save mod database to file with safe JSON serialization"""
        try:
            os.makedirs(os.path.dirname(self.mods_database_file), exist_ok=True)
            
            with open(self.mods_database_file, 'w', encoding='utf-8') as f:
                data = {}
                for modid, modinfo in self.installed_mods.items():
                    # Helper function to safely convert values to JSON-serializable format
                    def safe_value(obj):
                        if hasattr(obj, 'value'):  # Handle enums
                            return obj.value
                        elif isinstance(obj, (list, tuple)):
                            return [safe_value(item) for item in obj]
                        elif isinstance(obj, dict):
                            return {k: safe_value(v) for k, v in obj.items()}
                        else:
                            return str(obj) if obj is not None else None
                    
                    data[modid] = {
                        'mod_id': modinfo.mod_id,
                        'name': modinfo.name,
                        'version': modinfo.version,
                        'is_enabled': modinfo.is_enabled,
                        'file_path': modinfo.file_path,
                        'author': safe_value(getattr(modinfo, 'author', 'Unknown')),
                        'description': safe_value(getattr(modinfo, 'description', '')),
                        'mod_loader': safe_value(getattr(modinfo, 'mod_loader', 'Unknown')),  # ✅ Safe enum conversion
                        'file_size': getattr(modinfo, 'file_size', 0),
                        'install_date': safe_value(getattr(modinfo, 'install_date', '')),
                        'is_favorite': getattr(modinfo, 'is_favorite', False),
                        'tags': safe_value(getattr(modinfo, 'tags', [])),
                        'has_config': getattr(modinfo, 'has_config', False)
                    }
                
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logging.info(f"Mod database saved successfully with {len(data)} mods")
            
        except Exception as e:
            logging.error(f"Error saving mod database: {e}")
            import traceback
            traceback.print_exc()





    def set_server_directory(self, new_server_dir: str):
        """Set new server directory"""
        self.server_dir = new_server_dir
        self.mods_dir = os.path.join(self.server_dir, "mods") if self.server_dir else ""
        self.config_dir = os.path.join(self.server_dir, "config") if self.server_dir else ""
        logging.info(f"Server directory updated to: {new_server_dir}")

