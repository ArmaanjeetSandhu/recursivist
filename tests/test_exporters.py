"""Tests for recursivist.exporters: get_exporter and the per-format exporters."""

import io
import json
import os
import random
import re
import string
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from hypothesis import strategies as st
from pytest_mock import MockerFixture

from recursivist._models import FileEntry
from recursivist.exporters import get_exporter
from recursivist.exporters.rst import (
    _rst_display_width,
    _rst_escape,
    _rst_inline_literal,
)
from recursivist.flags import (
    METRIC_LOC,
    METRIC_MTIME,
    METRIC_SIZE,
    DisplayOptions,
)
from recursivist.scanner import get_directory_structure

_METRIC_SPECS = {
    "sort_by_loc": DisplayOptions(sort_key=METRIC_LOC, metrics=(METRIC_LOC,)),
    "sort_by_size": DisplayOptions(sort_key=METRIC_SIZE, metrics=(METRIC_SIZE,)),
    "sort_by_mtime": DisplayOptions(sort_key=METRIC_MTIME, metrics=(METRIC_MTIME,)),
}
_ALL_METRICS_SPEC = DisplayOptions(
    sort_key=METRIC_LOC, metrics=(METRIC_LOC, METRIC_SIZE, METRIC_MTIME)
)


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
            "rst",
            "rst",
            ["📄 ``file1.txt``", "📄 ``file2.py``", "📁 **subdir**"],
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
    elif option_name in _METRIC_SPECS:
        kwargs["spec"] = _METRIC_SPECS[option_name]

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
            ("rst", ["📁 test_root", "``file1.txt``", "``file2.py``"]),
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
        kwargs: dict[str, Any] = {"spec": _METRIC_SPECS[option_name]}

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
            with pytest.raises(error_type) as excinfo:
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
            spec=_ALL_METRICS_SPEC,
        )
        assert exporter.show_loc
        assert exporter.show_size
        assert exporter.show_mtime


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
            "rst",
            "rst",
            [
                lambda c: "- 📄 ``file1.txt``" in c,
                lambda c: "- 📁 **subdir**" in c,
                lambda c: any(line and set(line) == {"="} for line in c.splitlines()),
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
    get_structure_kwargs: dict[str, Any] = {}
    if option_name in [
        "show_full_path",
        "sort_by_loc",
        "sort_by_size",
        "sort_by_mtime",
    ]:
        get_structure_kwargs[option_name] = option_value

    structure, _ = get_directory_structure(sample_directory, **get_structure_kwargs)
    output_path = os.path.join(output_dir, f"structure_{option_name}.txt")

    kwargs: dict[str, Any] = {}
    if option_name == "show_full_path":
        kwargs["base_path"] = sample_directory if option_value else None
    elif option_name in _METRIC_SPECS:
        kwargs["spec"] = _METRIC_SPECS[option_name]

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
    }

    for fmt, patterns in format_indicators.items():
        output_path = os.path.join(output_dir, f"stats_export.{fmt}")
        get_exporter(
            fmt,
            structure=structure,
            root_name=os.path.basename(sample_directory),
            spec=_ALL_METRICS_SPEC,
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

    for fmt in ["txt", "json", "html", "md"]:
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

    for fmt in ["txt", "json", "html", "md"]:
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
        else:
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
        with pytest.raises(error_type) as excinfo:
            get_exporter(
                "txt",
                structure=structure,
                root_name=os.path.basename(sample_directory),
            ).export(output_path)
        assert error_msg in str(excinfo.value)


def test_export_with_excessive_loc(temp_dir: str, output_dir: str) -> None:
    """Test exporting files with very large line counts."""
    test_file = os.path.join(temp_dir, "many_lines.py")
    with open(test_file, "w") as f:
        for i in range(10000):
            f.write(f"print('Line {i}')\n")

    structure, _ = get_directory_structure(temp_dir, sort_by_loc=True)

    for fmt in ["txt", "json", "html", "md"]:
        output_path = os.path.join(output_dir, f"large_loc.{fmt}")
        get_exporter(
            fmt,
            structure=structure,
            root_name=os.path.basename(temp_dir),
            spec=_METRIC_SPECS["sort_by_loc"],
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

    for fmt in ["txt", "json", "html", "md"]:
        output_path = os.path.join(output_dir, f"escaping.{fmt}")
        get_exporter(
            fmt, structure=problematic_structure, root_name="escape_test"
        ).export(output_path)

        assert os.path.exists(output_path)
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

    for fmt in ["txt", "json", "html", "md"]:
        output_path = os.path.join(output_dir, f"combined_options.{fmt}")
        get_exporter(
            fmt,
            structure=complex_structure,
            root_name="complex_root",
            base_path="/path/to/complex_root",
            spec=_ALL_METRICS_SPEC,
        ).export(output_path)

        assert os.path.exists(output_path)
        with open(output_path, encoding="utf-8") as f:
            content = f.read().replace("&quot;", '"')
        assert "/path/to/file1.txt" in content
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
        assert len(timestamp_matches) > 0, f"No timestamp format found in {fmt} export"
        if fmt == "txt":
            assert "⋯ (max depth reached)" in content
        elif fmt == "json":
            assert "_max_depth_reached" in content
        elif fmt == "html":
            assert "max-depth" in content
        elif fmt == "md":
            assert "*(max depth reached)*" in content


class TestSvgExporter:
    """Tests for the SVG exporter (recursivist.exporters.svg.SvgExporter)."""

    def test_export_basic(
        self, nested_structure: dict[str, Any], tmp_path: Path
    ) -> None:
        """A basic export writes a well-formed SVG containing the tree.

        Uses a structure whose ``_files`` are plain strings and which nests
        sub-dictionaries, exercising both branches of the recursive extension
        collector.
        """
        output_path = os.path.join(tmp_path, "structure.svg")
        get_exporter("svg", structure=nested_structure, root_name="svg_root").export(
            output_path
        )

        assert os.path.exists(output_path)
        with open(output_path, encoding="utf-8") as f:
            content = f.read()
        assert content.lstrip().startswith("<svg")
        assert "rich-terminal" in content
        assert "svg_root" in content

    def test_export_real_scanner_output(
        self, sample_directory: str, tmp_path: Path
    ) -> None:
        """Export a structure produced by the scanner (FileEntry tuples)."""
        structure, _ = get_directory_structure(sample_directory)
        output_path = os.path.join(tmp_path, "scanned.svg")
        get_exporter(
            "svg",
            structure=structure,
            root_name=os.path.basename(sample_directory),
        ).export(output_path)

        assert os.path.exists(output_path)
        with open(output_path, encoding="utf-8") as f:
            content = f.read()
        assert "<svg" in content
        assert "file1.txt" in content
        assert "subdir" in content

    def test_export_with_statistics(
        self, structure_with_stats: dict[str, Any], tmp_path: Path
    ) -> None:
        """Exporting with metrics enabled renders the root metrics suffix.

        ``structure_with_stats`` stores ``_files`` as tuples and carries
        ``_loc``/``_size``/``_mtime`` keys, so this also covers the tuple branch
        of the extension collector.
        """
        output_path = os.path.join(tmp_path, "stats.svg")
        get_exporter(
            "svg",
            structure=structure_with_stats,
            root_name="stats_root",
            spec=_ALL_METRICS_SPEC,
        ).export(output_path)

        assert os.path.exists(output_path)
        with open(output_path, encoding="utf-8") as f:
            content = f.read()
        assert "<svg" in content
        assert "stats_root" in content

    def test_export_empty_structure(self, tmp_path: Path) -> None:
        """An empty structure still produces a valid SVG (no extensions)."""
        output_path = os.path.join(tmp_path, "empty.svg")
        get_exporter("svg", structure={}, root_name="empty_root").export(output_path)

        assert os.path.exists(output_path)
        with open(output_path, encoding="utf-8") as f:
            content = f.read()
        assert "<svg" in content
        assert "empty_root" in content

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
        """Failures while saving the SVG are re-raised (after being logged)."""
        output_path = os.path.join(tmp_path, "error.svg")
        exporter = get_exporter(
            "svg", structure=simple_structure, root_name="error_root"
        )
        error: Exception
        if error_type is OSError:
            error = OSError(28, error_msg)
        else:
            error = error_type(error_msg)
        with patch("recursivist.exporters.svg.Console.save_svg", side_effect=error):
            with pytest.raises(error_type) as excinfo:
                exporter.export(output_path)
            assert error_msg in str(excinfo.value)


def _rst_lines(content: str) -> list[str]:
    """Split exported reStructuredText into lines for structural assertions."""
    return content.split("\n")


class TestRstExporter:
    """Tests for the reStructuredText (``rst``) exporter."""

    def test_export_basic_structure(
        self, nested_structure: dict[str, Any], tmp_path: Path
    ) -> None:
        """Root is a section title; dirs are bold, files are inline literals."""
        output_path = os.path.join(tmp_path, "structure.rst")
        get_exporter("rst", structure=nested_structure, root_name="test_root").export(
            output_path
        )

        assert os.path.exists(output_path)
        with open(output_path, encoding="utf-8") as f:
            content = f.read()
        lines = _rst_lines(content)

        assert lines[0] == "📁 test_root"
        assert set(lines[1]) == {"="}
        assert "- 📄 ``root_file1.txt``" in content
        assert "- 📁 **subdir1**" in content
        assert "- 📁 **subdir2**" in content
        assert "  - 📄 ``subdir1_file2.js``" in content
        assert "    - 📄 ``nested_file1.json``" in content

    def test_section_title_underline_matches_display_width(
        self, tmp_path: Path
    ) -> None:
        """The title underline is sized by display width, not code-point count.

        The emoji icon occupies two columns but one code point, so a naive
        ``len``-based underline would be one column short. This guards against
        the docutils "Title underline too short" warning.
        """
        output_path = os.path.join(tmp_path, "structure.rst")
        get_exporter("rst", structure={"_files": ["a.py"]}, root_name="proj").export(
            output_path
        )
        with open(output_path, encoding="utf-8") as f:
            lines = _rst_lines(f.read())

        title, underline = lines[0], lines[1]
        assert title == "📁 proj"
        assert set(underline) == {"="}
        assert len(underline) == _rst_display_width(title)
        assert len(underline) == len(title) + 1

    def test_blank_line_precedes_nested_list(self, tmp_path: Path) -> None:
        """A directory bullet is separated from its nested list by a blank line.

        reStructuredText requires the blank line; without it the nested bullets
        are not parsed as a child list.
        """
        structure = {"outer": {"_files": ["inner.py"]}}
        output_path = os.path.join(tmp_path, "structure.rst")
        get_exporter("rst", structure=structure, root_name="root").export(output_path)
        with open(output_path, encoding="utf-8") as f:
            lines = _rst_lines(f.read())

        dir_idx = lines.index("- 📁 **outer**")
        assert lines[dir_idx + 1] == ""
        assert lines[dir_idx + 2] == "  - 📄 ``inner.py``"

    def test_files_listed_before_directories(self, tmp_path: Path) -> None:
        """Within a level, files are emitted before subdirectories."""
        structure = {"_files": ["zzz.py"], "aaadir": {"_files": ["x.py"]}}
        output_path = os.path.join(tmp_path, "structure.rst")
        get_exporter("rst", structure=structure, root_name="root").export(output_path)
        with open(output_path, encoding="utf-8") as f:
            content = f.read()

        assert content.index("``zzz.py``") < content.index("**aaadir**")

    def test_git_status_badges(self, tmp_path: Path) -> None:
        """Git markers are rendered as bold ``[U]``/``[M]``/``[A]``/``[D]`` badges."""
        structure = {
            "_files": ["untracked.txt", "modified.py", "added.md", "deleted.js"],
            "_git_markers": {
                "untracked.txt": "U",
                "modified.py": "M",
                "added.md": "A",
                "deleted.js": "D",
            },
        }
        output_path = os.path.join(tmp_path, "structure.rst")
        get_exporter(
            "rst",
            structure=structure,
            root_name="root",
            spec=DisplayOptions(show_git_status=True),
        ).export(output_path)
        with open(output_path, encoding="utf-8") as f:
            content = f.read()

        assert "``untracked.txt`` **[U]**" in content
        assert "``modified.py`` **[M]**" in content
        assert "``added.md`` **[A]**" in content
        assert "``deleted.js`` **[D]**" in content

    def test_git_status_omitted_when_disabled(self, tmp_path: Path) -> None:
        """No badges are emitted when Git status display is off."""
        structure = {
            "_files": ["modified.py"],
            "_git_markers": {"modified.py": "M"},
        }
        output_path = os.path.join(tmp_path, "structure.rst")
        get_exporter(
            "rst",
            structure=structure,
            root_name="root",
            spec=DisplayOptions(),
        ).export(output_path)
        with open(output_path, encoding="utf-8") as f:
            content = f.read()

        assert "[M]" not in content

    def test_max_depth_indicator(
        self, max_depth_structure: dict[str, Any], tmp_path: Path
    ) -> None:
        """Depth-limited directories show an emphasized max-depth marker."""
        output_path = os.path.join(tmp_path, "structure.rst")
        get_exporter("rst", structure=max_depth_structure, root_name="root").export(
            output_path
        )
        with open(output_path, encoding="utf-8") as f:
            lines = _rst_lines(f.read())

        marker = "  - ⋯ *(max depth reached)*"
        assert marker in lines
        assert lines[lines.index(marker) - 1] == ""

    def test_metrics_suffix_loc(
        self, structure_with_stats: dict[str, Any], tmp_path: Path
    ) -> None:
        """With ``sort_by_loc``, line counts are appended to files and the root."""
        output_path = os.path.join(tmp_path, "structure.rst")
        get_exporter(
            "rst",
            structure=structure_with_stats,
            root_name="root",
            spec=_METRIC_SPECS["sort_by_loc"],
        ).export(output_path)
        with open(output_path, encoding="utf-8") as f:
            content = f.read()

        assert "(100 lines)" in content
        assert "(50 lines)" in content

    def test_full_path_uses_absolute_paths(self, tmp_path: Path) -> None:
        """When a base path is set, file literals contain the full path."""
        structure = {
            "_files": [FileEntry("a.py", "/abs/root/a.py")],
            "sub": {"_files": [FileEntry("b.py", "/abs/root/sub/b.py")]},
        }
        output_path = os.path.join(tmp_path, "structure.rst")
        get_exporter(
            "rst", structure=structure, root_name="root", base_path="/abs/root"
        ).export(output_path)
        with open(output_path, encoding="utf-8") as f:
            content = f.read()

        assert "``/abs/root/a.py``" in content
        assert "``/abs/root/sub/b.py``" in content

    def test_nerd_icon_style(self, tmp_path: Path) -> None:
        """The nerd icon style substitutes glyphs for the default emoji."""
        structure = {"_files": ["main.py"]}
        output_path = os.path.join(tmp_path, "structure.rst")
        get_exporter(
            "rst", structure=structure, root_name="root", icon_style="nerd"
        ).export(output_path)
        with open(output_path, encoding="utf-8") as f:
            content = f.read()

        assert "📄" not in content
        assert "📁" not in content
        assert "\ue73c" in content

    def test_special_characters_are_escaped(self, tmp_path: Path) -> None:
        """Markup characters in directory names are backslash-escaped."""
        structure = {"weird*name_dir": {"_files": ["ok.py"]}}
        output_path = os.path.join(tmp_path, "structure.rst")
        get_exporter("rst", structure=structure, root_name="root").export(output_path)
        with open(output_path, encoding="utf-8") as f:
            content = f.read()

        assert "**weird\\*name\\_dir**" in content

    def test_empty_structure(self, tmp_path: Path) -> None:
        """An empty structure still yields a valid title and underline."""
        output_path = os.path.join(tmp_path, "structure.rst")
        get_exporter("rst", structure={}, root_name="empty_root").export(output_path)
        with open(output_path, encoding="utf-8") as f:
            lines = _rst_lines(f.read())

        assert lines[0] == "📁 empty_root"
        assert set(lines[1]) == {"="}

    def test_trailing_newline(self, tmp_path: Path) -> None:
        """The file ends with a single trailing newline."""
        output_path = os.path.join(tmp_path, "structure.rst")
        get_exporter("rst", structure={"_files": ["a.py"]}, root_name="root").export(
            output_path
        )
        with open(output_path, encoding="utf-8") as f:
            content = f.read()

        assert content.endswith("\n")
        assert not content.endswith("\n\n")

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
        """Failures while writing the file are re-raised (after being logged)."""
        output_path = os.path.join(tmp_path, "error.rst")
        exporter = get_exporter(
            "rst", structure=simple_structure, root_name="error_root"
        )
        error: Exception
        if error_type is OSError:
            error = OSError(28, error_msg)
        else:
            error = error_type(error_msg)
        with patch("builtins.open", side_effect=error):
            with pytest.raises(error_type) as excinfo:
                exporter.export(output_path)
            assert error_msg in str(excinfo.value)

    def test_output_parses_cleanly_with_docutils(self, tmp_path: Path) -> None:
        """The generated reStructuredText parses without docutils warnings.

        Skipped when docutils is unavailable. This exercises the finicky
        parts of the format together: an emoji-icon section title, nested
        bullet lists (with the required blank lines), Git-status badges, the
        max-depth marker, metric suffixes and escaped special characters.
        """
        docutils_core = pytest.importorskip("docutils.core")

        now = time.time()
        structure = {
            "_loc": 100,
            "_size": 1024,
            "_mtime": now,
            "_files": [
                ("app.py", "/p/app.py", 50, 512, now),
                ("weird*name.py", "/p/weird*name.py", 10, 64, now),
            ],
            "_git_markers": {"app.py": "M"},
            "src": {
                "_loc": 20,
                "_size": 256,
                "_mtime": now,
                "_files": [("helper.py", "/p/src/helper.py", 20, 256, now)],
                "vendored": {"_max_depth_reached": True},
            },
        }
        output_path = os.path.join(tmp_path, "structure.rst")
        get_exporter(
            "rst",
            structure=structure,
            root_name="my_project",
            spec=DisplayOptions(
                sort_key=METRIC_LOC, metrics=(METRIC_LOC,), show_git_status=True
            ),
        ).export(output_path)
        with open(output_path, encoding="utf-8") as f:
            content = f.read()

        warning_stream = io.StringIO()
        docutils_core.publish_doctree(
            content,
            settings_overrides={
                "warning_stream": warning_stream,
                "report_level": 1,
                "halt_level": 5,
            },
        )
        problems = warning_stream.getvalue().strip()
        assert not problems, f"docutils reported issues:\n{problems}\n\nrST:\n{content}"


class TestRstHelpers:
    """Unit tests for the reStructuredText exporter helper functions."""

    def test_inline_literal_basic(self) -> None:
        assert _rst_inline_literal("file.py") == "``file.py``"

    def test_inline_literal_internal_space_is_fine(self) -> None:
        assert _rst_inline_literal("my file.py") == "``my file.py``"

    def test_inline_literal_double_backtick_falls_back_to_escaped(self) -> None:
        result = _rst_inline_literal("a``b.py")
        assert "``a``b.py``" != result
        assert "\\`\\`" in result

    def test_inline_literal_leading_space_falls_back(self) -> None:
        result = _rst_inline_literal(" leading.py")
        assert not result.startswith("`` ")

    def test_inline_literal_trailing_space_falls_back(self) -> None:
        result = _rst_inline_literal("trailing.py ")
        assert not result.endswith(" ``")

    def test_inline_literal_empty_falls_back(self) -> None:
        assert _rst_inline_literal("") == ""

    def test_escape_markup_characters(self) -> None:
        assert _rst_escape("a*b`c_d|e") == "a\\*b\\`c\\_d\\|e"

    def test_escape_backslash_first(self) -> None:
        assert _rst_escape("a\\b") == "a\\\\b"

    def test_escape_plain_text_unchanged(self) -> None:
        assert _rst_escape("plain-name.txt") == "plain-name.txt"

    def test_display_width_ascii_matches_len(self) -> None:
        assert _rst_display_width("plain_ascii") == len("plain_ascii")

    def test_display_width_counts_wide_chars_as_two(self) -> None:
        assert _rst_display_width("📁") == 2
        assert _rst_display_width("日本語") == 6

    def test_display_width_ignores_combining_chars(self) -> None:
        assert _rst_display_width("e\u0301") == 1


class TestJsonGitAndMetrics:
    """The JSON exporter's detailed git-status + ordered-metric rendering."""

    def _export(
        self, structure: dict[str, Any], spec: DisplayOptions, tmp_path: Path
    ) -> dict[str, Any]:
        out = os.path.join(tmp_path, "out.json")
        get_exporter("json", structure=structure, root_name="root", spec=spec).export(
            out
        )
        with open(out, encoding="utf-8") as f:
            result: dict[str, Any] = json.load(f)
        return result

    def test_tuple_file_has_ordered_metrics_and_git(self, tmp_path: Path) -> None:
        structure = {
            "_loc": 60,
            "_size": 1536,
            "_mtime": 1600000000.0,
            "_files": [("a.py", "/p/a.py", 50, 1024, 1600000000.0)],
            "_git_markers": {"a.py": "M"},
        }
        spec = DisplayOptions(
            sort_key=METRIC_LOC,
            metrics=(METRIC_SIZE, METRIC_LOC),
            show_git_status=True,
        )
        data = self._export(structure, spec, tmp_path)
        entry = data["structure"]["_files"][0]
        assert entry["name"] == "a.py"
        assert entry["path"] == "/p/a.py"
        assert entry["loc"] == 50
        assert entry["size"] == 1024
        assert entry["size_formatted"] == "1.0 KB"
        assert entry["git_status"] == "M"
        assert data["sort_key"] == "loc"
        assert data["metric_order"] == ["size", "loc"]
        assert data["show_git_status"] is True

    def test_bare_string_file_wrapped_with_git_status(self, tmp_path: Path) -> None:
        structure = {
            "_files": ["b.txt"],
            "_git_markers": {"b.txt": "A"},
        }
        spec = DisplayOptions(show_git_status=True)
        data = self._export(structure, spec, tmp_path)
        entry = data["structure"]["_files"][0]
        assert entry == {"name": "b.txt", "path": "b.txt", "git_status": "A"}

    def test_git_markers_key_not_leaked(self, tmp_path: Path) -> None:
        structure = {
            "_files": ["b.txt"],
            "_git_markers": {"b.txt": "A"},
        }
        spec = DisplayOptions(show_git_status=True)
        data = self._export(structure, spec, tmp_path)
        assert "_git_markers" not in data["structure"]

    def test_no_git_status_when_disabled(self, tmp_path: Path) -> None:
        structure = {
            "_files": ["b.txt"],
            "_git_markers": {"b.txt": "A"},
        }
        data = self._export(structure, DisplayOptions(), tmp_path)
        assert data["structure"]["_files"] == ["b.txt"]
        assert data["show_git_status"] is False
