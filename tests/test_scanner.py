"""Tests for recursivist.scanner.get_directory_structure: traversal, depth limits, filtering integration, pathlib."""

import os
import re
from pathlib import Path
from typing import Any, cast

import pytest

from recursivist.scanner import get_directory_structure


def _materialize_tree(root: str, files: dict[str, str]) -> None:
    """Create each file (keyed by '/'-separated relative path) under *root*,
    making intermediate directories as needed."""
    for rel, content in files.items():
        path = os.path.join(root, *rel.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(content)


def _normalize_structure(structure: dict[str, Any]) -> dict[str, Any]:
    """Make a get_directory_structure result comparable: '_files' lists become
    sets of names (order from os.listdir isn't stable), and subdirectories are
    normalized recursively."""
    normalized: dict[str, Any] = {}
    for key, value in structure.items():
        if key == "_files":
            normalized["_files"] = {
                item[0] if isinstance(item, tuple) else item for item in value
            }
        elif isinstance(value, dict):
            normalized[key] = _normalize_structure(value)
        else:
            normalized[key] = value
    return normalized


def test_get_directory_structure(sample_directory: Any) -> None:
    """Test getting directory structure."""
    structure, extensions = get_directory_structure(sample_directory)
    assert isinstance(structure, dict)
    assert "_files" in structure
    assert "subdir" in structure
    file_names = [f if isinstance(f, str) else f[0] for f in structure["_files"]]
    assert "file1.txt" in file_names
    assert "file2.py" in file_names
    assert ".txt" in extensions
    assert ".py" in extensions
    assert ".md" in extensions
    assert ".json" in extensions


def test_get_directory_structure_gitignore_end_to_end(temp_dir: str) -> None:
    """End-to-end: get_directory_structure reads a real .gitignore and applies
    anchoring, depth-aware negation, and directory pruning to the final tree.

    .gitignore is:  *.log  /  !keep.log  /  /build
      - '*.log' floats: excludes app.log (root) and src/debug.log (depth)
      - '!keep.log' re-includes keep.log at both root and depth (last match wins)
      - '/build' is anchored: the root build/ is pruned wholesale, but src/build/
        survives because the pattern only anchors at the scan root
    """
    root = os.path.join(temp_dir, "project")
    os.makedirs(root, exist_ok=True)
    _materialize_tree(
        root,
        {
            ".gitignore": "*.log\n!keep.log\n/build\n",
            "app.log": "x",
            "keep.log": "x",
            "main.py": "x",
            "build/output.txt": "x",
            "src/debug.log": "x",
            "src/keep.log": "x",
            "src/helper.py": "x",
            "src/build/nested.py": "x",
        },
    )

    structure, extensions = get_directory_structure(root, ignore_file=".gitignore")

    assert _normalize_structure(structure) == {
        "_files": {".gitignore", "keep.log", "main.py"},
        "src": {
            "_files": {"helper.py", "keep.log"},
            "build": {"_files": {"nested.py"}},
        },
    }

    assert extensions == {".log", ".py"}


@pytest.mark.parametrize(
    "option_name,option_value,expected_result",
    [
        ("show_full_path", True, "tuple with path"),
        ("max_depth", 1, "max_depth_reached in level1"),
        ("sort_by_loc", True, "_loc in structure"),
        ("sort_by_size", True, "_size in structure"),
        ("sort_by_mtime", True, "_mtime in structure"),
    ],
)
def test_get_directory_structure_with_options(
    deeply_nested_directory: Any,
    option_name: str,
    option_value: Any,
    expected_result: str,
) -> None:
    """Test getting directory structure with various options."""
    kwargs = {option_name: option_value}
    structure, _ = get_directory_structure(deeply_nested_directory, **kwargs)
    if expected_result == "tuple with path":
        assert "_files" in structure
        for file_item in structure["_files"]:
            assert isinstance(file_item, tuple)
            assert len(file_item) >= 2
            full_path = file_item[1]
            assert os.path.isabs(full_path.replace("/", os.sep))
    elif expected_result == "max_depth_reached in level1":
        assert "level1" in structure
        assert "_max_depth_reached" in structure["level1"]
    elif expected_result == "_loc in structure":
        assert "_loc" in structure
        if "level1" in structure:
            assert "_loc" in structure["level1"]
    elif expected_result == "_size in structure":
        assert "_size" in structure
        if "level1" in structure:
            assert "_size" in structure["level1"]
    elif expected_result == "_mtime in structure":
        assert "_mtime" in structure
        if "level1" in structure:
            assert "_mtime" in structure["level1"]


def test_pathlib_compatibility(temp_dir: str) -> None:
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


class TestGetDirectoryStructure:
    """Property-based tests for get_directory_structure function."""

    def test_structure_properties(self, temp_dir: str) -> None:
        """Test properties of the directory structure."""
        file1 = os.path.join(temp_dir, "file1.txt")
        file2 = os.path.join(temp_dir, "file2.py")
        subdir = os.path.join(temp_dir, "subdir")
        os.makedirs(subdir, exist_ok=True)
        subfile = os.path.join(subdir, "subfile.md")
        with open(file1, "w") as f:
            f.write("File 1 content")
        with open(file2, "w") as f:
            f.write("File 2 content")
        with open(subfile, "w") as f:
            f.write("Subfile content")
        structure, extensions = get_directory_structure(temp_dir)
        assert "_files" in structure, "Root structure should have _files key"
        assert "subdir" in structure, "Root structure should have subdir directory"
        assert "_files" in structure["subdir"], (
            "Subdir structure should have _files key"
        )
        root_files = structure["_files"]
        assert "file1.txt" in [f if isinstance(f, str) else f[0] for f in root_files], (
            "file1.txt should be in root files"
        )
        assert "file2.py" in [f if isinstance(f, str) else f[0] for f in root_files], (
            "file2.py should be in root files"
        )
        subdir_files = structure["subdir"]["_files"]
        assert "subfile.md" in [
            f if isinstance(f, str) else f[0] for f in subdir_files
        ], "subfile.md should be in subdir files"
        assert ".txt" in extensions, ".txt should be in extensions"
        assert ".py" in extensions, ".py should be in extensions"
        assert ".md" in extensions, ".md should be in extensions"


def test_get_directory_structure_with_no_depth_limit(
    deeply_nested_directory: str,
) -> None:
    """Test that structure is built without depth limits when max_depth=0."""
    structure, _ = get_directory_structure(deeply_nested_directory, max_depth=0)
    assert "level1" in structure
    assert "level1_dir1" in structure["level1"]
    assert "level2" in structure["level1"]
    assert "level3" in structure["level1"]["level2"]
    assert "level4" in structure["level1"]["level2"]["level3"]
    assert "level5" in structure["level1"]["level2"]["level3"]["level4"]
    assert "level6" in structure["level1"]["level2"]["level3"]["level4"]["level5"]
    assert "_max_depth_reached" not in structure
    assert "_max_depth_reached" not in structure["level1"]
    assert "_max_depth_reached" not in structure["level1"]["level2"]

    def check_no_max_depth_flags(structure: dict[str, Any]) -> None:
        assert "_max_depth_reached" not in structure
        for key, value in structure.items():
            if key != "_files" and isinstance(value, dict):
                check_no_max_depth_flags(cast(dict[str, Any], value))

    check_no_max_depth_flags(structure)


@pytest.mark.parametrize(
    "depth,max_depth_in_level",
    [
        (1, ["level1"]),
        (2, ["level1/level2", "level1/level1_dir1"]),
        (3, ["level1/level2/level3"]),
    ],
)
def test_get_directory_structure_with_depth_limits(
    deeply_nested_directory: str, depth: int, max_depth_in_level: list[str]
) -> None:
    """Test that structure is limited to specified depth."""
    structure, _ = get_directory_structure(deeply_nested_directory, max_depth=depth)

    def check_path_has_max_depth(path_segments: list[str]) -> bool:
        current: dict[str, Any] = structure
        for segment in path_segments:
            if segment in current:
                current = current[segment]
            else:
                return False
        return "_max_depth_reached" in current

    for path in max_depth_in_level:
        segments: list[str] = path.split("/")
        assert check_path_has_max_depth(segments), (
            f"No max_depth_reached flag in {path}"
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


def test_get_directory_structure_pathlib(pattern_test_directory: str) -> None:
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
