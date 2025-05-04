import os
import yaml
from pathlib import Path

CONFIG_PATH = Path.home() / ".aidoctool" / "config.yaml"

# --- Config file helpers ---
def load_config():
    """Load configuration from YAML file into a Python dict. Create a default structure if file missing."""
    if not CONFIG_PATH.exists():
        return {"default_profile": None, "profiles": {}}
    with open(CONFIG_PATH, 'r') as f:
        data = yaml.safe_load(f) or {}
    data.setdefault("profiles", {})
    data.setdefault("default_profile", None)
    return data

def save_config(config_data: dict):
    """Save the configuration dictionary back to the YAML file."""
    os.makedirs(CONFIG_PATH.parent, exist_ok=True)
    with open(CONFIG_PATH, 'w') as f:
        yaml.safe_dump(config_data, f)
    # Set file permissions to 600 (user-only)
    os.chmod(CONFIG_PATH, 0o600)
