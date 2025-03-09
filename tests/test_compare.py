"""
Tests for the directory comparison functionality of the recursivist package.

This module contains tests for comparing two directory structures:
- Basic comparison functionality
- Full path display in comparisons
- Comparison with filtering options (exclude dirs, patterns, etc.)
- Export of comparisons to different formats
- Visual highlighting of differences
"""

import html
import os
import re

import pytest
from pytest_mock import MockerFixture
from rich.text import Text
from typer.testing import CliRunner

from recursivist.cli import app
from recursivist.compare import (
    build_comparison_tree,
    compare_directory_structures,
    display_comparison,
    export_comparison,
)


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def comparison_directories(temp_dir: str):
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


@pytest.fixture
def complex_comparison_directories(temp_dir: str):
    """
    Create two more complex directories for advanced comparison testing.

    First directory structure:
    dir1/
    ├── .gitignore
    ├── README.md
    ├── src/
    │   ├── main.py
    │   ├── utils.py
    │   └── tests/
    │       ├── test_main.py
    │       └── test_utils.py
    └── docs/
        ├── index.md
        └── api.md

    Second directory structure:
    dir2/
    ├── .gitignore (different content)
    ├── README.md (different content)
    ├── CHANGELOG.md (only in dir2)
    ├── src/
    │   ├── main.py (different content)
    │   ├── new_module.py (only in dir2)
    │   └── tests/
    │       ├── test_main.py
    │       └── test_new_module.py (only in dir2)
    └── docs/
        ├── index.md (different content)
        ├── api.md
        └── examples.md (only in dir2)
    """
    dir1 = os.path.join(temp_dir, "complex_dir1")
    dir2 = os.path.join(temp_dir, "complex_dir2")
    os.makedirs(dir1, exist_ok=True)
    os.makedirs(os.path.join(dir1, "src", "tests"), exist_ok=True)
    os.makedirs(os.path.join(dir1, "docs"), exist_ok=True)
    with open(os.path.join(dir1, ".gitignore"), "w") as f:
        f.write("*.pyc\n__pycache__/\n")
    with open(os.path.join(dir1, "README.md"), "w") as f:
        f.write("# Project\nThis is a test project.\n")
    with open(os.path.join(dir1, "src", "main.py"), "w") as f:
        f.write("def main():\n    print('Hello world')\n")
    with open(os.path.join(dir1, "src", "utils.py"), "w") as f:
        f.write("def helper():\n    return 'helper'\n")
    with open(os.path.join(dir1, "src", "tests", "test_main.py"), "w") as f:
        f.write("def test_main():\n    assert True\n")
    with open(os.path.join(dir1, "src", "tests", "test_utils.py"), "w") as f:
        f.write("def test_helper():\n    assert True\n")
    with open(os.path.join(dir1, "docs", "index.md"), "w") as f:
        f.write("# Documentation\nWelcome to the docs.\n")
    with open(os.path.join(dir1, "docs", "api.md"), "w") as f:
        f.write("# API Reference\nThis is the API reference.\n")
    os.makedirs(dir2, exist_ok=True)
    os.makedirs(os.path.join(dir2, "src", "tests"), exist_ok=True)
    os.makedirs(os.path.join(dir2, "docs"), exist_ok=True)
    with open(os.path.join(dir2, ".gitignore"), "w") as f:
        f.write("*.pyc\n__pycache__/\n*.log\n")
    with open(os.path.join(dir2, "README.md"), "w") as f:
        f.write("# Project\nThis is a test project with updates.\n")
    with open(os.path.join(dir2, "CHANGELOG.md"), "w") as f:
        f.write("# Changelog\n\n## 1.0.0\n- Initial release\n")
    with open(os.path.join(dir2, "src", "main.py"), "w") as f:
        f.write("def main():\n    print('Hello, updated world!')\n")
    with open(os.path.join(dir2, "src", "new_module.py"), "w") as f:
        f.write("def new_function():\n    return 'new function'\n")
    with open(os.path.join(dir2, "src", "tests", "test_main.py"), "w") as f:
        f.write("def test_main():\n    assert True\n")
    with open(os.path.join(dir2, "src", "tests", "test_new_module.py"), "w") as f:
        f.write("def test_new_function():\n    assert True\n")
    with open(os.path.join(dir2, "docs", "index.md"), "w") as f:
        f.write("# Documentation\nWelcome to the updated docs.\n")
    with open(os.path.join(dir2, "docs", "api.md"), "w") as f:
        f.write("# API Reference\nThis is the API reference.\n")
    with open(os.path.join(dir2, "docs", "examples.md"), "w") as f:
        f.write("# Examples\nHere are some examples.\n")
    return dir1, dir2


def test_compare_directory_structures(comparison_directories: tuple[str, str]):
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


def test_compare_directory_structures_with_full_path(
    comparison_directories: tuple[str, str],
):
    """Test that directory structures are correctly compared with full paths."""
    dir1, dir2 = comparison_directories
    structure1, structure2, extensions = compare_directory_structures(
        dir1, dir2, show_full_path=True
    )
    assert "_files" in structure1
    assert "_files" in structure2
    assert isinstance(structure1["_files"][0], tuple)
    assert len(structure1["_files"][0]) == 2
    found = False
    for filename, full_path in structure1["_files"]:
        if filename == "file1.txt":
            found = True
            assert (
                os.path.basename(dir1) in os.path.dirname(full_path)
                or "file1.txt" in full_path
            )
    assert found, "Could not find file1.txt with full path in structure1"


def test_compare_directory_structures_with_exclusions(
    comparison_directories: tuple[str, str],
):
    """Test comparison with directory exclusions."""
    dir1, dir2 = comparison_directories
    exclude_dir_path1 = os.path.join(dir1, "exclude_me")
    exclude_dir_path2 = os.path.join(dir2, "exclude_me")
    os.makedirs(exclude_dir_path1, exist_ok=True)
    os.makedirs(exclude_dir_path2, exist_ok=True)
    with open(os.path.join(exclude_dir_path1, "excluded1.txt"), "w") as f:
        f.write("This should be excluded")
    with open(os.path.join(exclude_dir_path2, "excluded2.txt"), "w") as f:
        f.write("This should be excluded too")
    structure1, structure2, extensions = compare_directory_structures(
        dir1, dir2, exclude_dirs=["exclude_me"]
    )
    assert "exclude_me" not in structure1
    assert "exclude_me" not in structure2


def test_compare_directory_structures_with_patterns(
    comparison_directories: tuple[str, str],
):
    """Test comparison with pattern exclusions."""
    dir1, dir2 = comparison_directories
    with open(os.path.join(dir1, "test_exclude1.py"), "w") as f:
        f.write("This should be excluded by pattern")
    with open(os.path.join(dir2, "test_exclude2.py"), "w") as f:
        f.write("This should be excluded by pattern too")
    exclude_patterns = ["test_*"]
    structure1, structure2, extensions = compare_directory_structures(
        dir1, dir2, exclude_patterns=exclude_patterns
    )
    assert "test_exclude1.py" not in structure1.get("_files", [])
    assert "test_exclude2.py" not in structure2.get("_files", [])


def test_compare_directory_structures_with_regex_patterns(
    comparison_directories: tuple[str, str],
):
    """Test comparison with regex pattern exclusions."""
    dir1, dir2 = comparison_directories
    with open(os.path.join(dir1, "test_exclude1.py"), "w") as f:
        f.write("This should be excluded by pattern")
    with open(os.path.join(dir2, "test_exclude2.py"), "w") as f:
        f.write("This should be excluded by pattern too")
    exclude_patterns = [re.compile(r"test_.*\.py$")]
    structure1, structure2, extensions = compare_directory_structures(
        dir1, dir2, exclude_patterns=exclude_patterns
    )
    assert "test_exclude1.py" not in structure1.get("_files", [])
    assert "test_exclude2.py" not in structure2.get("_files", [])


def test_compare_directory_structures_with_include_patterns(
    comparison_directories: tuple[str, str],
):
    """Test comparison with include patterns."""
    dir1, dir2 = comparison_directories
    with open(os.path.join(dir1, "include_me.txt"), "w") as f:
        f.write("This should be included")
    with open(os.path.join(dir1, "exclude_me.log"), "w") as f:
        f.write("This should be excluded")
    with open(os.path.join(dir2, "include_me_too.txt"), "w") as f:
        f.write("This should be included too")
    with open(os.path.join(dir2, "exclude_me_too.log"), "w") as f:
        f.write("This should be excluded too")
    include_patterns = ["*.txt"]
    structure1, structure2, extensions = compare_directory_structures(
        dir1, dir2, include_patterns=include_patterns
    )
    for file_name in structure1.get("_files", []):
        actual_name = file_name if isinstance(file_name, str) else file_name[0]
        assert actual_name.endswith(".txt"), f"Non-txt file {actual_name} was included"
    for file_name in structure2.get("_files", []):
        actual_name = file_name if isinstance(file_name, str) else file_name[0]
        assert actual_name.endswith(".txt"), f"Non-txt file {actual_name} was included"
    assert "include_me.txt" in [
        f if isinstance(f, str) else f[0] for f in structure1.get("_files", [])
    ]
    assert "exclude_me.log" not in [
        f if isinstance(f, str) else f[0] for f in structure1.get("_files", [])
    ]
    assert "include_me_too.txt" in [
        f if isinstance(f, str) else f[0] for f in structure2.get("_files", [])
    ]
    assert "exclude_me_too.log" not in [
        f if isinstance(f, str) else f[0] for f in structure2.get("_files", [])
    ]


def test_compare_directory_structures_with_statistics(
    comparison_directories: tuple[str, str],
):
    """Test comparison with statistics options."""
    dir1, dir2 = comparison_directories
    structure1, structure2, extensions = compare_directory_structures(
        dir1, dir2, sort_by_loc=True, sort_by_size=True, sort_by_mtime=True
    )
    assert "_loc" in structure1
    assert "_size" in structure1
    assert "_mtime" in structure1
    assert "_loc" in structure2
    assert "_size" in structure2
    assert "_mtime" in structure2
    if "_files" in structure1 and structure1["_files"]:
        file_item = structure1["_files"][0]
        if isinstance(file_item, tuple):
            assert len(file_item) > 4


def test_display_comparison(
    comparison_directories: tuple[str, str], capsys: pytest.CaptureFixture[str]
):
    """Test that comparison display works without errors."""
    dir1, dir2 = comparison_directories
    display_comparison(dir1, dir2)
    captured = capsys.readouterr()
    assert os.path.basename(dir1) in captured.out
    assert os.path.basename(dir2) in captured.out
    assert "Legend" in captured.out


def test_display_comparison_with_full_path(
    comparison_directories: tuple[str, str], capsys: pytest.CaptureFixture[str]
):
    """Test that comparison display works with full path option."""
    dir1, dir2 = comparison_directories
    display_comparison(dir1, dir2, show_full_path=True)
    captured = capsys.readouterr()
    assert os.path.basename(dir1) in captured.out
    assert os.path.basename(dir2) in captured.out
    assert "Legend" in captured.out
    assert "Full file paths are shown" in captured.out


def test_display_comparison_with_filters(
    comparison_directories: tuple[str, str], capsys: pytest.CaptureFixture[str]
):
    """Test that comparison display works with filtering options."""
    dir1, dir2 = comparison_directories
    exclude_dir1 = os.path.join(dir1, "exclude_me")
    exclude_dir2 = os.path.join(dir2, "exclude_me")
    os.makedirs(exclude_dir1, exist_ok=True)
    os.makedirs(exclude_dir2, exist_ok=True)
    with open(os.path.join(exclude_dir1, "excluded.txt"), "w") as f:
        f.write("This should be excluded")
    with open(os.path.join(dir1, "test_pattern.log"), "w") as f:
        f.write("This should be excluded by pattern")
    display_comparison(
        dir1, dir2, exclude_dirs=["exclude_me"], exclude_patterns=["*.log"]
    )
    captured = capsys.readouterr()
    assert "exclude_me" not in captured.out
    assert "excluded.txt" not in captured.out
    assert "test_pattern.log" not in captured.out


def test_display_comparison_with_statistics(
    comparison_directories: tuple[str, str], capsys: pytest.CaptureFixture[str]
):
    """Test that comparison display works with statistics options."""
    dir1, dir2 = comparison_directories
    display_comparison(
        dir1, dir2, sort_by_loc=True, sort_by_size=True, sort_by_mtime=True
    )
    captured = capsys.readouterr()
    assert "lines" in captured.out or "B" in captured.out
    assert any(
        re.search(r"Today|Yesterday|\d{4}-\d{2}-\d{2}", line)
        for line in captured.out.split("\n")
    )


def test_export_comparison_txt(
    comparison_directories: tuple[str, str], output_dir: str
):
    """Test HTML export of directory comparison but renamed to txt."""
    dir1, dir2 = comparison_directories
    output_path = os.path.join(output_dir, "comparison.txt")
    with pytest.raises(ValueError) as excinfo:
        export_comparison(dir1, dir2, "txt", output_path)
    assert "Only HTML format is supported for comparison export" in str(excinfo.value)


def test_export_comparison_html(
    comparison_directories: tuple[str, str], output_dir: str
):
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


def test_export_comparison_html_with_full_path(
    comparison_directories: tuple[str, str], output_dir: str
):
    """Test HTML export of directory comparison with full paths."""
    dir1, dir2 = comparison_directories
    output_path = os.path.join(output_dir, "comparison_full_path.html")
    export_comparison(dir1, dir2, "html", output_path, show_full_path=True)
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
    file1_path = os.path.join(dir1, "file1.txt").replace(os.sep, "/")
    dir1_only_path = os.path.join(dir1, "dir1_only.txt").replace(os.sep, "/")
    dir2_only_path = os.path.join(dir2, "dir2_only.txt").replace(os.sep, "/")
    found_at_least_one_full_path = False
    for path in [file1_path, dir1_only_path, dir2_only_path]:
        if path in content or html.escape(path) in content:
            found_at_least_one_full_path = True
            break
    if not found_at_least_one_full_path:
        base_name_dir1 = os.path.basename(dir1)
        base_name_dir2 = os.path.basename(dir2)
        for line in content.split("\n"):
            if ("📄" in line or "file" in line) and (
                base_name_dir1 in line or base_name_dir2 in line
            ):
                if "/" in line or "\\" in line:
                    found_at_least_one_full_path = True
                    break
    assert found_at_least_one_full_path, "No full paths found in the HTML export"


def test_export_comparison_with_filters(
    comparison_directories: tuple[str, str], output_dir: str
):
    """Test export of directory comparison with filtering options."""
    dir1, dir2 = comparison_directories
    exclude_dir1 = os.path.join(dir1, "exclude_me")
    exclude_dir2 = os.path.join(dir2, "exclude_me")
    os.makedirs(exclude_dir1, exist_ok=True)
    os.makedirs(exclude_dir2, exist_ok=True)
    with open(os.path.join(exclude_dir1, "excluded.txt"), "w") as f:
        f.write("This should be excluded")
    with open(os.path.join(dir1, "test_pattern.log"), "w") as f:
        f.write("This should be excluded by pattern")
    output_path = os.path.join(output_dir, "comparison_filtered.html")
    export_comparison(
        dir1,
        dir2,
        "html",
        output_path,
        exclude_dirs=["exclude_me"],
        exclude_patterns=["*.log"],
    )
    assert os.path.exists(output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "exclude_me" not in content
    assert "excluded.txt" not in content
    assert "test_pattern.log" not in content


def test_export_comparison_unsupported_format(
    comparison_directories: tuple[str, str], output_dir: str
):
    """Test error handling for unsupported export format."""
    dir1, dir2 = comparison_directories
    output_path = os.path.join(output_dir, "comparison.unsupported")
    with pytest.raises(ValueError) as excinfo:
        export_comparison(dir1, dir2, "unsupported", output_path)
    assert "Only HTML format is supported for comparison export" in str(excinfo.value)


def test_complex_comparison(
    complex_comparison_directories: tuple[str, str], output_dir: str
):
    """Test comparison of complex directory structures."""
    dir1, dir2 = complex_comparison_directories
    structure1, structure2, extensions = compare_directory_structures(dir1, dir2)
    assert "src" in structure1
    assert "src" in structure2
    assert "docs" in structure1
    assert "docs" in structure2
    assert "CHANGELOG.md" not in [
        f if isinstance(f, str) else f[0] for f in structure1.get("_files", [])
    ]
    assert "CHANGELOG.md" in [
        f if isinstance(f, str) else f[0] for f in structure2.get("_files", [])
    ]
    assert "utils.py" in [
        f if isinstance(f, str) else f[0] for f in structure1["src"].get("_files", [])
    ]
    assert "utils.py" not in [
        f if isinstance(f, str) else f[0] for f in structure2["src"].get("_files", [])
    ]
    assert "new_module.py" not in [
        f if isinstance(f, str) else f[0] for f in structure1["src"].get("_files", [])
    ]
    assert "new_module.py" in [
        f if isinstance(f, str) else f[0] for f in structure2["src"].get("_files", [])
    ]
    output_path = os.path.join(output_dir, "complex_comparison.html")
    export_comparison(dir1, dir2, "html", output_path)
    assert os.path.exists(output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "CHANGELOG.md" in content
    assert "utils.py" in content
    assert "new_module.py" in content
    assert "examples.md" in content


def test_build_comparison_tree(
    comparison_directories: tuple[str, str],
    mocker: MockerFixture,
):
    """Test building a comparison tree."""
    dir1, dir2 = comparison_directories
    structure1, structure2, extensions = compare_directory_structures(dir1, dir2)
    color_map = {ext: f"#{i:06x}" for i, ext in enumerate(extensions)}
    mock_tree = mocker.MagicMock()
    build_comparison_tree(structure1, structure2, mock_tree, color_map)
    assert mock_tree.add.called
    calls = [
        call for call in mock_tree.add.call_args_list if isinstance(call.args[0], Text)
    ]
    has_green_highlight = False
    for call in calls:
        text = call.args[0]
        if hasattr(text.style, "__contains__") and "on green" in text.style:
            has_green_highlight = True
            break
    assert has_green_highlight, "No green highlighting found for unique items"


def test_cli_command(runner: CliRunner, comparison_directories: tuple[str, str]):
    """Test the compare CLI command."""
    dir1, dir2 = comparison_directories
    result = runner.invoke(app, ["compare", dir1, dir2])
    assert result.exit_code == 0
    assert os.path.basename(dir1) in result.stdout
    assert os.path.basename(dir2) in result.stdout
    assert "Legend" in result.stdout


def test_cli_command_with_filters(
    runner: CliRunner, complex_comparison_directories: tuple[str, str]
):
    """Test the compare CLI command with filter options."""
    dir1, dir2 = complex_comparison_directories
    result = runner.invoke(
        app, ["compare", dir1, dir2, "--exclude", "tests", "--exclude-pattern", "*.md"]
    )
    assert result.exit_code == 0
    assert "tests" not in result.stdout
    assert "README.md" not in result.stdout
    assert "CHANGELOG.md" not in result.stdout
    assert "index.md" not in result.stdout
    assert "api.md" not in result.stdout
    assert "examples.md" not in result.stdout
    assert "src" in result.stdout
    assert "main.py" in result.stdout
    assert "utils.py" in result.stdout
    assert "new_module.py" in result.stdout


def test_cli_command_with_export(
    runner: CliRunner, comparison_directories: tuple[str, str], output_dir: str
):
    """Test the compare CLI command with export option."""
    dir1, dir2 = comparison_directories
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
            "test_compare",
        ],
    )
    assert result.exit_code == 0
    output_file = os.path.join(output_dir, "test_compare.html")
    assert os.path.exists(output_file)


def test_cli_command_with_export_full_path(
    runner: CliRunner, comparison_directories: tuple[str, str], output_dir: str
):
    """Test the compare CLI command with export option and full path display."""
    dir1, dir2 = comparison_directories
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
            "test_compare_full_path",
            "--full-path",
        ],
    )
    assert result.exit_code == 0
    output_file = os.path.join(output_dir, "test_compare_full_path.html")
    assert os.path.exists(output_file)
    with open(output_file, "r", encoding="utf-8") as f:
        content = f.read()
    base_name_dir1 = os.path.basename(dir1)
    base_name_dir2 = os.path.basename(dir2)
    found_full_path = False
    for line in content.split("\n"):
        if ("📄" in line) and (base_name_dir1 in line or base_name_dir2 in line):
            found_full_path = True
            break
    assert found_full_path, "No full paths found in the exported file"


def test_comparison_with_statistics(
    comparison_directories: tuple[str, str], output_dir: str
):
    """Test comparison with statistics options."""
    dir1, dir2 = comparison_directories
    output_path = os.path.join(output_dir, "comparison_with_stats.html")
    export_comparison(
        dir1,
        dir2,
        "html",
        output_path,
        sort_by_loc=True,
        sort_by_size=True,
        sort_by_mtime=True,
    )
    assert os.path.exists(output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "lines" in content
    assert "B" in content or "KB" in content
    has_time_indicator = False
    if re.search(r"Today|Yesterday|\d{4}-\d{2}-\d{2}|format_timestamp", content):
        has_time_indicator = True
    assert has_time_indicator, "No time indicators found in the comparison"
