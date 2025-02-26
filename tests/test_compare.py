"""Tests for the directory comparison functionality."""

import json
import os

import pytest
from typer.testing import CliRunner

from recursivist.compare import (
    compare_directory_structures,
    display_comparison,
    export_comparison,
)


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def comparison_directories(temp_dir):
    """Create two sample directories with some differences for comparison."""
    dir1 = os.path.join(temp_dir, "dir1")
    dir2 = os.path.join(temp_dir, "dir2")

    os.makedirs(dir1, exist_ok=True)
    os.makedirs(os.path.join(dir1, "common_dir"), exist_ok=True)
    os.makedirs(os.path.join(dir1, "dir1_only"), exist_ok=True)

    with open(os.path.join(dir1, "file1.txt"), "w") as f:
        f.write("File in both dirs")
    with open(os.path.join(dir1, "dir1_only.txt"), "w") as f:
        f.write("Only in dir1")
    with open(os.path.join(dir1, "common_dir", "common_file.py"), "w") as f:
        f.write("print('Common file')")

    os.makedirs(dir2, exist_ok=True)
    os.makedirs(os.path.join(dir2, "common_dir"), exist_ok=True)
    os.makedirs(os.path.join(dir2, "dir2_only"), exist_ok=True)

    with open(os.path.join(dir2, "file1.txt"), "w") as f:
        f.write("File in both dirs")
    with open(os.path.join(dir2, "dir2_only.txt"), "w") as f:
        f.write("Only in dir2")
    with open(os.path.join(dir2, "common_dir", "common_file.py"), "w") as f:
        f.write("print('Common file')")
    with open(os.path.join(dir2, "common_dir", "dir2_only.py"), "w") as f:
        f.write("print('Only in dir2')")

    return dir1, dir2


def test_compare_directory_structures(comparison_directories):
    """Test that directory structures are correctly compared."""
    dir1, dir2 = comparison_directories

    structure1, structure2, extensions = compare_directory_structures(dir1, dir2)

    assert "_files" in structure1
    assert "_files" in structure2
    assert "common_dir" in structure1
    assert "common_dir" in structure2
    assert "dir1_only" in structure1
    assert "dir1_only" not in structure2
    assert "dir2_only" not in structure1
    assert "dir2_only" in structure2

    assert "file1.txt" in structure1["_files"]
    assert "file1.txt" in structure2["_files"]
    assert "dir1_only.txt" in structure1["_files"]
    assert "dir1_only.txt" not in structure2.get("_files", [])
    assert "dir2_only.txt" not in structure1.get("_files", [])
    assert "dir2_only.txt" in structure2["_files"]

    assert ".txt" in extensions
    assert ".py" in extensions


def test_display_comparison(comparison_directories, capsys):
    """Test that comparison display works without errors."""
    dir1, dir2 = comparison_directories

    display_comparison(dir1, dir2)

    captured = capsys.readouterr()
    assert os.path.basename(dir1) in captured.out
    assert os.path.basename(dir2) in captured.out
    assert "Legend" in captured.out


def test_export_comparison_json(comparison_directories, output_dir):
    """Test JSON export of directory comparison."""
    dir1, dir2 = comparison_directories
    output_path = os.path.join(output_dir, "comparison.json")

    export_comparison(dir1, dir2, "json", output_path)

    assert os.path.exists(output_path)

    with open(output_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "dir1" in data
    assert "dir2" in data
    assert data["dir1"]["name"] == os.path.basename(dir1)
    assert data["dir2"]["name"] == os.path.basename(dir2)
    assert "dir1_only" in data["dir1"]["structure"]
    assert "dir2_only" in data["dir2"]["structure"]


def test_export_comparison_txt(comparison_directories, output_dir):
    """Test text export of directory comparison."""
    dir1, dir2 = comparison_directories
    output_path = os.path.join(output_dir, "comparison.txt")

    export_comparison(dir1, dir2, "txt", output_path)

    assert os.path.exists(output_path)

    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Directory Comparison" in content
    assert os.path.basename(dir1) in content
    assert os.path.basename(dir2) in content
    assert "dir1_only" in content
    assert "dir2_only" in content


def test_export_comparison_html(comparison_directories, output_dir):
    """Test HTML export of directory comparison."""
    dir1, dir2 = comparison_directories
    output_path = os.path.join(output_dir, "comparison.html")

    export_comparison(dir1, dir2, "html", output_path)

    assert os.path.exists(output_path)

    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "<!DOCTYPE html>" in content
    assert "<html>" in content
    assert "Directory Comparison" in content
    assert os.path.basename(dir1) in content
    assert os.path.basename(dir2) in content
    assert "dir1_only" in content
    assert "dir2_only" in content


def test_export_comparison_markdown(comparison_directories, output_dir):
    """Test Markdown export of directory comparison."""
    dir1, dir2 = comparison_directories
    output_path = os.path.join(output_dir, "comparison.md")

    export_comparison(dir1, dir2, "md", output_path)

    assert os.path.exists(output_path)

    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "# Directory Comparison" in content
    assert os.path.basename(dir1) in content
    assert os.path.basename(dir2) in content
    assert "dir1_only" in content
    assert "dir2_only" in content


def test_export_comparison_unsupported_format(comparison_directories, output_dir):
    """Test error handling for unsupported export format."""
    dir1, dir2 = comparison_directories
    output_path = os.path.join(output_dir, "comparison.unsupported")

    with pytest.raises(ValueError) as excinfo:
        export_comparison(dir1, dir2, "unsupported", output_path)

    assert "Unsupported format" in str(excinfo.value)


def test_comparison_with_exclude_dirs(comparison_directories, output_dir):
    """Test directory comparison with excluded directories."""
    dir1, dir2 = comparison_directories

    structure1, structure2, _ = compare_directory_structures(
        dir1, dir2, exclude_dirs=["dir1_only", "dir2_only"]
    )

    assert "dir1_only" not in structure1
    assert "dir2_only" not in structure2


def test_comparison_with_exclude_extensions(comparison_directories, output_dir):
    """Test directory comparison with excluded file extensions."""
    dir1, dir2 = comparison_directories

    structure1, structure2, extensions = compare_directory_structures(
        dir1, dir2, exclude_extensions={".py"}
    )

    assert ".py" not in extensions
    assert "common_file.py" not in structure1.get("common_dir", {}).get("_files", [])
    assert "common_file.py" not in structure2.get("common_dir", {}).get("_files", [])
    assert "dir2_only.py" not in structure2.get("common_dir", {}).get("_files", [])


def test_cli_command(runner, comparison_directories):
    """Test the compare CLI command."""
    from recursivist.cli import app

    dir1, dir2 = comparison_directories

    result = runner.invoke(app, ["compare", dir1, dir2])

    assert result.exit_code == 0
    assert os.path.basename(dir1) in result.stdout
    assert os.path.basename(dir2) in result.stdout
    assert "Legend" in result.stdout


def test_cli_command_with_export(runner, comparison_directories, output_dir):
    """Test the compare CLI command with export option."""
    from recursivist.cli import app

    dir1, dir2 = comparison_directories

    result = runner.invoke(
        app,
        [
            "compare",
            dir1,
            dir2,
            "--export",
            "txt",
            "--output-dir",
            output_dir,
            "--prefix",
            "test_compare",
        ],
    )

    assert result.exit_code == 0

    output_file = os.path.join(output_dir, "test_compare.txt")
    assert os.path.exists(output_file)
