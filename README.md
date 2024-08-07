# O.A.I.S

![O.A.I.S Logo](static/images/logo.png)

## Overview

O.A.I.S is an AI-powered system designed for dynamic interactions and integrations. The project leverages advanced language models and various tools to provide an extensible platform for development.

## Features

- **Dynamic Code Generation:** Generate and execute code on the fly using OpenAI models.
- **Database Management**
- **User Profiles**
- **File Operations**
- **Hardware Interaction:** List USB devices, discover Bluetooth devices, capture images from the webcam, and record audio.
- **Extensible and Modular:** Easily extend the system with additional functionality and integrations.

## Setup

### Prerequisites

- Python 3.8 or higher
- pip
- [Homebrew](https://brew.sh/) (for macOS)

### Installation

1. Clone the repository:

    ```sh
    git clone https://github.com/sulaimonao/O.A.I.S.git
    cd O.A.I.S
    ```

2. Create a virtual environment and activate it:

    ```sh
    python -m venv venv
    source venv/bin/activate
    ```

3. Install dependencies:

    ```sh
    pip install -r requirements.txt
    ```

4. Initialize the database:

    ```sh
    python -m utils.database
    ```

5. Install additional system dependencies (macOS):

    ```sh
    brew install portaudio
    ```

6. Run the application:

    ```sh
    python app.py
    ```

## Usage

### Running the Application

1. Start the application by running:

    ```sh
    python app.py
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
   Add new functions in the `utils/` directory and integrate them into `app.py`.

## Contributing

Contributions are welcome! Please follow these steps to contribute:

## License

[MIT License](LICENSE)

## Acknowledgments

- [OpenAI](https://www.openai.com/)
- [Gemini](https://www.gemini.google.com/)
- [Homebrew](https://brew.sh/) for managing macOS packages.
- [Flask](https://flask.palletsprojects.com/) for providing a lightweight web framework.
