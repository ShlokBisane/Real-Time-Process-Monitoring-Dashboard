"""
UI for process management
"""
import tkinter as tk
from tkinter import ttk, messagebox
from modules.processes.backend import ProcessManager
from modules.utils.helpers import check_psutil


class ProcessesUI:
    def __init__(self, parent):
        self.parent = parent
        self.manager = ProcessManager()
        self.update_running = False
        self.update_job = None
        self.search_var = tk.StringVar()
        # Remove trace that causes immediate refresh on every keystroke
        # self.search_var.trace('w', lambda *args: self.refresh_processes())
        self.group_processes = True
        self.selected_process = None
        self.selected_app_process = None
        self.expanded_processes = set()  # Track which processes are expanded
        self.process_data_map = {}  # Map tree items to process data
        
        if not check_psutil():
            tk.Label(parent, text="Install psutil: pip install psutil",
                    font=("Arial", 12), fg="red").pack(pady=20)
            return
        
        self.setup_ui()
    
    def setup_ui(self):
        # Title and Search Frame
        header_frame = tk.Frame(self.parent, bg="white")
        header_frame.pack(fill=tk.X, pady=10, padx=10)
        
        tk.Label(header_frame, text="Processes", font=("Arial", 16, "bold"),
                bg="white").pack(side=tk.LEFT)
        
        # Search box
        search_frame = tk.Frame(header_frame, bg="white")
        search_frame.pack(side=tk.RIGHT)
        
        tk.Label(search_frame, text="Search:", font=("Arial", 10),
                bg="white").pack(side=tk.LEFT, padx=(0, 5))
        
        search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                               font=("Arial", 10), width=30)
        search_entry.pack(side=tk.LEFT)
        
        # Bind Enter key to search instead of real-time search
        search_entry.bind("<Return>", lambda e: self.refresh_processes())
        
        tk.Button(search_frame, text="Search", command=self.refresh_processes,
                 bg="#0078d4", fg="white", padx=5).pack(side=tk.LEFT, padx=2)
        tk.Button(search_frame, text="Clear", command=self.clear_search,
                 bg="#999", fg="white", padx=5).pack(side=tk.LEFT, padx=2)
        
        # Toolbar
        toolbar = tk.Frame(self.parent, bg="white")
        toolbar.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(toolbar, text="Refresh", command=self.refresh_processes,
                 bg="#0078d4", fg="white", padx=10).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Kill Process", command=self.kill_selected_process,
                 bg="#d13438", fg="white", padx=10).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Suspend", command=self.suspend_selected_process,
                 bg="#ff8c00", fg="white", padx=10).pack(side=tk.LEFT, padx=2)
        
        # Group toggle
        self.group_var = tk.BooleanVar(value=True)
        tk.Checkbutton(toolbar, text="Group by Name", variable=self.group_var,
                      command=self.toggle_grouping, bg="white",
                      font=("Arial", 10)).pack(side=tk.LEFT, padx=10)
        
        # --- App Processes Table ---
        app_label_frame = tk.Frame(self.parent, bg="white")
        app_label_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        
        tk.Label(app_label_frame, text="Active Application Processes", 
                 font=("Arial", 12, "bold"), bg="white", fg="#FF6B00").pack(anchor="w")
        tk.Label(app_label_frame, text="Right-click to expand/collapse grouped processes", 
                 font=("Arial", 9), bg="white", fg="#666").pack(anchor="w")
        
        app_table_frame = tk.Frame(self.parent, bg="white", relief=tk.RIDGE, borderwidth=2)
        app_table_frame.pack(fill=tk.X, padx=10, pady=(5, 10))
        
        app_vsb = tk.Scrollbar(app_table_frame, orient="vertical")
        app_hsb = tk.Scrollbar(app_table_frame, orient="horizontal")
        
        app_columns = ("Count", "Name", "User", "CPU %", "Memory %", "Network (KB/s)", "Status")
        self.app_process_tree = ttk.Treeview(
            app_table_frame, 
            columns=app_columns, 
            show="tree headings",
            yscrollcommand=app_vsb.set, 
            xscrollcommand=app_hsb.set, 
            height=8
        )
        app_vsb.config(command=self.app_process_tree.yview)
        app_hsb.config(command=self.app_process_tree.xview)
        
        for col in app_columns:
            self.app_process_tree.heading(col, text=col)
            if col == "Name":
                self.app_process_tree.column(col, width=200)
            elif col == "Network (KB/s)":
                self.app_process_tree.column(col, width=120)
            elif col == "Count":
                self.app_process_tree.column(col, width=60)
            else:
                self.app_process_tree.column(col, width=100)
        
        self.app_process_tree.column("#0", width=30)
        
        self.app_process_tree.tag_configure('app_highlight', background='#FFE5CC')
        self.app_process_tree.tag_configure('instance', background='#FFF5E6')
        
        # Right-click and single-click to expand/collapse
        self.app_context_menu = tk.Menu(self.app_process_tree, tearoff=0)
        self.app_process_tree.bind("<Button-3>", self.show_app_context_menu)
        self.app_process_tree.bind("<Button-1>", self.on_tree_click)
        
        self.app_process_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        app_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        app_hsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        # All Processes Label
        all_label_frame = tk.Frame(self.parent, bg="white")
        all_label_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        
        tk.Label(all_label_frame, text="All System Processes", 
                 font=("Arial", 12, "bold"), bg="white").pack(anchor="w")
        
        # Process table (Main)
        table_frame = tk.Frame(self.parent, bg="white")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        vsb = tk.Scrollbar(table_frame, orient="vertical")
        hsb = tk.Scrollbar(table_frame, orient="horizontal")
        
        columns = ("Count", "Name", "User", "CPU %", "Memory %", "Network (KB/s)", "Status")
        self.process_tree = ttk.Treeview(
            table_frame, 
            columns=columns, 
            show="tree headings",
            yscrollcommand=vsb.set, 
            xscrollcommand=hsb.set
        )
        
        vsb.config(command=self.process_tree.yview)
        hsb.config(command=self.process_tree.xview)
        
        for col in columns:
            self.process_tree.heading(col, text=col)
            if col == "Name":
                self.process_tree.column(col, width=200)
            elif col == "Network (KB/s)":
                self.process_tree.column(col, width=120)
            elif col == "Count":
                self.process_tree.column(col, width=60)
            else:
                self.process_tree.column(col, width=100)
        
        self.process_tree.column("#0", width=30)
        
        self.process_tree.tag_configure('even', background='#f2f2f2')
        self.process_tree.tag_configure('odd', background='#ffffff')
        self.process_tree.tag_configure('active', background="#aefa0a")
        self.process_tree.tag_configure('instance', background='#E8E8E8')
        
        # Right-click and single-click
        self.context_menu = tk.Menu(self.process_tree, tearoff=0)
        self.process_tree.bind("<Button-3>", self.show_context_menu)
        self.process_tree.bind("<Button-1>", self.on_tree_click)
        
        self.process_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.refresh_processes()
    
    def toggle_grouping(self):
        """Toggle process grouping"""
        self.group_processes = self.group_var.get()
        self.expanded_processes.clear()
        self.refresh_processes()
    
    def on_tree_click(self, event):
        """Handle single click to toggle expansion"""
        tree = event.widget
        item = tree.identify_row(event.y)
        if not item:
            return
        
        # Select the clicked item
        tree.selection_set(item)
        
        # Only toggle if it's a parent item
        if item in self.process_data_map:
            data = self.process_data_map[item]
            if data.get('is_parent') and data.get('count', 1) > 1:
                name = data.get('name')
                # Toggle expansion state
                if name in self.expanded_processes:
                    self.expanded_processes.remove(name)
                else:
                    self.expanded_processes.add(name)
                # Refresh to show/hide children
                self.refresh_processes()
    
    def toggle_expansion(self, event):
        """Toggle expansion of grouped process (no longer used, kept for compatibility)"""
        pass
    
    def show_context_menu(self, event):
        """Show context menu on right-click and expand if grouped"""
        item = self.process_tree.identify_row(event.y)
        if not item:
            return
            
        self.process_tree.selection_set(item)
        
        # Check if this is a parent or child item
        if item in self.process_data_map:
            data = self.process_data_map[item]
            
            if data.get('is_parent'):
                # Parent item
                name = data.get('name')
                count = data.get('count', 1)
                
                # Auto-expand if it's a grouped process and not already expanded
                if count > 1 and name not in self.expanded_processes:
                    self.expanded_processes.add(name)
                    self.refresh_processes()
                    return  # Don't show menu, just expand
                
                # Build context menu
                self.context_menu.delete(0, tk.END)
                
                if count > 1:
                    self.context_menu.add_command(label="Collapse", 
                                                command=lambda: self.collapse_process(name))
                    self.context_menu.add_separator()
                    self.context_menu.add_command(label=f"Kill All {count} Instances", 
                                                command=self.kill_selected_process)
                    self.context_menu.add_command(label=f"Suspend All {count} Instances", 
                                                command=self.suspend_selected_process)
                else:
                    self.context_menu.add_command(label="Kill Process", 
                                                command=self.kill_selected_process)
                    self.context_menu.add_command(label="Suspend Process", 
                                                command=self.suspend_selected_process)
            else:
                # Child item (individual process)
                self.context_menu.delete(0, tk.END)
                self.context_menu.add_command(label="Kill This Process", 
                                            command=self.kill_selected_process)
                self.context_menu.add_command(label="Suspend This Process", 
                                            command=self.suspend_selected_process)
            
            self.context_menu.post(event.x_root, event.y_root)
    
    def show_app_context_menu(self, event):
        """Show context menu on right-click for app table and expand if grouped"""
        item = self.app_process_tree.identify_row(event.y)
        if not item:
            return
            
        self.app_process_tree.selection_set(item)
        
        if item in self.process_data_map:
            data = self.process_data_map[item]
            
            if data.get('is_parent'):
                name = data.get('name')
                count = data.get('count', 1)
                
                # Auto-expand if it's a grouped process and not already expanded
                if count > 1 and name not in self.expanded_processes:
                    self.expanded_processes.add(name)
                    self.refresh_processes()
                    return  # Don't show menu, just expand
                
                # Build context menu
                self.app_context_menu.delete(0, tk.END)
                
                if count > 1:
                    self.app_context_menu.add_command(label="Collapse", 
                                                    command=lambda: self.collapse_process(name))
                    self.app_context_menu.add_separator()
                    self.app_context_menu.add_command(label=f"Kill All {count} Instances", 
                                                    command=self.kill_selected_process)
                    self.app_context_menu.add_command(label=f"Suspend All {count} Instances", 
                                                    command=self.suspend_selected_process)
            else:
                # Child item
                self.app_context_menu.delete(0, tk.END)
                self.app_context_menu.add_command(label="Kill This Process", 
                                                command=self.kill_selected_process)
                self.app_context_menu.add_command(label="Suspend This Process", 
                                                command=self.suspend_selected_process)
            
            self.app_context_menu.post(event.x_root, event.y_root)
    
    def expand_process(self, name):
        """Expand a grouped process"""
        self.expanded_processes.add(name)
        self.refresh_processes()
    
    def collapse_process(self, name):
        """Collapse a grouped process"""
        self.expanded_processes.discard(name)
        self.refresh_processes()
    
    def show_instances(self):
        """Show all instances of a grouped process with action buttons"""
        # Determine which tree was used
        if hasattr(self, 'selected_process') and self.selected_process:
            selected = self.selected_process
        elif hasattr(self, 'selected_app_process') and self.selected_app_process:
            selected = self.selected_app_process
        else:
            return
        
        count = selected['count']
        name = selected['name']
        
        # Get all processes for this name
        all_processes = self.manager.list_processes()
        instances = [p for p in all_processes if p.get('name') == name]
        
        if not instances:
            messagebox.showinfo("No Instances", f"No instances of '{name}' found.")
            return
        
        # Create popup window
        popup = tk.Toplevel(self.parent)
        popup.title(f"Instances of {name}")
        popup.geometry("900x500")
        popup.configure(bg="white")
        
        # Header
        header = tk.Frame(popup, bg="white")
        header.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(header, text=f"All Instances of '{name}'",
                font=("Arial", 14, "bold"), bg="white").pack(side=tk.LEFT)
        
        tk.Label(header, text=f"Total: {len(instances)} process(es)",
                font=("Arial", 10), bg="white", fg="#666").pack(side=tk.LEFT, padx=10)
        
        # Create table for instances
        frame = tk.Frame(popup, bg="white")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        vsb = tk.Scrollbar(frame, orient="vertical")
        columns = ("PID", "User", "CPU %", "Memory %", "Network (KB/s)", "Status")
        tree = ttk.Treeview(frame, columns=columns, show="headings",
                           yscrollcommand=vsb.set)
        vsb.config(command=tree.yview)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
        # Insert instances with alternating colors
        for idx, proc in enumerate(instances):
            tags = ('even',) if idx % 2 == 0 else ('odd',)
            tree.insert("", "end", values=(
                proc.get('pid', 'N/A'),
                proc.get('username', 'N/A'),
                f"{proc.get('cpu_percent', 0):.1f}",
                f"{proc.get('memory_percent', 0):.1f}",
                f"{proc.get('network_kbps', 0):.2f}",
                proc.get('status', 'N/A')
            ), tags=tags)
        
        tree.tag_configure('even', background='#f2f2f2')
        tree.tag_configure('odd', background='#ffffff')
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Action buttons
        btn_frame = tk.Frame(popup, bg="white")
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def kill_selected_instance():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("No Selection", "Please select a process instance")
                return
            
            pid = tree.item(selected[0])['values'][0]
            if messagebox.askyesno("Confirm", f"Kill process {pid}?"):
                success, msg = self.manager.kill_process(pid)
                if success:
                    messagebox.showinfo("Success", msg)
                    popup.destroy()
                    self.refresh_processes()
                else:
                    messagebox.showerror("Error", msg)
        
        def suspend_selected_instance():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("No Selection", "Please select a process instance")
                return
            
            pid = tree.item(selected[0])['values'][0]
            success, msg = self.manager.suspend_process(pid)
            if success:
                messagebox.showinfo("Success", msg)
                popup.destroy()
                self.refresh_processes()
            else:
                messagebox.showerror("Error", msg)
        
        def resume_selected_instance():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("No Selection", "Please select a process instance")
                return
            
            pid = tree.item(selected[0])['values'][0]
            success, msg = self.manager.resume_process(pid)
            if success:
                messagebox.showinfo("Success", msg)
                popup.destroy()
                self.refresh_processes()
            else:
                messagebox.showerror("Error", msg)
        
        tk.Button(btn_frame, text="Kill Selected", command=kill_selected_instance,
                 bg="#d13438", fg="white", padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Suspend Selected", command=suspend_selected_instance,
                 bg="#ff8c00", fg="white", padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Resume Selected", command=resume_selected_instance,
                 bg="#28a745", fg="white", padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Close", command=popup.destroy,
                 bg="#999", fg="white", padx=20, pady=5).pack(side=tk.RIGHT, padx=5)
    
    def kill_all_instances(self):
        """Kill all instances of a grouped process"""
        selected = self.selected_process or self.selected_app_process
        if not selected:
            return
        
        name = selected['name']
        count = selected['count']
        
        if not messagebox.askyesno("Confirm", 
            f"Are you sure you want to kill all {count} instances of '{name}'?"):
            return
        
        all_processes = self.manager.list_processes()
        instances = [p for p in all_processes if p.get('name') == name]
        
        success_count = 0
        failed_count = 0
        
        for proc in instances:
            pid = proc.get('pid')
            success, msg = self.manager.kill_process(pid)
            if success:
                success_count += 1
            else:
                failed_count += 1
        
        messagebox.showinfo("Result", 
            f"Killed {success_count} process(es)\nFailed: {failed_count}")
        self.refresh_processes()
    
    def suspend_all_instances(self):
        """Suspend all instances of a grouped process"""
        selected = self.selected_process or self.selected_app_process
        if not selected:
            return
        
        name = selected['name']
        count = selected['count']
        
        if not messagebox.askyesno("Confirm", 
            f"Are you sure you want to suspend all {count} instances of '{name}'?"):
            return
        
        all_processes = self.manager.list_processes()
        instances = [p for p in all_processes if p.get('name') == name]
        
        success_count = 0
        failed_count = 0
        
        for proc in instances:
            pid = proc.get('pid')
            success, msg = self.manager.suspend_process(pid)
            if success:
                success_count += 1
            else:
                failed_count += 1
        
        messagebox.showinfo("Result", 
            f"Suspended {success_count} process(es)\nFailed: {failed_count}")
        self.refresh_processes()
    
    def clear_search(self):
        """Clear search and refresh"""
        self.search_var.set("")
        self.refresh_processes()
    
    def refresh_processes(self):
        """Refresh the process list"""
        if not hasattr(self, 'process_tree'):
            return

        # Save scroll positions and selections
        try:
            yview_position = self.process_tree.yview()[0]
            app_yview_position = self.app_process_tree.yview()[0]
            
            main_selected = self.process_tree.selection()
            main_selected_name = None
            if main_selected and main_selected[0] in self.process_data_map:
                main_selected_name = self.process_data_map[main_selected[0]].get('name')
            
            app_selected = self.app_process_tree.selection()
            app_selected_name = None
            if app_selected and app_selected[0] in self.process_data_map:
                app_selected_name = self.process_data_map[app_selected[0]].get('name')
        except:
            yview_position = 0
            app_yview_position = 0
            main_selected_name = None
            app_selected_name = None

        # IMPORTANT: DON'T clear expanded_processes here
        # This preserves the expansion state across refreshes
        # expanded_processes is only modified by user clicks

        # Clear tables and data map
        for item in self.process_tree.get_children():
            self.process_tree.delete(item)
        for item in self.app_process_tree.get_children():
            self.app_process_tree.delete(item)
        self.process_data_map.clear()

        try:
            all_processes = self.manager.list_processes()
            
            # Apply search filter
            search_query = self.search_var.get().strip()
            if search_query:
                all_processes = self.manager.search_processes(all_processes, search_query)
            
            # Group processes if enabled
            if self.group_processes:
                processes = self.manager.group_processes(all_processes)
            else:
                processes = [dict(p, count=1, processes=[p]) for p in all_processes]

            # Populate App Processes Table
            app_processes = [p for p in processes if self.is_app_process(p)]
            for proc in app_processes:
                self._insert_process(self.app_process_tree, proc, app_selected_name, is_app_table=True)

            # Populate All Processes Table
            for idx, proc in enumerate(processes):
                self._insert_process(self.process_tree, proc, main_selected_name, idx=idx)

            # Restore scroll positions
            self.process_tree.update_idletasks()
            self.process_tree.yview_moveto(yview_position)
            self.app_process_tree.update_idletasks()
            self.app_process_tree.yview_moveto(app_yview_position)

        except Exception as e:
            print(f"Error refreshing processes: {e}")
            # Don't show error dialog during auto-refresh
    
    def _insert_process(self, tree, proc, selected_name, idx=0, is_app_table=False):
        """Helper method to insert process with expansion support"""
        name = proc.get('name', 'N/A')
        count = proc.get('count', 1)
        
        # Determine tags
        if is_app_table:
            tags = ['app_highlight']
        else:
            if proc.get('cpu_percent', 0) > 0 or proc.get('memory_percent', 0) > 0:
                tags = ['active']
            else:
                tags = ['even' if idx % 2 == 0 else 'odd']
        
        # Insert parent item (no icon)
        values = (
            count,
            name,
            proc.get('username', 'N/A'),
            f"{proc.get('cpu_percent', 0):.1f}",
            f"{proc.get('memory_percent', 0):.1f}",
            f"{proc.get('network_kbps', 0):.2f}",
            proc.get('status', 'N/A')
        )
        
        parent_id = tree.insert("", "end", text="", values=values, tags=tags)
        
        # Store data mapping
        self.process_data_map[parent_id] = {
            'is_parent': True,
            'name': name,
            'count': count,
            'processes': proc.get('processes', [proc]),
            'pid': proc.get('pid')
        }
        
        # Restore selection
        if selected_name and name == selected_name:
            tree.selection_set(parent_id)
            tree.see(parent_id)
        
        # Insert children if expanded
        if count > 1 and name in self.expanded_processes:
            for child_proc in proc.get('processes', []):
                child_values = (
                    "",
                    f"  └─ PID {child_proc.get('pid')}",
                    child_proc.get('username', 'N/A'),
                    f"{child_proc.get('cpu_percent', 0):.1f}",
                    f"{child_proc.get('memory_percent', 0):.1f}",
                    f"{child_proc.get('network_kbps', 0):.2f}",
                    child_proc.get('status', 'N/A')
                )
                
                child_id = tree.insert(parent_id, "end", text="", 
                                      values=child_values, tags=['instance'])
                
                self.process_data_map[child_id] = {
                    'is_parent': False,
                    'name': name,
                    'pid': child_proc.get('pid'),
                    'count': 1
                }
    
    def is_app_process(self, proc):
        """Determine if a process is an application (not system process)"""
        name = proc.get('name', '').lower()
        
        # Common system processes to exclude
        system_processes = [
            'system', 'idle', 'init', 'systemd', 'kthreadd', 'ksoftirqd',
            'migration', 'watchdog', 'cpuhp', 'kdevtmpfs', 'netns',
            'kworker', 'rcu_', 'mm_', 'writeback', 'kblockd', 'kintegrityd',
            'kswapd', 'ksmd', 'khugepaged', 'crypto', 'kthrotld',
            'svchost', 'services', 'lsass', 'csrss', 'smss', 'wininit',
            'dwm', 'conhost', 'dllhost', 'taskhost', 'explorer.exe'
        ]
        
        # Check if it's a system process
        for sys_proc in system_processes:
            if sys_proc in name:
                return False
        
        # Consider it an app if it's using resources
        cpu = proc.get('cpu_percent', 0)
        mem = proc.get('memory_percent', 0)
        net = proc.get('network_kbps', 0)
        
        return (cpu > 0.1 or mem > 0.5 or net > 1) and len(name) > 2
    
    def kill_selected_process(self):
        """Kill the selected process or all instances if grouped"""
        # Try main tree first, then app tree
        if self.process_tree.selection():
            tree = self.process_tree
            selected = tree.selection()[0]
        elif self.app_process_tree.selection():
            tree = self.app_process_tree
            selected = tree.selection()[0]
        else:
            messagebox.showwarning("Warning", "Please select a process")
            return
        
        if selected not in self.process_data_map:
            return
        
        data = self.process_data_map[selected]
        
        if data.get('is_parent'):
            # Kill all instances
            name = data.get('name')
            count = data.get('count', 1)
            processes = data.get('processes', [])
            
            if count > 1:
                if not messagebox.askyesno("Confirm", 
                    f"Kill all {count} instances of '{name}'?"):
                    return
                
                success_count = 0
                failed_count = 0
                
                for proc in processes:
                    pid = proc.get('pid')
                    success, msg = self.manager.kill_process(pid)
                    if success:
                        success_count += 1
                    else:
                        failed_count += 1
                
                messagebox.showinfo("Result", 
                    f"Killed {success_count} process(es)\nFailed: {failed_count}")
            else:
                # Single process
                pid = data.get('pid')
                if messagebox.askyesno("Confirm", f"Kill process {pid}?"):
                    success, msg = self.manager.kill_process(pid)
                    if success:
                        messagebox.showinfo("Success", msg)
                    else:
                        messagebox.showerror("Error", msg)
        else:
            # Kill single child process
            pid = data.get('pid')
            if messagebox.askyesno("Confirm", f"Kill process {pid}?"):
                success, msg = self.manager.kill_process(pid)
                if success:
                    messagebox.showinfo("Success", msg)
                else:
                    messagebox.showerror("Error", msg)
        
        self.refresh_processes()
    
    def suspend_selected_process(self):
        """Suspend the selected process or all instances if grouped"""
        if self.process_tree.selection():
            tree = self.process_tree
            selected = tree.selection()[0]
        elif self.app_process_tree.selection():
            tree = self.app_process_tree
            selected = tree.selection()[0]
        else:
            messagebox.showwarning("Warning", "Please select a process")
            return
        
        if selected not in self.process_data_map:
            return
        
        data = self.process_data_map[selected]
        
        if data.get('is_parent'):
            name = data.get('name')
            count = data.get('count', 1)
            processes = data.get('processes', [])
            
            if count > 1:
                if not messagebox.askyesno("Confirm", 
                    f"Suspend all {count} instances of '{name}'?"):
                    return
                
                success_count = 0
                failed_count = 0
                
                for proc in processes:
                    pid = proc.get('pid')
                    success, msg = self.manager.suspend_process(pid)
                    if success:
                        success_count += 1
                    else:
                        failed_count += 1
                
                messagebox.showinfo("Result", 
                    f"Suspended {success_count} process(es)\nFailed: {failed_count}")
            else:
                pid = data.get('pid')
                success, msg = self.manager.suspend_process(pid)
                if success:
                    messagebox.showinfo("Success", msg)
                else:
                    messagebox.showerror("Error", msg)
        else:
            pid = data.get('pid')
            success, msg = self.manager.suspend_process(pid)
            if success:
                messagebox.showinfo("Success", msg)
            else:
                messagebox.showerror("Error", msg)
        
        self.refresh_processes()
    
    def start_updates(self):
        """Start auto-refresh using tkinter's after() method"""
        self.update_running = True
        self._schedule_update()
    
    def _schedule_update(self):
        """Schedule the next update"""
        if self.update_running:
            try:
                self.refresh_processes()
            except:
                pass
            # Schedule next update after 1 second
            self.update_job = self.parent.after(1000, self._schedule_update)
    
    def stop_updates(self):
        """Stop auto-refresh"""
        self.update_running = False
        if self.update_job:
            try:
                self.parent.after_cancel(self.update_job)
            except:
                pass
            self.update_job = None
