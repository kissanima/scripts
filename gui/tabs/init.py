"""
GUI Tabs
"""

from .dashboard_tab import DashboardTab
from .server_control_tab import ServerControlTab
from .console_tab import ConsoleTab
from .backup_tab import BackupTab
from .health_tab import HealthTab
from .settings_tab import SettingsTab
from .server_properties_tab import ServerPropertiesTab
from .mods_tab import ModsTab

__all__ = [
    'DashboardTab', 'ServerControlTab', 'ConsoleTab', 
    'BackupTab', 'HealthTab', 'SettingsTab', 'ServerPropertiesTab', 'ModsTab'
]
