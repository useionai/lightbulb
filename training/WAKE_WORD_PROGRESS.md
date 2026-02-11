# Wake Word Training Progress

## Status: Complete (ONNX format)

The wake word model for "i have an idea" has been successfully trained and exported to ONNX format.

**Output:** `training/output/i_have_an_idea.onnx` (205KB)

## What Was Done

1. **Set up Docker-based training environment** - Required because openWakeWord training only supports Linux (uses Piper TTS for synthetic speech generation)

2. **Generated synthetic training data:**
   - 1500 positive clips ("i have an idea")
   - 300 validation clips
   - Adversarial negative clips
   - Augmented with noise/reverb using MIT room impulse responses

3. **Trained neural network** - 10,000 training steps

4. **Exported model** - ONNX format (TFLite conversion failed)

## Limitations & Issues Encountered

### Memory Constraints
- Docker on Mac has limited RAM (~7.6GB available)
- Training crashes with `return code -9` (killed by OOM) when using multiple CPU workers
- **Solution:** Limited to 1 CPU (`--cpus=1`) and set `OMP_NUM_THREADS=1`
- Reduced samples from 3000 to 1500, training steps from 15000 to 10000

### TFLite Conversion Failed
- `onnx_tf` module has version conflicts with newer ONNX/TensorFlow
- `onnx2tf` requires cmake and has build issues
- **Workaround:** Use ONNX model directly - openWakeWord supports both formats

### Dependency Hell
- Specific version pinning required for torch/torchaudio (2.0.1/2.0.2) to work with torch-audiomentations
- Must use dscripka's fork of piper-sample-generator (not rhasspy's)
- Model file `en-us-libritts-high.pt` only available in v1.0.0 release

## File Structure

```
training/
├── Dockerfile              # Docker environment with all dependencies
├── train_wakeword.py       # Training orchestration script
├── run_training.sh         # One-command build & train
├── cache/                  # Cached datasets (persists between runs)
│   ├── mit_rirs/          # Room impulse responses
│   ├── fma/               # Background audio
│   └── *.npy              # Pre-computed features (~16GB)
├── generated_clips/        # Generated synthetic clips (persists)
│   └── i_have_an_idea/
│       ├── positive_train/
│       ├── positive_test/
│       ├── negative_train/
│       └── negative_test/
├── output/                 # Final trained model
│   └── i_have_an_idea.onnx
└── openWakeWord/          # Cloned repo
```

## Run Instructions

### Prerequisites
- Docker Desktop running
- At least 8GB RAM allocated to Docker (Settings → Resources → Memory)

### To Train a New Model

1. **Start training:**
   ```bash
   cd /Users/grandebrothers/Code/personalbranding/lightbulb/training
   ./run_training.sh
   ```

2. **Prevent Mac sleep (in separate terminal):**
   ```bash
   caffeinate -di
   ```

3. **Monitor progress:**
   ```bash
   # Find the output file from the command output, then:
   tail -f /private/tmp/claude/.../tasks/<task_id>.output

   # Or check percentage:
   grep -oE "Training: +[0-9]+%" <output_file> | tail -1
   ```

4. **If it crashes (memory):**
   - Clips are cached in `generated_clips/` - won't regenerate
   - Just run `./run_training.sh` again
   - Training restarts from step 0 (no mid-training checkpoints)

### To Modify Training Parameters

Edit `train_wakeword.py`:
```python
TARGET_PHRASE = "i have an idea"  # Change wake phrase
N_SAMPLES = 1500                   # Training samples
N_SAMPLES_VAL = 300                # Validation samples
TRAINING_STEPS = 10000             # Training iterations
```

### Docker Resource Settings

Current `run_training.sh` settings optimized for memory-constrained Mac:
```bash
docker run --rm --shm-size=2g --cpus=1 -e OMP_NUM_THREADS=1 ...
```

- `--shm-size=2g` - Shared memory for PyTorch DataLoader
- `--cpus=1` - Limits workers to reduce memory
- `OMP_NUM_THREADS=1` - Single-threaded operations

## Deploying to Raspberry Pi

### Option 1: Use ONNX (Recommended)

1. Update `pi/requirements.txt`:
   ```
   # Remove: tflite-runtime
   # Add:
   onnxruntime
   ```

2. Copy model:
   ```bash
   scp training/output/i_have_an_idea.onnx pi@lightbulb.local:~/lightbulb/lightbulb/models/
   ```

3. Update `pi/config.yaml`:
   ```yaml
   wake_word:
     model_path: "lightbulb/models/i_have_an_idea.onnx"
   ```

### Option 2: Convert to TFLite (If Needed)

Would require fixing onnx_tf dependency issues or using Google Colab for conversion.

## Future Improvements

- [ ] Add mid-training checkpoints to resume interrupted training
- [ ] Fix TFLite conversion pipeline
- [ ] Test model accuracy on real hardware
- [ ] Tune detection threshold based on false positive rate
