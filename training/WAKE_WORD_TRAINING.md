# Wake Word Training Guide

This guide explains how to train a custom wake word model for "I have an idea" using openWakeWord.

## Overview

openWakeWord uses synthetic audio generation and neural network training to create custom wake word models. The process involves:

1. Generating synthetic speech samples of your wake phrase
2. Training a neural network to recognize the phrase
3. Exporting the model as a TensorFlow Lite file

## Prerequisites

- Google account (for Google Colab)
- ~30-60 minutes for training

## Training Steps

### 1. Open the Training Notebook

Visit the openWakeWord GitHub repository and open the training notebook in Google Colab:

https://github.com/dscripka/openWakeWord

Look for the training notebook in the `notebooks/` directory, or use this direct link:
https://colab.research.google.com/github/dscripka/openWakeWord/blob/main/notebooks/automatic_model_training.ipynb

### 2. Configure the Wake Phrase

In the notebook, find the cell where you set the target phrase and configure it as:

```python
target_phrase = "i have an idea"
```

### 3. Generate Synthetic Training Data

The notebook will guide you through generating synthetic audio samples. For best results:

- Generate at least **2000 positive samples** (the wake phrase)
- Generate negative samples (other phrases) for contrast
- Use multiple voice styles and speeds

The notebook uses text-to-speech engines to create diverse training data automatically.

### 4. Train the Model

Run the training cells in the notebook. This typically takes:

- **30-60 minutes** on a free Colab GPU
- Longer if generating more samples

Monitor the training loss and accuracy metrics.

### 5. Export the Model

After training completes, export the model as a TensorFlow Lite file:

1. Run the export cell in the notebook
2. Download the `.tflite` file to your computer
3. Rename it to `i_have_an_idea.tflite`

### 6. Deploy to Raspberry Pi

Copy the model file to your Raspberry Pi:

```bash
# From your computer
scp i_have_an_idea.tflite pi@lightbulb.local:~/lightbulb/lightbulb/models/

# Or if using SCP with IP address
scp i_have_an_idea.tflite pi@192.168.x.x:~/lightbulb/lightbulb/models/
```

The model should be placed at:
```
lightbulb/
└── lightbulb/
    └── models/
        └── i_have_an_idea.tflite
```

## Configuration

After deploying the model, verify the configuration in `config.yaml`:

```yaml
wake_word:
  model_path: "lightbulb/models/i_have_an_idea.tflite"
  threshold: 0.5        # Adjust if needed (0.0-1.0)
  cooldown_seconds: 3.0 # Minimum time between detections
```

### Threshold Tuning

- **Higher threshold (0.6-0.8)**: Fewer false positives, but may miss some detections
- **Lower threshold (0.3-0.5)**: More sensitive, but may trigger on similar phrases

Start with 0.5 and adjust based on your experience.

## Testing

After deploying the model, test it:

```bash
# Run the hardware test
sudo ./venv/bin/python scripts/test_hardware.py

# Or start the full application
sudo ./venv/bin/python -m lightbulb.main
```

Then say "I have an idea" clearly. The LEDs should turn yellow if detection is successful.

## Troubleshooting

### Model Not Detected

- Verify the model file exists at the configured path
- Check file permissions: `chmod 644 lightbulb/models/i_have_an_idea.tflite`

### False Positives

- Increase the threshold in `config.yaml`
- Retrain with more diverse negative samples

### Missed Detections

- Decrease the threshold (but not below 0.3)
- Check microphone placement and volume
- Retrain with more positive samples
- Speak more clearly and consistently

### Audio Issues

- Run `scripts/test_hardware.py` to verify microphone works
- Check USB microphone is connected
- Verify audio permissions: `sudo usermod -a -G audio $USER`

## Alternative Models

If you don't want to train a custom model, openWakeWord includes pre-trained models for common wake words like "hey jarvis", "alexa", etc. However, for "I have an idea", a custom model is required.

## Resources

- [openWakeWord GitHub](https://github.com/dscripka/openWakeWord)
- [openWakeWord Documentation](https://github.com/dscripka/openWakeWord#readme)
- [Training Notebook](https://colab.research.google.com/github/dscripka/openWakeWord/blob/main/notebooks/automatic_model_training.ipynb)
