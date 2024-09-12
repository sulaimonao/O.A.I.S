import platform

def get_os_type():
    return platform.system()

def perform_os_specific_action():
    if get_os_type() == 'Windows':
        # Windows-specific code
        pass
    elif get_os_type() == 'Linux':
        # Linux-specific code
        pass
    elif get_os_type() == 'Darwin':  # macOS
        # macOS-specific code
        pass
