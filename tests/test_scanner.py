"""Tests for recursivist.scanner.get_directory_structure.

Covers traversal, depth limits, filtering integration, and pathlib support.
"""

import logging
import os
import re
from pathlib import Path
from typing import Any, cast

import pytest
from pytest_mock import MockerFixture

from recursivist._models import FileEntry
from recursivist.scanner import (
    get_directory_structure,
    get_subdirectory,
    has_contents,
    iter_subdirectories,
    subdirectory_key,
)


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
            normalized["_files"] = {item.name for item in value}
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
    file_names = [f.name for f in structure["_files"]]
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


def test_get_directory_structure_nested_gitignore_anchoring(temp_dir: str) -> None:
    """A nested .gitignore is evaluated relative to its own directory, matching
    Git rather than accumulating every pattern against the scan root.

    Root .gitignore is ``*.log``; ``sub/.gitignore`` is ``/build`` + ``data`` +
    ``!important.log``. Verified against ``git check-ignore``:

    - ``sub/build/`` is pruned by the *anchored* ``/build`` (relative to ``sub``)
      while the root-level ``build/`` and ``sub/nested/build/`` survive, because
      the anchor neither leaks up to the scan root nor reaches past ``sub``.
    - ``data`` (unanchored) prunes ``data`` at any depth under ``sub``
      (``sub/data`` and ``sub/nested/data``) but nowhere above ``sub``.
    - ``!important.log`` in the nested file overrides the root ``*.log`` for
      ``sub/important.log`` only; ``app.log`` and ``sub/app.log`` stay excluded.
    """
    root = os.path.join(temp_dir, "project")
    os.makedirs(root, exist_ok=True)
    _materialize_tree(
        root,
        {
            ".gitignore": "*.log\n",
            "main.py": "x",
            "app.log": "x",
            "build/keep.py": "x",
            "sub/.gitignore": "/build\ndata\n!important.log\n",
            "sub/app.log": "x",
            "sub/important.log": "x",
            "sub/build/x.py": "x",
            "sub/data/y.py": "x",
            "sub/nested/build/z.py": "x",
            "sub/nested/data/w.py": "x",
        },
    )

    structure, extensions = get_directory_structure(root, ignore_file=".gitignore")

    assert _normalize_structure(structure) == {
        "_files": {".gitignore", "main.py"},
        "build": {"_files": {"keep.py"}},
        "sub": {
            "_files": {".gitignore", "important.log"},
            "nested": {"build": {"_files": {"z.py"}}},
        },
    }

    assert extensions == {".log", ".py"}


@pytest.mark.parametrize(
    "option_name,option_value,expected_result",
    [
        ("show_full_path", True, "entry with full path"),
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
    if expected_result == "entry with full path":
        assert "_files" in structure
        for file_item in structure["_files"]:
            assert isinstance(file_item, FileEntry)
            assert os.path.isabs(file_item.path.replace("/", os.sep))
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
        file_name = file_item.name
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
        assert "file1.txt" in [f.name for f in root_files], (
            "file1.txt should be in root files"
        )
        assert "file2.py" in [f.name for f in root_files], (
            "file2.py should be in root files"
        )
        subdir_files = structure["subdir"]["_files"]
        assert "subfile.md" in [f.name for f in subdir_files], (
            "subfile.md should be in subdir files"
        )
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
            file_name = file.name
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
                            file_name = file.name
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
                file_name = file.name
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
                            file_name = file.name
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
        file_names = [f.name for f in structure["_files"]]
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
                assert isinstance(file_item, FileEntry)
                assert isinstance(file_item.loc, int)
                assert isinstance(file_item.size, int)
                assert isinstance(file_item.mtime, float)
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
                file_names.append(file_item.name)
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
            file_name = file_item.name
            assert file_name.endswith(".py"), (
                f"Non-Python file {file_name} was included"
            )


def _supports_symlinks(base: str) -> bool:
    """Return True if directory symlinks can be created under *base*."""
    src = os.path.join(base, "__symlink_probe_target__")
    link = os.path.join(base, "__symlink_probe_link__")
    try:
        os.makedirs(src, exist_ok=True)
        os.symlink(src, link)
    except (OSError, NotImplementedError, AttributeError):
        return False
    finally:
        for p in (link, src):
            try:
                (os.remove if os.path.islink(p) else os.rmdir)(p)
            except OSError:
                pass
    return True


class TestSymlinkCycles:
    """Cyclic symlinks must be cut, not walked until the OS ELOOP limit."""

    def test_symlink_to_ancestor_is_cut(self, temp_dir: str) -> None:
        """A symlink pointing back to an ancestor is marked, not recursed."""
        if not _supports_symlinks(temp_dir):
            pytest.skip("platform does not support directory symlinks")
        os.makedirs(os.path.join(temp_dir, "a", "b"))
        with open(os.path.join(temp_dir, "a", "file.txt"), "w") as f:
            f.write("hi\n")
        os.symlink(
            os.path.join(temp_dir, "a"), os.path.join(temp_dir, "a", "b", "loop")
        )

        structure, _ = get_directory_structure(temp_dir)

        loop = structure["a"]["b"]["loop"]
        assert loop == {"_symlink_loop": True}
        assert "a" not in loop

    def test_self_referential_symlink_is_cut(self, temp_dir: str) -> None:
        """A directory containing a symlink to itself is marked, not recursed."""
        if not _supports_symlinks(temp_dir):
            pytest.skip("platform does not support directory symlinks")
        os.makedirs(os.path.join(temp_dir, "c"))
        os.symlink(os.path.join(temp_dir, "c"), os.path.join(temp_dir, "c", "self"))

        structure, _ = get_directory_structure(temp_dir)

        assert structure["c"]["self"] == {"_symlink_loop": True}

    def test_non_cyclic_symlink_is_still_followed(self, temp_dir: str) -> None:
        """A symlink to a non-ancestor directory is traversed like any directory."""
        if not _supports_symlinks(temp_dir):
            pytest.skip("platform does not support directory symlinks")
        os.makedirs(os.path.join(temp_dir, "target"))
        with open(os.path.join(temp_dir, "target", "keep.txt"), "w") as f:
            f.write("x\n")
        os.makedirs(os.path.join(temp_dir, "src"))
        os.symlink(
            os.path.join(temp_dir, "target"), os.path.join(temp_dir, "src", "alias")
        )

        structure, _ = get_directory_structure(temp_dir)

        alias = structure["src"]["alias"]
        assert "_symlink_loop" not in alias
        names = {f.name for f in alias["_files"]}
        assert "keep.txt" in names

    def test_cycle_does_not_explode_depth(self, temp_dir: str) -> None:
        """The scanned tree stops at the symlink that closes the cycle."""
        if not _supports_symlinks(temp_dir):
            pytest.skip("platform does not support directory symlinks")
        os.makedirs(os.path.join(temp_dir, "a", "b"))
        os.symlink(
            os.path.join(temp_dir, "a"), os.path.join(temp_dir, "a", "b", "loop")
        )

        structure, _ = get_directory_structure(temp_dir)

        def max_depth(node: Any, d: int = 0) -> int:
            if not isinstance(node, dict):
                return d
            children = [v for k, v in node.items() if not k.startswith("_")]
            return max((max_depth(v, d + 1) for v in children), default=d)

        assert max_depth(structure) == 3


def test_exclude_extensions_applies_to_dangling_symlinks(temp_dir: str) -> None:
    """--exclude-ext hides any non-directory entry, not only regular files.

    A dangling symlink is neither a file nor a directory to ``os.path``, so the
    extension rule must not depend on ``os.path.isfile``.
    """
    if not _supports_symlinks(temp_dir):
        pytest.skip("platform does not support symlinks")
    os.symlink(
        os.path.join(temp_dir, "missing.log"), os.path.join(temp_dir, "dangling.log")
    )
    with open(os.path.join(temp_dir, "keep.txt"), "w") as f:
        f.write("x\n")

    structure, extensions = get_directory_structure(
        temp_dir, exclude_extensions={".log"}
    )

    names = {f.name for f in structure["_files"]}
    assert names == {"keep.txt"}
    assert extensions == {".txt"}


class TestHiddenContentsAtDepthLimit:
    """The ``_hidden_contents`` flag and the :func:`has_contents` predicate."""

    def test_flag_set_only_when_something_was_cut_off(self, temp_dir: str) -> None:
        """A truncated directory records whether it still held anything."""
        _materialize_tree(temp_dir, {"full/deep/file.txt": "x"})
        os.makedirs(os.path.join(temp_dir, "bare", "empty"), exist_ok=True)

        structure, _ = get_directory_structure(temp_dir, max_depth=2)

        assert structure["full"]["deep"] == {
            "_max_depth_reached": True,
            "_hidden_contents": True,
        }
        assert structure["bare"]["empty"] == {"_max_depth_reached": True}

    def test_excluded_children_do_not_count_as_contents(self, temp_dir: str) -> None:
        """A directory holding only excluded files is truncated as empty."""
        _materialize_tree(temp_dir, {"outer/inner/skipped.log": "x"})

        structure, _ = get_directory_structure(
            temp_dir, max_depth=2, exclude_extensions={".log"}
        )

        assert structure["outer"]["inner"] == {"_max_depth_reached": True}

    @pytest.mark.parametrize(
        "error", [PermissionError("Permission denied"), OSError("boom")]
    )
    def test_unreadable_directory_is_treated_as_empty(
        self, temp_dir: str, mocker: MockerFixture, error: Exception
    ) -> None:
        """A directory we cannot list is truncated as empty rather than raising."""
        os.makedirs(os.path.join(temp_dir, "outer", "locked"), exist_ok=True)
        real_listdir = os.listdir

        def fake_listdir(path: str) -> list[str]:
            if os.path.basename(path) == "locked":
                raise error
            return real_listdir(path)

        mocker.patch("recursivist.scanner.os.listdir", side_effect=fake_listdir)
        structure, _ = get_directory_structure(temp_dir, max_depth=2)

        assert structure["outer"]["locked"] == {"_max_depth_reached": True}

    @pytest.mark.parametrize(
        "structure,expected",
        [
            ({}, False),
            ({"_files": []}, False),
            ({"_loc": 0, "_size": 0}, False),
            ({"_files": [FileEntry("a.txt", "a.txt")]}, True),
            ({"subdir": {}}, True),
            ({"_max_depth_reached": True}, False),
            ({"_max_depth_reached": True, "_hidden_contents": True}, True),
            ({"_symlink_loop": True}, True),
            ("not-a-dict", False),
        ],
    )
    def test_has_contents(self, structure: Any, expected: bool) -> None:
        """Only entries with something to show are reported as non-empty."""
        assert has_contents(structure) is expected


class TestUnmatchedFilterReporting:
    """Filters that match no scanned entry are reported as warnings."""

    @pytest.fixture
    def tree(self, temp_dir: str) -> str:
        _materialize_tree(
            temp_dir,
            {
                "app.py": "print(1)\n",
                "notes.txt": "hi\n",
                "build/out.o": "",
                "src/deep/module.py": "x = 1\n",
            },
        )
        return temp_dir

    @staticmethod
    def _messages(caplog: pytest.LogCaptureFixture) -> list[str]:
        return [
            r.getMessage()
            for r in caplog.records
            if r.name == "recursivist.filtering" and r.levelno == logging.WARNING
        ]

    def test_reports_each_unmatched_filter(
        self, tree: str, caplog: pytest.LogCaptureFixture
    ) -> None:
        caplog.set_level(logging.INFO, logger="recursivist")
        get_directory_structure(
            tree,
            exclude_dirs=["build", "node_modules"],
            exclude_extensions={".txt", ".xyz"},
            exclude_patterns=["*.py", "*.test.js"],
            include_patterns=["*.nope"],
        )
        assert self._messages(caplog) == [
            "No files or directories matched --exclude 'node_modules'",
            "No files or directories matched --exclude-ext '.xyz'",
            "No files or directories matched --exclude-pattern '*.test.js'",
            "No files or directories matched --include-pattern '*.nope'",
        ]

    def test_silent_when_every_filter_matches(
        self, tree: str, caplog: pytest.LogCaptureFixture
    ) -> None:
        caplog.set_level(logging.INFO, logger="recursivist")
        get_directory_structure(
            tree,
            exclude_dirs=["build"],
            exclude_extensions={".txt"},
            exclude_patterns=[re.compile(r"^module\.py$")],
        )
        assert self._messages(caplog) == []

    def test_filter_counts_even_if_an_earlier_rule_removed_the_entry(
        self, tree: str, caplog: pytest.LogCaptureFixture
    ) -> None:
        caplog.set_level(logging.INFO, logger="recursivist")
        get_directory_structure(tree, exclude_dirs=["build"], exclude_patterns=["bui*"])
        assert self._messages(caplog) == []

    def test_regex_pattern_reported_by_its_source(
        self, tree: str, caplog: pytest.LogCaptureFixture
    ) -> None:
        caplog.set_level(logging.INFO, logger="recursivist")
        get_directory_structure(tree, exclude_patterns=[re.compile(r"\.rs$")])
        assert self._messages(caplog) == [
            r"No files or directories matched --exclude-pattern '\.rs$'"
        ]

    def test_depth_limit_is_mentioned(
        self, tree: str, caplog: pytest.LogCaptureFixture
    ) -> None:
        caplog.set_level(logging.INFO, logger="recursivist")
        get_directory_structure(tree, exclude_patterns=["module.py"], max_depth=1)
        assert self._messages(caplog) == [
            "No files or directories matched --exclude-pattern 'module.py' "
            "within the scanned depth"
        ]

    def test_reported_once_per_scan(
        self, tree: str, caplog: pytest.LogCaptureFixture
    ) -> None:
        caplog.set_level(logging.INFO, logger="recursivist")
        get_directory_structure(tree, exclude_extensions={".xyz"})
        assert len(self._messages(caplog)) == 1


class TestReservedNameDirectories:
    """Directories whose names clash with the structure's bookkeeping keys."""

    @pytest.fixture
    def tree(self, temp_dir: str) -> str:
        for rel in ("_files/inner.txt", "_loc/deep.py", "top.txt"):
            path = os.path.join(temp_dir, rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write("x\n")
        return temp_dir

    def test_reserved_name_does_not_clobber_bookkeeping(self, tree: str) -> None:
        structure, _ = get_directory_structure(tree, sort_by_loc=True)
        assert [entry.name for entry in structure["_files"]] == ["top.txt"]
        assert structure["_loc"] == 3
        subdirs = dict(iter_subdirectories(structure))
        assert sorted(subdirs) == ["_files", "_loc"]
        assert [e.name for e in subdirs["_files"]["_files"]] == ["inner.txt"]
        assert get_subdirectory(structure, "_loc") is subdirs["_loc"]

    def test_subdirectory_key_round_trips(self) -> None:
        assert subdirectory_key("src") == "src"
        assert subdirectory_key("_private") == "_private"
        structure: dict[str, Any] = {subdirectory_key("_files"): {}, "_files": []}
        assert [name for name, _ in iter_subdirectories(structure)] == ["_files"]
        assert get_subdirectory(structure, "_files") == {}
        assert get_subdirectory(structure, "missing") is None


def test_include_patterns_keep_directories_with_underscore_children(
    temp_dir: str,
) -> None:
    nested = os.path.join(temp_dir, "pkg", "_internal")
    os.makedirs(nested)
    with open(os.path.join(nested, "module.py"), "w") as f:
        f.write("x = 1\n")
    structure, _ = get_directory_structure(temp_dir, include_patterns=["*.py"])
    internal = structure["pkg"]["_internal"]
    assert [entry.name for entry in internal["_files"]] == ["module.py"]
