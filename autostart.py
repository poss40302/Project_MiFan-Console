import os
import sys
import ctypes
import winreg

def get_real_executable_path():
    """
    Get the real path of the current executable.
    In Nuitka onefile mode, sys.executable might be tricky.
    Using Windows API to be safe.
    """
    kernel32 = ctypes.windll.kernel32
    buffer = ctypes.create_unicode_buffer(1024)
    kernel32.GetModuleFileNameW(None, buffer, 1024)
    return buffer.value

def set_autostart(app_name, enable=True):
    """
    Set or remove the application from Windows Startup (Registry).
    """
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        if enable:
            exe_path = get_real_executable_path()
            # Wrap in quotes to handle spaces
            value = f'"{exe_path}"'
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, value)
            print(f"Autostart enabled: {value}")
        else:
            try:
                winreg.DeleteValue(key, app_name)
                print("Autostart disabled.")
            except FileNotFoundError:
                pass # Already removed
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"Failed to set autostart: {e}")
        return False

def is_autostart_enabled(app_name):
    """
    Check if the application is currently in Windows Startup.
    """
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
        try:
            winreg.QueryValueEx(key, app_name)
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            winreg.CloseKey(key)
            return False
    except Exception:
        return False
