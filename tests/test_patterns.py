import os
import re
from pathlib import Path
from typing import Any

import pytest
from pytest_mock import MockerFixture
from typer.testing import CliRunner

from recursivist.cli import app
from recursivist.core import (
    compile_regex_patterns,
    get_directory_structure,
    should_exclude,
)


class TestCompileRegexPatterns:
    @pytest.mark.parametrize(
        "patterns,is_regex,expected_types",
        [
            (["*.py", "test_*"], False, [str, str]),
            ([r"\.py$", r"^test_"], True, [re.Pattern, re.Pattern]),
            ([r"[invalid", r"(unclosed"], True, [str, str]),
        ],
    )
    def test_basic_compilation(
        self, patterns: list[str], is_regex: bool, expected_types: list[type]
    ) -> None:
        """Test basic pattern compilation."""
        compiled = compile_regex_patterns(patterns, is_regex=is_regex)
        assert len(compiled) == len(patterns)
        for i, pattern_type in enumerate(expected_types):
            assert isinstance(compiled[i], pattern_type)

    def test_empty_patterns(self) -> None:
        """Test compiling empty pattern lists."""
        assert compile_regex_patterns([], is_regex=False) == []
        assert compile_regex_patterns([], is_regex=True) == []

    def test_regex_matching(self) -> None:
        """Test compiled regex patterns match correctly."""
        patterns = [r"^data_\d{8}\.csv$", r".*\.(?:log|tmp)$", r"^\..*"]
        compiled = [re.compile(p) for p in patterns]
        assert len(compiled) == 3
        assert all(isinstance(p, re.Pattern) for p in compiled)
        assert compiled[0].match("data_20230101.csv")
        assert not compiled[0].match("data_20230101.txt")
        assert compiled[1].match("app.log")
        assert compiled[1].match("temp.tmp")
        assert not compiled[1].match("app.txt")
        assert compiled[2].match(".hidden")
        assert not compiled[2].match("visible")


class TestShouldExclude:
    @pytest.mark.parametrize(
        "path,patterns,expected",
        [
            ("/test/app.log", ["*.log", "node_modules"], True),
            ("/test/app.txt", ["*.log", "node_modules"], False),
            ("/test/node_modules", ["*.log", "node_modules"], True),
            ("/test/src", ["*.log", "node_modules"], False),
        ],
    )
    def test_with_ignore_patterns(
        self, mocker: MockerFixture, path: str, patterns: list[str], expected: bool
    ) -> None:
        """Test exclusion based on ignore patterns."""
        mocker.patch("os.path.isfile", return_value=True)
        ignore_context = {"patterns": patterns, "current_dir": "/test"}
        result = should_exclude(path, ignore_context)
        assert result == expected

    @pytest.mark.parametrize(
        "path,extensions,expected",
        [
            ("/test/script.py", {".py", ".js"}, True),
            ("/test/app.js", {".py", ".js"}, True),
            ("/test/app.txt", {".py", ".js"}, False),
        ],
    )
    def test_with_file_extensions(
        self, mocker: MockerFixture, path: str, extensions: set[str], expected: bool
    ) -> None:
        """Test exclusion based on file extensions."""
        mocker.patch("os.path.isfile", return_value=True)
        ignore_context = {"patterns": [], "current_dir": "/test"}
        result = should_exclude(path, ignore_context, exclude_extensions=extensions)
        assert result == expected

    @pytest.mark.parametrize(
        "path,pattern,expected",
        [
            ("/test/test_app.py", r"test_.*\.py$", True),
            ("/test/app.log", r"\.log$", True),
            ("/test/app.py", r"test_.*\.py$", False),
        ],
    )
    def test_with_regex_patterns(
        self, mocker: MockerFixture, path: str, pattern: str, expected: bool
    ) -> None:
        """Test exclusion based on regex patterns."""
        mocker.patch("os.path.isfile", return_value=True)
        ignore_context = {"patterns": [], "current_dir": "/test"}
        exclude_patterns = [re.compile(pattern)]
        result = should_exclude(path, ignore_context, exclude_patterns=exclude_patterns)
        assert result == expected

    def test_with_negation_patterns(self, mocker: MockerFixture) -> None:
        """Test negation patterns in ignore files."""
        mocker.patch("os.path.isfile", return_value=True)
        ignore_context = {
            "patterns": ["*.txt", "!important.txt"],
            "current_dir": "/test",
        }
        assert should_exclude("/test/file.txt", ignore_context)
        assert not should_exclude("/test/important.txt", ignore_context)
        assert not should_exclude("/test/file.py", ignore_context)

    def test_with_include_patterns(self, mocker: MockerFixture) -> None:
        """Test include patterns override exclusion."""
        mocker.patch("os.path.isfile", return_value=True)
        ignore_context = {"patterns": ["*.py"], "current_dir": "/test"}
        exclude_patterns = [re.compile(r"\.js$")]
        include_patterns = [re.compile(r"important\.py$")]
        assert should_exclude(
            "/test/app.py",
            ignore_context,
            exclude_patterns=exclude_patterns,
            include_patterns=include_patterns,
        )
        assert not should_exclude(
            "/test/important.py",
            ignore_context,
            exclude_patterns=exclude_patterns,
            include_patterns=include_patterns,
        )
        assert should_exclude(
            "/test/app.js",
            ignore_context,
            exclude_patterns=exclude_patterns,
            include_patterns=include_patterns,
        )
        assert should_exclude(
            "/test/app.txt",
            ignore_context,
            exclude_patterns=exclude_patterns,
            include_patterns=include_patterns,
        )

    @pytest.mark.parametrize(
        "path,pattern,expected",
        [
            ("/test/path/to/file.txt", "file.txt", True),
            ("/test/path/to/other.txt", "file.txt", False),
        ],
    )
    def test_basename_matching(
        self, mocker: MockerFixture, path: str, pattern: str, expected: bool
    ) -> None:
        """Test matching against the basename only."""
        mocker.patch("os.path.isfile", return_value=True)
        ignore_context = {"patterns": [], "current_dir": "/test"}
        exclude_patterns = [re.compile(pattern + "$")]
        result = should_exclude(path, ignore_context, exclude_patterns=exclude_patterns)
        assert result == expected

    def test_case_sensitivity(self, mocker: MockerFixture) -> None:
        """Test case sensitivity in pattern matching."""
        mocker.patch("os.path.isfile", return_value=True)
        ignore_context = {"patterns": [], "current_dir": "/test"}
        exclude_patterns = [re.compile(r"\.py$")]
        assert should_exclude(
            "/test/script.py", ignore_context, exclude_patterns=exclude_patterns
        )
        assert not should_exclude(
            "/test/script.PY", ignore_context, exclude_patterns=exclude_patterns
        )
        exclude_patterns = [re.compile(r"\.py$", re.IGNORECASE)]
        assert should_exclude(
            "/test/script.py", ignore_context, exclude_patterns=exclude_patterns
        )
        assert should_exclude(
            "/test/script.PY", ignore_context, exclude_patterns=exclude_patterns
        )
        exclude_extensions = {".py"}
        assert should_exclude(
            "/test/script.py", ignore_context, exclude_extensions=exclude_extensions
        )
        assert should_exclude(
            "/test/script.PY", ignore_context, exclude_extensions=exclude_extensions
        )


class TestPatternMatching:
    def test_get_directory_structure_with_regex_patterns(
        self, pattern_test_directory: str
    ) -> None:
        """Test filtering directory structure with regex patterns."""
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
        assert ".py" not in extensions, (
            "Python extension was included despite exclude pattern"
        )

        def check_subdirs_for_py_files(structure: dict[str, Any]) -> None:
            for key, value in structure.items():
                if key != "_files" and isinstance(value, dict):
                    if "_files" in value:
                        for file in value["_files"]:
                            file_name = file if isinstance(file, str) else file[0]
                            assert not file_name.endswith(".py"), (
                                f"Python file {file_name} found despite exclude pattern"
                            )
                    check_subdirs_for_py_files(value)

        check_subdirs_for_py_files(structure)

    def test_get_directory_structure_with_include_patterns(
        self, pattern_test_directory: str
    ) -> None:
        """Test including only specific patterns."""
        include_patterns = [re.compile(r"\.json$")]
        structure, extensions = get_directory_structure(
            pattern_test_directory, include_patterns=include_patterns
        )
        if "_files" in structure:
            for file in structure["_files"]:
                file_name = file if isinstance(file, str) else file[0]
                assert file_name.endswith(".json"), (
                    f"Non-JSON file {file_name} was included"
                )
        assert ".json" in extensions
        assert len(extensions) == 1, "Only JSON extension should be included"

        def check_subdirs_for_non_json(structure: dict[str, Any]) -> None:
            for key, value in structure.items():
                if key != "_files" and isinstance(value, dict):
                    if "_files" in value:
                        for file in value["_files"]:
                            file_name = file if isinstance(file, str) else file[0]
                            assert file_name.endswith(".json"), (
                                f"Non-JSON file {file_name} was included"
                            )
                    check_subdirs_for_non_json(value)

        check_subdirs_for_non_json(structure)

    def test_get_directory_structure_complex_regex(
        self, pattern_test_directory: str
    ) -> None:
        """Test complex regex pattern matching."""
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

    def test_regex_with_statistics(self, pattern_test_directory: str) -> None:
        """Test regex filtering combined with statistics gathering."""
        include_patterns = [re.compile(r"\.py$")]
        structure, _ = get_directory_structure(
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

    def test_both_include_and_exclude_patterns(
        self, pattern_test_directory: str
    ) -> None:
        """Test using both include and exclude patterns together."""
        with open(os.path.join(pattern_test_directory, "include_me.py"), "w") as f:
            f.write("This should be included")
        with open(os.path.join(pattern_test_directory, "exclude_me.py"), "w") as f:
            f.write("This should be excluded")
        include_patterns = [re.compile(r"\.py$")]
        exclude_patterns = [re.compile(r"^exclude_.*\.py$")]
        structure, _ = get_directory_structure(
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
        assert "exclude_me.py" not in file_names
        assert "regular_file.txt" not in file_names
        assert "config.json" not in file_names


def test_cli_with_regex_patterns(
    runner: CliRunner, pattern_test_directory: str
) -> None:
    """Test CLI with regex pattern options."""
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


def test_glob_patterns(pattern_test_directory: str) -> None:
    """Test glob-style pattern matching."""
    exclude_patterns = ["test_*", "*.log"]
    structure, _ = get_directory_structure(
        pattern_test_directory, exclude_patterns=exclude_patterns
    )
    test_files_found = False
    log_files_found = False

    def check_files(struct: dict[str, Any]) -> None:
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


def test_mixed_regex_and_glob_patterns(
    runner: CliRunner, pattern_test_directory: str
) -> None:
    """Test mixing regex and glob patterns."""
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


def test_regex_pattern_escaping(pattern_test_directory: str) -> None:
    """Test regex patterns with special characters that need escaping."""
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


def test_regex_nested_directory_patterns(pattern_test_directory: str) -> None:
    """Test regular expressions for files in nested directories."""
    structure, _ = get_directory_structure(pattern_test_directory)
    assert "tests" in structure, "Base structure doesn't have tests directory"
    assert "unit" in structure["tests"], "Base structure doesn't have unit directory"
    assert "integration" in structure["tests"], (
        "Base structure doesn't have integration directory"
    )
    include_patterns = [re.compile(r"test_.*\.py$")]
    structure, _ = get_directory_structure(
        pattern_test_directory, include_patterns=include_patterns
    )
    files_at_root = [
        f if isinstance(f, str) else f[0] for f in structure.get("_files", [])
    ]
    assert "test_file1.py" in files_at_root, "Root test_file1.py should be included"
    assert "regular_file.txt" not in files_at_root, (
        "Non-matching files should be excluded"
    )
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


def test_pathlib_compatibility(pattern_test_directory: str) -> None:
    """Test compatibility with pathlib.Path objects."""
    path_obj = Path(pattern_test_directory)
    include_patterns = [re.compile(r"\.py$")]
    structure, extensions = get_directory_structure(
        str(path_obj), include_patterns=include_patterns
    )
    assert ".py" in extensions
    if "_files" in structure:
        for file_item in structure["_files"]:
            file_name = file_item if isinstance(file_item, str) else file_item[0]
            assert file_name.endswith(".py"), (
                f"Non-Python file {file_name} was included"
            )
