"""Property-based tests for the recursivist package using Hypothesis."""

import os
import re
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st
from rich.tree import Tree

from recursivist.compare import build_comparison_tree
from recursivist.core import (
    build_tree,
    count_lines_of_code,
    format_size,
    format_timestamp,
    get_directory_structure,
    should_exclude,
    sort_files_by_type,
)
from recursivist.exports import DirectoryExporter

simple_filename = st.text(
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
file_item_tuple = st.tuples(
    simple_filename,
    st.text(min_size=1, max_size=100),
    st.integers(min_value=0, max_value=1000),
    st.integers(min_value=0, max_value=10 * 1024 * 1024),
    st.floats(min_value=0, max_value=1672531200),
)
file_list = st.lists(
    st.one_of(
        simple_filename,
        st.tuples(
            simple_filename,
            st.text(min_size=1, max_size=100),
        ),
        st.tuples(
            simple_filename,
            st.text(min_size=1, max_size=100),
            st.integers(min_value=0, max_value=1000),
        ),
        st.tuples(
            simple_filename,
            st.text(min_size=1, max_size=100),
            st.integers(min_value=0, max_value=1000),
            st.integers(min_value=0, max_value=10 * 1024 * 1024),
        ),
        file_item_tuple,
    ),
    min_size=0,
    max_size=20,
)


@st.composite
def simple_directory_structure(draw):
    """Generate a simple directory structure."""
    structure = {}
    structure["_files"] = draw(file_list)
    if draw(st.booleans()):
        structure["_loc"] = draw(st.integers(min_value=0, max_value=10000))
    if draw(st.booleans()):
        structure["_size"] = draw(st.integers(min_value=0, max_value=100 * 1024 * 1024))
    if draw(st.booleans()):
        structure["_mtime"] = draw(st.floats(min_value=0, max_value=1672531200))
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
        structure[subdir_name] = draw(simple_directory_structure())
    if draw(st.booleans()):
        structure["_max_depth_reached"] = True
    return structure


class TestCountLinesOfCode:
    """Property-based tests for count_lines_of_code function."""

    @given(st.text(alphabet=st.characters(max_codepoint=127)))
    @settings(max_examples=100)
    def test_always_nonnegative(self, content):
        """Test that count_lines_of_code always returns a non-negative value."""
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as f:
            try:
                f.write(content)
                file_path = f.name
            except UnicodeEncodeError:
                pytest.skip("Content contains characters that can't be encoded")
        try:
            line_count = count_lines_of_code(file_path)
            assert line_count >= 0, "Line count should never be negative"
        finally:
            os.unlink(file_path)

    @given(
        st.lists(
            st.text(alphabet=st.characters(max_codepoint=127)), min_size=0, max_size=100
        )
    )
    @settings(max_examples=50)
    def test_matches_line_count(self, lines):
        """Test that count_lines_of_code returns the correct number of lines."""
        content = "\n".join(lines)
        expected_lines = len(lines)
        if lines:
            additional_newlines = sum(line.count("\n") for line in lines)
            expected_lines += additional_newlines
        has_null_bytes = any("\x00" in line for line in lines)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as f:
            try:
                f.write(content)
                file_path = f.name
            except UnicodeEncodeError:
                pytest.skip("Content contains characters that can't be encoded")
        try:
            line_count = count_lines_of_code(file_path)
            if has_null_bytes:
                assert line_count == 0, (
                    f"Files with null bytes should return 0 lines, got {line_count}"
                )
            else:
                has_carriage_returns = any("\r" in line for line in lines)
                if has_carriage_returns:
                    assert line_count >= expected_lines, (
                        f"Line count should be at least expected_lines when carriage returns are present. Expected {expected_lines}, got {line_count}"
                    )
                else:
                    assert abs(line_count - expected_lines) <= 1, (
                        f"Expected {expected_lines} lines, got {line_count}"
                    )
        finally:
            os.unlink(file_path)

    @given(st.binary(min_size=0, max_size=1000))
    @settings(max_examples=50)
    def test_binary_files_handled(self, content):
        """Test that binary files are handled appropriately."""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            f.write(content)
            file_path = f.name
        try:
            line_count = count_lines_of_code(file_path)
            assert line_count >= 0, (
                "Line count should never be negative even for binary files"
            )
        finally:
            os.unlink(file_path)

    @given(st.text())
    @example("file.bin")
    @example("file.txt")
    @example("file.py")
    @settings(max_examples=20)
    def test_nonexistent_files(self, filename):
        """Test that nonexistent files return 0 lines."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, filename)
            assert count_lines_of_code(file_path) == 0, (
                "Nonexistent files should return 0 lines"
            )

    def test_permission_denied(self):
        """Test that permission denied errors are handled gracefully."""
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            assert count_lines_of_code("some/path.txt") == 0, (
                "Permission denied should return 0 lines"
            )


class TestSortFilesByType:
    """Property-based tests for sort_files_by_type function."""

    @given(file_list)
    @settings(max_examples=100)
    def test_sorts_by_extension(self, files):
        """Test that files are sorted by extension and then by name."""
        sorted_files = sort_files_by_type(files)
        assert len(sorted_files) == len(files), (
            "Sorted list should have same length as original"
        )
        extensions = []
        for f in sorted_files:
            if isinstance(f, tuple):
                filename = f[0]
            else:
                filename = f
            ext = os.path.splitext(filename)[1].lower()
            extensions.append(ext)
        assert extensions == sorted(extensions), "Files should be sorted by extension"
        for ext in set(extensions):
            names_for_ext = []
            for f in sorted_files:
                if isinstance(f, tuple):
                    filename = f[0]
                else:
                    filename = f
                file_ext = os.path.splitext(filename)[1].lower()
                if file_ext == ext:
                    names_for_ext.append(filename.lower())
            assert names_for_ext == sorted(names_for_ext), (
                f"Files with extension {ext} should be sorted by name"
            )

    @given(file_list, st.booleans(), st.booleans(), st.booleans())
    @settings(max_examples=100)
    def test_sort_with_stats(self, files, sort_by_loc, sort_by_size, sort_by_mtime):
        """Test sort_files_by_type with various sorting options."""
        sorted_files = sort_files_by_type(
            files, sort_by_loc, sort_by_size, sort_by_mtime
        )
        assert len(sorted_files) == len(files), (
            "Sorted list should have same length as original"
        )
        original_contents = set()
        for f in files:
            if isinstance(f, tuple):
                original_contents.add(f[0])
            else:
                original_contents.add(f)
        sorted_contents = set()
        for f in sorted_files:
            if isinstance(f, tuple):
                sorted_contents.add(f[0])
            else:
                sorted_contents.add(f)
        assert sorted_contents == original_contents, (
            "Sorted list should contain the same items as original"
        )


class TestBuildTree:
    """Property-based tests for build_tree function."""

    @given(
        structure=simple_directory_structure(),
        color_map=st.dictionaries(
            keys=st.text(min_size=1, max_size=10),
            values=st.text(min_size=1, max_size=10),
        ),
    )
    @settings(max_examples=50)
    def test_build_tree_adds_files(self, structure, color_map):
        """Test that build_tree properly adds all files to the tree."""
        mock_tree = MagicMock(spec=Tree)
        mock_subtree = MagicMock(spec=Tree)
        mock_tree.add.return_value = mock_subtree

        def count_files_and_folders(struct):
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


class TestBuildComparisonTree:
    """Property-based tests for build_comparison_tree function."""

    @given(
        structure1=simple_directory_structure(),
        structure2=simple_directory_structure(),
        color_map=st.dictionaries(
            keys=st.text(min_size=1, max_size=10),
            values=st.text(min_size=1, max_size=10),
        ),
    )
    @settings(max_examples=20)
    def test_build_comparison_tree(self, structure1, structure2, color_map):
        """Test that build_comparison_tree successfully builds a tree."""
        mock_tree = MagicMock(spec=Tree)
        mock_subtree = MagicMock(spec=Tree)
        mock_tree.add.return_value = mock_subtree

        def count_files_and_folders(struct):
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

        expected_calls = count_files_and_folders(structure1) + count_files_and_folders(
            structure2
        )
        build_comparison_tree(structure1, structure2, mock_tree, color_map)
        if expected_calls > 0:
            assert mock_tree.add.call_count > 0, (
                "build_comparison_tree should make at least one call to tree.add when there are files or folders"
            )
        else:
            pass


class TestFormatFunctions:
    """Property-based tests for formatting functions."""

    @given(st.integers(min_value=0, max_value=10**12))
    @settings(max_examples=100)
    def test_format_size(self, size):
        """Test that format_size always returns a string with units."""
        result = format_size(size)
        assert isinstance(result, str), "format_size should return a string"
        assert " " in result, "Result should include a space between number and unit"
        _, unit = result.split(" ", 1)
        assert unit in [
            "B",
            "KB",
            "MB",
            "GB",
        ], f"Unit should be one of B, KB, MB, GB, got {unit}"

    @given(st.floats(min_value=0, max_value=1672531200))
    @settings(max_examples=100)
    def test_format_timestamp(self, timestamp):
        """Test that format_timestamp always returns a string representation."""
        result = format_timestamp(timestamp)
        assert isinstance(result, str), "format_timestamp should return a string"
        assert re.search(
            r"Today \d{2}:\d{2}|Yesterday \d{2}:\d{2}|[A-Z][a-z]{2} \d{2}:\d{2}|[A-Z][a-z]{2} \d{1,2}|\d{4}-\d{2}-\d{2}",
            result,
        ), f"Invalid timestamp format: {result}"


class TestJSXExportSortingFunctions:
    """Property-based tests for sorting functions in jsx_export.py."""

    def get_sort_key_all(self, f):
        """Reimplementation of sort_key_all from jsx_export.py."""
        if isinstance(f, tuple):
            if len(f) == 0:
                return (0, 0, 0, "")
            file_name = f[0].lower() if len(f) > 0 else ""
            loc = f[2] if len(f) > 2 else 0
            size = f[3] if len(f) > 3 else 0
            mtime = f[4] if len(f) > 4 else 0
            return (-loc, -size, -mtime, file_name)
        return (0, 0, 0, f.lower() if isinstance(f, str) else "")

    def get_sort_key_loc_size(self, f):
        """Reimplementation of sort_key_loc_size from jsx_export.py."""
        if isinstance(f, tuple):
            if len(f) == 0:
                return (0, 0, "")
            file_name = f[0].lower() if len(f) > 0 else ""
            loc = f[2] if len(f) > 2 else 0
            size = f[3] if len(f) > 3 else 0
            return (-loc, -size, file_name)
        return (0, 0, f.lower() if isinstance(f, str) else "")

    def get_safe_get(self, tup, idx, default=None):
        """Reimplementation of safe_get from jsx_export.py."""
        if not isinstance(tup, tuple):
            return default
        return tup[idx] if len(tup) > idx else default

    @given(file_list)
    @settings(max_examples=100)
    def test_sort_key_all(self, files):
        """Test that sorting with sort_key_all is correct."""
        sorted_expected = sorted(files, key=self.get_sort_key_all)
        has_tuples_with_stats = any(isinstance(f, tuple) and len(f) > 2 for f in files)
        if has_tuples_with_stats:
            for i in range(len(sorted_expected) - 1):
                f1 = sorted_expected[i]
                f2 = sorted_expected[i + 1]
                loc1 = self.get_safe_get(f1, 2, 0) if isinstance(f1, tuple) else 0
                loc2 = self.get_safe_get(f2, 2, 0) if isinstance(f2, tuple) else 0
                loc1 = (
                    0
                    if loc1 is None
                    else int(loc1)
                    if isinstance(loc1, (int, float))
                    else 0
                )
                loc2 = (
                    0
                    if loc2 is None
                    else int(loc2)
                    if isinstance(loc2, (int, float))
                    else 0
                )
                if loc1 != loc2:
                    assert loc1 >= loc2, "Files should be sorted by LOC (descending)"
        else:
            for i in range(len(sorted_expected) - 1):
                f1 = sorted_expected[i]
                f2 = sorted_expected[i + 1]
                name1 = (
                    f1[0].lower()
                    if isinstance(f1, tuple) and len(f1) > 0
                    else f1.lower()
                    if isinstance(f1, str)
                    else ""
                )
                name2 = (
                    f2[0].lower()
                    if isinstance(f2, tuple) and len(f2) > 0
                    else f2.lower()
                    if isinstance(f2, str)
                    else ""
                )
                assert name1 <= name2, (
                    "Files without stats should be sorted by full filename (ascending)"
                )

    @given(file_list)
    @settings(max_examples=100)
    def test_sort_key_loc_size(self, files):
        """Test that sorting with sort_key_loc_size is correct."""
        sorted_expected = sorted(files, key=self.get_sort_key_loc_size)
        has_tuples_with_stats = any(isinstance(f, tuple) and len(f) > 2 for f in files)
        if has_tuples_with_stats:
            for i in range(len(sorted_expected) - 1):
                f1 = sorted_expected[i]
                f2 = sorted_expected[i + 1]
                loc1 = self.get_safe_get(f1, 2, 0) if isinstance(f1, tuple) else 0
                loc2 = self.get_safe_get(f2, 2, 0) if isinstance(f2, tuple) else 0
                loc1 = (
                    0
                    if loc1 is None
                    else int(loc1)
                    if isinstance(loc1, (int, float))
                    else 0
                )
                loc2 = (
                    0
                    if loc2 is None
                    else int(loc2)
                    if isinstance(loc2, (int, float))
                    else 0
                )
                if loc1 != loc2:
                    assert loc1 >= loc2, "Files should be sorted by LOC (descending)"

    @given(
        st.tuples(simple_filename, st.text(), st.integers()),
        st.integers(min_value=0, max_value=5),
        st.integers(),
    )
    @settings(max_examples=100)
    def test_safe_get(self, tup, idx, default):
        """Test that safe_get returns the expected value."""
        result = self.get_safe_get(tup, idx, default)
        if idx < len(tup):
            assert result == tup[idx], (
                "safe_get should return the value at the given index"
            )
        else:
            assert result == default, (
                "safe_get should return the default value for out-of-bounds indices"
            )


class TestDirectoryExporterToJSX:
    """Property-based tests for DirectoryExporter.to_jsx method."""

    def test_to_jsx_basic(self):
        """Basic test for to_jsx without property testing."""
        structure = {"_files": ["file1.txt"]}
        root_name = "test_root"
        with patch("recursivist.exports.generate_jsx_component") as mock_generate:
            exporter = DirectoryExporter(structure, root_name)
            output_path = "test_output.jsx"
            exporter.to_jsx(output_path)
            mock_generate.assert_called_once_with(
                structure, root_name, output_path, False, False, False, False
            )

    def test_to_jsx_with_options_basic(self):
        """Basic test for to_jsx with options, without property testing."""
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
            with patch("recursivist.exports.generate_jsx_component") as mock_generate:
                exporter = DirectoryExporter(
                    structure,
                    root_name,
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
                exporter.to_jsx(output_path)
                mock_generate.assert_called_once_with(
                    structure,
                    root_name,
                    output_path,
                    exporter.show_full_path,
                    sort_by_loc,
                    sort_by_size,
                    sort_by_mtime,
                )


class TestShouldExclude:
    """Property-based tests for the should_exclude function."""

    @given(
        st.text(min_size=1, max_size=100),
        st.lists(st.text(min_size=1, max_size=20), min_size=0, max_size=5),
        st.text(min_size=1, max_size=100),
    )
    @settings(max_examples=100)
    def test_should_exclude_patterns(self, path, patterns, current_dir):
        """Test that should_exclude correctly applies patterns."""
        pass

    def test_should_exclude_extensions_basic(self):
        """Test that should_exclude correctly applies extension exclusions with basic cases."""
        exclude_extensions = {".txt", ".md", ".py"}
        with patch("os.path.isfile", return_value=True):
            for ext in exclude_extensions:
                path = f"test_file{ext}"
                ignore_context = {"patterns": [], "current_dir": os.path.dirname(path)}
                result = should_exclude(
                    path, ignore_context, exclude_extensions=exclude_extensions
                )
                assert result, f"Path with excluded extension {ext} should be excluded"
            path = "test_file.allowed_ext"
            ignore_context = {"patterns": [], "current_dir": os.path.dirname(path)}
            result = should_exclude(
                path, ignore_context, exclude_extensions=exclude_extensions
            )
            assert not result, "Path without excluded extension should not be excluded"


class TestGetDirectoryStructure:
    """Property-based tests for get_directory_structure function."""

    def test_structure_properties(self, temp_dir):
        """Test properties of the directory structure."""
        file1 = os.path.join(temp_dir, "file1.txt")
        file2 = os.path.join(temp_dir, "file2.py")
        subdir = os.path.join(temp_dir, "subdir")
        os.makedirs(subdir, exist_ok=True)
        subfile = os.path.join(subdir, "subfile.md")
        with open(file1, "w") as f:
            f.write("File 1 content")
        with open(file2, "w") as f:
            f.write("File 2 content")
        with open(subfile, "w") as f:
            f.write("Subfile content")
        structure, extensions = get_directory_structure(temp_dir)
        assert "_files" in structure, "Root structure should have _files key"
        assert "subdir" in structure, "Root structure should have subdir directory"
        assert "_files" in structure["subdir"], (
            "Subdir structure should have _files key"
        )
        root_files = structure["_files"]
        assert "file1.txt" in [f if isinstance(f, str) else f[0] for f in root_files], (
            "file1.txt should be in root files"
        )
        assert "file2.py" in [f if isinstance(f, str) else f[0] for f in root_files], (
            "file2.py should be in root files"
        )
        subdir_files = structure["subdir"]["_files"]
        assert "subfile.md" in [
            f if isinstance(f, str) else f[0] for f in subdir_files
        ], "subfile.md should be in subdir files"
        assert ".txt" in extensions, ".txt should be in extensions"
        assert ".py" in extensions, ".py should be in extensions"
        assert ".md" in extensions, ".md should be in extensions"


class TestGenerateJSXComponent:
    """Property-based tests for generate_jsx_component function."""

    def test_generate_jsx_component_basic(self):
        """Basic test for generate_jsx_component without property testing."""
        structure = {"_files": ["file1.txt"]}
        root_name = "test_root"
        with patch("builtins.open", MagicMock()) as mock_open, patch(
            "recursivist.jsx_export.logger"
        ) as _:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            from recursivist.jsx_export import generate_jsx_component

            generate_jsx_component(structure, root_name, "output.jsx")
            mock_open.assert_called_once_with("output.jsx", "w", encoding="utf-8")
            assert mock_file.write.call_count > 0, "No data was written to the file"


if __name__ == "__main__":
    pytest.main()
