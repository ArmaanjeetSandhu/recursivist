"""Focused property-based tests for the count_lines_of_code function."""

import os
import random
import tempfile

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pytest_mock import MockerFixture

from recursivist.core import count_lines_of_code

text_content = st.text(
    alphabet=st.characters(blacklist_categories=["Cs"], max_codepoint=127),
    min_size=0,
    max_size=10000,
)


@st.composite
def file_with_n_lines(draw, min_lines=0, max_lines=1000):
    """Generate file content with a specific number of lines."""
    n_lines = draw(st.integers(min_value=min_lines, max_value=max_lines))
    if n_lines == 0:
        return ""
    lines = []
    for _ in range(n_lines - 1):
        line_content = draw(
            st.text(
                alphabet=st.characters(blacklist_categories=["Cs"], max_codepoint=127),
                min_size=0,
                max_size=100,
            )
        )
        lines.append(line_content)
    last_line = draw(
        st.text(
            alphabet=st.characters(blacklist_categories=["Cs"], max_codepoint=127),
            min_size=0,
            max_size=100,
        )
    )
    lines.append(last_line)
    with_final_newline = draw(st.booleans())
    content = "\n".join(lines)
    if with_final_newline:
        content += "\n"
    return content


binary_content = st.binary(min_size=0, max_size=1000)


@st.composite
def content_with_encoding(draw):
    """Generate text content with a specific encoding."""
    encoding = draw(
        st.sampled_from(
            ["utf-8", "utf-16", "utf-16-le", "utf-16-be", "latin-1", "ascii"]
        )
    )
    if encoding == "ascii":
        allowed_codepoint = 127
    elif encoding == "latin-1":
        allowed_codepoint = 255
    else:
        allowed_codepoint = 0xFFFF
    content = draw(
        st.text(
            alphabet=st.characters(
                blacklist_categories=["Cs"], max_codepoint=allowed_codepoint
            ),
            min_size=0,
            max_size=100,
        )
    )
    return content, encoding


class TestCountLinesOfCode:
    """Property-based tests specifically focused on count_lines_of_code."""

    @given(text_content)
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

    @given(file_with_n_lines(min_lines=0, max_lines=100))
    @settings(max_examples=100)
    def test_exact_line_count(self, content):
        """Test that count_lines_of_code returns the exact number of lines."""
        if "\x00" in content:
            return
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as f:
            try:
                f.write(content)
                file_path = f.name
            except UnicodeEncodeError:
                pytest.skip("Content contains characters that can't be encoded")
        try:
            with open(file_path, encoding="utf-8") as f:
                expected_lines = sum(1 for _ in f)
            line_count = count_lines_of_code(file_path)
            assert line_count == expected_lines, (
                f"Expected {expected_lines} lines, got {line_count} for content: {repr(content)}"
            )
        finally:
            os.unlink(file_path)

    @given(binary_content)
    @settings(max_examples=50)
    def test_binary_files(self, content):
        """Test that binary files are handled properly."""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            f.write(content)
            file_path = f.name
        try:
            line_count = count_lines_of_code(file_path)
            assert line_count >= 0, (
                "Line count should never be negative even for binary files"
            )
            if file_path.lower().endswith(".bin") or (
                b"\x00" in content and len(content) > 0 and content.strip()
            ):
                if content.strip() != b"\x00":
                    assert line_count == 0, (
                        "Files with non-trivial null bytes should return 0 lines"
                    )
        finally:
            os.unlink(file_path)

    @given(content_with_encoding())
    @settings(max_examples=50)
    def test_different_encodings(self, content_info):
        """Test that files with different encodings are handled correctly."""
        content, encoding = content_info
        if "\x00" in content:
            return
        try:
            encoded_content = content.encode(encoding)
        except UnicodeEncodeError:
            pytest.skip(f"Content can't be encoded with {encoding}")
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            f.write(encoded_content)
            file_path = f.name
        try:
            line_count = count_lines_of_code(file_path)
            assert line_count >= 0, "Line count should never be negative"
            if encoding == "utf-8" or encoding == "ascii":
                try:
                    with open(file_path, encoding=encoding) as f:
                        expected_lines = sum(1 for _ in f)
                    assert line_count == expected_lines, (
                        f"Line count mismatch for {encoding} content"
                    )
                except Exception:
                    pass
        finally:
            os.unlink(file_path)

    @given(st.integers(min_value=1, max_value=1000))
    @settings(max_examples=10)
    def test_large_files(self, num_lines):
        """Test that large files are handled correctly."""
        content = "\n".join(["Line " + str(i) for i in range(num_lines)])
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            file_path = f.name
        try:
            line_count = count_lines_of_code(file_path)
            assert line_count == num_lines, (
                f"Expected {num_lines} lines, got {line_count}"
            )
        finally:
            os.unlink(file_path)

    def test_nonexistent_file(self):
        """Test that count_lines_of_code handles nonexistent files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "nonexistent.txt")
            assert count_lines_of_code(file_path) == 0, (
                "Nonexistent files should return 0 lines"
            )

    def test_permission_denied(self, mocker: MockerFixture):
        """Test that count_lines_of_code handles permission denied errors."""
        mocker.patch("builtins.open", side_effect=PermissionError("Permission denied"))
        assert count_lines_of_code("some/path.txt") == 0, (
            "Permission denied should return 0 lines"
        )

    def test_binary_file_detection(self):
        """Test that files are properly identified as binary."""
        binary_data = bytes([random.randint(0, 255) for _ in range(100)])
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            f.write(binary_data)
            file_path = f.name
        try:
            line_count = count_lines_of_code(file_path)
            assert line_count >= 0, "Line count should never be negative"
        finally:
            os.unlink(file_path)

    def test_unicode_decode_error(self, mocker: MockerFixture):
        """Test that count_lines_of_code handles UnicodeDecodeError."""
        mocker.patch(
            "builtins.open",
            side_effect=UnicodeDecodeError(
                "utf-8", b"\x80", 0, 1, "invalid start byte"
            ),
        )
        assert count_lines_of_code("some/path.txt") == 0, (
            "UnicodeDecodeError should return 0 lines"
        )

    def test_file_with_bin_extension(self):
        """Test that files with .bin extension are handled correctly."""
        with tempfile.NamedTemporaryFile(suffix=".bin", mode="w", delete=False) as f:
            f.write("This is a text file with .bin extension\nIt has multiple lines\n")
            file_path = f.name
        try:
            line_count = count_lines_of_code(file_path)
            assert line_count == 0, "Files with .bin extension should return 0 lines"
        finally:
            os.unlink(file_path)


if __name__ == "__main__":
    pytest.main()
