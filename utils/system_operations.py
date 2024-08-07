import usb.core
import usb.util
import cv2
import pyaudio
import wave
import subprocess
from bleak import BleakScanner

# Example function to list USB devices
def list_usb_devices():
    devices = usb.core.find(find_all=True)
    return [usb.util.get_string(dev, dev.iProduct) for dev in devices]

# Example function to list Bluetooth devices using bleak
async def list_bluetooth_devices():
    devices = await BleakScanner.discover()
    return [f"{device.address} - {device.name}" for device in devices]

# Example function to capture an image from the webcam
def capture_image():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    if ret:
        cv2.imwrite('capture.jpg', frame)
    cap.release()
    return 'capture.jpg'

# Example function to record audio
def record_audio(duration=5, filename='recording.wav'):
    audio = pyaudio.PyAudio()
    stream = audio.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
    frames = []
    for i in range(0, int(44100 / 1024 * duration)):
        data = stream.read(1024)
        frames.append(data)
    stream.stop_stream()
    stream.close()
    audio.terminate()
    waveFile = wave.open(filename, 'wb')
    waveFile.setnchannels(1)
    waveFile.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
    waveFile.setframerate(44100)
    waveFile.writeframes(b''.join(frames))
    waveFile.close()
    return filename

# Example function to execute OS commands
def execute_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout
