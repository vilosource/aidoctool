from abc import ABC, abstractmethod
import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

class ConfigLoader(ABC):
    @abstractmethod
    def load_config(self):
        pass

class YamlConfigLoader(ConfigLoader):
    def __init__(self, config_path=None):
        self.config_path = config_path or (Path.home() / ".aidoctool" / "config.yaml")

    def load_config(self):
        if not self.config_path.exists():
            return {"default_profile": None, "profiles": {}}
        with open(self.config_path, 'r') as f:
            data = yaml.safe_load(f) or {}
        data.setdefault("profiles", {})
        data.setdefault("default_profile", None)
        # Resolve env vars in config values
        for profile in data["profiles"].values():
            if isinstance(profile.get("api_key"), str) and profile["api_key"].startswith("${"):
                env_var = profile["api_key"].strip("${}")
                profile["api_key"] = os.environ.get(env_var, "")
        return data

    def save_config(self, config_data):
        os.makedirs(self.config_path.parent, exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.safe_dump(config_data, f)
        os.chmod(self.config_path, 0o600)

class EnvConfigLoader(ConfigLoader):
    def __init__(self, dotenv_path=None):
        self.dotenv_path = dotenv_path or (Path.home() / ".env")
        load_dotenv(self.dotenv_path)

    def load_config(self):
        # Example: load a single profile from env vars
        provider = os.environ.get("AIDOCTOOL_PROVIDER")
        model = os.environ.get("AIDOCTOOL_MODEL")
        api_key = os.environ.get("AIDOCTOOL_API_KEY")
        params = {}
        return {
            "default_profile": "env-profile",
            "profiles": {
                "env-profile": {
                    "provider": provider,
                    "model": model,
                    "api_key": api_key,
                    "params": params
                }
            }
        }

class ConfigLoaderFactory:
    @staticmethod
    def get_loader(source="yaml", **kwargs):
        if source == "yaml":
            return YamlConfigLoader(**kwargs)
        elif source == "env":
            return EnvConfigLoader(**kwargs)
        else:
            raise ValueError(f"Unknown config source: {source}")
