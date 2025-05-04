"""
Debug utilities for aidoctool.
"""

import logging
import yaml
import os
from pathlib import Path

logger = logging.getLogger(__name__)

def dump_config(config, verbose=False):
    """
    Print the current configuration in a readable format.
    
    Args:
        config (dict): The configuration dictionary
        verbose (bool): Whether to show sensitive information like API keys
    """
    if not config:
        logger.info("No configuration found.")
        return
    
    # Create a copy to avoid modifying the original
    config_copy = config.copy()
    
    # Mask API keys if not verbose
    if not verbose and "profiles" in config_copy:
        for profile in config_copy["profiles"].values():
            if "api_key" in profile:
                profile["api_key"] = "sk-***" if profile["api_key"] else None
    
    # Format and print
    formatted = yaml.dump(config_copy, default_flow_style=False, sort_keys=False)
    logger.info(f"Current configuration:\n{formatted}")

def check_config_file_exists():
    """Check if the config file exists and return its path."""
    from aidoctool.config import CONFIG_PATH
    
    if CONFIG_PATH.exists():
        logger.info(f"Config file found at: {CONFIG_PATH}")
        return True
    else:
        logger.warning(f"Config file not found at: {CONFIG_PATH}")
        return False

def get_config_dir():
    """Return the configuration directory."""
    from aidoctool.config import CONFIG_PATH
    return CONFIG_PATH.parent
