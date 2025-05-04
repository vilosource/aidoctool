import click
from aidoctool.config import load_config, save_config, CONFIG_PATH

@click.group()
def config():
    """Manage aidoctool configuration profiles."""
    pass

@config.command('add')
@click.argument('profile_name')
@click.option('--provider', prompt=True, help="Provider name (e.g., openai, anthropic, openrouter)")
@click.option('--model', prompt=True, help="Model name (e.g., gpt-4, claude-v1, mixtral-8x7b)")
@click.option('--api-key', prompt=True, hide_input=True, help="API key for the provider")
def config_add(profile_name, provider, model, api_key):
    cfg = load_config()
    profiles = cfg.setdefault("profiles", {})
    if profile_name in profiles:
        raise click.ClickException(f"Profile '{profile_name}' already exists.")
    profiles[profile_name] = {"provider": provider, "model": model, "api_key": api_key, "params": {}}
    if not cfg.get("default_profile"):
        cfg["default_profile"] = profile_name
    save_config(cfg)
    click.echo(f"Profile '{profile_name}' added.")

@config.command('edit')
@click.argument('profile_name')
def config_edit(profile_name):
    cfg = load_config()
    if profile_name not in cfg["profiles"]:
        click.echo(f"Profile '{profile_name}' not found.")
        return
    click.edit(filename=str(CONFIG_PATH))
    click.echo(f"Edited config file. Please verify changes.")

@config.command('delete')
@click.argument('profile_name')
def config_delete(profile_name):
    cfg = load_config()
    profiles = cfg.get("profiles", {})
    if profile_name not in profiles:
        click.echo(f"Profile '{profile_name}' not found.")
        return
    confirm = click.confirm(f"Are you sure you want to delete profile '{profile_name}'?", default=False)
    if not confirm:
        click.echo("Aborted.")
        return
    del profiles[profile_name]
    if cfg.get("default_profile") == profile_name:
        cfg["default_profile"] = None if not profiles else next(iter(profiles))
    save_config(cfg)
    click.echo(f"Profile '{profile_name}' deleted.")

@config.command('default')
@click.argument('profile_name')
def config_default(profile_name):
    cfg = load_config()
    if profile_name not in cfg.get("profiles", {}):
        click.echo(f"Profile '{profile_name}' not found.")
        return
    cfg["default_profile"] = profile_name
    save_config(cfg)
    click.echo(f"Default profile set to '{profile_name}'.")