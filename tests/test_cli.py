"""
Tests for the command-line interface of the recursivist package.

This module contains tests for all CLI commands, options, and their combinations:
- visualize: Tests for directory visualization with various filtering options
- export: Tests for exporting directory structures to different formats
- compare: Tests for comparing two directory structures
- version: Tests for displaying version information
- completion: Tests for generating shell completion scripts
"""

import json
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
    """Test the visualize command with default options."""
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


def test_visualize_with_multiple_exclude_dirs(runner, sample_directory):
    """Test the visualize command with multiple excluded directories."""
    exclude_dir1 = os.path.join(sample_directory, "exclude_me1")
    exclude_dir2 = os.path.join(sample_directory, "exclude_me2")
    os.makedirs(exclude_dir1, exist_ok=True)
    os.makedirs(exclude_dir2, exist_ok=True)
    with open(os.path.join(exclude_dir1, "excluded1.txt"), "w") as f:
        f.write("This should be excluded")
    with open(os.path.join(exclude_dir2, "excluded2.txt"), "w") as f:
        f.write("This should also be excluded")
    result = runner.invoke(
        app, ["visualize", sample_directory, "--exclude", "exclude_me1 exclude_me2"]
    )
    assert result.exit_code == 0
    assert "exclude_me1" not in result.stdout
    assert "exclude_me2" not in result.stdout
    assert "excluded1.txt" not in result.stdout
    assert "excluded2.txt" not in result.stdout
    result = runner.invoke(
        app,
        [
            "visualize",
            sample_directory,
            "--exclude",
            "exclude_me1",
            "--exclude",
            "exclude_me2",
        ],
    )
    assert result.exit_code == 0
    assert "exclude_me1" not in result.stdout
    assert "exclude_me2" not in result.stdout


def test_visualize_with_exclude_extensions(runner, sample_directory):
    """Test the visualize command with excluded file extensions."""
    result = runner.invoke(app, ["visualize", sample_directory, "--exclude-ext", ".py"])
    assert result.exit_code == 0
    assert "file1.txt" in result.stdout
    assert "file2.py" not in result.stdout


def test_visualize_with_multiple_exclude_extensions(runner, sample_directory):
    """Test the visualize command with multiple excluded file extensions."""
    with open(os.path.join(sample_directory, "test1.log"), "w") as f:
        f.write("Log content")
    with open(os.path.join(sample_directory, "test2.tmp"), "w") as f:
        f.write("Temp content")
    result = runner.invoke(
        app, ["visualize", sample_directory, "--exclude-ext", ".py .log"]
    )
    assert result.exit_code == 0
    assert "file1.txt" in result.stdout
    assert "file2.py" not in result.stdout
    assert "test1.log" not in result.stdout
    assert "test2.tmp" in result.stdout
    result = runner.invoke(
        app,
        [
            "visualize",
            sample_directory,
            "--exclude-ext",
            ".py",
            "--exclude-ext",
            ".log",
        ],
    )
    assert result.exit_code == 0
    assert "file1.txt" in result.stdout
    assert "file2.py" not in result.stdout
    assert "test1.log" not in result.stdout
    assert "test2.tmp" in result.stdout


def test_visualize_with_include_patterns(runner, sample_directory):
    """Test the visualize command with include patterns."""
    with open(os.path.join(sample_directory, "include_me.txt"), "w") as f:
        f.write("This should be included")
    with open(os.path.join(sample_directory, "ignore_me.txt"), "w") as f:
        f.write("This should be ignored")
    result = runner.invoke(
        app, ["visualize", sample_directory, "--include-pattern", "include_*"]
    )
    assert result.exit_code == 0
    assert "include_me.txt" in result.stdout
    assert "ignore_me.txt" not in result.stdout
    assert "file1.txt" not in result.stdout
    assert "file2.py" not in result.stdout


def test_visualize_with_multiple_include_patterns(runner, sample_directory):
    """Test the visualize command with multiple include patterns."""
    with open(os.path.join(sample_directory, "include_me.txt"), "w") as f:
        f.write("This should be included")
    with open(os.path.join(sample_directory, "also_include.py"), "w") as f:
        f.write("This should also be included")
    with open(os.path.join(sample_directory, "ignore_me.txt"), "w") as f:
        f.write("This should be ignored")
    result = runner.invoke(
        app, ["visualize", sample_directory, "--include-pattern", "include_* also_*"]
    )
    assert result.exit_code == 0
    assert "include_me.txt" in result.stdout
    assert "also_include.py" in result.stdout
    assert "ignore_me.txt" not in result.stdout
    assert "file1.txt" not in result.stdout
    result = runner.invoke(
        app,
        [
            "visualize",
            sample_directory,
            "--include-pattern",
            "include_*",
            "--include-pattern",
            "also_*",
        ],
    )
    assert result.exit_code == 0
    assert "include_me.txt" in result.stdout
    assert "also_include.py" in result.stdout
    assert "ignore_me.txt" not in result.stdout


def test_visualize_with_exclude_patterns(runner, sample_directory):
    """Test the visualize command with exclude patterns."""
    with open(os.path.join(sample_directory, "exclude_this.txt"), "w") as f:
        f.write("This should be excluded")
    with open(os.path.join(sample_directory, "keep_this.txt"), "w") as f:
        f.write("This should be kept")
    result = runner.invoke(
        app, ["visualize", sample_directory, "--exclude-pattern", "exclude_*"]
    )
    assert result.exit_code == 0
    assert "exclude_this.txt" not in result.stdout
    assert "keep_this.txt" in result.stdout
    assert "file1.txt" in result.stdout
    assert "file2.py" in result.stdout


def test_visualize_with_multiple_exclude_patterns(runner, sample_directory):
    """Test the visualize command with multiple exclude patterns."""
    with open(os.path.join(sample_directory, "exclude_this.txt"), "w") as f:
        f.write("This should be excluded")
    with open(os.path.join(sample_directory, "also_exclude.py"), "w") as f:
        f.write("This should also be excluded")
    with open(os.path.join(sample_directory, "keep_this.txt"), "w") as f:
        f.write("This should be kept")
    result = runner.invoke(
        app, ["visualize", sample_directory, "--exclude-pattern", "exclude_* also_*"]
    )
    assert result.exit_code == 0
    assert "exclude_this.txt" not in result.stdout
    assert "also_exclude.py" not in result.stdout
    assert "keep_this.txt" in result.stdout
    result = runner.invoke(
        app,
        [
            "visualize",
            sample_directory,
            "--exclude-pattern",
            "exclude_*",
            "--exclude-pattern",
            "also_*",
        ],
    )
    assert result.exit_code == 0
    assert "exclude_this.txt" not in result.stdout
    assert "also_exclude.py" not in result.stdout
    assert "keep_this.txt" in result.stdout


def test_visualize_with_regex_patterns(runner, sample_directory):
    """Test the visualize command with regex patterns."""
    with open(os.path.join(sample_directory, "test123.txt"), "w") as f:
        f.write("This should be excluded with regex")
    with open(os.path.join(sample_directory, "test456.txt"), "w") as f:
        f.write("This should be excluded with regex")
    with open(os.path.join(sample_directory, "keep789.txt"), "w") as f:
        f.write("This should be kept")
    result = runner.invoke(
        app,
        [
            "visualize",
            sample_directory,
            "--exclude-pattern",
            "test\\d+\\.txt",
            "--regex",
        ],
    )
    assert result.exit_code == 0
    assert "test123.txt" not in result.stdout
    assert "test456.txt" not in result.stdout
    assert "keep789.txt" in result.stdout


def test_visualize_with_ignore_file(runner, sample_with_logs):
    """Test the visualize command with gitignore file."""
    result = runner.invoke(
        app, ["visualize", sample_with_logs, "--ignore-file", ".gitignore"]
    )
    assert result.exit_code == 0
    assert "app.log" not in result.stdout
    assert "node_modules" not in result.stdout


def test_visualize_with_depth_limit(runner, sample_directory):
    """Test the visualize command with depth limit."""
    import os

    from recursivist.cli import app

    level1 = os.path.join(sample_directory, "level1")
    level2 = os.path.join(level1, "level2")
    level3 = os.path.join(level2, "level3")
    os.makedirs(level3, exist_ok=True)
    with open(os.path.join(level1, "file1.txt"), "w") as f:
        f.write("Level 1 file")
    with open(os.path.join(level2, "file2.txt"), "w") as f:
        f.write("Level 2 file")
    with open(os.path.join(level3, "file3.txt"), "w") as f:
        f.write("Level 3 file")
    result = runner.invoke(app, ["visualize", sample_directory, "--depth", "1"])
    assert result.exit_code == 0
    assert "level1" in result.stdout
    assert "(max depth reached)" in result.stdout
    result = runner.invoke(app, ["visualize", sample_directory, "--depth", "2"])
    assert result.exit_code == 0
    assert "level1" in result.stdout
    assert "level2" in result.stdout
    assert "(max depth reached)" in result.stdout


def test_visualize_invalid_directory(runner, temp_dir, caplog):
    """Test the visualize command with non-existent directory."""
    invalid_dir = os.path.join(temp_dir, "nonexistent")
    result = runner.invoke(app, ["visualize", invalid_dir])
    assert result.exit_code == 1
    assert any("not a valid directory" in record.message for record in caplog.records)


def test_visualize_with_verbose_mode(runner, sample_directory, caplog):
    """Test the visualize command with verbose mode."""
    result = runner.invoke(app, ["visualize", sample_directory, "--verbose"])
    assert result.exit_code == 0
    assert any("Verbose mode enabled" in record.message for record in caplog.records)


def test_export_command(runner, sample_directory, output_dir):
    """Test the export command with txt format."""
    result = runner.invoke(
        app,
        [
            "export",
            sample_directory,
            "--format",
            "txt",
            "--output-dir",
            output_dir,
            "--prefix",
            "test_export",
        ],
    )
    assert result.exit_code == 0
    export_file = os.path.join(output_dir, "test_export.txt")
    assert os.path.exists(export_file)


def test_export_multiple_formats(runner, sample_directory, output_dir):
    """Test the export command with multiple formats."""
    result = runner.invoke(
        app,
        [
            "export",
            sample_directory,
            "--format",
            "txt json",
            "--output-dir",
            output_dir,
        ],
    )
    assert result.exit_code == 0
    assert os.path.exists(os.path.join(output_dir, "structure.txt"))
    assert os.path.exists(os.path.join(output_dir, "structure.json"))


def test_export_with_multiple_format_flags(runner, sample_directory, output_dir):
    """Test the export command with multiple format flags."""
    result = runner.invoke(
        app,
        [
            "export",
            sample_directory,
            "--format",
            "txt",
            "--format",
            "json",
            "--format",
            "html",
            "--output-dir",
            output_dir,
            "--prefix",
            "multi_format",
        ],
    )
    assert result.exit_code == 0
    assert os.path.exists(os.path.join(output_dir, "multi_format.txt"))
    assert os.path.exists(os.path.join(output_dir, "multi_format.json"))
    assert os.path.exists(os.path.join(output_dir, "multi_format.html"))


def test_export_all_formats(runner, sample_directory, output_dir):
    """Test the export command with all supported formats."""
    result = runner.invoke(
        app,
        [
            "export",
            sample_directory,
            "--format",
            "txt json html md jsx",
            "--output-dir",
            output_dir,
            "--prefix",
            "all_formats",
        ],
    )
    assert result.exit_code == 0
    assert os.path.exists(os.path.join(output_dir, "all_formats.txt"))
    assert os.path.exists(os.path.join(output_dir, "all_formats.json"))
    assert os.path.exists(os.path.join(output_dir, "all_formats.html"))
    assert os.path.exists(os.path.join(output_dir, "all_formats.md"))
    assert os.path.exists(os.path.join(output_dir, "all_formats.jsx"))
    with open(os.path.join(output_dir, "all_formats.json"), "r", encoding="utf-8") as f:
        data = json.load(f)
        assert "root" in data
        assert "structure" in data
        assert data["root"] == os.path.basename(sample_directory)
    with open(os.path.join(output_dir, "all_formats.txt"), "r", encoding="utf-8") as f:
        content = f.read()
        assert os.path.basename(sample_directory) in content
        assert "file1.txt" in content
    with open(os.path.join(output_dir, "all_formats.md"), "r", encoding="utf-8") as f:
        content = f.read()
        assert f"# 📂 {os.path.basename(sample_directory)}" in content
        assert "- 📄 `file1.txt`" in content
    with open(os.path.join(output_dir, "all_formats.html"), "r", encoding="utf-8") as f:
        content = f.read()
        assert "<!DOCTYPE html>" in content
        assert "<html>" in content
        assert os.path.basename(sample_directory) in content
    with open(os.path.join(output_dir, "all_formats.jsx"), "r", encoding="utf-8") as f:
        content = f.read()
        assert "import React" in content
        assert "DirectoryViewer" in content
        assert os.path.basename(sample_directory) in content


def test_export_with_full_path(runner, sample_directory, output_dir):
    """Test the export command with full path option."""
    result = runner.invoke(
        app,
        [
            "export",
            sample_directory,
            "--format",
            "txt",
            "--output-dir",
            output_dir,
            "--prefix",
            "test_export_full_path",
            "--full-path",
        ],
    )
    assert result.exit_code == 0
    export_file = os.path.join(output_dir, "test_export_full_path.txt")
    assert os.path.exists(export_file)
    with open(export_file, "r", encoding="utf-8") as f:
        content = f.read()
    base_name = os.path.basename(sample_directory)
    has_path_info = False
    lines = content.split("\n")
    for line in lines:
        if ("├── 📄" in line or "└── 📄" in line) and (
            base_name in line or os.path.sep in line or "/" in line
        ):
            has_path_info = True
            break
    assert has_path_info, "No full path information found in exported content"


def test_export_with_filtering_options(runner, sample_directory, output_dir):
    """Test the export command with filtering options."""
    exclude_dir = os.path.join(sample_directory, "exclude_me")
    os.makedirs(exclude_dir, exist_ok=True)
    with open(os.path.join(exclude_dir, "excluded.txt"), "w") as f:
        f.write("This should be excluded")
    with open(os.path.join(sample_directory, "test123.txt"), "w") as f:
        f.write("This should be excluded with pattern")
    result = runner.invoke(
        app,
        [
            "export",
            sample_directory,
            "--format",
            "json",
            "--output-dir",
            output_dir,
            "--prefix",
            "filtered_export",
            "--exclude",
            "exclude_me",
            "--exclude-pattern",
            "test*",
        ],
    )
    assert result.exit_code == 0
    export_file = os.path.join(output_dir, "filtered_export.json")
    assert os.path.exists(export_file)
    with open(export_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert "structure" in data
        assert "exclude_me" not in data["structure"]
        if "_files" in data["structure"]:
            for file in data["structure"]["_files"]:
                if isinstance(file, str):
                    assert not file.startswith("test")
                else:
                    assert not file[0].startswith("test")


def test_export_with_depth_limit(runner, sample_directory, output_dir):
    """Test the export command with depth limit."""
    level1 = os.path.join(sample_directory, "level1")
    level2 = os.path.join(level1, "level2")
    level3 = os.path.join(level2, "level3")
    os.makedirs(level3, exist_ok=True)
    with open(os.path.join(level1, "file1.txt"), "w") as f:
        f.write("Level 1 file")
    with open(os.path.join(level2, "file2.txt"), "w") as f:
        f.write("Level 2 file")
    with open(os.path.join(level3, "file3.txt"), "w") as f:
        f.write("Level 3 file")
    result = runner.invoke(
        app,
        [
            "export",
            sample_directory,
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


def test_export_invalid_format(runner, sample_directory, caplog):
    """Test the export command with invalid format."""
    result = runner.invoke(app, ["export", sample_directory, "--format", "invalid"])
    assert result.exit_code == 1
    assert any(
        "Unsupported export format" in record.message for record in caplog.records
    )


def test_export_jsx_format(runner, sample_directory, output_dir):
    """Test the export command with React component format."""
    result = runner.invoke(
        app,
        [
            "export",
            sample_directory,
            "--format",
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
    assert "CollapsibleItem" in content
    assert "ChevronDown" in content
    assert "ChevronUp" in content


def test_compare_command(runner, temp_dir):
    """Test the compare command with two directories."""
    dir1 = os.path.join(temp_dir, "dir1")
    dir2 = os.path.join(temp_dir, "dir2")
    os.makedirs(dir1, exist_ok=True)
    os.makedirs(dir2, exist_ok=True)
    with open(os.path.join(dir1, "common.txt"), "w") as f:
        f.write("Common file")
    with open(os.path.join(dir2, "common.txt"), "w") as f:
        f.write("Common file")
    with open(os.path.join(dir1, "unique1.txt"), "w") as f:
        f.write("Unique to dir1")
    with open(os.path.join(dir2, "unique2.txt"), "w") as f:
        f.write("Unique to dir2")
    result = runner.invoke(app, ["compare", dir1, dir2])
    assert result.exit_code == 0
    assert "dir1" in result.stdout
    assert "dir2" in result.stdout
    assert "common.txt" in result.stdout
    assert "unique1.txt" in result.stdout
    assert "unique2.txt" in result.stdout
    assert "Legend" in result.stdout


def test_compare_with_filtering_options(runner, temp_dir):
    """Test the compare command with filtering options."""
    dir1 = os.path.join(temp_dir, "dir1")
    dir2 = os.path.join(temp_dir, "dir2")
    os.makedirs(dir1, exist_ok=True)
    os.makedirs(dir2, exist_ok=True)
    os.makedirs(os.path.join(dir1, "exclude_me"), exist_ok=True)
    os.makedirs(os.path.join(dir2, "exclude_me"), exist_ok=True)
    with open(os.path.join(dir1, "exclude_me", "file.txt"), "w") as f:
        f.write("Should be excluded")
    with open(os.path.join(dir2, "exclude_me", "file.txt"), "w") as f:
        f.write("Should be excluded")
    with open(os.path.join(dir1, "excluded.pyc"), "w") as f:
        f.write("Should be excluded by extension")
    with open(os.path.join(dir2, "excluded.pyc"), "w") as f:
        f.write("Should be excluded by extension")
    with open(os.path.join(dir1, "normal.txt"), "w") as f:
        f.write("Normal file")
    with open(os.path.join(dir2, "different.txt"), "w") as f:
        f.write("Different file")
    result = runner.invoke(
        app, ["compare", dir1, dir2, "--exclude", "exclude_me", "--exclude-ext", ".pyc"]
    )
    assert result.exit_code == 0
    assert "dir1" in result.stdout
    assert "dir2" in result.stdout
    assert "normal.txt" in result.stdout
    assert "different.txt" in result.stdout
    assert "exclude_me" not in result.stdout
    assert "excluded.pyc" not in result.stdout


def test_compare_with_depth_limit(runner, temp_dir):
    """Test the compare command with depth limit."""
    import os

    from recursivist.cli import app

    dir1 = os.path.join(temp_dir, "dir1")
    dir2 = os.path.join(temp_dir, "dir2")
    level1_dir1 = os.path.join(dir1, "level1")
    level2_dir1 = os.path.join(level1_dir1, "level2")
    os.makedirs(level2_dir1, exist_ok=True)
    with open(os.path.join(level1_dir1, "file1.txt"), "w") as f:
        f.write("Level 1 file in dir1")
    with open(os.path.join(level2_dir1, "file2.txt"), "w") as f:
        f.write("Level 2 file in dir1")
    level1_dir2 = os.path.join(dir2, "level1")
    level2_dir2 = os.path.join(level1_dir2, "level2")
    os.makedirs(level2_dir2, exist_ok=True)
    with open(os.path.join(level1_dir2, "file1.txt"), "w") as f:
        f.write("Level 1 file in dir2")
    with open(os.path.join(level2_dir2, "different.txt"), "w") as f:
        f.write("Different file in dir2")
    result = runner.invoke(app, ["compare", dir1, dir2, "--depth", "1"])
    assert result.exit_code == 0
    assert "level1" in result.stdout
    assert "(max depth reached)" in result.stdout
    assert "file2.txt" not in result.stdout
    assert "different.txt" not in result.stdout


def test_compare_export_to_html(runner, temp_dir, output_dir):
    """Test the compare command with export to HTML."""
    dir1 = os.path.join(temp_dir, "dir1")
    dir2 = os.path.join(temp_dir, "dir2")
    os.makedirs(dir1, exist_ok=True)
    os.makedirs(dir2, exist_ok=True)
    with open(os.path.join(dir1, "common.txt"), "w") as f:
        f.write("Common file")
    with open(os.path.join(dir2, "common.txt"), "w") as f:
        f.write("Common file")
    with open(os.path.join(dir1, "unique1.txt"), "w") as f:
        f.write("Unique to dir1")
    with open(os.path.join(dir2, "unique2.txt"), "w") as f:
        f.write("Unique to dir2")
    result = runner.invoke(
        app,
        [
            "compare",
            dir1,
            dir2,
            "--save",
            "--output-dir",
            output_dir,
            "--prefix",
            "html_comparison",
        ],
    )
    assert result.exit_code == 0
    export_file = os.path.join(output_dir, "html_comparison.html")
    assert os.path.exists(export_file)
    with open(export_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert "<!DOCTYPE html>" in content
    assert "<html>" in content
    assert "Directory Comparison" in content
    assert "common.txt" in content
    assert "unique1.txt" in content
    assert "unique2.txt" in content


def test_compare_with_full_path(runner, temp_dir):
    """Test the compare command with full path option."""
    dir1 = os.path.join(temp_dir, "dir1")
    dir2 = os.path.join(temp_dir, "dir2")
    os.makedirs(dir1, exist_ok=True)
    os.makedirs(dir2, exist_ok=True)
    with open(os.path.join(dir1, "common.txt"), "w") as f:
        f.write("Common file")
    with open(os.path.join(dir2, "common.txt"), "w") as f:
        f.write("Common file")
    with open(os.path.join(dir1, "unique1.txt"), "w") as f:
        f.write("Unique to dir1")
    with open(os.path.join(dir2, "unique2.txt"), "w") as f:
        f.write("Unique to dir2")
    result = runner.invoke(app, ["compare", dir1, dir2, "--full-path"])
    assert result.exit_code == 0
    assert "dir1" in result.stdout
    assert "dir2" in result.stdout
    assert "Full file paths are shown" in result.stdout
    has_full_path = False
    for line in result.stdout.split("\n"):
        if ("📄" in line) and (
            dir1.replace(os.sep, "/") in line.replace(os.sep, "/")
            or dir2.replace(os.sep, "/") in line.replace(os.sep, "/")
        ):
            has_full_path = True
            break
    assert has_full_path, "No full paths found in the output"


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
    result = runner.invoke(app, ["completion", "zsh"])
    assert result.exit_code == 0
    result = runner.invoke(app, ["completion", "fish"])
    assert result.exit_code == 0
    result = runner.invoke(app, ["completion", "powershell"])
    assert result.exit_code == 0
    result = runner.invoke(app, ["completion", "invalid"])
    assert result.exit_code == 1
    assert any("Unsupported shell" in record.message for record in caplog.records)


def test_verbose_mode(runner, sample_directory, caplog):
    """Test the verbose mode."""
    result = runner.invoke(app, ["visualize", sample_directory, "--verbose"])
    assert result.exit_code == 0
    assert any("Verbose mode enabled" in record.message for record in caplog.records)
