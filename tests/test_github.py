"""Tests for remote GitHub repository support.

Network access is always mocked: :func:`urllib.request.urlopen` is patched to
serve a symref advertisement (for default-branch resolution) and an in-memory
``tar.gz`` archive (for the source download), so the real download → extract →
scan → render pipeline runs end to end without touching the network.
"""

from __future__ import annotations

import io
import os
import tarfile
from collections.abc import Callable, Mapping
from email.message import Message
from typing import Any
from urllib.error import HTTPError, URLError

import pytest
from typer.testing import CliRunner

from recursivist import github
from recursivist._models import FileEntry
from recursivist.cli import app
from recursivist.github import (
    GitHubError,
    GitHubTarget,
    apply_github_urls,
    checkout_repository,
    get_github_token,
    is_github_url,
    parse_github_url,
    resolve_default_branch,
)


def _make_tarball(top: str, files: Mapping[str, str]) -> bytes:
    """Build a ``tar.gz`` mimicking a GitHub source archive layout.

    Args:
        top: The single top-level directory name (e.g. ``"repo-main"``).
        files: Mapping of repo-relative path to text content.

    Returns:
        The gzipped tar archive bytes.
    """
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        top_info = tarfile.TarInfo(top)
        top_info.type = tarfile.DIRTYPE
        top_info.mode = 0o755
        tar.addfile(top_info)
        for rel, content in files.items():
            data = content.encode("utf-8")
            info = tarfile.TarInfo(f"{top}/{rel}")
            info.size = len(data)
            info.mtime = 1700000000
            tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def _make_traversal_tarball() -> bytes:
    """Build a malicious archive whose member escapes the destination."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        data = b"pwned"
        info = tarfile.TarInfo("../escape.txt")
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def _refs_payload(branch: str) -> bytes:
    """Build a smart-HTTP advertisement carrying the default-branch symref."""
    return (
        b"001e# service=git-upload-pack\n0000"
        b"0000000000000000000000000000000000000000 HEAD\x00multi_ack "
        b"symref=HEAD:refs/heads/" + branch.encode() + b" object-format=sha1\x00"
    )


def _http_error(url: str, code: int) -> HTTPError:
    return HTTPError(url, code, "error", Message(), None)


def _fake_urlopen(
    *,
    branch: str = "main",
    tarball: bytes = b"",
    refs_fail: int | None = None,
    download_fail: int | None = None,
    refs_error: Exception | None = None,
) -> Callable[..., Any]:
    """Return a stand-in for ``urlopen`` serving refs and archive responses."""

    def fake(request: Any, timeout: Any = None) -> io.BytesIO:
        url = request.full_url
        if "info/refs" in url:
            if refs_error is not None:
                raise refs_error
            if refs_fail is not None:
                raise _http_error(url, refs_fail)
            return io.BytesIO(_refs_payload(branch))
        if "codeload" in url or url.endswith(".tar.gz") or "/tar.gz/" in url:
            if download_fail is not None:
                raise _http_error(url, download_fail)
            return io.BytesIO(tarball)
        raise AssertionError(f"unexpected URL requested: {url}")

    return fake


SAMPLE_FILES = {
    "README.md": "# sample\n",
    "pkg/__init__.py": "",
    "pkg/core.py": "x = 1\ny = 2\n",
    "pkg/util/helpers.py": "def f():\n    return 1\n",
}


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.mark.parametrize(
    ("url", "owner", "repo", "ref", "subpath"),
    [
        ("https://github.com/o/r", "o", "r", None, ""),
        ("https://github.com/o/r.git", "o", "r", None, ""),
        ("http://github.com/o/r/", "o", "r", None, ""),
        ("github.com/o/r", "o", "r", None, ""),
        ("www.github.com/o/r", "o", "r", None, ""),
        ("https://www.github.com/o/r", "o", "r", None, ""),
        ("https://github.com/o/r/tree/dev", "o", "r", "dev", ""),
        ("https://github.com/o/r/tree/dev/src/pkg", "o", "r", "dev", "src/pkg"),
        ("https://github.com/o/r/blob/main/a/b.py", "o", "r", "main", "a/b.py"),
        ("git@github.com:o/r.git", "o", "r", None, ""),
        ("https://github.com/o/r?tab=readme", "o", "r", None, ""),
    ],
)
def test_parse_github_url_valid(
    url: str, owner: str, repo: str, ref: str | None, subpath: str
) -> None:
    target = parse_github_url(url)
    assert target is not None
    assert target.owner == owner
    assert target.repo == repo
    assert target.ref == ref
    assert target.subpath == subpath


@pytest.mark.parametrize(
    "text",
    [
        "",
        "/home/user/project",
        "./relative/dir",
        "https://example.com/o/r",
        "https://gitlab.com/o/r",
        "not a url at all",
        "github.com",
        "https://github.com/only-owner",
    ],
)
def test_parse_github_url_invalid(text: str) -> None:
    assert parse_github_url(text) is None
    assert is_github_url(text) is False


def test_is_github_url_true() -> None:
    assert is_github_url("https://github.com/o/r") is True


def test_target_slug_and_display_name() -> None:
    assert GitHubTarget("o", "r").slug == "o/r"
    assert GitHubTarget("o", "r").display_name == "r"
    assert GitHubTarget("o", "r", subpath="a/b/c").display_name == "c"


def test_target_blob_url() -> None:
    target = GitHubTarget("ArmaanjeetSandhu", "recursivist")
    url = target.blob_url("main", "recursivist/exporters/base.py")
    assert url == (
        "https://github.com/ArmaanjeetSandhu/recursivist/"
        "blob/main/recursivist/exporters/base.py"
    )


def test_target_blob_url_normalizes_leading_slash() -> None:
    assert (
        GitHubTarget("o", "r").blob_url("main", "/a/b.py").endswith("/blob/main/a/b.py")
    )


def test_get_github_token_prefers_github_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "  abc  ")
    monkeypatch.setenv("GH_TOKEN", "xyz")
    assert get_github_token() == "abc"


def test_get_github_token_falls_back_to_gh_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setenv("GH_TOKEN", "xyz")
    assert get_github_token() == "xyz"


def test_get_github_token_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    assert get_github_token() is None


def test_token_sent_as_bearer(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake(request: Any, timeout: Any = None) -> io.BytesIO:
        captured["auth"] = request.get_header("Authorization")
        return io.BytesIO(_refs_payload("main"))

    monkeypatch.setattr("recursivist.github.urllib.request.urlopen", fake)
    resolve_default_branch(GitHubTarget("o", "r"), token="secret")
    assert captured["auth"] == "Bearer secret"


def test_resolve_default_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "recursivist.github.urllib.request.urlopen", _fake_urlopen(branch="develop")
    )
    assert resolve_default_branch(GitHubTarget("o", "r")) == "develop"


def test_resolve_default_branch_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "recursivist.github.urllib.request.urlopen", _fake_urlopen(refs_fail=404)
    )
    with pytest.raises(GitHubError, match="was not found"):
        resolve_default_branch(GitHubTarget("o", "missing"))


def test_resolve_default_branch_network_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "recursivist.github.urllib.request.urlopen",
        _fake_urlopen(refs_error=URLError("boom")),
    )
    with pytest.raises(GitHubError, match="Could not reach GitHub"):
        resolve_default_branch(GitHubTarget("o", "r"))


def test_resolve_default_branch_missing_symref(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake(request: Any, timeout: Any = None) -> io.BytesIO:
        return io.BytesIO(b"no symref here")

    monkeypatch.setattr("recursivist.github.urllib.request.urlopen", fake)
    with pytest.raises(GitHubError, match="default branch"):
        resolve_default_branch(GitHubTarget("o", "r"))


def test_checkout_repository_default_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    tarball = _make_tarball("r-main", SAMPLE_FILES)
    monkeypatch.setattr(
        "recursivist.github.urllib.request.urlopen",
        _fake_urlopen(branch="main", tarball=tarball),
    )
    target = parse_github_url("https://github.com/o/r")
    assert target is not None
    with checkout_repository(target) as checkout:
        assert checkout.ref == "main"
        assert checkout.root_name == "r"
        assert os.path.isdir(checkout.local_root)
        assert os.path.isfile(os.path.join(checkout.local_root, "README.md"))
        local_root = checkout.local_root
    assert not os.path.exists(local_root)


def test_checkout_repository_pinned_ref_skips_resolution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tarball = _make_tarball("r-dev", SAMPLE_FILES)

    def fake(request: Any, timeout: Any = None) -> io.BytesIO:
        assert "info/refs" not in request.full_url, "should not resolve default branch"
        return io.BytesIO(tarball)

    monkeypatch.setattr("recursivist.github.urllib.request.urlopen", fake)
    target = parse_github_url("https://github.com/o/r/tree/dev")
    assert target is not None
    with checkout_repository(target) as checkout:
        assert checkout.ref == "dev"


def test_checkout_repository_subpath(monkeypatch: pytest.MonkeyPatch) -> None:
    tarball = _make_tarball("r-main", SAMPLE_FILES)
    monkeypatch.setattr(
        "recursivist.github.urllib.request.urlopen", _fake_urlopen(tarball=tarball)
    )
    target = parse_github_url("https://github.com/o/r/tree/main/pkg/util")
    assert target is not None
    with checkout_repository(target) as checkout:
        assert checkout.root_name == "util"
        assert os.path.isfile(os.path.join(checkout.local_root, "helpers.py"))


def test_checkout_repository_missing_subpath(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tarball = _make_tarball("r-main", SAMPLE_FILES)
    monkeypatch.setattr(
        "recursivist.github.urllib.request.urlopen", _fake_urlopen(tarball=tarball)
    )
    target = parse_github_url("https://github.com/o/r/tree/main/nope")
    assert target is not None
    with pytest.raises(GitHubError, match="was not found"):
        with checkout_repository(target):
            pass


def test_checkout_repository_download_404(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "recursivist.github.urllib.request.urlopen",
        _fake_urlopen(branch="main", download_fail=404),
    )
    target = parse_github_url("https://github.com/o/r")
    assert target is not None
    with pytest.raises(GitHubError, match="Could not download"):
        with checkout_repository(target):
            pass


def test_checkout_repository_rejects_traversal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tarball = _make_traversal_tarball()
    monkeypatch.setattr(
        "recursivist.github.urllib.request.urlopen", _fake_urlopen(tarball=tarball)
    )
    target = parse_github_url("https://github.com/o/r/tree/main")
    assert target is not None
    with pytest.raises(GitHubError):
        with checkout_repository(target):
            pass


def test_apply_github_urls_rewrites_paths() -> None:
    structure: dict[str, Any] = {
        "_files": [FileEntry(name="a.py", path="a.py")],
        "sub": {"_files": [FileEntry(name="b.py", path="b.py")]},
    }
    checkout = github.RepoCheckout(
        target=GitHubTarget("o", "r"),
        local_root="/tmp/whatever",
        ref="main",
        root_name="r",
    )
    apply_github_urls(structure, checkout)
    assert structure["_files"][0].path == "https://github.com/o/r/blob/main/a.py"
    assert (
        structure["sub"]["_files"][0].path
        == "https://github.com/o/r/blob/main/sub/b.py"
    )


def test_apply_github_urls_includes_subpath_prefix() -> None:
    structure: dict[str, Any] = {"_files": [FileEntry(name="c.py", path="c.py")]}
    checkout = github.RepoCheckout(
        target=GitHubTarget("o", "r", subpath="pkg/util"),
        local_root="/tmp/whatever",
        ref="dev",
        root_name="util",
    )
    apply_github_urls(structure, checkout)
    assert (
        structure["_files"][0].path == "https://github.com/o/r/blob/dev/pkg/util/c.py"
    )


def test_without_remote_unsupported_strips_git_and_mtime() -> None:
    from recursivist.flags import (
        METRIC_GIT,
        METRIC_LOC,
        METRIC_MTIME,
        METRIC_SIZE,
        DisplayOptions,
    )

    spec = DisplayOptions(
        sort_key=METRIC_MTIME,
        metrics=(METRIC_LOC, METRIC_MTIME, METRIC_SIZE),
        show_git_status=True,
    )
    remote = spec.without_remote_unsupported()
    assert remote.sort_key is None
    assert remote.metrics == (METRIC_LOC, METRIC_SIZE)
    assert remote.show_git_status is False
    git_sorted = DisplayOptions(sort_key=METRIC_GIT).without_remote_unsupported()
    assert git_sorted.sort_key is None


def test_without_remote_unsupported_keeps_loc_and_size_sort() -> None:
    from recursivist.flags import METRIC_LOC, DisplayOptions

    spec = DisplayOptions(sort_key=METRIC_LOC, metrics=(METRIC_LOC,))
    remote = spec.without_remote_unsupported()
    assert remote.sort_key == METRIC_LOC
    assert remote.metrics == (METRIC_LOC,)


@pytest.fixture
def patch_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch urlopen in both modules that reach the network."""
    tarball = _make_tarball("r-main", SAMPLE_FILES)
    fake = _fake_urlopen(branch="main", tarball=tarball)
    monkeypatch.setattr("recursivist.github.urllib.request.urlopen", fake)


def test_cli_visualize_github(runner: CliRunner, patch_network: None) -> None:
    result = runner.invoke(app, ["visualize", "https://github.com/o/r"])
    assert result.exit_code == 0
    assert "r" in result.stdout
    assert "README.md" in result.stdout
    assert "core.py" in result.stdout


def test_cli_visualize_github_full_path_shows_blob_urls(
    runner: CliRunner, patch_network: None
) -> None:
    result = runner.invoke(app, ["visualize", "https://github.com/o/r", "--full-path"])
    assert result.exit_code == 0
    assert "https://github.com/o/r/blob/main/README.md" in result.stdout


def test_cli_visualize_github_ignores_flags(
    runner: CliRunner, patch_network: None, caplog: pytest.LogCaptureFixture
) -> None:
    import logging

    with caplog.at_level(logging.INFO, logger="recursivist"):
        result = runner.invoke(
            app,
            [
                "visualize",
                "https://github.com/o/r",
                "--git-status",
                "--sort-by-git-status",
                "--mtime",
                "--sort-by-mtime",
                "--ignore-file",
                ".gitignore",
            ],
        )
    assert result.exit_code == 0
    assert "Ignoring" in caplog.text
    assert "not applicable to hosted repositories" in caplog.text
    for flag in ("--ignore-file", "--git-status", "--sort-by-git-status", "--mtime"):
        assert flag in caplog.text


def test_cli_visualize_github_mtime_not_annotated(
    runner: CliRunner, patch_network: None
) -> None:
    baseline = runner.invoke(app, ["visualize", "https://github.com/o/r"])
    with_mtime = runner.invoke(app, ["visualize", "https://github.com/o/r", "--mtime"])
    with_loc = runner.invoke(app, ["visualize", "https://github.com/o/r", "--loc"])
    assert baseline.exit_code == with_mtime.exit_code == with_loc.exit_code == 0
    assert with_mtime.stdout == baseline.stdout
    assert with_loc.stdout != baseline.stdout


def test_cli_visualize_github_sort_by_loc(
    runner: CliRunner, patch_network: None
) -> None:
    result = runner.invoke(
        app, ["visualize", "https://github.com/o/r", "--sort-by-loc"]
    )
    assert result.exit_code == 0
    assert "lines" in result.stdout


def test_cli_export_github_json_blob_urls(
    runner: CliRunner, patch_network: None, tmp_path: Any
) -> None:
    import json

    result = runner.invoke(
        app,
        [
            "export",
            "https://github.com/o/r",
            "-f",
            "json",
            "--full-path",
            "-o",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0
    data = json.loads((tmp_path / "structure.json").read_text())
    assert data["root"] == "r"
    paths = [f["path"] for f in data["structure"]["_files"]]
    assert "https://github.com/o/r/blob/main/README.md" in paths


def test_cli_visualize_invalid_local_dir(runner: CliRunner) -> None:
    result = runner.invoke(app, ["visualize", "/no/such/dir/here"])
    assert result.exit_code == 1


def test_cli_compare_both_github(
    runner: CliRunner, patch_network: None, caplog: pytest.LogCaptureFixture
) -> None:
    import logging

    with caplog.at_level(logging.INFO, logger="recursivist"):
        result = runner.invoke(
            app,
            [
                "compare",
                "https://github.com/o/r/tree/main/pkg",
                "https://github.com/o/r/tree/main/pkg/util",
                "--git-status",
            ],
        )
    assert result.exit_code == 0
    assert "not applicable to hosted repositories" in caplog.text


def test_cli_compare_mixed_local_and_github(
    runner: CliRunner, patch_network: None, tmp_path: Any
) -> None:
    local = tmp_path / "local"
    local.mkdir()
    (local / "only_local.py").write_text("print('x')\n")
    result = runner.invoke(
        app,
        ["compare", str(local), "https://github.com/o/r/tree/main/pkg"],
    )
    assert result.exit_code == 0
    assert "only_local.py" in result.stdout
    assert "core.py" in result.stdout


def test_cli_compare_mixed_honors_local_flags(
    runner: CliRunner,
    patch_network: None,
    tmp_path: Any,
    caplog: pytest.LogCaptureFixture,
) -> None:
    import logging

    local = tmp_path / "local"
    local.mkdir()
    (local / "f.py").write_text("print('x')\n")
    with caplog.at_level(logging.INFO, logger="recursivist"):
        result = runner.invoke(
            app,
            [
                "compare",
                str(local),
                "https://github.com/o/r/tree/main/pkg",
                "--git-status",
            ],
        )
    assert result.exit_code == 0
    assert "still apply to the local directory" in caplog.text


def test_cli_compare_invalid_local_side(runner: CliRunner, patch_network: None) -> None:
    result = runner.invoke(app, ["compare", "/no/such/dir", "https://github.com/o/r"])
    assert result.exit_code == 1


def test_cli_visualize_github_network_error(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "recursivist.github.urllib.request.urlopen",
        _fake_urlopen(refs_error=URLError("down")),
    )
    result = runner.invoke(app, ["visualize", "https://github.com/o/r"])
    assert result.exit_code == 1
