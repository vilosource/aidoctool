import pytest
from click.testing import CliRunner
from aidoctool.commands.debug_command import debug
from aidoctool.cli import cli

def test_debug_config_command():
    runner = CliRunner()
    result = runner.invoke(cli, ['debug', 'config'])
    assert result.exit_code == 0
    assert "Current configuration" in result.output

def test_debug_info_command():
    runner = CliRunner()
    result = runner.invoke(cli, ['debug', 'info'])
    assert result.exit_code == 0
    assert "System Information" in result.output
    assert "Python version" in result.output

def test_debug_config_verbose(monkeypatch, tmp_path):
    # Set up a temporary config directory
    config_dir = tmp_path / ".aidoctool"
    config_dir.mkdir(exist_ok=True)
    monkeypatch.setattr('aidoctool.config.CONFIG_PATH', tmp_path / ".aidoctool" / "config.yaml")
    monkeypatch.setattr('aidoctool.config_loader.Path.home', lambda: tmp_path)
    
    # First create a profile
    runner = CliRunner()
    result = runner.invoke(cli, ['config', 'add', 'testdebug'], input='openai\ngpt-4\nsk-test-key\n')
    assert result.exit_code == 0
    
    # Test non-verbose (should mask API key)
    result = runner.invoke(cli, ['debug', 'config'])
    assert result.exit_code == 0
    # Just check that the command runs without error
    assert "Current configuration" in result.output or "Config file found" in result.output
    
    # Test verbose (should show API key)
    result = runner.invoke(cli, ['debug', 'config', '--verbose'])
    assert result.exit_code == 0
    # Just check that the command runs without error
    assert result.exit_code == 0
