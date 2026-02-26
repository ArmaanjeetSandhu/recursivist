import json
import os
import shutil
from typing import List

import pytest
from typer.testing import CliRunner

from recursivist.cli import app
from recursivist.core import get_directory_structure


def test_get_directory_structure_with_no_depth_limit(deeply_nested_directory: str):
    """Test that structure is built without depth limits when max_depth=0."""
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

    def check_no_max_depth_flags(structure):
        assert "_max_depth_reached" not in structure
        for key, value in structure.items():
            if key != "_files" and isinstance(value, dict):
                check_no_max_depth_flags(value)

    check_no_max_depth_flags(structure)


@pytest.mark.parametrize(
    "depth,max_depth_in_level",
    [
        (1, ["level1"]),
        (2, ["level1/level2", "level1/level1_dir1"]),
        (3, ["level1/level2/level3"]),
    ],
)
def test_get_directory_structure_with_depth_limits(
    deeply_nested_directory: str, depth: int, max_depth_in_level: List[str]
):
    """Test that structure is limited to specified depth."""
    structure, _ = get_directory_structure(deeply_nested_directory, max_depth=depth)

    def check_path_has_max_depth(path_segments: List[str]) -> bool:
        current = structure
        for segment in path_segments:
            if segment in current:
                current = current[segment]
            else:
                return False
        return "_max_depth_reached" in current

    for path in max_depth_in_level:
        segments = path.split("/")
        assert check_path_has_max_depth(segments), (
            f"No max_depth_reached flag in {path}"
        )


def test_visualize_command_with_depth_limit(
    runner: CliRunner, deeply_nested_directory: str
):
    """Test CLI visualize command with depth limits."""
    result = runner.invoke(app, ["visualize", deeply_nested_directory, "--depth", "1"])
    assert result.exit_code == 0
    assert "level1" in result.stdout
    assert "(max depth reached)" in result.stdout
    assert "level2" not in result.stdout
    result = runner.invoke(app, ["visualize", deeply_nested_directory, "--depth", "2"])
    assert result.exit_code == 0
    assert "level1" in result.stdout
    assert "level2" in result.stdout
    assert "(max depth reached)" in result.stdout
    assert "level3" not in result.stdout


def test_export_command_with_depth_limit(
    runner: CliRunner, deeply_nested_directory: str, output_dir: str
):
    """Test CLI export command with depth limits."""
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
    with open(export_file, encoding="utf-8") as f:
        data = json.load(f)
    assert "structure" in data
    assert "level1" in data["structure"]
    assert "level2" in data["structure"]["level1"]
    assert "_max_depth_reached" in data["structure"]["level1"]["level2"]


def test_compare_command_with_depth_limit(
    runner: CliRunner, deeply_nested_directory: str, temp_dir: str
):
    """Test CLI compare command with depth limits."""
    compare_dir = os.path.join(os.path.dirname(temp_dir), "compare_dir")
    if os.path.exists(compare_dir):
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
    runner: CliRunner, deeply_nested_directory: str, temp_dir: str, output_dir: str
):
    """Test exporting comparison with depth limits."""
    compare_dir = os.path.join(os.path.dirname(temp_dir), "compare_export_dir")
    if os.path.exists(compare_dir):
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
    with open(export_file, encoding="utf-8") as f:
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


def test_depth_combined_with_filters(runner: CliRunner, deeply_nested_directory: str):
    """Test combining depth limits with other filters."""
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


@pytest.mark.parametrize("depth", [1, 2, 3, 4])
def test_export_with_different_depth_limits(
    runner: CliRunner, deeply_nested_directory: str, output_dir: str, depth: int
):
    """Test exporting with different depth limits."""
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
    with open(export_file, encoding="utf-8") as f:
        data = json.load(f)
    current = data["structure"]
    assert "level1" in current
    current = current["level1"]
    if depth == 1:
        assert "_max_depth_reached" in current
        return
    assert "level2" in current
    current = current["level2"]
    if depth == 2:
        assert "_max_depth_reached" in current
        return
    assert "level3" in current
    current = current["level3"]
    if depth == 3:
        assert "_max_depth_reached" in current
        return
    assert "level4" in current
    current = current["level4"]
    if depth == 4:
        assert "_max_depth_reached" in current
        return


def test_unlimited_depth(runner: CliRunner, deeply_nested_directory: str):
    """Test with unlimited depth (depth=0)."""
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
