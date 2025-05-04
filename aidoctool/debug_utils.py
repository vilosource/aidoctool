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
    Format the current configuration in a readable format.
    
    Args:
        config (dict): The configuration dictionary
        verbose (bool): Whether to show sensitive information like API keys
        
    Returns:
        str: The formatted configuration string
    """
    if not config:
        logger.info("No configuration found.")
        return "No configuration found."
    
    # Create a deep copy to avoid modifying the original
    config_copy = {}
    if isinstance(config, dict):
        import copy
        config_copy = copy.deepcopy(config)
    else:
        logger.info(f"Config is not a dictionary: {type(config)}")
        return f"Config is not a dictionary: {type(config)}"
    
    # Mask API keys if not verbose
    if not verbose and "profiles" in config_copy and isinstance(config_copy["profiles"], dict):
        for profile_name, profile in config_copy["profiles"].items():
            if isinstance(profile, dict) and "api_key" in profile:
                profile["api_key"] = "sk-***" if profile["api_key"] else None
    
    # Format and return
    try:
        formatted = yaml.dump(config_copy, default_flow_style=False, sort_keys=False)
        logger.info(f"Current configuration:\n{formatted}")
        return formatted
    except Exception as e:
        logger.error(f"Error formatting config: {e}")
        # Try a simpler representation if YAML dump fails
        try:
            simple_repr = str(config_copy)
            logger.info(f"Raw config: {simple_repr}")
            return simple_repr
        except:
            logger.error("Unable to display configuration")
            return "Unable to display configuration"

def check_config_file_exists():
    """Check if the config file exists and return its path."""
    try:
        from aidoctool.config import CONFIG_PATH
        
        if CONFIG_PATH.exists():
            logger.info(f"Config file found at: {CONFIG_PATH}")
            return True
        else:
            logger.warning(f"Config file not found at: {CONFIG_PATH}")
            return False
    except Exception as e:
        logger.error(f"Error checking config file: {e}")
        return False

def get_config_dir():
    """Return the configuration directory."""
    try:
        from aidoctool.config import CONFIG_PATH
        return CONFIG_PATH.parent
    except Exception as e:
        logger.error(f"Error getting config directory: {e}")
        return Path.home() / ".aidoctool"
