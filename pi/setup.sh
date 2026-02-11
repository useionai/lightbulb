#!/bin/bash
# Setup script for Lightbulb on Raspberry Pi Zero 2 W

set -e

echo "Installing system dependencies..."

# Update package list
sudo apt-get update

# Install audio dependencies for PyAudio
sudo apt-get install -y \
    portaudio19-dev \
    python3-pyaudio \
    libasound2-dev \
    libportaudio2

# Install dependencies for rpi_ws281x
sudo apt-get install -y \
    build-essential \
    python3-dev \
    swig

# Install OpenBLAS for numpy
sudo apt-get install -y libopenblas-dev

# Install Python venv if not present
sudo apt-get install -y python3-venv

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate and install Python packages
echo "Installing Python packages..."
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

# Install openwakeword without auto-pulling onnxruntime (we handle it below)
echo "Installing openwakeword..."
./venv/bin/pip install openwakeword --no-deps
./venv/bin/pip install scikit-learn

# Install onnxruntime for wake word inference
# ARM (Raspberry Pi) requires special handling - no PyPI wheels for 32-bit
echo "Installing onnxruntime..."
ARCH=$(uname -m)
if [ "$ARCH" = "aarch64" ]; then
    # 64-bit Pi OS: official wheels available on PyPI
    ./venv/bin/pip install onnxruntime
elif [ "$ARCH" = "armv7l" ] || [ "$ARCH" = "armv6l" ]; then
    # 32-bit Pi OS: no official wheels, install from community builds
    echo "WARNING: 32-bit OS detected. onnxruntime has no official ARM32 wheels."
    echo "Attempting to install from piwheels..."
    ./venv/bin/pip install onnxruntime --extra-index-url https://www.piwheels.org/simple || {
        echo ""
        echo "ERROR: onnxruntime installation failed."
        echo "Options to fix this:"
        echo "  1. (Recommended) Reinstall Raspberry Pi OS 64-bit (aarch64)"
        echo "     then re-run this script."
        echo "  2. Build onnxruntime from source (slow, may need swap space):"
        echo "     ./venv/bin/pip install --no-cache-dir onnxruntime"
        echo ""
        echo "Wake word detection will not work until onnxruntime is installed."
    }
else
    # Other architectures (Mac dev machine, etc.)
    ./venv/bin/pip install onnxruntime
fi

# Download openWakeWord's built-in models (melspectrogram, embedding, etc.)
echo "Downloading openWakeWord base models..."
./venv/bin/python -c "import openwakeword; openwakeword.utils.download_models()"

# Enable SPI and audio
echo "Configuring Raspberry Pi..."
sudo raspi-config nonint do_spi 0

# Add user to audio group for microphone access
sudo usermod -a -G audio $USER

# Create models directory
mkdir -p lightbulb/models

# Install and enable systemd service
echo "Installing systemd service..."
sudo cp lightbulb.service /etc/systemd/system/lightbulb.service
sudo systemctl daemon-reload
sudo systemctl enable lightbulb.service

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Ensure the wake word model is at: lightbulb/models/i_have_an_idea.onnx"
echo "2. Connect your USB microphone"
echo "3. Start the service: sudo systemctl start lightbulb"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status lightbulb   # Check status"
echo "  sudo journalctl -u lightbulb -f   # View logs"
echo "  sudo systemctl restart lightbulb  # Restart"
echo "  sudo systemctl stop lightbulb     # Stop"
