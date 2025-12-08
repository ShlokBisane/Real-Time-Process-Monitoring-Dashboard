import psutil
import os
import subprocess
import re
import time


class PerformanceMonitor:
    def __init__(self):
        # 60 data points for each graph (1 minute history)
        self.history_length = 60

        self.cpu_history = [0] * self.history_length
        self.mem_history = [0] * self.history_length
        self.disk_history = [0] * self.history_length
        self.gpu_history = [0] * self.history_length      # GPU usage %
        self.gpu_mem_history = [0] * self.history_length  # GPU Memory %
        self.network_send_history = [0] * self.history_length  # Network upload (MB/s)
        self.network_recv_history = [0] * self.history_length  # Network download (MB/s)
        
        # For calculating network rate
        self._last_net_io = None
        self._last_net_time = None
        
        # Detect GPU type
        self.gpu_type = self._detect_gpu()
        self.gpu_available = self.gpu_type != "none"

    def _detect_gpu(self):
        """Detect GPU type (nvidia, intel, amd, or none)"""
        try:
            # Check for NVIDIA
            result = subprocess.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'],
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0 and result.stdout.strip():
                return "nvidia"
        except:
            pass
        
        try:
            # Check for Intel
            with open('/proc/cpuinfo', 'r') as f:
                if 'Intel' in f.read():
                    # Check if integrated graphics exists
                    if os.path.exists('/sys/class/drm/card0') or os.path.exists('/sys/class/drm/card1'):
                        return "intel"
        except:
            pass
        
        try:
            # Check for AMD
            result = subprocess.run(['rocm-smi', '--showuse'], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                return "amd"
        except:
            pass
        
        return "none"

    def _get_nvidia_stats(self):
        """Get NVIDIA GPU stats using nvidia-smi"""
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=utilization.gpu,utilization.memory', 
                 '--format=csv,noheader,nounits'],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split(',')
                gpu_util = float(parts[0].strip())
                gpu_mem = float(parts[1].strip())
                return gpu_util, gpu_mem
        except:
            pass
        return None, None

    def _get_intel_stats(self):
        """Get Intel GPU stats (estimation based on system load)"""
        try:
            # Intel integrated GPUs don't have easy monitoring
            # We'll estimate based on graphics processes
            gpu_processes = 0
            total_cpu = 0
            
            for proc in psutil.process_iter(['name', 'cpu_percent']):
                try:
                    name = proc.info['name'].lower()
                    # Look for graphics-intensive processes
                    if any(x in name for x in ['chrome', 'firefox', 'vlc', 'mpv', 'xorg', 
                                                'gnome-shell', 'compositor', 'steam', 'game']):
                        cpu = proc.info['cpu_percent']
                        if cpu > 0:
                            gpu_processes += 1
                            total_cpu += cpu
                except:
                    pass
            
            # Estimate GPU usage (scaled)
            gpu_util = min(total_cpu / 2, 100)  # Rough estimation
            
            # Get GPU memory from DRM if available
            gpu_mem = self._get_drm_memory_usage()
            
            return gpu_util, gpu_mem
        except:
            return 0, 0

    def _get_drm_memory_usage(self):
        """Try to get GPU memory usage from DRM"""
        try:
            # Try different card paths
            for card in ['card0', 'card1']:
                mem_path = f'/sys/class/drm/{card}/device/mem_info_vram_used'
                mem_total_path = f'/sys/class/drm/{card}/device/mem_info_vram_total'
                
                if os.path.exists(mem_path) and os.path.exists(mem_total_path):
                    with open(mem_path, 'r') as f:
                        used = int(f.read().strip())
                    with open(mem_total_path, 'r') as f:
                        total = int(f.read().strip())
                    if total > 0:
                        return (used / total) * 100
        except:
            pass
        
        # Fallback: estimate based on system memory used by graphics
        try:
            graphics_mem = 0
            for proc in psutil.process_iter(['name', 'memory_percent']):
                try:
                    name = proc.info['name'].lower()
                    if any(x in name for x in ['xorg', 'gnome-shell', 'compositor']):
                        graphics_mem += proc.info['memory_percent']
                except:
                    pass
            return min(graphics_mem * 2, 100)  # Rough estimation
        except:
            return 0

    def _get_gpu_stats(self):
        """Get GPU statistics based on detected GPU type"""
        if self.gpu_type == "nvidia":
            return self._get_nvidia_stats()
        elif self.gpu_type == "intel":
            return self._get_intel_stats()
        else:
            # No GPU or unsupported, return zeros
            return 0, 0

    def _get_network_speed(self):
        """Get current network upload and download speeds separately in MB/s"""
        try:
            current_io = psutil.net_io_counters()
            current_time = time.time()
            
            if self._last_net_io is None:
                # First call, just store values
                self._last_net_io = current_io
                self._last_net_time = current_time
                return 0, 0
            
            # Calculate time difference
            time_delta = current_time - self._last_net_time
            if time_delta == 0:
                return 0, 0
            
            # Calculate bytes difference
            bytes_sent = current_io.bytes_sent - self._last_net_io.bytes_sent
            bytes_recv = current_io.bytes_recv - self._last_net_io.bytes_recv
            
            # Bytes per second, convert to MB/s
            send_mb_per_sec = (bytes_sent / time_delta) / (1024 * 1024)
            recv_mb_per_sec = (bytes_recv / time_delta) / (1024 * 1024)
            
            # Store current values for next calculation
            self._last_net_io = current_io
            self._last_net_time = current_time
            
            return round(send_mb_per_sec, 3), round(recv_mb_per_sec, 3)
        except Exception as e:
            print(f"Network speed error: {e}")
            return 0, 0

    # Maintains rolling window
    def _push(self, arr, value):
        arr.append(value)
        if len(arr) > self.history_length:
            arr.pop(0)
        return arr

    def get_all_data(self):
        # REAL system values
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent

        # Disk usage % (simplified)
        disk = psutil.disk_usage('/').percent

        # GPU stats (real if available, zeros if not)
        gpu, gpu_mem = self._get_gpu_stats()

        # Network speed (separate upload and download in MB/s)
        network_send, network_recv = self._get_network_speed()

        # Update histories
        self._push(self.cpu_history, cpu)
        self._push(self.mem_history, mem)
        self._push(self.disk_history, disk)
        self._push(self.gpu_history, gpu)
        self._push(self.gpu_mem_history, gpu_mem)
        self._push(self.network_send_history, network_send)
        self._push(self.network_recv_history, network_recv)

        # Return dictionary EXACTLY as UI expects
        return {
            "cpu": self.cpu_history,
            "memory": self.mem_history,
            "disk": self.disk_history,
            "gpu": self.gpu_history,
            "gpu_memory": self.gpu_mem_history,
            "network_send": self.network_send_history,
            "network_recv": self.network_recv_history,
        }
