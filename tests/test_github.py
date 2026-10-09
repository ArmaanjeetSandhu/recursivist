"""Tests for remote GitHub repository support.

Network access is always mocked: :func:`urllib.request.urlopen` is patched to serve a
symref advertisement (for default-branch resolution) and an in-memory ``tar.gz`` archive
(for the source download), so the real download → extract → scan → render pipeline runs
end to end without touching the network.
"""

from __future__ import annotations

import io
import os
import tarfile
from email.message import Message
from typing import TYPE_CHECKING, Any
from unittest import mock
from urllib.error import HTTPError, URLError

import pytest
from typer.testing import CliRunner

from recursivist import github
from recursivist._models import Directory, FileEntry
from recursivist.cli import app
from recursivist.github import (
    GitHubError,
    GitHubTarget,
    apply_github_urls,
    checkout_repository,
    commit_shas_equal,
    get_github_token,
    parse_github_url,
    resolve_commit_shas,
    resolve_default_branch,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from pathlib import Path


def _make_tarball(
    top: str, files: Mapping[str, str], links: Mapping[str, str] | None = None
) -> bytes:
    """Build a ``tar.gz`` mimicking a GitHub source archive layout.

    Args:
        top: The single top-level directory name (e.g. ``"repo-main"``).
        files: Mapping of repo-relative path to text content.
        links: Mapping of repo-relative path to symlink target.

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
        for rel, link_target in (links or {}).items():
            info = tarfile.TarInfo(f"{top}/{rel}")
            info.type = tarfile.SYMTYPE
            info.linkname = link_target
            info.mtime = 1700000000
            tar.addfile(info)
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
        (
            "https://github.com/o/r/tree/main/my%20dir/sub%231",
            "o",
            "r",
            "main",
            "my dir/sub#1",
        ),
        (
            "https://github.com/o/r/blob/main/src/my%20file%231.py",
            "o",
            "r",
            "main",
            "src/my file#1.py",
        ),
        ("https://github.com/o/r/tree/v1%2B2/docs", "o", "r", "v1+2", "docs"),
        ("https://github.com/o/r/tree/main/caf%C3%A9", "o", "r", "main", "café"),
        ("https://GitHub.com/o/r", "o", "r", None, ""),
        ("HTTPS://WWW.GITHUB.COM/o/r", "o", "r", None, ""),
        ("GitHub.com/Owner/Repo/tree/Main/Src", "Owner", "Repo", "Main", "Src"),
        ("git@GitHub.com:o/r.git", "o", "r", None, ""),
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


def test_parse_github_url_prefers_existing_local_path_without_scheme(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "github.com" / "golang" / "go").mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    assert parse_github_url("github.com/golang/go") is None
    assert parse_github_url("github.com/golang/go/") is None
    target = parse_github_url("https://github.com/golang/go")
    assert target is not None
    assert target.slug == "golang/go"


def test_parse_github_url_without_scheme_is_remote_when_path_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    target = parse_github_url("github.com/golang/go")
    assert target is not None
    assert target.slug == "golang/go"


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


def test_target_blob_url_percent_encodes_special_characters() -> None:
    url = GitHubTarget("o", "r").blob_url("main", "src/my file#1.py")
    assert url == "https://github.com/o/r/blob/main/src/my%20file%231.py"


def test_target_blob_url_encodes_query_and_percent_but_keeps_slashes() -> None:
    url = GitHubTarget("o", "r").blob_url("feature/x", "a?b/100%.txt")
    assert url == "https://github.com/o/r/blob/feature/x/a%3Fb/100%25.txt"


def test_target_blob_url_encodes_non_ascii() -> None:
    url = GitHubTarget("o", "r").blob_url("main", "docs/café.md")
    assert url == "https://github.com/o/r/blob/main/docs/caf%C3%A9.md"


def test_parse_then_blob_url_round_trips_encoding() -> None:
    url = "https://github.com/o/r/blob/main/src/my%20file%231.py"
    target = parse_github_url(url)
    assert target is not None
    assert target.ref is not None
    assert target.blob_url(target.ref, target.subpath) == url


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
    target = GitHubTarget("o", "missing")
    with pytest.raises(GitHubError, match="was not found"):
        resolve_default_branch(target)


def test_resolve_default_branch_network_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "recursivist.github.urllib.request.urlopen",
        _fake_urlopen(refs_error=URLError("boom")),
    )
    target = GitHubTarget("o", "r")
    with pytest.raises(GitHubError, match="Could not reach GitHub"):
        resolve_default_branch(target)


def test_resolve_default_branch_missing_symref(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake(request: Any, timeout: Any = None) -> io.BytesIO:
        return io.BytesIO(b"no symref here")

    monkeypatch.setattr("recursivist.github.urllib.request.urlopen", fake)
    target = GitHubTarget("o", "r")
    with pytest.raises(GitHubError, match="default branch"):
        resolve_default_branch(target)


def _pkt(line: bytes) -> bytes:
    """Frame *line* as a Git smart-HTTP pkt-line."""
    return f"{len(line) + 4:04x}".encode() + line


def _full_refs_payload() -> bytes:
    """A properly pkt-framed advertisement with branches and an annotated tag.

    ``HEAD`` and ``main`` share a commit; ``dev`` has its own commit; the annotated tag
    ``v1.0`` peels to the ``dev`` commit.
    """
    head = b"1" * 40
    dev = b"2" * 40
    tag_obj = b"3" * 40
    return b"".join(
        [
            _pkt(b"# service=git-upload-pack\n"),
            b"0000",
            _pkt(
                head
                + b" HEAD\x00multi_ack symref=HEAD:refs/heads/main object-format=sha1\n"
            ),
            _pkt(head + b" refs/heads/main\n"),
            _pkt(dev + b" refs/heads/dev\n"),
            _pkt(tag_obj + b" refs/tags/v1.0\n"),
            _pkt(dev + b" refs/tags/v1.0^{}\n"),
            b"0000",
        ]
    )


def _serve_payload(payload: bytes) -> Callable[..., Any]:
    def fake(request: Any, timeout: Any = None) -> io.BytesIO:
        return io.BytesIO(payload)

    return fake


def test_resolve_commit_shas_branch_and_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "recursivist.github.urllib.request.urlopen",
        _serve_payload(_full_refs_payload()),
    )
    assert resolve_commit_shas(GitHubTarget("o", "r"), [None, "main"]) == [
        "1" * 40,
        "1" * 40,
    ]


def test_resolve_commit_shas_annotated_tag_peels_to_commit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "recursivist.github.urllib.request.urlopen",
        _serve_payload(_full_refs_payload()),
    )
    dev_sha, tag_sha = resolve_commit_shas(GitHubTarget("o", "r"), ["dev", "v1.0"])
    assert dev_sha == "2" * 40
    assert tag_sha == "2" * 40


def test_resolve_commit_shas_explicit_commit_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "recursivist.github.urllib.request.urlopen",
        _serve_payload(_full_refs_payload()),
    )
    assert resolve_commit_shas(GitHubTarget("o", "r"), ["2222222"]) == ["2222222"]


def test_resolve_commit_shas_unknown_ref_is_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "recursivist.github.urllib.request.urlopen",
        _serve_payload(_full_refs_payload()),
    )
    assert resolve_commit_shas(GitHubTarget("o", "r"), ["nope"]) == [None]


def test_resolve_commit_shas_network_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "recursivist.github.urllib.request.urlopen",
        _fake_urlopen(refs_error=URLError("boom")),
    )
    target = GitHubTarget("o", "r")
    with pytest.raises(GitHubError, match="Could not reach GitHub"):
        resolve_commit_shas(target, [None])


def test_commit_shas_equal() -> None:
    assert commit_shas_equal("a" * 40, "A" * 40) is True
    assert commit_shas_equal("a" * 40, "b" * 40) is False
    assert commit_shas_equal("abcdef1234567890", "abcdef1") is True
    assert commit_shas_equal("abcdef1234", "abcde") is False
    assert commit_shas_equal(None, "a" * 40) is False
    assert commit_shas_equal("a" * 40, None) is False


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


def test_checkout_repository_encoded_subpath(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tarball = _make_tarball("r-main", {"my dir/a.py": "x = 1\n"})
    monkeypatch.setattr(
        "recursivist.github.urllib.request.urlopen", _fake_urlopen(tarball=tarball)
    )
    target = parse_github_url("https://github.com/o/r/tree/main/my%20dir")
    assert target is not None
    with checkout_repository(target) as checkout:
        assert checkout.root_name == "my dir"
        assert os.path.isfile(os.path.join(checkout.local_root, "a.py"))


def test_checkout_repository_encodes_ref_in_archive_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tarball = _make_tarball("r-v1", SAMPLE_FILES)
    requested: list[str] = []

    def fake(request: Any, timeout: Any = None) -> io.BytesIO:
        requested.append(request.full_url)
        return io.BytesIO(tarball)

    monkeypatch.setattr("recursivist.github.urllib.request.urlopen", fake)
    target = parse_github_url("https://github.com/o/r/tree/v1%231")
    assert target is not None
    assert target.ref == "v1#1"
    with checkout_repository(target):
        pass
    assert requested == ["https://codeload.github.com/o/r/tar.gz/v1%231"]


def test_checkout_repository_missing_subpath(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tarball = _make_tarball("r-main", SAMPLE_FILES)
    monkeypatch.setattr(
        "recursivist.github.urllib.request.urlopen", _fake_urlopen(tarball=tarball)
    )
    target = parse_github_url("https://github.com/o/r/tree/main/nope")
    assert target is not None
    with (
        pytest.raises(GitHubError, match="was not found"),
        checkout_repository(target),
    ):
        pass


def test_checkout_repository_download_404(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "recursivist.github.urllib.request.urlopen",
        _fake_urlopen(branch="main", download_fail=404),
    )
    target = parse_github_url("https://github.com/o/r")
    assert target is not None
    with (
        pytest.raises(GitHubError, match="Could not download"),
        checkout_repository(target),
    ):
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
    with pytest.raises(GitHubError), checkout_repository(target):
        pass


def test_apply_github_urls_rewrites_paths() -> None:
    structure = Directory(
        files=[FileEntry(name="a.py", path="a.py")],
        subdirectories={"sub": Directory(files=[FileEntry(name="b.py", path="b.py")])},
    )
    checkout = github.RepoCheckout(
        target=GitHubTarget("o", "r"),
        local_root="/tmp/whatever",
        ref="main",
        root_name="r",
    )
    apply_github_urls(structure, checkout)
    assert structure.files[0].path == "https://github.com/o/r/blob/main/a.py"
    assert (
        structure.subdirectories["sub"].files[0].path
        == "https://github.com/o/r/blob/main/sub/b.py"
    )


def test_apply_github_urls_includes_subpath_prefix() -> None:
    structure = Directory(files=[FileEntry(name="c.py", path="c.py")])
    checkout = github.RepoCheckout(
        target=GitHubTarget("o", "r", subpath="pkg/util"),
        local_root="/tmp/whatever",
        ref="dev",
        root_name="util",
    )
    apply_github_urls(structure, checkout)
    assert structure.files[0].path == "https://github.com/o/r/blob/dev/pkg/util/c.py"


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


@pytest.mark.usefixtures("patch_network")
def test_cli_visualize_github(runner: CliRunner) -> None:
    result = runner.invoke(app, ["visualize", "https://github.com/o/r"])
    assert result.exit_code == 0
    assert "r" in result.stdout
    assert "README.md" in result.stdout
    assert "core.py" in result.stdout


@pytest.mark.usefixtures("patch_network")
def test_cli_visualize_github_full_path_shows_blob_urls(runner: CliRunner) -> None:
    result = runner.invoke(app, ["visualize", "https://github.com/o/r", "--full-path"])
    assert result.exit_code == 0
    assert "https://github.com/o/r/blob/main/README.md" in result.stdout


@pytest.mark.usefixtures("patch_network")
def test_cli_visualize_github_ignores_flags(
    runner: CliRunner, caplog: pytest.LogCaptureFixture
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


@pytest.mark.usefixtures("patch_network")
def test_cli_visualize_github_does_not_use_configured_ignore_file(
    runner: CliRunner, caplog: pytest.LogCaptureFixture
) -> None:
    """A saved ignore file is left out for a GitHub input, without a message."""
    import logging

    from recursivist import cli as cli_module

    saved = runner.invoke(app, ["config", "set", "ignore-file", ".gitignore"])
    assert saved.exit_code == 0
    with (
        caplog.at_level(logging.INFO, logger="recursivist"),
        mock.patch.object(
            cli_module, "_scan_directory", wraps=cli_module._scan_directory
        ) as scan,
    ):
        result = runner.invoke(app, ["visualize", "https://github.com/o/r"])
    assert result.exit_code == 0
    assert scan.call_args.args[2] is None
    assert "Ignoring" not in caplog.text


def _rendered_tree(stdout: str) -> str:
    """Return the tree from ``visualize`` output, without the log lines above it."""
    return stdout[stdout.index("📂 r") :]


@pytest.mark.usefixtures("patch_network")
def test_cli_visualize_github_uses_saved_exclude(runner: CliRunner) -> None:
    """Saved directory exclusions apply to a GitHub input as ``--exclude`` does."""
    baseline = runner.invoke(app, ["visualize", "https://github.com/o/r"])
    saved = runner.invoke(app, ["config", "set", "exclude", "pkg"])
    excluded = runner.invoke(app, ["visualize", "https://github.com/o/r"])
    assert baseline.exit_code == saved.exit_code == excluded.exit_code == 0
    assert "core.py" in _rendered_tree(baseline.stdout)
    assert "core.py" not in _rendered_tree(excluded.stdout)
    assert "README.md" in _rendered_tree(excluded.stdout)


@pytest.mark.usefixtures("patch_network")
def test_cli_visualize_github_mtime_not_annotated(runner: CliRunner) -> None:
    baseline = runner.invoke(app, ["visualize", "https://github.com/o/r"])
    with_mtime = runner.invoke(app, ["visualize", "https://github.com/o/r", "--mtime"])
    with_loc = runner.invoke(app, ["visualize", "https://github.com/o/r", "--loc"])
    assert baseline.exit_code == with_mtime.exit_code == with_loc.exit_code == 0
    assert _rendered_tree(with_mtime.stdout) == _rendered_tree(baseline.stdout)
    assert _rendered_tree(with_loc.stdout) != _rendered_tree(baseline.stdout)


@pytest.mark.usefixtures("patch_network")
def test_cli_visualize_github_sort_by_loc(runner: CliRunner) -> None:
    result = runner.invoke(
        app, ["visualize", "https://github.com/o/r", "--sort-by-loc"]
    )
    assert result.exit_code == 0
    assert "lines" in result.stdout


@pytest.mark.usefixtures("patch_network")
def test_cli_export_github_json_blob_urls(runner: CliRunner, tmp_path: Any) -> None:
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
    paths = [f["path"] for f in data["structure"]["files"]]
    assert "https://github.com/o/r/blob/main/README.md" in paths


def test_cli_visualize_invalid_local_dir(runner: CliRunner) -> None:
    result = runner.invoke(app, ["visualize", "/no/such/dir/here"])
    assert result.exit_code == 1


@pytest.mark.usefixtures("patch_network")
def test_cli_compare_both_github(
    runner: CliRunner, caplog: pytest.LogCaptureFixture
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


@pytest.mark.usefixtures("patch_network")
def test_cli_compare_mixed_local_and_github(runner: CliRunner, tmp_path: Any) -> None:
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


@pytest.mark.usefixtures("patch_network")
def test_cli_compare_mixed_honors_local_flags(
    runner: CliRunner,
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


@pytest.mark.usefixtures("patch_network")
def test_cli_compare_mixed_applies_configured_ignore_file_to_local_side(
    runner: CliRunner,
    tmp_path: Any,
    caplog: pytest.LogCaptureFixture,
) -> None:
    import logging

    local = tmp_path / "local"
    local.mkdir()
    (local / "kept.py").write_text("print('x')\n")
    (local / "app.log").write_text("x\n")
    (local / ".gitignore").write_text("*.log\n")
    saved = runner.invoke(app, ["config", "set", "ignore-file", ".gitignore"])
    assert saved.exit_code == 0
    with caplog.at_level(logging.INFO, logger="recursivist"):
        result = runner.invoke(
            app, ["compare", str(local), "https://github.com/o/r/tree/main/pkg"]
        )
    assert result.exit_code == 0
    assert "kept.py" in result.stdout
    assert "app.log" not in result.stdout
    assert "still apply to the local directory" not in caplog.text


@pytest.mark.usefixtures("patch_network")
def test_cli_compare_invalid_local_side(runner: CliRunner) -> None:
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


def test_apply_github_urls_rewrites_underscore_and_field_named_directories() -> None:
    structure = Directory(
        subdirectories={
            "__tests__": Directory(files=[FileEntry(name="a.js", path="/tmp/x/a.js")]),
            "files": Directory(files=[FileEntry(name="b.js", path="/tmp/x/b.js")]),
        }
    )
    checkout = github.RepoCheckout(
        target=GitHubTarget("o", "r"),
        local_root="/tmp/whatever",
        ref="main",
        root_name="r",
    )
    apply_github_urls(structure, checkout)
    assert (
        structure.subdirectories["__tests__"].files[0].path
        == "https://github.com/o/r/blob/main/__tests__/a.js"
    )
    assert (
        structure.subdirectories["files"].files[0].path
        == "https://github.com/o/r/blob/main/files/b.js"
    )
