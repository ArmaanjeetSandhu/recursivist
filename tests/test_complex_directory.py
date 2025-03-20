import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional

import pytest
from typer.testing import CliRunner

from recursivist.cli import app
from recursivist.compare import compare_directory_structures, export_comparison
from recursivist.core import export_structure, get_directory_structure


def test_cli_with_complex_structure(
    runner: CliRunner, complex_directory: str, output_dir: str
):
    """Test CLI visualization of complex directory structure with filtering options."""
    result = runner.invoke(
        app,
        [
            "visualize",
            complex_directory,
            "--exclude",
            "build dist",
            "--exclude-ext",
            ".so .tmp",
            "--exclude-pattern",
            "__.*__",
            "--depth",
            "2",
        ],
    )
    assert result.exit_code == 0
    assert "build" not in result.stdout
    assert "dist" not in result.stdout
    assert "src" in result.stdout
    assert "docs" in result.stdout
    result = runner.invoke(
        app,
        [
            "export",
            complex_directory,
            "--format",
            "json md",
            "--output-dir",
            output_dir,
            "--prefix",
            "complex",
            "--exclude",
            "build dist",
            "--exclude-ext",
            ".so .tmp",
            "--depth",
            "2",
        ],
    )
    assert result.exit_code == 0
    assert os.path.exists(os.path.join(output_dir, "complex.json"))
    assert os.path.exists(os.path.join(output_dir, "complex.md"))
    with open(os.path.join(output_dir, "complex.json"), "r", encoding="utf-8") as f:
        data = json.load(f)
        assert "structure" in data
        assert "src" in data["structure"]
        assert "docs" in data["structure"]
        assert "build" not in data["structure"]
        assert "dist" not in data["structure"]


def test_regex_filtering_with_complex_directory(complex_directory: str):
    """Test regex filtering on complex directory structure."""
    include_patterns = [re.compile(r"\.py$")]
    structure, extensions = get_directory_structure(
        complex_directory,
        include_patterns=include_patterns,
    )
    assert ".py" in extensions
    assert ".md" not in extensions
    assert ".so" not in extensions
    assert ".tmp" not in extensions
    python_files_found = False
    non_python_files_found = False

    def check_files(structure):
        nonlocal python_files_found, non_python_files_found
        if "_files" in structure:
            for file in structure["_files"]:
                file_name = file if isinstance(file, str) else file[0]
                if file_name.endswith(".py"):
                    python_files_found = True
                else:
                    non_python_files_found = True
        for key, value in structure.items():
            if key != "_files" and isinstance(value, dict):
                check_files(value)

    check_files(structure)
    assert python_files_found, "No Python files found in structure"
    assert not non_python_files_found, "Non-Python files found despite include pattern"


def test_comparison_with_complex_directories(
    complex_directory: str, complex_directory_clone: str, output_dir: str
):
    """Test comparison between complex directory structures."""
    structure1, structure2, _ = compare_directory_structures(
        complex_directory,
        complex_directory_clone,
        exclude_dirs=["build", "dist"],
        max_depth=3,
    )
    assert "src" in structure1
    assert "src" in structure2
    assert "docs" in structure1
    assert "docs" in structure2
    assert "build" not in structure1
    assert "dist" not in structure1
    assert "CHANGELOG.md" not in get_file_names(structure1)
    changelog_found = False
    if "_files" in structure2:
        for file_item in structure2["_files"]:
            file_name = file_item if isinstance(file_item, str) else file_item[0]
            if file_name == "CHANGELOG.md":
                changelog_found = True
                break
    assert changelog_found, "CHANGELOG.md not found in structure2"
    output_path = os.path.join(output_dir, "comparison.html")
    export_comparison(
        complex_directory,
        complex_directory_clone,
        "html",
        output_path,
        exclude_dirs=["build", "dist"],
        max_depth=3,
    )
    assert os.path.exists(output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Directory Comparison" in content
    assert os.path.basename(complex_directory) in content
    assert os.path.basename(complex_directory_clone) in content
    assert "CHANGELOG.md" in content


def test_full_path_display_with_complex_directory(
    complex_directory: str, output_dir: str
):
    """Test full path display with complex directory structure."""
    structure, _ = get_directory_structure(
        complex_directory,
        show_full_path=True,
        max_depth=3,
    )
    assert "_files" in structure
    for file_item in structure["_files"]:
        assert isinstance(file_item, tuple)
        file_name, full_path = file_item
        assert os.path.isabs(full_path.replace("/", os.sep))
        assert file_name in os.path.basename(full_path)
    output_path = os.path.join(output_dir, "full_path.json")
    export_structure(
        structure,
        complex_directory,
        "json",
        output_path,
        show_full_path=True,
    )
    with open(output_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "structure" in data
    assert "_files" in data["structure"]
    paths = data["structure"]["_files"]
    for path in paths:
        if isinstance(path, dict) and "path" in path:
            assert os.path.isabs(path["path"].replace("/", os.sep))
            assert complex_directory.replace(os.sep, "/") in path["path"].replace(
                os.sep, "/"
            )
        elif isinstance(path, str):
            assert os.path.isabs(path.replace("/", os.sep))
            assert complex_directory.replace(os.sep, "/") in path.replace(os.sep, "/")


@pytest.mark.parametrize("depth", [1, 2, 3])
def test_depth_limit_with_complex_directory(complex_directory: str, depth: int):
    """Test depth limits with complex directory structure."""
    structure, _ = get_directory_structure(
        complex_directory,
        max_depth=depth,
    )

    def check_depth(structure, current_depth=0):
        if current_depth == depth:
            for key, value in structure.items():
                if (
                    key != "_files"
                    and key != "_max_depth_reached"
                    and isinstance(value, dict)
                ):
                    assert "_max_depth_reached" in value
            return
        for key, value in structure.items():
            if (
                key != "_files"
                and key != "_max_depth_reached"
                and isinstance(value, dict)
            ):
                if current_depth < depth - 1:
                    assert "_max_depth_reached" not in value
                check_depth(value, current_depth + 1)

    check_depth(structure)


def test_cli_with_regex_patterns(runner: CliRunner, temp_dir: str):
    """Test CLI with regex patterns."""
    with open(os.path.join(temp_dir, "test.txt"), "w") as f:
        f.write("Test file")
    with open(os.path.join(temp_dir, "test.py"), "w") as f:
        f.write("Python file")
    result = runner.invoke(app, ["visualize", temp_dir])
    assert result.exit_code == 0
    assert "test.txt" in result.stdout
    assert "test.py" in result.stdout
    result = runner.invoke(
        app, ["visualize", temp_dir, "--exclude-pattern", ".*\\.py$", "--regex"]
    )
    assert result.exit_code == 0
    assert "test.txt" in result.stdout
    assert "test.py" not in result.stdout


def test_gitignore_pattern_with_complex_directory(complex_directory: str):
    """Test using gitignore file for filtering."""
    structure, _ = get_directory_structure(
        complex_directory,
        ignore_file=".gitignore",
    )
    assert "build" not in structure
    assert "dist" not in structure

    def check_extensions(structure):
        for key, value in structure.items():
            if key == "_files":
                for file in value:
                    file_name = file if isinstance(file, str) else file[0]
                    assert not file_name.endswith(".pyc")
                    assert not file_name.endswith(".so")
                    assert not file_name.endswith(".tmp")
            elif key != "_max_depth_reached" and isinstance(value, dict):
                check_extensions(value)

    check_extensions(structure)


def test_statistics_integration(temp_dir: str):
    """Test statistics integration with directory structure."""
    src_dir = os.path.join(temp_dir, "src")
    os.makedirs(src_dir, exist_ok=True)
    file_contents = {
        "small.py": "print('Small file')",
        "medium.py": "def test_func():\n    print('Medium file')\n\ntest_func()",
        "large.py": "\n".join([f"print('Line {i}')" for i in range(10)]),
    }
    for file_name, content in file_contents.items():
        with open(os.path.join(src_dir, file_name), "w") as f:
            f.write(content)
    structure, _ = get_directory_structure(
        temp_dir, sort_by_loc=True, sort_by_size=True, sort_by_mtime=True
    )
    assert "_loc" in structure
    assert "_size" in structure
    assert "_mtime" in structure
    assert "_loc" in structure["src"]
    assert "_size" in structure["src"]
    assert "_mtime" in structure["src"]
    if "_files" in structure["src"]:
        for file_item in structure["src"]["_files"]:
            if isinstance(file_item, tuple) and len(file_item) > 4:
                _, _, loc, size, mtime = file_item
                assert isinstance(loc, int)
                assert isinstance(size, int)
                assert isinstance(mtime, float)


@pytest.mark.parametrize("fmt", ["json", "txt", "md", "html"])
def test_export_formats_with_statistics(temp_dir: str, output_dir: str, fmt: str):
    """Test exporting with statistics to different formats."""
    with open(os.path.join(temp_dir, "test1.py"), "w") as f:
        f.write("def main():\n    print('Test 1')\n\nmain()")
    with open(os.path.join(temp_dir, "test2.py"), "w") as f:
        f.write("\n".join([f"print('Line {i}')" for i in range(5)]))
    structure, _ = get_directory_structure(
        temp_dir, sort_by_loc=True, sort_by_size=True, sort_by_mtime=True
    )
    output_path = os.path.join(output_dir, f"stats_export.{fmt}")
    export_structure(
        structure,
        temp_dir,
        fmt,
        output_path,
        sort_by_loc=True,
        sort_by_size=True,
        sort_by_mtime=True,
    )
    assert os.path.exists(output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()
    if fmt == "json":
        assert '"show_loc": true' in content
        assert '"show_size": true' in content
        assert '"show_mtime": true' in content
    elif fmt in ["txt", "md", "html"]:
        has_stats = False
        for indicator in ["lines", "B", "KB", "MB", "Today", "Yesterday"]:
            if indicator in content:
                has_stats = True
                break
        assert has_stats, f"No statistics found in {fmt} export"


def test_comparison_with_statistics(temp_dir: str, output_dir: str):
    """Test comparison with statistics."""
    dir1 = os.path.join(temp_dir, "dir1")
    dir2 = os.path.join(temp_dir, "dir2")
    os.makedirs(dir1, exist_ok=True)
    os.makedirs(dir2, exist_ok=True)
    with open(os.path.join(dir1, "file1.py"), "w") as f:
        f.write("print('Dir 1 content')")
    with open(os.path.join(dir2, "file1.py"), "w") as f:
        f.write("print('Dir 2 different content with more lines')\nprint('Extra line')")
    structure1, structure2, _ = compare_directory_structures(
        dir1, dir2, sort_by_loc=True, sort_by_size=True, sort_by_mtime=True
    )
    assert "_loc" in structure1
    assert "_size" in structure1
    assert "_mtime" in structure1
    assert "_loc" in structure2
    assert "_size" in structure2
    assert "_mtime" in structure2
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
    has_stats = False
    for indicator in ["lines", "B", "KB", "MB", "Today", "Yesterday"]:
        if indicator in content:
            has_stats = True
            break
    assert has_stats, "No statistics found in comparison export"


def test_pathlib_compatibility(temp_dir: str, output_dir: str):
    """Test compatibility with pathlib.Path objects."""
    test_file = os.path.join(temp_dir, "test.txt")
    with open(test_file, "w") as f:
        f.write("Test content")
    path_obj = Path(temp_dir)
    structure, _ = get_directory_structure(str(path_obj))
    assert "_files" in structure
    file_found = False
    for file_item in structure["_files"]:
        file_name = file_item if isinstance(file_item, str) else file_item[0]
        if file_name == "test.txt":
            file_found = True
    assert file_found, "File not found when using pathlib.Path"
    output_path = Path(output_dir) / "pathlib_test.json"
    export_structure(structure, str(path_obj), "json", str(output_path))
    assert output_path.exists()
    with open(output_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "root" in data
    assert "structure" in data
    assert "_files" in data["structure"]


def get_file_names(structure: Dict, path: Optional[List[str]] = None) -> List[str]:
    """
    Extract file names from a structure, optionally at a specific path.
    Args:
        structure: The directory structure.
        path: Optional path to look at within the structure.
    Returns:
        List of file names.
    """
    if path is None:
        return [f if isinstance(f, str) else f[0] for f in structure.get("_files", [])]
    else:
        current = structure
        for segment in path:
            if segment in current:
                current = current[segment]
            else:
                return []
        return [f if isinstance(f, str) else f[0] for f in current.get("_files", [])]
