# Modular, SOLID Command-Line Tool Architecture: A Developer Guide

This document explains a robust, extensible, and maintainable pattern for building Python command-line tools, inspired by the architecture of `pywikicli` and `aidoctool`. It is intended for developers who want to design CLI tools that are easy to extend, test, and maintain, following SOLID principles and modern best practices.

---

## 1. Overview

A well-architected CLI tool should:
- Be modular: Each command and concern is in its own file/class.
- Be extensible: Adding new commands or features should not require rewriting core logic.
- Be testable: Commands and logic can be tested in isolation.
- Follow SOLID principles: Especially Single Responsibility, Open/Closed, and Dependency Inversion.
- Cleanly separate CLI, business logic, and configuration.

---

## 2. Project Structure

A typical structure for a modern CLI tool:

```
project/
  pyproject.toml
  README.md
  ...
  project/
    __init__.py
    cli.py                # Main CLI entry point
    config.py             # Configuration logic (load/save/validate)
    config_loader.py      # ConfigLoader factory and strategies
    config_manager.py     # ConfigManager abstraction
    commands/
      __init__.py
      config_command.py   # Each command in its own file
      other_command.py
    tests/
      test_config_command.py
      ...
```

---

## 3. CLI Entry Point (`cli.py`)

- Defines the main Click group.
- Sets up global options (e.g., --debug, --config-source).
- Initializes shared context (e.g., config manager) for subcommands.
- Registers all subcommands from the `commands/` directory.

Example:
```python
import click
from project.config_loader import ConfigLoaderFactory
from project.config_manager import ConfigManager, ReadOnlyConfigManager

@click.group()
@click.option('--debug/--no-debug', default=False)
@click.option('--config-source', default='yaml', type=click.Choice(['yaml', 'env']))
@click.pass_context
def cli(ctx, debug, config_source):
    ctx.ensure_object(dict)
    loader = ConfigLoaderFactory.get_loader(source=config_source)
    ctx.obj['config_manager'] = (
        ReadOnlyConfigManager(loader) if config_source == 'env' else ConfigManager(loader)
    )

from project.commands.config_command import config as config_command
cli.add_command(config_command)
```

---

## 4. Command Modules (`commands/`)

- Each command is implemented in its own file (e.g., `config_command.py`).
- Uses Click decorators to define subcommands and options.
- Accesses shared state (e.g., config manager) via Click context.
- Keeps business logic out of the CLI layer—delegates to manager or service classes.

Example:
```python
import click
@click.group()
def config():
    """Manage configuration profiles."""
    pass

@config.command('add')
@click.argument('profile_name')
@click.pass_context
def add(ctx, profile_name):
    manager = ctx.obj['config_manager']
    # ... call manager.add_profile ...
```

---

## 5. Configuration Management

- Use a `ConfigLoader` factory and strategy pattern to support multiple config sources (YAML, .env, Redis, etc.).
- Use a `ConfigManager` abstraction for all config operations (read/write/edit/delete/set default).
- For read-only sources, provide a `ReadOnlyConfigManager` that raises on write attempts.
- This enables both CLI and library users to interact with config in a consistent, extensible way.

---

## 6. SOLID Principles in Practice

- **Single Responsibility:** Each file/class has one job (e.g., config loading, command logic, CLI entry).
- **Open/Closed:** New commands or config sources can be added without modifying core logic.
- **Liskov Substitution:** All config managers provide the same interface; read-only managers raise on writes.
- **Interface Segregation:** CLI commands only depend on the config manager interface, not on config details.
- **Dependency Inversion:** CLI and business logic depend on abstractions (managers/loaders), not concrete implementations.

---

## 7. Adding New Commands

1. Create a new file in `commands/` (e.g., `summarize_command.py`).
2. Define a Click command or group in that file.
3. Register the command in `cli.py` with `cli.add_command(...)`.
4. Use the context object to access shared state (e.g., config manager).

---

## 8. Testing

- Use `pytest` and `click.testing.CliRunner` to test commands in isolation.
- Use fixtures and monkeypatching to isolate config and environment.
- Test both CLI and programmatic (manager) usage.

---

## 9. Extending Further

- Add new config sources by implementing new `ConfigLoader` classes and registering them in the factory.
- Add new business logic by creating new manager/service classes.
- Add new CLI features by creating new command modules.

---

## 10. Summary

This pattern enables you to:
- Build large, complex CLI tools that remain easy to extend and maintain.
- Cleanly separate CLI, configuration, and business logic.
- Support both CLI and library use cases.
- Embrace SOLID and modern Python best practices.

For a real-world example, see the structure of `pywikicli` and `aidoctool` in this repository.
