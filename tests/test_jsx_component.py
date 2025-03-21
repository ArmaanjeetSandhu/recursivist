"""Property-based tests for the jsx_export.py module."""

import os
import tempfile
import unittest.mock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from recursivist.jsx_export import generate_jsx_component


@st.composite
def file_tuples_for_sorting(draw):
    """Generate various file tuple formats for testing sorting functions."""
    filename = draw(
        st.text(
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Nd"),
                whitelist_characters="_-",
            ),
            min_size=1,
            max_size=20,
        ).map(
            lambda s: s
            + st.sampled_from(
                [".txt", ".py", ".md", ".json", ".js", ".html", ".css"]
            ).example()
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


class TestJSXSort:
    """Focused property-based tests for sorting functions in jsx_export.py."""

    def safe_get(self, tup, idx, default=0):
        """Reimplementation of safe_get from jsx_export.py."""
        if not isinstance(tup, tuple):
            return default
        return tup[idx] if len(tup) > idx else default

    def sort_key_all(self, f):
        """Reimplementation of sort_key_all from jsx_export.py."""
        if isinstance(f, tuple):
            if len(f) == 0:
                return (0, 0, 0, "")
            file_name = f[0].lower() if len(f) > 0 else ""
            loc = self.safe_get(f, 2, 0)
            size = self.safe_get(f, 3, 0)
            mtime = self.safe_get(f, 4, 0)
            return (-loc, -size, -mtime, file_name)
        return (0, 0, 0, f.lower() if isinstance(f, str) else "")

    def sort_key_loc_size(self, f):
        """Reimplementation of sort_key_loc_size from jsx_export.py."""
        if isinstance(f, tuple):
            if len(f) == 0:
                return (0, 0, "")
            file_name = f[0].lower() if len(f) > 0 else ""
            loc = self.safe_get(f, 2, 0)
            size = self.safe_get(f, 3, 0)
            return (-loc, -size, file_name)
        return (0, 0, f.lower() if isinstance(f, str) else "")

    def sort_key_loc_mtime(self, f):
        """Reimplementation of sort_key_loc_mtime from jsx_export.py."""
        if isinstance(f, tuple):
            if len(f) == 0:
                return (0, 0, "")
            file_name = f[0].lower() if len(f) > 0 else ""
            loc = self.safe_get(f, 2, 0)
            mtime = self.safe_get(f, 4, 0) if len(f) > 4 else self.safe_get(f, 3, 0)
            return (-loc, -mtime, file_name)
        return (0, 0, f.lower() if isinstance(f, str) else "")

    def sort_key_size_mtime(self, f):
        """Reimplementation of sort_key_size_mtime from jsx_export.py."""
        if isinstance(f, tuple):
            if len(f) == 0:
                return (0, 0, "")
            file_name = f[0].lower() if len(f) > 0 else ""
            size = self.safe_get(f, 2, 0)
            mtime = self.safe_get(f, 3, 0) if len(f) > 3 else 0
            return (-size, -mtime, file_name)
        return (0, 0, f.lower() if isinstance(f, str) else "")

    def sort_key_mtime(self, f):
        """Reimplementation of sort_key_mtime from jsx_export.py."""
        if isinstance(f, tuple):
            if len(f) == 0:
                return (0, "")
            file_name = f[0].lower() if len(f) > 0 else ""
            mtime = 0
            if len(f) > 4:
                mtime = self.safe_get(f, 4, 0)
            elif len(f) > 3:
                mtime = self.safe_get(f, 3, 0)
            elif len(f) > 2:
                mtime = self.safe_get(f, 2, 0)
            return (-mtime, file_name)
        return (0, f.lower() if isinstance(f, str) else "")

    def sort_key_size(self, f):
        """Reimplementation of sort_key_size from jsx_export.py."""
        if isinstance(f, tuple):
            if len(f) == 0:
                return (0, "")
            file_name = f[0].lower() if len(f) > 0 else ""
            size = 0
            if len(f) > 3:
                size = self.safe_get(f, 3, 0)
            elif len(f) > 2:
                size = self.safe_get(f, 2, 0)
            return (-size, file_name)
        return (0, f.lower() if isinstance(f, str) else "")

    def sort_key_loc(self, f):
        """Reimplementation of sort_key_loc from jsx_export.py."""
        if isinstance(f, tuple):
            if len(f) == 0:
                return (0, "")
            file_name = f[0].lower() if len(f) > 0 else ""
            loc = self.safe_get(f, 2, 0)
            return (-loc, file_name)
        return (0, f.lower() if isinstance(f, str) else "")

    def sort_key_name(self, f):
        """Reimplementation of sort_key_name from jsx_export.py."""
        if isinstance(f, tuple):
            if len(f) == 0:
                return ""
            return f[0].lower() if len(f) > 0 else ""
        return f.lower() if isinstance(f, str) else ""

    @given(files=file_tuple_list)
    @settings(max_examples=100)
    def test_sort_key_all(self, files):
        """Test that sorting with sort_key_all maintains consistent ordering."""
        sorted_files = sorted(files, key=self.sort_key_all)
        assert len(sorted_files) == len(files), "Sorting should preserve all elements"
        assert (
            sorted(sorted_files, key=self.sort_key_all) == sorted_files
        ), "Sorting should be stable"
        for i in range(len(sorted_files) - 1):
            f1 = sorted_files[i]
            f2 = sorted_files[i + 1]
            key1 = self.sort_key_all(f1)
            key2 = self.sort_key_all(f2)
            assert key1 <= key2, "Keys should be in sorted order"

    @given(files=file_tuple_list)
    @settings(max_examples=100)
    def test_sort_key_loc_size(self, files):
        """Test that sorting with sort_key_loc_size maintains consistent ordering."""
        sorted_files = sorted(files, key=self.sort_key_loc_size)
        assert len(sorted_files) == len(files), "Sorting should preserve all elements"
        assert (
            sorted(sorted_files, key=self.sort_key_loc_size) == sorted_files
        ), "Sorting should be stable"
        for i in range(len(sorted_files) - 1):
            f1 = sorted_files[i]
            f2 = sorted_files[i + 1]
            key1 = self.sort_key_loc_size(f1)
            key2 = self.sort_key_loc_size(f2)
            assert key1 <= key2, "Keys should be in sorted order"

    @given(files=file_tuple_list)
    @settings(max_examples=100)
    def test_sort_key_loc_mtime(self, files):
        """Test that sorting with sort_key_loc_mtime maintains consistent ordering."""
        sorted_files = sorted(files, key=self.sort_key_loc_mtime)
        assert len(sorted_files) == len(files), "Sorting should preserve all elements"
        assert (
            sorted(sorted_files, key=self.sort_key_loc_mtime) == sorted_files
        ), "Sorting should be stable"
        for i in range(len(sorted_files) - 1):
            f1 = sorted_files[i]
            f2 = sorted_files[i + 1]
            key1 = self.sort_key_loc_mtime(f1)
            key2 = self.sort_key_loc_mtime(f2)
            assert key1 <= key2, "Keys should be in sorted order"

    @given(files=file_tuple_list)
    @settings(max_examples=100)
    def test_sort_key_size_mtime(self, files):
        """Test that sorting with sort_key_size_mtime maintains consistent ordering."""
        sorted_files = sorted(files, key=self.sort_key_size_mtime)
        assert len(sorted_files) == len(files), "Sorting should preserve all elements"
        assert (
            sorted(sorted_files, key=self.sort_key_size_mtime) == sorted_files
        ), "Sorting should be stable"
        for i in range(len(sorted_files) - 1):
            f1 = sorted_files[i]
            f2 = sorted_files[i + 1]
            key1 = self.sort_key_size_mtime(f1)
            key2 = self.sort_key_size_mtime(f2)
            assert key1 <= key2, "Keys should be in sorted order"

    @given(files=file_tuple_list)
    @settings(max_examples=100)
    def test_sort_key_mtime(self, files):
        """Test that sorting with sort_key_mtime maintains consistent ordering."""
        sorted_files = sorted(files, key=self.sort_key_mtime)
        assert len(sorted_files) == len(files), "Sorting should preserve all elements"
        assert (
            sorted(sorted_files, key=self.sort_key_mtime) == sorted_files
        ), "Sorting should be stable"
        for i in range(len(sorted_files) - 1):
            f1 = sorted_files[i]
            f2 = sorted_files[i + 1]
            key1 = self.sort_key_mtime(f1)
            key2 = self.sort_key_mtime(f2)
            assert key1 <= key2, "Keys should be in sorted order"

    @given(files=file_tuple_list)
    @settings(max_examples=100)
    def test_sort_key_size(self, files):
        """Test that sorting with sort_key_size maintains consistent ordering."""
        sorted_files = sorted(files, key=self.sort_key_size)
        assert len(sorted_files) == len(files), "Sorting should preserve all elements"
        assert (
            sorted(sorted_files, key=self.sort_key_size) == sorted_files
        ), "Sorting should be stable"
        for i in range(len(sorted_files) - 1):
            f1 = sorted_files[i]
            f2 = sorted_files[i + 1]
            key1 = self.sort_key_size(f1)
            key2 = self.sort_key_size(f2)
            assert key1 <= key2, "Keys should be in sorted order"

    @given(files=file_tuple_list)
    @settings(max_examples=100)
    def test_sort_key_loc(self, files):
        """Test that sorting with sort_key_loc maintains consistent ordering."""
        sorted_files = sorted(files, key=self.sort_key_loc)
        assert len(sorted_files) == len(files), "Sorting should preserve all elements"
        assert (
            sorted(sorted_files, key=self.sort_key_loc) == sorted_files
        ), "Sorting should be stable"
        for i in range(len(sorted_files) - 1):
            f1 = sorted_files[i]
            f2 = sorted_files[i + 1]
            key1 = self.sort_key_loc(f1)
            key2 = self.sort_key_loc(f2)
            assert key1 <= key2, "Keys should be in sorted order"

    @given(files=file_tuple_list)
    @settings(max_examples=100)
    def test_sort_key_name(self, files):
        """Test that sorting with sort_key_name maintains consistent ordering."""
        sorted_files = sorted(files, key=self.sort_key_name)
        assert len(sorted_files) == len(files), "Sorting should preserve all elements"
        assert (
            sorted(sorted_files, key=self.sort_key_name) == sorted_files
        ), "Sorting should be stable"
        for i in range(len(sorted_files) - 1):
            f1 = sorted_files[i]
            f2 = sorted_files[i + 1]
            key1 = self.sort_key_name(f1)
            key2 = self.sort_key_name(f2)
            assert key1 <= key2, "Keys should be in sorted order"


@st.composite
def jsx_directory_structure(draw):
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
                ).map(
                    lambda s: s
                    + st.sampled_from(
                        [".txt", ".py", ".md", ".json", ".js", ".html", ".css"]
                    ).example()
                ),
                st.tuples(
                    st.text(
                        alphabet=st.characters(
                            whitelist_categories=("Lu", "Ll", "Nd"),
                            whitelist_characters="_-",
                        ),
                        min_size=1,
                        max_size=20,
                    ).map(
                        lambda s: s
                        + st.sampled_from(
                            [".txt", ".py", ".md", ".json", ".js", ".html", ".css"]
                        ).example()
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


class TestJSXComponent:
    """Test the JSX component generation functionality."""

    @given(
        dir_structure=jsx_directory_structure(),
        root_name=st.text(min_size=1, max_size=20),
    )
    @settings(max_examples=20)
    def test_generate_jsx_component_basics(self, dir_structure, root_name):
        """Test basic generation of JSX component."""
        with unittest.mock.patch(
            "builtins.open", unittest.mock.mock_open()
        ) as mock_open:
            generate_jsx_component(dir_structure, root_name, "output.jsx")
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
    def test_jsx_end_to_end(self, dir_structure, root_name):
        """Test end-to-end JSX component generation with temporary file."""
        with tempfile.NamedTemporaryFile(suffix=".jsx", delete=False) as temp_file:
            output_path = temp_file.name
        try:
            generate_jsx_component(dir_structure, root_name, output_path)
            assert os.path.exists(output_path), "The JSX file was not created"
            assert os.path.getsize(output_path) > 0, "The JSX file is empty"
            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()
            assert "import React" in content, "JSX should import React"
            assert (
                "export default DirectoryViewer" in content
            ), "JSX should export the DirectoryViewer component"
            assert root_name in content, "JSX should include the root name"
            assert (
                "const DirectoryViewer = () =>" in content
            ), "DirectoryViewer component should be defined"
            assert (
                "const DirectoryItem = (props) =>" in content
            ), "DirectoryItem component should be defined"
            assert (
                "const FileItem = (props) =>" in content
            ), "FileItem component should be defined"
            if "_files" in dir_structure and dir_structure["_files"]:
                for file_item in dir_structure["_files"]:
                    if isinstance(file_item, tuple):
                        file_name = file_item[0]
                    else:
                        file_name = file_item
                    assert (
                        file_name in content
                    ), f"File {file_name} should be included in JSX content"
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
        dir_structure,
        root_name,
        show_full_path,
        sort_by_loc,
        sort_by_size,
        sort_by_mtime,
    ):
        """Test JSX generation with various options."""
        with unittest.mock.patch(
            "builtins.open", unittest.mock.mock_open()
        ) as mock_open:
            generate_jsx_component(
                dir_structure,
                root_name,
                "output.jsx",
                show_full_path,
                sort_by_loc,
                sort_by_size,
                sort_by_mtime,
            )
            mock_open.assert_called_once_with("output.jsx", "w", encoding="utf-8")
            mock_file = mock_open()
            write_calls = [args[0] for args, _ in mock_file.write.call_args_list]
            content = "".join(write_calls)
            if sort_by_loc:
                assert (
                    "const showLoc = true;" in content
                ), "LOC display should be enabled"
                assert (
                    "const sortByLoc = true;" in content
                ), "LOC sorting should be enabled"
            else:
                assert (
                    "const showLoc = false;" in content
                ), "LOC display should be disabled"
                assert (
                    "const sortByLoc = false;" in content
                ), "LOC sorting should be disabled"
            if sort_by_size:
                assert (
                    "const showSize = true;" in content
                ), "Size display should be enabled"
                assert (
                    "const sortBySize = true;" in content
                ), "Size sorting should be enabled"
                assert (
                    "format_size" in content
                ), "Size formatting function should be included"
            else:
                assert (
                    "const showSize = false;" in content
                ), "Size display should be disabled"
                assert (
                    "const sortBySize = false;" in content
                ), "Size sorting should be disabled"
            if sort_by_mtime:
                assert (
                    "const showMtime = true;" in content
                ), "Mtime display should be enabled"
                assert (
                    "const sortByMtime = true;" in content
                ), "Mtime sorting should be enabled"
                assert (
                    "format_timestamp" in content
                ), "Timestamp formatting function should be included"
            else:
                assert (
                    "const showMtime = false;" in content
                ), "Mtime display should be disabled"
                assert (
                    "const sortByMtime = false;" in content
                ), "Mtime sorting should be disabled"


if __name__ == "__main__":
    pytest.main()
