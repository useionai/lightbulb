#!/bin/bash
# Build and run wake word training in Docker

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Building Docker Image ==="
docker build -t openwakeword-trainer .

echo ""
echo "=== Starting Training Container ==="
echo "This will take a while (30-60 minutes)..."
echo "The trained model will be saved to: $SCRIPT_DIR/output/"
echo ""

mkdir -p output
mkdir -p cache
mkdir -p generated_clips

docker run --rm --shm-size=2g --cpus=1 -e OMP_NUM_THREADS=1 \
    -v "$SCRIPT_DIR/train_wakeword.py:/app/train_wakeword.py:ro" \
    -v "$SCRIPT_DIR/output:/output" \
    -v "$SCRIPT_DIR/cache:/app/cache" \
    -v "$SCRIPT_DIR/generated_clips:/app/my_custom_model" \
    openwakeword-trainer \
    python /app/train_wakeword.py

echo ""
echo "=== Training Complete ==="
echo "Model location: $SCRIPT_DIR/output/i_have_an_idea.tflite"
echo ""
echo "To deploy to your Pi:"
echo "  scp output/i_have_an_idea.tflite pi@lightbulb.local:~/lightbulb/lightbulb/models/"
