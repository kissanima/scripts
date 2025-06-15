# 🎮 Minecraft Server Manager

A professional, feature-rich GUI application for managing Minecraft servers with ease. Built with Python and Tkinter, offering a modern interface with comprehensive server management capabilities.

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![Platform](https://img.shields.io/badge/platform-windows%20%7C%20linux%20%7C%20macos-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)

## ✨ Features

### 🧙‍♂️ **Setup Wizard**
- **First-time setup**: Guided server creation for beginners
- **EULA handling**: Automatic Minecraft EULA acceptance
- **Configuration**: Easy server settings configuration
- **World generation**: Automatic world creation

### 🏠 **Dashboard**
- **Real-time monitoring**: Live server status and performance metrics
- **Visual indicators**: Color-coded health status and progress bars
- **Quick actions**: Start/stop/restart server, create backups
- **System overview**: CPU, memory, and disk usage monitoring

### 🎮 **Server Control**
- **File management**: Easy JAR and Playit.gg file selection
- **Auto-start features**: Launch Playit.gg automatically with server
- **Path persistence**: Remembers file selections between sessions
- **Java testing**: Built-in Java installation validation

### 💻 **Live Console**
- **Real-time output**: Live server console with color-coded messages
- **Command interface**: Send commands directly to server
- **Auto-scroll**: Optional auto-scrolling to latest messages
- **Log management**: Clear console and save logs

### 💾 **Smart Backups**
- **World-only backups**: Backs up only essential world folders
- **Server management**: Option to stop server during backup for integrity
- **Auto-restart**: Automatically restarts server after backup
- **Backup browser**: List, restore, and delete existing backups

### ❤️ **Health Monitoring**
- **System metrics**: Real-time CPU, memory, and disk monitoring
- **Server performance**: Server-specific resource tracking
- **Health alerts**: Automatic warnings for high resource usage
- **Recommendations**: Smart optimization suggestions

### 📝 **Properties Manager**
- **Visual editor**: GUI for editing server.properties
- **Categorized settings**: Organized by function (Basic, World, Performance, etc.)
- **Input validation**: Real-time validation with error checking
- **Import/Export**: Backup and restore configurations

### 🌐 **Playit.gg Integration**
- **Global access**: Make local servers accessible worldwide
- **Cracked client support**: Perfect for online-mode=false servers
- **Auto-start**: Launch with server automatically
- **Information tooltips**: Detailed explanations of functionality

### 🎨 **Professional UI**
- **Multiple themes**: Dark, Light, Blue, and more
- **Responsive design**: Scales properly on different screen sizes
- **Modern interface**: Clean, intuitive navigation
- **Professional styling**: Enterprise-grade appearance

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **Java 8+** (for running Minecraft servers)
- **Windows/Linux/macOS**

### Installation

1. **Clone the repository**
git clone https://github.com/yourusername/minecraft-server-manager.git
cd minecraft-server-manager

text

2. **Install dependencies**
pip install -r requirements.txt

text

3. **Run the application**
python main.py

text

### First-Time Setup

1. **Launch the application** - The setup wizard will appear automatically
2. **Select server JAR** - Choose your Minecraft server file
3. **Configure settings** - Set server name, memory, and options
4. **Complete setup** - Let the wizard handle EULA and world generation
5. **Start playing** - Your server is ready to go!

## 📦 Building Executable

Create a standalone .exe file for easy distribution:

Install PyInstaller
pip install pyinstaller

Build executable
pyinstaller minecraft_server_manager.spec

Or use the build script
python build_advanced.py

text

The executable will be created in the `dist/` folder.

## 📋 Requirements

tkinter (included with Python)
psutil>=5.8.0
pathlib (included with Python 3.4+)

text

Optional dependencies:
- **psutil**: For enhanced system monitoring (recommended)
- **PyInstaller**: For building executable files

## 🗂️ Project Structure

minecraft-server-manager/
├── main.py # Application entry point
├── constants.py # Application constants
├── config.py # Configuration management
├── themes.py # Theme definitions
├── process_manager.py # Server process management
├── error_handler.py # Error handling system
├── memory_manager.py # Memory optimization
├── health_monitor.py # Health monitoring
├── backup_manager.py # Backup system
├── server_properties_manager.py # Properties management
├── gui/ # GUI components
│ ├── init.py
│ ├── main_window.py # Main application window
│ ├── dialogs/ # Dialog windows
│ │ ├── init.py
│ │ └── setup_wizard.py # First-time setup wizard
│ ├── tabs/ # Application tabs
│ │ ├── init.py
│ │ ├── dashboard_tab.py # Dashboard overview
│ │ ├── server_control_tab.py # Server controls
│ │ ├── console_tab.py # Live console
│ │ ├── backup_tab.py # Backup management
│ │ ├── health_tab.py # Health monitoring
│ │ ├── settings_tab.py # Application settings
│ │ └── server_properties_tab.py # Properties editor
│ ├── components/ # Reusable UI components
│ │ ├── init.py
│ │ ├── header.py # Application header
│ │ ├── footer.py # Status footer
│ │ ├── status_card.py # Status display cards
│ │ └── modern_widgets.py # Custom widgets
│ └── utils/ # GUI utilities
│ ├── init.py
│ ├── theme_manager.py # Theme management
│ └── ui_helpers.py # UI helper functions
├── build_advanced.py # Build script
├── minecraft_server_manager.spec # PyInstaller spec
├── requirements.txt # Python dependencies
├── README.md # This file
├── .gitignore # Git ignore rules
└── LICENSE # License file

text

## 🎯 Usage Examples

### Starting a Server
1. Go to **Server Control** tab
2. Click **Browse** to select your server JAR
3. Configure any settings needed
4. Click **🚀 Start Server**

### Creating Backups
1. Go to **Backup** tab
2. Enable "Stop server during backup" for safety
3. Enter a backup name
4. Click **💾 Create World Backup**

### Monitoring Performance
1. Go to **Health** tab
2. View real-time system and server metrics
3. Check alerts and recommendations
4. Generate detailed health reports

### Using Playit.gg
1. Download Playit.gg from [playit.gg](https://playit.gg)
2. In **Server Control**, browse for Playit.gg executable
3. Enable "Auto-start Playit.gg when server starts"
4. Your server will be globally accessible!

## 🛠️ Configuration

### Settings File
Configuration is automatically saved to `config.json`:
- Server paths and settings
- Theme preferences
- Memory allocation
- Auto-start options

### Themes
Available themes:
- **Dark** (default)
- **Light**
- **Blue**
- **Custom** (editable)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Adding New Features
- Follow the modular architecture
- Add new tabs to `gui/tabs/`
- Use the theme system for consistency
- Include error handling
- Add documentation

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Common Issues

**Q: "Java not found" error**
A: Install Java 8+ and ensure it's in your system PATH

**Q: Server won't start**
A: Check that your JAR file is valid and EULA is accepted

**Q: Can't see server console output**
A: Make sure "Hide server console" is enabled in settings

**Q: Playit.gg not working**
A: Download the latest version from playit.gg and select the correct executable

### Getting Help
- Check the **Health** tab for system recommendations
- Enable debug logging in **Settings**
- Review console output for error messages
- Submit issues on GitHub with detailed descriptions

## 🏆 Acknowledgments

- **Minecraft** - The amazing game that inspired this project
- **Playit.gg** - For providing free global server access
- **Python Community** - For the excellent libraries and tools
- **Contributors** - Everyone who helped improve this project

## 📊 Statistics

- **Lines of Code**: ~5000+
- **Files**: 25+ Python modules
- **Features**: 50+ distinct features
- **Themes**: 4+ professional themes
- **Platforms**: Windows, Linux, macOS support

---

**Made with ❤️ for the Minecraft community**

*Star ⭐ this repo if you found it helpful!*