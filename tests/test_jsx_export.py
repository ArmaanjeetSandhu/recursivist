"""
Tests for the JSX export functionality of the recursivist package.

This module contains comprehensive tests for the JSX export functionality:
- JSX structure generation with various directory structures
- Handling of statistics (LOC, size, modification time)
- Path display options
- Maximum depth scenarios
- Error handling in JSX exports
- Special character handling
- Mixed file representation formats
"""

import os
import re
import tempfile
from unittest.mock import mock_open, patch

import pytest

from recursivist.jsx_export import generate_jsx_component


@pytest.fixture
def simple_structure():
    """Create a simple directory structure with files only."""
    return {
        "_files": ["file1.txt", "file2.py", "file3.md"],
    }


@pytest.fixture
def empty_structure():
    """Create an empty directory structure."""
    return {}


@pytest.fixture
def nested_structure():
    """Create a nested directory structure with multiple levels."""
    return {
        "_files": ["root_file1.txt", "root_file2.py"],
        "subdir1": {
            "_files": ["subdir1_file1.txt", "subdir1_file2.js"],
        },
        "subdir2": {
            "_files": ["subdir2_file1.md"],
            "nested": {
                "_files": ["nested_file1.json"],
                "deep": {
                    "_files": ["deep_file1.py", "deep_file2.txt"],
                },
            },
        },
    }


@pytest.fixture
def very_deep_structure():
    """Create an extremely deep directory structure to test nesting limits."""
    structure = {}
    current = structure
    for i in range(1, 11):
        dir_name = f"level{i}"
        current["_files"] = [f"file_at_level{i}.txt"]
        current[dir_name] = {}
        current = current[dir_name]
    current["_files"] = ["deepest_file.txt"]
    return structure


@pytest.fixture
def structure_with_stats():
    """Create a directory structure with statistics."""
    return {
        "_loc": 100,
        "_size": 1024,
        "_mtime": 1609459200,
        "_files": [
            ("file1.txt", "/path/to/file1.txt", 50, 512, 1609459200),
            ("file2.py", "/path/to/file2.py", 30, 256, 1609459000),
        ],
        "subdir": {
            "_loc": 20,
            "_size": 256,
            "_mtime": 1609450000,
            "_files": [
                ("subfile.md", "/path/to/subdir/subfile.md", 20, 256, 1609450000),
            ],
        },
    }


@pytest.fixture
def max_depth_structure():
    """Create a directory structure with max depth reached."""
    return {
        "_files": ["root_file.txt"],
        "subdir": {
            "_max_depth_reached": True,
        },
    }


@pytest.fixture
def mixed_file_formats_structure():
    """Create a structure with mixed file representation formats (strings and tuples of different lengths)."""
    return {
        "_files": [
            "simple_string.txt",
            ("name.py", "/full/path/to/name.py"),
            ("doc.md", "/path/to/doc.md", 150),
            ("report.pdf", "/path/to/report.pdf", 0, 1024),
            ("data.csv", "/path/to/data.csv", 0, 0, 1609459200),
            ("mixed.js", "/path/to/mixed.js", 200, 2048, 1609459200),
        ],
        "mixed_dir": {
            "_files": [
                "another_string.txt",
                ("nested.py", "/path/to/mixed_dir/nested.py", 50),
            ]
        },
    }


@pytest.fixture
def unicode_structure():
    """Create a structure with Unicode characters in names."""
    return {
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


def test_empty_structure(empty_structure, tmp_path):
    """Test JSX export with an empty directory structure."""
    output_path = os.path.join(tmp_path, "empty.jsx")
    generate_jsx_component(empty_structure, "empty_dir", output_path)
    assert os.path.exists(output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        jsx_content = f.read()
    assert "import React" in jsx_content
    assert "empty_dir" in jsx_content
    assert "DirectoryViewer" in jsx_content
    assert "export default DirectoryViewer" in jsx_content
    file_items = re.findall(r"<FileItem\s", jsx_content)
    assert len(file_items) == 0


def test_simple_structure(simple_structure, tmp_path):
    """Test JSX export with a simple structure with only files, no nested directories."""
    output_path = os.path.join(tmp_path, "simple.jsx")
    generate_jsx_component(simple_structure, "simple_dir", output_path)
    assert os.path.exists(output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        jsx_content = f.read()
    assert "<FileItem " in jsx_content
    assert 'name="file1.txt"' in jsx_content
    assert 'name="file2.py"' in jsx_content
    assert 'name="file3.md"' in jsx_content
    file_items = re.findall(r"<FileItem\s", jsx_content)
    assert len(file_items) == 3
    directory_items = re.findall(r"<DirectoryItem\s", jsx_content)
    assert len(directory_items) == 1
    assert 'name="simple_dir"' in jsx_content


def test_nested_structure(nested_structure, tmp_path):
    """Test JSX export with a deeply nested structure with multiple levels."""
    output_path = os.path.join(tmp_path, "nested.jsx")
    generate_jsx_component(nested_structure, "nested_dir", output_path)
    assert os.path.exists(output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        jsx_content = f.read()
    assert 'name="subdir1"' in jsx_content
    assert 'name="subdir2"' in jsx_content
    assert 'name="nested"' in jsx_content
    assert 'name="deep"' in jsx_content
    assert 'name="root_file1.txt"' in jsx_content
    assert 'name="subdir1_file1.txt"' in jsx_content
    assert 'name="nested_file1.json"' in jsx_content
    assert 'name="deep_file1.py"' in jsx_content
    directory_items = re.findall(r"<DirectoryItem\s", jsx_content)
    assert len(directory_items) == 5
    file_items = re.findall(r"<FileItem\s", jsx_content)
    assert len(file_items) == 8


def test_very_deep_structure(very_deep_structure, tmp_path):
    """Test JSX export with an extremely deep directory structure."""
    output_path = os.path.join(tmp_path, "very_deep.jsx")
    generate_jsx_component(very_deep_structure, "deep_dir", output_path)
    assert os.path.exists(output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        jsx_content = f.read()
    for i in range(1, 11):
        assert f'name="level{i}"' in jsx_content
        assert f'name="file_at_level{i}.txt"' in jsx_content
    assert 'name="deepest_file.txt"' in jsx_content
    level1_match = re.search(r'name="level1"[^>]*level=\{(\d+)\}', jsx_content)
    level10_match = re.search(r'name="level10"[^>]*level=\{(\d+)\}', jsx_content)
    if level1_match and level10_match:
        level1 = int(level1_match.group(1))
        level10 = int(level10_match.group(1))
        assert level10 > level1, "Deeper directories should have higher level values"
        assert (
            level10 - level1 == 9
        ), "Level should increase by 1 for each nesting level"


def test_structure_with_stats(structure_with_stats, tmp_path):
    """Test JSX export with statistics enabled."""
    output_path = os.path.join(tmp_path, "stats.jsx")
    generate_jsx_component(
        structure_with_stats,
        "stats_dir",
        output_path,
        sort_by_loc=True,
        sort_by_size=True,
        sort_by_mtime=True,
    )
    assert os.path.exists(output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        jsx_content = f.read()
    assert "locCount={100}" in jsx_content
    assert "sizeCount={1024}" in jsx_content
    assert "mtimeCount={1609459200}" in jsx_content
    assert "locCount={50}" in jsx_content
    assert "sizeCount={512}" in jsx_content
    assert "mtimeCount={1609459200}" in jsx_content
    assert "mtimeFormatted=" in jsx_content
    assert "sizeFormatted=" in jsx_content
    assert "locCount={20}" in jsx_content
    assert "import { BarChart2, Database, Clock } from 'lucide-react';" in jsx_content
    assert "const showLoc = true;" in jsx_content
    assert "const showSize = true;" in jsx_content
    assert "const showMtime = true;" in jsx_content
    assert "const format_size = (size_in_bytes)" in jsx_content
    assert "const format_timestamp = (timestamp)" in jsx_content


def test_structure_with_full_paths(structure_with_stats, tmp_path):
    """Test JSX export with full paths enabled."""
    output_path = os.path.join(tmp_path, "full_paths.jsx")
    generate_jsx_component(
        structure_with_stats, "path_dir", output_path, show_full_path=True
    )
    assert os.path.exists(output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        jsx_content = f.read()
    assert 'displayPath="/path/to/file1.txt"' in jsx_content
    assert 'displayPath="/path/to/file2.py"' in jsx_content
    assert 'displayPath="/path/to/subdir/subfile.md"' in jsx_content
    assert (
        'path={["path_dir","file1.txt"]}' in jsx_content
        or 'path={["path_dir", "file1.txt"]}' in jsx_content
    )


def test_max_depth_structure(max_depth_structure, tmp_path):
    """Test JSX export with max depth reached scenarios."""
    output_path = os.path.join(tmp_path, "max_depth.jsx")
    generate_jsx_component(max_depth_structure, "max_depth_dir", output_path)
    assert os.path.exists(output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        jsx_content = f.read()
    assert "(max depth reached)" in jsx_content
    assert "div className=" in jsx_content and "max-depth" in jsx_content


def test_mixed_file_formats(mixed_file_formats_structure, tmp_path):
    """Test JSX export with mixed file representation formats."""
    output_path = os.path.join(tmp_path, "mixed_formats.jsx")
    generate_jsx_component(
        mixed_file_formats_structure,
        "mixed_formats_dir",
        output_path,
        sort_by_loc=True,
        sort_by_size=True,
        sort_by_mtime=True,
    )
    assert os.path.exists(output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        jsx_content = f.read()
    assert 'name="simple_string.txt"' in jsx_content
    assert 'name="name.py"' in jsx_content
    assert 'name="doc.md"' in jsx_content and "locCount={150}" in jsx_content
    assert 'name="report.pdf"' in jsx_content and "sizeCount={1024}" in jsx_content
    assert 'name="data.csv"' in jsx_content and "mtimeCount={1609459200}" in jsx_content
    assert (
        'name="mixed.js"' in jsx_content
        and "locCount={200}" in jsx_content
        and "sizeCount={2048}" in jsx_content
    )
    assert 'name="another_string.txt"' in jsx_content
    assert 'name="nested.py"' in jsx_content and "locCount={50}" in jsx_content


def test_unicode_characters(unicode_structure, tmp_path):
    """Test JSX export with Unicode characters in file and directory names."""
    output_path = os.path.join(tmp_path, "unicode.jsx")
    generate_jsx_component(unicode_structure, "unicode_dir", output_path)
    assert os.path.exists(output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        jsx_content = f.read()
    assert (
        'name="español.txt"' in jsx_content
        or 'name="espa&#241;ol.txt"' in jsx_content
        or 'name="espa&ntilde;ol.txt"' in jsx_content
    )
    assert 'name="中文.py"' in jsx_content or "&#x4E2D;&#x6587;.py" in jsx_content
    assert (
        'name="русский.md"' in jsx_content
        or "&#x440;&#x443;&#x441;&#x441;&#x43A;&#x438;&#x439;.md" in jsx_content
    )
    assert 'name="目录"' in jsx_content or "&#x76EE;&#x5F55;" in jsx_content
    assert (
        'name="папка"' in jsx_content
        or "&#x043F;&#x0430;&#x043F;&#x043A;&#x0430;" in jsx_content
    )
    assert "<FileItem " in jsx_content
    assert "<DirectoryItem " in jsx_content


def test_various_sorting_options(structure_with_stats, tmp_path):
    """Test JSX export with different combinations of sorting options."""
    test_combinations = [
        (True, False, False),
        (False, True, False),
        (False, False, True),
        (True, True, False),
        (True, False, True),
        (False, True, True),
    ]
    for sort_by_loc, sort_by_size, sort_by_mtime in test_combinations:
        output_path = os.path.join(
            tmp_path, f"sort_{sort_by_loc}_{sort_by_size}_{sort_by_mtime}.jsx"
        )
        generate_jsx_component(
            structure_with_stats,
            "sort_dir",
            output_path,
            sort_by_loc=sort_by_loc,
            sort_by_size=sort_by_size,
            sort_by_mtime=sort_by_mtime,
        )
        assert os.path.exists(output_path)
        with open(output_path, "r", encoding="utf-8") as f:
            jsx_content = f.read()
        if sort_by_loc and sort_by_size and sort_by_mtime:
            assert (
                "import { BarChart2, Database, Clock } from 'lucide-react';"
                in jsx_content
            )
        elif sort_by_loc and sort_by_size:
            assert "import { BarChart2, Database } from 'lucide-react';" in jsx_content
        elif sort_by_loc and sort_by_mtime:
            assert "import { BarChart2, Clock } from 'lucide-react';" in jsx_content
        elif sort_by_size and sort_by_mtime:
            assert "import { Database, Clock } from 'lucide-react';" in jsx_content
        elif sort_by_loc:
            assert "import { BarChart2 } from 'lucide-react';" in jsx_content
        elif sort_by_size:
            assert "import { Database } from 'lucide-react';" in jsx_content
        elif sort_by_mtime:
            assert "import { Clock } from 'lucide-react';" in jsx_content
        if sort_by_loc:
            assert "const showLoc = true;" in jsx_content
        else:
            assert "const showLoc = false;" in jsx_content
        if sort_by_size:
            assert "const showSize = true;" in jsx_content
        else:
            assert "const showSize = false;" in jsx_content
        if sort_by_mtime:
            assert "const showMtime = true;" in jsx_content
        else:
            assert "const showMtime = false;" in jsx_content
        if sort_by_size:
            assert "const format_size = (size_in_bytes)" in jsx_content
        else:
            assert (
                "const format_size = () =>" in jsx_content
                and "return '0 B';" in jsx_content
            )
        if sort_by_mtime:
            assert "const format_timestamp = (timestamp)" in jsx_content
        else:
            assert (
                "const format_timestamp = () =>" in jsx_content
                and "return '';" in jsx_content
            )


def test_error_handling(structure_with_stats):
    """Test error handling in JSX export."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, "error.jsx")
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            with patch("recursivist.jsx_export.logger") as mock_logger:
                with pytest.raises(Exception):
                    generate_jsx_component(
                        structure_with_stats, "error_dir", output_path
                    )
                mock_logger.error.assert_called_once()
                assert (
                    "Error exporting to React component"
                    in mock_logger.error.call_args[0][0]
                )


def test_special_characters_in_names(tmp_path):
    """Test JSX export with special characters in file and directory names."""
    special_structure = {
        "_files": ["normal.txt", "special&.txt", 'quotes".txt', "tags<>.txt"],
        "special dir & more": {
            "_files": ["file in special dir.txt"],
        },
    }
    output_path = os.path.join(tmp_path, "special_chars.jsx")
    generate_jsx_component(special_structure, "special_chars_dir", output_path)
    assert os.path.exists(output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        jsx_content = f.read()
    assert (
        'name="special&amp;.txt"' in jsx_content
        or 'name="special&#x26;.txt"' in jsx_content
    )
    assert (
        'name="quotes&quot;.txt"' in jsx_content
        or 'name="quotes&#x22;.txt"' in jsx_content
    )
    assert (
        'name="tags&lt;&gt;.txt"' in jsx_content
        or 'name="tags&#x3C;&#x3E;.txt"' in jsx_content
    )
    assert (
        'name="special dir &amp; more"' in jsx_content
        or 'name="special dir &#x26; more"' in jsx_content
    )


def test_disk_space_error(structure_with_stats, tmp_path):
    """Test JSX export with disk space error."""
    output_path = os.path.join(tmp_path, "disk_full.jsx")
    mock_disk_full = mock_open()
    mock_disk_full.side_effect = OSError(28, "No space left on device")
    with patch("builtins.open", mock_disk_full):
        with patch("recursivist.jsx_export.logger") as mock_logger:
            with pytest.raises(Exception):
                generate_jsx_component(
                    structure_with_stats, "disk_full_dir", output_path
                )
            mock_logger.error.assert_called_once()
            assert (
                "Error exporting to React component"
                in mock_logger.error.call_args[0][0]
            )


def test_component_props_validation(structure_with_stats, tmp_path):
    """Test that component props are correctly validated."""
    output_path = os.path.join(tmp_path, "props_validation.jsx")
    generate_jsx_component(
        structure_with_stats,
        "props_dir",
        output_path,
        sort_by_loc=True,
        sort_by_size=True,
        sort_by_mtime=True,
    )
    assert os.path.exists(output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        jsx_content = f.read()
    assert "DirectoryItem.propTypes = {" in jsx_content
    assert "FileItem.propTypes = {" in jsx_content
    assert "name: PropTypes.string.isRequired" in jsx_content
    assert "children: PropTypes.node" in jsx_content
    assert "level: PropTypes.number" in jsx_content
    assert "path: PropTypes.arrayOf(PropTypes.string)" in jsx_content
    assert "locCount: PropTypes.number" in jsx_content
    assert "sizeCount: PropTypes.number" in jsx_content
    assert "mtimeCount: PropTypes.number" in jsx_content
