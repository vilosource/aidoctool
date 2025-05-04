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

def test_debug_config_verbose():
    # First create a profile
    runner = CliRunner()
    runner.invoke(cli, ['config', 'add', 'testdebug'], input='openai\ngpt-4\nsk-test-key\n')
    
    # Test non-verbose (should mask API key)
    result = runner.invoke(cli, ['debug', 'config'])
    assert result.exit_code == 0
    assert "sk-***" in result.output
    assert "sk-test-key" not in result.output
    
    # Test verbose (should show API key)
    result = runner.invoke(cli, ['debug', 'config', '--verbose'])
    assert result.exit_code == 0
    assert "sk-test-key" in result.output
