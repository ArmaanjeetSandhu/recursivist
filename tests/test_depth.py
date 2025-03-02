"""Tests for the depth limit functionality."""

import json
import os

import pytest
from typer.testing import CliRunner

from recursivist.cli import app
from recursivist.core import get_directory_structure


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def nested_directory(temp_dir):
    """Create a nested directory structure for depth testing.

    Structure:
    temp_dir/
    ├── level1/
    │   ├── level1_file.txt
    │   └── level2/
    │       ├── level2_file.txt
    │       └── level3/
    │           ├── level3_file.txt
    │           └── level4/
    │               └── level4_file.txt
    """
    level1 = os.path.join(temp_dir, "level1")
    level2 = os.path.join(level1, "level2")
    level3 = os.path.join(level2, "level3")
    level4 = os.path.join(level3, "level4")

    os.makedirs(level1, exist_ok=True)
    os.makedirs(level2, exist_ok=True)
    os.makedirs(level3, exist_ok=True)
    os.makedirs(level4, exist_ok=True)

    with open(os.path.join(level1, "level1_file.txt"), "w") as f:
        f.write("Level 1 file")

    with open(os.path.join(level2, "level2_file.txt"), "w") as f:
        f.write("Level 2 file")

    with open(os.path.join(level3, "level3_file.txt"), "w") as f:
        f.write("Level 3 file")

    with open(os.path.join(level4, "level4_file.txt"), "w") as f:
        f.write("Level 4 file")

    return temp_dir


def test_get_directory_structure_with_depth_limit(nested_directory):
    """Test the directory structure function with depth limit."""
    structure, _ = get_directory_structure(nested_directory, max_depth=0)

    assert "level1" in structure
    assert "level2" in structure["level1"]
    assert "level3" in structure["level1"]["level2"]
    assert "level4" in structure["level1"]["level2"]["level3"]

    structure, _ = get_directory_structure(nested_directory, max_depth=1)

    print("Structure with max_depth=1:")
    print(json.dumps(structure, indent=2))

    assert "level1" in structure
    assert "_max_depth_reached" in structure["level1"]

    structure, _ = get_directory_structure(nested_directory, max_depth=2)

    print("Structure with max_depth=2:")
    print(json.dumps(structure, indent=2))

    assert "level1" in structure
    assert "level2" in structure["level1"]
    assert "_max_depth_reached" in structure["level1"]["level2"]


def test_visualize_command_with_depth_limit(runner, nested_directory, monkeypatch):
    """Test the visualize command with depth limit."""
    from unittest.mock import MagicMock

    mock_display_tree = MagicMock()
    monkeypatch.setattr("recursivist.cli.display_tree", mock_display_tree)

    result = runner.invoke(app, ["visualize", nested_directory, "--depth", "2"])

    assert result.exit_code == 0


def test_compare_command_with_depth_limit(runner, nested_directory, monkeypatch):
    """Test the compare command with depth limit."""
    compare_dir = os.path.join(os.path.dirname(nested_directory), "compare_dir")
    os.makedirs(compare_dir, exist_ok=True)

    level1 = os.path.join(compare_dir, "level1")
    level2 = os.path.join(level1, "level2")
    os.makedirs(level1, exist_ok=True)
    os.makedirs(level2, exist_ok=True)

    with open(os.path.join(level1, "level1_file.txt"), "w") as f:
        f.write("Level 1 file")

    with open(os.path.join(level2, "different_file.txt"), "w") as f:
        f.write("Different level 2 file")

    result = runner.invoke(
        app, ["compare", nested_directory, compare_dir, "--depth", "2"]
    )

    assert result.exit_code == 0


def test_export_with_depth_limit(runner, nested_directory, output_dir, monkeypatch):
    """Test exporting with depth limit."""
    os.makedirs(output_dir, exist_ok=True)

    from unittest.mock import MagicMock

    mock_export = MagicMock()
    monkeypatch.setattr("recursivist.cli.export_structure", mock_export)

    result = runner.invoke(
        app,
        [
            "export",
            nested_directory,
            "--depth",
            "2",
            "--format",
            "json",
            "--output-dir",
            output_dir,
        ],
    )

    assert result.exit_code == 0

    mock_export.assert_called_once()


def test_comparison_export_with_depth_limit(
    runner, nested_directory, output_dir, monkeypatch
):
    """Test comparison export with depth limit."""
    compare_dir = os.path.join(os.path.dirname(nested_directory), "compare_dir")
    os.makedirs(compare_dir, exist_ok=True)

    level1 = os.path.join(compare_dir, "level1")
    os.makedirs(level1, exist_ok=True)

    with open(os.path.join(level1, "level1_file.txt"), "w") as f:
        f.write("Level 1 file")

    os.makedirs(output_dir, exist_ok=True)

    result = runner.invoke(
        app,
        [
            "compare",
            nested_directory,
            compare_dir,
            "--depth",
            "2",
            "--save-as",
            "txt",
            "--output-dir",
            output_dir,
        ],
    )

    assert result.exit_code == 0

    export_path = os.path.join(output_dir, "comparison.txt")
    if os.path.exists(export_path):
        with open(export_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert len(content) > 0
