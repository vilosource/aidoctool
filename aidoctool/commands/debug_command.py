"""
Debug commands for aidoctool.
"""

import click
import logging
from aidoctool.debug_utils import dump_config, check_config_file_exists, get_config_dir

logger = logging.getLogger(__name__)

@click.group()
def debug():
    """Debug and troubleshooting commands."""
    pass

@debug.command('config')
@click.option('--verbose', '-v', is_flag=True, help='Show sensitive information like API keys')
@click.pass_context
def debug_config(ctx, verbose):
    """Display the current configuration."""
    config_manager = ctx.obj.get("config_manager")
    if not config_manager:
        logger.error("Config manager not initialized.")
        return
    
    try:
        config = config_manager.get_config()
        dump_config(config, verbose)
        check_config_file_exists()
        config_dir = get_config_dir()
        logger.info(f"Config directory: {config_dir}")
    except Exception as e:
        logger.error(f"Error retrieving configuration: {e}")

@debug.command('info')
def debug_info():
    """Display system and environment information."""
    import sys
    import platform
    import os
    
    logger.info("System Information:")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    # Check for environment variables
    env_vars = [var for var in os.environ if var.startswith("AIDOCTOOL_")]
    if env_vars:
        logger.info("AIDOCTOOL environment variables:")
        for var in env_vars:
            value = os.environ[var]
            # Mask API keys
            if "API_KEY" in var:
                value = "sk-***" if value else None
            logger.info(f"  {var}={value}")
    else:
        logger.info("No AIDOCTOOL environment variables found.")
