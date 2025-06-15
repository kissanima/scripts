# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(SPEC))

block_cipher = None

a = Analysis(
    ['main.py'],  # Your main script
    pathex=[current_dir],
    binaries=[
        # Add any DLL files if needed
        # ('VirtualDesktopAccessor.dll', '.'),
    ],
    datas=[
        # Include all GUI files
        ('gui', 'gui'),
        # Include themes if you have a separate themes folder
        ('themes.py', '.'),
        ('constants.py', '.'),
        ('config.py', '.'),
        # Include any other Python modules your app uses
        ('*.py', '.'),
        # Include any config files
        ('config.json', '.'),
        # Include any icon files
        # ('icon.ico', '.'),
        # Include any other assets
        # ('assets', 'assets'),
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'psutil',
        'threading',
        'subprocess',
        'pathlib',
        'datetime',
        'json',
        'logging',
        'zipfile',
        'shutil',
        'time',
        'os',
        'sys',
        # Add any other modules that might not be auto-detected
        'gui.tabs.dashboard_tab',
        'gui.tabs.server_control_tab',
        'gui.tabs.console_tab',
        'gui.tabs.backup_tab',
        'gui.tabs.health_tab',
        'gui.tabs.settings_tab',
        'gui.tabs.server_properties_tab',
        'gui.components.header',
        'gui.components.footer',
        'gui.components.status_card',
        'gui.components.modern_widgets',
        'gui.utils.theme_manager',
        'gui.setup_wizard',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'cv2',
        'torch',
        'tensorflow',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MinecraftServerManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress the executable (optional)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True if you want a console window for debugging
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',  # Add your icon file here if you have one
    version='version_info.txt'  # Add version info file if you have one
)
