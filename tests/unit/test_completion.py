"""Unit tests for shell completion command."""

from typer.testing import CliRunner

from paketci.cli.app import app

runner = CliRunner()


def test_completion_bash():
    result = runner.invoke(app, ["completion", "bash"])
    assert result.exit_code == 0
    assert "_paketci_completion" in result.output
    assert "_PAKETCI_COMPLETE=complete_bash" in result.output


def test_completion_zsh():
    result = runner.invoke(app, ["completion", "zsh"])
    assert result.exit_code == 0
    assert "_PAKETCI_COMPLETE=complete_zsh" in result.output


def test_completion_fish():
    result = runner.invoke(app, ["completion", "fish"])
    assert result.exit_code == 0
    assert "complete --command paketci" in result.output
    assert "_PAKETCI_COMPLETE=complete_fish" in result.output
