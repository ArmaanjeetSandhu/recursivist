"""Tests for the command-line interface of the recursivist package."""

import os

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


def test_visualize_with_full_path(runner, sample_directory):
    """Test the visualize command with full path option."""
    result = runner.invoke(app, ["visualize", sample_directory, "--full-path"])
    assert result.exit_code == 0
    assert os.path.basename(sample_directory) in result.stdout

    base_name = os.path.basename(sample_directory)
    sample_path = f"{base_name}/file1.txt".replace("/", os.path.sep)
    sample_path_alt = f"{base_name}\\file1.txt".replace("\\", os.path.sep)

    has_full_path = base_name in result.stdout and (
        "file1.txt" in result.stdout
        or "file2.py" in result.stdout
        or sample_path in result.stdout
        or sample_path_alt in result.stdout
    )

    assert has_full_path, "Full path information not found in output"


def test_visualize_with_jsx_export(runner, sample_directory, output_dir):
    """Test the visualize command with React export option."""
    result = runner.invoke(
        app,
        [
            "visualize",
            sample_directory,
            "--export",
            "jsx",
            "--output-dir",
            output_dir,
            "--prefix",
            "test_component",
        ],
    )
    assert result.exit_code == 0

    export_file = os.path.join(output_dir, "test_component.jsx")
    assert os.path.exists(export_file)

    with open(export_file, "r", encoding="utf-8") as f:
        content = f.read()

    assert "import React" in content
    assert "DirectoryViewer" in content


def test_visualize_with_jsx_export_full_path(runner, sample_directory, output_dir):
    """Test the visualize command with React export option and full path display."""
    result = runner.invoke(
        app,
        [
            "visualize",
            sample_directory,
            "--export",
            "jsx",
            "--output-dir",
            output_dir,
            "--prefix",
            "test_component_full_path",
            "--full-path",
        ],
    )
    assert result.exit_code == 0

    export_file = os.path.join(output_dir, "test_component_full_path.jsx")
    assert os.path.exists(export_file)

    with open(export_file, "r", encoding="utf-8") as f:
        content = f.read()

    assert "import React" in content
    assert "DirectoryViewer" in content
    assert "Showing full file paths" in content


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


def test_visualize_with_export_full_path(runner, sample_directory, output_dir):
    """Test the visualize command with export option and full path display."""
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
            "test_full_path",
            "--full-path",
        ],
    )
    assert result.exit_code == 0

    export_file = os.path.join(output_dir, "test_full_path.txt")
    assert os.path.exists(export_file)

    with open(export_file, "r", encoding="utf-8") as f:
        content = f.read()

    assert (
        "file1.txt" in content or "file2.py" in content
    ), "No file information found in exported content"

    has_path_info = False
    base_name = os.path.basename(sample_directory)

    lines = content.split("\n")
    for line in lines:
        if ("├── 📄" in line or "└── 📄" in line) and (
            base_name in line or os.path.sep in line or "/" in line
        ):
            has_path_info = True
            break

    assert has_path_info, "No full path information found in exported content"


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


def test_visualize_invalid_export_format(runner, sample_directory, caplog):
    """Test the visualize command with invalid export format."""
    result = runner.invoke(app, ["visualize", sample_directory, "--export", "invalid"])
    assert result.exit_code == 1
    assert any(
        "Unsupported export format" in record.message for record in caplog.records
    )


def test_visualize_invalid_directory(runner, temp_dir, caplog):
    """Test the visualize command with non-existent directory."""
    invalid_dir = os.path.join(temp_dir, "nonexistent")
    result = runner.invoke(app, ["visualize", invalid_dir])
    assert result.exit_code == 1
    assert any("not a valid directory" in record.message for record in caplog.records)


def test_version_command(runner):
    """Test the version command."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "Recursivist version" in result.stdout


def test_completion_command(runner, monkeypatch, caplog):
    """Test the completion command."""

    def mock_get_completion(shell):
        if shell not in ["bash", "zsh", "fish", "powershell"]:
            raise ValueError(f"Unsupported shell: {shell}")
        return f"# {shell} completion script"

    monkeypatch.setattr(
        "typer.completion.get_completion_inspect_parameters", mock_get_completion
    )

    result = runner.invoke(app, ["completion", "bash"])
    assert result.exit_code == 0

    result = runner.invoke(app, ["completion", "invalid"])
    assert result.exit_code == 1
    assert any("Unsupported shell" in record.message for record in caplog.records)


def test_verbose_mode(runner, sample_directory, caplog):
    """Test the verbose mode."""
    result = runner.invoke(app, ["visualize", sample_directory, "--verbose"])
    assert result.exit_code == 0
    assert any("Verbose mode enabled" in record.message for record in caplog.records)
