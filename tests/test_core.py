"""Tests for the core functionality of the recursivist package."""

import os

from recursivist.core import (
    generate_color_for_extension,
    get_directory_structure,
    parse_ignore_file,
    should_exclude,
)


def test_get_directory_structure(sample_directory):
    """Test that directory structure is correctly built."""
    structure, extensions = get_directory_structure(sample_directory)

    assert isinstance(structure, dict)
    assert "_files" in structure
    assert "subdir" in structure

    assert "file1.txt" in structure["_files"]
    assert "file2.py" in structure["_files"]

    assert ".txt" in extensions
    assert ".py" in extensions
    assert ".md" in extensions
    assert ".json" in extensions


def test_get_directory_structure_with_full_path(sample_directory):
    """Test that directory structure with full paths is correctly built."""
    structure, extensions = get_directory_structure(
        sample_directory, show_full_path=True
    )

    assert isinstance(structure, dict)
    assert "_files" in structure
    assert "subdir" in structure

    assert isinstance(structure["_files"][0], tuple)
    assert len(structure["_files"][0]) == 2

    found_txt = False
    found_py = False
    base_name = os.path.basename(sample_directory)

    for file_name, full_path in structure["_files"]:
        if file_name == "file1.txt":
            found_txt = True
            norm_path = full_path.replace("\\", "/")
            assert f"{base_name}/file1.txt" in norm_path or file_name in norm_path

        if file_name == "file2.py":
            found_py = True
            norm_path = full_path.replace("\\", "/")
            assert f"{base_name}/file2.py" in norm_path or file_name in norm_path

    assert found_txt, "file1.txt not found in structure with full path"
    assert found_py, "file2.py not found in structure with full path"

    assert ".txt" in extensions
    assert ".py" in extensions
    assert ".md" in extensions
    assert ".json" in extensions


def test_get_directory_structure_with_excludes(sample_directory):
    """Test directory structure with excluded directories."""
    exclude_dirs = ["node_modules"]
    structure, _ = get_directory_structure(sample_directory, exclude_dirs)

    assert "node_modules" not in structure


def test_get_directory_structure_with_exclude_extensions(sample_directory):
    """Test directory structure with excluded file extensions."""
    exclude_extensions = {".py"}
    structure, extensions = get_directory_structure(
        sample_directory, exclude_extensions=exclude_extensions
    )

    assert "file2.py" not in structure["_files"]
    assert ".py" not in extensions


def test_get_directory_structure_with_ignore_file(sample_directory):
    """Test directory structure respects gitignore patterns."""
    log_file = os.path.join(sample_directory, "app.log")
    with open(log_file, "w") as f:
        f.write("Some log content")

    structure, _ = get_directory_structure(sample_directory, ignore_file=".gitignore")

    assert "app.log" not in structure["_files"]
    assert "node_modules" not in structure


def test_generate_color_for_extension():
    """Test color generation for file extensions."""
    color1 = generate_color_for_extension(".py")
    color2 = generate_color_for_extension(".py")
    assert color1 == color2

    color_py = generate_color_for_extension(".py")
    color_txt = generate_color_for_extension(".txt")
    assert color_py != color_txt

    assert color_py.startswith("#")
    assert len(color_py) == 7


def test_parse_ignore_file(sample_directory):
    """Test parsing of ignore file."""
    ignore_file_path = os.path.join(sample_directory, ".gitignore")
    patterns = parse_ignore_file(ignore_file_path)

    assert "*.log" in patterns
    assert "node_modules" in patterns


def test_should_exclude(mocker):
    """Test the exclude logic."""
    mocker.patch("os.path.isfile", return_value=True)

    ignore_context = {"patterns": ["*.log", "node_modules"], "current_dir": "/test"}

    assert should_exclude("/test/app.log", ignore_context)
    assert not should_exclude("/test/app.txt", ignore_context)

    assert should_exclude("/test/node_modules", ignore_context)
    assert not should_exclude("/test/src", ignore_context)

    ignore_context_without_patterns = {
        "patterns": [],
        "current_dir": "/test",
    }
    exclude_extensions = {".py"}

    assert should_exclude(
        "/test/script.py", ignore_context_without_patterns, exclude_extensions
    )
    assert not should_exclude(
        "/test/app.txt", ignore_context_without_patterns, exclude_extensions
    )


def test_empty_directory(temp_dir):
    """Test handling of empty directories."""
    structure, extensions = get_directory_structure(temp_dir)

    assert structure == {}
    assert not extensions


def test_permission_denied(mocker, temp_dir):
    """Test handling of permission denied errors."""
    mocker.patch("os.listdir", side_effect=PermissionError("Permission denied"))

    structure, extensions = get_directory_structure(temp_dir)

    assert structure == {}
    assert not extensions
