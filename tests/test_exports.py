"""
Tests for the export functionality of the recursivist package.

This module tests the export capabilities:
- Sorting files by name and extension
- Directory exporter initialization and configuration
- Export to different formats (txt, json, html, md, jsx)
- Full path display in exports
- Error handling for export operations
- Unicode and special character handling
- Statistics display in exports
- Large directory structures
"""

import json
import os
import random
import re
import string
import time
from typing import Any, Dict, List
from unittest.mock import patch

import pytest
from pytest_mock import MockerFixture

from recursivist.core import (
    export_structure,
    format_size,
    format_timestamp,
    get_directory_structure,
)
from recursivist.exports import DirectoryExporter, sort_files_by_type


def test_sort_files_by_type():
    """Test sorting files by extension and name."""
    files = ["c.txt", "b.py", "a.txt", "d.py"]
    sorted_files = sort_files_by_type(files)
    assert sorted_files[0].endswith(".py")
    assert sorted_files[1].endswith(".py")
    assert sorted_files[2].endswith(".txt")
    assert sorted_files[3].endswith(".txt")


def test_sort_files_by_type_with_tuples():
    """Test sorting files by extension and name when using tuples for full paths."""
    files = [
        ("c.txt", "/path/to/c.txt"),
        ("b.py", "/path/to/b.py"),
        ("a.txt", "/path/to/a.txt"),
        ("d.py", "/path/to/d.py"),
    ]
    sorted_files = sort_files_by_type(files)
    assert sorted_files[0][0].endswith(".py")
    assert sorted_files[1][0].endswith(".py")
    assert sorted_files[2][0].endswith(".txt")
    assert sorted_files[3][0].endswith(".txt")


def test_sort_files_by_type_with_mixed_inputs():
    """Test sorting files with a mix of strings and tuples."""
    files = [
        "c.txt",
        ("b.py", "/path/to/b.py"),
        ("a.txt", "/path/to/a.txt"),
        "d.py",
    ]
    sorted_files = sort_files_by_type(files)
    assert len(sorted_files) == 4
    original_names = ["c.txt", "b.py", "a.txt", "d.py"]
    sorted_names = []
    for item in sorted_files:
        if isinstance(item, str):
            sorted_names.append(item)
        else:
            sorted_names.append(item[0])
    for name in original_names:
        assert name in sorted_names
    py_files = [f for f in sorted_names if f.endswith(".py")]
    txt_files = [f for f in sorted_names if f.endswith(".txt")]
    assert len(py_files) == 2
    assert len(txt_files) == 2


def test_sort_files_by_type_with_special_cases():
    """Test sorting files with special cases like no extensions or dotfiles."""
    files = [
        "readme",
        ".gitignore",
        "file.txt.bak",
        ".env.local",
    ]
    sorted_files = sort_files_by_type(files)
    assert len(sorted_files) == 4
    assert set(sorted_files) == set(files)


def test_sort_files_by_type_with_loc():
    """Test sorting files by lines of code."""
    files = [
        ("a.py", "/path/to/a.py", 100),
        ("b.py", "/path/to/b.py", 50),
        ("c.py", "/path/to/c.py", 200),
    ]
    sorted_files = sort_files_by_type(files, sort_by_loc=True)
    assert sorted_files[0][0] == "c.py"
    assert sorted_files[1][0] == "a.py"
    assert sorted_files[2][0] == "b.py"


def test_sort_files_by_type_with_size():
    """Test sorting files by size."""
    files = [
        ("a.txt", "/path/to/a.txt", 0, 1024),
        ("b.txt", "/path/to/b.txt", 0, 2048),
        ("c.txt", "/path/to/c.txt", 0, 512),
    ]
    sorted_files = sort_files_by_type(files, sort_by_size=True)
    assert sorted_files[0][0] == "b.txt"
    assert sorted_files[1][0] == "a.txt"
    assert sorted_files[2][0] == "c.txt"


def test_sort_files_by_type_with_mtime():
    """Test sorting files by modification time."""
    files = [
        ("a.txt", "/path/to/a.txt", 0, 0, 1609459200),
        ("b.txt", "/path/to/b.txt", 0, 0, 1612137600),
        ("c.txt", "/path/to/c.txt", 0, 0, 1606780800),
    ]
    sorted_files = sort_files_by_type(files, sort_by_mtime=True)
    assert sorted_files[0][0] == "b.txt"
    assert sorted_files[1][0] == "a.txt"
    assert sorted_files[2][0] == "c.txt"


def test_sort_files_by_type_with_multiple_criteria():
    """Test sorting files with multiple criteria (LOC, size, mtime)."""
    files = [
        ("a.py", "/path/to/a.py", 100, 1024, 1609459200),
        (
            "b.py",
            "/path/to/b.py",
            100,
            2048,
            1609459200,
        ),
        ("c.py", "/path/to/c.py", 200, 512, 1609459200),
        (
            "d.py",
            "/path/to/d.py",
            100,
            1024,
            1612137600,
        ),
    ]
    sorted_files = sort_files_by_type(
        files, sort_by_loc=True, sort_by_size=True, sort_by_mtime=True
    )
    assert sorted_files[0][0] == "c.py"
    assert sorted_files[1][0] == "b.py"
    assert sorted_files[2][0] == "d.py"
    assert sorted_files[3][0] == "a.py"


def test_sort_files_empty_list():
    """Test sorting an empty list of files."""
    assert sort_files_by_type([]) == []


def test_sort_files_with_nonstandard_extensions():
    """Test sorting files with nonstandard extensions."""
    files = [
        "file.tar.gz",
        "file.min.js",
        "file.spec.ts",
        "file.d.ts",
    ]
    sorted_files = sort_files_by_type(files)
    assert len(sorted_files) == 4
    assert set(sorted_files) == set(files)
    js_files = [f for f in sorted_files if f.endswith(".js")]
    ts_files = [f for f in sorted_files if f.endswith(".ts")]
    assert len(js_files) == 1
    assert len(ts_files) == 2


def test_directory_exporter_init():
    """Test DirectoryExporter initialization."""
    structure = {"_files": ["file1.txt"], "dir1": {"_files": ["file2.py"]}}
    exporter = DirectoryExporter(structure, "test_root")
    assert exporter.structure == structure
    assert exporter.root_name == "test_root"
    assert exporter.base_path is None
    assert not exporter.show_full_path


def test_directory_exporter_init_with_full_path():
    """Test DirectoryExporter initialization with full path option."""
    structure = {
        "_files": [("file1.txt", "/path/to/file1.txt")],
        "dir1": {"_files": [("file2.py", "/path/to/dir1/file2.py")]},
    }
    exporter = DirectoryExporter(structure, "test_root", base_path="/path/to")
    assert exporter.structure == structure
    assert exporter.root_name == "test_root"
    assert exporter.base_path == "/path/to"
    assert exporter.show_full_path


def test_directory_exporter_with_statistics():
    """Test DirectoryExporter initialization with statistics options."""
    structure = {
        "_loc": 100,
        "_size": 1024,
        "_mtime": 1609459200,
        "_files": [("file1.txt", "/path/to/file1.txt", 50, 512, 1609459200)],
        "dir1": {
            "_loc": 50,
            "_size": 512,
            "_mtime": 1609459200,
            "_files": [("file2.py", "/path/to/dir1/file2.py", 50, 512, 1609459200)],
        },
    }
    exporter = DirectoryExporter(
        structure,
        "test_root",
        base_path="/path/to",
        sort_by_loc=True,
        sort_by_size=True,
        sort_by_mtime=True,
    )
    assert exporter.sort_by_loc
    assert exporter.sort_by_size
    assert exporter.sort_by_mtime


def test_export_to_txt(sample_directory: Any, output_dir: str):
    """Test exporting directory structure to text format."""
    structure, _ = get_directory_structure(sample_directory)
    output_path = os.path.join(output_dir, "structure.txt")
    export_structure(structure, sample_directory, "txt", output_path)
    assert os.path.exists(output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert os.path.basename(sample_directory) in content
    assert "file1.txt" in content
    assert "file2.py" in content
    assert "subdir" in content


def test_export_to_txt_with_full_path(sample_directory: Any, output_dir: str):
    """Test exporting directory structure to text format with full paths."""
    structure, _ = get_directory_structure(sample_directory, show_full_path=True)
    output_path = os.path.join(output_dir, "structure_full_path.txt")
    export_structure(
        structure, sample_directory, "txt", output_path, show_full_path=True
    )
    assert os.path.exists(output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert os.path.basename(sample_directory) in content
    for file_name in ["file1.txt", "file2.py"]:
        expected_abs_path = os.path.abspath(os.path.join(sample_directory, file_name))
        expected_abs_path = expected_abs_path.replace(os.sep, "/")
        assert (
            expected_abs_path in content
        ), f"Absolute path for {file_name} not found in TXT export"
    assert "subdir" in content


def test_txt_export_format(sample_directory: Any, output_dir: str):
    """Test the formatting of text export."""
    nested_dir = os.path.join(sample_directory, "nested")
    os.makedirs(nested_dir, exist_ok=True)
    with open(os.path.join(nested_dir, "nested_file.txt"), "w") as f:
        f.write("Nested file content")
    structure, _ = get_directory_structure(sample_directory)
    output_path = os.path.join(output_dir, "structure_format.txt")
    export_structure(structure, sample_directory, "txt", output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()
    lines = content.split("\n")
    assert lines[0].startswith("📂")
    file_lines = [line for line in lines if "📄" in line]
    assert all(
        re.match(r".*├── 📄 .*", line) or re.match(r".*└── 📄 .*", line)
        for line in file_lines
    )
    dir_lines = [line for line in lines if "📁" in line]
    assert all(
        re.match(r".*├── 📁 .*", line) or re.match(r".*└── 📁 .*", line)
        for line in dir_lines
    )


def test_export_to_json(sample_directory: Any, output_dir: str):
    """Test exporting directory structure to JSON format."""
    structure, _ = get_directory_structure(sample_directory)
    output_path = os.path.join(output_dir, "structure.json")
    export_structure(structure, sample_directory, "json", output_path)
    assert os.path.exists(output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "root" in data
    assert "structure" in data
    assert data["root"] == os.path.basename(sample_directory)
    assert "_files" in data["structure"]
    assert "subdir" in data["structure"]
    assert "show_loc" in data
    assert "show_size" in data
    assert "show_mtime" in data


def test_export_to_json_with_full_path(sample_directory: Any, output_dir: str):
    """Test exporting directory structure to JSON format with full paths."""
    structure, _ = get_directory_structure(sample_directory, show_full_path=True)
    output_path = os.path.join(output_dir, "structure_full_path.json")
    export_structure(
        structure, sample_directory, "json", output_path, show_full_path=True
    )
    assert os.path.exists(output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "root" in data
    assert "structure" in data
    assert data["root"] == os.path.basename(sample_directory)
    assert "_files" in data["structure"]
    assert "subdir" in data["structure"]
    files = data["structure"]["_files"]
    assert len(files) > 0, "No files found in JSON output"
    has_full_path = False
    for file_item in files:
        if isinstance(file_item, dict):
            if "path" in file_item:
                assert os.path.isabs(
                    file_item["path"].replace("/", os.sep)
                ), f"File path '{file_item['path']}' is not absolute"
                has_full_path = True
        elif isinstance(file_item, str):
            assert os.path.isabs(
                file_item.replace("/", os.sep)
            ), f"File path '{file_item}' is not absolute"
            has_full_path = True
    assert has_full_path, "No full paths found in JSON output"


def test_json_export_structure(sample_directory: Any, output_dir: str):
    """Test the structure of JSON export."""
    nested_dir = os.path.join(sample_directory, "nested", "deep")
    os.makedirs(nested_dir, exist_ok=True)
    with open(os.path.join(nested_dir, "deep_file.txt"), "w") as f:
        f.write("Deep nested file")
    structure, _ = get_directory_structure(sample_directory)
    output_path = os.path.join(output_dir, "nested_structure.json")
    export_structure(structure, sample_directory, "json", output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "nested" in data["structure"]
    assert "deep" in data["structure"]["nested"]
    assert "_files" in data["structure"]["nested"]["deep"]
    assert "deep_file.txt" in data["structure"]["nested"]["deep"]["_files"]


def test_export_to_html(sample_directory: Any, output_dir: str):
    """Test exporting directory structure to HTML format."""
    structure, _ = get_directory_structure(sample_directory)
    output_path = os.path.join(output_dir, "structure.html")
    export_structure(structure, sample_directory, "html", output_path)
    assert os.path.exists(output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "<!DOCTYPE html>" in content
    assert "<html>" in content
    assert "</html>" in content
    assert os.path.basename(sample_directory) in content
    assert "file1.txt" in content
    assert "file2.py" in content
    assert "subdir" in content


def test_export_to_html_with_full_path(sample_directory: Any, output_dir: str):
    """Test exporting directory structure to HTML format with full paths."""
    structure, _ = get_directory_structure(sample_directory, show_full_path=True)
    output_path = os.path.join(output_dir, "structure_full_path.html")
    export_structure(
        structure, sample_directory, "html", output_path, show_full_path=True
    )
    assert os.path.exists(output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "<!DOCTYPE html>" in content
    assert "<html>" in content
    assert "</html>" in content
    assert os.path.basename(sample_directory) in content
    for file_name in ["file1.txt", "file2.py"]:
        expected_abs_path = os.path.abspath(os.path.join(sample_directory, file_name))
        expected_abs_path = expected_abs_path.replace(os.sep, "/")
        assert (
            expected_abs_path in content
        ), f"Absolute path for {file_name} not found in HTML export"
    assert "subdir" in content


def test_html_export_styling(sample_directory: Any, output_dir: str):
    """Test the styling elements in HTML export."""
    structure, _ = get_directory_structure(sample_directory)
    output_path = os.path.join(output_dir, "structure_styled.html")
    export_structure(structure, sample_directory, "html", output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "<style>" in content
    assert "</style>" in content
    assert "font-family" in content
    assert "directory" in content and "file" in content
    assert "<ul>" in content and "</ul>" in content
    assert "<li" in content and "</li>" in content
    assert "📄" in content
    assert "📁" in content


def test_export_to_markdown(sample_directory: Any, output_dir: str):
    """Test exporting directory structure to Markdown format."""
    structure, _ = get_directory_structure(sample_directory)
    output_path = os.path.join(output_dir, "structure.md")
    export_structure(structure, sample_directory, "md", output_path)
    assert os.path.exists(output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert f"# 📂 {os.path.basename(sample_directory)}" in content
    assert "- 📄 `file1.txt`" in content
    assert "- 📄 `file2.py`" in content
    assert "- 📁 **subdir**" in content


def test_export_to_markdown_with_full_path(sample_directory: Any, output_dir: str):
    """Test exporting directory structure to Markdown format with full paths."""
    structure, _ = get_directory_structure(sample_directory, show_full_path=True)
    output_path = os.path.join(output_dir, "structure_full_path.md")
    export_structure(
        structure, sample_directory, "md", output_path, show_full_path=True
    )
    assert os.path.exists(output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert f"# 📂 {os.path.basename(sample_directory)}" in content
    for file_name in ["file1.txt", "file2.py"]:
        expected_abs_path = os.path.abspath(os.path.join(sample_directory, file_name))
        expected_abs_path = expected_abs_path.replace(os.sep, "/")
        assert (
            f"`{expected_abs_path}`" in content
        ), f"Absolute path for {file_name} not found in Markdown export"
    assert "- 📁 **subdir**" in content


def test_markdown_export_formatting(sample_directory: Any, output_dir: str):
    """Test the formatting of markdown export."""
    level1 = os.path.join(sample_directory, "level1")
    level2 = os.path.join(level1, "level2")
    os.makedirs(level2, exist_ok=True)
    with open(os.path.join(level1, "level1.txt"), "w") as f:
        f.write("Level 1 file")
    with open(os.path.join(level2, "level2.txt"), "w") as f:
        f.write("Level 2 file")
    structure, _ = get_directory_structure(sample_directory)
    output_path = os.path.join(output_dir, "structure_md_format.md")
    export_structure(structure, sample_directory, "md", output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()
    lines = content.split("\n")
    assert lines[0].startswith("# 📂")
    file_lines = [line for line in lines if "`file" in line]
    assert all("- 📄 `" in line for line in file_lines)
    assert "- 📁 **level1**" in content
    assert "    - 📄 `level1.txt`" in content
    assert "    - 📁 **level2**" in content
    assert "        - 📄 `level2.txt`" in content


def test_export_to_jsx(sample_directory: Any, output_dir: str):
    """Test exporting directory structure to React component format."""
    structure, _ = get_directory_structure(sample_directory)
    output_path = os.path.join(output_dir, "structure.jsx")
    export_structure(structure, sample_directory, "jsx", output_path)
    assert os.path.exists(output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "import React" in content
    assert os.path.basename(sample_directory) in content
    assert "DirectoryViewer" in content
    assert "file1.txt" in content
    assert "file2.py" in content
    assert "subdir" in content
    assert "ChevronDown" in content
    assert "ChevronUp" in content


def test_export_to_jsx_with_full_path(sample_directory: Any, output_dir: str):
    """Test exporting directory structure to React component format with full paths."""
    structure, _ = get_directory_structure(sample_directory, show_full_path=True)
    output_path = os.path.join(output_dir, "structure_full_path.jsx")
    export_structure(
        structure, sample_directory, "jsx", output_path, show_full_path=True
    )
    assert os.path.exists(output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "import React" in content
    assert os.path.basename(sample_directory) in content
    assert "DirectoryViewer" in content
    assert "ChevronDown" in content
    assert "ChevronUp" in content
    for file_name in ["file1.txt", "file2.py"]:
        expected_abs_path = os.path.abspath(os.path.join(sample_directory, file_name))
        expected_abs_path = expected_abs_path.replace(os.sep, "/")
        escaped_path = expected_abs_path.replace('"', '\\"')
        assert (
            escaped_path in content or expected_abs_path in content
        ), f"Absolute path for {file_name} not found in JSX export"


def test_jsx_export_functionality(sample_directory: Any, output_dir: str):
    """Test the functional elements of JSX export."""
    structure, _ = get_directory_structure(sample_directory)
    output_path = os.path.join(output_dir, "structure_functional.jsx")
    export_structure(structure, sample_directory, "jsx", output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "import React" in content
    assert "import { ChevronDown, ChevronUp" in content
    assert "const DirectoryViewer =" in content
    assert "useState" in content
    assert "toggleDarkMode" in content
    assert "handleExpandAll" in content
    assert "handleCollapseAll" in content
    assert "export default DirectoryViewer;" in content


def test_export_unsupported_format(sample_directory: Any, output_dir: str):
    """Test exporting to an unsupported format raises ValueError."""
    structure, _ = get_directory_structure(sample_directory)
    output_path = os.path.join(output_dir, "structure.unsupported")
    with pytest.raises(ValueError) as excinfo:
        export_structure(structure, sample_directory, "unsupported", output_path)
    assert "Unsupported format" in str(excinfo.value)


def test_export_error_handling(
    sample_directory: Any,
    output_dir: str,
    mocker: MockerFixture,
):
    """Test error handling during export."""
    structure, _ = get_directory_structure(sample_directory)
    output_path = os.path.join(output_dir, "structure.txt")
    mocker.patch("builtins.open", side_effect=PermissionError("Permission denied"))
    with pytest.raises(Exception):
        export_structure(structure, sample_directory, "txt", output_path)


def test_export_with_max_depth_indicator(temp_dir: str, output_dir: str):
    """Test export with max depth indicator."""
    level1 = os.path.join(temp_dir, "level1")
    level2 = os.path.join(level1, "level2")
    level3 = os.path.join(level2, "level3")
    os.makedirs(level3, exist_ok=True)
    with open(os.path.join(level1, "file1.txt"), "w") as f:
        f.write("Level 1 file")
    structure, _ = get_directory_structure(temp_dir, max_depth=2)
    formats = ["txt", "json", "html", "md", "jsx"]
    for fmt in formats:
        output_path = os.path.join(output_dir, f"max_depth.{fmt}")
        export_structure(structure, temp_dir, fmt, output_path)
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
        if fmt == "txt":
            assert "⋯ (max depth reached)" in content
        elif fmt == "json":
            assert "_max_depth_reached" in content
        elif fmt == "html":
            assert "max-depth" in content
        elif fmt == "md":
            assert "*(max depth reached)*" in content
        elif fmt == "jsx":
            assert "max depth reached" in content


def test_export_with_statistics(sample_directory: Any, output_dir: str):
    """Test export with statistics information (LOC, size, mtime)."""
    structure, _ = get_directory_structure(
        sample_directory, sort_by_loc=True, sort_by_size=True, sort_by_mtime=True
    )
    formats = ["txt", "json", "html", "md", "jsx"]
    for fmt in formats:
        output_path = os.path.join(output_dir, f"stats_export.{fmt}")
        export_structure(
            structure,
            sample_directory,
            fmt,
            output_path,
            sort_by_loc=True,
            sort_by_size=True,
            sort_by_mtime=True,
        )
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
        if fmt == "txt":
            match_found = False
            for line in content.split("\n"):
                if re.search(
                    r"lines|B|KB|MB|GB|Today|Yesterday|\d{4}-\d{2}-\d{2}", line
                ):
                    match_found = True
                    break
            assert match_found, "Statistics not found in TXT export"
        elif fmt == "json":
            assert '"show_loc": true' in content
            assert '"show_size": true' in content
            assert '"show_mtime": true' in content
        elif fmt == "html":
            match_found = False
            if re.search(
                r"lines|B|KB|MB|GB|Today|Yesterday|\d{4}-\d{2}-\d{2}|format_timestamp",
                content,
            ):
                match_found = True
            assert match_found, "Statistics not found in HTML export"
        elif fmt == "md":
            match_found = False
            for line in content.split("\n"):
                if re.search(
                    r"lines|B|KB|MB|GB|Today|Yesterday|\d{4}-\d{2}-\d{2}", line
                ):
                    match_found = True
                    break
            assert match_found, "Statistics not found in MD export"
        elif fmt == "jsx":
            assert (
                "locCount" in content
                or "sizeCount" in content
                or "mtimeCount" in content
            ), "Statistics not found in JSX export"


def generate_large_structure(
    depth: int, files_per_dir: int, dir_branching: int
) -> Dict:
    """Generate a large directory structure for testing."""

    def _generate_recursive(current_depth: int) -> Dict:
        if current_depth > depth:
            return {}
        structure: Dict[str, Any] = {}
        structure["_files"] = []
        for i in range(files_per_dir):
            file_name = f"file_{current_depth}_{i}.txt"
            structure["_files"].append(file_name)
        if current_depth < depth:
            for i in range(dir_branching):
                dir_name = f"dir_{current_depth}_{i}"
                structure[dir_name] = _generate_recursive(current_depth + 1)
        return structure

    return _generate_recursive(1)


def test_export_large_structure(output_dir: str):
    """Test exporting a large directory structure."""
    large_structure = generate_large_structure(
        depth=5, files_per_dir=10, dir_branching=3
    )
    formats = ["txt", "json", "html", "md", "jsx"]
    for fmt in formats:
        output_path = os.path.join(output_dir, f"large_structure.{fmt}")
        export_structure(large_structure, "large_root", fmt, output_path)
        assert os.path.exists(output_path)
        file_size = os.path.getsize(output_path)
        assert file_size > 0, f"Exported {fmt} file is empty"
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
        if fmt == "txt":
            assert "📂 large_root" in content
            assert "file_1_0.txt" in content
        elif fmt == "json":
            assert '"root": "large_root"' in content
            data = json.loads(content)
            assert "_files" in data["structure"]
        elif fmt == "html":
            assert "<!DOCTYPE html>" in content
            assert "large_root" in content
        elif fmt == "md":
            assert "# 📂 large_root" in content
        elif fmt == "jsx":
            assert "import React" in content
            assert 'name="large_root"' in content


def test_export_with_unicode_characters(output_dir: str):
    """Test export with Unicode characters in file and directory names."""
    unicode_structure = {
        "_files": [
            "ascii.txt",
            "español.txt",
            "中文.py",
            "русский.md",
            "日本語.js",
            "한국어.json",
        ],
        "目录": {
            "_files": ["файл.txt"],
        },
        "папка": {
            "_files": ["ファイル.py"],
            "子目录": {
                "_files": ["파일.md"],
            },
        },
    }
    formats = ["txt", "json", "html", "md", "jsx"]
    for fmt in formats:
        output_path = os.path.join(output_dir, f"unicode.{fmt}")
        export_structure(unicode_structure, "unicode_root", fmt, output_path)
        assert os.path.exists(output_path)
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
        if fmt == "json":
            data = json.loads(content)
            files = data["structure"]["_files"]
            assert "español.txt" in files
            assert "中文.py" in files
            assert "русский.md" in files
            assert "目录" in data["structure"]
        elif fmt not in ["jsx"]:
            assert "español.txt" in content
            assert "中文.py" in content
            assert "русский.md" in content
            assert "目录" in content
            assert "папка" in content


def test_format_size_function():
    """Test the format_size function."""
    assert format_size(0) == "0 B"
    assert format_size(999) == "999 B"
    assert format_size(1024) == "1.0 KB"
    assert format_size(1536) == "1.5 KB"
    assert format_size(1024 * 1024) == "1.0 MB"
    assert format_size(int(1.5 * 1024 * 1024)) == "1.5 MB"
    assert format_size(1024 * 1024 * 1024) == "1.0 GB"
    assert format_size(int(2.5 * 1024 * 1024 * 1024)) == "2.5 GB"


def test_format_timestamp_function():
    """Test the format_timestamp function."""
    from datetime import datetime, timedelta

    today = (
        datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    )
    yesterday = (
        (datetime.now() - timedelta(days=1))
        .replace(hour=0, minute=0, second=0, microsecond=0)
        .timestamp()
    )
    last_week = (datetime.now() - timedelta(days=5)).timestamp()
    last_month = (datetime.now() - timedelta(days=40)).timestamp()
    last_year = (datetime.now() - timedelta(days=400)).timestamp()
    assert "Today" in format_timestamp(today + 3600)
    assert "Yesterday" in format_timestamp(yesterday + 3600)
    weekday_format = format_timestamp(last_week)
    assert any(
        day in weekday_format
        for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    )
    month_format = format_timestamp(last_month)
    assert any(
        month in month_format
        for month in [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]
    )
    year_format = format_timestamp(last_year)
    assert re.match(r"\d{4}-\d{2}-\d{2}", year_format)


def test_export_structure_permission_error(sample_directory: Any, output_dir: str):
    """Test permission error handling in export_structure."""
    structure, _ = get_directory_structure(sample_directory)
    output_path = os.path.join(output_dir, "permission_error.txt")
    with patch(
        "recursivist.exports.DirectoryExporter.to_txt",
        side_effect=PermissionError("Permission denied"),
    ):
        with pytest.raises(Exception) as excinfo:
            export_structure(structure, sample_directory, "txt", output_path)
        assert "Permission denied" in str(excinfo.value)


def test_export_structure_disk_full_error(sample_directory: Any, output_dir: str):
    """Test disk full error handling in export_structure."""
    structure, _ = get_directory_structure(sample_directory)
    output_path = os.path.join(output_dir, "disk_full.txt")
    disk_full_error = OSError(28, "No space left on device")
    with patch(
        "recursivist.exports.DirectoryExporter.to_txt", side_effect=disk_full_error
    ):
        with pytest.raises(Exception) as excinfo:
            export_structure(structure, sample_directory, "txt", output_path)
        assert "No space left on device" in str(excinfo.value)


def test_to_jsx_with_long_paths(output_dir: str):
    """Test exporting to JSX with very long file and directory names."""
    long_name = "a" * 255
    long_structure = {
        "_files": [
            f"{long_name}.txt",
            (f"{long_name}.py", f"/path/to/{long_name}.py"),
        ],
        f"dir_{long_name}": {
            "_files": [f"nested_{long_name}.md"],
        },
    }
    output_path = os.path.join(output_dir, "long_names.jsx")
    exporter = DirectoryExporter(long_structure, "long_root")
    exporter.to_jsx(output_path)
    assert os.path.exists(output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert f'name="{long_name}.txt"' in content
    assert f'name="{long_name}.py"' in content
    assert f'name="dir_{long_name}"' in content
    assert f'name="nested_{long_name}.md"' in content


@pytest.fixture
def file_with_excessive_loc(temp_dir: str):
    """Create a directory with a file containing many lines for testing."""
    test_file = os.path.join(temp_dir, "many_lines.py")
    with open(test_file, "w") as f:
        for i in range(10000):
            f.write(f"print('Line {i}')\n")
    return temp_dir


def test_export_with_very_large_loc(file_with_excessive_loc: str, output_dir: str):
    """Test exporting files with very large line counts."""
    structure, _ = get_directory_structure(file_with_excessive_loc, sort_by_loc=True)
    formats = ["txt", "json", "html", "md", "jsx"]
    for fmt in formats:
        output_path = os.path.join(output_dir, f"large_loc.{fmt}")
        export_structure(
            structure, file_with_excessive_loc, fmt, output_path, sort_by_loc=True
        )
        assert os.path.exists(output_path)
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
        if fmt == "txt":
            assert re.search(r"many_lines\.py \(\d{4,} lines\)", content)
        elif fmt == "json":
            assert re.search(r'"loc": \d{4,}', content)
        elif fmt == "html" or fmt == "md":
            assert re.search(r"many_lines\.py.*\(\d{4,} lines\)", content)
        elif fmt == "jsx":
            assert re.search(r"locCount={\d{4,}}", content)


def random_string(length: int) -> str:
    """Generate a random string of fixed length."""
    return "".join(random.choice(string.ascii_letters) for _ in range(length))


def test_export_with_many_unique_extensions(output_dir: str):
    """Test exporting with many unique file extensions to verify color generation."""
    many_extensions_structure: Dict[str, List[str]] = {"_files": []}
    for i in range(100):
        ext = random_string(5)
        many_extensions_structure["_files"].append(f"file_{i}.{ext}")
    output_path = os.path.join(output_dir, "many_extensions.html")
    export_structure(many_extensions_structure, "extensions_test", "html", output_path)
    assert os.path.exists(output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()
    color_matches = re.findall(r'style="([^"]*)"', content)
    unique_colors = set()
    for style in color_matches:
        if "#" in style:
            color_code = re.search(r"#[0-9A-Fa-f]{6}", style)
            if color_code:
                unique_colors.add(color_code.group())
    assert (
        len(unique_colors) > 10
    ), "Too few unique colors generated for different extensions"


def test_export_with_filename_escaping(output_dir: str):
    """Test exporting with filenames that need escaping in various formats."""
    problematic_structure = {
        "_files": [
            "file with spaces.txt",
            "file&with&ampersands.py",
            "file<with>brackets.md",
            "file'with\"quotes.js",
            "file\\with/slashes.html",
        ],
        "directory with spaces": {
            "_files": ["nested problematic.txt"],
        },
    }
    formats = ["txt", "json", "html", "md", "jsx"]
    for fmt in formats:
        output_path = os.path.join(output_dir, f"escaping.{fmt}")
        export_structure(problematic_structure, "escape_test", fmt, output_path)
        assert os.path.exists(output_path)
        try:
            if fmt == "json":
                with open(output_path, "r", encoding="utf-8") as f:
                    json.load(f)
            elif fmt == "html":
                with open(output_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    assert "&amp;" in content or "&#x26;" in content
                    assert "&lt;" in content or "&#x3C;" in content
                    assert "&gt;" in content or "&#x3E;" in content
                    assert "&quot;" in content or "&#x22;" in content
            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()
                assert "file with spaces" in content.replace("&#x20;", " ").replace(
                    "&nbsp;", " "
                )
                assert "directory with spaces" in content.replace(
                    "&#x20;", " "
                ).replace("&nbsp;", " ")
        except Exception as e:
            pytest.fail(f"Format {fmt} failed validation: {str(e)}")


def test_combining_all_export_options(output_dir: str):
    """Test exporting with all options combined (full path, LOC, size, mtime)."""
    complex_structure = {
        "_loc": 500,
        "_size": 1024 * 1024,
        "_mtime": int(time.time()),
        "_files": [
            ("file1.txt", "/path/to/file1.txt", 100, 512, int(time.time()) - 86400),
            ("file2.py", "/path/to/file2.py", 200, 1024, int(time.time())),
        ],
        "subdir": {
            "_loc": 300,
            "_size": 2048,
            "_mtime": int(time.time()) - 3600,
            "_files": [
                (
                    "subfile.md",
                    "/path/to/subdir/subfile.md",
                    300,
                    2048,
                    int(time.time()) - 7200,
                ),
            ],
            "nested": {
                "_max_depth_reached": True,
            },
        },
    }
    formats = ["txt", "json", "html", "md", "jsx"]
    for fmt in formats:
        output_path = os.path.join(output_dir, f"combined_options.{fmt}")
        export_structure(
            complex_structure,
            "complex_root",
            fmt,
            output_path,
            show_full_path=True,
            sort_by_loc=True,
            sort_by_size=True,
            sort_by_mtime=True,
        )
        assert os.path.exists(output_path)
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "/path/to/file1.txt" in content.replace("&quot;", '"')
        if fmt != "jsx":
            assert "100" in content.replace("&quot;", '"')
            assert "200" in content.replace("&quot;", '"')
            assert "300" in content.replace("&quot;", '"')
        assert "512 B" in content.replace("&quot;", '"') or "0.5 KB" in content.replace(
            "&quot;", '"'
        )
        assert "1.0 KB" in content.replace(
            "&quot;", '"'
        ) or "1024 B" in content.replace("&quot;", '"')
        assert "2.0 KB" in content.replace(
            "&quot;", '"'
        ) or "2048 B" in content.replace("&quot;", '"')
        timestamp_patterns = [
            "Today",
            "Yesterday",
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]
        if fmt != "json":
            timestamp_matches = [
                pattern for pattern in timestamp_patterns if pattern in content
            ]
            assert (
                len(timestamp_matches) > 0
            ), f"No timestamp format found in {fmt} export"
        if fmt == "txt":
            assert "⋯ (max depth reached)" in content
        elif fmt == "json":
            assert "_max_depth_reached" in content
        elif fmt == "html":
            assert "max-depth" in content
        elif fmt == "md":
            assert "*(max depth reached)*" in content
        elif fmt == "jsx":
            assert "max depth reached" in content
