"""
Tests for the depth limit functionality of the recursivist package.

This module contains tests that verify the depth limiting capabilities:
- Structure generation with various depth limits
- Visual indicators for max depth reached
- CLI commands with depth limits
- Exports with depth limits
- Comparison with depth limits
"""

import json
import os
from typing import Any

import pytest
from typer.testing import CliRunner

from recursivist.cli import app
from recursivist.core import get_directory_structure


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def deeply_nested_directory(temp_dir: str):
    """
    Create a deeply nested directory structure for testing depth limits.

    Structure:
    temp_dir/
    ├── level1/
    │   ├── level1_file.txt
    │   ├── level1_dir1/
    │   │   ├── level2_file1.txt
    │   │   └── level2_file2.txt
    │   └── level2/
    │       ├── level2_file.txt
    │       └── level3/
    │           ├── level3_file.txt
    │           └── level4/
    │               ├── level4_file.txt
    │               └── level5/
    │                   ├── level5_file.txt
    │                   └── level6/
    │                       └── level6_file.txt
    └── root_file.txt
    """
    level1 = os.path.join(temp_dir, "level1")
    level1_dir1 = os.path.join(level1, "level1_dir1")
    level2 = os.path.join(level1, "level2")
    level3 = os.path.join(level2, "level3")
    level4 = os.path.join(level3, "level4")
    level5 = os.path.join(level4, "level5")
    level6 = os.path.join(level5, "level6")
    os.makedirs(level1, exist_ok=True)
    os.makedirs(level1_dir1, exist_ok=True)
    os.makedirs(level2, exist_ok=True)
    os.makedirs(level3, exist_ok=True)
    os.makedirs(level4, exist_ok=True)
    os.makedirs(level5, exist_ok=True)
    os.makedirs(level6, exist_ok=True)
    with open(os.path.join(temp_dir, "root_file.txt"), "w") as f:
        f.write("Root level file")
    with open(os.path.join(level1, "level1_file.txt"), "w") as f:
        f.write("Level 1 file")
    with open(os.path.join(level1_dir1, "level2_file1.txt"), "w") as f:
        f.write("Level 2 file in parallel directory")
    with open(os.path.join(level1_dir1, "level2_file2.txt"), "w") as f:
        f.write("Another level 2 file")
    with open(os.path.join(level2, "level2_file.txt"), "w") as f:
        f.write("Level 2 file")
    with open(os.path.join(level3, "level3_file.txt"), "w") as f:
        f.write("Level 3 file")
    with open(os.path.join(level4, "level4_file.txt"), "w") as f:
        f.write("Level 4 file")
    with open(os.path.join(level5, "level5_file.txt"), "w") as f:
        f.write("Level 5 file")
    with open(os.path.join(level6, "level6_file.txt"), "w") as f:
        f.write("Level 6 file")
    return temp_dir


def test_get_directory_structure_with_no_depth_limit(deeply_nested_directory: Any):
    """Test the directory structure function with no depth limit."""
    structure, _ = get_directory_structure(deeply_nested_directory, max_depth=0)
    assert "level1" in structure
    assert "level1_dir1" in structure["level1"]
    assert "level2" in structure["level1"]
    assert "level3" in structure["level1"]["level2"]
    assert "level4" in structure["level1"]["level2"]["level3"]
    assert "level5" in structure["level1"]["level2"]["level3"]["level4"]
    assert "level6" in structure["level1"]["level2"]["level3"]["level4"]["level5"]
    assert "_max_depth_reached" not in structure
    assert "_max_depth_reached" not in structure["level1"]
    assert "_max_depth_reached" not in structure["level1"]["level2"]


def test_get_directory_structure_with_depth_limits(deeply_nested_directory: Any):
    """Test the directory structure function with various depth limits."""
    structure, _ = get_directory_structure(deeply_nested_directory, max_depth=1)
    assert "level1" in structure
    assert "_max_depth_reached" in structure["level1"]
    structure, _ = get_directory_structure(deeply_nested_directory, max_depth=2)
    assert "level1" in structure
    assert "level2" in structure["level1"]
    assert "_max_depth_reached" in structure["level1"]["level2"]
    if "level1_dir1" in structure["level1"]:
        assert "_max_depth_reached" in structure["level1"]["level1_dir1"]


def test_get_directory_structure_with_zero_depth(deeply_nested_directory: Any):
    """Test the directory structure function with zero depth limit (meaning unlimited)."""
    structure, _ = get_directory_structure(deeply_nested_directory, max_depth=0)
    assert "level1" in structure
    assert "level1_dir1" in structure["level1"]
    assert "level2" in structure["level1"]
    assert "level3" in structure["level1"]["level2"]
    assert "level4" in structure["level1"]["level2"]["level3"]
    assert "level5" in structure["level1"]["level2"]["level3"]["level4"]
    assert "level6" in structure["level1"]["level2"]["level3"]["level4"]["level5"]

    def check_no_max_depth_flags(structure):
        assert "_max_depth_reached" not in structure
        for key, value in structure.items():
            if key != "_files" and isinstance(value, dict):
                check_no_max_depth_flags(value)

    check_no_max_depth_flags(structure)


def test_get_directory_structure_with_depth_1(deeply_nested_directory: Any):
    """Test the directory structure function with depth limit 1."""
    structure, _ = get_directory_structure(deeply_nested_directory, max_depth=1)
    assert "level1" in structure
    assert "_max_depth_reached" in structure["level1"]
    assert "level2" not in structure["level1"]
    assert "level1_dir1" not in structure["level1"]


def test_visualize_command_with_depth_limit(
    runner: CliRunner, deeply_nested_directory: Any
):
    """Test the visualize command with depth limit."""
    result = runner.invoke(app, ["visualize", deeply_nested_directory, "--depth", "1"])
    assert result.exit_code == 0
    assert "level1" in result.stdout
    assert "(max depth reached)" in result.stdout
    result = runner.invoke(app, ["visualize", deeply_nested_directory, "--depth", "2"])
    assert result.exit_code == 0
    assert "level1" in result.stdout
    assert "level2" in result.stdout
    assert "(max depth reached)" in result.stdout


def test_export_command_with_depth_limit(
    runner: CliRunner, deeply_nested_directory: Any, output_dir: str
):
    """Test the export command with depth limit."""
    result = runner.invoke(
        app,
        [
            "export",
            deeply_nested_directory,
            "--format",
            "json",
            "--output-dir",
            output_dir,
            "--prefix",
            "depth_limited",
            "--depth",
            "2",
        ],
    )
    assert result.exit_code == 0
    export_file = os.path.join(output_dir, "depth_limited.json")
    assert os.path.exists(export_file)
    with open(export_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert "structure" in data
        assert "level1" in data["structure"]
        assert "level2" in data["structure"]["level1"]
        assert "_max_depth_reached" in data["structure"]["level1"]["level2"]


def test_compare_command_with_depth_limit(
    runner: CliRunner, deeply_nested_directory: Any, temp_dir: str
):
    """Test the compare command with depth limit."""
    compare_dir = os.path.join(os.path.dirname(temp_dir), "compare_dir")
    if os.path.exists(compare_dir):
        import shutil

        shutil.rmtree(compare_dir)
    os.makedirs(compare_dir, exist_ok=True)
    level1 = os.path.join(compare_dir, "level1")
    level2 = os.path.join(level1, "level2")
    level3 = os.path.join(level2, "level3")
    os.makedirs(level1, exist_ok=True)
    os.makedirs(level2, exist_ok=True)
    os.makedirs(level3, exist_ok=True)
    with open(os.path.join(compare_dir, "different_root.txt"), "w") as f:
        f.write("Different root file")
    with open(os.path.join(level1, "level1_file.txt"), "w") as f:
        f.write("Level 1 file with different content")
    with open(os.path.join(level2, "different_level2.txt"), "w") as f:
        f.write("Different level 2 file")
    with open(os.path.join(level3, "level3_file.txt"), "w") as f:
        f.write("Level 3 file")
    result = runner.invoke(
        app, ["compare", deeply_nested_directory, compare_dir, "--depth", "2"]
    )
    assert result.exit_code == 0
    assert "level1" in result.stdout
    assert "level2" in result.stdout
    assert "level1_file.txt" in result.stdout
    assert "different_root.txt" in result.stdout
    assert "level3" not in result.stdout
    assert "level3_file.txt" not in result.stdout
    assert "(max depth reached)" in result.stdout


def test_compare_export_with_depth_limit(
    runner: CliRunner, deeply_nested_directory: Any, temp_dir: str, output_dir: str
):
    """Test comparison export with depth limit."""
    compare_dir = os.path.join(os.path.dirname(temp_dir), "compare_export_dir")
    if os.path.exists(compare_dir):
        import shutil

        shutil.rmtree(compare_dir)
    os.makedirs(compare_dir, exist_ok=True)
    level1 = os.path.join(compare_dir, "level1")
    level2 = os.path.join(level1, "level2")
    level3 = os.path.join(level2, "level3")
    os.makedirs(level1, exist_ok=True)
    os.makedirs(level2, exist_ok=True)
    os.makedirs(level3, exist_ok=True)
    with open(os.path.join(compare_dir, "different_root.txt"), "w") as f:
        f.write("Different root file")
    with open(os.path.join(level1, "level1_file.txt"), "w") as f:
        f.write("Level 1 file with different content")
    with open(os.path.join(level2, "different_level2.txt"), "w") as f:
        f.write("Different level 2 file")
    with open(os.path.join(level3, "level3_file.txt"), "w") as f:
        f.write("Level 3 file")
    result = runner.invoke(
        app,
        [
            "compare",
            deeply_nested_directory,
            compare_dir,
            "--depth",
            "2",
            "--save",
            "--output-dir",
            output_dir,
            "--prefix",
            "depth_limited_compare",
        ],
    )
    assert result.exit_code == 0
    export_file = os.path.join(output_dir, "depth_limited_compare.html")
    assert os.path.exists(export_file)
    with open(export_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert "Directory Comparison" in content
        assert "level1" in content
        assert "level2" in content
        assert "level1_file.txt" in content
        assert "different_root.txt" in content
        assert "level3" not in content or (
            "level3" in content and "max depth reached" in content
        )
        assert "(max depth reached)" in content


def test_depth_combined_with_filters(runner: CliRunner, deeply_nested_directory: Any):
    """Test depth limiting combined with other filtering options."""
    excluded_dir = os.path.join(deeply_nested_directory, "excluded")
    os.makedirs(excluded_dir, exist_ok=True)
    with open(os.path.join(excluded_dir, "excluded.txt"), "w") as f:
        f.write("This should be excluded")
    with open(os.path.join(deeply_nested_directory, "excluded_root.txt"), "w") as f:
        f.write("This should be excluded at root")
    result = runner.invoke(
        app,
        [
            "visualize",
            deeply_nested_directory,
            "--depth",
            "2",
            "--exclude",
            "excluded",
            "--exclude-pattern",
            "excluded_*",
        ],
    )
    assert result.exit_code == 0
    assert "level1" in result.stdout
    assert "level2" in result.stdout
    assert "excluded" not in result.stdout
    assert "excluded_root.txt" not in result.stdout
    assert "(max depth reached)" in result.stdout


def test_export_with_different_depth_limits(
    runner: CliRunner, deeply_nested_directory: Any, output_dir: str
):
    """Test exporting with various depth limits to verify indicator behavior."""
    for depth in [1, 2, 3, 4]:
        result = runner.invoke(
            app,
            [
                "export",
                deeply_nested_directory,
                "--format",
                "json",
                "--output-dir",
                output_dir,
                "--prefix",
                f"depth_{depth}",
                "--depth",
                str(depth),
            ],
        )
        assert result.exit_code == 0
        export_file = os.path.join(output_dir, f"depth_{depth}.json")
        assert os.path.exists(export_file)
        with open(export_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            current = data["structure"]
            assert "level1" in current
            current = current["level1"]
            if depth == 1:
                assert "_max_depth_reached" in current
                continue
            assert "level2" in current
            current = current["level2"]
            if depth == 2:
                assert "_max_depth_reached" in current
                continue
            assert "level3" in current
            current = current["level3"]
            if depth == 3:
                assert "_max_depth_reached" in current
                continue
            assert "level4" in current
            current = current["level4"]
            if depth == 4:
                assert "_max_depth_reached" in current
                continue


def test_unlimited_depth(runner: CliRunner, deeply_nested_directory: Any):
    """Test explicitly setting unlimited depth with --depth 0."""
    level1 = os.path.join(deeply_nested_directory, "level1")
    level2 = os.path.join(level1, "level2")
    level3 = os.path.join(level2, "level3")
    level4 = os.path.join(level3, "level4")
    level5 = os.path.join(level4, "level5")
    level6 = os.path.join(level5, "level6")
    assert os.path.exists(level6), "Test setup error: level6 directory should exist"
    result = runner.invoke(
        app,
        [
            "visualize",
            deeply_nested_directory,
            "--depth",
            "0",
        ],
    )
    assert result.exit_code == 0
    assert "level1" in result.stdout
    assert "level2" in result.stdout
    assert "level3" in result.stdout
    assert "level4" in result.stdout
    assert "level5" in result.stdout
    assert "level6" in result.stdout
    assert "level6_file.txt" in result.stdout
    assert "(max depth reached)" not in result.stdout
