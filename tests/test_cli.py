"""Tests for the command-line interface of the recursivist package."""

import os
from pathlib import Path
import pytest
from typer.testing import CliRunner
from recursivist.cli import app, parse_list_option


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


def test_parse_list_option():
    """Test parsing of space-separated list options."""
    result = parse_list_option(["value1"])
    assert result == ["value1"]

    result = parse_list_option(["value1 value2 value3"])
    assert result == ["value1", "value2", "value3"]

    result = parse_list_option(["value1", "value2", "value3"])
    assert result == ["value1", "value2", "value3"]

    result = parse_list_option(["value1 value2", "value3 value4"])
    assert result == ["value1", "value2", "value3", "value4"]

    result = parse_list_option([])
    assert result == []

    result = parse_list_option(None)
    assert result == []


def test_visualize_command(runner, sample_directory):
    """Test the visualize command."""
    result = runner.invoke(app, ["visualize", sample_directory])
    assert result.exit_code == 0
    assert os.path.basename(sample_directory) in result.stdout
    assert "file1.txt" in result.stdout
    assert "file2.py" in result.stdout
    assert "subdir" in result.stdout


def test_visualize_with_exclude_dirs(runner, sample_directory):
    """Test the visualize command with excluded directories."""
    exclude_dir = os.path.join(sample_directory, "exclude_me")
    os.makedirs(exclude_dir, exist_ok=True)

    with open(os.path.join(exclude_dir, "excluded.txt"), "w") as f:
        f.write("This should be excluded")

    result = runner.invoke(
        app, ["visualize", sample_directory, "--exclude", "exclude_me"]
    )
    assert result.exit_code == 0
    assert "exclude_me" not in result.stdout
    assert "excluded.txt" not in result.stdout


def test_visualize_with_exclude_extensions(runner, sample_directory):
    """Test the visualize command with excluded file extensions."""
    result = runner.invoke(app, ["visualize", sample_directory, "--exclude-ext", ".py"])
    assert result.exit_code == 0
    assert "file1.txt" in result.stdout
    assert "file2.py" not in result.stdout


def test_visualize_with_ignore_file(runner, sample_with_logs):
    """Test the visualize command with gitignore file."""
    result = runner.invoke(
        app, ["visualize", sample_with_logs, "--ignore-file", ".gitignore"]
    )
    assert result.exit_code == 0
    assert "app.log" not in result.stdout
    assert "node_modules" not in result.stdout


def test_visualize_with_export(runner, sample_directory, output_dir):
    """Test the visualize command with export option."""
    result = runner.invoke(
        app,
        [
            "visualize",
            sample_directory,
            "--export",
            "txt",
            "--output-dir",
            output_dir,
            "--prefix",
            "test",
        ],
    )
    assert result.exit_code == 0

    export_file = os.path.join(output_dir, "test.txt")
    assert os.path.exists(export_file)


def test_visualize_multiple_exports(runner, sample_directory, output_dir):
    """Test the visualize command with multiple export formats."""
    result = runner.invoke(
        app,
        [
            "visualize",
            sample_directory,
            "--export",
            "txt json",
            "--output-dir",
            output_dir,
        ],
    )
    assert result.exit_code == 0

    assert os.path.exists(os.path.join(output_dir, "structure.txt"))
    assert os.path.exists(os.path.join(output_dir, "structure.json"))


def test_visualize_invalid_export_format(runner, sample_directory):
    """Test the visualize command with invalid export format."""
    result = runner.invoke(app, ["visualize", sample_directory, "--export", "invalid"])
    assert result.exit_code == 1
    assert "Unsupported export format" in result.stdout


def test_visualize_invalid_directory(runner, temp_dir):
    """Test the visualize command with non-existent directory."""
    invalid_dir = os.path.join(temp_dir, "nonexistent")
    result = runner.invoke(app, ["visualize", invalid_dir])
    assert result.exit_code == 1
    assert "not a valid directory" in result.stdout


def test_version_command(runner):
    """Test the version command."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "Recursivist version" in result.stdout


def test_completion_command(runner):
    """Test the completion command."""
    result = runner.invoke(app, ["completion", "bash"])
    assert result.exit_code == 0

    result = runner.invoke(app, ["completion", "invalid"])
    assert result.exit_code == 1
    assert "Unsupported shell" in result.stdout


def test_verbose_mode(runner, sample_directory):
    """Test the verbose mode."""
    result = runner.invoke(app, ["visualize", sample_directory, "--verbose"])
    assert result.exit_code == 0
    assert "Verbose mode enabled" in result.stdout
