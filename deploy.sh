#!/bin/bash
# Deploy Lightbulb to Raspberry Pi

set -e

PI_USER="bengrande"
PI_HOST="lightbulb.local"
PI_DEST="/home/bengrande/lightbulb"

echo "Deploying Lightbulb to ${PI_USER}@${PI_HOST}..."

# Create destination directory on Pi
ssh ${PI_USER}@${PI_HOST} "mkdir -p ${PI_DEST}"

# Upload all files from pi/ directory
scp -r pi/* ${PI_USER}@${PI_HOST}:${PI_DEST}/

echo ""
echo "Deployment complete!"
echo ""
echo "Next steps on the Raspberry Pi:"
echo "  1. cd ${PI_DEST}"
echo "  2. chmod +x setup.sh && ./setup.sh"
echo "  3. sudo ./venv/bin/python -m lightbulb.main"
