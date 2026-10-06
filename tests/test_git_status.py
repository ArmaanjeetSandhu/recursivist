"""Tests for recursivist.git_status: get_git_status.

Two complementary layers are used:

- :class:`TestGitStatusRealRepo` runs the function against real, throwaway Git
  repositories (skipped when ``git`` is unavailable). These exercise the
  realistic untracked/modified/deleted/added/renamed paths and the mapping of
  results to a location relative to the queried directory.
- :class:`TestGitStatusParsing` mocks ``subprocess.run`` to feed crafted
  ``--porcelain -z`` output, deterministically covering every parsing branch
  plus the error paths that are awkward to provoke with a real repository.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from recursivist.git_status import GitStatusError, get_git_status

git_available = shutil.which("git") is not None
requires_git = pytest.mark.skipif(not git_available, reason="git is not installed")


def _completed(
    returncode: int, stdout: bytes, stderr: bytes = b""
) -> subprocess.CompletedProcess[bytes]:
    """Build a ``CompletedProcess`` stand-in for mocking ``subprocess.run``."""
    return subprocess.CompletedProcess(
        args=[], returncode=returncode, stdout=stdout, stderr=stderr
    )


def _init_repo(path: str) -> None:
    """Initialise an isolated Git repo with a deterministic identity."""
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=path, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True)
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=path, check=True)


@requires_git
class TestGitStatusRealRepo:
    """End-to-end tests against real, throwaway Git repositories."""

    def test_untracked_modified_deleted(self, tmp_path: Path) -> None:
        """Untracked, modified and deleted files map to U / M / D."""
        repo = str(tmp_path)
        _init_repo(repo)
        for name in ("keep.txt", "remove.txt", "change.txt"):
            (tmp_path / name).write_text("initial\n")
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=repo, check=True)

        (tmp_path / "brand_new.txt").write_text("new\n")
        (tmp_path / "change.txt").write_text("initial\nmore\n")
        (tmp_path / "remove.txt").unlink()

        status = get_git_status(repo)
        assert status["brand_new.txt"] == "U"
        assert status["change.txt"] == "M"
        assert status["remove.txt"] == "D"
        assert "keep.txt" not in status

    def test_staged_added_and_renamed(self, tmp_path: Path) -> None:
        """A staged new file and a staged rename both map to A."""
        repo = str(tmp_path)
        _init_repo(repo)
        (tmp_path / "original.txt").write_text("content\n")
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=repo, check=True)

        (tmp_path / "added.txt").write_text("added\n")
        subprocess.run(["git", "add", "added.txt"], cwd=repo, check=True)
        subprocess.run(
            ["git", "mv", "original.txt", "renamed.txt"], cwd=repo, check=True
        )

        status = get_git_status(repo)
        assert status["added.txt"] == "A"
        assert status["renamed.txt"] == "A"
        assert "original.txt" not in status

    def test_files_in_subdirectory_are_relative(self, tmp_path: Path) -> None:
        """Querying a subdirectory returns paths relative to it and excludes
        files that live outside it."""
        repo = str(tmp_path)
        _init_repo(repo)
        sub = tmp_path / "pkg"
        sub.mkdir()
        (sub / "module.py").write_text("x = 1\n")
        (tmp_path / "top.txt").write_text("top\n")
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=repo, check=True)

        (sub / "module.py").write_text("x = 2\n")
        (tmp_path / "top.txt").write_text("changed\n")

        status = get_git_status(str(sub))
        assert status == {"module.py": "M"}

    def test_clean_repository_returns_empty(self, tmp_path: Path) -> None:
        """A repository with no changes yields an empty mapping."""
        repo = str(tmp_path)
        _init_repo(repo)
        (tmp_path / "keep.txt").write_text("initial\n")
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=repo, check=True)

        assert get_git_status(repo) == {}


class TestGitStatusParsing:
    """Branch coverage of the porcelain parser via mocked ``subprocess.run``."""

    def test_all_status_codes(self) -> None:
        """Every recognised porcelain code maps to the expected character, and
        rename/copy second records plus too-short records are skipped."""
        root = _completed(0, b"/repo\n")
        porcelain = (
            b"A  added.txt\0"
            b"M  staged_mod.txt\0"
            b" M worktree_mod.txt\0"
            b"D  staged_del.txt\0"
            b" D worktree_del.txt\0"
            b"?? untracked.txt\0"
            b"R  new_name.txt\0old_name.txt\0"
            b"C  copy.txt\0source.txt\0"
            b"XY\0"
        )
        status = _completed(0, porcelain)
        with patch("subprocess.run", side_effect=[root, status]):
            result = get_git_status("/repo")
        assert result == {
            "added.txt": "A",
            "staged_mod.txt": "M",
            "worktree_mod.txt": "M",
            "staged_del.txt": "D",
            "worktree_del.txt": "D",
            "untracked.txt": "U",
            "new_name.txt": "A",
            "copy.txt": "M",
        }
        assert "old_name.txt" not in result
        assert "source.txt" not in result

    def test_files_outside_directory_are_filtered(self) -> None:
        """A changed file above the queried directory is excluded."""
        root = _completed(0, b"/repo\n")
        porcelain = b" M pkg/inside.txt\0 M outside.txt\0"
        status = _completed(0, porcelain)
        with patch("subprocess.run", side_effect=[root, status]):
            result = get_git_status(os.path.join("/repo", "pkg"))
        assert result == {"inside.txt": "M"}

    def test_non_utf8_path_is_kept(self) -> None:
        """A path that is not valid UTF-8 decodes losslessly and leaves the other
        entries intact."""
        raw = b"caf\xe9.txt"
        root = _completed(0, b"/repo\n")
        status = _completed(0, b"?? " + raw + b"\0 M plain.txt\0")
        with patch("subprocess.run", side_effect=[root, status]):
            result = get_git_status("/repo")
        assert result.pop("plain.txt") == "M"
        ((name, marker),) = result.items()
        assert marker == "U"
        assert name.encode(sys.getfilesystemencoding(), "surrogateescape") == raw

    def test_rev_parse_failure_raises_with_git_message(self) -> None:
        """A non-zero ``rev-parse`` exit raises, carrying Git's error output."""
        root = _completed(128, b"", b"fatal: not a git repository\n")
        with patch("subprocess.run", side_effect=[root]):
            with pytest.raises(GitStatusError, match="^fatal: not a git repository$"):
                get_git_status("/repo")

    def test_status_failure_raises(self) -> None:
        """A non-zero ``git status`` exit raises, naming the command and exit status
        when Git printed nothing."""
        root = _completed(0, b"/repo\n")
        status = _completed(1, b"")
        with patch("subprocess.run", side_effect=[root, status]):
            with pytest.raises(GitStatusError, match="git status exited with status 1"):
                get_git_status("/repo")

    def test_git_not_runnable_raises(self) -> None:
        """An ``OSError`` from launching Git (e.g. ``git`` missing) is raised as a
        ``GitStatusError`` chained to the original error."""
        error = FileNotFoundError("git missing")
        with patch("subprocess.run", side_effect=error):
            with pytest.raises(GitStatusError, match="git missing") as excinfo:
                get_git_status("/repo")
        assert excinfo.value.__cause__ is error

    def test_relpath_value_error_is_ignored(self) -> None:
        """A ``ValueError`` from ``relpath`` (e.g. cross-drive) skips the entry."""
        root = _completed(0, b"/repo\n")
        status = _completed(0, b" M somefile.txt\0")
        with patch("subprocess.run", side_effect=[root, status]):
            with patch("os.path.relpath", side_effect=ValueError("different drive")):
                assert get_git_status("/repo") == {}
