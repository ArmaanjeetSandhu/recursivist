"""Tests for recursivist.tree: build_tree and display_tree.

Both take a resolved :class:`~recursivist.flags.DisplayOptions` (``spec``) that
carries the sort key and metric annotations. ``spec`` is a required positional
argument to ``build_tree`` and an optional keyword to ``display_tree``
(defaulting to a plain ``DisplayOptions``).
"""

import os
import re
import time
from typing import Any
from unittest.mock import MagicMock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pytest_mock import MockerFixture
from rich.text import Text
from rich.tree import Tree

from recursivist.flags import (
    METRIC_LOC,
    METRIC_MTIME,
    METRIC_SIZE,
    DisplayOptions,
)
from recursivist.tree import build_tree, display_tree
from tests.strategies import simple_directory_structure

ALL_METRICS_SPEC = DisplayOptions(
    sort_key=METRIC_LOC, metrics=(METRIC_LOC, METRIC_SIZE, METRIC_MTIME)
)


def _text_calls(mock_tree: MagicMock) -> list[Text]:
    """Return the Text objects added to *mock_tree* (the file/leaf nodes)."""
    return [
        call.args[0]
        for call in mock_tree.add.call_args_list
        if isinstance(call.args[0], Text)
    ]


def _text_plains(mock_tree: MagicMock) -> list[str]:
    return [t.plain for t in _text_calls(mock_tree)]


class TestBuildTree:
    def test_basic_tree(
        self,
        mocker: MockerFixture,
        simple_structure: dict[str, Any],
        color_map: dict[str, str],
    ) -> None:
        mock_tree = MagicMock(spec=Tree)
        mock_subtree = MagicMock(spec=Tree)
        mock_tree.add.return_value = mock_subtree
        build_tree(simple_structure, mock_tree, color_map, DisplayOptions())
        assert mock_tree.add.call_count >= 3
        file_texts = _text_plains(mock_tree)
        assert any("file1.txt" in text for text in file_texts)
        assert any("file2.py" in text for text in file_texts)

    def test_empty_structure(self, mocker: MockerFixture) -> None:
        mock_tree = MagicMock(spec=Tree)
        color_map: dict[str, str] = {}
        structure: dict[str, Any] = {}
        build_tree(structure, mock_tree, color_map, DisplayOptions())
        mock_tree.add.assert_not_called()

    def test_with_full_paths(
        self, mocker: MockerFixture, color_map: dict[str, str]
    ) -> None:
        mock_tree = MagicMock(spec=Tree)
        mock_subtree = MagicMock(spec=Tree)
        mock_tree.add.return_value = mock_subtree
        structure = {
            "_files": [
                ("file1.txt", "/path/to/file1.txt"),
                ("file2.py", "/path/to/file2.py"),
            ],
            "subdir": {"_files": [("subfile.py", "/path/to/subdir/subfile.py")]},
        }
        build_tree(
            structure, mock_tree, color_map, DisplayOptions(), show_full_path=True
        )
        file_texts = _text_plains(mock_tree)
        assert any("/path/to/file1.txt" in text for text in file_texts)
        assert any("/path/to/file2.py" in text for text in file_texts)

    @pytest.mark.parametrize(
        "spec,expected_indicator",
        [
            (DisplayOptions(sort_key=METRIC_LOC, metrics=(METRIC_LOC,)), "lines"),
            (
                DisplayOptions(sort_key=METRIC_SIZE, metrics=(METRIC_SIZE,)),
                ["B", "KB", "MB"],
            ),
            (
                DisplayOptions(sort_key=METRIC_MTIME, metrics=(METRIC_MTIME,)),
                ["Today", "Yesterday", r"\d{4}-\d{2}-\d{2}"],
            ),
        ],
    )
    def test_with_statistics(
        self,
        mocker: MockerFixture,
        structure_with_stats: dict[str, Any],
        color_map: dict[str, str],
        spec: DisplayOptions,
        expected_indicator: str | list[str],
    ) -> None:
        mock_tree = MagicMock(spec=Tree)
        mock_subtree = MagicMock(spec=Tree)
        mock_tree.add.return_value = mock_subtree
        build_tree(structure_with_stats, mock_tree, color_map, spec)
        calls = [str(call.args[0]) for call in mock_tree.add.call_args_list]
        if isinstance(expected_indicator, list):
            found = any(
                re.search(indicator, call)
                for indicator in expected_indicator
                for call in calls
            )
            assert found, f"None of the expected indicators {expected_indicator} found"
        else:
            assert any(expected_indicator in call for call in calls), (
                f"Expected indicator '{expected_indicator}' not found"
            )

    def test_max_depth_indicator(
        self,
        mocker: MockerFixture,
        max_depth_structure: dict[str, Any],
        color_map: dict[str, str],
    ) -> None:
        mock_tree = MagicMock(spec=Tree)
        mock_subtree = MagicMock(spec=Tree)
        mock_tree.add.return_value = mock_subtree
        build_tree(max_depth_structure, mock_tree, color_map, DisplayOptions())
        mock_subtree.add.assert_called_once()
        assert "(max depth reached)" in str(mock_subtree.add.call_args[0][0])


class TestBuildTreeGitStatus:
    """Git-status annotation and ordering, threaded through ``spec``."""

    @pytest.fixture
    def git_structure(self) -> dict[str, Any]:
        return {
            "_files": ["clean.py", "mod.py", "add.py", "del.py", "untr.py"],
            "_git_markers": {
                "mod.py": "M",
                "add.py": "A",
                "del.py": "D",
                "untr.py": "U",
            },
        }

    def test_badges_appended_when_shown(
        self, git_structure: dict[str, Any], color_map: dict[str, str]
    ) -> None:
        mock_tree = MagicMock(spec=Tree)
        build_tree(
            git_structure, mock_tree, color_map, DisplayOptions(show_git_status=True)
        )
        by_name = {t.plain.split()[1]: t.plain for t in _text_calls(mock_tree)}
        assert by_name["mod.py"].endswith("[M]")
        assert by_name["add.py"].endswith("[A]")
        assert by_name["del.py"].endswith("[D]")
        assert by_name["untr.py"].endswith("[U]")
        assert "[" not in by_name["clean.py"]

    def test_deleted_file_is_struck_through(
        self, git_structure: dict[str, Any], color_map: dict[str, str]
    ) -> None:
        mock_tree = MagicMock(spec=Tree)
        build_tree(
            git_structure, mock_tree, color_map, DisplayOptions(show_git_status=True)
        )
        del_text = next(t for t in _text_calls(mock_tree) if "del.py" in t.plain)
        assert any("strike" in str(span.style) for span in del_text.spans)

    def test_no_badges_without_show_git_status(
        self, git_structure: dict[str, Any], color_map: dict[str, str]
    ) -> None:
        """Sorting by git status still fetches markers, but adds no badge."""
        mock_tree = MagicMock(spec=Tree)
        build_tree(
            git_structure,
            mock_tree,
            color_map,
            DisplayOptions(sort_key="git_status"),
        )
        plains = _text_plains(mock_tree)
        assert not any("[M]" in p or "[A]" in p for p in plains)

    def test_git_status_sort_order(
        self, git_structure: dict[str, Any], color_map: dict[str, str]
    ) -> None:
        mock_tree = MagicMock(spec=Tree)
        build_tree(
            git_structure,
            mock_tree,
            color_map,
            DisplayOptions(sort_key="git_status", show_git_status=True),
        )
        ordered_names = [t.plain.split()[1] for t in _text_calls(mock_tree)]
        assert ordered_names == ["mod.py", "add.py", "del.py", "untr.py", "clean.py"]


class TestDisplayTree:
    def test_basic_display(self, mocker: MockerFixture, temp_dir: str) -> None:
        mock_console = mocker.patch("recursivist.tree.Console")
        mock_tree_class = mocker.patch("recursivist.tree.Tree")
        mock_build_tree = mocker.patch("recursivist.tree.build_tree")
        mock_get_structure = mocker.patch("recursivist.tree.get_directory_structure")
        mock_get_structure.return_value = ({}, set())
        with open(os.path.join(temp_dir, "test.txt"), "w") as f:
            f.write("Test content")
        display_tree(temp_dir)
        mock_tree_class.assert_called_once()
        mock_console.return_value.print.assert_called_once()
        mock_build_tree.assert_called_once()

    def test_default_spec_is_passed_to_build_tree(
        self, mocker: MockerFixture, temp_dir: str
    ) -> None:
        """When no spec is given, build_tree receives a plain DisplayOptions."""
        mocker.patch("recursivist.tree.Console")
        mocker.patch("recursivist.tree.Tree")
        mock_build_tree = mocker.patch("recursivist.tree.build_tree")
        mock_get_structure = mocker.patch("recursivist.tree.get_directory_structure")
        mock_get_structure.return_value = ({}, set())
        display_tree(temp_dir)
        passed_spec = mock_build_tree.call_args.args[3]
        assert passed_spec == DisplayOptions()

    def test_with_filtering_options(self, mocker: MockerFixture, temp_dir: str) -> None:
        mock_get_structure = mocker.patch("recursivist.tree.get_directory_structure")
        mock_compile_regex = mocker.patch("recursivist.tree.compile_regex_patterns")
        mock_get_structure.return_value = ({}, set())
        mock_compile_regex.return_value = []
        exclude_extensions = {".pyc", ".log"}
        display_tree(
            temp_dir,
            ["node_modules", "dist"],
            ".gitignore",
            exclude_extensions,
            ["test_*"],
            ["*.py"],
            True,
            2,
        )
        mock_get_structure.assert_called_once()
        assert mock_compile_regex.call_count >= 1
        _, kwargs = mock_get_structure.call_args
        assert kwargs["exclude_dirs"] == ["node_modules", "dist"]
        assert kwargs["ignore_file"] == ".gitignore"
        assert kwargs["exclude_extensions"] == {".pyc", ".log"}
        assert kwargs["max_depth"] == 2

    def test_with_statistics(self, mocker: MockerFixture, temp_dir: str) -> None:
        mock_tree = mocker.patch("recursivist.tree.Tree")
        mock_get_structure = mocker.patch("recursivist.tree.get_directory_structure")
        structure = {"_loc": 100, "_size": 10240, "_mtime": 1625097600.0, "_files": []}
        mock_get_structure.return_value = (structure, set())
        display_tree(temp_dir, spec=ALL_METRICS_SPEC)
        args, _ = mock_tree.call_args
        root_label = args[0]
        assert "100 lines" in root_label
        assert "10.0 KB" in root_label
        date_formats = ["Today", "Yesterday", "Jul 1", "2021-07-01"]
        assert any(fmt in root_label for fmt in date_formats)

    def test_spec_drives_scanner_metric_flags(
        self, mocker: MockerFixture, temp_dir: str
    ) -> None:
        """display_tree maps the spec's show_* onto the scanner's sort_by_* kwargs."""
        mocker.patch("recursivist.tree.Console")
        mocker.patch("recursivist.tree.Tree")
        mocker.patch("recursivist.tree.build_tree")
        mock_get_structure = mocker.patch("recursivist.tree.get_directory_structure")
        mock_get_structure.return_value = ({}, set())
        display_tree(
            temp_dir,
            spec=DisplayOptions(metrics=(METRIC_LOC, METRIC_SIZE)),
        )
        _, kwargs = mock_get_structure.call_args
        assert kwargs["sort_by_loc"] is True
        assert kwargs["sort_by_size"] is True
        assert kwargs["sort_by_mtime"] is False


def test_build_tree_combined(mocker: MockerFixture) -> None:
    """Combined test of build_tree functionality across mixed file shapes."""
    mock_tree = MagicMock(spec=Tree)
    color_map = {".py": "#FF0000", ".txt": "#00FF00"}
    structure = {
        "_files": [
            "file1.txt",
            ("file2.py", "/path/to/file2.py"),
            ("file3.md", "/path/to/file3.md", 50),
            ("file4.json", "/path/to/file4.json", 20, 1024),
            ("file5.js", "/path/to/file5.js", 30, 2048, time.time()),
        ],
        "subdir": {"_files": ["subfile.py"]},
    }
    build_tree(structure, mock_tree, color_map, ALL_METRICS_SPEC)
    assert mock_tree.add.call_count >= 6
    texts = _text_plains(mock_tree)
    for file_name in ["file1.txt", "file2.py", "file3.md", "file4.json", "file5.js"]:
        assert any(file_name in text for text in texts)


class TestBuildTreeProperties:
    """Property-based tests for build_tree function."""

    @given(
        structure=simple_directory_structure(),
        color_map=st.dictionaries(
            keys=st.text(min_size=1, max_size=10),
            values=st.text(min_size=1, max_size=10),
        ),
    )
    @settings(max_examples=50)
    def test_build_tree_adds_files(
        self, structure: dict[str, Any], color_map: dict[str, str]
    ) -> None:
        """Test that build_tree properly adds all files to the tree."""
        mock_tree = MagicMock(spec=Tree)
        mock_subtree = MagicMock(spec=Tree)
        mock_tree.add.return_value = mock_subtree

        def count_files_and_folders(struct: dict[str, Any]) -> int:
            count = 0
            if "_files" in struct:
                count += len(struct["_files"])
            for key, value in struct.items():
                if (
                    key != "_files"
                    and key != "_loc"
                    and key != "_size"
                    and key != "_mtime"
                    and key != "_max_depth_reached"
                    and isinstance(value, dict)
                ):
                    count += 1
                    count += count_files_and_folders(value)
            return count

        expected_calls = count_files_and_folders(structure)
        build_tree(structure, mock_tree, color_map, DisplayOptions())
        if expected_calls > 0:
            assert mock_tree.add.call_count > 0, (
                "build_tree should make at least one call to tree.add when there are files or folders"
            )


class TestBuildTreeStructures:
    def test_simple_structure(
        self,
        mock_tree: MagicMock,
        color_map: dict[str, str],
        simple_structure: dict[str, Any],
    ) -> None:
        """Test building a tree from a simple structure."""
        build_tree(simple_structure, mock_tree, color_map, DisplayOptions())
        assert mock_tree.add.call_count == 3
        texts = _text_plains(mock_tree)
        assert "📄 file1.txt" in texts
        assert "📄 file2.py" in texts
        assert "📄 file3.md" in texts

    def test_nested_structure(
        self,
        mock_tree: MagicMock,
        mock_subtree: MagicMock,
        color_map: dict[str, str],
        nested_structure: dict[str, Any],
    ) -> None:
        """Test building a tree with nested directories."""
        mock_tree.add.return_value = mock_subtree
        build_tree(nested_structure, mock_tree, color_map, DisplayOptions())
        assert mock_tree.add.call_count >= 4
        assert mock_subtree.add.call_count >= 3
        dir_calls = [
            call
            for call in mock_tree.add.call_args_list
            if not isinstance(call.args[0], Text)
        ]
        dir_names = [call.args[0] for call in dir_calls]
        assert "📁 subdir1" in dir_names
        assert "📁 subdir2" in dir_names

    def test_with_full_path(
        self, mock_tree: MagicMock, color_map: dict[str, str]
    ) -> None:
        """Test building a tree with full file paths."""
        full_path_structure = {
            "_files": [
                ("file1.txt", "/path/to/file1.txt"),
                ("file2.py", "/path/to/file2.py"),
                ("file3.md", "/path/to/file3.md"),
            ],
        }
        build_tree(
            full_path_structure,
            mock_tree,
            color_map,
            DisplayOptions(),
            show_full_path=True,
        )
        texts = _text_plains(mock_tree)
        assert "📄 /path/to/file1.txt" in texts
        assert "📄 /path/to/file2.py" in texts
        assert "📄 /path/to/file3.md" in texts

    @pytest.mark.parametrize(
        "spec,expected_indicator",
        [
            (DisplayOptions(sort_key=METRIC_LOC, metrics=(METRIC_LOC,)), "lines"),
            (DisplayOptions(sort_key=METRIC_SIZE, metrics=(METRIC_SIZE,)), ["B", "KB"]),
            (
                DisplayOptions(sort_key=METRIC_MTIME, metrics=(METRIC_MTIME,)),
                ["Today", "Yesterday", r"\d{4}-\d{2}-\d{2}"],
            ),
        ],
    )
    def test_with_statistics(
        self,
        mock_tree: MagicMock,
        color_map: dict[str, str],
        structure_with_stats: dict[str, Any],
        spec: DisplayOptions,
        expected_indicator: str | list[str],
    ) -> None:
        """Test building a tree with file statistics."""
        build_tree(structure_with_stats, mock_tree, color_map, spec)
        calls = [str(call.args[0]) for call in mock_tree.add.call_args_list]
        if isinstance(expected_indicator, list):
            found = any(
                re.search(indicator, call)
                for indicator in expected_indicator
                for call in calls
            )
            assert found, f"No indicator matching {expected_indicator} found"
        else:
            assert any(expected_indicator in call for call in calls), (
                f"Expected indicator '{expected_indicator}' not found"
            )

    def test_max_depth_indicator(
        self,
        mock_tree: MagicMock,
        mock_subtree: MagicMock,
        color_map: dict[str, str],
        max_depth_structure: dict[str, Any],
    ) -> None:
        """Test displaying max depth indicator in tree."""
        mock_tree.add.return_value = mock_subtree
        build_tree(max_depth_structure, mock_tree, color_map, DisplayOptions())
        mock_subtree.add.assert_called_once()
        assert "(max depth reached)" in str(mock_subtree.add.call_args[0][0])

    def test_with_various_file_formats(
        self, mock_tree: MagicMock, color_map: dict[str, str]
    ) -> None:
        """Test building a tree with various file info formats."""
        mixed_structure = {
            "_files": [
                "file1.txt",
                ("file2.py", "/path/to/file2.py"),
                ("file3.md", "/path/to/file3.md", 50),
                ("file4.json", "/path/to/file4.json", 20, 1024),
                ("file5.js", "/path/to/file5.js", 30, 2048, time.time()),
            ]
        }
        build_tree(mixed_structure, mock_tree, color_map, ALL_METRICS_SPEC)
        assert mock_tree.add.call_count == 5
        texts = _text_plains(mock_tree)
        for file_name in [
            "file1.txt",
            "file2.py",
            "file3.md",
            "file4.json",
            "file5.js",
        ]:
            assert any(file_name in text for text in texts)
        assert not any("/path/to/" in text for text in texts)
        mock_tree.reset_mock()
        build_tree(
            mixed_structure,
            mock_tree,
            color_map,
            ALL_METRICS_SPEC,
            show_full_path=True,
        )
        texts = _text_plains(mock_tree)
        assert any("/path/to/file2.py" in text for text in texts)
        assert any("/path/to/file3.md" in text for text in texts)
        assert any("/path/to/file4.json" in text for text in texts)
        assert any("/path/to/file5.js" in text for text in texts)
        assert any("file1.txt" in text and "/path/to/" not in text for text in texts)
