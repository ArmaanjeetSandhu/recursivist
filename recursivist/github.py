"""Remote GitHub repository support.

Lets the ``visualize``, ``export`` and ``compare`` commands accept a GitHub
repository URL anywhere they accept a local directory. A repository is
*materialized* by downloading its source archive from ``codeload.github.com``
and extracting it into a temporary directory, after which the existing
local-directory scanner, renderers and exporters are reused unchanged.

The archive endpoint is used rather than the REST API on purpose: the REST API
limits unauthenticated clients to 60 requests/hour (shared per public IP),
which is easily exhausted, whereas archive downloads are not subject to that
limit. Only the default branch is resolved through a lightweight, unlimited
``info/refs`` request when the caller did not pin a ref explicitly.

Because a hosted repository already reflects its ignore rules — files excluded
by a ``.gitignore`` are simply absent — and because every file in a checkout
shares the same Git status and effective modification time (the tip commit's),
the ``--ignore-file``, ``--git-status``, ``--sort-by-git-status``, ``--mtime``
and ``--sort-by-mtime`` options are not meaningful for a GitHub input and are
skipped. The lines-of-code and size annotations are retained, since they are
derived from the file contents. The ``--full-path`` option still applies, but
instead of a filesystem path it shows each file's canonical GitHub blob URL.

Only the Python standard library is used. When a token is present in the
``GITHUB_TOKEN`` or ``GH_TOKEN`` environment variable it is sent with every
request, which raises the rate limits and enables access to private
repositories.
"""

from __future__ import annotations

import logging
import os
import re
import shutil
import tarfile
import tempfile
import urllib.error
import urllib.request
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

from recursivist._models import FileEntry

logger = logging.getLogger(__name__)

_USER_AGENT = "recursivist"
_ARCHIVE_HOST = "https://codeload.github.com"
_WEB_HOST = "https://github.com"

_HTTP_RE = re.compile(
    r"""
    ^\s*
    (?:https?://)?
    (?:www\.)?
    github\.com/
    (?P<owner>[^/\s]+)/
    (?P<repo>[^/\s#?]+?)
    (?:\.git)?
    (?:/
        (?:tree|blob)/
        (?P<ref>[^/\s#?]+)
        (?:/(?P<subpath>[^\s#?]+?))?
    )?
    /?
    (?:[#?].*)?
    \s*$
    """,
    re.VERBOSE,
)

_SSH_RE = re.compile(
    r"^\s*git@github\.com:(?P<owner>[^/\s]+)/(?P<repo>[^/\s#?]+?)(?:\.git)?/?\s*$"
)


class GitHubError(Exception):
    """Raised when a GitHub repository cannot be resolved or downloaded.

    Carries a human-readable message suitable for surfacing directly to the
    user (e.g. an invalid URL, a missing repository, a rate-limit response, or
    a network/extraction failure).
    """


@dataclass(frozen=True)
class GitHubTarget:
    """A parsed reference to a GitHub repository or a subtree within one.

    Attributes:
        owner: Repository owner (user or organization).
        repo: Repository name, without any trailing ``.git``.
        ref: The branch, tag, or commit the caller pinned via
            ``/tree/<ref>`` or ``/blob/<ref>``, or ``None`` to use the
            repository's default branch.
        subpath: A forward-slashed path within the repository to treat as the
            root of the scan, or ``""`` for the whole repository.
    """

    owner: str
    repo: str
    ref: str | None = None
    subpath: str = ""

    @property
    def slug(self) -> str:
        """The ``owner/repo`` identifier."""
        return f"{self.owner}/{self.repo}"

    @property
    def display_name(self) -> str:
        """A short label for the scanned root (subpath basename or repo name)."""
        if self.subpath:
            return self.subpath.rstrip("/").split("/")[-1]
        return self.repo

    def blob_url(self, ref: str, relpath: str) -> str:
        """Return the canonical GitHub blob URL for a file.

        Args:
            ref: The concrete ref (branch, tag, or commit) to embed in the URL.
            relpath: The file's forward-slashed path relative to the repository
                root (already including any :attr:`subpath` prefix).

        Returns:
            A URL of the form
            ``https://github.com/<owner>/<repo>/blob/<ref>/<relpath>``.
        """
        clean = relpath.replace(os.sep, "/").lstrip("/")
        return f"{_WEB_HOST}/{self.owner}/{self.repo}/blob/{ref}/{clean}"


@dataclass(frozen=True)
class RepoCheckout:
    """A materialized GitHub repository on the local filesystem.

    Attributes:
        target: The :class:`GitHubTarget` that was checked out.
        local_root: Absolute path to the directory to scan — the extracted
            repository root, or the requested subpath within it.
        ref: The concrete ref that was downloaded (the pinned ref, or the
            resolved default branch).
        root_name: The display name for the scanned root (the repository name,
            or the last segment of the subpath).
    """

    target: GitHubTarget
    local_root: str
    ref: str
    root_name: str


def get_github_token() -> str | None:
    """Return a GitHub token from the environment, if configured.

    Looks up ``GITHUB_TOKEN`` first and then ``GH_TOKEN``. When set, the token
    is sent with archive and ref requests, raising rate limits and permitting
    access to private repositories.

    Returns:
        The token string, or ``None`` when neither variable is set.
    """
    for var in ("GITHUB_TOKEN", "GH_TOKEN"):
        token = os.environ.get(var)
        if token:
            return token.strip()
    return None


def is_github_url(text: str) -> bool:
    """Return whether *text* looks like a GitHub repository reference.

    This is a cheap syntactic check used to decide whether an argument should
    be treated as a remote repository rather than a local path; it does not
    contact the network.

    Args:
        text: The raw argument to test.

    Returns:
        ``True`` if *text* parses as a GitHub URL, ``False`` otherwise.
    """
    return parse_github_url(text) is not None


def parse_github_url(text: str) -> GitHubTarget | None:
    """Parse a GitHub repository URL into a :class:`GitHubTarget`.

    Accepts the common HTTPS forms (with or without scheme, ``www.`` or a
    trailing ``.git``), an optional ``/tree/<ref>[/<subpath>]`` or
    ``/blob/<ref>/<subpath>`` selector, and the SSH form
    ``git@github.com:owner/repo.git``.

    When a ``/tree`` or ``/blob`` selector is present, the segment immediately
    after it is taken as the ref and everything beyond it as the subpath. Refs
    that themselves contain slashes (e.g. ``feature/x``) therefore cannot be
    distinguished from a subpath by URL alone; pass such a repository without a
    selector, or pin the ref with a plain branch name.

    Args:
        text: The raw argument to parse.

    Returns:
        The parsed :class:`GitHubTarget`, or ``None`` when *text* is not a
        recognizable GitHub URL.
    """
    if not text or "github.com" not in text:
        return None
    ssh = _SSH_RE.match(text)
    if ssh:
        return GitHubTarget(owner=ssh.group("owner"), repo=ssh.group("repo"))
    match = _HTTP_RE.match(text)
    if not match:
        return None
    subpath = (match.group("subpath") or "").strip("/")
    return GitHubTarget(
        owner=match.group("owner"),
        repo=match.group("repo"),
        ref=match.group("ref"),
        subpath=subpath,
    )


def _request(
    url: str, token: str | None, *, accept: str | None = None
) -> urllib.request.Request:
    """Build a urllib request with the shared headers and optional auth."""
    headers = {"User-Agent": _USER_AGENT}
    if accept:
        headers["Accept"] = accept
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return urllib.request.Request(url, headers=headers)


def resolve_default_branch(target: GitHubTarget, token: str | None = None) -> str:
    """Resolve a repository's default branch without using the REST API.

    Reads the symbolic ``HEAD`` reference from the repository's Git smart-HTTP
    ``info/refs`` advertisement, which is not subject to the REST API's
    unauthenticated rate limit.

    Args:
        target: The repository whose default branch is wanted.
        token: Optional GitHub token for private repositories.

    Returns:
        The default branch name (e.g. ``"main"``).

    Raises:
        GitHubError: If the repository is missing or private without a valid
            token, or if the default branch cannot be determined.
    """
    url = f"{_WEB_HOST}/{target.owner}/{target.repo}/info/refs?service=git-upload-pack"
    try:
        with urllib.request.urlopen(_request(url, token), timeout=30) as response:
            payload = response.read()
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 404):
            raise GitHubError(
                f"Repository '{target.slug}' was not found. It may not exist, "
                "or it may be private (set GITHUB_TOKEN to access private repositories)."
            ) from exc
        raise GitHubError(
            f"Could not reach GitHub for '{target.slug}' (HTTP {exc.code})."
        ) from exc
    except OSError as exc:
        raise GitHubError(f"Could not reach GitHub for '{target.slug}': {exc}") from exc

    match = re.search(rb"symref=HEAD:refs/heads/([^\x00 \n]+)", payload)
    if not match:
        raise GitHubError(
            f"Could not determine the default branch for '{target.slug}'."
        )
    return match.group(1).decode("utf-8", "replace")


def _download_archive(
    target: GitHubTarget, ref: str, token: str | None, dest: str
) -> None:
    """Download the ``tar.gz`` source archive for *ref* to the file *dest*."""
    url = f"{_ARCHIVE_HOST}/{target.owner}/{target.repo}/tar.gz/{ref}"
    try:
        with urllib.request.urlopen(_request(url, token), timeout=120) as response:
            with open(dest, "wb") as fh:
                shutil.copyfileobj(response, fh)
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 404):
            raise GitHubError(
                f"Could not download '{target.slug}' at ref '{ref}'. The "
                "repository or ref may not exist, or it may be private "
                "(set GITHUB_TOKEN to access private repositories)."
            ) from exc
        raise GitHubError(
            f"Could not download '{target.slug}' at ref '{ref}' (HTTP {exc.code})."
        ) from exc
    except OSError as exc:
        raise GitHubError(
            f"Could not download '{target.slug}' at ref '{ref}': {exc}"
        ) from exc


def _is_within(base: str, path: str) -> bool:
    """Return whether *path* resolves to a location inside *base*."""
    base_real = os.path.realpath(base)
    target_real = os.path.realpath(path)
    return target_real == base_real or target_real.startswith(base_real + os.sep)


def _safe_extract(archive_path: str, dest_dir: str) -> None:
    """Extract *archive_path* into *dest_dir*, rejecting path traversal.

    Uses the tar ``data`` extraction filter when available (Python 3.12+) and
    otherwise validates every member manually so that entries with absolute
    paths, ``..`` components, or symlinks pointing outside *dest_dir* cannot
    escape the destination directory. Any extraction failure is surfaced as a
    :class:`GitHubError`.
    """
    try:
        with tarfile.open(archive_path, mode="r:gz") as tar:
            if hasattr(tarfile, "data_filter"):
                tar.extractall(dest_dir, filter="data")
                return
            for member in tar.getmembers():
                member_path = os.path.join(dest_dir, member.name)
                if not _is_within(dest_dir, member_path):
                    raise GitHubError(
                        f"Refusing to extract unsafe path from archive: {member.name!r}"
                    )
                if member.issym() or member.islnk():
                    link_path = os.path.join(
                        os.path.dirname(member_path), member.linkname
                    )
                    if not _is_within(dest_dir, link_path):
                        raise GitHubError(
                            "Refusing to extract unsafe link from archive: "
                            f"{member.name!r}"
                        )
            tar.extractall(dest_dir)
    except tarfile.TarError as exc:
        raise GitHubError(f"Could not extract repository archive: {exc}") from exc


def _locate_root(extract_dir: str, target: GitHubTarget) -> str:
    """Return the directory to scan within a freshly extracted archive.

    GitHub archives contain a single top-level directory (``<repo>-<ref>``);
    this returns that directory, descending into :attr:`GitHubTarget.subpath`
    when one was requested.

    Raises:
        GitHubError: If the archive layout is unexpected or the requested
            subpath does not exist or is not a directory.
    """
    entries = [e for e in os.listdir(extract_dir) if not e.startswith(".")]
    if len(entries) != 1:
        entries = os.listdir(extract_dir)
        if len(entries) != 1:
            raise GitHubError(f"Unexpected archive layout for '{target.slug}'.")
    root = os.path.join(extract_dir, entries[0])
    if target.subpath:
        candidate = os.path.join(root, target.subpath.replace("/", os.sep))
        if not _is_within(root, candidate) or not os.path.isdir(candidate):
            raise GitHubError(
                f"Path '{target.subpath}' was not found in '{target.slug}'."
            )
        return candidate
    return root


@contextmanager
def checkout_repository(
    target: GitHubTarget, token: str | None = None
) -> Iterator[RepoCheckout]:
    """Download and extract a GitHub repository into a temporary directory.

    Resolves the ref (using the default branch when the target does not pin
    one), downloads the source archive, and safely extracts it. The extracted
    files are removed when the context exits.

    Args:
        target: The repository (and optional subtree) to check out.
        token: Optional GitHub token; defaults to :func:`get_github_token`.

    Yields:
        A :class:`RepoCheckout` describing the local extraction.

    Raises:
        GitHubError: If the repository cannot be resolved, downloaded, or
            extracted.
    """
    if token is None:
        token = get_github_token()
    ref = target.ref or resolve_default_branch(target, token)
    temp_dir = tempfile.mkdtemp(prefix="recursivist-gh-")
    try:
        archive_path = os.path.join(temp_dir, "archive.tar.gz")
        logger.debug("Downloading %s at ref '%s'", target.slug, ref)
        _download_archive(target, ref, token, archive_path)
        extract_dir = os.path.join(temp_dir, "extracted")
        os.makedirs(extract_dir, exist_ok=True)
        _safe_extract(archive_path, extract_dir)
        os.remove(archive_path)
        local_root = _locate_root(extract_dir, target)
        yield RepoCheckout(
            target=target,
            local_root=local_root,
            ref=ref,
            root_name=target.display_name,
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def apply_github_urls(
    structure: dict[str, Any], checkout: RepoCheckout
) -> dict[str, Any]:
    """Rewrite each file's display path to its GitHub blob URL, in place.

    Used when ``--full-path`` is requested for a GitHub input: it walks
    *structure* and replaces every :class:`~recursivist._models.FileEntry`
    ``path`` with the file's canonical blob URL, so the unmodified renderers
    and exporters display GitHub URLs instead of temporary filesystem paths.

    Args:
        structure: A scanned structure produced by
            :func:`recursivist.scanner.get_directory_structure` for the
            checkout's :attr:`RepoCheckout.local_root`.
        checkout: The checkout the structure was scanned from, supplying the
            owner, repo, ref, and subpath used to build URLs.

    Returns:
        The same *structure* object, with file paths rewritten.
    """
    target = checkout.target
    base_prefix = target.subpath.strip("/")

    def _walk(node: dict[str, Any], rel_dir: str) -> None:
        files = node.get("_files")
        if files:
            rewritten: list[FileEntry] = []
            for raw in files:
                entry = FileEntry.coerce(raw)
                rel_file = f"{rel_dir}/{entry.name}" if rel_dir else entry.name
                url = target.blob_url(checkout.ref, rel_file)
                rewritten.append(entry._replace(path=url))
            node["_files"] = rewritten
        for name, content in node.items():
            if name.startswith("_") or not isinstance(content, dict):
                continue
            next_dir = f"{rel_dir}/{name}" if rel_dir else name
            _walk(content, next_dir)

    _walk(structure, base_prefix)
    return structure
