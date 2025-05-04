from aidoctool.config_loader import ConfigLoader, YamlConfigLoader, EnvConfigLoader

class ConfigManager:
    def __init__(self, loader: ConfigLoader):
        self.loader = loader
        self._config = None

    def load(self):
        self._config = self.loader.load_config()
        return self._config

    def get_config(self):
        if self._config is None:
            return self.load()
        return self._config

    def save(self):
        if hasattr(self.loader, 'save_config'):
            self.loader.save_config(self._config)
        else:
            raise NotImplementedError("This config source is read-only.")

    def add_profile(self, profile_name, provider, model, api_key, params=None):
        config = self.get_config()
        profiles = config.setdefault("profiles", {})
        if profile_name in profiles:
            raise ValueError(f"Profile '{profile_name}' already exists.")
        profiles[profile_name] = {
            "provider": provider,
            "model": model,
            "api_key": api_key,
            "params": params or {}
        }
        if not config.get("default_profile"):
            config["default_profile"] = profile_name
        self.save()

    def edit_profile(self, profile_name, **kwargs):
        config = self.get_config()
        profiles = config.get("profiles", {})
        if profile_name not in profiles:
            raise ValueError(f"Profile '{profile_name}' not found.")
        profiles[profile_name].update(kwargs)
        self.save()

    def delete_profile(self, profile_name):
        config = self.get_config()
        profiles = config.get("profiles", {})
        if profile_name not in profiles:
            raise ValueError(f"Profile '{profile_name}' not found.")
        del profiles[profile_name]
        if config.get("default_profile") == profile_name:
            config["default_profile"] = None if not profiles else next(iter(profiles))
        self.save()

    def set_default(self, profile_name):
        config = self.get_config()
        if profile_name not in config.get("profiles", {}):
            raise ValueError(f"Profile '{profile_name}' not found.")
        config["default_profile"] = profile_name
        self.save()

class ReadOnlyConfigManager(ConfigManager):
    def save(self):
        raise NotImplementedError("This config source is read-only.")
    def add_profile(self, *args, **kwargs):
        raise NotImplementedError("This config source is read-only.")
    def edit_profile(self, *args, **kwargs):
        raise NotImplementedError("This config source is read-only.")
    def delete_profile(self, *args, **kwargs):
        raise NotImplementedError("This config source is read-only.")
    def set_default(self, *args, **kwargs):
        raise NotImplementedError("This config source is read-only.")
