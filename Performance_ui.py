"""
UI for performance monitoring
"""
import tkinter as tk
from modules.performance.Performance_backend import PerformanceMonitor
from modules.utils.helpers import check_matplotlib, check_psutil


class PerformanceUI:
    def __init__(self, parent, monitor=None):
        self.parent = parent
        self.monitor = monitor if monitor else PerformanceMonitor()
        self.update_running = False
        self.update_job = None
        self.selected_tab = 'cpu'
        
        # Initialize history lists for all metrics
        self.cpu_history = []
        self.memory_history = []
        self.disk_history = []
        self.gpu_history = []
        self.network_sent_history = []
        self.network_recv_history = []
        
        # Check dependencies
        if not check_matplotlib():
            tk.Label(parent, text="Install matplotlib for graphs: pip install matplotlib",
                    font=("Arial", 12), fg="red").pack(pady=20)
            return
        
        if not check_psutil():
            tk.Label(parent, text="Install psutil: pip install psutil",
                    font=("Arial", 12), fg="red").pack(pady=20)
            return
        
        self._setup_matplotlib()
        self.setup_ui()
        self.start_updates()
    
    def _setup_matplotlib(self):
        """Setup matplotlib imports"""
        import matplotlib
        matplotlib.use('TkAgg')
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        self.Figure = Figure
        self.FigureCanvasTkAgg = FigureCanvasTkAgg
    
    def setup_ui(self):
        tk.Label(self.parent, text="Performance", font=("Arial", 16, "bold"),
                bg="white").pack(pady=10)

        # --- Top Nav Bar ---
        nav_frame = tk.Frame(self.parent, bg="white")
        nav_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
        self.nav_buttons = {}
        for tab in ['cpu', 'memory', 'ssd', 'gpu', 'network']:
            btn = tk.Button(nav_frame, text=tab.upper(), font=("Arial", 11, "bold"),
                            bg="#f2f2f2", fg="#0078d4", padx=12, pady=4,
                            command=lambda t=tab: self.show_tab(t))
            btn.pack(side=tk.LEFT, padx=5)
            self.nav_buttons[tab] = btn

        # --- Main Content Frame ---
        self.content_frame = tk.Frame(self.parent, bg="white")
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.show_tab('cpu')

    def show_tab(self, tab):
        self.selected_tab = tab
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Highlight selected button
        for t, btn in self.nav_buttons.items():
            btn.config(bg="#f2f2f2" if t != tab else "#0078d4", fg="#0078d4" if t != tab else "white")

        # Show selected graph and details
        if tab == 'cpu':
            self._show_cpu_tab()
        elif tab == 'memory':
            self._show_memory_tab()
        elif tab == 'ssd':
            self._show_ssd_tab()
        elif tab == 'gpu':
            self._show_gpu_tab()
        elif tab == 'network':
            self._show_network_tab()

    def _show_cpu_tab(self):
        # Graph
        graph_frame = tk.Frame(self.content_frame, bg="white")
        graph_frame.pack(fill=tk.X, padx=5, pady=5)
        self.cpu_fig = self.Figure(figsize=(7, 2.5), dpi=80)
        self.cpu_ax = self.cpu_fig.add_subplot(111)
        self.cpu_canvas = self.FigureCanvasTkAgg(self.cpu_fig, graph_frame)
        self.cpu_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        # Details
        details_frame = tk.Frame(self.content_frame, bg="white")
        details_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        import psutil, platform
        cpu_percent = psutil.cpu_percent()
        cpu_count = psutil.cpu_count(logical=False)
        cpu_threads = psutil.cpu_count(logical=True)
        cpu_name = platform.processor() or "Unknown"
        tk.Label(details_frame, text=f"CPU Name: {cpu_name}", font=("Arial", 12), bg="white").pack(anchor="w")
        tk.Label(details_frame, text=f"Total Usage: {cpu_percent:.1f}%", font=("Arial", 12), bg="white").pack(anchor="w")
        tk.Label(details_frame, text=f"Cores: {cpu_count}", font=("Arial", 12), bg="white").pack(anchor="w")
        tk.Label(details_frame, text=f"Threads: {cpu_threads}", font=("Arial", 12), bg="white").pack(anchor="w")
        # Draw graph
        self.cpu_ax.clear()
        self.cpu_ax.plot([cpu_percent]*60, color='#0078d4', linewidth=2)
        self.cpu_ax.set_ylim(0, 100)
        self.cpu_ax.set_xlim(0, 60)
        self.cpu_ax.set_ylabel('%')
        self.cpu_ax.set_title("CPU Usage (%)")
        self.cpu_ax.grid(True, alpha=0.3)
        self.cpu_canvas.draw()

    def _show_memory_tab(self):
        graph_frame = tk.Frame(self.content_frame, bg="white")
        graph_frame.pack(fill=tk.X, padx=5, pady=5)
        self.mem_fig = self.Figure(figsize=(7, 2.5), dpi=80)
        self.mem_ax = self.mem_fig.add_subplot(111)
        self.mem_canvas = self.FigureCanvasTkAgg(self.mem_fig, graph_frame)
        self.mem_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        details_frame = tk.Frame(self.content_frame, bg="white")
        details_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        import psutil
        mem = psutil.virtual_memory()
        tk.Label(details_frame, text=f"Total Memory: {mem.total // (1024**2)} MB", font=("Arial", 12), bg="white").pack(anchor="w")
        tk.Label(details_frame, text=f"Used: {mem.used // (1024**2)} MB", font=("Arial", 12), bg="white").pack(anchor="w")
        tk.Label(details_frame, text=f"Available: {mem.available // (1024**2)} MB", font=("Arial", 12), bg="white").pack(anchor="w")
        tk.Label(details_frame, text=f"Usage: {mem.percent:.1f}%", font=("Arial", 12), bg="white").pack(anchor="w")
        self.mem_ax.clear()
        self.mem_ax.plot([mem.percent]*60, color='#00a651', linewidth=2)
        self.mem_ax.set_ylim(0, 100)
        self.mem_ax.set_xlim(0, 60)
        self.mem_ax.set_ylabel('%')
        self.mem_ax.set_title("Memory Usage (%)")
        self.mem_ax.grid(True, alpha=0.3)
        self.mem_canvas.draw()

    def _show_ssd_tab(self):
        graph_frame = tk.Frame(self.content_frame, bg="white")
        graph_frame.pack(fill=tk.X, padx=5, pady=5)
        self.disk_fig = self.Figure(figsize=(7, 2.5), dpi=80)
        self.disk_ax = self.disk_fig.add_subplot(111)
        self.disk_canvas = self.FigureCanvasTkAgg(self.disk_fig, graph_frame)
        self.disk_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        details_frame = tk.Frame(self.content_frame, bg="white")
        details_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        import psutil
        disk = psutil.disk_usage('/')
        tk.Label(details_frame, text=f"Total SSD: {disk.total // (1024**3)} GB", font=("Arial", 12), bg="white").pack(anchor="w")
        tk.Label(details_frame, text=f"Used: {disk.used // (1024**3)} GB", font=("Arial", 12), bg="white").pack(anchor="w")
        tk.Label(details_frame, text=f"Free: {disk.free // (1024**3)} GB", font=("Arial", 12), bg="white").pack(anchor="w")
        tk.Label(details_frame, text=f"Usage: {disk.percent:.1f}%", font=("Arial", 12), bg="white").pack(anchor="w")
        self.disk_ax.clear()
        self.disk_ax.plot([disk.percent]*60, color='#ff8c00', linewidth=2)
        self.disk_ax.set_ylim(0, 100)
        self.disk_ax.set_xlim(0, 60)
        self.disk_ax.set_ylabel('%')
        self.disk_ax.set_title("SSD Usage (%)")
        self.disk_ax.grid(True, alpha=0.3)
        self.disk_canvas.draw()

    def _show_gpu_tab(self):
        graph_frame = tk.Frame(self.content_frame, bg="white")
        graph_frame.pack(fill=tk.X, padx=5, pady=5)
        self.gpu_fig = self.Figure(figsize=(7, 2.5), dpi=80)
        self.gpu_ax = self.gpu_fig.add_subplot(111)
        self.gpu_canvas = self.FigureCanvasTkAgg(self.gpu_fig, graph_frame)
        self.gpu_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        details_frame = tk.Frame(self.content_frame, bg="white")
        details_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        # Placeholder details
        tk.Label(details_frame, text="GPU monitoring requires additional libraries.", font=("Arial", 12), bg="white").pack(anchor="w")
        self.gpu_ax.clear()
        self.gpu_ax.plot([0]*60, color='#7719aa', linewidth=2)
        self.gpu_ax.set_ylim(0, 100)
        self.gpu_ax.set_xlim(0, 60)
        self.gpu_ax.set_ylabel('%')
        self.gpu_ax.set_title("GPU Usage (%)")
        self.gpu_ax.grid(True, alpha=0.3)
        self.gpu_canvas.draw()

    def _show_network_tab(self):
        graph_frame = tk.Frame(self.content_frame, bg="white")
        graph_frame.pack(fill=tk.X, padx=5, pady=5)
        self.network_fig = self.Figure(figsize=(7, 2.5), dpi=80)
        self.network_ax = self.network_fig.add_subplot(111)
        self.network_canvas = self.FigureCanvasTkAgg(self.network_fig, graph_frame)
        self.network_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.details_frame = tk.Frame(self.content_frame, bg="white")
        self.details_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create labels for details
        self.network_sent_label = tk.Label(self.details_frame, text=f"Sent: 0.00 KB/s", font=("Arial", 12), bg="white")
        self.network_sent_label.pack(anchor="w")
        self.network_recv_label = tk.Label(self.details_frame, text=f"Received: 0.00 KB/s", font=("Arial", 12), bg="white")
        self.network_recv_label.pack(anchor="w")
        
        # Draw initial graph
        self._update_network_graph()

    def _update_network_graph(self):
        """Update network graph with current history"""
        if not hasattr(self, 'network_ax'):
            return
        
        self.network_ax.clear()
        
        # Plot sent data
        if self.network_sent_history:
            self.network_ax.plot(self.network_sent_history, label="Sent", color='#0078d4', linewidth=2)
            self.network_ax.fill_between(range(len(self.network_sent_history)), self.network_sent_history, 
                                         alpha=0.3, color='#0078d4')
        
        # Plot received data
        if self.network_recv_history:
            self.network_ax.plot(self.network_recv_history, label="Received", color='#00a651', linewidth=2)
            self.network_ax.fill_between(range(len(self.network_recv_history)), self.network_recv_history, 
                                         alpha=0.3, color='#00a651')
        
        # Calculate max for y-axis
        max_val = 1
        if self.network_sent_history or self.network_recv_history:
            max_val = max(max(self.network_sent_history + [0]), max(self.network_recv_history + [0]), 1)
        
        self.network_ax.set_ylim(0, max_val * 1.2)
        self.network_ax.set_xlim(0, 60)
        self.network_ax.set_ylabel('KB/s')
        self.network_ax.set_title("Network Usage (KB/s)")
        self.network_ax.legend()
        self.network_ax.grid(True, alpha=0.3)
        self.network_canvas.draw()

    def update_graphs(self):
        """Update all performance graphs"""
        import psutil
        
        # Update histories (keep last 60 points)
        self.cpu_history.append(psutil.cpu_percent())
        self.cpu_history = self.cpu_history[-60:]
        
        mem = psutil.virtual_memory()
        self.memory_history.append(mem.percent)
        self.memory_history = self.memory_history[-60:]
        
        disk = psutil.disk_usage('/')
        self.disk_history.append(disk.percent)
        self.disk_history = self.disk_history[-60:]
        
        self.gpu_history.append(0)  # Placeholder
        self.gpu_history = self.gpu_history[-60:]
        
        # Update network history
        net_stats = self.monitor.get_network_usage()
        self.network_sent_history.append(net_stats.get('sent', 0))
        self.network_recv_history.append(net_stats.get('recv', 0))
        self.network_sent_history = self.network_sent_history[-60:]
        self.network_recv_history = self.network_recv_history[-60:]
        
        # Update the currently visible tab
        if self.selected_tab == 'cpu' and hasattr(self, 'cpu_ax'):
            self.cpu_ax.clear()
            self.cpu_ax.plot(self.cpu_history, color='#0078d4', linewidth=2)
            self.cpu_ax.fill_between(range(len(self.cpu_history)), self.cpu_history, alpha=0.3, color='#0078d4')
            self.cpu_ax.set_ylim(0, 100)
            self.cpu_ax.set_xlim(0, 60)
            self.cpu_ax.set_ylabel('%')
            self.cpu_ax.set_title("CPU Usage (%)")
            self.cpu_ax.grid(True, alpha=0.3)
            self.cpu_canvas.draw()
        
        elif self.selected_tab == 'memory' and hasattr(self, 'mem_ax'):
            self.mem_ax.clear()
            self.mem_ax.plot(self.memory_history, color='#00a651', linewidth=2)
            self.mem_ax.fill_between(range(len(self.memory_history)), self.memory_history, alpha=0.3, color='#00a651')
            self.mem_ax.set_ylim(0, 100)
            self.mem_ax.set_xlim(0, 60)
            self.mem_ax.set_ylabel('%')
            self.mem_ax.set_title("Memory Usage (%)")
            self.mem_ax.grid(True, alpha=0.3)
            self.mem_canvas.draw()
        
        elif self.selected_tab == 'ssd' and hasattr(self, 'disk_ax'):
            self.disk_ax.clear()
            self.disk_ax.plot(self.disk_history, color='#ff8c00', linewidth=2)
            self.disk_ax.fill_between(range(len(self.disk_history)), self.disk_history, alpha=0.3, color='#ff8c00')
            self.disk_ax.set_ylim(0, 100)
            self.disk_ax.set_xlim(0, 60)
            self.disk_ax.set_ylabel('%')
            self.disk_ax.set_title("SSD Usage (%)")
            self.disk_ax.grid(True, alpha=0.3)
            self.disk_canvas.draw()
        
        elif self.selected_tab == 'network' and hasattr(self, 'network_ax'):
            # Update labels
            if hasattr(self, 'network_sent_label') and hasattr(self, 'network_recv_label'):
                self.network_sent_label.config(text=f"Sent: {net_stats.get('sent', 0):.2f} KB/s")
                self.network_recv_label.config(text=f"Received: {net_stats.get('recv', 0):.2f} KB/s")
            # Update graph
            self._update_network_graph()

    def start_updates(self):
        """Start the update thread"""
        self.update_running = True
        self._schedule_update()
    
    def _schedule_update(self):
        """Schedule the next graph update"""
        if self.update_running:
            try:
                self.update_graphs()
            except:
                pass
            # Update graphs every 1 second for smooth animation
            self.update_job = self.parent.after(1000, self._schedule_update)
    
    def stop_updates(self):
        """Stop the update thread"""
        self.update_running = False
        if self.update_job:
            try:
                self.parent.after_cancel(self.update_job)
            except:
                pass
            self.update_job = None
