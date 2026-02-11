"""Configuration loader for Lightbulb."""

import os
from pathlib import Path
from typing import Any

import yaml


def load_config(config_path: str | None = None) -> dict[str, Any]:
    """Load configuration from YAML file.

    Args:
        config_path: Path to config file. Defaults to config.yaml in project root.

    Returns:
        Configuration dictionary.
    """
    if config_path is None:
        # Default to config.yaml in project root
        project_root = Path(__file__).parent.parent
        config_path = project_root / "config.yaml"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    return config


class Config:
    """Configuration singleton for easy access throughout the application."""

    _instance: "Config | None" = None
    _config: dict[str, Any] = {}

    def __new__(cls, config_path: str | None = None) -> "Config":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = load_config(config_path)
        return cls._instance

    @property
    def led(self) -> dict[str, Any]:
        """LED configuration."""
        return self._config.get("led", {})

    @property
    def audio(self) -> dict[str, Any]:
        """Audio configuration."""
        return self._config.get("audio", {})

    @property
    def wake_word(self) -> dict[str, Any]:
        """Wake word configuration."""
        return self._config.get("wake_word", {})

    @property
    def api(self) -> dict[str, Any]:
        """API configuration."""
        return self._config.get("api", {})

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance (useful for testing)."""
        cls._instance = None
        cls._config = {}
