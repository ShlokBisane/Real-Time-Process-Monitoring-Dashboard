"""
Backend logic for startup applications management
"""
import platform
import os
import re


class StartupAppsManager:
    def __init__(self):
        self.platform = platform.system()
        self.autostart_dir = os.path.expanduser("~/.config/autostart/")
        
        # Create autostart directory if it doesn't exist
        if self.platform == "Linux":
            os.makedirs(self.autostart_dir, exist_ok=True)
    
    def list_startup_apps(self):
        """List all startup applications"""
        if self.platform == "Windows":
            return self._list_windows_startup()
        elif self.platform == "Linux":
            return self._list_linux_startup()
        else:
            return []
    
    def _list_windows_startup(self):
        """List Windows startup applications"""
        apps = []
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r"Software\Microsoft\Windows\CurrentVersion\Run", 0,
                                winreg.KEY_READ)
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    apps.append({
                        'name': name,
                        'path': value,
                        'command': value,
                        'status': 'Enabled',
                        'filename': name
                    })
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
        except Exception as e:
            pass
        return apps
    
    def _list_linux_startup(self):
        """List Linux startup applications"""
        apps = []
        seen_names = set()
        
        # Check user autostart directory first (takes precedence)
        if os.path.exists(self.autostart_dir):
            for filename in os.listdir(self.autostart_dir):
                if filename.endswith(".desktop"):
                    filepath = os.path.join(self.autostart_dir, filename)
                    app_info = self._parse_desktop_file(filepath, user_level=True)
                    if app_info:
                        apps.append(app_info)
                        seen_names.add(filename)
        
        # Also check system-wide autostart directory
        system_autostart = "/etc/xdg/autostart/"
        if os.path.exists(system_autostart):
            for filename in os.listdir(system_autostart):
                if filename.endswith(".desktop") and filename not in seen_names:
                    filepath = os.path.join(system_autostart, filename)
                    app_info = self._parse_desktop_file(filepath, user_level=False)
                    if app_info:
                        apps.append(app_info)
        
        return apps
    
    def _parse_desktop_file(self, filepath, user_level=True):
        """Parse a .desktop file and extract information"""
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            name = self._extract_field(content, 'Name')
            exec_cmd = self._extract_field(content, 'Exec')
            hidden = self._extract_field(content, 'Hidden')
            no_display = self._extract_field(content, 'NoDisplay')
            only_show_in = self._extract_field(content, 'OnlyShowIn')
            
            # Determine status
            status = 'Disabled' if hidden == 'true' else 'Enabled'
            
            # Add location indicator
            location = "User" if user_level else "System"
            
            return {
                'name': name or os.path.basename(filepath).replace('.desktop', ''),
                'path': filepath,
                'command': exec_cmd or 'Unknown',
                'status': status,
                'filename': os.path.basename(filepath),
                'location': location,
                'user_level': user_level
            }
        except Exception as e:
            return None
    
    def _extract_field(self, content, field_name):
        """Extract a field value from desktop file content"""
        pattern = rf'^{field_name}=(.+)$'
        match = re.search(pattern, content, re.MULTILINE)
        return match.group(1).strip() if match else None
    
    def enable_app(self, filepath):
        """Enable a startup application"""
        if self.platform != "Linux":
            return False, "Only supported on Linux"
        
        try:
            # If it's a system-level app, we need to copy it to user directory first
            if filepath.startswith('/etc/'):
                filename = os.path.basename(filepath)
                user_filepath = os.path.join(self.autostart_dir, filename)
                
                # Read the system file
                with open(filepath, 'r') as f:
                    content = f.read()
                
                # Write to user directory without Hidden=true
                content = re.sub(r'^Hidden=true\s*$', '', content, flags=re.MULTILINE)
                content = re.sub(r'^X-GNOME-Autostart-enabled=false\s*$', '', content, flags=re.MULTILINE)
                
                with open(user_filepath, 'w') as f:
                    f.write(content)
                
                return True, "Application enabled successfully (copied to user directory)"
            else:
                # It's already a user-level file
                with open(filepath, 'r') as f:
                    content = f.read()
                
                # Remove Hidden=true line if it exists
                content = re.sub(r'^Hidden=true\s*$', '', content, flags=re.MULTILINE)
                content = re.sub(r'^X-GNOME-Autostart-enabled=false\s*$', '', content, flags=re.MULTILINE)
                
                with open(filepath, 'w') as f:
                    f.write(content)
                
                return True, "Application enabled successfully"
        except Exception as e:
            return False, f"Failed to enable: {str(e)}"

    def disable_app(self, filepath):
        """Disable a startup application"""
        if self.platform != "Linux":
            return False, "Only supported on Linux"
        
        try:
            # If it's a system-level app, copy it to user directory with Hidden=true
            if filepath.startswith('/etc/'):
                filename = os.path.basename(filepath)
                user_filepath = os.path.join(self.autostart_dir, filename)
                
                # Read the system file
                with open(filepath, 'r') as f:
                    content = f.read()
                
                # Add Hidden=true after [Desktop Entry]
                if 'Hidden=' not in content:
                    content = content.replace('[Desktop Entry]', '[Desktop Entry]\nHidden=true')
                else:
                    content = re.sub(r'^Hidden=.*$', 'Hidden=true', content, flags=re.MULTILINE)
                
                # Write to user directory
                with open(user_filepath, 'w') as f:
                    f.write(content)
                
                return True, "Application disabled successfully (saved to user directory)"
            else:
                # It's already a user-level file
                with open(filepath, 'r') as f:
                    content = f.read()
                
                # Add Hidden=true if not already present
                if 'Hidden=' not in content:
                    content = content.replace('[Desktop Entry]', '[Desktop Entry]\nHidden=true')
                else:
                    content = re.sub(r'^Hidden=.*$', 'Hidden=true', content, flags=re.MULTILINE)
                
                with open(filepath, 'w') as f:
                    f.write(content)
                
                return True, "Application disabled successfully"
        except Exception as e:
            return False, f"Failed to disable: {str(e)}"
    
    def add_app(self, app_name, app_command):
        """Add a new startup application"""
        if self.platform != "Linux":
            return False, "Only supported on Linux"
        
        try:
            # Sanitize filename
            safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', app_name)
            filename = f"{safe_name}.desktop"
            filepath = os.path.join(self.autostart_dir, filename)
            
            # Check if file already exists
            if os.path.exists(filepath):
                return False, f"Startup entry '{app_name}' already exists"
            
            # Create .desktop file
            desktop_content = f"""[Desktop Entry]
Type=Application
Name={app_name}
Exec={app_command}
Terminal=false
X-GNOME-Autostart-enabled=true
"""
            
            with open(filepath, 'w') as f:
                f.write(desktop_content)
            
            return True, f"Added '{app_name}' to startup applications"
        except Exception as e:
            return False, f"Failed to add application: {str(e)}"
    
    def remove_app(self, filepath):
        """Remove a startup application"""
        if self.platform != "Linux":
            return False, "Only supported on Linux"
        
        try:
            # Can only remove user-level apps
            if filepath.startswith('/etc/'):
                return False, "Cannot remove system-level apps. Disable them instead."
            
            if os.path.exists(filepath):
                os.remove(filepath)
                return True, "Application removed successfully"
            else:
                return False, "Application not found"
        except Exception as e:
            return False, f"Failed to remove: {str(e)}"
