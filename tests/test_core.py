import json
import os
import re
import tempfile
import time
from pathlib import Path
from typing import Any, Optional, Union
from unittest.mock import MagicMock, mock_open

import pytest
from pytest_mock import MockerFixture
from rich.text import Text
from rich.tree import Tree

from recursivist.core import (
    build_tree,
    compile_regex_patterns,
    count_lines_of_code,
    display_tree,
    format_size,
    format_timestamp,
    generate_color_for_extension,
    get_directory_structure,
    get_file_mtime,
    get_file_size,
    parse_ignore_file,
    should_exclude,
    sort_files_by_type,
)
from recursivist.exporters import get_exporter


class TestFileSize:
    @pytest.mark.parametrize(
        "file_name,size",
        [
            ("empty.txt", 0),
            ("small.txt", 10),
            ("medium.txt", 1024),
        ],
    )
    def test_normal_files(self, temp_dir: str, file_name: str, size: int) -> None:
        path = os.path.join(temp_dir, file_name)
        with open(path, "wb") as f:
            f.write(b"x" * size)
        assert get_file_size(path) == size

    def test_nonexistent_file(self, temp_dir: str) -> None:
        non_existent = os.path.join(temp_dir, "non_existent.txt")
        assert get_file_size(non_existent) == 0

    @pytest.mark.parametrize(
        "error_type,error_msg",
        [
            (PermissionError, "Permission denied"),
            (Exception, "Generic error"),
        ],
    )
    def test_file_errors(
        self,
        mocker: MockerFixture,
        temp_dir: str,
        error_type: type[Exception],
        error_msg: str,
    ) -> None:
        error_file = os.path.join(temp_dir, "error.txt")
        with open(error_file, "w") as f:
            f.write("content")
        mocker.patch("os.path.getsize", side_effect=error_type(error_msg))
        assert get_file_size(error_file) == 0

    def test_special_files(self, mocker: MockerFixture) -> None:
        mocker.patch("os.path.getsize", return_value=42)
        assert get_file_size("/dev/null") == 42


class TestFileMtime:
    def test_normal_files(self, temp_dir: str) -> None:
        file_path = os.path.join(temp_dir, "test_file.txt")
        with open(file_path, "w") as f:
            f.write("content")
        actual_mtime = os.path.getmtime(file_path)
        assert get_file_mtime(file_path) == actual_mtime

    @pytest.mark.parametrize(
        "error_type,error_msg,expected",
        [
            (None, None, 0.0),
            (PermissionError, "Permission denied", 0.0),
            (Exception, "Generic error", 0.0),
        ],
    )
    def test_file_errors(
        self,
        mocker: MockerFixture,
        temp_dir: str,
        error_type: Optional[type[Exception]],
        error_msg: Optional[str],
        expected: float,
    ) -> None:
        if error_type is None:
            non_existent = os.path.join(temp_dir, "non_existent.txt")
            assert get_file_mtime(non_existent) == expected
        else:
            error_file = os.path.join(temp_dir, "error.txt")
            with open(error_file, "w") as f:
                f.write("content")
            mocker.patch("os.path.getmtime", side_effect=error_type(error_msg))
            assert get_file_mtime(error_file) == expected

    def test_future_timestamp(self, mocker: MockerFixture) -> None:
        future_time = time.time() + 86400 * 365
        mocker.patch("os.path.getmtime", return_value=future_time)
        assert get_file_mtime("/path/to/future/file") == future_time


class TestCountLines:
    @pytest.mark.parametrize(
        "file_content,expected_lines",
        [
            ("", 0),
            ("Single line", 1),
            ("Line 1\nLine 2\nLine 3", 3),
            ("Line 1\nLine 2\nLine 3\n", 3),
        ],
    )
    def test_line_counting(
        self, temp_dir: str, file_content: str, expected_lines: int
    ) -> None:
        file_path = os.path.join(temp_dir, f"test_file_{expected_lines}.txt")
        with open(file_path, "w") as f:
            f.write(file_content)
        assert count_lines_of_code(file_path) == expected_lines

    def test_binary_file(self, temp_dir: str) -> None:
        file_path = os.path.join(temp_dir, "binary.bin")
        with open(file_path, "wb") as f:
            f.write(b"\x00\x01\x02\x03")
        assert count_lines_of_code(file_path) == 0

    def test_nonexistent_file(self, temp_dir: str) -> None:
        non_existent = os.path.join(temp_dir, "non_existent.txt")
        assert count_lines_of_code(non_existent) == 0

    def test_permission_denied(self, mocker: MockerFixture, temp_dir: str) -> None:
        permission_denied = os.path.join(temp_dir, "permission_denied.txt")
        with open(permission_denied, "w") as f:
            f.write("content")
        mock_open_call = mock_open(read_data="content")
        mocker.patch("builtins.open", mock_open_call)
        mock_open_call.side_effect = PermissionError("Permission denied")
        assert count_lines_of_code(permission_denied) == 0

    @pytest.mark.parametrize("encoding", ["utf-8", "utf-16"])
    def test_with_different_encodings(self, temp_dir: str, encoding: str) -> None:
        """Test counting lines with different file encodings."""
        file_path = os.path.join(temp_dir, f"{encoding}.txt")
        try:
            with open(file_path, "w", encoding=encoding) as f:
                f.write("Line 1\nLine 2\n")
            line_count = count_lines_of_code(file_path)
            assert line_count == 2, (
                f"Expected 2 lines in {encoding} file, got {line_count}"
            )
        except Exception as e:
            pytest.fail(f"count_lines_of_code failed with {encoding} encoding: {e}")

    def test_very_large_file(self, temp_dir: str) -> None:
        """Test counting lines in a large file."""
        test_file_path = os.path.join(temp_dir, "large_test.txt")
        expected_lines = 1000
        with open(test_file_path, "w") as f:
            for i in range(expected_lines):
                f.write(f"Line {i}\n")
        line_count = count_lines_of_code(test_file_path)
        assert line_count == expected_lines


class TestFormatSize:
    @pytest.mark.parametrize(
        "size,expected",
        [
            (0, "0 B"),
            (1, "1 B"),
            (10, "10 B"),
            (999, "999 B"),
            (1023, "1023 B"),
            (1024, "1.0 KB"),
            (1500, "1.5 KB"),
            (10 * 1024, "10.0 KB"),
            (1023.9 * 1024, "1023.9 KB"),
            (1024 * 1024, "1.0 MB"),
            (1.5 * 1024 * 1024, "1.5 MB"),
            (10 * 1024 * 1024, "10.0 MB"),
            (1023.9 * 1024 * 1024, "1023.9 MB"),
            (1024 * 1024 * 1024, "1.0 GB"),
            (1.5 * 1024 * 1024 * 1024, "1.5 GB"),
            (10 * 1024 * 1024 * 1024, "10.0 GB"),
            (-1, "-1 B"),
            (1024 * 1024 * 1024 * 1024, "1024.0 GB"),
        ],
    )
    def test_format_size(self, size: float, expected: str) -> None:
        assert format_size(int(size)) == expected


class TestFormatTimestamp:
    def test_today(self) -> None:
        now = time.time()
        formatted = format_timestamp(now)
        assert "Today" in formatted
        assert re.match(r"Today \d\d:\d\d", formatted)

    def test_yesterday(self) -> None:
        yesterday = time.time() - 86400
        formatted = format_timestamp(yesterday)
        assert "Yesterday" in formatted
        assert re.match(r"Yesterday \d\d:\d\d", formatted)

    def test_this_week(self) -> None:
        earlier_this_week = time.time() - 86400 * 3
        formatted = format_timestamp(earlier_this_week)
        assert re.match(r"\w{3} \d\d:\d\d", formatted)

    def test_this_year(self) -> None:
        earlier_this_year = time.time() - 86400 * 30
        formatted = format_timestamp(earlier_this_year)
        assert re.match(r"\w{3} \d{1,2}", formatted)

    def test_previous_year(self) -> None:
        previous_year = time.time() - 86400 * 400
        formatted = format_timestamp(previous_year)
        assert re.match(r"\d{4}-\d{2}-\d{2}", formatted)

    def test_old_date(self) -> None:
        assert re.match(r"\d{4}-\d{2}-\d{2}", format_timestamp(978307200))

    def test_epoch(self) -> None:
        assert format_timestamp(0) == "-"


class TestGenerateColorForExtension:
    def test_color_format(self) -> None:
        color = generate_color_for_extension(".py")
        assert re.match(r"^#[0-9A-Fa-f]{6}$", color)

    def test_consistency(self) -> None:
        """Test that the same extension always gets the same color."""
        color1 = generate_color_for_extension(".py")
        color2 = generate_color_for_extension(".py")
        color3 = generate_color_for_extension(".py")
        assert color1 == color2 == color3

    def test_different_extensions(self) -> None:
        """Test that different extensions get different colors."""
        extensions = [".py", ".js", ".txt", ".md", ".html", ".css", ".json", ".xml"]
        colors = [generate_color_for_extension(ext) for ext in extensions]
        assert len(set(colors)) == len(extensions)

    @pytest.mark.parametrize(
        "test_case,extension1,extension2",
        [
            ("case_sensitivity", ".py", ".PY"),
            ("with_without_dot", ".py", "py"),
        ],
    )
    def test_extension_variants(
        self, test_case: str, extension1: str, extension2: str
    ) -> None:
        """Test behavior with different variants of extensions."""
        color1 = generate_color_for_extension(extension1)
        color2 = generate_color_for_extension(extension2)
        assert isinstance(color1, str)
        assert isinstance(color2, str)
        assert color1.startswith("#")
        assert color2.startswith("#")
        if test_case == "case_sensitivity":
            assert color1 != color2
        else:
            assert color1 == color2

    def test_empty_extension(self) -> None:
        color = generate_color_for_extension("")
        assert color == "#FFFFFF"


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
        expected_indicator: Union[str, list[str]],
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
        mock_console = mocker.patch("recursivist.core.Console")
        mock_tree_class = mocker.patch("recursivist.core.Tree")
        mock_build_tree = mocker.patch("recursivist.core.build_tree")
        mock_get_structure = mocker.patch("recursivist.core.get_directory_structure")
        mock_get_structure.return_value = ({}, set())
        with open(os.path.join(temp_dir, "test.txt"), "w") as f:
            f.write("Test content")
        display_tree(temp_dir)
        mock_tree_class.assert_called_once()
        mock_console.return_value.print.assert_called_once()
        mock_build_tree.assert_called_once()

    def test_with_filtering_options(self, mocker: MockerFixture, temp_dir: str) -> None:
        mock_get_structure = mocker.patch("recursivist.core.get_directory_structure")
        mock_compile_regex = mocker.patch("recursivist.core.compile_regex_patterns")
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
        mock_tree = mocker.patch("recursivist.core.Tree")
        mock_get_structure = mocker.patch("recursivist.core.get_directory_structure")
        structure = {"_loc": 100, "_size": 10240, "_mtime": 1625097600.0, "_files": []}
        mock_get_structure.return_value = (structure, set())
        display_tree(temp_dir, sort_by_loc=True, sort_by_size=True, sort_by_mtime=True)
        args, _ = mock_tree.call_args
        root_label = args[0]
        assert "100 lines" in root_label
        assert "10.0 KB" in root_label
        date_formats = ["Today", "Yesterday", "Jul 1", "2021-07-01"]
        assert any(fmt in root_label for fmt in date_formats)


@pytest.mark.parametrize(
    "format_name,format_extension,expected_content",
    [
        ("json", "json", ["root", "structure"]),
        ("txt", "txt", ["file1.txt", "file2.py", "subdir"]),
        ("md", "md", ["# 📁", "file1.txt", "file2.py", "**subdir**"]),
        (
            "html",
            "html",
            ["<!DOCTYPE html>", "<html>", "file1.txt", "file2.py", "subdir"],
        ),
        (
            "jsx",
            "jsx",
            ["import React", "DirectoryViewer", "file1.txt", "file2.py", "subdir"],
        ),
    ],
)
def test_export_structure(
    sample_directory: Any,
    output_dir: str,
    format_name: str,
    format_extension: str,
    expected_content: list[str],
) -> None:
    """Test exporting structure to different formats."""
    structure, _ = get_directory_structure(sample_directory)
    output_path = os.path.join(output_dir, f"structure.{format_extension}")
    get_exporter(
        format_name, structure=structure, root_name=os.path.basename(sample_directory)
    ).export(output_path)
    assert os.path.exists(output_path)
    with open(output_path, encoding="utf-8") as f:
        content = f.read()
    for expected in expected_content:
        assert expected in content
    if format_name == "json":
        data = json.loads(content)
        assert "root" in data
        assert "structure" in data
        assert data["root"] == os.path.basename(sample_directory)
        assert "_files" in data["structure"]
    elif format_name == "html":
        assert "</html>" in content
    elif format_name == "jsx":
        assert "ChevronDown" in content
        assert "ChevronUp" in content


@pytest.mark.parametrize(
    "option_name,option_value",
    [
        ("show_full_path", True),
        ("sort_by_loc", True),
        ("sort_by_size", True),
        ("sort_by_mtime", True),
    ],
)
def test_export_structure_with_options(
    sample_directory: Any, output_dir: str, option_name: str, option_value: bool
) -> None:
    """Test exporting structure with various options."""
    exclude_dirs = None
    ignore_file = None
    exclude_extensions = None
    parent_ignore_patterns = None
    exclude_patterns = None
    include_patterns = None
    max_depth = 0
    current_depth = 0
    current_path = ""
    show_full_path = False
    sort_by_loc = False
    sort_by_size = False
    sort_by_mtime = False
    if option_name == "show_full_path":
        show_full_path = option_value
    elif option_name == "sort_by_loc":
        sort_by_loc = option_value
    elif option_name == "sort_by_size":
        sort_by_size = option_value
    elif option_name == "sort_by_mtime":
        sort_by_mtime = option_value
    elif option_name == "max_depth":
        max_depth = option_value
    structure, _ = get_directory_structure(
        sample_directory,
        exclude_dirs,
        ignore_file,
        exclude_extensions,
        parent_ignore_patterns,
        exclude_patterns,
        include_patterns,
        max_depth,
        current_depth,
        current_path,
        show_full_path,
        sort_by_loc,
        sort_by_size,
        sort_by_mtime,
    )
    output_path = os.path.join(output_dir, f"structure_{option_name}.json")

    kwargs: dict[str, Any] = {}
    if option_name == "show_full_path":
        kwargs["base_path"] = sample_directory if option_value else None
    elif option_name == "sort_by_loc":
        kwargs["sort_by_loc"] = option_value
    elif option_name == "sort_by_size":
        kwargs["sort_by_size"] = option_value
    elif option_name == "sort_by_mtime":
        kwargs["sort_by_mtime"] = option_value

    get_exporter(
        "json",
        structure=structure,
        root_name=os.path.basename(sample_directory),
        **kwargs,
    ).export(output_path)

    assert os.path.exists(output_path)
    with open(output_path, encoding="utf-8") as f:
        data = json.load(f)
    if option_name == "show_full_path":
        if "_files" in data["structure"]:
            has_full_path = False
            for file_item in data["structure"]["_files"]:
                if isinstance(file_item, dict) and "path" in file_item:
                    assert os.path.isabs(file_item["path"].replace("/", os.sep))
                    has_full_path = True
                    break
            assert has_full_path, "No full paths found in export"
    elif option_name in ["sort_by_loc", "sort_by_size", "sort_by_mtime"]:
        option_flag = f"show_{option_name[8:]}"
        assert option_flag in data
        assert data[option_flag] is True


def test_export_invalid_format(temp_dir: str, output_dir: str) -> None:
    """Test exporting with an invalid format."""
    structure = {"_files": ["file1.txt"]}
    output_path = os.path.join(output_dir, "test_export.invalid")
    with pytest.raises(ValueError) as excinfo:
        get_exporter(
            "invalid", structure=structure, root_name=os.path.basename(temp_dir)
        ).export(output_path)
    assert "Unsupported export format" in str(excinfo.value)


@pytest.mark.parametrize(
    "files,sort_key,expected_order",
    [
        (["c.txt", "b.py", "a.txt", "d.py"], None, ["b.py", "d.py", "a.txt", "c.txt"]),
        (
            [
                ("a.py", "/path/to/a.py", 5),
                ("b.py", "/path/to/b.py", 10),
                ("c.py", "/path/to/c.py", 3),
            ],
            "sort_by_loc",
            ["b.py", "a.py", "c.py"],
        ),
        (
            [
                ("a.py", "/path/to/a.py", 0, 1024),
                ("b.py", "/path/to/b.py", 0, 2048),
                ("c.py", "/path/to/c.py", 0, 512),
            ],
            "sort_by_size",
            ["b.py", "a.py", "c.py"],
        ),
    ],
)
def test_sort_files_by_type(
    files: list[Any], sort_key: Optional[str], expected_order: list[str]
) -> None:
    """Test sorting files by different criteria."""
    kwargs = {}
    if sort_key:
        kwargs[sort_key] = True
    sorted_files = sort_files_by_type(files, **kwargs)
    sorted_names = []
    for item in sorted_files:
        if isinstance(item, tuple):
            sorted_names.append(item[0])
        else:
            sorted_names.append(item)
    for i, expected_file in enumerate(expected_order):
        assert sorted_names[i] == expected_file, (
            f"Expected {expected_file} at position {i}, got {sorted_names[i]}"
        )


@pytest.mark.parametrize(
    "path,patterns,extensions,expected,exclude_patterns",
    [
        ("/test/app.log", ["*.log", "node_modules"], set(), True, None),
        ("/test/app.txt", ["*.log", "node_modules"], set(), False, None),
        ("/test/node_modules", ["*.log", "node_modules"], set(), True, None),
        ("/test/script.py", [], {".py", ".js"}, True, None),
        ("/test/app.js", [], {".py", ".js"}, True, None),
        ("/test/app.txt", [], {".py", ".js"}, False, None),
        ("/test/test_app.py", [], set(), True, [re.compile(r"test_.*\.py$")]),
        ("/test/app.log", [], set(), True, [re.compile(r"\.log$")]),
        ("/test/app.py", [], set(), False, [re.compile(r"test_.*\.py$")]),
    ],
)
def test_should_exclude(
    mocker: MockerFixture,
    path: str,
    patterns: list[str],
    extensions: set[str],
    expected: bool,
    exclude_patterns: Optional[list[Any]],
) -> None:
    """Test file exclusion logic."""
    mocker.patch("os.path.isfile", return_value=True)
    ignore_context = {"patterns": patterns, "current_dir": "/test"}
    kwargs = {}
    if exclude_patterns:
        kwargs["exclude_patterns"] = exclude_patterns
    result = should_exclude(
        path, ignore_context, exclude_extensions=extensions, **kwargs
    )
    assert result == expected, (
        f"Expected should_exclude('{path}') to return {expected}, got {result}"
    )


@pytest.mark.parametrize(
    "patterns,rel_path,is_dir,expected",
    [
        (["/build"], "build", True, True),
        (["/build"], "src/build", True, False),
        (["build"], "build", True, True),
        (["build"], "src/nested/build", True, True),
        (["src/build"], "src/build", True, True),
        (["src/build"], "build", True, False),
        (["src/build"], "other/src/build", True, False),
        (["build/"], "build", True, True),
        (["build/"], "build", False, False),
        (["*.log"], "foo.log", False, True),
        (["*.log"], "src/deep/foo.log", False, True),
        (["*.log"], "foo.log.txt", False, False),
        (["*.log", "!keep.log"], "keep.log", False, False),
        (["*.log", "!keep.log"], "other.log", False, True),
        (["!keep.log", "*.log"], "keep.log", False, True),
    ],
)
def test_should_exclude_gitignore_patterns(
    temp_dir: str,
    patterns: list[str],
    rel_path: str,
    is_dir: bool,
    expected: bool,
) -> None:
    """Gitignore-style matching in should_exclude: root-relative anchoring,
    directory-only markers, '*' not crossing '/', and order-sensitive negation."""
    target, current_dir, rel_dir = _make_entry(temp_dir, rel_path, is_dir)
    ignore_context = {
        "patterns": patterns,
        "current_dir": current_dir,
        "rel_dir": rel_dir,
    }
    assert should_exclude(target, ignore_context) is expected


@pytest.mark.parametrize(
    "ignore_patterns,exclude_patterns,exclude_extensions,include_patterns,rel_path,expected",
    [
        (["*.log", "!keep.log"], None, None, None, "keep.log", False),
        (["*.log", "!keep.log"], ["keep.log"], None, None, "keep.log", True),
        (["*.log", "!keep.log"], ["*.log"], None, None, "keep.log", True),
        (["*.log", "!keep.log"], None, {".log"}, None, "keep.log", True),
        (["*.log"], None, None, ["*.log"], "keep.log", False),
        (["!keep.log"], None, None, ["*.md"], "keep.log", True),
    ],
)
def test_should_exclude_filter_precedence(
    temp_dir: str,
    ignore_patterns: list[str],
    exclude_patterns: Optional[list[str]],
    exclude_extensions: Optional[set[str]],
    include_patterns: Optional[list[str]],
    rel_path: str,
    expected: bool,
) -> None:
    """CLI excludes and excluded extensions take priority over the gitignore
    stage, and include_patterns bypasses it; the gitignore negation only decides
    the outcome when no higher-priority filter applies."""
    target, current_dir, rel_dir = _make_entry(temp_dir, rel_path, is_dir=False)
    ignore_context = {
        "patterns": ignore_patterns,
        "current_dir": current_dir,
        "rel_dir": rel_dir,
    }
    result = should_exclude(
        target,
        ignore_context,
        exclude_extensions=exclude_extensions,
        exclude_patterns=exclude_patterns,
        include_patterns=include_patterns,
    )
    assert result is expected


@pytest.mark.parametrize(
    "ignore_patterns,rel_path,is_dir,expected",
    [
        (["doc/**/*.txt"], "doc/a.txt", False, True),
        (["doc/**/*.txt"], "doc/sub/deep/a.txt", False, True),
        (["doc/**/*.txt"], "doc/a.md", False, False),
        (["doc/**/*.txt"], "src/doc/a.txt", False, False),
        (["doc/**/*.txt"], "doc/sub", True, False),
        (["**/build"], "build", True, True),
        (["**/build"], "a/b/build", True, True),
    ],
)
def test_should_exclude_double_star(
    temp_dir: str,
    ignore_patterns: list[str],
    rel_path: str,
    is_dir: bool,
    expected: bool,
) -> None:
    """'**' spans directory boundaries: 'doc/**/*.txt' matches at any depth under
    doc/, '**/foo' floats a name anywhere, and intermediate directories are not
    incidentally matched."""
    target, current_dir, rel_dir = _make_entry(temp_dir, rel_path, is_dir=is_dir)
    ignore_context = {
        "patterns": ignore_patterns,
        "current_dir": current_dir,
        "rel_dir": rel_dir,
    }
    assert should_exclude(target, ignore_context) is expected


@pytest.mark.parametrize(
    "patterns,is_regex,expected_count,expected_types",
    [
        (["*.py", "test_*"], False, 2, [str, str]),
        ([r"\.py$", r"^test_"], True, 2, [re.Pattern, re.Pattern]),
        ([r"[invalid", r"(unclosed"], True, 2, [str, str]),
        ([], False, 0, []),
        ([], True, 0, []),
    ],
)
def test_compile_regex_patterns(
    patterns: list[str],
    is_regex: bool,
    expected_count: int,
    expected_types: list[type[Any]],
) -> None:
    """Test compiling regex patterns."""
    compiled = compile_regex_patterns(patterns, is_regex=is_regex)
    assert len(compiled) == expected_count
    for i, pattern_type in enumerate(expected_types):
        assert isinstance(compiled[i], pattern_type)


@pytest.mark.parametrize(
    "content,expected_patterns",
    [
        (
            "# This is a comment\n*.log\n\nnode_modules/\ndist\n# Another comment\n",
            ["*.log", "node_modules/", "dist"],
        ),
        ("", []),
        (
            "# Logs\n*.log\nlogs/\n!important.log\n# Directories\nnode_modules/\ndist/\n",
            ["*.log", "logs/", "!important.log", "node_modules/", "dist/"],
        ),
    ],
)
def test_parse_ignore_file(
    temp_dir: str, content: str, expected_patterns: list[str]
) -> None:
    """Test parsing ignore files."""
    ignore_path = os.path.join(temp_dir, ".testignore")
    with open(ignore_path, "w") as f:
        f.write(content)
    patterns = parse_ignore_file(ignore_path)
    assert set(patterns) == set(expected_patterns)


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


def _make_entry(base_dir: str, rel_path: str, is_dir: bool) -> tuple[str, str, str]:
    """Create *rel_path* (relative to a fresh scan root under *base_dir*) on disk
    and return ``(path, current_dir, rel_dir)`` exactly as get_directory_structure
    would hand them to should_exclude for a direct child entry.

    A fresh scan root per call keeps the cases order- and fixture-scope-independent
    (so a dir named ``build`` in one case can't collide with a file named ``build``
    in another).
    """
    scan_root = tempfile.mkdtemp(dir=base_dir)
    rel_path = rel_path.replace("/", os.sep)
    parent_rel, name = os.path.split(rel_path)
    parent = os.path.join(scan_root, parent_rel) if parent_rel else scan_root
    os.makedirs(parent, exist_ok=True)
    target = os.path.join(parent, name)
    if is_dir:
        os.makedirs(target, exist_ok=True)
    else:
        with open(target, "w") as fh:
            fh.write("x")
    return target, parent, parent_rel


def _materialize_tree(root: str, files: dict[str, str]) -> None:
    """Create each file (keyed by '/'-separated relative path) under *root*,
    making intermediate directories as needed."""
    for rel, content in files.items():
        path = os.path.join(root, *rel.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(content)


def _normalize_structure(structure: dict) -> dict:
    """Make a get_directory_structure result comparable: '_files' lists become
    sets of names (order from os.listdir isn't stable), and subdirectories are
    normalized recursively."""
    normalized: dict = {}
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
