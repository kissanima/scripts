"""
Constants for Minecraft Server Manager
"""

from pathlib import Path

# Application information
APP_NAME = "Minecraft Server Manager"
VERSION = "2.1.0"

# Directories
APP_DIR = Path.cwd()
LOGS_DIR = APP_DIR / "logs"
BACKUPS_DIR = APP_DIR / "backups"
ERROR_REPORTS_DIR = APP_DIR / "error_reports"

# Log files
LOG_FILE = LOGS_DIR / "server_manager.log"
ERROR_LOG_FILE = LOGS_DIR / "errors.log"
DEBUG_LOG_FILE = LOGS_DIR / "debug.log"

# Configuration
CONFIG_FILE = "config.json"

# Default settings
DEFAULT_JAVA_PATH = "java"
DEFAULT_MAX_MEMORY = "2G"
DEFAULT_MIN_MEMORY = ""
DEFAULT_SERVER_PORT = 25565
DEFAULT_LOG_LEVEL = "INFO"

# UI settings
UI_UPDATE_INTERVAL = 1000  # ms
STATUS_UPDATE_INTERVAL = 2000  # ms

# DLL path for virtual desktop manager
DLL_PATH = "VirtualDesktopAccessor.dll"

# Backup settings
DEFAULT_BACKUP_INTERVAL = 3600  # seconds
MAX_BACKUP_COUNT = 10

# Health monitoring
HEALTH_CHECK_INTERVAL = 30  # seconds
MEMORY_THRESHOLD = 85  # percent
CPU_THRESHOLD = 90  # percent

# Error handling
MAX_ERROR_REPORTS = 50
ERROR_REPORT_RETENTION_DAYS = 30

# Process management
SERVER_START_TIMEOUT = 30  # seconds
SERVER_STOP_TIMEOUT = 30   # seconds

# Network
DEFAULT_RCON_PORT = 25575
DEFAULT_QUERY_PORT = 25565

# Auto-shutdown
DEFAULT_SHUTDOWN_HOUR = 12
DEFAULT_SHUTDOWN_MINUTE = 0
DEFAULT_SHUTDOWN_AMPM = "AM"
DEFAULT_SHUTDOWN_WARNING_MINUTES = 5

# Virtual Desktop
DEFAULT_VIRTUAL_DESKTOP = 1
MAX_VIRTUAL_DESKTOPS = 10

# Console
DEFAULT_CONSOLE_FONT_SIZE = 10
DEFAULT_CONSOLE_MAX_LINES = 1000

# Memory optimization
DEFAULT_MEMORY_CLEANUP_INTERVAL = 300  # seconds
DEFAULT_LOG_ROTATION_SIZE = 10 * 1024 * 1024  # 10MB

# Theme settings
DEFAULT_THEME = "dark"
AVAILABLE_THEMES = ["dark", "light", "blue"]

# File patterns to exclude from backups
BACKUP_EXCLUDE_PATTERNS = [
    "*.log",
    "*.log.*", 
    "logs/",
    "crash-reports/",
    "session.lock",
    "usercache.json"
]

# Supported file types
SUPPORTED_JAR_EXTENSIONS = [".jar"]
SUPPORTED_EXECUTABLE_EXTENSIONS = [".exe"] if Path.cwd().drive else [""]

# URLs and external resources
JAVA_DOWNLOAD_URL = "https://adoptium.net/temurin/releases/"
PLAYIT_DOWNLOAD_URL = "https://playit.gg/download"

# Error categories
ERROR_CATEGORIES = [
    "server_startup",
    "server_shutdown", 
    "file_operation",
    "network_error",
    "configuration_error",
    "system_error",
    "gui_error",
    "backup_error",
    "health_check_error"
]

# Status indicators
SERVER_STATUS_RUNNING = "running"
SERVER_STATUS_STOPPED = "stopped"
SERVER_STATUS_STARTING = "starting"
SERVER_STATUS_STOPPING = "stopping"
SERVER_STATUS_ERROR = "error"

HEALTH_STATUS_EXCELLENT = "excellent"
HEALTH_STATUS_GOOD = "good"
HEALTH_STATUS_WARNING = "warning"
HEALTH_STATUS_CRITICAL = "critical"
HEALTH_STATUS_UNKNOWN = "unknown"

# API endpoints (if needed)
GITHUB_API_URL = "https://api.github.com"
MINECRAFT_VERSION_MANIFEST = "https://launchermeta.mojang.com/mc/game/version_manifest.json"

# Validation limits
MIN_MEMORY_MB = 256
MAX_MEMORY_GB = 32
MIN_PORT = 1024
MAX_PORT = 65535
MIN_BACKUP_INTERVAL = 300  # 5 minutes
MAX_BACKUP_INTERVAL = 86400  # 24 hours
