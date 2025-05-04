"""
Common pytest fixtures and configuration.
"""
import os
import sys
import pytest
from pathlib import Path

# Make sure the aidoctool package is in the path
sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary config directory."""
    config_dir = tmp_path / ".aidoctool"
    os.makedirs(config_dir, exist_ok=True)
    return config_dir
