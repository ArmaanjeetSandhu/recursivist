"""Tests for the export functionality of the recursivist package."""

import json
import os

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

    normalized_content = content.replace("\\", "/")
    base_name = os.path.basename(sample_directory)
    assert (
        f"{base_name}/file1.txt" in normalized_content
        or "file1.txt" in normalized_content
    )
    assert (
        f"{base_name}/file2.py" in normalized_content
        or "file2.py" in normalized_content
    )
    assert "subdir" in content


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
    assert "show_full_path" in data
    assert data["show_full_path"] is False


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
    assert "show_full_path" in data
    assert data["show_full_path"] is True

    files = data["structure"]["_files"]

    assert len(files) > 0, "No files found in JSON output"

    for file_path in files:
        assert isinstance(file_path, str), "File path is not a string"
        assert any(
            ext in file_path for ext in [".txt", ".py", ".json", ".md", ".gitignore"]
        ), f"File path '{file_path}' doesn't seem to contain valid file information"


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
    assert "Showing full file paths" not in content


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
    assert "Showing full file paths" in content

    normalized_content = content.replace("\\", "/")
    base_name = os.path.basename(sample_directory)
    assert (
        f"{base_name}/file1.txt" in normalized_content
        or "file1.txt" in normalized_content
    )
    assert (
        f"{base_name}/file2.py" in normalized_content
        or "file2.py" in normalized_content
    )
    assert "subdir" in content


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
    assert "Showing full file paths" not in content


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
    assert "Showing full file paths" in content

    normalized_content = content.replace("\\", "/")
    base_name = os.path.basename(sample_directory)
    assert (
        f"`{base_name}/file1.txt`" in normalized_content
        or "`file1.txt`" in normalized_content
    )
    assert (
        f"`{base_name}/file2.py`" in normalized_content
        or "`file2.py`" in normalized_content
    )
    assert "- 📁 **subdir**" in content


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
    assert "Showing full file paths" not in content


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
    assert "Showing full file paths" in content
    assert "ChevronDown" in content
    assert "ChevronUp" in content


def test_export_unsupported_format(sample_directory, output_dir):
    """Test exporting to an unsupported format raises ValueError."""
    structure, _ = get_directory_structure(sample_directory)
    output_path = os.path.join(output_dir, "structure.unsupported")

    with pytest.raises(ValueError):
        export_structure(structure, sample_directory, "unsupported", output_path)


def test_export_error_handling(sample_directory, output_dir, mocker):
    """Test error handling during export."""
    structure, _ = get_directory_structure(sample_directory)
    output_path = os.path.join(output_dir, "structure.txt")

    mocker.patch("builtins.open", side_effect=PermissionError("Permission denied"))

    with pytest.raises(Exception):
        export_structure(structure, sample_directory, "txt", output_path)
