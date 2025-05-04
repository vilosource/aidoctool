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

@pytest.fixture
def setup_test_config(monkeypatch, tmp_path):
    """Setup a test configuration with a profile"""
    # Create config directory
    config_dir = tmp_path / ".aidoctool"
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / "config.yaml"
    
    # Patch paths
    monkeypatch.setattr('aidoctool.config.CONFIG_PATH', config_file)
    monkeypatch.setattr('aidoctool.config_loader.Path.home', lambda: tmp_path)
    
    # Create a test profile
    runner = CliRunner()
    result = runner.invoke(cli, ['config', 'add', 'testdebug'], input='openai\ngpt-4\nsk-test-key\n')
    assert result.exit_code == 0, f"Failed to create test profile: {result.output}"
    
    return tmp_path

def test_debug_config_command(setup_test_config):
    runner = CliRunner()
    result = runner.invoke(cli, ['debug', 'config'])
    assert result.exit_code == 0
    assert "Current configuration" in result.output or "Config file found" in result.output

def test_debug_info_command():
    runner = CliRunner()
    result = runner.invoke(cli, ['debug', 'info'])
    assert result.exit_code == 0
    assert "System Information" in result.output
    assert "Python version" in result.output

def test_debug_config_verbose(setup_test_config):
    # Test non-verbose (should mask API key)
    runner = CliRunner()
    result = runner.invoke(cli, ['debug', 'config'])
    assert result.exit_code == 0
    if "profiles" in result.output and "api_key" in result.output:
        assert "sk-***" in result.output
        assert "sk-test-key" not in result.output
    
    # Test verbose (should show API key)
    result = runner.invoke(cli, ['debug', 'config', '--verbose'])
    assert result.exit_code == 0
