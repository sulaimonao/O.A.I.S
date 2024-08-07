# O.A.I.S

![O.A.I.S Logo](static/images/logo1.png)

## Project Description

O.A.I.S is a powerful and flexible system designed to integrate language models with various tools and technologies. The system allows for dynamic code generation, file operations, hardware interactions, and much more.

## Features

- **Dynamic Code Generation:** Generate and execute code on the fly using OpenAI models.
- **File Operations:** Read, write, and manage files within the system.
- **Hardware Interaction:** List USB devices, discover Bluetooth devices, capture images from the webcam, and record audio.
- **User Profile Management:** Store and retrieve user profiles for personalized interactions.
- **Extensible and Modular:** Easily extend the system with additional functionality and integrations.

## Installation

### Prerequisites

- Python 3.8 or higher
- [pip](https://pip.pypa.io/en/stable/installation/)
- [Homebrew](https://brew.sh/) (for macOS)

### Step-by-Step Guide

1. **Clone the repository:**

    ```sh
    git clone https://github.com/sulaimonao/O.A.I.S.git
    cd O.A.I.S
    ```

2. **Set up a virtual environment:**

    ```sh
    python3 -m venv env
    source env/bin/activate
    ```

3. **Install the dependencies:**

    ```sh
    pip install -r requirements.txt
    ```

4. **Install additional system dependencies (macOS):**

    ```sh
    brew install portaudio
    ```

5. **Run the application:**

    ```sh
    python main.py
    ```

## Usage

### Running the Application

1. Start the application by running:

    ```sh
    python main.py
    ```

2. Open your web browser and navigate to `http://localhost:5000`.

3. Interact with the system through the web interface.

### Available Endpoints

- `/list_usb_devices`: List connected USB devices.
- `/list_bluetooth_devices`: Discover nearby Bluetooth devices.
- `/capture_image`: Capture an image from the webcam.
- `/record_audio`: Record audio from the microphone.
- `/execute_command`: Execute OS commands.

### Customizing the System

1. **Modifying Configurations:**
<<<<<<< Updated upstream
   Edit the `config.py` and '.env' files to update API keys and other configurations.
=======

2. **Adding New Functionality:**
   Add new functions in the `tools/` directory and integrate them into `main.py`.

## Contributing

Contributions are welcome! Please follow these steps to contribute:

## License

This project has no LICENSE

## Acknowledgments

- [OpenAI](https://www.openai.com/) for their powerful language models.
- [Gemini](https://www.gemini.google.com/) for their powerful language models.
- [Homebrew](https://brew.sh/) for managing macOS packages.
- [Flask](https://flask.palletsprojects.com/) for providing a lightweight web framework.
