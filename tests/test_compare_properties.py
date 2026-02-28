"""Property-based tests for the compare module functionality."""

from typing import Any
from unittest.mock import ANY, MagicMock, patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from recursivist.compare import (
    build_comparison_tree,
    compare_directory_structures,
    display_comparison,
    export_comparison,
)


@st.composite
def comparison_structure(draw: st.DrawFn, ensure_files: bool = False) -> dict[str, Any]:
    """Generate a structure for comparison testing."""
    structure: dict[str, Any] = {}
    file_list: list[Any] = []
    if ensure_files:
        filename = "sample.txt"
        file_path = "/path/to/sample.txt"
        loc = 100
        size = 1024
        mtime = 1600000000.0
        file_list.append((filename, file_path, loc, size, mtime))
    for _ in range(draw(st.integers(min_value=0, max_value=5))):
        filename = draw(
            st.text(
                alphabet=st.characters(
                    whitelist_categories=("Lu", "Ll", "Nd"),
                    whitelist_characters="_-",
                ),
                min_size=1,
                max_size=20,
            )
        ) + draw(st.sampled_from([".txt", ".py", ".md", ".json", ".js"]))
        if draw(st.booleans()):
            file_path = "/path/to/" + filename
            loc = draw(st.integers(min_value=1, max_value=1000))
            size = draw(st.integers(min_value=1, max_value=10 * 1024 * 1024))
            mtime = draw(st.floats(min_value=1000000, max_value=1672531200))
            file_list.append((filename, file_path, loc, size, mtime))
        else:
            file_list.append(filename)
    structure["_files"] = file_list
    if draw(st.booleans()):
        structure["_loc"] = draw(st.integers(min_value=0, max_value=10000))
    if draw(st.booleans()):
        structure["_size"] = draw(st.integers(min_value=0, max_value=100 * 1024 * 1024))
    if draw(st.booleans()):
        structure["_mtime"] = draw(st.floats(min_value=1000000, max_value=1672531200))
    for _ in range(draw(st.integers(min_value=0, max_value=3))):
        dir_name = draw(
            st.text(
                alphabet=st.characters(
                    whitelist_categories=("Lu", "Ll", "Nd"),
                    whitelist_characters="_-",
                ),
                min_size=1,
                max_size=10,
            )
        )
        if draw(st.booleans()) and draw(st.booleans()):
            structure[dir_name] = {"_max_depth_reached": True}
        else:
            sub_structure: dict[str, Any] = {}
            sub_file_list: list[Any] = []
            for _ in range(draw(st.integers(min_value=0, max_value=3))):
                sub_filename = draw(
                    st.text(
                        alphabet=st.characters(
                            whitelist_categories=("Lu", "Ll", "Nd"),
                            whitelist_characters="_-",
                        ),
                        min_size=1,
                        max_size=15,
                    )
                ) + draw(st.sampled_from([".txt", ".py", ".md"]))
                sub_file_list.append(sub_filename)
            sub_structure["_files"] = sub_file_list
            if draw(st.booleans()):
                sub_structure["_loc"] = draw(st.integers(min_value=0, max_value=5000))
            if draw(st.booleans()):
                sub_structure["_size"] = draw(
                    st.integers(min_value=0, max_value=50 * 1024 * 1024)
                )
            if draw(st.booleans()):
                sub_structure["_mtime"] = draw(
                    st.floats(min_value=1000000, max_value=1672531200)
                )
            structure[dir_name] = sub_structure
    return structure


@st.composite
def comparison_pair(
    draw: st.DrawFn, ensure_files: bool = False
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Generate a pair of related structures for comparison testing."""
    base_structure: dict[str, Any] = draw(
        comparison_structure(ensure_files=ensure_files)
    )
    modified_structure: dict[str, Any] = {}
    if "_files" in base_structure:
        modified_files: list[Any] = []
        for file_item in base_structure["_files"]:
            if draw(st.booleans()):
                modified_files.append(file_item)
        for _ in range(draw(st.integers(min_value=0, max_value=3))):
            new_filename = draw(
                st.text(
                    alphabet=st.characters(
                        whitelist_categories=("Lu", "Ll", "Nd"),
                        whitelist_characters="_-",
                    ),
                    min_size=1,
                    max_size=15,
                )
            ) + draw(st.sampled_from([".txt", ".py", ".md", ".json", ".js"]))
            if draw(st.booleans()):
                file_path = "/path/to/" + new_filename
                loc = draw(st.integers(min_value=1, max_value=1000))
                size = draw(st.integers(min_value=1, max_value=10 * 1024 * 1024))
                mtime = draw(st.floats(min_value=1000000, max_value=1672531200))
                modified_files.append((new_filename, file_path, loc, size, mtime))
            else:
                modified_files.append(new_filename)
        modified_structure["_files"] = modified_files
    if "_loc" in base_structure and draw(st.booleans()):
        modified_structure["_loc"] = base_structure["_loc"] + draw(
            st.integers(min_value=-100, max_value=100)
        )
    if "_size" in base_structure and draw(st.booleans()):
        modified_structure["_size"] = base_structure["_size"] + draw(
            st.integers(min_value=-1024, max_value=1024)
        )
    if "_mtime" in base_structure and draw(st.booleans()):
        modified_structure["_mtime"] = base_structure["_mtime"] + draw(
            st.floats(min_value=-86400, max_value=86400)
        )
    for key, value in base_structure.items():
        if key not in ["_files", "_loc", "_size", "_mtime", "_max_depth_reached"]:
            if draw(st.booleans()):
                modified_structure[key] = value
    for _ in range(draw(st.integers(min_value=0, max_value=2))):
        dir_name = draw(
            st.text(
                alphabet=st.characters(
                    whitelist_categories=("Lu", "Ll", "Nd"),
                    whitelist_characters="_-",
                ),
                min_size=1,
                max_size=10,
            )
        )
        if dir_name not in modified_structure:
            modified_structure[dir_name] = draw(comparison_structure())
    return (base_structure, modified_structure)


safe_path = st.text(
    alphabet=st.characters(
        blacklist_characters='\0\n\r\\/:*?"<>|',
    ),
    min_size=1,
    max_size=20,
)


class TestCompareDirectoryStructures:
    """Property-based tests for compare_directory_structures function."""

    @given(dir1=safe_path, dir2=safe_path)
    @settings(max_examples=10)
    def test_comparison_returns_structures(self, dir1: str, dir2: str) -> None:
        """Test that compare_directory_structures returns valid structures."""
        with patch("recursivist.compare.get_directory_structure") as mock_get_structure:
            mock_get_structure.side_effect = [
                ({"_files": ["file1.txt"]}, {".txt"}),
                ({"_files": ["file2.txt"]}, {".txt"}),
            ]
            structure1, structure2, extensions = compare_directory_structures(
                dir1, dir2
            )
            assert structure1 == {"_files": ["file1.txt"]}, (
                "Should return structure1 from get_directory_structure"
            )
            assert structure2 == {"_files": ["file2.txt"]}, (
                "Should return structure2 from get_directory_structure"
            )
            assert extensions == {".txt"}, "Should return combined extensions"
            assert mock_get_structure.call_count == 2, (
                "get_directory_structure should be called twice"
            )
            mock_get_structure.assert_any_call(
                dir1,
                None,
                None,
                None,
                exclude_patterns=None,
                include_patterns=None,
                max_depth=0,
                show_full_path=False,
                sort_by_loc=False,
                sort_by_size=False,
                sort_by_mtime=False,
            )
            mock_get_structure.assert_any_call(
                dir2,
                None,
                None,
                None,
                exclude_patterns=None,
                include_patterns=None,
                max_depth=0,
                show_full_path=False,
                sort_by_loc=False,
                sort_by_size=False,
                sort_by_mtime=False,
            )

    @given(dir1=safe_path, dir2=safe_path)
    @settings(max_examples=5)
    def test_comparison_with_options(self, dir1: str, dir2: str) -> None:
        """Test compare_directory_structures with various options."""
        with patch("recursivist.compare.get_directory_structure") as mock_get_structure:
            mock_get_structure.side_effect = [
                ({"_files": ["file1.txt"]}, {".txt"}),
                ({"_files": ["file2.txt"]}, {".txt"}),
            ]
            exclude_dirs = ["node_modules", "dist"]
            exclude_extensions = {".pyc", ".log"}
            exclude_patterns = [r"\.tmp$", r"^test_"]
            include_patterns = [r"\.py$"]
            max_depth = 2
            compare_directory_structures(
                dir1,
                dir2,
                exclude_dirs,
                ".gitignore",
                exclude_extensions,
                exclude_patterns=exclude_patterns,
                include_patterns=include_patterns,
                max_depth=max_depth,
                show_full_path=True,
                sort_by_loc=True,
                sort_by_size=True,
                sort_by_mtime=True,
            )
            mock_get_structure.assert_any_call(
                dir1,
                exclude_dirs,
                ".gitignore",
                exclude_extensions,
                exclude_patterns=ANY,
                include_patterns=ANY,
                max_depth=max_depth,
                show_full_path=True,
                sort_by_loc=True,
                sort_by_size=True,
                sort_by_mtime=True,
            )


class TestBuildComparisonTree:
    """Property-based tests for build_comparison_tree function."""

    @given(
        structures=comparison_pair(ensure_files=True),
        color_map=st.dictionaries(
            st.text(min_size=1, max_size=10),
            st.text(min_size=1, max_size=10),
            min_size=1,
            max_size=5,
        ),
    )
    @settings(max_examples=10)
    def test_build_comparison_tree(
        self,
        structures: tuple[dict[str, Any], dict[str, Any]],
        color_map: dict[str, str],
    ) -> None:
        """Test that build_comparison_tree builds a valid tree."""
        structure1, structure2 = structures
        mock_tree = MagicMock()
        mock_tree.add.return_value = mock_tree
        build_comparison_tree(structure1, structure2, mock_tree, color_map)
        assert mock_tree.add.call_count > 0, "Tree.add should have been called"

    @given(
        structures=comparison_pair(ensure_files=True),
        color_map=st.dictionaries(
            st.text(min_size=1, max_size=10),
            st.text(min_size=1, max_size=10),
            min_size=1,
            max_size=5,
        ),
    )
    @settings(max_examples=5)
    def test_build_comparison_tree_with_options(
        self,
        structures: tuple[dict[str, Any], dict[str, Any]],
        color_map: dict[str, str],
    ) -> None:
        """Test build_comparison_tree with various options."""
        structure1, structure2 = structures
        mock_tree = MagicMock()
        mock_tree.add.return_value = mock_tree
        build_comparison_tree(
            structure1,
            structure2,
            mock_tree,
            color_map,
            parent_name="root",
            show_full_path=True,
            sort_by_loc=True,
            sort_by_size=True,
            sort_by_mtime=True,
        )
        assert mock_tree.add.call_count > 0, "Tree.add should have been called"


class TestDisplayComparison:
    """Property-based tests for display_comparison function."""

    @given(dir1=safe_path, dir2=safe_path)
    @settings(max_examples=5)
    def test_display_comparison(self, dir1: str, dir2: str) -> None:
        """Test that display_comparison calls the necessary functions."""
        with (
            patch("recursivist.compare.compare_directory_structures") as mock_compare,
            patch("recursivist.compare.generate_color_for_extension") as mock_color_map,
            patch("recursivist.compare.Console") as mock_console,
            patch("recursivist.compare.build_comparison_tree") as mock_build_tree,
            patch("recursivist.compare.Tree") as mock_tree,
        ):
            mock_compare.return_value = ({"_files": []}, {"_files": []}, {".txt"})
            mock_color_map.return_value = "#FFFFFF"
            display_comparison(dir1, dir2)
            mock_compare.assert_called_once()
            mock_tree.assert_called()
            mock_build_tree.assert_called()
            mock_console.return_value.print.assert_called()

    @given(dir1=safe_path, dir2=safe_path)
    @settings(max_examples=5)
    def test_display_comparison_with_options(self, dir1: str, dir2: str) -> None:
        """Test display_comparison with various options."""
        with (
            patch("recursivist.compare.compare_directory_structures") as mock_compare,
            patch("recursivist.compare.generate_color_for_extension") as mock_color_map,
        ):
            mock_compare.return_value = ({"_files": []}, {"_files": []}, {".txt"})
            mock_color_map.return_value = "#FFFFFF"
            display_comparison(
                dir1,
                dir2,
                exclude_dirs=["node_modules"],
                ignore_file=".gitignore",
                exclude_extensions={".log"},
                exclude_patterns=["test_*"],
                include_patterns=["*.py"],
                use_regex=True,
                max_depth=2,
                show_full_path=True,
                sort_by_loc=True,
                sort_by_size=True,
                sort_by_mtime=True,
            )
            mock_compare.assert_called_once_with(
                dir1,
                dir2,
                ["node_modules"],
                ".gitignore",
                {".log"},
                exclude_patterns=ANY,
                include_patterns=ANY,
                max_depth=2,
                show_full_path=True,
                sort_by_loc=True,
                sort_by_size=True,
                sort_by_mtime=True,
            )


class TestExportComparison:
    """Property-based tests for export_comparison function."""

    @given(
        dir1=safe_path,
        dir2=safe_path,
        output_path=safe_path,
    )
    @settings(max_examples=5)
    def test_export_comparison(self, dir1: str, dir2: str, output_path: str) -> None:
        """Test that export_comparison exports to HTML."""
        with (
            patch("recursivist.compare.compare_directory_structures") as mock_compare,
            patch("recursivist.compare._export_comparison_to_html") as mock_export_html,
        ):
            mock_compare.return_value = ({"_files": []}, {"_files": []}, {".txt"})
            export_comparison(dir1, dir2, "html", output_path)
            mock_export_html.assert_called_once()

    @given(
        dir1=safe_path,
        dir2=safe_path,
        output_path=safe_path,
    )
    @settings(max_examples=5)
    def test_export_comparison_invalid_format(
        self, dir1: str, dir2: str, output_path: str
    ) -> None:
        """Test that export_comparison raises an error for invalid formats."""
        with pytest.raises(ValueError) as excinfo:
            export_comparison(dir1, dir2, "invalid", output_path)
        assert "Only HTML format is supported" in str(excinfo.value)

    @given(
        dir1=safe_path,
        dir2=safe_path,
        output_path=safe_path,
    )
    @settings(max_examples=5)
    def test_export_comparison_with_options(
        self, dir1: str, dir2: str, output_path: str
    ) -> None:
        """Test export_comparison with various options."""
        with (
            patch("recursivist.compare.compare_directory_structures") as mock_compare,
            patch("recursivist.compare._export_comparison_to_html") as _,
        ):
            mock_compare.return_value = ({"_files": []}, {"_files": []}, {".txt"})
            export_comparison(
                dir1,
                dir2,
                "html",
                output_path,
                exclude_dirs=["node_modules"],
                ignore_file=".gitignore",
                exclude_extensions={".log"},
                exclude_patterns=["test_*"],
                include_patterns=["*.py"],
                use_regex=True,
                max_depth=2,
                show_full_path=True,
                sort_by_loc=True,
                sort_by_size=True,
                sort_by_mtime=True,
            )
            mock_compare.assert_called_once_with(
                dir1,
                dir2,
                ["node_modules"],
                ".gitignore",
                {".log"},
                exclude_patterns=ANY,
                include_patterns=ANY,
                max_depth=2,
                show_full_path=True,
                sort_by_loc=True,
                sort_by_size=True,
                sort_by_mtime=True,
            )


class TestExportComparisonToHTML:
    """Property-based tests for _export_comparison_to_html function."""

    @given(
        structures=comparison_pair(),
        dir1_name=safe_path,
        dir2_name=safe_path,
    )
    @settings(max_examples=5)
    def test_export_comparison_to_html(
        self,
        structures: tuple[dict[str, Any], dict[str, Any]],
        dir1_name: str,
        dir2_name: str,
    ) -> None:
        """Test that _export_comparison_to_html creates a valid HTML file."""
        structure1, structure2 = structures
        comparison_data: dict[str, Any] = {
            "dir1": {
                "path": f"/path/to/{dir1_name}",
                "name": dir1_name,
                "structure": structure1,
            },
            "dir2": {
                "path": f"/path/to/{dir2_name}",
                "name": dir2_name,
                "structure": structure2,
            },
            "metadata": {
                "exclude_patterns": [],
                "include_patterns": [],
                "pattern_type": "glob",
                "max_depth": 0,
                "show_full_path": False,
                "sort_by_loc": False,
                "sort_by_size": False,
                "sort_by_mtime": False,
            },
        }
        with patch("builtins.open", MagicMock()) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            from recursivist.compare import _export_comparison_to_html

            with patch.object(mock_file, "write") as mock_write:
                _export_comparison_to_html(comparison_data, "output.html")
                mock_open.assert_called_once_with("output.html", "w", encoding="utf-8")
                assert mock_write.call_count > 0, "No data was written to the file"


if __name__ == "__main__":
    pytest.main()
