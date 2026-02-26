import os
import re
import time
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from rich.text import Text

from recursivist.compare import build_comparison_tree
from recursivist.core import build_tree
from recursivist.exports import DirectoryExporter


class TestBuildTree:
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
        kwargs = {option: True}
        build_tree(structure_with_stats, mock_tree, color_map, parent_name="", **kwargs)
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


class TestBuildComparisonTree:
    def test_identical_structures(
        self,
        mock_tree: MagicMock,
        color_map: dict[str, str],
        simple_structure: dict[str, Any],
    ) -> None:
        """Test comparing identical structures."""
        build_comparison_tree(simple_structure, simple_structure, mock_tree, color_map)
        assert mock_tree.add.call_count == 3
        calls = [
            call
            for call in mock_tree.add.call_args_list
            if isinstance(call.args[0], Text)
        ]
        styles = [str(call.args[0].style) for call in calls]
        assert not any("on green" in style for style in styles)
        assert not any("on red" in style for style in styles)

    def test_different_files(
        self, mock_tree: MagicMock, color_map: dict[str, str]
    ) -> None:
        """Test comparing structures with different files."""
        structure1 = {"_files": ["file1.txt", "common.py"]}
        structure2 = {"_files": ["file2.txt", "common.py"]}
        build_comparison_tree(structure1, structure2, mock_tree, color_map)
        calls = [
            call
            for call in mock_tree.add.call_args_list
            if isinstance(call.args[0], Text)
        ]
        texts_and_styles = [
            (call.args[0].plain, str(call.args[0].style)) for call in calls
        ]
        assert any(
            "file1.txt" in text and "on green" in style
            for text, style in texts_and_styles
        )
        assert any(
            "common.py" in text and "on green" not in style and "on red" not in style
            for text, style in texts_and_styles
        )

    def test_different_directories(
        self, mock_tree: MagicMock, mock_subtree: MagicMock, color_map: dict[str, str]
    ) -> None:
        """Test comparing structures with different directories."""
        structure1 = {
            "dir1": {"_files": ["file1.txt"]},
            "common_dir": {"_files": ["common.py"]},
        }
        structure2 = {
            "dir2": {"_files": ["file2.txt"]},
            "common_dir": {"_files": ["common.py"]},
        }
        mock_tree.add.return_value = mock_subtree
        build_comparison_tree(structure1, structure2, mock_tree, color_map)
        dir_calls = [
            call
            for call in mock_tree.add.call_args_list
            if isinstance(call.args[0], Text)
        ]
        dir_texts_styles = [
            (call.args[0].plain, str(call.args[0].style))
            for call in dir_calls
            if "📁" in call.args[0].plain
        ]
        assert any(
            "dir1" in text and "green" in style for text, style in dir_texts_styles
        )
        common_dir_calls = [
            call
            for call in mock_tree.add.call_args_list
            if not isinstance(call.args[0], Text) and "common_dir" in str(call.args[0])
        ]
        assert len(common_dir_calls) > 0

    def test_with_statistics(
        self, mock_tree: MagicMock, color_map: dict[str, str]
    ) -> None:
        """Test comparison tree with statistics."""
        now = time.time()
        structure1 = {
            "_loc": 100,
            "_size": 1024,
            "_mtime": now,
            "_files": [("file1.txt", "/path/to/file1.txt", 50, 512, now)],
        }
        structure2 = {
            "_loc": 200,
            "_size": 2048,
            "_mtime": now,
            "_files": [("file2.txt", "/path/to/file2.txt", 100, 1024, now)],
        }
        build_comparison_tree(
            structure1,
            structure2,
            mock_tree,
            color_map,
            sort_by_loc=True,
            sort_by_size=True,
            sort_by_mtime=True,
        )
        calls = [
            str(call.args[0])
            for call in mock_tree.add.call_args_list
            if isinstance(call.args[0], Text)
        ]
        has_stats = False
        for call in calls:
            if (
                "lines" in call
                and "B" in call
                and (
                    "Today" in call
                    or "Yesterday" in call
                    or re.search(r"\d{4}-\d{2}-\d{2}", call)
                )
            ):
                has_stats = True
                break
        assert has_stats, "No statistics indicators found in comparison tree"

    def test_with_complex_structures(
        self, mock_tree: MagicMock, mock_subtree: MagicMock, color_map: dict[str, str]
    ) -> None:
        """Test comparison with complex nested structures."""
        structure1 = {
            "_files": ["common1.txt", "only1.txt"],
            "dir1": {
                "_files": ["dir1_file.txt"],
                "nested1": {"_files": ["nested1_file.txt"]},
            },
            "common_dir": {"_files": ["common_file.txt", "only_in_1.txt"]},
        }
        structure2 = {
            "_files": ["common1.txt", "only2.txt"],
            "dir2": {
                "_files": ["dir2_file.txt"],
                "nested2": {"_files": ["nested2_file.txt"]},
            },
            "common_dir": {"_files": ["common_file.txt", "only_in_2.txt"]},
        }
        all_calls = []

        def side_effect(*args: Any, **kwargs: Any) -> MagicMock:
            all_calls.append((args, kwargs))
            return mock_subtree

        mock_tree.add.side_effect = side_effect
        mock_subtree.add.side_effect = side_effect
        build_comparison_tree(structure1, structure2, mock_tree, color_map)
        file_texts_styles = []
        for args, _ in all_calls:
            if args and isinstance(args[0], Text) and "📄" in args[0].plain:
                file_texts_styles.append((args[0].plain, str(args[0].style)))
        assert any(
            "only1.txt" in text and "on green" in style
            for text, style in file_texts_styles
        )
        assert any(
            "only_in_1.txt" in text and "on green" in style
            for text, style in file_texts_styles
        )
        assert any(
            "common1.txt" in text and "on green" not in style and "on red" not in style
            for text, style in file_texts_styles
        )

    def test_with_max_depth(
        self, mock_tree: MagicMock, mock_subtree: MagicMock, color_map: dict[str, str]
    ) -> None:
        """Test comparison tree with max depth indicators."""
        structure1 = {
            "_files": ["file1.txt"],
            "subdir": {
                "_max_depth_reached": True,
            },
        }
        structure2 = {"_files": ["file2.txt"], "subdir": {"_files": ["subfile.txt"]}}
        mock_tree.add.return_value = mock_subtree
        build_comparison_tree(structure1, structure2, mock_tree, color_map)
        subtree_calls = [
            call.args[0]
            for call in mock_subtree.add.call_args_list
            if isinstance(call.args[0], Text)
        ]
        assert any("max depth reached" in text.plain for text in subtree_calls)


class TestDirectoryExporter:
    @pytest.mark.parametrize(
        "format_name,format_method,expected_content",
        [
            ("txt", "to_txt", ["📂 test_root", "file1.txt", "file2.py", "file3.md"]),
            ("md", "to_markdown", ["# 📂 test_root", "`file1.txt`"]),
            (
                "html",
                "to_html",
                ["<!DOCTYPE html>", "<html>", 'class="file"'],
            ),
            ("json", "to_json", ["root", "structure", "_files"]),
        ],
    )
    def test_export_formats(
        self,
        simple_structure: dict[str, Any],
        tmp_path: Path,
        format_name: str,
        format_method: str,
        expected_content: list[str],
    ) -> None:
        """Test DirectoryExporter's format-specific export methods."""
        output_path = os.path.join(tmp_path, f"test_output.{format_name}")
        exporter = DirectoryExporter(simple_structure, "test_root")
        getattr(exporter, format_method)(output_path)
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
        md_exporter = DirectoryExporter(nested_structure, "test_root")
        md_exporter.to_markdown(md_output_path)
        with open(md_output_path, encoding="utf-8") as f:
            md_content = f.read()
        assert "**subdir1**" in md_content or "**subdir2**" in md_content
        html_output_path = os.path.join(tmp_path, "test_dirs.html")
        html_exporter = DirectoryExporter(nested_structure, "test_root")
        html_exporter.to_html(html_output_path)
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
        exporter = DirectoryExporter(structure_with_stats, "test_root", **kwargs)
        exporter.to_txt(output_path)
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
        exporter = DirectoryExporter(
            structure_with_stats, "test_root", base_path="/path/to"
        )
        exporter.to_txt(output_path)
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
        exporter = DirectoryExporter(simple_structure, "test_root")
        error: Exception
        if error_type is OSError:
            error = OSError(28, error_msg)
        else:
            error = error_type(error_msg)
        with patch("builtins.open", side_effect=error):
            with pytest.raises(Exception) as excinfo:
                exporter.to_txt(output_path)
            assert error_msg in str(excinfo.value)

    def test_export_with_max_depth(
        self, max_depth_structure: dict[str, Any], tmp_path: Path
    ) -> None:
        """Test exporting with max depth indicators."""
        exporter = DirectoryExporter(max_depth_structure, "max_depth_root")
        txt_path = os.path.join(tmp_path, "max_depth.txt")
        exporter.to_txt(txt_path)
        with open(txt_path, encoding="utf-8") as f:
            content = f.read()
        assert "⋯ (max depth reached)" in content
        md_path = os.path.join(tmp_path, "max_depth.md")
        exporter.to_markdown(md_path)
        with open(md_path, encoding="utf-8") as f:
            content = f.read()
        assert "⋯ *(max depth reached)*" in content
        html_path = os.path.join(tmp_path, "max_depth.html")
        exporter.to_html(html_path)
        with open(html_path, encoding="utf-8") as f:
            content = f.read()
        assert "max-depth" in content

    def test_jsx_export(self, nested_structure: dict[str, Any], tmp_path: Path) -> None:
        """Test JSX export with mock."""
        output_path = os.path.join(tmp_path, "test_output.jsx")
        with patch("recursivist.exports.generate_jsx_component") as mock_generate:
            exporter = DirectoryExporter(nested_structure, "test_root")
            exporter.to_jsx(output_path)
            mock_generate.assert_called_once_with(
                nested_structure, "test_root", output_path, False, False, False, False
            )
            mock_generate.reset_mock()
            exporter = DirectoryExporter(
                nested_structure,
                "test_root",
                sort_by_loc=True,
                sort_by_size=True,
                sort_by_mtime=True,
            )
            exporter.to_jsx(output_path)
            mock_generate.assert_called_once_with(
                nested_structure, "test_root", output_path, False, True, True, True
            )
