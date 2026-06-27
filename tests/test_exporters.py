"""Tests for recursivist.exporters: get_exporter and the per-format exporters (including Jsx)."""

import json
import os
import random
import re
import string
import tempfile
import time
import unittest.mock
from collections.abc import Callable
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pytest_mock import MockerFixture

from recursivist._models import FileEntry
from recursivist.exporters import get_exporter
from recursivist.exporters.jsx import (
    sort_key_all,
    sort_key_loc,
    sort_key_loc_mtime,
    sort_key_loc_size,
    sort_key_mtime,
    sort_key_name,
    sort_key_size,
    sort_key_size_mtime,
)
from recursivist.scanner import get_directory_structure


@st.composite
def file_tuples_for_sorting(draw: st.DrawFn) -> Any:
    """Generate various file tuple formats for testing sorting functions."""
    filename = draw(
        st.text(
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Nd"),
                whitelist_characters="_-",
            ),
            min_size=1,
            max_size=20,
        ).flatmap(
            lambda s: st.sampled_from(
                [".txt", ".py", ".md", ".json", ".js", ".html", ".css"]
            ).map(lambda ext: s + ext)
        )
    )
    tuple_type = draw(st.integers(min_value=0, max_value=4))
    if tuple_type == 0:
        return filename
    elif tuple_type == 1:
        path = draw(st.text(min_size=1, max_size=100))
        return (filename, path)
    elif tuple_type == 2:
        path = draw(st.text(min_size=1, max_size=100))
        loc = draw(st.integers(min_value=0, max_value=1000))
        return (filename, path, loc)
    elif tuple_type == 3:
        path = draw(st.text(min_size=1, max_size=100))
        loc = draw(st.integers(min_value=0, max_value=1000))
        size = draw(st.integers(min_value=0, max_value=10 * 1024 * 1024))
        return (filename, path, loc, size)
    else:
        path = draw(st.text(min_size=1, max_size=100))
        loc = draw(st.integers(min_value=0, max_value=1000))
        size = draw(st.integers(min_value=0, max_value=10 * 1024 * 1024))
        mtime = draw(st.floats(min_value=0, max_value=1672531200))
        return (filename, path, loc, size, mtime)


file_tuple_list = st.lists(
    file_tuples_for_sorting(),
    min_size=1,
    max_size=20,
)


@st.composite
def jsx_directory_structure(draw: st.DrawFn) -> Any:
    """Generate a simplified directory structure suitable for JSX component testing."""
    structure = {}
    structure["_files"] = draw(
        st.lists(
            st.one_of(
                st.text(
                    alphabet=st.characters(
                        whitelist_categories=("Lu", "Ll", "Nd"),
                        whitelist_characters="_-",
                    ),
                    min_size=1,
                    max_size=20,
                ).flatmap(
                    lambda s: st.sampled_from(
                        [".txt", ".py", ".md", ".json", ".js", ".html", ".css"]
                    ).map(lambda ext: s + ext)
                ),
                st.tuples(
                    st.text(
                        alphabet=st.characters(
                            whitelist_categories=("Lu", "Ll", "Nd"),
                            whitelist_characters="_-",
                        ),
                        min_size=1,
                        max_size=20,
                    ).flatmap(
                        lambda s: st.sampled_from(
                            [".txt", ".py", ".md", ".json", ".js", ".html", ".css"]
                        ).map(lambda ext: s + ext)
                    ),
                    st.text(min_size=1, max_size=100),
                ),
            ),
            min_size=0,
            max_size=10,
        )
    )
    if draw(st.booleans()):
        subdir_name = draw(
            st.text(
                alphabet=st.characters(
                    whitelist_categories=("Lu", "Ll", "Nd"),
                    whitelist_characters="_-",
                ),
                min_size=1,
                max_size=10,
            )
        )
        structure[subdir_name] = draw(jsx_directory_structure())
    return structure


def generate_large_structure(
    depth: int, files_per_dir: int, dir_branching: int
) -> dict[str, Any]:
    """Generate a large directory structure for testing."""

    def _generate_recursive(current_depth: int) -> dict[str, Any]:
        if current_depth > depth:
            return {}
        structure: dict[str, Any] = {}
        structure["_files"] = []
        for i in range(files_per_dir):
            file_name = f"file_{current_depth}_{i}.txt"
            structure["_files"].append(file_name)
        if current_depth < depth:
            for i in range(dir_branching):
                dir_name = f"dir_{current_depth}_{i}"
                structure[dir_name] = _generate_recursive(current_depth + 1)
        return structure

    return _generate_recursive(1)


def random_string(length: int) -> str:
    """Generate a random string of specified length."""
    return "".join(random.choice(string.ascii_letters) for _ in range(length))


class TestJSXSort:
    """Property-based tests for the module-level sort keys in recursivist.exporters.jsx.

    Each test builds FileEntry objects the way JsxExporter does, sorts them with
    the real sort-key function, and asserts the resulting order respects that key.
    """

    @staticmethod
    def _entries(files: list[str | tuple[Any, ...]]) -> list[FileEntry]:
        """Build FileEntry objects as JsxExporter does before sorting."""
        return [
            FileEntry.from_raw(f, True, True, True)
            for f in files
            if not (isinstance(f, tuple) and len(f) == 0)
        ]

    @given(files=file_tuple_list)
    @settings(max_examples=100)
    def test_sort_key_all(self, files: list[str | tuple[Any, ...]]) -> None:
        """sort_key_all orders by LOC, size, then mtime (all descending), then name."""
        entries = self._entries(files)
        sorted_files = sorted(entries, key=sort_key_all)
        assert len(sorted_files) == len(entries), "Sorting should preserve all elements"
        assert sorted(sorted_files, key=sort_key_all) == sorted_files, (
            "Sorting should be stable"
        )
        for i in range(len(sorted_files) - 1):
            assert sort_key_all(sorted_files[i]) <= sort_key_all(sorted_files[i + 1]), (
                "Keys should be in sorted order"
            )

    @given(files=file_tuple_list)
    @settings(max_examples=100)
    def test_sort_key_loc_size(self, files: list[str | tuple[Any, ...]]) -> None:
        """sort_key_loc_size orders by LOC, then size (descending), then name."""
        entries = self._entries(files)
        sorted_files = sorted(entries, key=sort_key_loc_size)
        assert len(sorted_files) == len(entries), "Sorting should preserve all elements"
        assert sorted(sorted_files, key=sort_key_loc_size) == sorted_files, (
            "Sorting should be stable"
        )
        for i in range(len(sorted_files) - 1):
            assert sort_key_loc_size(sorted_files[i]) <= sort_key_loc_size(
                sorted_files[i + 1]
            ), "Keys should be in sorted order"

    @given(files=file_tuple_list)
    @settings(max_examples=100)
    def test_sort_key_loc_mtime(self, files: list[str | tuple[Any, ...]]) -> None:
        """sort_key_loc_mtime orders by LOC, then mtime (descending), then name."""
        entries = self._entries(files)
        sorted_files = sorted(entries, key=sort_key_loc_mtime)
        assert len(sorted_files) == len(entries), "Sorting should preserve all elements"
        assert sorted(sorted_files, key=sort_key_loc_mtime) == sorted_files, (
            "Sorting should be stable"
        )
        for i in range(len(sorted_files) - 1):
            assert sort_key_loc_mtime(sorted_files[i]) <= sort_key_loc_mtime(
                sorted_files[i + 1]
            ), "Keys should be in sorted order"

    @given(files=file_tuple_list)
    @settings(max_examples=100)
    def test_sort_key_size_mtime(self, files: list[str | tuple[Any, ...]]) -> None:
        """sort_key_size_mtime orders by size, then mtime (descending), then name."""
        entries = self._entries(files)
        sorted_files = sorted(entries, key=sort_key_size_mtime)
        assert len(sorted_files) == len(entries), "Sorting should preserve all elements"
        assert sorted(sorted_files, key=sort_key_size_mtime) == sorted_files, (
            "Sorting should be stable"
        )
        for i in range(len(sorted_files) - 1):
            assert sort_key_size_mtime(sorted_files[i]) <= sort_key_size_mtime(
                sorted_files[i + 1]
            ), "Keys should be in sorted order"

    @given(files=file_tuple_list)
    @settings(max_examples=100)
    def test_sort_key_mtime(self, files: list[str | tuple[Any, ...]]) -> None:
        """sort_key_mtime orders by mtime (descending), then name."""
        entries = self._entries(files)
        sorted_files = sorted(entries, key=sort_key_mtime)
        assert len(sorted_files) == len(entries), "Sorting should preserve all elements"
        assert sorted(sorted_files, key=sort_key_mtime) == sorted_files, (
            "Sorting should be stable"
        )
        for i in range(len(sorted_files) - 1):
            assert sort_key_mtime(sorted_files[i]) <= sort_key_mtime(
                sorted_files[i + 1]
            ), "Keys should be in sorted order"

    @given(files=file_tuple_list)
    @settings(max_examples=100)
    def test_sort_key_size(self, files: list[str | tuple[Any, ...]]) -> None:
        """sort_key_size orders by size (descending), then name."""
        entries = self._entries(files)
        sorted_files = sorted(entries, key=sort_key_size)
        assert len(sorted_files) == len(entries), "Sorting should preserve all elements"
        assert sorted(sorted_files, key=sort_key_size) == sorted_files, (
            "Sorting should be stable"
        )
        for i in range(len(sorted_files) - 1):
            assert sort_key_size(sorted_files[i]) <= sort_key_size(
                sorted_files[i + 1]
            ), "Keys should be in sorted order"

    @given(files=file_tuple_list)
    @settings(max_examples=100)
    def test_sort_key_loc(self, files: list[str | tuple[Any, ...]]) -> None:
        """sort_key_loc orders by LOC (descending), then name."""
        entries = self._entries(files)
        sorted_files = sorted(entries, key=sort_key_loc)
        assert len(sorted_files) == len(entries), "Sorting should preserve all elements"
        assert sorted(sorted_files, key=sort_key_loc) == sorted_files, (
            "Sorting should be stable"
        )
        for i in range(len(sorted_files) - 1):
            assert sort_key_loc(sorted_files[i]) <= sort_key_loc(sorted_files[i + 1]), (
                "Keys should be in sorted order"
            )

    @given(files=file_tuple_list)
    @settings(max_examples=100)
    def test_sort_key_name(self, files: list[str | tuple[Any, ...]]) -> None:
        """sort_key_name orders by name (case-insensitive, ascending)."""
        entries = self._entries(files)
        sorted_files = sorted(entries, key=sort_key_name)
        assert len(sorted_files) == len(entries), "Sorting should preserve all elements"
        assert sorted(sorted_files, key=sort_key_name) == sorted_files, (
            "Sorting should be stable"
        )
        for i in range(len(sorted_files) - 1):
            assert sort_key_name(sorted_files[i]) <= sort_key_name(
                sorted_files[i + 1]
            ), "Keys should be in sorted order"


class TestJSXComponent:
    """Test the JSX component generation functionality using the Factory Exporter."""

    @given(
        dir_structure=jsx_directory_structure(),
        root_name=st.text(min_size=1, max_size=20),
    )
    @settings(max_examples=20)
    def test_export_jsx_basics(
        self, dir_structure: dict[str, Any], root_name: str
    ) -> None:
        """Test basic generation of JSX component."""
        with unittest.mock.patch(
            "builtins.open", unittest.mock.mock_open()
        ) as mock_open:
            get_exporter(
                "jsx",
                structure=dir_structure,
                root_name=root_name,
            ).export("output.jsx")
            mock_open.assert_called_once_with("output.jsx", "w", encoding="utf-8")
            mock_file = mock_open()
            assert mock_file.write.call_count > 0, "No data was written to the file"

    @given(
        dir_structure=jsx_directory_structure(),
        root_name=st.text(
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Nd"),
                whitelist_characters="_-",
            ),
            min_size=1,
            max_size=20,
        ),
    )
    @settings(max_examples=5)
    def test_jsx_end_to_end(
        self, dir_structure: dict[str, Any], root_name: str
    ) -> None:
        """Test end-to-end JSX component generation with temporary file."""
        with tempfile.NamedTemporaryFile(suffix=".jsx", delete=False) as temp_file:
            output_path = temp_file.name
        try:
            get_exporter(
                "jsx",
                structure=dir_structure,
                root_name=root_name,
            ).export(output_path)

            assert os.path.exists(output_path), "The JSX file was not created"
            assert os.path.getsize(output_path) > 0, "The JSX file is empty"
            with open(output_path, encoding="utf-8") as f:
                content = f.read()
            assert "import React" in content, "JSX should import React"
            assert "export default DirectoryViewer" in content, (
                "JSX should export the DirectoryViewer component"
            )
            assert root_name in content, "JSX should include the root name"
            assert "const DirectoryViewer = () =>" in content, (
                "DirectoryViewer component should be defined"
            )
            assert "const DirectoryItem = (props) =>" in content, (
                "DirectoryItem component should be defined"
            )
            assert "const FileItem = (props) =>" in content, (
                "FileItem component should be defined"
            )
            if "_files" in dir_structure and dir_structure["_files"]:
                for file_item in dir_structure["_files"]:
                    if isinstance(file_item, tuple):
                        file_name = file_item[0]
                    else:
                        file_name = file_item
                    assert file_name in content, (
                        f"File {file_name} should be included in JSX content"
                    )
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @given(
        dir_structure=jsx_directory_structure(),
        root_name=st.text(min_size=1, max_size=20),
        show_full_path=st.booleans(),
        sort_by_loc=st.booleans(),
        sort_by_size=st.booleans(),
        sort_by_mtime=st.booleans(),
    )
    @settings(max_examples=10)
    def test_jsx_options(
        self,
        dir_structure: dict[str, Any],
        root_name: str,
        show_full_path: bool,
        sort_by_loc: bool,
        sort_by_size: bool,
        sort_by_mtime: bool,
    ) -> None:
        """Test JSX generation with various options."""
        with unittest.mock.patch(
            "builtins.open", unittest.mock.mock_open()
        ) as mock_open:
            get_exporter(
                "jsx",
                structure=dir_structure,
                root_name=root_name,
                base_path="base/path" if show_full_path else None,
                sort_by_loc=sort_by_loc,
                sort_by_size=sort_by_size,
                sort_by_mtime=sort_by_mtime,
            ).export("output.jsx")

            mock_open.assert_called_once_with("output.jsx", "w", encoding="utf-8")
            mock_file = mock_open()
            write_calls = [args[0] for args, _ in mock_file.write.call_args_list]
            content = "".join(write_calls)
            if sort_by_loc:
                assert "const showLoc = true;" in content, (
                    "LOC display should be enabled"
                )
                assert "const sortByLoc = true;" in content, (
                    "LOC sorting should be enabled"
                )
            else:
                assert "const showLoc = false;" in content, (
                    "LOC display should be disabled"
                )
                assert "const sortByLoc = false;" in content, (
                    "LOC sorting should be disabled"
                )
            if sort_by_size:
                assert "const showSize = true;" in content, (
                    "Size display should be enabled"
                )
                assert "const sortBySize = true;" in content, (
                    "Size sorting should be enabled"
                )
                assert "format_size" in content, (
                    "Size formatting function should be included"
                )
            else:
                assert "const showSize = false;" in content, (
                    "Size display should be disabled"
                )
                assert "const sortBySize = false;" in content, (
                    "Size sorting should be disabled"
                )
            if sort_by_mtime:
                assert "const showMtime = true;" in content, (
                    "Mtime display should be enabled"
                )
                assert "const sortByMtime = true;" in content, (
                    "Mtime sorting should be enabled"
                )
                assert "format_timestamp" in content, (
                    "Timestamp formatting function should be included"
                )
            else:
                assert "const showMtime = false;" in content, (
                    "Mtime display should be disabled"
                )
                assert "const sortByMtime = false;" in content, (
                    "Mtime sorting should be disabled"
                )


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


def test_get_exporter_invalid_format(temp_dir: str, output_dir: str) -> None:
    """Test exporting with an invalid format."""
    structure = {"_files": ["file1.txt"]}
    output_path = os.path.join(output_dir, "test_export.invalid")
    with pytest.raises(ValueError) as excinfo:
        get_exporter(
            "invalid", structure=structure, root_name=os.path.basename(temp_dir)
        ).export(output_path)
    assert "Unsupported export format" in str(excinfo.value)


class TestJsxExporter:
    """Property-based tests for JsxExporter.export method."""

    def test_export_basic(self) -> None:
        """Basic test for export without property testing."""
        structure = {"_files": ["file1.txt"]}
        root_name = "test_root"
        with patch("builtins.open", MagicMock()) as mock_open:
            exporter = get_exporter("jsx", structure=structure, root_name=root_name)
            output_path = "test_output.jsx"
            exporter.export(output_path)
            mock_open.assert_called_once_with(output_path, "w", encoding="utf-8")

    def test_export_with_options_basic(self) -> None:
        """Basic test for export with options, without property testing."""
        structure = {"_files": ["file1.txt"]}
        root_name = "test_root"
        option_combinations = [
            (False, False, False),
            (True, False, False),
            (False, True, False),
            (False, False, True),
            (True, True, False),
            (True, False, True),
            (False, True, True),
            (True, True, True),
        ]
        for sort_by_loc, sort_by_size, sort_by_mtime in option_combinations:
            with patch("builtins.open", MagicMock()) as mock_open:
                exporter = get_exporter(
                    "jsx",
                    structure=structure,
                    root_name=root_name,
                    base_path=(
                        "base/path"
                        if any([sort_by_loc, sort_by_size, sort_by_mtime])
                        else None
                    ),
                    sort_by_loc=sort_by_loc,
                    sort_by_size=sort_by_size,
                    sort_by_mtime=sort_by_mtime,
                )
                output_path = "test_output.jsx"
                exporter.export(output_path)
                mock_open.assert_called_once_with(output_path, "w", encoding="utf-8")


class TestJsxExporterFileWriting:
    """Tests for JsxExporter file writing."""

    def test_generate_jsx_component_basic(self) -> None:
        """Basic test for JsxExporter without property testing."""
        structure = {"_files": ["file1.txt"]}
        root_name = "test_root"
        with patch("builtins.open", MagicMock()) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            get_exporter("jsx", structure=structure, root_name=root_name).export(
                "output.jsx"
            )

            mock_open.assert_called_once_with("output.jsx", "w", encoding="utf-8")
            assert mock_file.write.call_count > 0, "No data was written to the file"


class TestExporterFileOutput:
    @pytest.mark.parametrize(
        "format_name,expected_content",
        [
            ("txt", ["📁 test_root", "file1.txt", "file2.py", "file3.md"]),
            ("md", ["# 📁 test_root", "`file1.txt`"]),
            (
                "html",
                ["<!DOCTYPE html>", "<html>", 'class="file"'],
            ),
            ("json", ["root", "structure", "_files"]),
        ],
    )
    def test_export_formats(
        self,
        simple_structure: dict[str, Any],
        tmp_path: Path,
        format_name: str,
        expected_content: list[str],
    ) -> None:
        """Test Exporter format-specific exports."""
        output_path = os.path.join(tmp_path, f"test_output.{format_name}")
        get_exporter(
            format_name, structure=simple_structure, root_name="test_root"
        ).export(output_path)

        assert os.path.exists(output_path)
        with open(output_path, encoding="utf-8") as f:
            content = f.read()
        for expected in expected_content:
            assert expected in content

    def test_export_with_directories(
        self, nested_structure: dict[str, Any], tmp_path: Path
    ) -> None:
        """Test that directories are properly formatted in exports."""
        md_output_path = os.path.join(tmp_path, "test_dirs.md")
        get_exporter("md", structure=nested_structure, root_name="test_root").export(
            md_output_path
        )
        with open(md_output_path, encoding="utf-8") as f:
            md_content = f.read()
        assert "**subdir1**" in md_content or "**subdir2**" in md_content

        html_output_path = os.path.join(tmp_path, "test_dirs.html")
        get_exporter("html", structure=nested_structure, root_name="test_root").export(
            html_output_path
        )
        with open(html_output_path, encoding="utf-8") as f:
            html_content = f.read()
        assert 'class="directory"' in html_content

    @pytest.mark.parametrize(
        "option_name,option_value,expected_in_content",
        [
            ("sort_by_loc", True, "lines"),
            ("sort_by_size", True, ["B", "KB", "MB"]),
            ("sort_by_mtime", True, ["Today", "Yesterday"]),
        ],
    )
    def test_export_with_statistics(
        self,
        structure_with_stats: dict[str, Any],
        tmp_path: Path,
        option_name: str,
        option_value: bool,
        expected_in_content: str | list[str],
    ) -> None:
        """Test exporting with statistics options."""
        output_path = os.path.join(tmp_path, f"test_output_{option_name}.txt")
        kwargs: dict[str, Any] = {option_name: option_value}

        get_exporter(
            "txt", structure=structure_with_stats, root_name="test_root", **kwargs
        ).export(output_path)

        assert os.path.exists(output_path)
        with open(output_path, encoding="utf-8") as f:
            content = f.read()
        if isinstance(expected_in_content, list):
            assert any(expected in content for expected in expected_in_content), (
                f"None of {expected_in_content} found in export"
            )
        else:
            assert expected_in_content in content, (
                f"{expected_in_content} not found in export"
            )

    def test_export_with_full_path(
        self, structure_with_stats: dict[str, Any], tmp_path: Path
    ) -> None:
        """Test exporting with full file paths."""
        output_path = os.path.join(tmp_path, "test_output_fullpath.txt")
        get_exporter(
            "txt",
            structure=structure_with_stats,
            root_name="test_root",
            base_path="/path/to",
        ).export(output_path)

        with open(output_path, encoding="utf-8") as f:
            content = f.read()
        assert "/path/to/" in content

    @pytest.mark.parametrize(
        "error_type,error_msg",
        [
            (PermissionError, "Permission denied"),
            (OSError, "No space left on device"),
        ],
    )
    def test_export_error_handling(
        self,
        simple_structure: dict[str, Any],
        tmp_path: Path,
        error_type: type[Exception],
        error_msg: str,
    ) -> None:
        """Test error handling during export."""
        output_path = os.path.join(tmp_path, "test_output.txt")
        exporter = get_exporter(
            "txt", structure=simple_structure, root_name="test_root"
        )
        error: Exception
        if error_type is OSError:
            error = OSError(28, error_msg)
        else:
            error = error_type(error_msg)
        with patch("builtins.open", side_effect=error):
            with pytest.raises(Exception) as excinfo:
                exporter.export(output_path)
            assert error_msg in str(excinfo.value)

    def test_export_with_max_depth(
        self, max_depth_structure: dict[str, Any], tmp_path: Path
    ) -> None:
        """Test exporting with max depth indicators."""
        txt_path = os.path.join(tmp_path, "max_depth.txt")
        get_exporter(
            "txt", structure=max_depth_structure, root_name="max_depth_root"
        ).export(txt_path)
        with open(txt_path, encoding="utf-8") as f:
            content = f.read()
        assert "⋯ (max depth reached)" in content

        md_path = os.path.join(tmp_path, "max_depth.md")
        get_exporter(
            "md", structure=max_depth_structure, root_name="max_depth_root"
        ).export(md_path)
        with open(md_path, encoding="utf-8") as f:
            content = f.read()
        assert "⋯ *(max depth reached)*" in content

        html_path = os.path.join(tmp_path, "max_depth.html")
        get_exporter(
            "html", structure=max_depth_structure, root_name="max_depth_root"
        ).export(html_path)
        with open(html_path, encoding="utf-8") as f:
            content = f.read()
        assert "max-depth" in content

    def test_jsx_export(self, nested_structure: dict[str, Any], tmp_path: Path) -> None:
        """Test JSX export output matches expected basic structure."""
        output_path = os.path.join(tmp_path, "test_output.jsx")

        get_exporter("jsx", structure=nested_structure, root_name="test_root").export(
            output_path
        )
        assert os.path.exists(output_path)
        with open(output_path, encoding="utf-8") as f:
            content = f.read()
        assert "import React" in content

        get_exporter(
            "jsx",
            structure=nested_structure,
            root_name="test_root",
            sort_by_loc=True,
            sort_by_size=True,
            sort_by_mtime=True,
        ).export(output_path)
        assert os.path.exists(output_path)
        with open(output_path, encoding="utf-8") as f:
            content = f.read()
        assert "import React" in content


class TestExporters:
    def test_init(self) -> None:
        """Test initializing an exporter through the factory."""
        structure = {"_files": ["file1.txt"], "dir1": {"_files": ["file2.py"]}}
        exporter = get_exporter("txt", structure=structure, root_name="test_root")
        assert exporter.structure == structure
        assert exporter.root_name == "test_root"
        assert exporter.base_path is None
        assert not exporter.show_full_path

    def test_init_with_full_path(self) -> None:
        """Test initializing an exporter with full paths."""
        structure = {
            "_files": [("file1.txt", "/path/to/file1.txt")],
            "dir1": {"_files": [("file2.py", "/path/to/dir1/file2.py")]},
        }
        exporter = get_exporter(
            "txt", structure=structure, root_name="test_root", base_path="/path/to"
        )
        assert exporter.structure == structure
        assert exporter.root_name == "test_root"
        assert exporter.base_path == "/path/to"
        assert exporter.show_full_path

    def test_init_with_statistics(self) -> None:
        """Test initializing an exporter with statistics."""
        now = time.time()
        structure = {
            "_loc": 100,
            "_size": 1024,
            "_mtime": now,
            "_files": [("file1.txt", "/path/to/file1.txt", 50, 512, now)],
            "dir1": {
                "_loc": 50,
                "_size": 512,
                "_mtime": now,
                "_files": [("file2.py", "/path/to/dir1/file2.py", 50, 512, now)],
            },
        }
        exporter = get_exporter(
            "txt",
            structure=structure,
            root_name="test_root",
            base_path="/path/to",
            sort_by_loc=True,
            sort_by_size=True,
            sort_by_mtime=True,
        )
        assert exporter.sort_by_loc
        assert exporter.sort_by_size
        assert exporter.sort_by_mtime


@pytest.mark.parametrize(
    "format_name,format_extension,content_checks",
    [
        (
            "txt",
            "txt",
            [
                lambda c: "file1.txt" in c,
                lambda c: "file2.py" in c,
                lambda c: "subdir" in c,
            ],
        ),
        (
            "json",
            "json",
            [
                lambda c: '"root":' in c,
                lambda c: '"structure":' in c,
                lambda c: '"_files":' in c,
            ],
        ),
        (
            "md",
            "md",
            [
                lambda c: "# 📁" in c,
                lambda c: "- 📄 `file1.txt`" in c,
                lambda c: "- 📁 **subdir**" in c,
            ],
        ),
        (
            "html",
            "html",
            [
                lambda c: "<!DOCTYPE html>" in c,
                lambda c: "<html>" in c,
                lambda c: "</html>" in c,
                lambda c: 'class="file"' in c,
                lambda c: 'class="directory"' in c,
            ],
        ),
        (
            "jsx",
            "jsx",
            [
                lambda c: "import React" in c,
                lambda c: "DirectoryViewer" in c,
                lambda c: "ChevronDown" in c,
                lambda c: "ChevronUp" in c,
            ],
        ),
    ],
)
def test_export_formats(
    sample_directory: str,
    output_dir: str,
    format_name: str,
    format_extension: str,
    content_checks: list[Callable[[str], bool]],
) -> None:
    """Test exporting to different formats."""
    structure, _ = get_directory_structure(sample_directory)
    output_path = os.path.join(output_dir, f"structure.{format_extension}")

    exporter = get_exporter(
        format_name,
        structure=structure,
        root_name=os.path.basename(sample_directory),
    )
    exporter.export(output_path)

    assert os.path.exists(output_path)
    with open(output_path, encoding="utf-8") as f:
        content = f.read()
    assert os.path.basename(sample_directory) in content
    for check in content_checks:
        assert check(content), "Content check failed"
    if format_name == "json":
        data = json.loads(content)
        assert "root" in data
        assert "structure" in data
        assert data["root"] == os.path.basename(sample_directory)
        file_names = data["structure"]["_files"]
        assert "file1.txt" in file_names
        assert "file2.py" in file_names
        assert "subdir" in data["structure"]


@pytest.mark.parametrize(
    "option_name,option_value,content_check",
    [
        (
            "show_full_path",
            True,
            lambda c, d: any(
                [
                    os.path.join(d, "file1.txt").replace(os.sep, "/") in c,
                    os.path.join(d, "file2.py").replace(os.sep, "/") in c,
                ]
            ),
        ),
        ("sort_by_loc", True, lambda c, d: "lines" in c),
        (
            "sort_by_size",
            True,
            lambda c, d: any(unit in c for unit in ["B", "KB", "MB"]),
        ),
        (
            "sort_by_mtime",
            True,
            lambda c, d: (
                any(indicator in c for indicator in ["Today", "Yesterday"])
                or re.search(r"\d{4}-\d{2}-\d{2}", c)
            ),
        ),
    ],
)
def test_export_with_options(
    sample_directory: str,
    output_dir: str,
    option_name: str,
    option_value: bool,
    content_check: Callable[[str, str], bool],
) -> None:
    """Test exporting with various options."""
    get_structure_kwargs = {}
    if option_name in [
        "show_full_path",
        "sort_by_loc",
        "sort_by_size",
        "sort_by_mtime",
    ]:
        get_structure_kwargs[option_name] = option_value

    structure, _ = get_directory_structure(sample_directory, **get_structure_kwargs)
    output_path = os.path.join(output_dir, f"structure_{option_name}.txt")

    kwargs = {}
    if option_name == "show_full_path":
        kwargs["base_path"] = sample_directory if option_value else None
    elif option_name in ["sort_by_loc", "sort_by_size", "sort_by_mtime"]:
        kwargs[option_name] = option_value

    exporter = get_exporter(
        "txt",
        structure=structure,
        root_name=os.path.basename(sample_directory),
        **kwargs,
    )
    exporter.export(output_path)

    assert os.path.exists(output_path)
    with open(output_path, encoding="utf-8") as f:
        content = f.read()
    assert content_check(content, sample_directory), (
        f"Content check failed for option {option_name}"
    )


def test_export_nested_structure(sample_directory: str, output_dir: str) -> None:
    """Test exporting nested directory structure."""
    nested_dir = os.path.join(sample_directory, "nested", "deep")
    os.makedirs(nested_dir, exist_ok=True)
    with open(os.path.join(nested_dir, "deep_file.txt"), "w") as f:
        f.write("Deep nested file")

    structure, _ = get_directory_structure(sample_directory)
    output_path = os.path.join(output_dir, "nested_structure.json")

    get_exporter(
        "json",
        structure=structure,
        root_name=os.path.basename(sample_directory),
    ).export(output_path)

    with open(output_path, encoding="utf-8") as f:
        data = json.load(f)
    assert "nested" in data["structure"]
    assert "deep" in data["structure"]["nested"]
    assert "_files" in data["structure"]["nested"]["deep"]
    assert "deep_file.txt" in data["structure"]["nested"]["deep"]["_files"]


def test_export_invalid_format(temp_dir: str, output_dir: str) -> None:
    """Test exporting with invalid format."""
    structure = {"_files": ["file1.txt"]}
    output_path = os.path.join(output_dir, "test_export.invalid")

    with pytest.raises(ValueError) as excinfo:
        get_exporter(
            "invalid",
            structure=structure,
            root_name=os.path.basename(temp_dir),
        ).export(output_path)
    assert "Unsupported export format" in str(excinfo.value)


def test_export_error_handling(
    sample_directory: str,
    output_dir: str,
    mocker: MockerFixture,
) -> None:
    """Test error handling during export."""
    structure, _ = get_directory_structure(sample_directory)
    output_path = os.path.join(output_dir, "structure.txt")

    mocker.patch("builtins.open", side_effect=PermissionError("Permission denied"))
    with pytest.raises(PermissionError):
        get_exporter(
            "txt",
            structure=structure,
            root_name=os.path.basename(sample_directory),
        ).export(output_path)


def test_export_with_max_depth_indicator(temp_dir: str, output_dir: str) -> None:
    """Test exporting structure with max depth indicators."""
    level1 = os.path.join(temp_dir, "level1")
    level2 = os.path.join(level1, "level2")
    level3 = os.path.join(level2, "level3")
    os.makedirs(level3, exist_ok=True)
    with open(os.path.join(level1, "file1.txt"), "w") as f:
        f.write("Level 1 file")

    structure, _ = get_directory_structure(temp_dir, max_depth=2)
    format_indicators = {
        "txt": "⋯ (max depth reached)",
        "json": "_max_depth_reached",
        "html": "max-depth",
        "md": "*(max depth reached)*",
        "jsx": "max depth reached",
    }

    for fmt, indicator in format_indicators.items():
        output_path = os.path.join(output_dir, f"max_depth.{fmt}")
        get_exporter(
            fmt,
            structure=structure,
            root_name=os.path.basename(temp_dir),
        ).export(output_path)

        with open(output_path, encoding="utf-8") as f:
            content = f.read()
        assert indicator in content, (
            f"Max depth indicator '{indicator}' not found in {fmt} export"
        )


def test_export_with_statistics(sample_directory: str, output_dir: str) -> None:
    """Test exporting with statistics (LOC, size, mtime)."""
    structure, _ = get_directory_structure(
        sample_directory, sort_by_loc=True, sort_by_size=True, sort_by_mtime=True
    )
    format_indicators = {
        "txt": [
            r"lines",
            r"[KMG]?B",
            r"Today|Yesterday|\d{4}-\d{2}-\d{2}",
        ],
        "json": [r'"show_loc": true', r'"show_size": true', r'"show_mtime": true'],
        "html": [
            r"lines",
            r"[KMG]?B",
            r"Today|Yesterday|\d{4}-\d{2}-\d{2}|format_timestamp",
        ],
        "md": [
            r"lines",
            r"[KMG]?B",
            r"Today|Yesterday|\d{4}-\d{2}-\d{2}",
        ],
        "jsx": [r"locCount", r"sizeCount", r"mtimeCount"],
    }

    for fmt, patterns in format_indicators.items():
        output_path = os.path.join(output_dir, f"stats_export.{fmt}")
        get_exporter(
            fmt,
            structure=structure,
            root_name=os.path.basename(sample_directory),
            sort_by_loc=True,
            sort_by_size=True,
            sort_by_mtime=True,
        ).export(output_path)

        with open(output_path, encoding="utf-8") as f:
            content = f.read()
        for pattern in patterns:
            assert re.search(pattern, content), (
                f"Pattern '{pattern}' not found in {fmt} export"
            )


def test_large_structure_export(output_dir: str) -> None:
    """Test exporting a large directory structure."""
    structure = generate_large_structure(depth=5, files_per_dir=10, dir_branching=3)

    for fmt in ["txt", "json", "html", "md", "jsx"]:
        output_path = os.path.join(output_dir, f"large_structure.{fmt}")
        get_exporter(fmt, structure=structure, root_name="large_root").export(
            output_path
        )

        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0, f"Exported {fmt} file is empty"
        with open(output_path, encoding="utf-8") as f:
            content = f.read()
        if fmt == "txt":
            assert "📁 large_root" in content
            assert "file_1_0.txt" in content
        elif fmt == "json":
            assert '"root": "large_root"' in content
            data = json.loads(content)
            assert "_files" in data["structure"]
        elif fmt == "html":
            assert "<!DOCTYPE html>" in content
            assert "large_root" in content
        elif fmt == "md":
            assert "# 📁 large_root" in content
        elif fmt == "jsx":
            assert "import React" in content
            assert 'name="large_root"' in content


def test_unicode_file_names(output_dir: str) -> None:
    """Test exporting with Unicode characters in file names."""
    unicode_structure = {
        "_files": [
            "ascii.txt",
            "español.txt",
            "中文.py",
            "русский.md",
            "日本語.js",
            "한국어.json",
        ],
        "目录": {
            "_files": ["файл.txt"],
        },
        "папка": {
            "_files": ["ファイル.py"],
            "子目录": {
                "_files": ["파일.md"],
            },
        },
    }

    for fmt in ["txt", "json", "html", "md", "jsx"]:
        output_path = os.path.join(output_dir, f"unicode.{fmt}")
        get_exporter(fmt, structure=unicode_structure, root_name="unicode_root").export(
            output_path
        )

        assert os.path.exists(output_path)
        with open(output_path, encoding="utf-8") as f:
            content = f.read()
        if fmt == "json":
            data = json.loads(content)
            files = data["structure"]["_files"]
            assert "español.txt" in files
            assert "中文.py" in files
            assert "русский.md" in files
            assert "目录" in data["structure"]
        elif fmt != "jsx":
            assert "español.txt" in content
            assert "中文.py" in content
            assert "русский.md" in content
            assert "目录" in content
            assert "папка" in content


@pytest.mark.parametrize(
    "error_type,error_msg",
    [
        (PermissionError, "Permission denied"),
        (OSError, "No space left on device"),
    ],
)
def test_export_structure_error_types(
    sample_directory: str,
    output_dir: str,
    error_type: type[Exception],
    error_msg: str,
) -> None:
    """Test handling different error types during export."""
    structure, _ = get_directory_structure(sample_directory)
    output_path = os.path.join(output_dir, f"error_{error_type.__name__}.txt")
    error: Exception
    if error_type is OSError:
        error = OSError(28, error_msg)
    else:
        error = error_type(error_msg)

    with patch("recursivist.exporters.txt.TxtExporter.export", side_effect=error):
        with pytest.raises(Exception) as excinfo:
            get_exporter(
                "txt",
                structure=structure,
                root_name=os.path.basename(sample_directory),
            ).export(output_path)
        assert error_msg in str(excinfo.value)


def test_to_jsx_with_long_paths(output_dir: str) -> None:
    """Test JSX export with very long file names."""
    long_name = "a" * 255
    long_structure = {
        "_files": [
            f"{long_name}.txt",
            (f"{long_name}.py", f"/path/to/{long_name}.py"),
        ],
        f"dir_{long_name}": {
            "_files": [f"nested_{long_name}.md"],
        },
    }
    output_path = os.path.join(output_dir, "long_names.jsx")

    get_exporter("jsx", structure=long_structure, root_name="long_root").export(
        output_path
    )

    assert os.path.exists(output_path)
    with open(output_path, encoding="utf-8") as f:
        content = f.read()
    assert f'name="{long_name}.txt"' in content
    assert f'name="{long_name}.py"' in content
    assert f'name="dir_{long_name}"' in content
    assert f'name="nested_{long_name}.md"' in content


def test_export_with_excessive_loc(temp_dir: str, output_dir: str) -> None:
    """Test exporting files with very large line counts."""
    test_file = os.path.join(temp_dir, "many_lines.py")
    with open(test_file, "w") as f:
        for i in range(10000):
            f.write(f"print('Line {i}')\n")

    structure, _ = get_directory_structure(temp_dir, sort_by_loc=True)

    for fmt in ["txt", "json", "html", "md", "jsx"]:
        output_path = os.path.join(output_dir, f"large_loc.{fmt}")
        get_exporter(
            fmt,
            structure=structure,
            root_name=os.path.basename(temp_dir),
            sort_by_loc=True,
        ).export(output_path)

        assert os.path.exists(output_path)
        with open(output_path, encoding="utf-8") as f:
            content = f.read()
        if fmt == "txt":
            assert re.search(r"many_lines\.py \(\d{4,} lines\)", content)
        elif fmt == "json":
            assert re.search(r'"loc": \d{4,}', content)
        elif fmt in ["html", "md"]:
            assert re.search(r"many_lines\.py.*\(\d{4,} lines\)", content)
        elif fmt == "jsx":
            assert re.search(r"locCount={\d{4,}}", content)


def test_many_unique_extensions(output_dir: str) -> None:
    """Test export with many unique file extensions."""
    many_extensions_structure: dict[str, list[str]] = {"_files": []}
    for i in range(100):
        ext = random_string(5)
        many_extensions_structure["_files"].append(f"file_{i}.{ext}")

    output_path = os.path.join(output_dir, "many_extensions.html")
    get_exporter(
        "html",
        structure=many_extensions_structure,
        root_name="extensions_test",
    ).export(output_path)

    assert os.path.exists(output_path)
    with open(output_path, encoding="utf-8") as f:
        content = f.read()
    color_matches = re.findall(r'style="([^"]*)"', content)
    unique_colors = set()
    for style in color_matches:
        if "#" in style:
            color_code = re.search(r"#[0-9A-Fa-f]{6}", style)
            if color_code:
                unique_colors.add(color_code.group())
    assert len(unique_colors) > 10, (
        "Too few unique colors generated for different extensions"
    )


def test_problematic_filenames(output_dir: str) -> None:
    """Test export with filenames containing special characters."""
    problematic_structure = {
        "_files": [
            "file with spaces.txt",
            "file&with&ampersands.py",
            "file<with>brackets.md",
            "file'with\"quotes.js",
            "file\\with/slashes.html",
        ],
        "directory with spaces": {
            "_files": ["nested problematic.txt"],
        },
    }

    for fmt in ["txt", "json", "html", "md", "jsx"]:
        output_path = os.path.join(output_dir, f"escaping.{fmt}")
        get_exporter(
            fmt, structure=problematic_structure, root_name="escape_test"
        ).export(output_path)

        assert os.path.exists(output_path)
        try:
            if fmt == "json":
                with open(output_path, encoding="utf-8") as f:
                    json.load(f)
            elif fmt == "html":
                with open(output_path, encoding="utf-8") as f:
                    content = f.read()
                assert any(entity in content for entity in ["&amp;", "&#x26;"])
                assert any(entity in content for entity in ["&lt;", "&#x3C;"])
                assert any(entity in content for entity in ["&gt;", "&#x3E;"])
                assert any(entity in content for entity in ["&quot;", "&#x22;"])
            with open(output_path, encoding="utf-8") as f:
                content = f.read()
            normalized_content = content.replace("&#x20;", " ").replace("&nbsp;", " ")
            assert "file with spaces" in normalized_content
            assert "directory with spaces" in normalized_content
        except Exception as e:
            pytest.fail(f"Format {fmt} failed validation: {str(e)}")


def test_combined_export_options(output_dir: str) -> None:
    """Test exporting with all options combined."""
    now = time.time()
    complex_structure = {
        "_loc": 500,
        "_size": 1024 * 1024,
        "_mtime": int(now),
        "_files": [
            ("file1.txt", "/path/to/file1.txt", 100, 512, int(now - 86400)),
            ("file2.py", "/path/to/file2.py", 200, 1024, int(now)),
        ],
        "subdir": {
            "_loc": 300,
            "_size": 2048,
            "_mtime": int(now - 3600),
            "_files": [
                (
                    "subfile.md",
                    "/path/to/subdir/subfile.md",
                    300,
                    2048,
                    int(now - 7200),
                ),
            ],
            "nested": {
                "_max_depth_reached": True,
            },
        },
    }

    for fmt in ["txt", "json", "html", "md", "jsx"]:
        output_path = os.path.join(output_dir, f"combined_options.{fmt}")
        get_exporter(
            fmt,
            structure=complex_structure,
            root_name="complex_root",
            base_path="/path/to/complex_root",
            sort_by_loc=True,
            sort_by_size=True,
            sort_by_mtime=True,
        ).export(output_path)

        assert os.path.exists(output_path)
        with open(output_path, encoding="utf-8") as f:
            content = f.read().replace("&quot;", '"')
        assert "/path/to/file1.txt" in content
        if fmt != "jsx":
            assert any(str(count) in content for count in [100, 200, 300])
            assert any(
                size in content
                for size in ["512 B", "0.5 KB", "1.0 KB", "1024 B", "2.0 KB", "2048 B"]
            )
            timestamp_patterns = [
                "Today",
                "Yesterday",
                "Jan",
                "Feb",
                "Mar",
                "Apr",
                "May",
                "Jun",
                "Jul",
                "Aug",
                "Sep",
                "Oct",
                "Nov",
                "Dec",
            ]
            timestamp_matches = [
                pattern for pattern in timestamp_patterns if pattern in content
            ]
            assert len(timestamp_matches) > 0, (
                f"No timestamp format found in {fmt} export"
            )
        if fmt == "txt":
            assert "⋯ (max depth reached)" in content
        elif fmt == "json":
            assert "_max_depth_reached" in content
        elif fmt == "html":
            assert "max-depth" in content
        elif fmt == "md":
            assert "*(max depth reached)*" in content
        elif fmt == "jsx":
            assert "max depth reached" in content
