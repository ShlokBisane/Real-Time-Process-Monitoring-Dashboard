"""
Backend logic for process management
"""
from modules.utils.helpers import get_psutil
from collections import defaultdict


class ProcessManager:
    def __init__(self):
        self.psutil = get_psutil()
        self._net_io_counters = {}  # Store previous network I/O for calculating rate
    
    def list_processes(self):
        """Get list of all running processes"""
        if not self.psutil:
            return []
        
        processes = []
        for proc in self.psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'status']):
            try:
                info = proc.info
                
                # Get network usage
                try:
                    net_io = proc.io_counters()
                    pid = info['pid']
                    
                    # Calculate network rate if we have previous data
                    if pid in self._net_io_counters:
                        prev_bytes = self._net_io_counters[pid]
                        bytes_sent = net_io.write_bytes - prev_bytes[0]
                        bytes_recv = net_io.read_bytes - prev_bytes[1]
                        # Convert to KB/s (assuming 1 second interval)
                        net_usage = (bytes_sent + bytes_recv) / 1024
                    else:
                        net_usage = 0
                    
                    # Store current values for next iteration
                    self._net_io_counters[pid] = (net_io.write_bytes, net_io.read_bytes)
                    info['network_kbps'] = net_usage
                except (self.psutil.NoSuchProcess, self.psutil.AccessDenied, AttributeError):
                    info['network_kbps'] = 0
                
                processes.append(info)
            except (self.psutil.NoSuchProcess, self.psutil.AccessDenied):
                pass
        
        # Clean up old entries
        current_pids = {p['pid'] for p in processes}
        self._net_io_counters = {pid: val for pid, val in self._net_io_counters.items() if pid in current_pids}
        
        return processes
    
    def group_processes(self, processes):
        """Group processes by name and aggregate their stats"""
        grouped = defaultdict(list)
        
        for proc in processes:
            name = proc.get('name', 'Unknown')
            grouped[name].append(proc)
        
        result = []
        for name, proc_list in grouped.items():
            # Aggregate stats
            total_cpu = sum(p.get('cpu_percent', 0) for p in proc_list)
            total_mem = sum(p.get('memory_percent', 0) for p in proc_list)
            total_net = sum(p.get('network_kbps', 0) for p in proc_list)
            
            # Get representative info
            first_proc = proc_list[0]
            
            result.append({
                'name': name,
                'count': len(proc_list),
                'processes': proc_list,
                'pid': first_proc.get('pid', 'N/A'),
                'username': first_proc.get('username', 'N/A'),
                'cpu_percent': total_cpu,
                'memory_percent': total_mem,
                'network_kbps': total_net,
                'status': first_proc.get('status', 'N/A')
            })
        
        return result
    
    def search_processes(self, processes, query):
        """Filter processes by search query"""
        if not query:
            return processes
        
        query = query.lower()
        return [p for p in processes if 
                query in p.get('name', '').lower() or
                query in str(p.get('pid', '')).lower() or
                query in p.get('username', '').lower()]
    
    def kill_process(self, pid):
        """Kill a process by PID"""
        if not self.psutil:
            return False, "psutil not available"
        
        try:
            proc = self.psutil.Process(pid)
            proc.kill()
            return True, f"Process {pid} killed successfully"
        except self.psutil.NoSuchProcess:
            return False, f"Process {pid} not found"
        except self.psutil.AccessDenied:
            return False, f"Access denied to kill process {pid}"
        except Exception as e:
            return False, str(e)
    
    def suspend_process(self, pid):
        """Suspend a process by PID"""
        if not self.psutil:
            return False, "psutil not available"
        
        try:
            proc = self.psutil.Process(pid)
            proc.suspend()
            return True, f"Process {pid} suspended successfully"
        except self.psutil.NoSuchProcess:
            return False, f"Process {pid} not found"
        except self.psutil.AccessDenied:
            return False, f"Access denied to suspend process {pid}"
        except Exception as e:
            return False, str(e)
    
    def resume_process(self, pid):
        """Resume a suspended process"""
        if not self.psutil:
            return False, "psutil not available"
        
        try:
            proc = self.psutil.Process(pid)
            proc.resume()
            return True, f"Process {pid} resumed successfully"
        except self.psutil.NoSuchProcess:
            return False, f"Process {pid} not found"
        except self.psutil.AccessDenied:
            return False, f"Access denied to resume process {pid}"
        except Exception as e:
            return False, str(e)
