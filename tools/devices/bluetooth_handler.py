import bluetooth

def search_bluetooth_devices():
    devices = bluetooth.discover_devices(lookup_names=True)
    return devices

def connect_bluetooth_device(device_address):
    # Logic to connect to the selected Bluetooth device
    pass
