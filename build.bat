@echo off
echo Building Minecraft Server Manager...
echo.

REM Clean previous builds
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

REM Build the executable
pyinstaller minecraft_server_manager.spec

REM Check if build was successful
if exist "dist\MinecraftServerManager.exe" (
    echo.
    echo ✅ Build successful!
    echo Executable created: dist\MinecraftServerManager.exe
    echo.
    echo Opening dist folder...
    explorer dist
) else (
    echo.
    echo ❌ Build failed!
    echo Check the output above for errors.
    pause
)

pause
