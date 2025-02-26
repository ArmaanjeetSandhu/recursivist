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


def test_directory_exporter_init():
    """Test DirectoryExporter initialization."""
    structure = {"_files": ["file1.txt"], "dir1": {"_files": ["file2.py"]}}
    exporter = DirectoryExporter(structure, "test_root")

    assert exporter.structure == structure
    assert exporter.root_name == "test_root"


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
