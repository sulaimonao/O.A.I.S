import os
import psutil

def system_health_check():
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    disk_info = psutil.disk_usage('/')
    return {
        "CPU Usage": f"{cpu_usage}%",
        "Memory": f"{memory_info.percent}%",
        "Disk Space": f"{disk_info.percent}% used"
    }

def map_file_system():
    root_dir = "/"
    directory_structure = []
    for root, dirs, files in os.walk(root_dir):
        directory_structure.append({"root": root, "dirs": dirs, "files": files})
    return directory_structure
