"""
Configuration handling for i3ctl.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from i3ctl.utils.logger import logger

# Configuration paths - made as variables for easier testing
CONFIG_DIR = os.path.expanduser("~/.config/i3ctl")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

# Default configuration
DEFAULT_CONFIG = {
    "i3_config_path": os.path.expanduser("~/.config/i3/config"),
    "editor": os.environ.get("EDITOR", "nano"),
    "brightness_tool": "auto",  # auto, xbacklight, or brightnessctl
    "volume_tool": "auto",  # auto, pulseaudio, or alsa
    "wallpaper_tool": "auto",  # auto, feh, or nitrogen
    "log_level": "INFO",
    "log_file": os.path.join(CONFIG_DIR, "i3ctl.log"),
}


def ensure_config_dir() -> None:
    """
    Ensure the configuration directory exists.
    """
    os.makedirs(CONFIG_DIR, exist_ok=True)


def load_config() -> Dict[str, Any]:
    """
    Load configuration from file, creating default if it doesn't exist.

    Returns:
        Dict containing configuration
    """
    ensure_config_dir()
    
    if not os.path.exists(CONFIG_FILE):
        logger.info(f"Config file not found. Creating default at {CONFIG_FILE}")
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            
        # Update with any missing default keys
        updated = False
        for key, value in DEFAULT_CONFIG.items():
            if key not in config:
                config[key] = value
                updated = True
        
        if updated:
            save_config(config)
            
        return config
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        logger.info("Using default configuration")
        return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any]) -> bool:
    """
    Save configuration to file.

    Args:
        config: Configuration dictionary to save

    Returns:
        True if successful, False otherwise
    """
    ensure_config_dir()
    
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        logger.error(f"Failed to save config: {e}")
        return False


def get_i3_config_path() -> str:
    """
    Get the path to the i3 configuration file.

    Returns:
        Path to i3 config file
    """
    config = load_config()
    path = config.get("i3_config_path", DEFAULT_CONFIG["i3_config_path"])
    
    # Check if the path exists, if not try common locations
    if not os.path.exists(path):
        common_paths = [
            os.path.expanduser("~/.config/i3/config"),
            os.path.expanduser("~/.i3/config"),
            "/etc/i3/config",
        ]
        
        for common_path in common_paths:
            if os.path.exists(common_path):
                logger.info(f"Found i3 config at {common_path}")
                config["i3_config_path"] = common_path
                save_config(config)
                return common_path
    
    return path


def get_config_value(key: str, default: Optional[Any] = None) -> Any:
    """
    Get a specific configuration value.

    Args:
        key: Configuration key
        default: Default value if key not found

    Returns:
        Configuration value
    """
    config = load_config()
    return config.get(key, default)