"""
Tests for the export functionality of the recursivist package.

This module tests the export capabilities:
- Sorting files by name and extension
- Directory exporter initialization and configuration
- Export to different formats (txt, json, html, md, jsx)
- Full path display in exports
- Error handling for export operations
"""

import json
import os
import re

import pytest

from recursivist.core import export_structure, get_directory_structure
from recursivist.exports import DirectoryExporter, sort_files_by_type


def test_sort_files_by_type():
    """Test sorting files by extension and name."""
    files = ["c.txt", "b.py", "a.txt", "d.py"]
    sorted_files = sort_files_by_type(files)
    assert sorted_files == ["b.py", "d.py", "a.txt", "c.txt"]


def test_sort_files_by_type_with_tuples():
    """Test sorting files by extension and name when using tuples for full paths."""
    files = [
        ("c.txt", "/path/to/c.txt"),
        ("b.py", "/path/to/b.py"),
        ("a.txt", "/path/to/a.txt"),
        ("d.py", "/path/to/d.py"),
    ]
    sorted_files = sort_files_by_type(files)
    expected = [
        ("b.py", "/path/to/b.py"),
        ("d.py", "/path/to/d.py"),
        ("a.txt", "/path/to/a.txt"),
        ("c.txt", "/path/to/c.txt"),
    ]
    assert sorted_files == expected


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
    sorted_strings = [f for f in sorted_files if isinstance(f, str)]
    sorted_tuples = [f for f in sorted_files if isinstance(f, tuple)]
    assert sorted_strings == ["d.py", "c.txt"]
    assert sorted_tuples == [
        ("b.py", "/path/to/b.py"),
        ("a.txt", "/path/to/a.txt"),
    ]


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
    for file in sorted_files:
        assert file in files


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


def test_export_to_txt(sample_directory, output_dir):
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


def test_export_to_txt_with_full_path(sample_directory, output_dir):
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


def test_txt_export_format(sample_directory, output_dir):
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
    assert all(re.match(r".*├── 📄 .*", line) for line in file_lines)
    dir_lines = [line for line in lines if "📁" in line]
    assert all(re.match(r".*├── 📁 .*", line) for line in dir_lines)


def test_export_to_json(sample_directory, output_dir):
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


def test_export_to_json_with_full_path(sample_directory, output_dir):
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
    for file_path in files:
        assert isinstance(file_path, str), "File path is not a string"
        assert os.path.isabs(
            file_path.replace("/", os.sep)
        ), f"File path '{file_path}' is not absolute"
        base_name = os.path.basename(sample_directory)
        assert (
            base_name in file_path
        ), f"File path '{file_path}' doesn't contain base directory '{base_name}'"


def test_json_export_structure(sample_directory, output_dir):
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


def test_export_to_html(sample_directory, output_dir):
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


def test_export_to_html_with_full_path(sample_directory, output_dir):
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


def test_html_export_styling(sample_directory, output_dir):
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


def test_export_to_markdown(sample_directory, output_dir):
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


def test_export_to_markdown_with_full_path(sample_directory, output_dir):
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


def test_markdown_export_formatting(sample_directory, output_dir):
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


def test_export_to_jsx(sample_directory, output_dir):
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
    assert "CollapsibleItem" in content
    assert "file1.txt" in content
    assert "file2.py" in content
    assert "subdir" in content
    assert "ChevronDown" in content
    assert "ChevronUp" in content


def test_export_to_jsx_with_full_path(sample_directory, output_dir):
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
    assert "CollapsibleItem" in content
    assert "ChevronDown" in content
    assert "ChevronUp" in content
    for file_name in ["file1.txt", "file2.py"]:
        expected_abs_path = os.path.abspath(os.path.join(sample_directory, file_name))
        expected_abs_path = expected_abs_path.replace(os.sep, "/")
        escaped_path = expected_abs_path.replace('"', '\\"')
        assert (
            escaped_path in content or expected_abs_path in content
        ), f"Absolute path for {file_name} not found in JSX export"


def test_jsx_export_functionality(sample_directory, output_dir):
    """Test the functional elements of JSX export."""
    structure, _ = get_directory_structure(sample_directory)
    output_path = os.path.join(output_dir, "structure_functional.jsx")
    export_structure(structure, sample_directory, "jsx", output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "import React, { useState, useEffect } from 'react';" in content
    assert (
        "import { ChevronDown, ChevronUp, Folder, Maximize2, Minimize2 } from 'lucide-react';"
        in content
    )
    assert "const CollapsibleItem =" in content
    assert "const DirectoryViewer =" in content
    assert "const [isOpen, setIsOpen] = useState(false);" in content
    assert "const CollapsibleContext = React.createContext();" in content
    assert "handleExpandAll" in content
    assert "handleCollapseAll" in content
    assert "export default DirectoryViewer;" in content


def test_export_unsupported_format(sample_directory, output_dir):
    """Test exporting to an unsupported format raises ValueError."""
    structure, _ = get_directory_structure(sample_directory)
    output_path = os.path.join(output_dir, "structure.unsupported")
    with pytest.raises(ValueError) as excinfo:
        export_structure(structure, sample_directory, "unsupported", output_path)
    assert "Unsupported format" in str(excinfo.value)


def test_export_error_handling(sample_directory, output_dir, mocker):
    """Test error handling during export."""
    structure, _ = get_directory_structure(sample_directory)
    output_path = os.path.join(output_dir, "structure.txt")
    mocker.patch("builtins.open", side_effect=PermissionError("Permission denied"))
    with pytest.raises(Exception):
        export_structure(structure, sample_directory, "txt", output_path)


def test_export_with_max_depth_indicator(temp_dir, output_dir):
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
