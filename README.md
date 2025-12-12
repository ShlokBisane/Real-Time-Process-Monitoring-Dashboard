🌌 System Monitoring Dashboard
A Modern, Real-Time Performance & Process Monitoring Suite for Windows
<p align="center"> <img src="https://img.shields.io/badge/Platform-Windows%2010%2F11-blue?style=for-the-badge"> <img src="https://img.shields.io/badge/GUI-CustomTkinter-orange?style=for-the-badge"> <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge"> <img src="https://img.shields.io/badge/Status-Active%20Development-purple?style=for-the-badge"> </p> <p align="center"> <img src="https://img.shields.io/github/stars/yourusername/yourrepo?style=social"> </p>
✨ Overview

The System Monitoring Dashboard is a sleek, real-time monitoring application with a premium UI inspired by modern OS dashboards.
Crafted using CustomTkinter, Matplotlib, and Psutil, it visualizes your entire system in an elegant dark theme with vibrant accents.

It tracks:
✔ CPU usage
✔ RAM usage
✔ Disk usage
✔ Network upload/download
✔ GPU load (if available)
✔ Running Processes (App + System)
✔ Startup Applications (from Windows Registry)

All wrapped in a smooth, animated, gradient-enhanced, real-time dashboard.

🚀 Features
🖥️ Performance Monitoring

Real-time graphs updating every 250ms

Gradient-filled plots for CPU, GPU, Memory, Disk, and Network

Dedicated color theme per graph

Mini metric cards with live percentage bars

Network I/O graphs with download & upload lines

<p align="center"> <img src="https://img.icons8.com/fluency/48/dashboard.png"/> </p>
⚙️ Process Manager
<p align="center"> <img src="https://img.icons8.com/fluency/48/task-manager.png"/> </p>

Divided into Application and System processes

Fast-loading tables with alternating row colors

Kill or suspend processes directly

Smooth UI matching performance tab theme

Auto-refresh every 1.5 seconds

🟢 Startup Applications Manager
<p align="center"> <img src="https://img.icons8.com/emoji/48/rocket-emoj.png"/> </p>

Reads Windows' startup registry keys

Beautiful full-screen table for:
✓ Name
✓ Command path
✓ Registry location
✓ Enabled state

“Open Location” button opens executable folder directly

🛠️ Tech Stack
Component	Technology
UI Framework	CustomTkinter
System Info	psutil, GPUtil (optional)
Graphing	Matplotlib
OS Integration	Windows Registry
Rendering	Dark Mode + Neon Accents
📦 Installation
1️⃣ Clone the Repository
git clone https://github.com/yourusername/yourrepo.git
cd yourrepo

2️⃣ Install Dependencies
pip install customtkinter matplotlib psutil pillow
pip install gputil   # optional

3️⃣ Run the Application
python main.py

📁 Project Structure
main.py
modules/
│── performance/
│     └── ui.py
│── processes/
│     └── ui.py
│── startup/
│     └── ui.py
│── styles.py
assets/
README.md

🎨 UI Theme

The UI is powered by:

Clean midnight-dark background

Vibrant accent colors

Smooth rounded cards with shadows

High-contrast white typography

The dashboard aesthetic resembles a mix of Task Manager + ROG Armory Crate + macOS Activity Monitor.

🔥 Why This Project Stands Out

Not a basic Tkinter app — looks premium

Super fast updates (0.25-sec refresh)

Modular codebase for easy extension

Runs without admin privileges (except optional process actions)

Looks insane on 1080p / 1440p / 4K monitors

🧩 Planned Features (Future Updates)

CPU/GPU temperature graphs

GPU VRAM usage (detailed)

Process grouping like Windows Task Manager

Search bar for processes

Import/export custom themes

Logging & analytics export

🤝 Contributing

Pull requests are welcome!
Feel free to fork the project and improve modules, UI, or performance.

📜 License

This project is under the MIT License — free for personal and commercial use.

⭐ Support the Project

If you found this project useful or beautiful, star the repo:

<p align="center"> <img src="https://img.icons8.com/color/48/star--v1.png"/> </p>
