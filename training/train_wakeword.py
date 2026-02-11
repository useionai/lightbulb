#!/usr/bin/env python3
"""
Train a custom wake word model for "I have an idea"
Run this inside the Docker container.
"""

import os
import sys
import yaml
import subprocess
from pathlib import Path

# Configuration
TARGET_PHRASE = "i have an idea"
MODEL_NAME = "i_have_an_idea"
N_SAMPLES = 1500  # Number of synthetic samples to generate (reduced for memory)
N_SAMPLES_VAL = 300  # Validation samples
TRAINING_STEPS = 10000

def download_datasets():
    """Download required training datasets with caching."""
    import datasets
    import scipy.io.wavfile
    import numpy as np
    from tqdm import tqdm
    import shutil

    # Use cache directory for persistence between runs
    cache_dir = "/app/cache"
    os.makedirs(cache_dir, exist_ok=True)

    print("\n=== Downloading Room Impulse Responses ===")
    cache_rirs = os.path.join(cache_dir, "mit_rirs")
    output_dir = "./mit_rirs"
    if os.path.exists(cache_rirs) and os.listdir(cache_rirs):
        print("Found in cache, copying...")
        if not os.path.exists(output_dir):
            shutil.copytree(cache_rirs, output_dir)
    elif not os.path.exists(output_dir):
        os.makedirs(output_dir)
        rir_dataset = datasets.load_dataset(
            "davidscripka/MIT_environmental_impulse_responses",
            split="train",
            streaming=True
        )
        for row in tqdm(rir_dataset):
            name = row['audio']['path'].split('/')[-1]
            scipy.io.wavfile.write(
                os.path.join(output_dir, name),
                16000,
                (row['audio']['array']*32767).astype(np.int16)
            )
        # Cache for next time
        shutil.copytree(output_dir, cache_rirs)
    else:
        print("Already downloaded, skipping...")

    print("\n=== Downloading Background Audio (FMA) ===")
    cache_fma = os.path.join(cache_dir, "fma")
    output_dir = "./fma"
    if os.path.exists(cache_fma) and os.listdir(cache_fma):
        print("Found in cache, copying...")
        if not os.path.exists(output_dir):
            shutil.copytree(cache_fma, output_dir)
    elif not os.path.exists(output_dir):
        os.makedirs(output_dir)
        fma_dataset = datasets.load_dataset(
            "rudraml/fma",
            name="small",
            split="train",
            streaming=True
        )
        fma_dataset = iter(fma_dataset.cast_column("audio", datasets.Audio(sampling_rate=16000)))

        n_hours = 2  # 2 hours of background audio
        for i in tqdm(range(n_hours * 3600 // 30)):
            try:
                row = next(fma_dataset)
                name = row['audio']['path'].split('/')[-1].replace(".mp3", ".wav")
                scipy.io.wavfile.write(
                    os.path.join(output_dir, name),
                    16000,
                    (row['audio']['array']*32767).astype(np.int16)
                )
            except StopIteration:
                break
        # Cache for next time
        shutil.copytree(output_dir, cache_fma)
    else:
        print("Already downloaded, skipping...")

    print("\n=== Downloading Pre-computed Features ===")
    features_file = "openwakeword_features_ACAV100M_2000_hrs_16bit.npy"
    cache_features = os.path.join(cache_dir, features_file)
    if os.path.exists(cache_features):
        print("Found in cache, linking...")
        if not os.path.exists(features_file):
            os.symlink(cache_features, features_file)
    elif not os.path.exists(features_file):
        subprocess.run([
            "wget", "-q", "--show-progress",
            f"https://huggingface.co/datasets/davidscripka/openwakeword_features/resolve/main/{features_file}",
            "-O", cache_features
        ])
        os.symlink(cache_features, features_file)

    val_file = "validation_set_features.npy"
    cache_val = os.path.join(cache_dir, val_file)
    if os.path.exists(cache_val):
        print("Found in cache, linking...")
        if not os.path.exists(val_file):
            os.symlink(cache_val, val_file)
    elif not os.path.exists(val_file):
        subprocess.run([
            "wget", "-q", "--show-progress",
            f"https://huggingface.co/datasets/davidscripka/openwakeword_features/resolve/main/{val_file}",
            "-O", cache_val
        ])
        os.symlink(cache_val, val_file)

def create_config():
    """Create training configuration."""
    print("\n=== Creating Training Config ===")

    # Load default config
    config_path = "openWakeWord/examples/custom_model.yml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Modify for our wake phrase
    config["target_phrase"] = [TARGET_PHRASE]
    config["model_name"] = MODEL_NAME
    config["n_samples"] = N_SAMPLES
    config["n_samples_val"] = N_SAMPLES_VAL
    config["steps"] = TRAINING_STEPS
    config["target_accuracy"] = 0.7
    config["target_recall"] = 0.5

    config["background_paths"] = ['./fma']
    config["rir_paths"] = ['./mit_rirs']
    config["tts_batch_size"] = 10  # Reduced for memory constraints
    config["false_positive_validation_data_path"] = "validation_set_features.npy"
    config["feature_data_files"] = {
        "ACAV100M_sample": "openwakeword_features_ACAV100M_2000_hrs_16bit.npy"
    }

    # Save config
    with open('training_config.yaml', 'w') as f:
        yaml.dump(config, f)

    print(f"Config saved to training_config.yaml")
    print(f"  Target phrase: {TARGET_PHRASE}")
    print(f"  Samples: {N_SAMPLES} training, {N_SAMPLES_VAL} validation")
    print(f"  Training steps: {TRAINING_STEPS}")

def train():
    """Run the training pipeline."""
    python = sys.executable

    print("\n=== Step 1: Generating Synthetic Clips ===")
    result = subprocess.run([
        python, "openWakeWord/openwakeword/train.py",
        "--training_config", "training_config.yaml",
        "--generate_clips"
    ])
    if result.returncode != 0:
        print(f"Step 1 failed with return code {result.returncode}")
        sys.exit(1)

    print("\n=== Step 2: Augmenting Clips ===")
    result = subprocess.run([
        python, "openWakeWord/openwakeword/train.py",
        "--training_config", "training_config.yaml",
        "--augment_clips"
    ])
    if result.returncode != 0:
        print(f"Step 2 failed with return code {result.returncode}")
        sys.exit(1)

    print("\n=== Step 3: Training Model ===")
    result = subprocess.run([
        python, "openWakeWord/openwakeword/train.py",
        "--training_config", "training_config.yaml",
        "--train_model"
    ])
    if result.returncode != 0:
        print(f"Step 3 failed with return code {result.returncode}")
        sys.exit(1)

def copy_output():
    """Copy the trained model to output directory."""
    print("\n=== Copying Model to Output ===")
    import shutil

    model_dir = f"my_custom_model"
    output_dir = "/output"

    for ext in ['.tflite', '.onnx']:
        src = f"{model_dir}/{MODEL_NAME}{ext}"
        if os.path.exists(src):
            dst = f"{output_dir}/{MODEL_NAME}{ext}"
            shutil.copy(src, dst)
            print(f"Copied: {src} -> {dst}")
        else:
            print(f"Warning: {src} not found")

def main():
    os.chdir("/app")

    print("=" * 60)
    print(f"Training Wake Word Model: '{TARGET_PHRASE}'")
    print("=" * 60)

    download_datasets()
    create_config()
    train()
    copy_output()

    print("\n" + "=" * 60)
    print("Training complete!")
    print(f"Model saved to: /output/{MODEL_NAME}.tflite")
    print("=" * 60)

if __name__ == "__main__":
    main()
