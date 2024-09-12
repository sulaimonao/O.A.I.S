import serial.tools.list_ports

def list_usb_devices():
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]

def connect_to_device(device_name):
    # Logic to connect to the selected USB device
    pass
