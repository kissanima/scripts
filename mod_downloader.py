"""
Mod Downloader for Minecraft Server Manager
Handles downloading mods from various sources with progress tracking
"""
import os
import json
import logging
import threading
import requests
import hashlib
from typing import Dict, List, Optional, Tuple, Any, Callable
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import tempfile
import queue
import time

class DownloadStatus(Enum):
    """Download status types"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class DownloadSource(Enum):
    """Download source types"""
    CURSEFORGE = "curseforge"
    MODRINTH = "modrinth"
    GITHUB = "github"
    DIRECT_URL = "direct_url"
    LOCAL_FILE = "local_file"

@dataclass
class DownloadTask:
    """Download task information"""
    task_id: str
    mod_name: str
    mod_id: str
    download_url: str
    destination_path: str
    source: DownloadSource
    file_size: int = 0
    downloaded_bytes: int = 0
    status: DownloadStatus = DownloadStatus.PENDING
    start_time: datetime = None
    end_time: datetime = None
    error_message: str = ""
    progress_callback: Callable = None
    completion_callback: Callable = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def progress_percentage(self) -> float:
        """Get download progress as percentage"""
        if self.file_size <= 0:
            return 0.0
        return (self.downloaded_bytes / self.file_size) * 100
    
    @property
    def download_speed(self) -> float:
        """Get download speed in bytes per second"""
        if not self.start_time or self.status != DownloadStatus.DOWNLOADING:
            return 0.0
        
        elapsed = (datetime.now() - self.start_time).total_seconds()
        if elapsed <= 0:
            return 0.0
        
        return self.downloaded_bytes / elapsed
    
    @property
    def eta_seconds(self) -> float:
        """Get estimated time to completion in seconds"""
        speed = self.download_speed
        if speed <= 0 or self.file_size <= 0:
            return 0.0
        
        remaining_bytes = self.file_size - self.downloaded_bytes
        return remaining_bytes / speed

class ModDownloader:
    """Advanced mod downloading system with queue management"""
    
    def __init__(self, modmanager, config):
        self.modmanager = modmanager
        self.config = config
        
        # Download management
        self.download_queue = queue.Queue()
        self.active_downloads: Dict[str, DownloadTask] = {}
        self.completed_downloads: Dict[str, DownloadTask] = {}
        self.download_history: List[DownloadTask] = []
        
        # Threading
        self.worker_threads = []
        self.download_lock = threading.Lock()
        self.shutdown_event = threading.Event()
        
        # Paths
        self.download_dir = ""
        self.temp_dir = ""
        
        # Settings
        self.settings = {
            "max_concurrent_downloads": 3,
            "download_timeout": 300,  # 5 minutes
            "retry_attempts": 3,
            "retry_delay": 5,  # seconds
            "chunk_size": 8192,
            "verify_downloads": True,
            "auto_install_after_download": True,
            "cleanup_temp_files": True,
            "download_resume_support": True,
            "bandwidth_limit": 0,  # 0 = unlimited (bytes per second)
            "user_agent": "MinecraftServerManager/1.0"
        }
        
        # API configurations
        self.api_configs = {
            "modrinth": {
                "base_url": "https://api.modrinth.com/v2",
                "rate_limit": 300,  # requests per minute
                "requires_auth": False
            },
            "curseforge": {
                "base_url": "https://api.curseforge.com/v1",
                "rate_limit": 600,  # requests per minute
                "requires_auth": True,
                "api_key": ""  # User needs to provide
            },
            "github": {
                "base_url": "https://api.github.com",
                "rate_limit": 5000,  # requests per hour
                "requires_auth": False
            }
        }
        
        # Statistics
        self.stats = {
            "total_downloads": 0,
            "successful_downloads": 0,
            "failed_downloads": 0,
            "total_bytes_downloaded": 0,
            "average_download_speed": 0.0
        }
        
        # Callbacks
        self.global_progress_callbacks = []
        self.queue_changed_callbacks = []
        self.download_completed_callbacks = []
        
        self.initialize()
    
    def initialize(self):
        """Initialize the downloader"""
        try:
            self.setup_directories()
            self.load_download_history()
            self.start_worker_threads()
            logging.info("ModDownloader initialized")
        except Exception as e:
            logging.error(f"Failed to initialize ModDownloader: {e}")
    
    def setup_directories(self):
        """Set up download directories"""
        if hasattr(self.modmanager, 'moddatadir'):
            self.download_dir = os.path.join(self.modmanager.moddatadir, "downloads")
            self.temp_dir = os.path.join(self.modmanager.moddatadir, "downloads", "temp")
        else:
            self.download_dir = "downloads"
            self.temp_dir = os.path.join("downloads", "temp")
        
        # Create directories
        os.makedirs(self.download_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def load_download_history(self):
        """Load download history from file"""
        try:
            history_file = os.path.join(self.download_dir, "download_history.json")
            
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                
                # Load statistics
                if 'stats' in history_data:
                    self.stats.update(history_data['stats'])
                
                logging.info("Download history loaded")
        
        except Exception as e:
            logging.error(f"Failed to load download history: {e}")
    
    def save_download_history(self):
        """Save download history to file"""
        try:
            history_file = os.path.join(self.download_dir, "download_history.json")
            
            # Prepare recent history (last 100 downloads)
            recent_history = []
            for task in self.download_history[-100:]:
                recent_history.append({
                    'task_id': task.task_id,
                    'mod_name': task.mod_name,
                    'mod_id': task.mod_id,
                    'source': task.source.value,
                    'file_size': task.file_size,
                    'status': task.status.value,
                    'start_time': task.start_time.isoformat() if task.start_time else None,
                    'end_time': task.end_time.isoformat() if task.end_time else None,
                    'error_message': task.error_message
                })
            
            history_data = {
                'stats': self.stats,
                'recent_history': recent_history,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, indent=2, ensure_ascii=False)
            
            logging.info("Download history saved")
        
        except Exception as e:
            logging.error(f"Failed to save download history: {e}")
    
    def start_worker_threads(self):
        """Start download worker threads"""
        for i in range(self.settings["max_concurrent_downloads"]):
            worker = threading.Thread(
                target=self.download_worker,
                name=f"DownloadWorker-{i+1}",
                daemon=True
            )
            worker.start()
            self.worker_threads.append(worker)
        
        logging.info(f"Started {len(self.worker_threads)} download worker threads")
    
    def download_worker(self):
        """Download worker thread function"""
        while not self.shutdown_event.is_set():
            try:
                # Get task from queue (with timeout)
                task = self.download_queue.get(timeout=1.0)
                
                if task is None:  # Shutdown signal
                    break
                
                # Process the download
                self.process_download(task)
                
                # Mark task as done
                self.download_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"Error in download worker: {e}")
    
    def add_download(self, mod_name: str, mod_id: str, download_url: str,
                    source: DownloadSource, metadata: Dict[str, Any] = None,
                    progress_callback: Callable = None,
                    completion_callback: Callable = None) -> str:
        """Add a download to the queue"""
        try:
            # Generate unique task ID
            task_id = f"download_{int(time.time())}_{len(self.active_downloads)}"
            
            # Determine destination path
            filename = self.extract_filename_from_url(download_url, mod_name)
            destination_path = os.path.join(self.download_dir, filename)
            
            # Create download task
            task = DownloadTask(
                task_id=task_id,
                mod_name=mod_name,
                mod_id=mod_id,
                download_url=download_url,
                destination_path=destination_path,
                source=source,
                progress_callback=progress_callback,
                completion_callback=completion_callback,
                metadata=metadata or {}
            )
            
            # Add to active downloads
            with self.download_lock:
                self.active_downloads[task_id] = task
            
            # Add to queue
            self.download_queue.put(task)
            
            # Notify queue changed
            self.notify_queue_changed()
            
            logging.info(f"Added download task: {mod_name} ({task_id})")
            return task_id
            
        except Exception as e:
            logging.error(f"Error adding download: {e}")
            return ""
    
    def process_download(self, task: DownloadTask):
        """Process a single download task"""
        try:
            task.status = DownloadStatus.DOWNLOADING
            task.start_time = datetime.now()
            
            # Get file size
            file_size = self.get_file_size(task.download_url)
            task.file_size = file_size
            
            # Create temporary file
            temp_path = os.path.join(self.temp_dir, f"{task.task_id}.tmp")
            
            # Download with progress tracking
            success = self.download_file_with_progress(task, temp_path)
            
            if success:
                # Verify download if enabled
                if self.settings["verify_downloads"]:
                    if not self.verify_download(task, temp_path):
                        task.status = DownloadStatus.FAILED
                        task.error_message = "Download verification failed"
                        return
                
                # Move to final location
                os.makedirs(os.path.dirname(task.destination_path), exist_ok=True)
                os.rename(temp_path, task.destination_path)
                
                # Mark as completed
                task.status = DownloadStatus.COMPLETED
                task.end_time = datetime.now()
                
                # Update statistics
                self.update_statistics(task)
                
                # Auto-install if enabled
                if self.settings["auto_install_after_download"]:
                    self.auto_install_downloaded_mod(task)
                
                logging.info(f"Download completed: {task.mod_name}")
                
            else:
                task.status = DownloadStatus.FAILED
                if not task.error_message:
                    task.error_message = "Download failed"
            
        except Exception as e:
            task.status = DownloadStatus.FAILED
            task.error_message = f"Download error: {str(e)}"
            logging.error(f"Error processing download {task.task_id}: {e}")
        
        finally:
            # Clean up
            task.end_time = datetime.now()
            
            # Move from active to completed
            with self.download_lock:
                if task.task_id in self.active_downloads:
                    del self.active_downloads[task.task_id]
                self.completed_downloads[task.task_id] = task
                self.download_history.append(task)
            
            # Clean up temp file
            temp_path = os.path.join(self.temp_dir, f"{task.task_id}.tmp")
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            
            # Notify completion
            self.notify_download_completed(task)
            
            # Call task-specific callback
            if task.completion_callback:
                try:
                    task.completion_callback(task)
                except Exception as e:
                    logging.error(f"Error in completion callback: {e}")
    
    def download_file_with_progress(self, task: DownloadTask, temp_path: str) -> bool:
        """Download file with progress tracking"""
        try:
            headers = {
                'User-Agent': self.settings["user_agent"]
            }
            
            # Support for resume downloads
            resume_pos = 0
            if (self.settings["download_resume_support"] and 
                os.path.exists(temp_path)):
                resume_pos = os.path.getsize(temp_path)
                headers['Range'] = f'bytes={resume_pos}-'
            
            response = requests.get(
                task.download_url,
                headers=headers,
                stream=True,
                timeout=self.settings["download_timeout"]
            )
            
            # Handle resume response
            if resume_pos > 0 and response.status_code == 206:
                mode = 'ab'  # Append mode for resume
                task.downloaded_bytes = resume_pos
            elif response.status_code == 200:
                mode = 'wb'  # Write mode for new download
                task.downloaded_bytes = 0
            else:
                response.raise_for_status()
                return False
            
            # Download with progress tracking
            with open(temp_path, mode) as f:
                last_progress_time = time.time()
                
                for chunk in response.iter_content(chunk_size=self.settings["chunk_size"]):
                    if self.shutdown_event.is_set():
                        return False
                    
                    if chunk:
                        f.write(chunk)
                        task.downloaded_bytes += len(chunk)
                        
                        # Throttle bandwidth if limited
                        if self.settings["bandwidth_limit"] > 0:
                            self.throttle_bandwidth(len(chunk))
                        
                        # Update progress (limit frequency to avoid overhead)
                        current_time = time.time()
                        if current_time - last_progress_time >= 0.1:  # Update every 100ms
                            self.notify_progress(task)
                            last_progress_time = current_time
            
            return True
            
        except Exception as e:
            task.error_message = f"Download error: {str(e)}"
            logging.error(f"Download error for {task.task_id}: {e}")
            return False
    
    def get_file_size(self, url: str) -> int:
        """Get file size from URL"""
        try:
            response = requests.head(url, timeout=10)
            return int(response.headers.get('content-length', 0))
        except:
            return 0
    
    def extract_filename_from_url(self, url: str, fallback_name: str) -> str:
        """Extract filename from URL"""
        try:
            # Try to get filename from URL
            from urllib.parse import urlparse, unquote
            parsed = urlparse(url)
            filename = os.path.basename(unquote(parsed.path))
            
            if filename and filename.endswith('.jar'):
                return filename
            
            # Fallback to mod name
            safe_name = "".join(c for c in fallback_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            return f"{safe_name}.jar"
            
        except:
            return f"{fallback_name}.jar"
    
    def verify_download(self, task: DownloadTask, file_path: str) -> bool:
        """Verify downloaded file integrity"""
        try:
            # Check file size
            if task.file_size > 0:
                actual_size = os.path.getsize(file_path)
                if actual_size != task.file_size:
                    logging.warning(f"File size mismatch for {task.task_id}: expected {task.file_size}, got {actual_size}")
                    return False
            
            # Check if it's a valid ZIP/JAR file
            import zipfile
            try:
                with zipfile.ZipFile(file_path, 'r') as zf:
                    # Test the ZIP file
                    bad_file = zf.testzip()
                    if bad_file:
                        logging.warning(f"Corrupted file in download: {bad_file}")
                        return False
            except zipfile.BadZipFile:
                logging.warning(f"Downloaded file is not a valid ZIP/JAR: {file_path}")
                return False
            
            return True
            
        except Exception as e:
            logging.error(f"Error verifying download: {e}")
            return False
    
    def auto_install_downloaded_mod(self, task: DownloadTask):
        """Automatically install downloaded mod"""
        try:
            if hasattr(self.modmanager, 'installmod'):
                success, message = self.modmanager.installmod(task.destination_path)
                if success:
                    logging.info(f"Auto-installed downloaded mod: {task.mod_name}")
                else:
                    logging.warning(f"Failed to auto-install {task.mod_name}: {message}")
        except Exception as e:
            logging.error(f"Error auto-installing mod: {e}")
    
    def throttle_bandwidth(self, bytes_downloaded: int):
        """Throttle bandwidth if limit is set"""
        if self.settings["bandwidth_limit"] <= 0:
            return
        
        # Calculate required delay
        required_time = bytes_downloaded / self.settings["bandwidth_limit"]
        time.sleep(required_time)
    
    def update_statistics(self, task: DownloadTask):
        """Update download statistics"""
        self.stats["total_downloads"] += 1
        
        if task.status == DownloadStatus.COMPLETED:
            self.stats["successful_downloads"] += 1
            self.stats["total_bytes_downloaded"] += task.file_size
            
            # Update average speed
            if task.start_time and task.end_time:
                duration = (task.end_time - task.start_time).total_seconds()
                if duration > 0:
                    speed = task.file_size / duration
                    # Running average
                    current_avg = self.stats["average_download_speed"]
                    successful_count = self.stats["successful_downloads"]
                    self.stats["average_download_speed"] = (
                        (current_avg * (successful_count - 1) + speed) / successful_count
                    )
        else:
            self.stats["failed_downloads"] += 1
        
        # Save updated statistics
        self.save_download_history()
    
    def cancel_download(self, task_id: str) -> bool:
        """Cancel a download"""
        try:
            with self.download_lock:
                if task_id in self.active_downloads:
                    task = self.active_downloads[task_id]
                    task.status = DownloadStatus.CANCELLED
                    task.error_message = "Cancelled by user"
                    return True
            
            return False
            
        except Exception as e:
            logging.error(f"Error cancelling download: {e}")
            return False
    
    def pause_download(self, task_id: str) -> bool:
        """Pause a download (if supported)"""
        # Placeholder - would need more complex implementation
        return False
    
    def resume_download(self, task_id: str) -> bool:
        """Resume a paused download"""
        # Placeholder - would need more complex implementation
        return False
    
    def retry_download(self, task_id: str) -> bool:
        """Retry a failed download"""
        try:
            with self.download_lock:
                if task_id in self.completed_downloads:
                    old_task = self.completed_downloads[task_id]
                    
                    if old_task.status == DownloadStatus.FAILED:
                        # Create new task based on old one
                        new_task_id = self.add_download(
                            old_task.mod_name,
                            old_task.mod_id,
                            old_task.download_url,
                            old_task.source,
                            old_task.metadata,
                            old_task.progress_callback,
                            old_task.completion_callback
                        )
                        return bool(new_task_id)
            
            return False
            
        except Exception as e:
            logging.error(f"Error retrying download: {e}")
            return False
    
    def get_active_downloads(self) -> List[DownloadTask]:
        """Get list of active downloads"""
        with self.download_lock:
            return list(self.active_downloads.values())
    
    def get_completed_downloads(self) -> List[DownloadTask]:
        """Get list of completed downloads"""
        with self.download_lock:
            return list(self.completed_downloads.values())
    
    def get_download_statistics(self) -> Dict[str, Any]:
        """Get download statistics"""
        active_count = len(self.active_downloads)
        queue_size = self.download_queue.qsize()
        
        stats = self.stats.copy()
        stats.update({
            "active_downloads": active_count,
            "queued_downloads": queue_size,
            "total_bytes_downloaded_mb": round(self.stats["total_bytes_downloaded"] / 1024 / 1024, 2),
            "average_download_speed_mbps": round(self.stats["average_download_speed"] / 1024 / 1024, 2)
        })
        
        return stats
    
    def cleanup_old_downloads(self, days: int = 30):
        """Clean up old downloaded files"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            removed_count = 0
            
            for filename in os.listdir(self.download_dir):
                filepath = os.path.join(self.download_dir, filename)
                
                if os.path.isfile(filepath) and filepath.endswith('.jar'):
                    file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                    
                    if file_time < cutoff_date:
                        os.remove(filepath)
                        removed_count += 1
                        logging.info(f"Removed old download: {filename}")
            
            logging.info(f"Cleaned up {removed_count} old downloads")
            
        except Exception as e:
            logging.error(f"Error cleaning up old downloads: {e}")
    
    def shutdown(self):
        """Shutdown the downloader"""
        try:
            logging.info("Shutting down mod downloader...")
            
            # Signal shutdown
            self.shutdown_event.set()
            
            # Add shutdown signals to queue for each worker
            for _ in self.worker_threads:
                self.download_queue.put(None)
            
            # Wait for workers to finish
            for worker in self.worker_threads:
                worker.join(timeout=5.0)
            
            # Save final state
            self.save_download_history()
            
            logging.info("Mod downloader shutdown complete")
            
        except Exception as e:
            logging.error(f"Error during downloader shutdown: {e}")
    
    # Callback methods
    def notify_progress(self, task: DownloadTask):
        """Notify progress callbacks"""
        if task.progress_callback:
            try:
                task.progress_callback(task)
            except Exception as e:
                logging.error(f"Error in progress callback: {e}")
        
        for callback in self.global_progress_callbacks:
            try:
                callback(task)
            except Exception as e:
                logging.error(f"Error in global progress callback: {e}")
    
    def notify_queue_changed(self):
        """Notify queue changed callbacks"""
        for callback in self.queue_changed_callbacks:
            try:
                callback()
            except Exception as e:
                logging.error(f"Error in queue changed callback: {e}")
    
    def notify_download_completed(self, task: DownloadTask):
        """Notify download completed callbacks"""
        for callback in self.download_completed_callbacks:
            try:
                callback(task)
            except Exception as e:
                logging.error(f"Error in download completed callback: {e}")
    
    def register_global_progress_callback(self, callback):
        """Register global progress callback"""
        self.global_progress_callbacks.append(callback)
    
    def register_queue_changed_callback(self, callback):
        """Register queue changed callback"""
        self.queue_changed_callbacks.append(callback)
    
    def register_download_completed_callback(self, callback):
        """Register download completed callback"""
        self.download_completed_callbacks.append(callback)
