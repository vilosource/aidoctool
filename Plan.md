# aidoctool Configuration and Architecture Plan

## 1. Configuration System
- Store user settings in `~/.aidoctool/config.yaml` (YAML format) by default.
- Support multiple named profiles, each with:
  - provider (e.g., openai, anthropic, openrouter)
  - model (e.g., gpt-4, claude-v1, mixtral-8x7b, claude-3.7-sonnet)
  - api_key (string or env var reference)
  - params (optional dict for provider/model-specific options)
- Example config:

```yaml
default_profile: openai-gpt4
profiles:
  openai-gpt4:
    provider: openai
    model: gpt-4
    api_key: "sk-..."
    params:
      temperature: 0.5
  my-anthropic:
    provider: anthropic
    model: claude-v1
    api_key: "ANTHROPIC_API_KEY"
    params: {}
  openrouter-mixtral:
    provider: openrouter
    model: mixtral-8x7b
    api_key: "OPENROUTER_API_KEY"
    params:
      temperature: 0.7
      max_tokens: 1000
  openrouter-claude-sonnet:
    provider: openrouter
    model: claude-3.7-sonnet
    api_key: "OPENROUTER_API_KEY"
    params:
      temperature: 0.6
```

## 2. ConfigLoader Factory & Strategy
- Implement a `ConfigLoader` abstract base class defining a standard interface (e.g., load_config()).
- Implement concrete loaders:
  - `YamlConfigLoader`: Loads from YAML file (default).
  - `EnvConfigLoader`: Loads from environment variables or .env file (using python-dotenv).
  - (Future) `RedisConfigLoader`, `ApiConfigLoader`, etc.
- Implement a `ConfigLoaderFactory` to instantiate the appropriate loader based on user choice or context.
- This enables easy extension for new config sources without changing existing code (Open/Closed Principle).

## 3. ConfigManager Abstraction (Updated)
- Implement a `ConfigManager` class that supports both read and write operations (load, save, add_profile, edit_profile, delete_profile, set_default, etc.).
- Allow the user (CLI or library) to select or inject the desired `ConfigLoader` (YAML, Env, etc.) when creating a `ConfigManager` instance.
- For read-only sources (like `EnvConfigLoader`), raise an appropriate exception (e.g., `NotImplementedError`) or make write methods no-ops, and document this behavior.
- Optionally, provide a `ReadOnlyConfigManager` for sources that do not support editing, and a full-featured `ConfigManager` for editable sources.
- This enables both CLI and library users to programmatically read and update configuration, with clear error handling for unsupported operations.

## 4. CLI Integration (Updated)
- CLI commands interact with `ConfigManager` for all config operations.
- User can specify config source via CLI flag or environment variable (e.g., --config-source yaml|env|redis).
- Document how to use different config sources and programmatic config editing in README.

## 5. Extensibility & Security
- Allow referencing API keys via environment variables in YAML config.
- Never print or log API keys.
- Set config file permissions to 600 (user-only).
- Add `.gitignore` to exclude config and secrets.

## 6. Project Structure
```
aidoctool/
  __init__.py
  cli.py
  config.py
  config_loader.py  # <-- new
  config_manager.py # <-- new
  commands/
    __init__.py
    config_command.py
  llm/
    __init__.py
    base.py
    openai_client.py
    anthropic_client.py
    openrouter_client.py
  utils/
    __init__.py
  tests/
    test_config_command.py
    test_config_loader.py
    test_config_manager.py
  main.py
```

## 7. Next Steps
- Implement `ConfigLoader` base class and concrete loaders (YAML, Env).
- Implement `ConfigLoaderFactory`.
- Implement `ConfigManager` and `CliConfigManager`.
- Refactor CLI commands to use `ConfigManager`.
- Add tests for new config loading strategies.
- Document usage in README.
