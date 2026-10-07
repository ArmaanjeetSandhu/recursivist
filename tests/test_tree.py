"""Tests for recursivist.tree: build_tree and display_tree.

Both render a scanned ``Directory`` and take a resolved
:class:`~recursivist.flags.DisplayOptions` (``spec``) that carries the sort key and
metric annotations. ``spec`` is a required positional argument to ``build_tree`` and
optional for ``display_tree`` (defaulting to a plain ``DisplayOptions``).
"""

import re
import time
from unittest.mock import MagicMock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pytest_mock import MockerFixture
from rich.text import Text
from rich.tree import Tree

from recursivist._models import Directory, FileEntry
from recursivist.colors import build_color_map
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
        simple_structure: Directory,
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

    def test_empty_structure(self) -> None:
        mock_tree = MagicMock(spec=Tree)
        color_map: dict[str, str] = {}
        build_tree(Directory(), mock_tree, color_map, DisplayOptions())
        mock_tree.add.assert_not_called()

    def test_with_full_paths(self, color_map: dict[str, str]) -> None:
        mock_tree = MagicMock(spec=Tree)
        mock_subtree = MagicMock(spec=Tree)
        mock_tree.add.return_value = mock_subtree
        structure = Directory(
            files=[
                FileEntry("file1.txt", "/path/to/file1.txt"),
                FileEntry("file2.py", "/path/to/file2.py"),
            ],
            subdirectories={
                "subdir": Directory(
                    files=[FileEntry("subfile.py", "/path/to/subdir/subfile.py")]
                )
            },
        )
        build_tree(structure, mock_tree, color_map, DisplayOptions())
        file_texts = _text_plains(mock_tree)
        assert any("/path/to/file1.txt" in text for text in file_texts)
        assert any("/path/to/file2.py" in text for text in file_texts)


class TestBuildTreeGitStatus:
    """Git-status annotation and ordering, threaded through ``spec``."""

    @pytest.fixture
    def git_structure(self) -> Directory:
        return Directory(
            files=[
                FileEntry("clean.py", "clean.py"),
                FileEntry("mod.py", "mod.py"),
                FileEntry("add.py", "add.py"),
                FileEntry("del.py", "del.py"),
                FileEntry("untr.py", "untr.py"),
            ],
            git_markers={
                "mod.py": "M",
                "add.py": "A",
                "del.py": "D",
                "untr.py": "U",
            },
        )

    def test_badges_appended_when_shown(
        self, git_structure: Directory, color_map: dict[str, str]
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
        self, git_structure: Directory, color_map: dict[str, str]
    ) -> None:
        mock_tree = MagicMock(spec=Tree)
        build_tree(
            git_structure, mock_tree, color_map, DisplayOptions(show_git_status=True)
        )
        del_text = next(t for t in _text_calls(mock_tree) if "del.py" in t.plain)
        assert any("strike" in str(span.style) for span in del_text.spans)

    def test_no_badges_without_show_git_status(
        self, git_structure: Directory, color_map: dict[str, str]
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
        self, git_structure: Directory, color_map: dict[str, str]
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
    def test_basic_display(self, mocker: MockerFixture) -> None:
        mock_console = mocker.patch("recursivist.tree.Console")
        mock_tree_class = mocker.patch("recursivist.tree.Tree")
        mock_build_tree = mocker.patch("recursivist.tree.build_tree")
        structure = Directory(files=[FileEntry("test.txt", "test.txt")])
        display_tree(structure, {".txt"}, "root")
        mock_tree_class.assert_called_once()
        mock_console.return_value.print.assert_called_once_with(
            mock_tree_class.return_value
        )
        mock_build_tree.assert_called_once()
        assert mock_build_tree.call_args.args[0] is structure

    def test_default_spec_is_passed_to_build_tree(self, mocker: MockerFixture) -> None:
        """When no spec is given, build_tree receives a plain DisplayOptions."""
        mocker.patch("recursivist.tree.Console")
        mocker.patch("recursivist.tree.Tree")
        mock_build_tree = mocker.patch("recursivist.tree.build_tree")
        display_tree(Directory(), set(), "root")
        passed_spec = mock_build_tree.call_args.args[3]
        assert passed_spec == DisplayOptions()

    def test_color_map_depends_only_on_the_extension_set(
        self, mocker: MockerFixture
    ) -> None:
        """build_tree receives the mapping shared by every renderer."""
        mocker.patch("recursivist.tree.Console")
        mocker.patch("recursivist.tree.Tree")
        mock_build_tree = mocker.patch("recursivist.tree.build_tree")
        extensions = {".py", ".md", ".toml", ".json", ".txt"}
        display_tree(Directory(), extensions, "root")
        assert mock_build_tree.call_args.args[2] == build_color_map(extensions)

    def test_root_name_labels_the_root(self, mocker: MockerFixture) -> None:
        mocker.patch("recursivist.tree.Console")
        mock_tree = mocker.patch("recursivist.tree.Tree")
        display_tree(Directory(), set(), "owner-repo")
        (root_label,), _ = mock_tree.call_args
        assert root_label.plain.endswith(" owner-repo")

    def test_icon_style_is_passed_to_build_tree(self, mocker: MockerFixture) -> None:
        mocker.patch("recursivist.tree.Console")
        mocker.patch("recursivist.tree.Tree")
        mock_build_tree = mocker.patch("recursivist.tree.build_tree")
        display_tree(Directory(), set(), "root", icon_style="nerd")
        assert mock_build_tree.call_args.kwargs["icon_style"] == "nerd"

    def test_with_statistics(self, mocker: MockerFixture) -> None:
        mocker.patch("recursivist.tree.Console")
        mock_tree = mocker.patch("recursivist.tree.Tree")
        structure = Directory(loc=100, size=10240, mtime=1625097600.0)
        display_tree(structure, set(), "root", spec=ALL_METRICS_SPEC)
        args, _ = mock_tree.call_args
        root_label = args[0]
        assert "100 lines" in root_label
        assert "10.0 KB" in root_label
        date_formats = ["Today", "Yesterday", "Jul 1", "2021-07-01"]
        assert any(fmt in root_label for fmt in date_formats)

    def test_renders_structure_as_given(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The root name and every entry of the structure are printed."""
        structure = Directory(
            files=[FileEntry("a.py", "a.py")],
            subdirectories={"pkg": Directory(files=[FileEntry("b.md", "b.md")])},
        )
        display_tree(structure, {".py", ".md"}, "project")
        out = capsys.readouterr().out
        for name in ("project", "a.py", "pkg", "b.md"):
            assert name in out


def test_build_tree_combined() -> None:
    """Combined test of build_tree functionality across mixed file shapes."""
    mock_tree = MagicMock(spec=Tree)
    color_map = {".py": "#FF0000", ".txt": "#00FF00"}
    structure = Directory(
        files=[
            FileEntry("file1.txt", "file1.txt"),
            FileEntry("file2.py", "/path/to/file2.py"),
            FileEntry("file3.md", "/path/to/file3.md", 50),
            FileEntry("file4.json", "/path/to/file4.json", 20, 1024),
            FileEntry("file5.js", "/path/to/file5.js", 30, 2048, time.time()),
        ],
        subdirectories={
            "subdir": Directory(files=[FileEntry("subfile.py", "subfile.py")])
        },
    )
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
        self, structure: Directory, color_map: dict[str, str]
    ) -> None:
        """Test that build_tree properly adds all files to the tree."""
        mock_tree = MagicMock(spec=Tree)
        mock_subtree = MagicMock(spec=Tree)
        mock_tree.add.return_value = mock_subtree

        def count_files_and_folders(struct: Directory) -> int:
            count = len(struct.files)
            for subdirectory in struct.subdirectories.values():
                count += 1
                count += count_files_and_folders(subdirectory)
            return count

        expected_calls = count_files_and_folders(structure)
        build_tree(structure, mock_tree, color_map, DisplayOptions())
        if expected_calls > 0:
            assert mock_tree.add.call_count > 0, (
                "build_tree should make at least one call to tree.add "
                "when there are files or folders"
            )


class TestBuildTreeStructures:
    def test_simple_structure(
        self,
        mock_tree: MagicMock,
        color_map: dict[str, str],
        simple_structure: Directory,
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
        nested_structure: Directory,
    ) -> None:
        """Test building a tree with nested directories."""
        mock_tree.add.return_value = mock_subtree
        build_tree(nested_structure, mock_tree, color_map, DisplayOptions())
        assert mock_tree.add.call_count >= 4
        assert mock_subtree.add.call_count >= 3
        added = [call.args[0] for call in mock_tree.add.call_args_list]
        assert all(isinstance(node, Text) for node in added)
        dir_names = [node.plain for node in added if node.plain.startswith("📂")]
        assert "📂 subdir1" in dir_names
        assert "📂 subdir2" in dir_names

    def test_with_full_path(
        self, mock_tree: MagicMock, color_map: dict[str, str]
    ) -> None:
        """Test building a tree with full file paths."""
        full_path_structure = Directory(
            files=[
                FileEntry("file1.txt", "/path/to/file1.txt"),
                FileEntry("file2.py", "/path/to/file2.py"),
                FileEntry("file3.md", "/path/to/file3.md"),
            ]
        )
        build_tree(full_path_structure, mock_tree, color_map, DisplayOptions())
        texts = _text_plains(mock_tree)
        assert "📄 /path/to/file1.txt" in texts
        assert "📄 /path/to/file2.py" in texts
        assert "📄 /path/to/file3.md" in texts

    @pytest.mark.parametrize(
        ("spec", "expected_indicator"),
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
        structure_with_stats: Directory,
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

    def test_metric_annotations_on_files_and_directories(
        self, mock_tree: MagicMock, mock_subtree: MagicMock
    ) -> None:
        """Every file is annotated with its own metrics and every directory with
        its totals, in the order the metrics were requested."""
        mock_tree.add.return_value = mock_subtree
        structure = Directory(
            loc=100,
            size=1024,
            files=[
                FileEntry("big.py", "big.py", 50, 512),
                FileEntry("small.py", "small.py", 30, 256),
            ],
            subdirectories={
                "subdir": Directory(
                    loc=20,
                    size=256,
                    files=[FileEntry("nested.py", "nested.py", 20, 256)],
                )
            },
        )
        spec = DisplayOptions(metrics=(METRIC_LOC, METRIC_SIZE))
        build_tree(structure, mock_tree, {}, spec)
        assert _text_plains(mock_tree) == [
            "📄 big.py (50 lines, 512 B)",
            "📄 small.py (30 lines, 256 B)",
            "📂 subdir (20 lines, 256 B)",
        ]
        assert _text_plains(mock_subtree) == ["📄 nested.py (20 lines, 256 B)"]

    def test_max_depth_is_not_expanded(
        self,
        mock_tree: MagicMock,
        mock_subtree: MagicMock,
        color_map: dict[str, str],
        max_depth_structure: Directory,
    ) -> None:
        """Test that a truncated directory is left unexpanded."""
        mock_tree.add.return_value = mock_subtree
        build_tree(max_depth_structure, mock_tree, color_map, DisplayOptions())
        mock_subtree.add.assert_not_called()
        labels = [str(call.args[0]) for call in mock_tree.add.call_args_list]
        assert "📂 subdir" in labels
        assert "📁 empty_subdir" in labels

    def test_symlink_loop_is_marked_not_expanded(
        self,
        mock_tree: MagicMock,
        mock_subtree: MagicMock,
        color_map: dict[str, str],
    ) -> None:
        """A directory that links back to an ancestor gets a marker, not children."""
        mock_tree.add.return_value = mock_subtree
        structure = Directory(subdirectories={"loop": Directory(symlink_loop=True)})
        build_tree(structure, mock_tree, color_map, DisplayOptions())
        assert [str(call.args[0]) for call in mock_tree.add.call_args_list] == [
            "📂 loop"
        ]
        assert [str(call.args[0]) for call in mock_subtree.add.call_args_list] == [
            "↩ (symlink loop)"
        ]

    def test_with_various_file_formats(
        self, mock_tree: MagicMock, color_map: dict[str, str]
    ) -> None:
        """Test building a tree with various file info formats."""
        mixed_structure = Directory(
            files=[
                FileEntry("file1.txt", "file1.txt"),
                FileEntry("file2.py", "/path/to/file2.py"),
                FileEntry("file3.md", "/path/to/file3.md", 50),
                FileEntry("file4.json", "/path/to/file4.json", 20, 1024),
                FileEntry("file5.js", "/path/to/file5.js", 30, 2048, time.time()),
            ]
        )
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
        assert any("/path/to/file2.py" in text for text in texts)
        assert any("/path/to/file3.md" in text for text in texts)
        assert any("/path/to/file4.json" in text for text in texts)
        assert any("/path/to/file5.js" in text for text in texts)
        assert any("file1.txt" in text and "/path/to/" not in text for text in texts)
