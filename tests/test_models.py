"""Tests for recursivist._models.FileEntry, the shared file-entry model."""

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
