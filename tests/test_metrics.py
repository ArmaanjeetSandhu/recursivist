"""Tests for recursivist.metrics: file size/mtime, count_lines_of_code, format_size, format_timestamp."""

import os
import random
import re
import tempfile
import time
from unittest.mock import mock_open, patch

import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st
from hypothesis.strategies import DrawFn
from pytest_mock import MockerFixture

from recursivist.metrics import (
    count_lines_of_code,
    format_size,
    format_timestamp,
    get_file_mtime,
    get_file_size,
)

text_content = st.text(
    alphabet=st.characters(blacklist_categories=["Cs"], max_codepoint=127),
    min_size=0,
    max_size=10000,
)


@st.composite
def file_with_n_lines(draw: DrawFn, min_lines: int = 0, max_lines: int = 1000) -> str:
    """Generate file content with a specific number of lines."""
    n_lines: int = draw(st.integers(min_value=min_lines, max_value=max_lines))
    if n_lines == 0:
        return ""
    lines: list[str] = []
    for _ in range(n_lines - 1):
        line_content: str = draw(
            st.text(
                alphabet=st.characters(blacklist_categories=["Cs"], max_codepoint=127),
                min_size=0,
                max_size=100,
            )
        )
        lines.append(line_content)
    last_line: str = draw(
        st.text(
            alphabet=st.characters(blacklist_categories=["Cs"], max_codepoint=127),
            min_size=0,
            max_size=100,
        )
    )
    lines.append(last_line)
    with_final_newline: bool = draw(st.booleans())
    content: str = "\n".join(lines)
    if with_final_newline:
        content += "\n"
    return content


binary_content = st.binary(min_size=0, max_size=1000)


@st.composite
def content_with_encoding(draw: DrawFn) -> tuple[str, str]:
    """Generate text content with a specific encoding."""
    encoding: str = draw(
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
    content: str = draw(
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
    def test_always_nonnegative(self, content: str) -> None:
        """Test that count_lines_of_code always returns a non-negative value."""
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as f:
            try:
                f.write(content)
                file_path: str = f.name
            except UnicodeEncodeError:
                pytest.skip("Content contains characters that can't be encoded")
        try:
            line_count: int = count_lines_of_code(file_path)
            assert line_count >= 0, "Line count should never be negative"
        finally:
            os.unlink(file_path)

    @given(file_with_n_lines(min_lines=0, max_lines=100))
    @settings(max_examples=100)
    def test_exact_line_count(self, content: str) -> None:
        """Test that count_lines_of_code returns the exact number of lines."""
        if "\x00" in content:
            return
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as f:
            try:
                f.write(content)
                file_path: str = f.name
            except UnicodeEncodeError:
                pytest.skip("Content contains characters that can't be encoded")
        try:
            with open(file_path, encoding="utf-8") as f:
                expected_lines: int = sum(1 for _ in f)
            line_count: int = count_lines_of_code(file_path)
            assert line_count == expected_lines, (
                f"Expected {expected_lines} lines, got {line_count} for content: {repr(content)}"
            )
        finally:
            os.unlink(file_path)

    @given(binary_content)
    @settings(max_examples=50)
    def test_binary_files(self, content: bytes) -> None:
        """Test that binary files are handled properly."""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            f.write(content)
            file_path: str = f.name
        try:
            line_count: int = count_lines_of_code(file_path)
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
    def test_different_encodings(self, content_info: tuple[str, str]) -> None:
        """Test that files with different encodings are handled correctly."""
        content: str
        encoding: str
        content, encoding = content_info
        if "\x00" in content:
            return
        try:
            encoded_content: bytes = content.encode(encoding)
        except UnicodeEncodeError:
            pytest.skip(f"Content can't be encoded with {encoding}")
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            f.write(encoded_content)
            file_path: str = f.name
        try:
            line_count: int = count_lines_of_code(file_path)
            assert line_count >= 0, "Line count should never be negative"
            if encoding == "utf-8" or encoding == "ascii":
                try:
                    with open(file_path, encoding=encoding) as f:
                        expected_lines: int = sum(1 for _ in f)
                    assert line_count == expected_lines, (
                        f"Line count mismatch for {encoding} content"
                    )
                except Exception:
                    pass
        finally:
            os.unlink(file_path)

    @given(st.integers(min_value=1, max_value=1000))
    @settings(max_examples=10)
    def test_large_files(self, num_lines: int) -> None:
        """Test that large files are handled correctly."""
        content: str = "\n".join(["Line " + str(i) for i in range(num_lines)])
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            file_path: str = f.name
        try:
            line_count: int = count_lines_of_code(file_path)
            assert line_count == num_lines, (
                f"Expected {num_lines} lines, got {line_count}"
            )
        finally:
            os.unlink(file_path)

    def test_nonexistent_file(self) -> None:
        """Test that count_lines_of_code handles nonexistent files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path: str = os.path.join(temp_dir, "nonexistent.txt")
            assert count_lines_of_code(file_path) == 0, (
                "Nonexistent files should return 0 lines"
            )

    def test_permission_denied(self, mocker: MockerFixture) -> None:
        """Test that count_lines_of_code handles permission denied errors."""
        mocker.patch("builtins.open", side_effect=PermissionError("Permission denied"))
        assert count_lines_of_code("some/path.txt") == 0, (
            "Permission denied should return 0 lines"
        )

    def test_binary_file_detection(self) -> None:
        """Test that files are properly identified as binary."""
        binary_data: bytes = bytes([random.randint(0, 255) for _ in range(100)])
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            f.write(binary_data)
            file_path: str = f.name
        try:
            line_count: int = count_lines_of_code(file_path)
            assert line_count >= 0, "Line count should never be negative"
        finally:
            os.unlink(file_path)

    def test_unicode_decode_error(self, mocker: MockerFixture) -> None:
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
        error_type: type[Exception] | None,
        error_msg: str | None,
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


class TestCountLinesOfCodeProperties:
    """Property-based tests for count_lines_of_code function."""

    @given(st.text(alphabet=st.characters(max_codepoint=127)))
    @settings(max_examples=100)
    def test_always_nonnegative(self, content: str) -> None:
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
    def test_matches_line_count(self, lines: list[str]) -> None:
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
                    max_lines = content.count("\n") + content.count("\r") + 1
                    assert 0 <= line_count <= max_lines, (
                        f"Line count {line_count} outside expected range [0, {max_lines}]"
                    )
                else:
                    assert abs(line_count - expected_lines) <= 1, (
                        f"Expected {expected_lines} lines, got {line_count}"
                    )
        finally:
            os.unlink(file_path)

    @given(st.binary(min_size=0, max_size=1000))
    @settings(max_examples=50)
    def test_binary_files_handled(self, content: bytes) -> None:
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
    def test_nonexistent_files(self, filename: str) -> None:
        """Test that nonexistent files return 0 lines."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, filename)
            assert count_lines_of_code(file_path) == 0, (
                "Nonexistent files should return 0 lines"
            )

    def test_permission_denied(self) -> None:
        """Test that permission denied errors are handled gracefully."""
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            assert count_lines_of_code("some/path.txt") == 0, (
                "Permission denied should return 0 lines"
            )


class TestFormatFunctions:
    """Property-based tests for formatting functions."""

    @given(st.integers(min_value=0, max_value=10**12))
    @settings(max_examples=100)
    def test_format_size(self, size: int) -> None:
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

    @given(st.floats(min_value=1, max_value=1672531200))
    @settings(max_examples=100)
    def test_format_timestamp(self, timestamp: float) -> None:
        """Real (non-sentinel) timestamps always yield a recognizable string."""
        result = format_timestamp(timestamp)
        assert isinstance(result, str)
        assert re.search(
            r"Today \d{2}:\d{2}|Yesterday \d{2}:\d{2}|[A-Z][a-z]{2} \d{2}:\d{2}|[A-Z][a-z]{2} \d{1,2}|\d{4}-\d{2}-\d{2}|^-$",
            result,
        ), f"Invalid timestamp format: {result}"
