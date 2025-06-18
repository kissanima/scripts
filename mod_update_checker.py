"""
Mod Update Checker for Minecraft Server Manager
Monitors mods for available updates from various sources
"""
import os
import json
import logging
import threading
import requests
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from mod_manager import ModInfo, ModLoaderType

class UpdateStatus(Enum):
    """Update status types"""
    UP_TO_DATE = "up_to_date"
    UPDATE_AVAILABLE = "update_available"
    UNKNOWN = "unknown"
    ERROR = "error"

@dataclass
class UpdateInfo:
    """Update information structure"""
    modid: str
    current_version: str
    latest_version: str
    update_status: UpdateStatus
    download_url: str = ""
    changelog_url: str = ""
    release_date: datetime = None
    update_source: str = ""
    release_type: str = "release"  # release, beta, alpha
    file_size: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'modid': self.modid,
            'current_version': self.current_version,
            'latest_version': self.latest_version,
            'update_status': self.update_status.value,
            'download_url': self.download_url,
            'changelog_url': self.changelog_url,
            'release_date': self.release_date.isoformat() if self.release_date else None,
            'update_source': self.update_source,
            'release_type': self.release_type,
            'file_size': self.file_size
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UpdateInfo':
        """Create from dictionary"""
        release_date = None
        if data.get('release_date'):
            release_date = datetime.fromisoformat(data['release_date'])
        
        return cls(
            modid=data['modid'],
            current_version=data['current_version'],
            latest_version=data['latest_version'],
            update_status=UpdateStatus(data['update_status']),
            download_url=data.get('download_url', ''),
            changelog_url=data.get('changelog_url', ''),
            release_date=release_date,
            update_source=data.get('update_source', ''),
            release_type=data.get('release_type', 'release'),
            file_size=data.get('file_size', 0)
        )

class ModUpdateChecker:
    """Comprehensive mod update checking system"""
    
    def __init__(self, modmanager, config):
        self.modmanager = modmanager
        self.config = config
        
        # Update cache
        self.update_cache: Dict[str, UpdateInfo] = {}
        self.cache_file = ""
        
        # API endpoints
        self.api_endpoints = {
            'modrinth': 'https://api.modrinth.com/v2',
            'curseforge': 'https://api.curseforge.com/v1',
            'github': 'https://api.github.com'
        }
        
        # Settings
        self.settings = {
            "auto_check_enabled": True,
            "check_interval_hours": 24,
            "include_prereleases": False,
            "include_beta_versions": False,
            "check_sources": ["modrinth", "curseforge"],
            "notification_enabled": True,
            "auto_download_updates": False,
            "backup_before_update": True,
            "update_check_timeout": 30
        }
        
        # State
        self.check_in_progress = False
        self.last_check_time = None
        self.check_progress = 0
        
        # Callbacks
        self.progress_callbacks = []
        self.completion_callbacks = []
        self.update_found_callbacks = []
        
        # Background check timer
        self.check_timer = None
        
        self.initialize()
    
    def initialize(self):
        """Initialize the update checker"""
        try:
            self.setup_cache_file()
            self.load_update_cache()
            self.schedule_next_check()
            logging.info("ModUpdateChecker initialized")
        except Exception as e:
            logging.error(f"Failed to initialize ModUpdateChecker: {e}")
    
    def setup_cache_file(self):
        """Set up cache file path"""
        if hasattr(self.modmanager, 'moddatadir'):
            self.cache_file = os.path.join(
                self.modmanager.moddatadir,
                "update_cache.json"
            )
        else:
            self.cache_file = "update_cache.json"
    
    def load_update_cache(self):
        """Load update cache from file"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                # Convert cache data back to UpdateInfo objects
                for modid, update_data in cache_data.get('updates', {}).items():
                    try:
                        self.update_cache[modid] = UpdateInfo.from_dict(update_data)
                    except Exception as e:
                        logging.error(f"Error loading update info for {modid}: {e}")
                
                # Load last check time
                if 'last_check_time' in cache_data:
                    self.last_check_time = datetime.fromisoformat(cache_data['last_check_time'])
                
                logging.info(f"Loaded update cache with {len(self.update_cache)} entries")
        
        except Exception as e:
            logging.error(f"Failed to load update cache: {e}")
            self.update_cache = {}
    
    def save_update_cache(self):
        """Save update cache to file"""
        try:
            cache_data = {
                'last_check_time': self.last_check_time.isoformat() if self.last_check_time else None,
                'updates': {}
            }
            
            # Convert UpdateInfo objects to serializable dict
            for modid, update_info in self.update_cache.items():
                cache_data['updates'][modid] = update_info.to_dict()
            
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            logging.info("Update cache saved")
        
        except Exception as e:
            logging.error(f"Failed to save update cache: {e}")
    
    def check_for_updates(self, force_check: bool = False) -> Dict[str, UpdateInfo]:
        """Check for updates for all installed mods"""
        if self.check_in_progress and not force_check:
            logging.info("Update check already in progress")
            return self.update_cache
        
        try:
            self.check_in_progress = True
            self.check_progress = 0
            
            # Get installed mods
            installed_mods = {}
            if hasattr(self.modmanager, 'installedmods'):
                installed_mods = self.modmanager.installedmods
            
            if not installed_mods:
                logging.info("No installed mods to check for updates")
                return {}
            
            self.notify_progress(5, "Preparing update check...")
            
            # Check each mod for updates
            total_mods = len(installed_mods)
            checked_mods = 0
            
            for modid, modinfo in installed_mods.items():
                try:
                    self.notify_progress(
                        10 + (checked_mods * 80 // total_mods),
                        f"Checking {modinfo.name}..."
                    )
                    
                    update_info = self.check_mod_update(modinfo)
                    if update_info:
                        self.update_cache[modid] = update_info
                        
                        # Notify if update available
                        if update_info.update_status == UpdateStatus.UPDATE_AVAILABLE:
                            self.notify_update_found(update_info)
                    
                    checked_mods += 1
                    
                except Exception as e:
                    logging.error(f"Error checking updates for {modinfo.name}: {e}")
                    # Create error entry
                    self.update_cache[modid] = UpdateInfo(
                        modid=modid,
                        current_version=modinfo.version,
                        latest_version="unknown",
                        update_status=UpdateStatus.ERROR
                    )
            
            self.last_check_time = datetime.now()
            self.notify_progress(90, "Saving update cache...")
            
            # Save cache
            self.save_update_cache()
            
            # Schedule next check
            self.schedule_next_check()
            
            self.notify_progress(100, "Update check completed")
            
            # Notify completion
            self.notify_completion()
            
            return self.update_cache
            
        except Exception as e:
            logging.error(f"Error during update check: {e}")
            return {}
        
        finally:
            self.check_in_progress = False
            self.check_progress = 0
    
    def check_mod_update(self, modinfo: ModInfo) -> Optional[UpdateInfo]:
        """Check for updates for a specific mod"""
        update_info = None
        
        # Try different sources
        for source in self.settings["check_sources"]:
            try:
                if source == "modrinth":
                    update_info = self.check_modrinth_update(modinfo)
                elif source == "curseforge":
                    update_info = self.check_curseforge_update(modinfo)
                elif source == "github":
                    update_info = self.check_github_update(modinfo)
                
                if update_info and update_info.update_status != UpdateStatus.UNKNOWN:
                    break
                    
            except Exception as e:
                logging.error(f"Error checking {source} for {modinfo.name}: {e}")
        
        # If no source provided updates, create default entry
        if not update_info:
            update_info = UpdateInfo(
                modid=modinfo.modid,
                current_version=modinfo.version,
                latest_version=modinfo.version,
                update_status=UpdateStatus.UNKNOWN
            )
        
        return update_info
    
    def check_modrinth_update(self, modinfo: ModInfo) -> Optional[UpdateInfo]:
        """Check for updates on Modrinth"""
        try:
            # Search for the mod
            search_url = f"{self.api_endpoints['modrinth']}/search"
            search_params = {
                "query": modinfo.name,
                "facets": '[["project_type:mod"]]',
                "limit": 5
            }
            
            response = requests.get(
                search_url, 
                params=search_params, 
                timeout=self.settings["update_check_timeout"]
            )
            response.raise_for_status()
            
            search_data = response.json()
            
            # Find matching project
            project = None
            for hit in search_data.get("hits", []):
                if (hit["title"].lower() == modinfo.name.lower() or 
                    hit["slug"] == modinfo.modid):
                    project = hit
                    break
            
            if not project:
                return None
            
            # Get project versions
            project_id = project["project_id"]
            versions_url = f"{self.api_endpoints['modrinth']}/project/{project_id}/version"
            
            response = requests.get(versions_url, timeout=self.settings["update_check_timeout"])
            response.raise_for_status()
            
            versions = response.json()
            
            if not versions:
                return None
            
            # Find latest compatible version
            latest_version = self.find_latest_compatible_version(versions, modinfo)
            
            if not latest_version:
                return None
            
            # Compare versions
            is_newer = self.is_version_newer(
                latest_version["version_number"], 
                modinfo.version
            )
            
            update_status = UpdateStatus.UPDATE_AVAILABLE if is_newer else UpdateStatus.UP_TO_DATE
            
            # Get download info
            download_url = ""
            file_size = 0
            if latest_version.get("files"):
                primary_file = latest_version["files"][0]
                download_url = primary_file.get("url", "")
                file_size = primary_file.get("size", 0)
            
            return UpdateInfo(
                modid=modinfo.modid,
                current_version=modinfo.version,
                latest_version=latest_version["version_number"],
                update_status=update_status,
                download_url=download_url,
                changelog_url=f"https://modrinth.com/mod/{project['slug']}/changelog",
                release_date=datetime.fromisoformat(latest_version["date_published"].replace('Z', '+00:00')),
                update_source="modrinth",
                release_type=latest_version.get("version_type", "release"),
                file_size=file_size
            )
            
        except Exception as e:
            logging.error(f"Error checking Modrinth for {modinfo.name}: {e}")
            return None
    
    def check_curseforge_update(self, modinfo: ModInfo) -> Optional[UpdateInfo]:
        """Check for updates on CurseForge"""
        try:
            # CurseForge API requires API key
            # This is a placeholder implementation
            logging.info(f"CurseForge update check not implemented for {modinfo.name}")
            return None
            
        except Exception as e:
            logging.error(f"Error checking CurseForge for {modinfo.name}: {e}")
            return None
    
    def check_github_update(self, modinfo: ModInfo) -> Optional[UpdateInfo]:
        """Check for updates on GitHub (for mods with GitHub releases)"""
        try:
            # This would need the GitHub repository URL
            # Placeholder implementation
            if not hasattr(modinfo, 'website') or not modinfo.website:
                return None
            
            if "github.com" not in modinfo.website.lower():
                return None
            
            # Extract repo info from URL
            # Implementation would go here
            
            return None
            
        except Exception as e:
            logging.error(f"Error checking GitHub for {modinfo.name}: {e}")
            return None
    
    def find_latest_compatible_version(self, versions: List[Dict], modinfo: ModInfo) -> Optional[Dict]:
        """Find the latest compatible version from a list"""
        compatible_versions = []
        
        for version in versions:
            # Check game version compatibility
            game_versions = version.get("game_versions", [])
            loaders = version.get("loaders", [])
            
            # Filter by mod loader
            if modinfo.modloader != ModLoaderType.UNKNOWN:
                loader_name = modinfo.modloader.value.lower()
                if loader_name not in [l.lower() for l in loaders]:
                    continue
            
            # Check release type
            version_type = version.get("version_type", "release")
            if not self.should_include_version_type(version_type):
                continue
            
            compatible_versions.append(version)
        
        # Return the most recent compatible version
        if compatible_versions:
            # Sort by date published (most recent first)
            compatible_versions.sort(
                key=lambda v: v.get("date_published", ""), 
                reverse=True
            )
            return compatible_versions[0]
        
        return None
    
    def should_include_version_type(self, version_type: str) -> bool:
        """Check if version type should be included based on settings"""
        if version_type == "release":
            return True
        elif version_type == "beta" and self.settings["include_beta_versions"]:
            return True
        elif version_type in ["alpha", "snapshot"] and self.settings["include_prereleases"]:
            return True
        
        return False
    
    def is_version_newer(self, new_version: str, current_version: str) -> bool:
        """Compare two version strings"""
        try:
            def normalize_version(v):
                # Extract numeric parts
                parts = []
                for part in v.split('.'):
                    # Extract numbers from version part
                    num_str = ''.join(c for c in part if c.isdigit())
                    parts.append(int(num_str) if num_str else 0)
                return parts
            
            new_parts = normalize_version(new_version)
            current_parts = normalize_version(current_version)
            
            # Pad shorter version with zeros
            max_len = max(len(new_parts), len(current_parts))
            new_parts.extend([0] * (max_len - len(new_parts)))
            current_parts.extend([0] * (max_len - len(current_parts)))
            
            return new_parts > current_parts
            
        except Exception:
            # Fallback to string comparison
            return new_version > current_version
    
    def download_update(self, update_info: UpdateInfo) -> Tuple[bool, str]:
        """Download an update for a mod"""
        try:
            if not update_info.download_url:
                return False, "No download URL available"
            
            # Create backup if enabled
            if self.settings["backup_before_update"]:
                self.create_update_backup(update_info.modid)
            
            # Download the update
            response = requests.get(update_info.download_url, timeout=60)
            response.raise_for_status()
            
            # Save to temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.jar', delete=False) as temp_file:
                temp_file.write(response.content)
                temp_path = temp_file.name
            
            # Install the update
            success, message = self.modmanager.installmod(temp_path)
            
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except:
                pass
            
            if success:
                # Update cache to reflect successful update
                update_info.current_version = update_info.latest_version
                update_info.update_status = UpdateStatus.UP_TO_DATE
                self.update_cache[update_info.modid] = update_info
                self.save_update_cache()
                
                return True, "Update installed successfully"
            else:
                return False, f"Failed to install update: {message}"
            
        except Exception as e:
            return False, f"Update download failed: {str(e)}"
    
    def create_update_backup(self, modid: str):
        """Create backup before updating a mod"""
        try:
            if hasattr(self.modmanager, 'installedmods') and modid in self.modmanager.installedmods:
                mod = self.modmanager.installedmods[modid]
                # Create backup using backup manager if available
                if hasattr(self.modmanager, 'backupmanager'):
                    self.modmanager.backupmanager.createbackup(
                        "preupdate", 
                        f"Before updating {mod.name}"
                    )
        except Exception as e:
            logging.error(f"Failed to create update backup: {e}")
    
    def schedule_next_check(self):
        """Schedule the next automatic update check"""
        if not self.settings["auto_check_enabled"]:
            return
        
        # Cancel existing timer
        if self.check_timer:
            self.check_timer.cancel()
        
        # Schedule next check
        interval = self.settings["check_interval_hours"] * 3600  # Convert to seconds
        
        def auto_check():
            logging.info("Running scheduled update check")
            self.check_for_updates()
        
        self.check_timer = threading.Timer(interval, auto_check)
        self.check_timer.daemon = True
        self.check_timer.start()
    
    def get_update_statistics(self) -> Dict[str, Any]:
        """Get update statistics"""
        stats = {
            "total_mods_checked": len(self.update_cache),
            "updates_available": 0,
            "up_to_date": 0,
            "unknown_status": 0,
            "errors": 0,
            "last_check_time": self.last_check_time.isoformat() if self.last_check_time else None,
            "auto_check_enabled": self.settings["auto_check_enabled"],
            "check_interval_hours": self.settings["check_interval_hours"]
        }
        
        # Count by status
        for update_info in self.update_cache.values():
            if update_info.update_status == UpdateStatus.UPDATE_AVAILABLE:
                stats["updates_available"] += 1
            elif update_info.update_status == UpdateStatus.UP_TO_DATE:
                stats["up_to_date"] += 1
            elif update_info.update_status == UpdateStatus.UNKNOWN:
                stats["unknown_status"] += 1
            elif update_info.update_status == UpdateStatus.ERROR:
                stats["errors"] += 1
        
        return stats
    
    def get_available_updates(self) -> List[UpdateInfo]:
        """Get list of mods with available updates"""
        return [
            update_info for update_info in self.update_cache.values()
            if update_info.update_status == UpdateStatus.UPDATE_AVAILABLE
        ]
    
    # Callback methods
    def notify_progress(self, progress: int, message: str):
        """Notify progress callbacks"""
        self.check_progress = progress
        for callback in self.progress_callbacks:
            try:
                callback(progress, message)
            except Exception as e:
                logging.error(f"Error in progress callback: {e}")
    
    def notify_completion(self):
        """Notify completion callbacks"""
        for callback in self.completion_callbacks:
            try:
                callback(self.update_cache)
            except Exception as e:
                logging.error(f"Error in completion callback: {e}")
    
    def notify_update_found(self, update_info: UpdateInfo):
        """Notify when update is found"""
        for callback in self.update_found_callbacks:
            try:
                callback(update_info)
            except Exception as e:
                logging.error(f"Error in update found callback: {e}")
    
    def register_progress_callback(self, callback):
        """Register progress callback"""
        self.progress_callbacks.append(callback)
    
    def register_completion_callback(self, callback):
        """Register completion callback"""
        self.completion_callbacks.append(callback)
    
    def register_update_found_callback(self, callback):
        """Register update found callback"""
        self.update_found_callbacks.append(callback)
