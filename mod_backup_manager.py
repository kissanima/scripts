"""
Mod Backup Manager for Minecraft Server Manager
Handles creation, restoration, and management of mod backups
"""
import os
import json
import shutil
import zipfile
import logging
import threading
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict

@dataclass
class BackupInfo:
    """Backup information structure"""
    name: str
    description: str
    backuptype: str  # 'manual', 'auto', 'preinstall', 'preremove'
    timestamp: datetime
    filepath: str
    filesize: int
    modcount: int
    enabledmods: int
    profilename: str
    compressiontype: str  # 'zip', 'tar', 'copy'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BackupInfo':
        """Create from dictionary"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

class ModBackupManager:
    """Comprehensive mod backup management system"""
    
    def __init__(self, modmanager, config):
        self.modmanager = modmanager
        self.config = config
        
        # Paths
        self.backupsdir = ""
        self.backupindexfile = ""
        
        # Backup index
        self.backupindex: Dict[str, BackupInfo] = {}
        
        # Settings
        self.settings = {
            "autobackupinterval": 24,  # hours
            "maxbackups": 10,
            "compressionlevel": 6,
            "compressiontype": "zip",  # zip, tar, copy
            "includeconfigs": True,
            "includeworldgen": False,
            "excludepatterns": ["*.log", "*.tmp", "cache/*"],
            "enableautocleanup": True,
            "backupbeforechanges": True
        }
        
        # State
        self.isbackingup = False
        self.isrestoring = False
        self.backupprogress = 0
        self.lastbackuptime = None
        
        # Callbacks
        self.progresscallbacks = []
        self.completioncallbacks = []
        
        self.initialize()
    
    def initialize(self):
        """Initialize backup manager"""
        try:
            self.updatepaths()
            self.loadbackupindex()
            self.schedulenextautobackup()
            logging.info("ModBackupManager initialized")
        except Exception as e:
            logging.error(f"Failed to initialize ModBackupManager: {e}")
    
    def updatepaths(self):
        """Update paths based on current server directory"""
        if hasattr(self.modmanager, 'moddatadir') and self.modmanager.moddatadir:
            self.backupsdir = os.path.join(self.modmanager.moddatadir, "backups")
            self.backupindexfile = os.path.join(self.backupsdir, "backupindex.json")
            os.makedirs(self.backupsdir, exist_ok=True)
    
    def loadbackupindex(self):
        """Load backup index from file"""
        try:
            if os.path.exists(self.backupindexfile):
                with open(self.backupindexfile, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.backupindex = {}
                for name, backupdata in data.items():
                    try:
                        self.backupindex[name] = BackupInfo.from_dict(backupdata)
                    except Exception as e:
                        logging.error(f"Error loading backup info for {name}: {e}")
                
                # Verify backup files exist
                self.verifybackups()
                
                logging.info(f"Loaded {len(self.backupindex)} backup entries")
        except Exception as e:
            logging.error(f"Failed to load backup index: {e}")
            self.backupindex = {}
    
    def savebackupindex(self):
        """Save backup index to file"""
        try:
            data = {}
            for name, backupinfo in self.backupindex.items():
                data[name] = backupinfo.to_dict()
            
            with open(self.backupindexfile, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logging.info("Backup index saved")
        except Exception as e:
            logging.error(f"Failed to save backup index: {e}")
    
    def verifybackups(self):
        """Verify that backup files exist and remove orphaned entries"""
        toremove = []
        for name, backupinfo in self.backupindex.items():
            if not os.path.exists(backupinfo.filepath):
                toremove.append(name)
                logging.warning(f"Backup file missing: {backupinfo.filepath}")
        
        for name in toremove:
            del self.backupindex[name]
        
        if toremove:
            self.savebackupindex()
    
    def createbackup(self, backuptype: str = "manual", description: str = "", 
                    profilename: str = None) -> Tuple[bool, str]:
        """Create a new backup"""
        if self.isbackingup:
            return False, "Backup already in progress"
        
        try:
            self.isbackingup = True
            self.backupprogress = 0
            
            # Generate backup name
            timestamp = datetime.now()
            backupname = f"backup_{backuptype}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
            
            # Create backup directory
            backupdir = os.path.join(self.backupsdir, backupname)
            os.makedirs(backupdir, exist_ok=True)
            
            self.notifyprogress(10, "Preparing backup...")
            
            # Gather files to backup
            filestobackup = self.gatherbackupfiles()
            totalfiles = len(filestobackup)
            
            if totalfiles == 0:
                return False, "No files to backup"
            
            self.notifyprogress(20, "Copying files...")
            
            # Copy files
            copiedfiles = 0
            for sourcefile, relativepath in filestobackup:
                try:
                    targetfile = os.path.join(backupdir, relativepath)
                    targetdir = os.path.dirname(targetfile)
                    os.makedirs(targetdir, exist_ok=True)
                    
                    shutil.copy2(sourcefile, targetfile)
                    copiedfiles += 1
                    
                    # Update progress
                    progress = 20 + (copiedfiles / totalfiles) * 60
                    self.notifyprogress(progress, f"Copied {copiedfiles}/{totalfiles} files")
                    
                except Exception as e:
                    logging.error(f"Error copying {sourcefile}: {e}")
            
            self.notifyprogress(80, "Creating backup metadata...")
            
            # Create backup metadata
            backupmetadata = {
                "name": backupname,
                "description": description,
                "type": backuptype,
                "timestamp": timestamp.isoformat(),
                "modcount": len(self.modmanager.installedmods),
                "enabledmods": len([m for m in self.modmanager.installedmods.values() if m.isenabled]),
                "profilename": profilename or self.modmanager.currentprofile,
                "modlist": list(self.modmanager.installedmods.keys()),
                "settings": dict(self.modmanager.settings)
            }
            
            metadatafile = os.path.join(backupdir, "backup_metadata.json")
            with open(metadatafile, 'w', encoding='utf-8') as f:
                json.dump(backupmetadata, f, indent=2, ensure_ascii=False)
            
            # Compress if enabled
            finalpath = backupdir
            compressiontype = "copy"
            
            if self.settings["compressiontype"] == "zip":
                self.notifyprogress(85, "Compressing backup...")
                zippath = backupdir + ".zip"
                
                with zipfile.ZipFile(zippath, 'w', zipfile.ZIP_DEFLATED, 
                                   compresslevel=self.settings["compressionlevel"]) as zf:
                    for root, dirs, files in os.walk(backupdir):
                        for file in files:
                            filepath = os.path.join(root, file)
                            arcname = os.path.relpath(filepath, backupdir)
                            zf.write(filepath, arcname)
                
                # Remove uncompressed directory
                shutil.rmtree(backupdir)
                finalpath = zippath
                compressiontype = "zip"
            
            self.notifyprogress(90, "Updating backup index...")
            
            # Calculate backup size
            if os.path.isfile(finalpath):
                backupsize = os.path.getsize(finalpath)
            else:
                backupsize = self.getdirectorysize(finalpath)
            
            # Create backup info
            backupinfo = BackupInfo(
                name=backupname,
                description=description,
                backuptype=backuptype,
                timestamp=timestamp,
                filepath=finalpath,
                filesize=backupsize,
                modcount=len(self.modmanager.installedmods),
                enabledmods=len([m for m in self.modmanager.installedmods.values() if m.isenabled]),
                profilename=profilename or self.modmanager.currentprofile,
                compressiontype=compressiontype
            )
            
            # Add to index
            self.backupindex[backupname] = backupinfo
            self.savebackupindex()
            
            # Clean up old backups
            self.cleanupoldbackups()
            
            self.lastbackuptime = timestamp
            self.notifyprogress(100, "Backup completed successfully")
            
            # Notify completion
            for callback in self.completioncallbacks:
                callback("backup_created", backupinfo, "Backup created successfully")
            
            logging.info(f"Backup created: {backupname}")
            return True, backupname
            
        except Exception as e:
            logging.error(f"Error creating backup: {e}")
            return False, f"Backup failed: {str(e)}"
        finally:
            self.isbackingup = False
            self.backupprogress = 0
    
    def gatherbackupfiles(self) -> List[Tuple[str, str]]:
        """Gather files that should be included in backup"""
        filestobackup = []
        
        # Mods directory
        if os.path.exists(self.modmanager.modsdir):
            for root, dirs, files in os.walk(self.modmanager.modsdir):
                for file in files:
                    if not self.shouldexcludefile(file):
                        filepath = os.path.join(root, file)
                        relativepath = os.path.relpath(filepath, self.modmanager.serverdir)
                        filestobackup.append((filepath, relativepath))
        
        # Config directory (if enabled)
        if self.settings["includeconfigs"] and os.path.exists(self.modmanager.configdir):
            for root, dirs, files in os.walk(self.modmanager.configdir):
                for file in files:
                    if not self.shouldexcludefile(file):
                        filepath = os.path.join(root, file)
                        relativepath = os.path.relpath(filepath, self.modmanager.serverdir)
                        filestobackup.append((filepath, relativepath))
        
        # Mod manager data
        if os.path.exists(self.modmanager.moddatadir):
            for file in ["modsdatabase.json", "modprofiles.json", "modsettings.json"]:
                filepath = os.path.join(self.modmanager.moddatadir, file)
                if os.path.exists(filepath):
                    relativepath = os.path.relpath(filepath, self.modmanager.serverdir)
                    filestobackup.append((filepath, relativepath))
        
        return filestobackup
    
    def shouldexcludefile(self, filename: str) -> bool:
        """Check if file should be excluded from backup"""
        import fnmatch
        
        for pattern in self.settings["excludepatterns"]:
            if fnmatch.fnmatch(filename.lower(), pattern.lower()):
                return True
        
        return False
    
    def restorebackup(self, backupname: str, restoreoptions: Dict[str, bool] = None) -> Tuple[bool, str]:
        """Restore from backup"""
        if self.isrestoring:
            return False, "Restore already in progress"
        
        if backupname not in self.backupindex:
            return False, "Backup not found"
        
        try:
            self.isrestoring = True
            self.backupprogress = 0
            
            backupinfo = self.backupindex[backupname]
            
            if not os.path.exists(backupinfo.filepath):
                return False, "Backup file not found"
            
            # Default restore options
            if restoreoptions is None:
                restoreoptions = {
                    "restoremods": True,
                    "restoreconfigs": True,
                    "restoreprofiles": True,
                    "createbackupbeforerestore": True
                }
            
            self.notifyprogress(10, "Preparing restore...")
            
            # Create backup before restore if enabled
            if restoreoptions.get("createbackupbeforerestore", True):
                self.notifyprogress(15, "Creating pre-restore backup...")
                success, message = self.createbackup("prerestore", f"Before restoring {backupname}")
                if not success:
                    logging.warning(f"Pre-restore backup failed: {message}")
            
            # Extract backup
            tempdir = os.path.join(self.backupsdir, "temp_restore")
            if os.path.exists(tempdir):
                shutil.rmtree(tempdir)
            os.makedirs(tempdir, exist_ok=True)
            
            self.notifyprogress(25, "Extracting backup...")
            
            if backupinfo.compressiontype == "zip":
                with zipfile.ZipFile(backupinfo.filepath, 'r') as zf:
                    zf.extractall(tempdir)
            else:
                # Copy directory
                if os.path.isdir(backupinfo.filepath):
                    for item in os.listdir(backupinfo.filepath):
                        source = os.path.join(backupinfo.filepath, item)
                        dest = os.path.join(tempdir, item)
                        if os.path.isdir(source):
                            shutil.copytree(source, dest)
                        else:
                            shutil.copy2(source, dest)
            
            self.notifyprogress(40, "Restoring files...")
            
            # Restore mods
            if restoreoptions.get("restoremods", True):
                modsbackupdir = os.path.join(tempdir, "mods")
                if os.path.exists(modsbackupdir):
                    if os.path.exists(self.modmanager.modsdir):
                        shutil.rmtree(self.modmanager.modsdir)
                    shutil.copytree(modsbackupdir, self.modmanager.modsdir)
                    self.notifyprogress(60, "Mods restored")
            
            # Restore configs
            if restoreoptions.get("restoreconfigs", True):
                configbackupdir = os.path.join(tempdir, "config")
                if os.path.exists(configbackupdir):
                    if os.path.exists(self.modmanager.configdir):
                        shutil.rmtree(self.modmanager.configdir)
                    shutil.copytree(configbackupdir, self.modmanager.configdir)
                    self.notifyprogress(80, "Configs restored")
            
            # Restore mod manager data
            if restoreoptions.get("restoreprofiles", True):
                databackupdir = os.path.join(tempdir, "modmanagerdata")
                if os.path.exists(databackupdir):
                    for file in ["modsdatabase.json", "modprofiles.json", "modsettings.json"]:
                        sourcefile = os.path.join(databackupdir, file)
                        if os.path.exists(sourcefile):
                            targetfile = os.path.join(self.modmanager.moddatadir, file)
                            shutil.copy2(sourcefile, targetfile)
                    self.notifyprogress(90, "Profiles restored")
            
            # Reload mod manager data
            self.notifyprogress(95, "Reloading mod data...")
            self.modmanager.loaddatabase()
            self.modmanager.loadprofiles()
            self.modmanager.loadsettings()
            
            # Cleanup temp directory
            shutil.rmtree(tempdir, ignore_errors=True)
            
            self.notifyprogress(100, "Restore completed successfully")
            
            # Notify completion
            for callback in self.completioncallbacks:
                callback("backup_restored", backupinfo, "Backup restored successfully")
            
            logging.info(f"Backup restored: {backupname}")
            return True, "Backup restored successfully"
            
        except Exception as e:
            logging.error(f"Error restoring backup: {e}")
            return False, f"Restore failed: {str(e)}"
        finally:
            self.isrestoring = False
            self.backupprogress = 0
    
    def deletebackup(self, backupname: str) -> Tuple[bool, str]:
        """Delete a backup"""
        try:
            if backupname not in self.backupindex:
                return False, "Backup not found"
            
            backupinfo = self.backupindex[backupname]
            
            # Remove backup file/directory
            if os.path.exists(backupinfo.filepath):
                if os.path.isfile(backupinfo.filepath):
                    os.remove(backupinfo.filepath)
                else:
                    shutil.rmtree(backupinfo.filepath)
            
            # Remove from index
            del self.backupindex[backupname]
            self.savebackupindex()
            
            logging.info(f"Backup deleted: {backupname}")
            return True, "Backup deleted successfully"
            
        except Exception as e:
            logging.error(f"Error deleting backup: {e}")
            return False, f"Delete failed: {str(e)}"
    
    def cleanupoldbackups(self):
        """Clean up old backups based on settings"""
        try:
            if not self.settings["enableautocleanup"]:
                return
            
            maxbackups = self.settings["maxbackups"]
            if len(self.backupindex) <= maxbackups:
                return
            
            # Sort backups by timestamp (oldest first)
            sortedbackups = sorted(
                self.backupindex.items(),
                key=lambda x: x[1].timestamp
            )
            
            # Remove oldest backups
            toremove = len(sortedbackups) - maxbackups
            for i in range(toremove):
                backupname, backupinfo = sortedbackups[i]
                if backupinfo.backuptype != "manual":  # Keep manual backups
                    self.deletebackup(backupname)
                    logging.info(f"Auto-cleaned backup: {backupname}")
            
        except Exception as e:
            logging.error(f"Error cleaning up backups: {e}")
    
    def getdirectorysize(self, dirpath: str) -> int:
        """Calculate total size of directory"""
        totalsize = 0
        try:
            for root, dirs, files in os.walk(dirpath):
                for file in files:
                    filepath = os.path.join(root, file)
                    if os.path.exists(filepath):
                        totalsize += os.path.getsize(filepath)
        except Exception as e:
            logging.error(f"Error calculating directory size: {e}")
        return totalsize
    
    def schedulenextautobackup(self):
        """Schedule next automatic backup"""
        if self.settings["autobackupinterval"] > 0:
            interval = self.settings["autobackupinterval"] * 3600  # Convert hours to seconds
            
            def autobackup():
                logging.info("Running scheduled auto backup")
                self.createbackup("auto", "Scheduled automatic backup")
                self.schedulenextautobackup()  # Schedule next one
            
            timer = threading.Timer(interval, autobackup)
            timer.daemon = True
            timer.start()
    
    def notifyprogress(self, progress: int, message: str):
        """Notify progress callbacks"""
        self.backupprogress = progress
        for callback in self.progresscallbacks:
            callback(progress, message)
    
    def registerprogresscallback(self, callback):
        """Register progress callback"""
        self.progresscallbacks.append(callback)
    
    def registercompletioncallback(self, callback):
        """Register completion callback"""
        self.completioncallbacks.append(callback)
    
    def getbackuplist(self) -> List[BackupInfo]:
        """Get list of all backups sorted by timestamp"""
        return sorted(self.backupindex.values(), key=lambda x: x.timestamp, reverse=True)
    
    def getbackupstatistics(self) -> Dict[str, Any]:
        """Get backup statistics"""
        backups = list(self.backupindex.values())
        
        if not backups:
            return {
                "totalbackups": 0,
                "totalsize": 0,
                "lastbackup": None,
                "oldestbackup": None,
                "typebreakdown": {}
            }
        
        totalsize = sum(backup.filesize for backup in backups)
        lastbackup = max(backups, key=lambda x: x.timestamp)
        oldestbackup = min(backups, key=lambda x: x.timestamp)
        
        # Type breakdown
        typebreakdown = {}
        for backup in backups:
            typebreakdown[backup.backuptype] = typebreakdown.get(backup.backuptype, 0) + 1
        
        return {
            "totalbackups": len(backups),
            "totalsizemb": round(totalsize / 1024 / 1024, 2),
            "lastbackup": lastbackup.timestamp.isoformat(),
            "oldestbackup": oldestbackup.timestamp.isoformat(),
            "typebreakdown": typebreakdown,
            "averagesizemb": round((totalsize / len(backups)) / 1024 / 1024, 2) if backups else 0
        }
