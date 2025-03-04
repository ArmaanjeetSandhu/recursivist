"""
Tests for the core functionality of the recursivist package.

This module tests the fundamental components of the package:
- Directory structure generation and representation
- Pattern matching and filtering
- Color coding by file extension
- Handling of ignore files
- Tree visualization formatting
"""

import os
import re

from rich.text import Text
from rich.tree import Tree

from recursivist.core import (
    build_tree,
    compile_regex_patterns,
    generate_color_for_extension,
    get_directory_structure,
    parse_ignore_file,
    should_exclude,
    sort_files_by_type,
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
    """Test that directory structure with absolute paths is correctly built."""
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
    for file_name, full_path in structure["_files"]:
        if file_name == "file1.txt":
            found_txt = True
            assert os.path.isabs(
                full_path.replace("/", os.sep)
            ), f"Path should be absolute: {full_path}"
            expected_path = os.path.abspath(os.path.join(sample_directory, "file1.txt"))
            normalized_expected = expected_path.replace(os.sep, "/")
            assert (
                full_path == normalized_expected
            ), f"Expected {normalized_expected}, got {full_path}"
        if file_name == "file2.py":
            found_py = True
            assert os.path.isabs(
                full_path.replace("/", os.sep)
            ), f"Path should be absolute: {full_path}"
            expected_path = os.path.abspath(os.path.join(sample_directory, "file2.py"))
            normalized_expected = expected_path.replace(os.sep, "/")
            assert (
                full_path == normalized_expected
            ), f"Expected {normalized_expected}, got {full_path}"
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


def test_get_directory_structure_with_multiple_excludes(sample_directory):
    """Test directory structure with multiple excluded directories."""
    os.makedirs(os.path.join(sample_directory, "dist"), exist_ok=True)
    os.makedirs(os.path.join(sample_directory, "build"), exist_ok=True)
    with open(os.path.join(sample_directory, "dist", "bundle.js"), "w") as f:
        f.write("// Bundled JavaScript")
    with open(os.path.join(sample_directory, "build", "output.txt"), "w") as f:
        f.write("Build output")
    exclude_dirs = ["node_modules", "dist", "build"]
    structure, _ = get_directory_structure(sample_directory, exclude_dirs)
    assert "node_modules" not in structure
    assert "dist" not in structure
    assert "build" not in structure


def test_get_directory_structure_with_exclude_extensions(sample_directory):
    """Test directory structure with excluded file extensions."""
    exclude_extensions = {".py"}
    structure, extensions = get_directory_structure(
        sample_directory, exclude_extensions=exclude_extensions
    )
    assert "file2.py" not in structure["_files"]
    assert ".py" not in extensions


def test_get_directory_structure_with_multiple_exclude_extensions(sample_directory):
    """Test directory structure with multiple excluded file extensions."""
    with open(os.path.join(sample_directory, "script.js"), "w") as f:
        f.write("// JavaScript code")
    with open(os.path.join(sample_directory, "styles.css"), "w") as f:
        f.write("/* CSS styles */")
    with open(os.path.join(sample_directory, "data.csv"), "w") as f:
        f.write("column1,column2\nvalue1,value2")
    exclude_extensions = {".py", ".js", ".css"}
    structure, extensions = get_directory_structure(
        sample_directory, exclude_extensions=exclude_extensions
    )
    file_names = structure.get("_files", [])
    assert "file2.py" not in file_names
    assert "script.js" not in file_names
    assert "styles.css" not in file_names
    assert "data.csv" in file_names
    assert ".py" not in extensions
    assert ".js" not in extensions
    assert ".css" not in extensions
    assert ".csv" in extensions


def test_get_directory_structure_with_ignore_file(sample_directory):
    """Test directory structure respects gitignore patterns."""
    log_file = os.path.join(sample_directory, "app.log")
    with open(log_file, "w") as f:
        f.write("Some log content")
    structure, _ = get_directory_structure(sample_directory, ignore_file=".gitignore")
    assert "app.log" not in structure["_files"]
    assert "node_modules" not in structure


def test_get_directory_structure_with_multiple_ignore_patterns(sample_directory):
    """Test directory structure with multiple ignore patterns."""
    gitignore_path = os.path.join(sample_directory, ".gitignore")
    with open(gitignore_path, "a") as f:
        f.write("\n*.tmp\n*.cache\ndist/\n")
    with open(os.path.join(sample_directory, "temp.tmp"), "w") as f:
        f.write("Temporary file")
    with open(os.path.join(sample_directory, "data.cache"), "w") as f:
        f.write("Cache file")
    os.makedirs(os.path.join(sample_directory, "dist"), exist_ok=True)
    with open(os.path.join(sample_directory, "dist", "bundle.js"), "w") as f:
        f.write("// Bundled JavaScript")
    structure, _ = get_directory_structure(sample_directory, ignore_file=".gitignore")
    assert "temp.tmp" not in structure["_files"]
    assert "data.cache" not in structure["_files"]
    assert "dist" not in structure


def test_get_directory_structure_with_exclude_patterns(sample_directory):
    """Test directory structure with exclude patterns."""
    with open(os.path.join(sample_directory, "test_file1.py"), "w") as f:
        f.write("# Test file 1")
    with open(os.path.join(sample_directory, "test_file2.js"), "w") as f:
        f.write("// Test file 2")
    exclude_patterns = ["test_*"]
    structure, _ = get_directory_structure(
        sample_directory, exclude_patterns=exclude_patterns
    )
    assert "test_file1.py" not in structure["_files"]
    assert "test_file2.js" not in structure["_files"]


def test_get_directory_structure_with_include_patterns(sample_directory):
    """Test directory structure with include patterns."""
    with open(os.path.join(sample_directory, "include_this.md"), "w") as f:
        f.write("# Include this file")
    with open(os.path.join(sample_directory, "exclude_this.txt"), "w") as f:
        f.write("Exclude this file")
    include_patterns = ["*.md"]
    structure, extensions = get_directory_structure(
        sample_directory, include_patterns=include_patterns
    )
    md_files_found = False
    non_md_files_found = False
    for file in structure.get("_files", []):
        file_name = file if isinstance(file, str) else file[0]
        if file_name.endswith(".md"):
            md_files_found = True
        else:
            non_md_files_found = True
    assert md_files_found, "No markdown files found despite include pattern"
    assert not non_md_files_found, "Non-markdown files found despite include pattern"
    if "subdir" in structure:
        for file in structure["subdir"].get("_files", []):
            file_name = file if isinstance(file, str) else file[0]
            assert file_name.endswith(
                ".md"
            ), f"Non-markdown file {file_name} found in subdir despite include pattern"


def test_get_directory_structure_with_regex_patterns(sample_directory):
    """Test directory structure with regex patterns."""
    with open(os.path.join(sample_directory, "test123.txt"), "w") as f:
        f.write("Test file with numbers")
    with open(os.path.join(sample_directory, "test456.txt"), "w") as f:
        f.write("Another test file with numbers")
    with open(os.path.join(sample_directory, "regular.txt"), "w") as f:
        f.write("Regular file")
    exclude_patterns = [re.compile(r"test\d+\.txt")]
    structure, _ = get_directory_structure(
        sample_directory, exclude_patterns=exclude_patterns
    )
    assert "test123.txt" not in structure["_files"]
    assert "test456.txt" not in structure["_files"]
    assert "regular.txt" in structure["_files"]
    include_patterns = [re.compile(r"test\d+\.txt")]
    structure, _ = get_directory_structure(
        sample_directory, include_patterns=include_patterns
    )
    for file in structure["_files"]:
        file_name = file if isinstance(file, str) else file[0]
        assert re.match(
            r"test\d+\.txt", file_name
        ), f"File {file_name} doesn't match include pattern"


def test_generate_color_for_extension():
    """Test color generation for file extensions."""
    color1 = generate_color_for_extension(".py")
    color2 = generate_color_for_extension(".py")
    assert color1 == color2, "Same extension should produce the same color"
    color_py = generate_color_for_extension(".py")
    color_txt = generate_color_for_extension(".txt")
    assert color_py != color_txt, "Different extensions should produce different colors"
    assert color_py.startswith("#"), "Color should be a hex code starting with #"
    assert len(color_py) == 7, "Color should be a 7-character hex code (#RRGGBB)"


def test_generate_color_consistency():
    """Test consistency of color generation across multiple extensions."""
    extensions = [".py", ".js", ".txt", ".md", ".html", ".css", ".json", ".xml", ".csv"]
    colors = {ext: generate_color_for_extension(ext) for ext in extensions}
    for ext in extensions:
        assert (
            generate_color_for_extension(ext) == colors[ext]
        ), f"Color for {ext} is not consistent"
    unique_colors = set(colors.values())
    assert len(unique_colors) == len(extensions), "Some extensions got the same color"


def test_parse_ignore_file(sample_directory):
    """Test parsing of ignore file."""
    ignore_file_path = os.path.join(sample_directory, ".gitignore")
    patterns = parse_ignore_file(ignore_file_path)
    assert "*.log" in patterns
    assert "node_modules" in patterns


def test_parse_ignore_file_with_comments(temp_dir):
    """Test parsing ignore file with comments and empty lines."""
    ignore_file_path = os.path.join(temp_dir, "test_ignore")
    with open(ignore_file_path, "w") as f:
        f.write("# This is a comment\n")
        f.write("*.log\n")
        f.write("\n")
        f.write("node_modules/\n")
        f.write("# Another comment\n")
        f.write("dist\n")
    patterns = parse_ignore_file(ignore_file_path)
    assert "*.log" in patterns
    assert "node_modules" in patterns
    assert "dist" in patterns
    assert "# This is a comment" not in patterns
    assert "# Another comment" not in patterns
    assert "" not in patterns


def test_parse_ignore_file_nonexistent():
    """Test parsing a non-existent ignore file."""
    patterns = parse_ignore_file("/path/to/nonexistent/file")
    assert patterns == []


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


def test_should_exclude_with_negation_patterns(mocker):
    """Test exclude logic with negation patterns - current implementation doesn't support negation."""
    mocker.patch("os.path.isfile", return_value=True)
    ignore_context = {"patterns": ["*.log", "!important.log"], "current_dir": "/test"}
    assert should_exclude("/test/app.log", ignore_context)
    assert should_exclude("/test/important.log", ignore_context)
    assert not should_exclude("/test/app.txt", ignore_context)


def test_should_exclude_with_complex_patterns(mocker):
    """Minimal test for exclude logic."""
    mocker.patch("os.path.isfile", return_value=True)
    ignore_context = {"patterns": [], "current_dir": "/test"}
    exclude_extensions = {".txt"}
    assert should_exclude("/test/file.txt", ignore_context, exclude_extensions)
    assert not should_exclude("/test/file.py", ignore_context, exclude_extensions)


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


def test_subdirectory_full_path(sample_directory):
    """Test full path resolution for files in subdirectories."""
    structure, _ = get_directory_structure(sample_directory, show_full_path=True)
    assert "subdir" in structure
    assert "_files" in structure["subdir"]
    found_md = False
    found_json = False
    for file_name, full_path in structure["subdir"]["_files"]:
        if file_name == "subfile1.md":
            found_md = True
            expected_path = os.path.abspath(
                os.path.join(sample_directory, "subdir", "subfile1.md")
            )
            normalized_expected = expected_path.replace(os.sep, "/")
            assert (
                full_path == normalized_expected
            ), f"Expected {normalized_expected}, got {full_path}"
        if file_name == "subfile2.json":
            found_json = True
            expected_path = os.path.abspath(
                os.path.join(sample_directory, "subdir", "subfile2.json")
            )
            normalized_expected = expected_path.replace(os.sep, "/")
            assert (
                full_path == normalized_expected
            ), f"Expected {normalized_expected}, got {full_path}"
    assert found_md, "subfile1.md not found in structure with full path"
    assert found_json, "subfile2.json not found in structure with full path"


def test_compile_regex_patterns():
    """Test compiling regex patterns."""
    valid_patterns = ["\\d+", "test_.*", "[a-z]+"]
    compiled = compile_regex_patterns(valid_patterns, is_regex=True)
    assert len(compiled) == 3
    assert all(isinstance(p, re.Pattern) for p in compiled)
    invalid_patterns = ["[invalid", "unmatched)"]
    compiled = compile_regex_patterns(invalid_patterns, is_regex=True)
    assert len(compiled) == 2
    assert all(isinstance(p, str) for p in compiled)
    glob_patterns = ["*.py", "test_*"]
    compiled = compile_regex_patterns(glob_patterns, is_regex=False)
    assert len(compiled) == 2
    assert all(isinstance(p, str) for p in compiled)


def test_sort_files_by_type():
    """Test sorting files by type."""
    files = ["c.txt", "b.py", "a.txt", "d.py"]
    sorted_files = sort_files_by_type(files)
    assert sorted_files == ["b.py", "d.py", "a.txt", "c.txt"]
    tuple_files = [
        ("c.txt", "/path/to/c.txt"),
        ("b.py", "/path/to/b.py"),
        ("a.txt", "/path/to/a.txt"),
        ("d.py", "/path/to/d.py"),
    ]
    sorted_tuple_files = sort_files_by_type(tuple_files)
    assert sorted_tuple_files == [
        ("b.py", "/path/to/b.py"),
        ("d.py", "/path/to/d.py"),
        ("a.txt", "/path/to/a.txt"),
        ("c.txt", "/path/to/c.txt"),
    ]
    mixed_files = [
        "c.txt",
        ("b.py", "/path/to/b.py"),
        "a.txt",
        ("d.py", "/path/to/d.py"),
    ]
    sorted_mixed = sort_files_by_type(mixed_files)
    assert len(sorted_mixed) == 4
    assert "a.txt" in sorted_mixed
    assert "c.txt" in sorted_mixed
    assert ("b.py", "/path/to/b.py") in sorted_mixed
    assert ("d.py", "/path/to/d.py") in sorted_mixed


def test_build_tree(mocker):
    """Test building a tree structure with colored file names."""
    mock_tree = mocker.MagicMock(spec=Tree)
    color_map = {".py": "#FF0000", ".txt": "#00FF00"}
    structure = {
        "_files": ["file1.txt", "file2.py"],
        "subdir": {"_files": ["subfile.py"]},
    }
    build_tree(structure, mock_tree, color_map)
    mock_calls = mock_tree.add.call_args_list
    assert len(mock_calls) >= 3
    colored_texts = [
        call.args[0] for call in mock_calls if isinstance(call.args[0], Text)
    ]
    assert any(
        text.plain == "📄 file1.txt" and "#00FF00" in text.style
        for text in colored_texts
    )
    assert any(
        text.plain == "📄 file2.py" and "#FF0000" in text.style
        for text in colored_texts
    )
    mock_tree.reset_mock()
    structure_with_paths = {
        "_files": [
            ("file1.txt", "/path/to/file1.txt"),
            ("file2.py", "/path/to/file2.py"),
        ],
        "subdir": {"_files": [("subfile.py", "/path/to/subdir/subfile.py")]},
    }
    build_tree(structure_with_paths, mock_tree, color_map, show_full_path=True)
    mock_calls = mock_tree.add.call_args_list
    colored_texts = [
        call.args[0] for call in mock_calls if isinstance(call.args[0], Text)
    ]
    assert any(text.plain == "📄 /path/to/file1.txt" for text in colored_texts)
    assert any(text.plain == "📄 /path/to/file2.py" for text in colored_texts)


def test_build_tree_with_max_depth(mocker):
    """Test building a tree structure with max depth indicator."""
    mock_tree = mocker.MagicMock(spec=Tree)
    mock_subtree = mocker.MagicMock(spec=Tree)
    mock_tree.add.return_value = mock_subtree
    color_map = {".py": "#FF0000", ".txt": "#00FF00"}
    structure = {"_files": ["file1.txt"], "subdir": {"_max_depth_reached": True}}
    build_tree(structure, mock_tree, color_map)
    mock_subtree.add.assert_called_once()
    args = mock_subtree.add.call_args[0]
    assert isinstance(args[0], Text)
    assert args[0].plain == "⋯ (max depth reached)"
    assert "dim" in args[0].style
