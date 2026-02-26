import json
import os
import random
import re
import string
import time
from typing import Any, Callable, Dict, List
from unittest.mock import patch

import pytest
from pytest_mock import MockerFixture

from recursivist.core import (
    export_structure,
    get_directory_structure,
)
from recursivist.exports import DirectoryExporter, sort_files_by_type


class TestSortFilesByType:
    @pytest.mark.parametrize(
        "input_files,expected_order",
        [
            (["c.txt", "b.py", "a.txt", "d.py"], ["b.py", "d.py", "a.txt", "c.txt"]),
            (
                [
                    ("c.txt", "/path/to/c.txt"),
                    ("b.py", "/path/to/b.py"),
                    ("a.txt", "/path/to/a.txt"),
                    ("d.py", "/path/to/d.py"),
                ],
                [
                    ("b.py", "/path/to/b.py"),
                    ("d.py", "/path/to/d.py"),
                    ("a.txt", "/path/to/a.txt"),
                    ("c.txt", "/path/to/c.txt"),
                ],
            ),
            (
                [
                    "c.txt",
                    ("b.py", "/path/to/b.py"),
                    ("a.txt", "/path/to/a.txt"),
                    "d.py",
                ],
                [
                    ("b.py", "/path/to/b.py"),
                    "d.py",
                    ("a.txt", "/path/to/a.txt"),
                    "c.txt",
                ],
            ),
            (
                [
                    "readme",
                    ".gitignore",
                    "file.txt.bak",
                    ".env.local",
                ],
                [
                    ".gitignore",
                    "readme",
                    "file.txt.bak",
                    ".env.local",
                ],
            ),
            ([], []),
            (
                [
                    "file.tar.gz",
                    "file.min.js",
                    "file.spec.ts",
                    "file.d.ts",
                ],
                [
                    "file.tar.gz",
                    "file.min.js",
                    "file.d.ts",
                    "file.spec.ts",
                ],
            ),
        ],
    )
    def test_sort_by_extension(self, input_files, expected_order):
        sorted_files = sort_files_by_type(input_files)
        sorted_names = [f if isinstance(f, str) else f[0] for f in sorted_files]
        if len(expected_order) > 0:
            expected_names = [f if isinstance(f, str) else f[0] for f in expected_order]
            assert sorted_names == expected_names, (
                f"Expected {expected_names}, got {sorted_names}"
            )

    @pytest.mark.parametrize(
        "sort_option,files,expected_order",
        [
            (
                "sort_by_loc",
                [
                    ("a.py", "/path/to/a.py", 100),
                    ("b.py", "/path/to/b.py", 50),
                    ("c.py", "/path/to/c.py", 200),
                ],
                ["c.py", "a.py", "b.py"],
            ),
            (
                "sort_by_size",
                [
                    ("a.txt", "/path/to/a.txt", 0, 1024),
                    ("b.txt", "/path/to/b.txt", 0, 2048),
                    ("c.txt", "/path/to/c.txt", 0, 512),
                ],
                ["b.txt", "a.txt", "c.txt"],
            ),
            (
                "sort_by_mtime",
                [
                    ("a.txt", "/path/to/a.txt", 0, 0, 1609459200),
                    ("b.txt", "/path/to/b.txt", 0, 0, 1612137600),
                    ("c.txt", "/path/to/c.txt", 0, 0, 1606780800),
                ],
                ["b.txt", "a.txt", "c.txt"],
            ),
        ],
    )
    def test_sort_by_statistics(self, sort_option, files, expected_order):
        kwargs = {sort_option: True}
        sorted_files = sort_files_by_type(files, **kwargs)
        sorted_names = [item[0] for item in sorted_files]
        assert sorted_names == expected_order, (
            f"Expected {expected_order}, got {sorted_names}"
        )

    def test_sort_with_multiple_criteria(self):
        files = [
            ("a.py", "/path/to/a.py", 100, 1024, 1609459200),
            ("b.py", "/path/to/b.py", 100, 2048, 1609459200),
            ("c.py", "/path/to/c.py", 200, 512, 1609459200),
            ("d.py", "/path/to/d.py", 100, 1024, 1612137600),
        ]
        sorted_files = sort_files_by_type(
            files, sort_by_loc=True, sort_by_size=True, sort_by_mtime=True
        )
        sorted_names = [item[0] for item in sorted_files]
        expected_order = ["c.py", "b.py", "d.py", "a.py"]
        assert sorted_names == expected_order, (
            f"Expected {expected_order}, got {sorted_names}"
        )


class TestDirectoryExporter:
    def test_init(self):
        """Test initializing DirectoryExporter."""
        structure = {"_files": ["file1.txt"], "dir1": {"_files": ["file2.py"]}}
        exporter = DirectoryExporter(structure, "test_root")
        assert exporter.structure == structure
        assert exporter.root_name == "test_root"
        assert exporter.base_path is None
        assert not exporter.show_full_path

    def test_init_with_full_path(self):
        """Test initializing DirectoryExporter with full paths."""
        structure = {
            "_files": [("file1.txt", "/path/to/file1.txt")],
            "dir1": {"_files": [("file2.py", "/path/to/dir1/file2.py")]},
        }
        exporter = DirectoryExporter(structure, "test_root", base_path="/path/to")
        assert exporter.structure == structure
        assert exporter.root_name == "test_root"
        assert exporter.base_path == "/path/to"
        assert exporter.show_full_path

    def test_init_with_statistics(self):
        """Test initializing DirectoryExporter with statistics."""
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
        exporter = DirectoryExporter(
            structure,
            "test_root",
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
                lambda c: "# 📂" in c,
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
    content_checks: List[Callable[[str], bool]],
):
    """Test exporting to different formats."""
    structure, _ = get_directory_structure(sample_directory)
    output_path = os.path.join(output_dir, f"structure.{format_extension}")
    export_structure(structure, sample_directory, format_name, output_path)
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
):
    """Test exporting with various options."""
    get_structure_kwargs = {}
    if option_name in [
        "show_full_path",
        "sort_by_loc",
        "sort_by_size",
        "sort_by_mtime",
    ]:
        get_structure_kwargs[option_name] = option_value
    if option_name == "show_full_path":
        structure, _ = get_directory_structure(
            sample_directory, show_full_path=option_value
        )
    elif option_name == "sort_by_loc":
        structure, _ = get_directory_structure(
            sample_directory, sort_by_loc=option_value
        )
    elif option_name == "sort_by_size":
        structure, _ = get_directory_structure(
            sample_directory, sort_by_size=option_value
        )
    elif option_name == "sort_by_mtime":
        structure, _ = get_directory_structure(
            sample_directory, sort_by_mtime=option_value
        )
    else:
        structure, _ = get_directory_structure(sample_directory)
    export_kwargs = {option_name: option_value}
    output_path = os.path.join(output_dir, f"structure_{option_name}.txt")
    export_structure(structure, sample_directory, "txt", output_path, **export_kwargs)
    assert os.path.exists(output_path)
    with open(output_path, encoding="utf-8") as f:
        content = f.read()
    assert content_check(content, sample_directory), (
        f"Content check failed for option {option_name}"
    )


def test_export_nested_structure(sample_directory: str, output_dir: str):
    """Test exporting nested directory structure."""
    nested_dir = os.path.join(sample_directory, "nested", "deep")
    os.makedirs(nested_dir, exist_ok=True)
    with open(os.path.join(nested_dir, "deep_file.txt"), "w") as f:
        f.write("Deep nested file")
    structure, _ = get_directory_structure(sample_directory)
    output_path = os.path.join(output_dir, "nested_structure.json")
    export_structure(structure, sample_directory, "json", output_path)
    with open(output_path, encoding="utf-8") as f:
        data = json.load(f)
    assert "nested" in data["structure"]
    assert "deep" in data["structure"]["nested"]
    assert "_files" in data["structure"]["nested"]["deep"]
    assert "deep_file.txt" in data["structure"]["nested"]["deep"]["_files"]


def test_export_invalid_format(temp_dir: str, output_dir: str):
    """Test exporting with invalid format."""
    structure = {"_files": ["file1.txt"]}
    output_path = os.path.join(output_dir, "test_export.invalid")
    with pytest.raises(ValueError) as excinfo:
        export_structure(structure, temp_dir, "invalid", output_path)
    assert "Unsupported format" in str(excinfo.value)


def test_export_error_handling(
    sample_directory: str,
    output_dir: str,
    mocker: MockerFixture,
):
    """Test error handling during export."""
    structure, _ = get_directory_structure(sample_directory)
    output_path = os.path.join(output_dir, "structure.txt")
    mocker.patch("builtins.open", side_effect=PermissionError("Permission denied"))
    with pytest.raises(PermissionError):
        export_structure(structure, sample_directory, "txt", output_path)


def test_export_with_max_depth_indicator(temp_dir: str, output_dir: str):
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
        export_structure(structure, temp_dir, fmt, output_path)
        with open(output_path, encoding="utf-8") as f:
            content = f.read()
        assert indicator in content, (
            f"Max depth indicator '{indicator}' not found in {fmt} export"
        )


def test_export_with_statistics(sample_directory: str, output_dir: str):
    """Test exporting with statistics (LOC, size, mtime)."""
    structure, _ = get_directory_structure(
        sample_directory, sort_by_loc=True, sort_by_size=True, sort_by_mtime=True
    )
    format_indicators = {
        "txt": [
            r"lines",
            r"[KMG]?B",
            r"Today|Yesterday|\d{4}-\d{2}-\d{2}",
        ],  # Fixed pattern
        "json": [r'"show_loc": true', r'"show_size": true', r'"show_mtime": true'],
        "html": [
            r"lines",
            r"[KMG]?B",  # Fixed pattern
            r"Today|Yesterday|\d{4}-\d{2}-\d{2}|format_timestamp",
        ],
        "md": [
            r"lines",
            r"[KMG]?B",
            r"Today|Yesterday|\d{4}-\d{2}-\d{2}",
        ],  # Fixed pattern
        "jsx": [r"locCount", r"sizeCount", r"mtimeCount"],
    }
    for fmt, patterns in format_indicators.items():
        output_path = os.path.join(output_dir, f"stats_export.{fmt}")
        export_structure(
            structure,
            sample_directory,
            fmt,
            output_path,
            sort_by_loc=True,
            sort_by_size=True,
            sort_by_mtime=True,
        )
        with open(output_path, encoding="utf-8") as f:
            content = f.read()
        for pattern in patterns:
            assert re.search(pattern, content), (
                f"Pattern '{pattern}' not found in {fmt} export"
            )


def test_large_structure_export(output_dir: str):
    """Test exporting a large directory structure."""
    structure = generate_large_structure(depth=5, files_per_dir=10, dir_branching=3)
    for fmt in ["txt", "json", "html", "md", "jsx"]:
        output_path = os.path.join(output_dir, f"large_structure.{fmt}")
        export_structure(structure, "large_root", fmt, output_path)
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0, f"Exported {fmt} file is empty"
        with open(output_path, encoding="utf-8") as f:
            content = f.read()
        if fmt == "txt":
            assert "📂 large_root" in content
            assert "file_1_0.txt" in content
        elif fmt == "json":
            assert '"root": "large_root"' in content
            data = json.loads(content)
            assert "_files" in data["structure"]
        elif fmt == "html":
            assert "<!DOCTYPE html>" in content
            assert "large_root" in content
        elif fmt == "md":
            assert "# 📂 large_root" in content
        elif fmt == "jsx":
            assert "import React" in content
            assert 'name="large_root"' in content


def test_unicode_file_names(output_dir: str):
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
        export_structure(unicode_structure, "unicode_root", fmt, output_path)
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
    error_type: type,
    error_msg: str,
):
    """Test handling different error types during export."""
    structure, _ = get_directory_structure(sample_directory)
    output_path = os.path.join(output_dir, f"error_{error_type.__name__}.txt")
    if error_type is OSError:
        error = OSError(28, error_msg)
    else:
        error = error_type(error_msg)
    with patch("recursivist.exports.DirectoryExporter.to_txt", side_effect=error):
        with pytest.raises(Exception) as excinfo:
            export_structure(structure, sample_directory, "txt", output_path)
        assert error_msg in str(excinfo.value)


def test_to_jsx_with_long_paths(output_dir: str):
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
    exporter = DirectoryExporter(long_structure, "long_root")
    exporter.to_jsx(output_path)
    assert os.path.exists(output_path)
    with open(output_path, encoding="utf-8") as f:
        content = f.read()
    assert f'name="{long_name}.txt"' in content
    assert f'name="{long_name}.py"' in content
    assert f'name="dir_{long_name}"' in content
    assert f'name="nested_{long_name}.md"' in content


def test_export_with_excessive_loc(temp_dir: str, output_dir: str):
    """Test exporting files with very large line counts."""
    test_file = os.path.join(temp_dir, "many_lines.py")
    with open(test_file, "w") as f:
        for i in range(10000):
            f.write(f"print('Line {i}')\n")
    structure, _ = get_directory_structure(temp_dir, sort_by_loc=True)
    for fmt in ["txt", "json", "html", "md", "jsx"]:
        output_path = os.path.join(output_dir, f"large_loc.{fmt}")
        export_structure(structure, temp_dir, fmt, output_path, sort_by_loc=True)
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


def test_many_unique_extensions(output_dir: str):
    """Test export with many unique file extensions."""
    many_extensions_structure: Dict[str, List[str]] = {"_files": []}
    for i in range(100):
        ext = random_string(5)
        many_extensions_structure["_files"].append(f"file_{i}.{ext}")
    output_path = os.path.join(output_dir, "many_extensions.html")
    export_structure(many_extensions_structure, "extensions_test", "html", output_path)
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


def test_problematic_filenames(output_dir: str):
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
        export_structure(problematic_structure, "escape_test", fmt, output_path)
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


def test_combined_export_options(output_dir: str):
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
        export_structure(
            complex_structure,
            "complex_root",
            fmt,
            output_path,
            show_full_path=True,
            sort_by_loc=True,
            sort_by_size=True,
            sort_by_mtime=True,
        )
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


def generate_large_structure(
    depth: int, files_per_dir: int, dir_branching: int
) -> Dict:
    """Generate a large directory structure for testing."""

    def _generate_recursive(current_depth: int) -> Dict:
        if current_depth > depth:
            return {}
        structure: Dict[str, Any] = {}
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
