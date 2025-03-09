"""
Tests for the regex pattern matching functionality of the recursivist package.

This module contains comprehensive tests for pattern matching, including:
- Regular expression compilation and validation
- Pattern matching for file and directory exclusion
- Include patterns that override exclusions
- Complex regular expressions for advanced filtering
- Integration with directory structure generation
- Error handling for invalid regex patterns
"""

import os
import re
from pathlib import Path

import pytest
from pytest_mock import MockerFixture
from typer.testing import CliRunner

from recursivist.cli import app
from recursivist.core import (
    compile_regex_patterns,
    get_directory_structure,
    should_exclude,
)


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def pattern_test_directory(temp_dir):
    """
    Create a directory with various test files for pattern matching.

    Structure:
    temp_dir/
    ├── regular_file.txt
    ├── test_file1.py
    ├── test_file2.js
    ├── spec.file.js
    ├── .hidden.file
    ├── config.json
    ├── data_20230101.csv
    ├── data_20230102.csv
    ├── logs/
    │   ├── app.log
    │   ├── error.log
    │   └── debug.log
    └── tests/
        ├── unit/
        │   └── test_unit.py
        └── integration/
            └── test_integration.py
    """

    os.makedirs(os.path.join(temp_dir, "logs"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "tests", "unit"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "tests", "integration"), exist_ok=True)
    with open(os.path.join(temp_dir, "regular_file.txt"), "w") as f:
        f.write("Regular file content")
    with open(os.path.join(temp_dir, "test_file1.py"), "w") as f:
        f.write("Test file 1 content")
    with open(os.path.join(temp_dir, "test_file2.js"), "w") as f:
        f.write("Test file 2 content")
    with open(os.path.join(temp_dir, "spec.file.js"), "w") as f:
        f.write("Spec file content")
    with open(os.path.join(temp_dir, ".hidden.file"), "w") as f:
        f.write("Hidden file content")
    with open(os.path.join(temp_dir, "config.json"), "w") as f:
        f.write('{"key": "value"}')
    with open(os.path.join(temp_dir, "data_20230101.csv"), "w") as f:
        f.write("date,value\n2023-01-01,100")
    with open(os.path.join(temp_dir, "data_20230102.csv"), "w") as f:
        f.write("date,value\n2023-01-02,200")
    with open(os.path.join(temp_dir, "logs", "app.log"), "w") as f:
        f.write("App log content")
    with open(os.path.join(temp_dir, "logs", "error.log"), "w") as f:
        f.write("Error log content")
    with open(os.path.join(temp_dir, "logs", "debug.log"), "w") as f:
        f.write("Debug log content")
    with open(os.path.join(temp_dir, "tests", "unit", "test_unit.py"), "w") as f:
        f.write("Unit test content")
    with open(
        os.path.join(temp_dir, "tests", "integration", "test_integration.py"), "w"
    ) as f:
        f.write("Integration test content")
    return temp_dir


def test_compile_regex_patterns():
    """Test compiling regex patterns with valid and invalid patterns."""
    patterns = ["*.py", "test_*"]
    compiled = compile_regex_patterns(patterns, is_regex=False)
    assert compiled == patterns
    patterns = [r"\.py$", r"^test_"]
    compiled = compile_regex_patterns(patterns, is_regex=True)
    assert len(compiled) == 2
    for pattern in compiled:
        assert isinstance(pattern, re.Pattern)
    assert compiled[0].search("file.py")
    assert not compiled[0].search("file.txt")
    assert compiled[1].search("test_file.py")
    assert not compiled[1].search("file_test.py")


def test_compile_regex_patterns_empty():
    """Test compiling empty pattern lists."""
    compiled = compile_regex_patterns([], is_regex=False)
    assert compiled == []
    compiled = compile_regex_patterns([], is_regex=True)
    assert compiled == []


def test_compile_regex_patterns_invalid():
    """Test compiling invalid regex patterns."""
    patterns = [r"[invalid", r"(unclosed"]
    compiled = compile_regex_patterns(patterns, is_regex=True)
    assert len(compiled) == 2
    for pattern in compiled:
        assert isinstance(pattern, str)
    assert compiled == patterns


def test_compile_regex_patterns_complex():
    """Test compiling complex regex patterns."""
    patterns = [
        r"^data_\d{8}\.csv$",  # Match date-formatted CSV files
        r".*\.(?:log|tmp)$",  # Match log or tmp files with any prefix
        r"^\..*",  # Match hidden files starting with .
        r"^(?:test|spec).*\.js$",  # Match test or spec JS files
    ]
    compiled = compile_regex_patterns(patterns, is_regex=True)
    assert len(compiled) == 4
    assert all(isinstance(p, re.Pattern) for p in compiled)
    assert compiled[0].match("data_20230101.csv")
    assert not compiled[0].match("data_20230101.txt")
    assert compiled[1].match("app.log")
    assert compiled[1].match("temp.tmp")
    assert not compiled[1].match("app.txt")
    assert compiled[2].match(".hidden")
    assert not compiled[2].match("visible")
    assert compiled[3].match("test_file.js")
    assert compiled[3].match("spec.file.js")
    assert not compiled[3].match("regular.js")


def test_should_exclude_with_regex(mocker: MockerFixture):
    """Test the exclude logic with regex patterns."""
    mocker.patch("os.path.isfile", return_value=True)
    ignore_context = {"patterns": [], "current_dir": "/test"}
    exclude_patterns = [re.compile(r"\.py$"), re.compile(r"test_.*\.js$")]
    assert should_exclude(
        "/test/script.py", ignore_context, exclude_patterns=exclude_patterns
    )
    assert should_exclude(
        "/test/test_app.js", ignore_context, exclude_patterns=exclude_patterns
    )
    assert not should_exclude(
        "/test/script.txt", ignore_context, exclude_patterns=exclude_patterns
    )
    assert not should_exclude(
        "/test/app.js", ignore_context, exclude_patterns=exclude_patterns
    )
    include_patterns = [re.compile(r".*src.*"), re.compile(r"\.md$")]
    assert should_exclude(
        "/test/script.py", ignore_context, include_patterns=include_patterns
    )
    assert not should_exclude(
        "/test/src/script.py", ignore_context, include_patterns=include_patterns
    )
    assert not should_exclude(
        "/test/README.md", ignore_context, include_patterns=include_patterns
    )
    assert not should_exclude(
        "/test/src/script.py",
        ignore_context,
        exclude_patterns=exclude_patterns,
        include_patterns=include_patterns,
    )
    assert should_exclude(
        "/test/script.py",
        ignore_context,
        exclude_patterns=exclude_patterns,
        include_patterns=include_patterns,
    )


def test_should_exclude_with_basename_matching(mocker: MockerFixture):
    """Test the exclude logic with basename matching for regex patterns."""
    mocker.patch("os.path.isfile", return_value=True)
    ignore_context = {"patterns": [], "current_dir": "/test"}
    exclude_patterns = [re.compile(r"file\.txt$")]
    assert should_exclude(
        "/test/path/to/file.txt", ignore_context, exclude_patterns=exclude_patterns
    )
    assert not should_exclude(
        "/test/path/to/other.txt", ignore_context, exclude_patterns=exclude_patterns
    )
    exclude_patterns = [re.compile(r"file\+\[\]\.txt$")]
    assert should_exclude(
        "/test/path/to/file+[].txt", ignore_context, exclude_patterns=exclude_patterns
    )


def test_should_exclude_with_extensions(mocker: MockerFixture):
    """Test the exclude logic with file extensions."""
    mocker.patch("os.path.isfile", return_value=True)
    ignore_context = {"patterns": [], "current_dir": "/test"}
    exclude_extensions = {".py", ".js", ".log"}
    assert should_exclude(
        "/test/script.py", ignore_context, exclude_extensions=exclude_extensions
    )
    assert should_exclude(
        "/test/app.js", ignore_context, exclude_extensions=exclude_extensions
    )
    assert should_exclude(
        "/test/app.log", ignore_context, exclude_extensions=exclude_extensions
    )
    assert not should_exclude(
        "/test/README.md", ignore_context, exclude_extensions=exclude_extensions
    )


def test_should_exclude_case_sensitivity(mocker: MockerFixture):
    """Test case sensitivity in pattern matching."""
    mocker.patch("os.path.isfile", return_value=True)
    ignore_context = {"patterns": [], "current_dir": "/test"}
    exclude_patterns = [re.compile(r"\.py$", re.IGNORECASE)]
    assert should_exclude(
        "/test/script.py", ignore_context, exclude_patterns=exclude_patterns
    )
    assert should_exclude(
        "/test/script.PY", ignore_context, exclude_patterns=exclude_patterns
    )
    assert should_exclude(
        "/test/script.Py", ignore_context, exclude_patterns=exclude_patterns
    )
    exclude_patterns = [re.compile(r"\.py$")]
    assert should_exclude(
        "/test/script.py", ignore_context, exclude_patterns=exclude_patterns
    )
    assert not should_exclude(
        "/test/script.PY", ignore_context, exclude_patterns=exclude_patterns
    )
    exclude_extensions = {".py"}
    assert should_exclude(
        "/test/script.py", ignore_context, exclude_extensions=exclude_extensions
    )
    assert should_exclude(
        "/test/script.PY", ignore_context, exclude_extensions=exclude_extensions
    )


def test_should_exclude_with_ignore_patterns(mocker: MockerFixture):
    """Test exclude logic with ignore patterns."""
    mocker.patch("os.path.isfile", return_value=True)
    ignore_context = {"patterns": ["*.txt", "!important.txt"], "current_dir": "/test"}
    assert should_exclude("/test/file.txt", ignore_context)
    assert not should_exclude("/test/important.txt", ignore_context)
    assert not should_exclude("/test/file.py", ignore_context)


def test_get_directory_structure_with_regex_patterns(pattern_test_directory):
    """Test directory structure generation with regex patterns for filtering."""
    exclude_patterns = [re.compile(r"\.py$")]
    structure, extensions = get_directory_structure(
        pattern_test_directory, exclude_patterns=exclude_patterns
    )
    assert "_files" in structure
    py_files_found = False
    for file in structure.get("_files", []):
        file_name = file if isinstance(file, str) else file[0]
        if file_name.endswith(".py"):
            py_files_found = True
            break
    assert not py_files_found, "Python files were found despite exclude pattern"
    assert (
        ".py" not in extensions
    ), "Python extension was included despite exclude pattern"

    def check_subdirs_for_py_files(structure):
        for key, value in structure.items():
            if key != "_files" and isinstance(value, dict):
                if "_files" in value:
                    for file in value["_files"]:
                        file_name = file if isinstance(file, str) else file[0]
                        assert not file_name.endswith(
                            ".py"
                        ), f"Python file {file_name} found despite exclude pattern"
                check_subdirs_for_py_files(value)

    check_subdirs_for_py_files(structure)


def test_get_directory_structure_with_include_patterns(pattern_test_directory):
    """Test directory structure generation with include patterns for filtering."""
    include_patterns = [re.compile(r"\.json$")]
    structure, extensions = get_directory_structure(
        pattern_test_directory, include_patterns=include_patterns
    )
    if "_files" in structure:
        for file in structure["_files"]:
            file_name = file if isinstance(file, str) else file[0]
            assert file_name.endswith(
                ".json"
            ), f"Non-JSON file {file_name} was included"
    assert ".json" in extensions
    assert len(extensions) == 1, "Only JSON extension should be included"

    def check_subdirs_for_non_json(structure):
        for key, value in structure.items():
            if key != "_files" and isinstance(value, dict):
                if "_files" in value:
                    for file in value["_files"]:
                        file_name = file if isinstance(file, str) else file[0]
                        assert file_name.endswith(
                            ".json"
                        ), f"Non-JSON file {file_name} was included"
                check_subdirs_for_non_json(value)

    check_subdirs_for_non_json(structure)


def test_get_directory_structure_complex_regex(pattern_test_directory):
    """Test directory structure generation with complex regex patterns."""
    include_patterns = [re.compile(r"data_\d{8}\.csv$")]
    structure, extensions = get_directory_structure(
        pattern_test_directory, include_patterns=include_patterns
    )
    assert "_files" in structure
    assert len(structure["_files"]) == 2, "Should find exactly 2 data CSV files"
    file_names = [f if isinstance(f, str) else f[0] for f in structure["_files"]]
    assert "data_20230101.csv" in file_names
    assert "data_20230102.csv" in file_names
    assert ".csv" in extensions
    assert len(extensions) == 1, "Only CSV extension should be included"


def test_both_include_and_exclude_patterns(pattern_test_directory):
    """
    Test directory structure with both include and exclude patterns.

    The include patterns take precedence over exclude patterns in the actual implementation.
    """

    with open(os.path.join(pattern_test_directory, "include_me.py"), "w") as f:
        f.write("This should be included")
    with open(os.path.join(pattern_test_directory, "exclude_me.py"), "w") as f:
        f.write("This should be excluded")
    include_patterns = [re.compile(r"\.py$")]
    exclude_patterns = [re.compile(r"^exclude_.*\.py$")]
    structure, extensions = get_directory_structure(
        pattern_test_directory,
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns,
    )
    file_names = []
    if "_files" in structure:
        for file_item in structure["_files"]:
            if isinstance(file_item, tuple):
                file_names.append(file_item[0])
            else:
                file_names.append(file_item)
    assert "test_file1.py" in file_names
    assert "include_me.py" in file_names
    assert "exclude_me.py" in file_names
    assert "regular_file.txt" not in file_names
    assert "config.json" not in file_names


def test_cli_with_regex_patterns(runner, pattern_test_directory):
    """Test the CLI with regex pattern options."""
    result = runner.invoke(
        app,
        [
            "visualize",
            pattern_test_directory,
            "--include-pattern",
            r"data_\d{8}\.csv$",
            "--regex",
        ],
    )
    assert result.exit_code == 0
    assert "data_20230101.csv" in result.stdout
    assert "data_20230102.csv" in result.stdout
    assert "regular_file.txt" not in result.stdout
    assert "test_file1.py" not in result.stdout
    result = runner.invoke(
        app,
        [
            "visualize",
            pattern_test_directory,
            "--exclude-pattern",
            r"^test_|^\.hidden",
            "--regex",
        ],
    )
    assert result.exit_code == 0
    assert "test_file1.py" not in result.stdout
    assert "test_file2.js" not in result.stdout
    assert ".hidden.file" not in result.stdout
    assert "regular_file.txt" in result.stdout
    assert "data_20230101.csv" in result.stdout


def test_glob_patterns(pattern_test_directory):
    """Test glob pattern matching without regex."""
    exclude_patterns = ["test_*", "*.log"]
    structure, extensions = get_directory_structure(
        pattern_test_directory, exclude_patterns=exclude_patterns
    )
    test_files_found = False
    log_files_found = False

    def check_files(struct):
        nonlocal test_files_found, log_files_found
        if "_files" in struct:
            for file in struct["_files"]:
                file_name = file if isinstance(file, str) else file[0]
                if file_name.startswith("test_"):
                    test_files_found = True
                if file_name.endswith(".log"):
                    log_files_found = True
        for key, value in struct.items():
            if key != "_files" and isinstance(value, dict):
                check_files(value)

    check_files(structure)
    assert not test_files_found, "Test files were found despite glob exclude pattern"
    assert not log_files_found, "Log files were found despite glob exclude pattern"


def test_regex_with_statistics(pattern_test_directory):
    """Test regex pattern filtering with statistics options."""
    include_patterns = [re.compile(r"\.py$")]
    structure, extensions = get_directory_structure(
        pattern_test_directory,
        include_patterns=include_patterns,
        sort_by_loc=True,
        sort_by_size=True,
        sort_by_mtime=True,
    )
    assert "_loc" in structure
    assert "_size" in structure
    assert "_mtime" in structure
    if "_files" in structure:
        for file_item in structure["_files"]:
            assert isinstance(file_item, tuple)
            assert len(file_item) > 4, "File item doesn't include statistics"
            _, _, loc, size, mtime = file_item
            assert isinstance(loc, int)
            assert isinstance(size, int)
            assert isinstance(mtime, float)
    for key, value in structure.items():
        if (
            key != "_files"
            and key != "_loc"
            and key != "_size"
            and key != "_mtime"
            and isinstance(value, dict)
        ):
            assert "_loc" in value
            assert "_size" in value
            assert "_mtime" in value


def test_mixed_regex_and_glob_patterns(runner, pattern_test_directory):
    """Test mixing regex and glob patterns in the CLI."""
    with open(os.path.join(pattern_test_directory, "glob_match.txt"), "w") as f:
        f.write("Should match glob pattern")
    with open(os.path.join(pattern_test_directory, "regex_match.txt"), "w") as f:
        f.write("Should match regex pattern")
    result = runner.invoke(
        app, ["visualize", pattern_test_directory, "--exclude-pattern", "glob_*"]
    )
    assert result.exit_code == 0
    assert "glob_match.txt" not in result.stdout
    assert "regex_match.txt" in result.stdout
    result = runner.invoke(
        app,
        [
            "visualize",
            pattern_test_directory,
            "--exclude-pattern",
            r"regex_.*\.txt$",
            "--regex",
        ],
    )
    assert result.exit_code == 0
    assert "regex_match.txt" not in result.stdout
    assert "glob_match.txt" in result.stdout


def test_regex_pattern_escaping(pattern_test_directory):
    """Test regex pattern escaping for special characters."""
    special_file = os.path.join(pattern_test_directory, "file+[special].txt")
    with open(special_file, "w") as f:
        f.write("Special characters in filename")
    include_patterns = [re.compile(r"file\+\[special\]\.txt$")]
    structure, _ = get_directory_structure(
        pattern_test_directory, include_patterns=include_patterns
    )
    found = False
    if "_files" in structure:
        for file_item in structure["_files"]:
            file_name = file_item if isinstance(file_item, str) else file_item[0]
            if file_name == "file+[special].txt":
                found = True
                break
    assert found, "File with special characters not found with escaped regex pattern"


def test_regex_nested_directory_patterns(pattern_test_directory):
    """Test regex patterns for filtering files at different directory levels."""
    structure, _ = get_directory_structure(pattern_test_directory)
    assert "tests" in structure, "Base structure doesn't have tests directory"
    assert "unit" in structure["tests"], "Base structure doesn't have unit directory"
    assert (
        "integration" in structure["tests"]
    ), "Base structure doesn't have integration directory"
    include_patterns = [re.compile(r"test_.*\.py$")]
    structure, _ = get_directory_structure(
        pattern_test_directory, include_patterns=include_patterns
    )
    files_at_root = [
        f if isinstance(f, str) else f[0] for f in structure.get("_files", [])
    ]
    assert "test_file1.py" in files_at_root, "Root test_file1.py should be included"
    assert (
        "regular_file.txt" not in files_at_root
    ), "Non-matching files should be excluded"
    include_patterns = [re.compile(r"regular_file\.txt$")]
    structure, _ = get_directory_structure(
        pattern_test_directory, include_patterns=include_patterns
    )
    if "_files" in structure:
        files_at_root = [
            f if isinstance(f, str) else f[0] for f in structure.get("_files", [])
        ]
        assert "regular_file.txt" in files_at_root, "Regular file should be included"
        assert "test_file1.py" not in files_at_root, "Test file should be excluded"
    with open(os.path.join(pattern_test_directory, "unique_test_pattern.py"), "w") as f:
        f.write("# Unique test file")
    include_patterns = [re.compile(r"unique_test_pattern\.py$")]
    structure, _ = get_directory_structure(
        pattern_test_directory, include_patterns=include_patterns
    )
    if "_files" in structure:
        files = [f if isinstance(f, str) else f[0] for f in structure["_files"]]
        assert "unique_test_pattern.py" in files, "Unique test file should be included"


def test_pathlib_compatibility(pattern_test_directory):
    """Test compatibility with pathlib.Path objects for regex filtering."""
    path_obj = Path(pattern_test_directory)
    include_patterns = [re.compile(r"\.py$")]
    structure, extensions = get_directory_structure(
        path_obj, include_patterns=include_patterns
    )
    assert ".py" in extensions
    if "_files" in structure:
        for file_item in structure["_files"]:
            file_name = file_item if isinstance(file_item, str) else file_item[0]
            assert file_name.endswith(
                ".py"
            ), f"Non-Python file {file_name} was included"
