"""
CLI entry point for aidoctool.
Defines the main command group and registers subcommands.
"""

import click
import logging
from aidoctool.config_loader import ConfigLoaderFactory
from aidoctool.config_manager import ConfigManager, ReadOnlyConfigManager

@click.group(help="aidoctool - AI-powered documentation and code tools")
@click.option("--debug/--no-debug", default=False, help="Enable debug output")
@click.option("--config-source", default="yaml", type=click.Choice(["yaml", "env"]), help="Config source: yaml or env")
@click.pass_context
def cli(ctx, debug, config_source):
    """Main entry point for aidoctool."""
    # Set up logging
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format="%(message)s")

    # Initialize context object for sharing data between commands
    ctx.ensure_object(dict)
    loader = ConfigLoaderFactory.get_loader(source=config_source)
    if config_source == "env":
        ctx.obj["config_manager"] = ReadOnlyConfigManager(loader)
    else:
        ctx.obj["config_manager"] = ConfigManager(loader)

# Import and register subcommands
from aidoctool.commands.config_command import config as config_command
from aidoctool.commands.debug_command import debug as debug_command
# Import any test commands if needed
# ...add other commands here as implemented...

cli.add_command(config_command)
cli.add_command(debug_command)
# ...add other commands here as implemented...

if __name__ == "__main__":
    cli()
