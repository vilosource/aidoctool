import os
import tempfile
import shutil
import pytest
from click.testing import CliRunner
from aidoctool.commands.config_command import config
from aidoctool.config_manager import ConfigManager, ReadOnlyConfigManager
from aidoctool.config_loader import YamlConfigLoader, EnvConfigLoader
import pathlib
import sys

@pytest.fixture(autouse=True)
def isolate_config(monkeypatch, tmp_path):
    # Use a temporary directory for config file
    temp_dir = tmp_path
    temp_config = temp_dir / "config.yaml"
    config_dir = temp_dir / ".aidoctool"
    os.makedirs(config_dir, exist_ok=True)
    monkeypatch.setattr('aidoctool.config_loader.Path.home', lambda: temp_dir)
    monkeypatch.setattr('aidoctool.config.CONFIG_PATH', config_dir / "config.yaml")
    yield

def test_add_profile():
    runner = CliRunner()
    result = runner.invoke(config, ['add', 'testprofile'], input='openai\ngpt-4\nsk-test\n')
    assert result.exit_code == 0
    assert "Profile 'testprofile' added." in result.output

def test_add_duplicate_profile():
    runner = CliRunner()
    runner.invoke(config, ['add', 'dup'], input='openai\ngpt-4\nsk-test\n')
    result = runner.invoke(config, ['add', 'dup'], input='openai\ngpt-4\nsk-test\n')
    assert result.exit_code != 0
    assert "already exists" in result.output

def test_delete_profile():
    runner = CliRunner()
    runner.invoke(config, ['add', 'todelete'], input='openai\ngpt-4\nsk-test\n')
    result = runner.invoke(config, ['delete', 'todelete'], input='y\n')
    assert result.exit_code == 0
    assert "deleted" in result.output

def test_set_default_profile():
    runner = CliRunner()
    runner.invoke(config, ['add', 'p1'], input='openai\ngpt-4\nsk-test\n')
    runner.invoke(config, ['add', 'p2'], input='openai\ngpt-4\nsk-test\n')
    result = runner.invoke(config, ['default', 'p2'])
    assert result.exit_code == 0
    assert "Default profile set to 'p2'" in result.output

def test_edit_profile(monkeypatch):
    runner = CliRunner()
    runner.invoke(config, ['add', 'toedit'], input='openai\ngpt-4\nsk-test\n')
    # Patch click.edit to simulate editing
    monkeypatch.setattr('click.edit', lambda filename: None)
    result = runner.invoke(config, ['edit', 'toedit'])
    assert result.exit_code == 0
    assert "Edited config file" in result.output

def test_delete_nonexistent_profile():
    runner = CliRunner()
    result = runner.invoke(config, ['delete', 'nope'], input='y\n')
    assert result.exit_code == 0
    assert "not found" in result.output

def test_set_default_nonexistent_profile():
    runner = CliRunner()
    result = runner.invoke(config, ['default', 'nope'])
    assert result.exit_code == 0
    assert "not found" in result.output

# --- New tests for ConfigManager and loaders ---
def test_config_manager_yaml(tmp_path):
    config_path = tmp_path / "config.yaml"
    loader = YamlConfigLoader(config_path=config_path)
    manager = ConfigManager(loader)
    manager.add_profile("p1", "openai", "gpt-4", "sk-test")
    config = manager.get_config()
    assert "p1" in config["profiles"]
    manager.set_default("p1")
    assert config["default_profile"] == "p1"
    manager.edit_profile("p1", model="gpt-3.5")
    assert config["profiles"]["p1"]["model"] == "gpt-3.5"
    manager.delete_profile("p1")
    assert "p1" not in config["profiles"]

def test_readonly_config_manager_env(monkeypatch):
    monkeypatch.setenv("AIDOCTOOL_PROVIDER", "openai")
    monkeypatch.setenv("AIDOCTOOL_MODEL", "gpt-4")
    monkeypatch.setenv("AIDOCTOOL_API_KEY", "sk-env")
    loader = EnvConfigLoader()
    manager = ReadOnlyConfigManager(loader)
    config = manager.get_config()
    assert config["profiles"]["env-profile"]["provider"] == "openai"
    with pytest.raises(NotImplementedError):
        manager.add_profile("fail", "openai", "gpt-4", "sk-test")
    with pytest.raises(NotImplementedError):
        manager.save()
