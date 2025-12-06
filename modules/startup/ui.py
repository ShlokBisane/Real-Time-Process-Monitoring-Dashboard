
"""
UI for startup applications management
"""
import customtkinter as ctk
from tkinter import ttk, messagebox, simpledialog
from modules.startup.backend import StartupAppsManager

# Theme colors
BACKGROUND_DARK = "#0E0E12"
CARD_BG = "#1B1B24"
ACCENT_ORANGE = "#FF6B00"
TEXT_PRIMARY = "#F5F5F5"
TEXT_SECONDARY = "#B9B9C6"


class StartupAppsUI:
    def __init__(self, parent):
        self.parent = parent
        self.manager = StartupAppsManager()
        self.setup_ui()
    
    def setup_ui(self):
        self.parent.configure(fg_color=BACKGROUND_DARK)
        
        # Header
        header = ctk.CTkFrame(self.parent, fg_color=BACKGROUND_DARK)
        header.pack(fill="x", padx=22, pady=(20, 10))
        
        title = ctk.CTkLabel(
            header,
            text="STARTUP APPLICATIONS",
            font=ctk.CTkFont("Segoe UI", 26, weight="bold"),
            text_color=TEXT_PRIMARY,
        )
        title.pack(side="left")
        
        subtitle = ctk.CTkLabel(
            header,
            text="Manage apps that run at system startup",
            font=ctk.CTkFont("Segoe UI", 14),
            text_color=ACCENT_ORANGE,
        )
        subtitle.pack(side="left", padx=(12, 0))
        
        # Toolbar
        toolbar = ctk.CTkFrame(self.parent, fg_color=CARD_BG, corner_radius=12)
        toolbar.pack(fill="x", padx=20, pady=(0, 10))
        
        btn_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        btn_frame.pack(pady=12, padx=12)
        
        ctk.CTkButton(
            btn_frame, 
            text="🔄 Refresh",
            command=self.load_startup_apps,
            fg_color="#0078d4",
            hover_color="#005a9e",
            width=120,
            height=35
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="✓ Enable",
            command=self.enable_startup_app,
            fg_color="#00a651",
            hover_color="#008040",
            width=120,
            height=35
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="✕ Disable",
            command=self.disable_startup_app,
            fg_color="#ff8c00",
            hover_color="#cc7000",
            width=120,
            height=35
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="+ Add New",
            command=self.add_startup_app,
            fg_color=ACCENT_ORANGE,
            hover_color="#cc5500",
            width=120,
            height=35
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="🗑 Remove",
            command=self.remove_startup_app,
            fg_color="#d13438",
            hover_color="#a82a2d",
            width=120,
            height=35
        ).pack(side="left", padx=5)
        
        # Count label
        self.count_label = ctk.CTkLabel(
            toolbar,
            text="Total startup apps: 0",
            font=ctk.CTkFont("Segoe UI", 12),
            text_color=TEXT_SECONDARY,
        )
        self.count_label.pack(pady=(0, 10))
        
        # Table container
        table_container = ctk.CTkFrame(self.parent, fg_color=CARD_BG, corner_radius=12)
        table_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Table frame
        import tkinter as tk
        table_frame = tk.Frame(table_container, bg=CARD_BG)
        table_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Scrollbars
        vsb = tk.Scrollbar(table_frame, orient="vertical")
        hsb = tk.Scrollbar(table_frame, orient="horizontal")
        
        # Treeview with custom style
        style = ttk.Style()
        style.theme_use('default')
        style.configure("Startup.Treeview",
                       background="#1B1B24",
                       foreground=TEXT_PRIMARY,
                       fieldbackground="#1B1B24",
                       borderwidth=0,
                       rowheight=30)
        style.configure("Startup.Treeview.Heading",
                       background="#2A2A35",
                       foreground=TEXT_PRIMARY,
                       borderwidth=0,
                       relief="flat")
        style.map("Startup.Treeview",
                 background=[('selected', ACCENT_ORANGE)])
        style.map("Startup.Treeview.Heading",
                 background=[('active', '#3A3A45')])
        
        columns = ("Name", "Command", "Status", "Location")
        self.startup_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            style="Startup.Treeview"
        )
        
        vsb.config(command=self.startup_tree.yview)
        hsb.config(command=self.startup_tree.xview)
        
        # Configure columns
        self.startup_tree.heading("Name", text="Application Name")
        self.startup_tree.heading("Command", text="Command")
        self.startup_tree.heading("Status", text="Status")
        self.startup_tree.heading("Location", text="Location")
        
        self.startup_tree.column("Name", width=250, minwidth=150)
        self.startup_tree.column("Command", width=300, minwidth=200)
        self.startup_tree.column("Status", width=100, minwidth=80)
        self.startup_tree.column("Location", width=100, minwidth=80)
        
        # Pack
        self.startup_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        
        # Load initial data
        self.load_startup_apps()
    
    def load_startup_apps(self):
        """Load and display startup applications"""
        # Clear existing
        for item in self.startup_tree.get_children():
            self.startup_tree.delete(item)
        
        # Load apps
        apps = self.manager.list_startup_apps()
        
        for app in apps:
            # Store the full path in values for later use
            self.startup_tree.insert("", "end", values=(
                app['name'],
                app['command'][:60] + '...' if len(app['command']) > 60 else app['command'],
                app['status'],
                app['location']
            ), tags=(app['path'],))
        
        # Update count
        enabled_count = sum(1 for app in apps if app['status'] == 'Enabled')
        self.count_label.configure(text=f"Total: {len(apps)} apps ({enabled_count} enabled, {len(apps) - enabled_count} disabled)")
    
    def get_selected_app(self):
        """Get the currently selected app"""
        selected = self.startup_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an application first")
            return None
        
        item = self.startup_tree.item(selected[0])
        tags = self.startup_tree.item(selected[0], 'tags')
        
        if tags:
            filepath = tags[0]
            return {
                'name': item['values'][0],
                'command': item['values'][1],
                'status': item['values'][2],
                'location': item['values'][3],
                'path': filepath
            }
        return None
    
    def enable_startup_app(self):
        """Enable the selected startup app"""
        app = self.get_selected_app()
        if not app:
            return
        
        if app['status'] == 'Enabled':
            messagebox.showinfo("Already Enabled", f"'{app['name']}' is already enabled")
            return
        
        success, msg = self.manager.enable_app(app['path'])
        if success:
            messagebox.showinfo("Success", msg)
            self.load_startup_apps()
        else:
            messagebox.showerror("Error", msg)
    
    def disable_startup_app(self):
        """Disable the selected startup app"""
        app = self.get_selected_app()
        if not app:
            return
        
        if app['status'] == 'Disabled':
            messagebox.showinfo("Already Disabled", f"'{app['name']}' is already disabled")
            return
        
        success, msg = self.manager.disable_app(app['path'])
        if success:
            messagebox.showinfo("Success", msg)
            self.load_startup_apps()
        else:
            messagebox.showerror("Error", msg)
    
    def add_startup_app(self):
        """Add a new startup application"""
        # Create dialog
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Add Startup Application")
        dialog.geometry("500x200")
        dialog.configure(fg_color=CARD_BG)
        
        # Make it modal
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (200 // 2)
        dialog.geometry(f"500x200+{x}+{y}")
        
        # App name
        ctk.CTkLabel(
            dialog,
            text="Application Name:",
            font=ctk.CTkFont("Segoe UI", 12),
            text_color=TEXT_PRIMARY
        ).pack(pady=(20, 5), padx=20, anchor="w")
        
        name_entry = ctk.CTkEntry(
            dialog,
            width=460,
            height=35,
            fg_color="#2A2A35",
            text_color=TEXT_PRIMARY
        )
        name_entry.pack(padx=20)
        
        # App command
        ctk.CTkLabel(
            dialog,
            text="Command (full path to executable):",
            font=ctk.CTkFont("Segoe UI", 12),
            text_color=TEXT_PRIMARY
        ).pack(pady=(10, 5), padx=20, anchor="w")
        
        command_entry = ctk.CTkEntry(
            dialog,
            width=460,
            height=35,
            fg_color="#2A2A35",
            text_color=TEXT_PRIMARY
        )
        command_entry.pack(padx=20)
        
        # Buttons
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        def on_add():
            name = name_entry.get().strip()
            command = command_entry.get().strip()
            
            if not name or not command:
                messagebox.showerror("Invalid Input", "Please fill in all fields")
                return
            
            success, msg = self.manager.add_app(name, command)
            if success:
                messagebox.showinfo("Success", msg)
                self.load_startup_apps()
                dialog.destroy()
            else:
                messagebox.showerror("Error", msg)
        
        ctk.CTkButton(
            btn_frame,
            text="Add",
            command=on_add,
            fg_color=ACCENT_ORANGE,
            hover_color="#cc5500",
            width=100
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=dialog.destroy,
            fg_color="#555",
            hover_color="#666",
            width=100
        ).pack(side="left", padx=5)
        
        # Focus on name entry
        name_entry.focus()
    
    def remove_startup_app(self):
        """Remove the selected startup app"""
        app = self.get_selected_app()
        if not app:
            return
        
        result = messagebox.askyesno(
            "Confirm Removal",
            f"Are you sure you want to remove '{app['name']}' from startup applications?"
        )
        
        if result:
            success, msg = self.manager.remove_app(app['path'])
            if success:
                messagebox.showinfo("Success", msg)
                self.load_startup_apps()
            else:
                messagebox.showerror("Error", msg)
