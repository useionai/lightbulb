# Lightbulb

WS281x LED Controller with Flask API and Wake Word Detection for Raspberry Pi Zero 2 W.

## Project Structure

```
lightbulb/
├── deploy.sh          # Deploy to Raspberry Pi
├── pi/                # Raspberry Pi application
│   ├── lightbulb/     # Python package
│   ├── scripts/       # Test scripts
│   ├── config.yaml    # Configuration
│   ├── requirements.txt
│   └── setup.sh       # System setup
├── training/          # Wake word training resources
│   └── WAKE_WORD_TRAINING.md
└── TVLights/          # Legacy TV lights project
```

## Raspberry Pi Setup

Bookworm without desktop environment (legacy lite)

```bash
ssh bengrande@lightbulb.local
```

## Deployment

```bash
./deploy.sh
```

Then on the Pi:
```bash
cd ~/lightbulb
chmod +x setup.sh && ./setup.sh
sudo ./venv/bin/python -m lightbulb.main
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/leds` | GET | Get current LED state |
| `/api/leds/<index>` | PUT | Set individual LED |
| `/api/leds` | PUT | Set all LEDs to same color |
| `/api/scenes` | GET | List available scenes |
| `/api/scenes/<name>` | POST | Activate a scene |
| `/api/brightness` | GET/PUT | Get or set brightness |
