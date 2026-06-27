"""Tests for recursivist.tree: build_tree and display_tree."""

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

from recursivist.tree import build_tree, display_tree
from tests.strategies import simple_directory_structure


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
        build_tree(simple_structure, mock_tree, color_map)
        assert mock_tree.add.call_count >= 3
        calls = [
            call
            for call in mock_tree.add.call_args_list
            if isinstance(call.args[0], Text)
        ]
        file_texts = [call.args[0].plain for call in calls]
        assert any("file1.txt" in text for text in file_texts)
        assert any("file2.py" in text for text in file_texts)

    def test_empty_structure(self, mocker: MockerFixture) -> None:
        mock_tree = MagicMock(spec=Tree)
        color_map: dict[str, str] = {}
        structure: dict[str, Any] = {}
        build_tree(structure, mock_tree, color_map)
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
        build_tree(structure, mock_tree, color_map, show_full_path=True)
        calls = [
            call
            for call in mock_tree.add.call_args_list
            if isinstance(call.args[0], Text)
        ]
        file_texts = [call.args[0].plain for call in calls]
        assert any("/path/to/file1.txt" in text for text in file_texts)
        assert any("/path/to/file2.py" in text for text in file_texts)

    @pytest.mark.parametrize(
        "option,expected_indicator",
        [
            ("sort_by_loc", "lines"),
            ("sort_by_size", ["B", "KB", "MB"]),
            ("sort_by_mtime", ["Today", "Yesterday", r"\d{4}-\d{2}-\d{2}"]),
        ],
    )
    def test_with_statistics(
        self,
        mocker: MockerFixture,
        structure_with_stats: dict[str, Any],
        color_map: dict[str, str],
        option: str,
        expected_indicator: str | list[str],
    ) -> None:
        mock_tree = MagicMock(spec=Tree)
        mock_subtree = MagicMock(spec=Tree)
        mock_tree.add.return_value = mock_subtree
        if option == "sort_by_loc":
            build_tree(
                structure_with_stats,
                mock_tree,
                color_map,
                sort_by_loc=True,
            )
        elif option == "sort_by_size":
            build_tree(
                structure_with_stats,
                mock_tree,
                color_map,
                sort_by_size=True,
            )
        elif option == "sort_by_mtime":
            build_tree(
                structure_with_stats,
                mock_tree,
                color_map,
                sort_by_mtime=True,
            )
        else:
            build_tree(structure_with_stats, mock_tree, color_map)
        calls = [str(call.args[0]) for call in mock_tree.add.call_args_list]
        if isinstance(expected_indicator, list):
            found = False
            for indicator in expected_indicator:
                if any(re.search(indicator, call) for call in calls):
                    found = True
                    break
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
        build_tree(max_depth_structure, mock_tree, color_map)
        mock_subtree.add.assert_called_once()
        assert "(max depth reached)" in str(mock_subtree.add.call_args[0][0])


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
        display_tree(temp_dir, sort_by_loc=True, sort_by_size=True, sort_by_mtime=True)
        args, _ = mock_tree.call_args
        root_label = args[0]
        assert "100 lines" in root_label
        assert "10.0 KB" in root_label
        date_formats = ["Today", "Yesterday", "Jul 1", "2021-07-01"]
        assert any(fmt in root_label for fmt in date_formats)


def test_build_tree_combined(mocker: MockerFixture) -> None:
    """Combined test of build_tree functionality."""
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
    build_tree(
        structure,
        mock_tree,
        color_map,
        sort_by_loc=True,
        sort_by_size=True,
        sort_by_mtime=True,
    )
    assert mock_tree.add.call_count >= 6
    calls = [
        call for call in mock_tree.add.call_args_list if isinstance(call.args[0], Text)
    ]
    texts = [call.args[0].plain for call in calls if isinstance(call.args[0], Text)]
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
        build_tree(structure, mock_tree, color_map)
        if expected_calls > 0:
            assert mock_tree.add.call_count > 0, (
                "build_tree should make at least one call to tree.add when there are files or folders"
            )
        else:
            pass


class TestBuildTreeStructures:
    def test_simple_structure(
        self,
        mock_tree: MagicMock,
        color_map: dict[str, str],
        simple_structure: dict[str, Any],
    ) -> None:
        """Test building a tree from a simple structure."""
        build_tree(simple_structure, mock_tree, color_map)
        assert mock_tree.add.call_count == 3
        calls = [
            call
            for call in mock_tree.add.call_args_list
            if isinstance(call.args[0], Text)
        ]
        texts = [call.args[0].plain for call in calls]
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
        build_tree(nested_structure, mock_tree, color_map)
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
        build_tree(full_path_structure, mock_tree, color_map, show_full_path=True)
        calls = [
            call
            for call in mock_tree.add.call_args_list
            if isinstance(call.args[0], Text)
        ]
        texts = [call.args[0].plain for call in calls]
        assert "📄 /path/to/file1.txt" in texts
        assert "📄 /path/to/file2.py" in texts
        assert "📄 /path/to/file3.md" in texts

    @pytest.mark.parametrize(
        "option,expected_indicator",
        [
            ("sort_by_loc", "lines"),
            ("sort_by_size", ["B", "KB"]),
            ("sort_by_mtime", ["Today", "Yesterday", r"\d{4}-\d{2}-\d{2}"]),
        ],
    )
    def test_with_statistics(
        self,
        mock_tree: MagicMock,
        color_map: dict[str, str],
        structure_with_stats: dict[str, Any],
        option: str,
        expected_indicator: str | list[str],
    ) -> None:
        """Test building a tree with file statistics."""
        if option == "sort_by_loc":
            build_tree(
                structure_with_stats,
                mock_tree,
                color_map,
                sort_by_loc=True,
            )
        elif option == "sort_by_size":
            build_tree(
                structure_with_stats,
                mock_tree,
                color_map,
                sort_by_size=True,
            )
        elif option == "sort_by_mtime":
            build_tree(
                structure_with_stats,
                mock_tree,
                color_map,
                sort_by_mtime=True,
            )
        else:
            build_tree(structure_with_stats, mock_tree, color_map)
        calls = [str(call.args[0]) for call in mock_tree.add.call_args_list]
        if isinstance(expected_indicator, list):
            found = False
            for indicator in expected_indicator:
                if any(re.search(indicator, call) for call in calls):
                    found = True
                    break
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
        build_tree(max_depth_structure, mock_tree, color_map)
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
        build_tree(
            mixed_structure,
            mock_tree,
            color_map,
            sort_by_loc=True,
            sort_by_size=True,
            sort_by_mtime=True,
        )
        assert mock_tree.add.call_count == 5
        calls = [
            call
            for call in mock_tree.add.call_args_list
            if isinstance(call.args[0], Text)
        ]
        texts = [call.args[0].plain for call in calls]
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
            show_full_path=True,
            sort_by_loc=True,
            sort_by_size=True,
            sort_by_mtime=True,
        )
        calls = [
            call
            for call in mock_tree.add.call_args_list
            if isinstance(call.args[0], Text)
        ]
        texts = [call.args[0].plain for call in calls]
        assert any("/path/to/file2.py" in text for text in texts)
        assert any("/path/to/file3.md" in text for text in texts)
        assert any("/path/to/file4.json" in text for text in texts)
        assert any("/path/to/file5.js" in text for text in texts)
        assert any("file1.txt" in text and "/path/to/" not in text for text in texts)
