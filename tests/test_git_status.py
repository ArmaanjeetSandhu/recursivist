"""Tests for recursivist.git_status: get_git_status.

Two complementary layers are used:

- :class:`TestGitStatusRealRepo` runs the function against real, throwaway Git
  repositories (skipped when ``git`` is unavailable). These exercise the
  realistic untracked/modified/deleted/added/renamed paths and the mapping of
  results to a location relative to the queried directory.
- :class:`TestGitStatusParsing` mocks ``subprocess.run`` to feed crafted
  ``--porcelain -z`` output, deterministically covering every parsing branch
  plus the early-return and error paths that are awkward to provoke with a real
  repository.
"""

import os
import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from recursivist.git_status import get_git_status

git_available = shutil.which("git") is not None
requires_git = pytest.mark.skipif(not git_available, reason="git is not installed")


def _completed(returncode: int, stdout: str) -> subprocess.CompletedProcess[str]:
    """Build a ``CompletedProcess`` stand-in for mocking ``subprocess.run``."""
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout)


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

    def test_non_git_directory_returns_empty(self, tmp_path: Path) -> None:
        """Outside a repository ``git rev-parse`` fails and the result is {}."""
        assert get_git_status(str(tmp_path)) == {}


class TestGitStatusParsing:
    """Branch coverage of the porcelain parser via mocked ``subprocess.run``."""

    def test_all_status_codes(self) -> None:
        """Every recognised porcelain code maps to the expected character, and
        rename/copy second records plus too-short records are skipped."""
        root = _completed(0, "/repo\n")
        porcelain = (
            "A  added.txt\0"
            "M  staged_mod.txt\0"
            " M worktree_mod.txt\0"
            "D  staged_del.txt\0"
            " D worktree_del.txt\0"
            "?? untracked.txt\0"
            "R  new_name.txt\0old_name.txt\0"
            "C  copy.txt\0source.txt\0"
            "XY\0"
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
        root = _completed(0, "/repo\n")
        porcelain = " M pkg/inside.txt\0 M outside.txt\0"
        status = _completed(0, porcelain)
        with patch("subprocess.run", side_effect=[root, status]):
            result = get_git_status(os.path.join("/repo", "pkg"))
        assert result == {"inside.txt": "M"}

    def test_rev_parse_failure_returns_empty(self) -> None:
        """A non-zero ``rev-parse`` exit short-circuits to {}."""
        root = _completed(128, "")
        with patch("subprocess.run", side_effect=[root]):
            assert get_git_status("/repo") == {}

    def test_status_failure_returns_empty(self) -> None:
        """A non-zero ``git status`` exit short-circuits to {}."""
        root = _completed(0, "/repo\n")
        status = _completed(1, "")
        with patch("subprocess.run", side_effect=[root, status]):
            assert get_git_status("/repo") == {}

    def test_subprocess_exception_returns_empty(self) -> None:
        """Any exception (e.g. ``git`` missing) is swallowed, returning {}."""
        with patch("subprocess.run", side_effect=FileNotFoundError("git missing")):
            assert get_git_status("/repo") == {}

    def test_relpath_value_error_is_ignored(self) -> None:
        """A ``ValueError`` from ``relpath`` (e.g. cross-drive) skips the entry."""
        root = _completed(0, "/repo\n")
        status = _completed(0, " M somefile.txt\0")
        with patch("subprocess.run", side_effect=[root, status]):
            with patch("os.path.relpath", side_effect=ValueError("different drive")):
                assert get_git_status("/repo") == {}
