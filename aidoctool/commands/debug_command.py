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
        click.echo("ERROR: Config manager not initialized.")
        return
    
    try:
        config = config_manager.get_config()
        formatted_config = dump_config(config, verbose)
        click.echo(f"Current configuration:\n{formatted_config}")
        
        if check_config_file_exists():
            click.echo(f"Config file found at: {get_config_dir() / 'config.yaml'}")
        else:
            click.echo(f"Config file not found at: {get_config_dir() / 'config.yaml'}")
            
        click.echo(f"Config directory: {get_config_dir()}")
    except Exception as e:
        logger.error(f"Error retrieving configuration: {e}")
        click.echo(f"ERROR: Error retrieving configuration: {e}")

@debug.command('info')
def debug_info():
    """Display system and environment information."""
    import sys
    import platform
    import os
    
    click.echo("System Information:")
    click.echo(f"Python version: {sys.version}")
    click.echo(f"Platform: {platform.platform()}")
    click.echo(f"Working directory: {os.getcwd()}")
    
    # Check for environment variables
    env_vars = [var for var in os.environ if var.startswith("AIDOCTOOL_")]
    if env_vars:
        click.echo("AIDOCTOOL environment variables:")
        for var in env_vars:
            value = os.environ[var]
            # Mask API keys
            if "API_KEY" in var:
                value = "sk-***" if value else None
            click.echo(f"  {var}={value}")
    else:
        click.echo("No AIDOCTOOL environment variables found.")
