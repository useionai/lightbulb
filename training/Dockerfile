FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    build-essential \
    libsndfile1 \
    ffmpeg \
    espeak-ng \
    && rm -rf /var/lib/apt/lists/*

# Clone dscripka's fork of piper-sample-generator (compatible with openWakeWord)
RUN git clone https://github.com/dscripka/piper-sample-generator && \
    mkdir -p piper-sample-generator/models && \
    wget -O piper-sample-generator/models/en-us-libritts-high.pt \
    'https://github.com/rhasspy/piper-sample-generator/releases/download/v1.0.0/en-us-libritts-high.pt'

# Install torch and torchaudio FIRST with specific compatible versions
RUN pip install --no-cache-dir \
    torch==2.0.1 \
    torchaudio==2.0.2 \
    piper-tts \
    espeak-phonemizer

# Install other Python dependencies
RUN pip install --no-cache-dir \
    piper-phonemize \
    webrtcvad \
    mutagen==1.47.0 \
    torchinfo==1.8.0 \
    torchmetrics==1.2.0 \
    speechbrain==0.5.14 \
    audiomentations==0.33.0 \
    torch-audiomentations==0.11.0 \
    acoustics==0.2.6 \
    pronouncing==0.2.0 \
    datasets==2.14.6 \
    pyarrow==14.0.1 \
    deep-phonemizer==0.0.19 \
    scipy \
    tqdm \
    pyyaml \
    numpy

# Install TensorFlow (CPU version for conversion) - use version compatible with ARM64
RUN pip install --no-cache-dir tensorflow==2.15.0 tensorflow_probability

# Install ONNX conversion tools
RUN pip install --no-cache-dir onnx tf2onnx

# Clone and install openWakeWord
RUN git clone https://github.com/dscripka/openWakeWord && \
    pip install -e ./openWakeWord

# Download required models
RUN mkdir -p ./openWakeWord/openwakeword/resources/models && \
    wget https://github.com/dscripka/openWakeWord/releases/download/v0.5.1/embedding_model.onnx \
        -O ./openWakeWord/openwakeword/resources/models/embedding_model.onnx && \
    wget https://github.com/dscripka/openWakeWord/releases/download/v0.5.1/embedding_model.tflite \
        -O ./openWakeWord/openwakeword/resources/models/embedding_model.tflite && \
    wget https://github.com/dscripka/openWakeWord/releases/download/v0.5.1/melspectrogram.onnx \
        -O ./openWakeWord/openwakeword/resources/models/melspectrogram.onnx && \
    wget https://github.com/dscripka/openWakeWord/releases/download/v0.5.1/melspectrogram.tflite \
        -O ./openWakeWord/openwakeword/resources/models/melspectrogram.tflite

# Create output directory
RUN mkdir -p /output

CMD ["/bin/bash"]
