"""
Backup management for Minecraft Server Manager
"""

import os
import shutil
import time
import threading
import logging
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Callable
from error_handler import ErrorHandler, ErrorSeverity

class BackupManager:
    """Enhanced backup management with scheduling and restoration"""
    
    def __init__(self, process_manager, config):
        self.process_manager = process_manager
        self.config = config
        self.error_handler = ErrorHandler()
        
        # Backup settings
        self.BACKUPS_DIR = Path.cwd() / "backups"
        self.BACKUPS_DIR.mkdir(exist_ok=True)
        
        # Auto backup
        self.auto_backup_active = False
        self.backup_thread = None
        self.backup_callbacks = []
        
        # Statistics
        self.backup_stats = {
            'total_backups': 0,
            'successful_backups': 0,
            'failed_backups': 0,
            'total_size_bytes': 0,
            'last_backup_time': None
        }
        
        self._update_backup_stats()
    
    def start_auto_backup(self):
        """Start automatic backup system"""
        if self.config.get("auto_backup", True) and not self.auto_backup_active:
            self.auto_backup_active = True
            self.backup_thread = threading.Thread(target=self._auto_backup_loop, daemon=True)
            self.backup_thread.start()
            logging.info("Auto-backup system started")
    
    def stop_auto_backup(self):
        """Stop automatic backup system"""
        self.auto_backup_active = False
        if self.backup_thread:
            self.backup_thread.join(timeout=1)
        logging.info("Auto-backup system stopped")
    
    def register_backup_callback(self, callback: Callable):
        """Register a backup event callback"""
        self.backup_callbacks.append(callback)
    
    def _auto_backup_loop(self):
        """Auto backup loop"""
        while self.auto_backup_active:
            try:
                interval = self.config.get("backup_interval", 3600)
                
                # Wait for the interval
                for _ in range(interval):
                    if not self.auto_backup_active:
                        break
                    time.sleep(1)
                
                if self.auto_backup_active:
                    # Perform automatic backup
                    server_jar_path = self.config.get("last_server_jar", "")
                    if server_jar_path and os.path.exists(server_jar_path):
                        server_dir = os.path.dirname(server_jar_path)
                        self.create_backup(server_dir, backup_type='automatic')
                
            except Exception as e:
                self.error_handler.handle_error(e, "auto_backup_loop", ErrorSeverity.MEDIUM)
                time.sleep(60)
    
    def create_backup(self, server_dir: str, backup_type: str = 'manual', description: str = "") -> Dict[str, Any]:
        """Create a backup of the server directory"""
        try:
            # Notify callbacks - backup started
            self._notify_callbacks("backup_started", {"type": backup_type})
            
            # Generate backup name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}_{backup_type}"
            backup_path = self.BACKUPS_DIR / f"{backup_name}.zip"
            
            # Pause server if configured
            server_was_running = False
            if self.config.get("pause_server_for_backup", False) and self.process_manager.is_server_running():
                server_was_running = True
                self.process_manager.send_server_command("save-all")
                time.sleep(2)  # Wait for save to complete
            
            backup_info = {
                'name': backup_name,
                'type': backup_type,
                'description': description,
                'start_time': datetime.now(),
                'server_dir': server_dir,
                'backup_path': str(backup_path),
                'status': 'in_progress'
            }
            
            # Create backup
            total_size = 0
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                server_path = Path(server_dir)
                
                for file_path in server_path.rglob('*'):
                    if file_path.is_file():
                        # Skip certain files
                        if self._should_skip_file(file_path):
                            continue
                        
                        try:
                            arcname = file_path.relative_to(server_path)
                            zipf.write(file_path, arcname)
                            total_size += file_path.stat().st_size
                        except Exception as e:
                            logging.warning(f"Failed to backup file {file_path}: {e}")
            
            # Update backup info
            backup_info.update({
                'end_time': datetime.now(),
                'size_bytes': backup_path.stat().st_size,
                'original_size_bytes': total_size,
                'status': 'completed'
            })
            
            # Resume server if it was paused
            if server_was_running and self.config.get("pause_server_for_backup", False):
                # Server should resume automatically
                pass
            
            # Update statistics
            self.backup_stats['successful_backups'] += 1
            self.backup_stats['total_backups'] += 1
            self.backup_stats['total_size_bytes'] += backup_info['size_bytes']
            self.backup_stats['last_backup_time'] = backup_info['end_time']
            
            # Clean old backups
            self._cleanup_old_backups()
            
            # Notify callbacks - backup completed
            self._notify_callbacks("backup_completed", backup_info)
            
            logging.info(f"Backup created successfully: {backup_name}")
            return backup_info
            
        except Exception as e:
            error_info = self.error_handler.handle_error(e, "create_backup", ErrorSeverity.HIGH)
            
            # Update statistics
            self.backup_stats['failed_backups'] += 1
            self.backup_stats['total_backups'] += 1
            
            # Notify callbacks - backup failed
            self._notify_callbacks("backup_failed", {"error": str(e), "type": backup_type})
            
            raise Exception(f"Backup failed: {error_info['message']}")
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if a file should be skipped during backup"""
        skip_patterns = [
            'logs/',
            'crash-reports/',
            '*.log',
            '*.log.*',
            'server.jar',
            'session.lock',
            'usercache.json'
        ]
        
        file_str = str(file_path)
        for pattern in skip_patterns:
            if pattern in file_str or file_str.endswith(pattern.replace('*', '')):
                return True
        
        return False
    
    def restore_backup(self, backup_name: str) -> Dict[str, Any]:
        """Restore a backup"""
        try:
            backup_path = self.BACKUPS_DIR / f"{backup_name}.zip"
            
            if not backup_path.exists():
                raise FileNotFoundError(f"Backup not found: {backup_name}")
            
            # Stop server if running
            server_was_running = self.process_manager.is_server_running()
            if server_was_running:
                self.process_manager.stop_server()
                time.sleep(3)
            
            # Get server directory
            server_jar_path = self.config.get("last_server_jar", "")
            if not server_jar_path:
                raise ValueError("No server directory configured")
            
            server_dir = Path(os.path.dirname(server_jar_path))
            
            # Create backup of current state before restore
            current_backup = self.create_backup(str(server_dir), 'pre_restore', f"Before restoring {backup_name}")
            
            # Extract backup
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(server_dir)
            
            restore_info = {
                'backup_name': backup_name,
                'restore_time': datetime.now(),
                'server_dir': str(server_dir),
                'pre_restore_backup': current_backup['name'],
                'server_restarted': False
            }
            
            # Restart server if it was running
            if server_was_running:
                time.sleep(2)
                success = self.process_manager.start_server(server_jar_path)
                restore_info['server_restarted'] = success
            
            # Notify callbacks
            self._notify_callbacks("restore_completed", restore_info)
            
            logging.info(f"Backup restored successfully: {backup_name}")
            return restore_info
            
        except Exception as e:
            error_info = self.error_handler.handle_error(e, "restore_backup", ErrorSeverity.HIGH)
            raise Exception(f"Restore failed: {error_info['message']}")
    
    def delete_backup(self, backup_name: str) -> bool:
        """Delete a backup"""
        try:
            backup_path = self.BACKUPS_DIR / f"{backup_name}.zip"
            
            if backup_path.exists():
                size = backup_path.stat().st_size
                backup_path.unlink()
                
                # Update statistics
                self.backup_stats['total_size_bytes'] -= size
                
                logging.info(f"Backup deleted: {backup_name}")
                return True
            else:
                logging.warning(f"Backup not found for deletion: {backup_name}")
                return False
                
        except Exception as e:
            self.error_handler.handle_error(e, "delete_backup", ErrorSeverity.MEDIUM)
            return False
    
    def get_backup_list(self) -> List[Dict[str, Any]]:
        """Get list of available backups"""
        try:
            backups = []
            
            for backup_file in self.BACKUPS_DIR.glob("*.zip"):
                try:
                    stat = backup_file.stat()
                    
                    # Parse backup name
                    name = backup_file.stem
                    parts = name.split('_')
                    
                    backup_type = 'manual'
                    if len(parts) >= 3:
                        backup_type = parts[2]
                    
                    # Parse date
                    date_str = None
                    if len(parts) >= 2:
                        date_str = f"{parts[1][:8]}_{parts[1][8:]}"
                    
                    backup_info = {
                        'name': name,
                        'type': backup_type,
                        'size_bytes': stat.st_size,
                        'created_time': datetime.fromtimestamp(stat.st_ctime),
                        'modified_time': datetime.fromtimestamp(stat.st_mtime),
                        'status': 'completed'
                    }
                    
                    backups.append(backup_info)
                    
                except Exception as e:
                    logging.warning(f"Failed to process backup file {backup_file}: {e}")
            
            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x['created_time'], reverse=True)
            return backups
            
        except Exception as e:
            self.error_handler.handle_error(e, "get_backup_list", ErrorSeverity.LOW)
            return []
    
    def _cleanup_old_backups(self):
        """Clean up old backups based on max count"""
        try:
            max_backups = self.config.get("max_backup_count", 10)
            backups = self.get_backup_list()
            
            if len(backups) > max_backups:
                # Delete oldest backups
                backups_to_delete = backups[max_backups:]
                
                for backup in backups_to_delete:
                    self.delete_backup(backup['name'])
                    logging.info(f"Deleted old backup: {backup['name']}")
                    
        except Exception as e:
            self.error_handler.handle_error(e, "cleanup_old_backups", ErrorSeverity.LOW)
    
    def _update_backup_stats(self):
        """Update backup statistics"""
        try:
            backups = self.get_backup_list()
            
            total_size = sum(backup['size_bytes'] for backup in backups)
            
            self.backup_stats.update({
                'total_backups': len(backups),
                'total_size_bytes': total_size,
                'auto_backup_enabled': self.config.get("auto_backup", True)
            })
            
            if backups:
                self.backup_stats['last_backup_time'] = backups[0]['created_time']
                
        except Exception as e:
            self.error_handler.handle_error(e, "update_backup_stats", ErrorSeverity.LOW)
    
    def get_backup_statistics(self) -> Dict[str, Any]:
        """Get backup statistics"""
        self._update_backup_stats()
        
        stats = self.backup_stats.copy()
        stats['total_size_mb'] = stats['total_size_bytes'] / 1024 / 1024
        
        return stats
    
    def _notify_callbacks(self, event_type: str, data: Dict[str, Any]):
        """Notify backup event callbacks"""
        for callback in self.backup_callbacks:
            try:
                callback(event_type, data)
            except Exception as e:
                self.error_handler.handle_error(e, "backup_callback", ErrorSeverity.LOW)
