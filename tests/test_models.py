"""Tests for recursivist._models.FileEntry.

Covers the shared file-entry model and :meth:`FileEntry.coerce`, the single
normalization helper, which reads the canonical positional slots.
"""

from typing import Any

import pytest

from recursivist._models import FileEntry


class TestFileEntryBasics:
    def test_is_a_tuple(self) -> None:
        entry = FileEntry(name="main.py", path="/p/main.py")
        assert isinstance(entry, tuple)
        assert entry[0] == "main.py"
        assert entry[1] == "/p/main.py"

    def test_attribute_access(self) -> None:
        entry = FileEntry("main.py", "/p/main.py", 5, 512, 1.5)
        assert entry.name == "main.py"
        assert entry.path == "/p/main.py"
        assert entry.loc == 5
        assert entry.size == 512
        assert entry.mtime == 1.5

    def test_metric_defaults(self) -> None:
        entry = FileEntry(name="main.py", path="main.py")
        assert entry.loc == 0
        assert entry.size == 0
        assert entry.mtime == 0.0

    def test_tuple_equality(self) -> None:
        assert FileEntry("a.py", "a.py") == ("a.py", "a.py", 0, 0, 0.0)


class TestCoerce:
    def test_fileentry_passthrough_is_identity(self) -> None:
        entry = FileEntry("a.py", "/p/a.py", 5, 512, 1.5)
        assert FileEntry.coerce(entry) is entry

    def test_bare_string(self) -> None:
        entry = FileEntry.coerce("main.py")
        assert entry == FileEntry("main.py", "main.py", 0, 0, 0.0)

    def test_non_string_non_tuple_is_stringified(self) -> None:
        entry = FileEntry.coerce(123)  # type: ignore[arg-type]
        assert entry.name == "123"
        assert entry.path == "123"

    def test_empty_tuple(self) -> None:
        entry = FileEntry.coerce(())
        assert entry == FileEntry("unknown", "unknown", 0, 0, 0.0)

    @pytest.mark.parametrize(
        "raw,expected",
        [
            (("a.py",), FileEntry("a.py", "a.py", 0, 0, 0.0)),
            (("a.py", "/p/a.py"), FileEntry("a.py", "/p/a.py", 0, 0, 0.0)),
            (("a.py", "/p/a.py", 5), FileEntry("a.py", "/p/a.py", 5, 0, 0.0)),
            (
                ("a.py", "/p/a.py", 5, 512),
                FileEntry("a.py", "/p/a.py", 5, 512, 0.0),
            ),
            (
                ("a.py", "/p/a.py", 5, 512, 1699999999),
                FileEntry("a.py", "/p/a.py", 5, 512, 1699999999.0),
            ),
        ],
    )
    def test_positional_slots(self, raw: tuple[Any, ...], expected: FileEntry) -> None:
        """coerce reads name/path/loc/size/mtime by index, unconditionally."""
        assert FileEntry.coerce(raw) == expected

    def test_extra_trailing_fields_are_ignored(self) -> None:
        entry = FileEntry.coerce(("a.py", "/p/a.py", 5, 512, 1.5, "x", "y"))
        assert entry == FileEntry("a.py", "/p/a.py", 5, 512, 1.5)

    def test_mtime_is_coerced_to_float(self) -> None:
        entry = FileEntry.coerce(("a.py", "/p/a.py", 5, 512, 7))
        assert isinstance(entry.mtime, float)
        assert entry.mtime == 7.0

    def test_coerce_reads_every_present_slot(self) -> None:
        """coerce always reads every present positional slot."""
        raw = ("a.py", "/p/a.py", 5, 512, 7.0)
        assert FileEntry.coerce(raw) == FileEntry("a.py", "/p/a.py", 5, 512, 7.0)
