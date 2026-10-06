"""Remote GitHub repository support.

Lets the ``visualize``, ``export`` and ``compare`` commands accept a GitHub repository
URL anywhere they accept a local directory. A repository is *materialized* by
downloading its source archive from ``codeload.github.com`` and extracting it into a
temporary directory, which is then scanned, rendered and exported exactly like a local
directory.

The archive endpoint is used rather than the REST API on purpose: the REST API limits
unauthenticated clients to 60 requests/hour (shared per public IP), which is easily
exhausted, whereas archive downloads are not subject to that limit. Only the default
branch is resolved through a lightweight, unlimited ``info/refs`` request when the
caller did not pin a ref explicitly.

Because a hosted repository already reflects its ignore rules — files excluded by a
``.gitignore`` are simply absent — and because every file in a checkout shares the same
Git status and effective modification time (the tip commit's), the ``--ignore-file``,
``--git-status``, ``--sort-by-git-status``, ``--mtime`` and ``--sort-by-mtime`` options
are not meaningful for a GitHub input and are skipped. The lines-of-code and size
annotations are retained, since they are derived from the file contents. The
``--full-path`` option still applies, but instead of a filesystem path it shows each
file's canonical GitHub blob URL.

Only the Python standard library is used. When a token is present in the
``GITHUB_TOKEN`` or ``GH_TOKEN`` environment variable it is sent with every request,
which raises the rate limits and enables access to private repositories.
"""

from __future__ import annotations

import logging
import os
import posixpath
import re
import shutil
import tarfile
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from contextlib import contextmanager
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from collections.abc import Generator, Iterator

    from recursivist._models import Directory, FileEntry

logger = logging.getLogger(__name__)

_USER_AGENT = "recursivist"
_ARCHIVE_HOST = "https://codeload.github.com"
_WEB_HOST = "https://github.com"

_HTTP_RE = re.compile(
    r"""
    \A
    (?:https?://)?
    (?:www\.)?
    github\.com/
    (?P<owner>[^/\s]+)/
    (?P<repo>[^/\s#?]+)
    (?:/
        (?:tree|blob)/
        (?P<ref>[^/\s#?]+)
        (?:/(?P<subpath>[^\s#?]*))?
    )?
    /?
    (?:[#?].*)?
    \Z
    """,
    re.VERBOSE | re.IGNORECASE,
)

_SSH_RE = re.compile(
    r"\Agit@github\.com:(?P<owner>[^/\s]+)/(?P<repo>[^/\s#?]+)/?\Z", re.IGNORECASE
)

_HAS_SCHEME_RE = re.compile(r"\A(?:[a-zA-Z][a-zA-Z0-9+.-]*://|git@)")


def _strip_git_suffix(repo: str) -> str:
    """Return *repo* without a trailing ``.git``, unless that is the whole name."""
    if repo.endswith(".git") and len(repo) > 4:
        return repo[:-4]
    return repo


class GitHubError(Exception):
    """Raised when a GitHub repository cannot be resolved or downloaded.

    Carries a human-readable message suitable for surfacing directly to the user (e.g.
    an invalid URL, a missing repository, a rate-limit response, or a network/extraction
    failure).
    """


@dataclass(frozen=True)
class GitHubTarget:
    """A parsed reference to a GitHub repository or a subtree within one.

    Attributes:
        owner: Repository owner (user or organization).
        repo: Repository name, without any trailing ``.git``.
        ref: The branch, tag, or commit the caller pinned via ``/tree/<ref>`` or
            ``/blob/<ref>``, or ``None`` to use the repository's default branch.
        subpath: A forward-slashed path within the repository to treat as the root of
            the scan, or ``""`` for the whole repository.
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
            relpath: The file's forward-slashed path relative to the repository root
                (already including any `subpath` prefix).

        Returns:
            A URL of the form ``https://github.com/<owner>/<repo>/blob/<ref>/<relpath>``,
            with the ref and path percent-encoded to keep characters such as spaces,
            ``#`` and ``?`` from breaking the link. ``/`` is kept as the path separator.
        """
        clean = relpath.replace(os.sep, "/").lstrip("/")
        quoted_ref = urllib.parse.quote(ref, safe="/")
        quoted_path = urllib.parse.quote(clean, safe="/")
        return f"{_WEB_HOST}/{self.owner}/{self.repo}/blob/{quoted_ref}/{quoted_path}"


@dataclass(frozen=True)
class RepoCheckout:
    """A materialized GitHub repository on the local filesystem.

    Attributes:
        target: The [`GitHubTarget`][recursivist.github.GitHubTarget] that was checked
            out. Its ``subpath`` always names the scanned directory: when the requested
            subpath pointed at a file, it is that file's parent directory.
        local_root: Absolute path to the directory to scan — the extracted repository
            root, or the requested subpath within it (the containing directory, when the
            subpath pointed at a file).
        ref: The concrete ref that was downloaded (the pinned ref, or the resolved
            default branch).
        root_name: The display name for the scanned root (the repository name, or the
            last segment of the scanned subpath).
    """

    target: GitHubTarget
    local_root: str
    ref: str
    root_name: str


def get_github_token() -> str | None:
    """Return a GitHub token from the environment, if configured.

    Looks up ``GITHUB_TOKEN`` first and then ``GH_TOKEN``. When set, the token is sent
    with archive and ref requests, raising rate limits and permitting access to private
    repositories.

    Returns:
        The token string, or ``None`` when neither variable is set.
    """
    for var in ("GITHUB_TOKEN", "GH_TOKEN"):
        token = os.environ.get(var)
        if token:
            return token.strip()
    return None


def parse_github_url(text: str) -> GitHubTarget | None:
    """Parse a GitHub repository URL into a
    [`GitHubTarget`][recursivist.github.GitHubTarget].

    Accepts the common HTTPS forms (with or without scheme, ``www.`` or a trailing
    ``.git``), an optional ``/tree/<ref>[/<subpath>]`` or ``/blob/<ref>/<subpath>``
    selector, and the SSH form ``git@github.com:owner/repo.git``. Percent-encoded
    characters in the ref and subpath (e.g. ``%20``, ``%23``) are decoded, so URLs
    copied from a browser address bar resolve to the real names. The scheme and host are
    matched case-insensitively, as URL hosts are; owner, repository, ref and subpath are
    kept exactly as written.

    A form without a scheme (``github.com/owner/repo``) is also a valid relative
    filesystem path, e.g. a GOPATH-style ``src/github.com/golang/go`` checkout entered
    from ``src``. When such an argument names an existing local file or directory, it is
    treated as that local path and ``None`` is returned. A URL with an explicit
    ``http(s)://`` scheme, or the SSH form, is always treated as GitHub.

    The subpath is returned as written, whether it names a directory or a file: the two
    cannot be told apart from the URL alone. A subpath that turns out to be a file — as
    in the ``/blob/<ref>/<file>`` URL of a GitHub file page — is resolved to its
    containing directory by
    [`checkout_repository`][recursivist.github.checkout_repository].

    When a ``/tree`` or ``/blob`` selector is present, the segment immediately after it
    is taken as the ref and everything beyond it as the subpath. Refs that themselves
    contain slashes (e.g. ``feature/x``) therefore cannot be distinguished from a
    subpath by URL alone; pass such a repository without a selector, or pin the ref with
    a plain branch name.

    Args:
        text: The raw argument to parse.

    Returns:
        The parsed [`GitHubTarget`][recursivist.github.GitHubTarget], or ``None`` when
        *text* is not a recognizable GitHub URL.
    """
    if not text or "github.com" not in text.lower():
        return None
    text = text.strip()
    if _HAS_SCHEME_RE.match(text) is None and os.path.exists(text):
        return None
    ssh = _SSH_RE.match(text)
    if ssh:
        return GitHubTarget(
            owner=ssh.group("owner"), repo=_strip_git_suffix(ssh.group("repo"))
        )
    match = _HTTP_RE.match(text)
    if not match:
        return None
    ref = match.group("ref")
    if ref is not None:
        ref = urllib.parse.unquote(ref)
    subpath = urllib.parse.unquote(match.group("subpath") or "").strip("/")
    return GitHubTarget(
        owner=match.group("owner"),
        repo=_strip_git_suffix(match.group("repo")),
        ref=ref,
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


def _fetch_refs_advertisement(target: GitHubTarget, token: str | None) -> bytes:
    """Fetch a repository's Git smart-HTTP ``info/refs`` advertisement.

    The advertisement is served by the ``git-upload-pack`` service and lists every ref
    (branches, tags, and the symbolic ``HEAD``) together with the commit each points at.
    It is not subject to the REST API's unauthenticated rate limit, so it is used both
    to discover the default branch and to resolve refs to commit SHAs.

    Args:
        target: The repository whose refs are wanted.
        token: Optional GitHub token for private repositories.

    Returns:
        The raw advertisement payload.

    Raises:
        GitHubError: If the repository is missing or private without a valid token, or
            cannot otherwise be reached.
    """
    url = f"{_WEB_HOST}/{target.owner}/{target.repo}/info/refs?service=git-upload-pack"
    try:
        with urllib.request.urlopen(_request(url, token), timeout=30) as response:
            return cast("bytes", response.read())
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 404):
            raise GitHubError(
                f"Repository '{target.slug}' was not found. It may not exist, "
                "or it may be private (set GITHUB_TOKEN to access private repositories)"
            ) from exc
        raise GitHubError(
            f"Could not reach GitHub for '{target.slug}' (HTTP {exc.code})."
        ) from exc
    except OSError as exc:
        raise GitHubError(f"Could not reach GitHub for '{target.slug}': {exc}") from exc


def _iter_pkt_lines(payload: bytes) -> Iterator[bytes]:
    """Yield the content of each pkt-line in a Git smart-HTTP *payload*.

    The advertisement is framed as pkt-lines: a 4-hex-digit length prefix (counting
    itself) followed by that many bytes of content, with ``0000`` acting as a flush
    marker. Malformed framing stops iteration rather than raising, since callers treat
    missing data as an unresolved ref.
    """
    i, n = 0, len(payload)
    while i + 4 <= n:
        try:
            length = int(payload[i : i + 4], 16)
        except ValueError:
            return
        if length == 0:
            i += 4
            continue
        if length < 4 or i + length > n:
            return
        yield payload[i + 4 : i + length]
        i += length


def _parse_advertised_refs(payload: bytes) -> dict[str, str]:
    """Parse an ``info/refs`` advertisement into a ``ref name -> commit SHA`` map.

    The returned mapping includes ``HEAD``, every ``refs/heads/*`` branch and every
    ``refs/tags/*`` tag. Annotated tags are advertised both as the tag object
    (``refs/tags/x``) and as the commit they dereference to (``refs/tags/x^{}``); the
    peeled commit is preferred so that a tag always maps to a commit.

    Args:
        payload: The raw advertisement bytes.

    Returns:
        A mapping from ref name to lowercase 40-character commit SHA.
    """
    refs: dict[str, str] = {}
    peeled: dict[str, str] = {}
    for content in _iter_pkt_lines(payload):
        line = content.split(b"\x00", 1)[0].strip(b"\n")
        parts = line.split(b" ", 1)
        if len(parts) != 2 or len(parts[0]) != 40:
            continue
        try:
            sha = parts[0].decode("ascii").lower()
        except UnicodeDecodeError:
            continue
        name = parts[1].decode("utf-8", "replace")
        if name.endswith("^{}"):
            peeled[name[:-3]] = sha
        else:
            refs[name] = sha
    refs.update(peeled)
    return refs


def resolve_default_branch(target: GitHubTarget, token: str | None = None) -> str:
    """Resolve a repository's default branch without using the REST API.

    Reads the symbolic ``HEAD`` reference from the repository's Git smart-HTTP
    ``info/refs`` advertisement, which is not subject to the REST API's unauthenticated
    rate limit.

    Args:
        target: The repository whose default branch is wanted.
        token: Optional GitHub token for private repositories.

    Returns:
        The default branch name (e.g. ``"main"``).

    Raises:
        GitHubError: If the repository is missing or private without a valid token, or
            if the default branch cannot be determined.
    """
    payload = _fetch_refs_advertisement(target, token)
    match = re.search(rb"symref=HEAD:refs/heads/([^\x00 \n]+)", payload)
    if not match:
        raise GitHubError(
            f"Could not determine the default branch for '{target.slug}'."
        )
    return match.group(1).decode("utf-8", "replace")


_SHA_RE = re.compile(r"[0-9a-fA-F]{7,40}")


def resolve_commit_shas(
    target: GitHubTarget,
    refs: list[str | None],
    token: str | None = None,
) -> list[str | None]:
    """Resolve each ref in *refs* to a commit SHA using one advertisement fetch.

    A single ``info/refs`` request serves every ref, however many are resolved on the
    same repository. Each entry is resolved as follows:

    * ``None`` resolves to the commit the default branch (``HEAD``) points at.
    * A branch or tag name resolves to its tip commit; annotated tags resolve to the
      commit they dereference to.
    * A value that is not an advertised ref but looks like a commit SHA (7-40 hex
      characters) is returned as-is, lowercased. This supports explicit commit pins.
    * Anything else resolves to ``None``.

    Args:
        target: The repository to resolve against.
        refs: The refs to resolve, in order. ``None`` means the default branch.
        token: Optional GitHub token for private repositories.

    Returns:
        A list the same length as *refs*, each a lowercase commit SHA or ``None`` when
        the ref could not be resolved.

    Raises:
        GitHubError: If the repository is missing, private, or unreachable.
    """
    advertised = _parse_advertised_refs(_fetch_refs_advertisement(target, token))
    resolved: list[str | None] = []
    for ref in refs:
        if ref is None:
            resolved.append(advertised.get("HEAD"))
            continue
        sha = (
            advertised.get(f"refs/heads/{ref}")
            or advertised.get(f"refs/tags/{ref}")
            or advertised.get(ref)
        )
        if sha is None and _SHA_RE.fullmatch(ref):
            sha = ref.lower()
        resolved.append(sha)
    return resolved


def commit_shas_equal(sha1: str | None, sha2: str | None) -> bool:
    """Return whether two commit SHAs identify the same commit.

    Handles abbreviated SHAs (as short as 7 characters, Git's conventional minimum) by
    treating one as a match for the other when it is a case-insensitive prefix. ``None``
    never matches.

    Args:
        sha1: The first commit SHA, or ``None``.
        sha2: The second commit SHA, or ``None``.

    Returns:
        ``True`` if both are non-``None`` and identify the same commit.
    """
    if sha1 is None or sha2 is None:
        return False
    a, b = sha1.lower(), sha2.lower()
    if a == b:
        return True
    shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
    return len(shorter) >= 7 and longer.startswith(shorter)


def same_github_target(
    target1: GitHubTarget,
    target2: GitHubTarget,
    token: str | None = None,
) -> bool:
    """Return whether two GitHub targets refer to the same scanned tree.

    Owner and repository names are compared case-insensitively because GitHub treats
    them that way, while the subpath is compared case-sensitively because file paths are
    case-sensitive.

    When both sides pin the same ref (or neither does, so both use the default branch),
    no network access is needed. Otherwise the two refs are resolved to the commits they
    point at and compared, so that distinct refs that name the same commit — a branch
    and a tag on the same tip, a branch and the default branch, or a branch and an
    explicit commit SHA — are recognized as the same. If either ref cannot be resolved
    (repository missing, private, unreachable, or the ref does not exist), the targets
    are treated as *not* the same so the normal comparison flow can surface the real
    error rather than a misleading "compare with itself" message.

    Subpaths are compared as given. A subpath that names a file is only resolved to its
    containing directory by
    [`checkout_repository`][recursivist.github.checkout_repository], so two URLs for
    different files in one directory are recognized as the same tree only when the
    targets passed here are the checked-out ones (`RepoCheckout.target`).

    Args:
        target1: The first GitHub target.
        target2: The second GitHub target.
        token: Optional GitHub token used for the ref lookups.

    Returns:
        ``True`` if both targets resolve to the same repository, commit and subtree,
        else ``False``.
    """
    if (
        target1.owner.lower() != target2.owner.lower()
        or target1.repo.lower() != target2.repo.lower()
        or target1.subpath != target2.subpath
    ):
        return False
    if target1.ref == target2.ref:
        return True
    try:
        sha1, sha2 = resolve_commit_shas(target1, [target1.ref, target2.ref], token)
    except GitHubError:
        return False
    return commit_shas_equal(sha1, sha2)


def _download_archive(
    target: GitHubTarget, ref: str, token: str | None, dest: str
) -> None:
    """Download the ``tar.gz`` source archive for *ref* to the file *dest*."""
    quoted_ref = urllib.parse.quote(ref, safe="/")
    url = f"{_ARCHIVE_HOST}/{target.owner}/{target.repo}/tar.gz/{quoted_ref}"
    try:
        with (
            urllib.request.urlopen(_request(url, token), timeout=120) as response,
            open(dest, "wb") as fh,
        ):
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


def _warn_skipped_link(member: tarfile.TarInfo) -> None:
    """Warn that the link *member* is left out of the extraction."""
    logger.warning(
        "Skipping link '%s': its target '%s' lies outside the repository",
        member.name.partition("/")[2] or member.name,
        member.linkname,
    )


def _skip_unsafe_links(
    member: tarfile.TarInfo, dest_path: str
) -> tarfile.TarInfo | None:
    """Tar extraction filter: the ``data`` filter, with unsafe links skipped.

    A repository may legitimately track a symlink with an absolute target, or a
    relative one that climbs out of the repository. Such a member is left out of the
    extraction, and a warning names it. Any other member that the ``data`` filter
    rejects raises, which fails the extraction.
    """
    try:
        return tarfile.data_filter(member, dest_path)
    except (tarfile.AbsoluteLinkError, tarfile.LinkOutsideDestinationError):
        _warn_skipped_link(member)
        return None


def _safe_extract(archive_path: str, dest_dir: str) -> None:
    """Extract *archive_path* into *dest_dir*, rejecting path traversal.

    Uses the tar ``data`` extraction filter when available (Python 3.12+) and otherwise
    validates every member manually so that entries with absolute paths or ``..``
    components cannot escape the destination directory. A link whose target lies
    outside *dest_dir* is skipped with a warning, and the remaining members are
    extracted. Any extraction failure is surfaced as a
    [`GitHubError`][recursivist.github.GitHubError].
    """
    try:
        with tarfile.open(archive_path, mode="r:gz") as tar:
            if hasattr(tarfile, "data_filter"):
                tar.extractall(dest_dir, filter=_skip_unsafe_links)
                return
            members = []
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
                        _warn_skipped_link(member)
                        continue
                members.append(member)
            tar.extractall(dest_dir, members=members)
    except tarfile.TarError as exc:
        raise GitHubError(f"Could not extract repository archive: {exc}") from exc


def _locate_root(extract_dir: str, target: GitHubTarget) -> tuple[str, str]:
    """Return the directory to scan within a freshly extracted archive.

    GitHub archives contain a single top-level directory (``<repo>-<ref>``); this
    returns that directory, descending into `GitHubTarget.subpath` when one was
    requested. A subpath that names a file rather than a directory — as in the
    ``/blob/<ref>/<file>`` URL of a GitHub file page — resolves to the directory that
    contains the file.

    Returns:
        A ``(directory, subpath)`` tuple: the absolute path of the directory to scan,
        and that directory's forward-slashed path within the repository (``""`` for the
        repository root). The subpath differs from `GitHubTarget.subpath` only when the
        latter named a file.

    Raises:
        GitHubError: If the archive layout is unexpected or the requested subpath does
            not exist.
    """
    entries = os.listdir(extract_dir)
    if len(entries) != 1:
        raise GitHubError(f"Unexpected archive layout for '{target.slug}'.")
    root = os.path.join(extract_dir, entries[0])
    if not target.subpath:
        return root, ""
    candidate = os.path.join(root, target.subpath.replace("/", os.sep))
    if _is_within(root, candidate):
        if os.path.isdir(candidate):
            return candidate, target.subpath
        if os.path.isfile(candidate):
            return os.path.dirname(candidate), posixpath.dirname(target.subpath)
    raise GitHubError(f"Path '{target.subpath}' was not found in '{target.slug}'.")


@contextmanager
def checkout_repository(
    target: GitHubTarget, token: str | None = None
) -> Generator[RepoCheckout]:
    """Download and extract a GitHub repository into a temporary directory.

    Resolves the ref (using the default branch when the target does not pin one),
    downloads the source archive, and safely extracts it. The extracted files are
    removed when the context exits.

    When the target's subpath names a file rather than a directory, the directory
    containing that file is checked out instead, and the yielded checkout's ``target``
    carries that directory as its subpath.

    Args:
        target: The repository (and optional subtree) to check out.
        token: Optional GitHub token; defaults to
            [`get_github_token`][recursivist.github.get_github_token].

    Yields:
        A [`RepoCheckout`][recursivist.github.RepoCheckout] describing the local
        extraction.

    Raises:
        GitHubError: If the repository cannot be resolved, downloaded, or extracted, or
            the requested subpath does not exist in it.
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
        local_root, subpath = _locate_root(extract_dir, target)
        if subpath != target.subpath:
            logger.info(
                "'%s' is a file in '%s'; scanning its containing directory instead",
                target.subpath,
                target.slug,
            )
            target = replace(target, subpath=subpath)
        yield RepoCheckout(
            target=target,
            local_root=local_root,
            ref=ref,
            root_name=target.display_name,
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def apply_github_urls(structure: Directory, checkout: RepoCheckout) -> Directory:
    """Rewrite each file's display path to its GitHub blob URL, in place.

    Used when ``--full-path`` is requested for a GitHub input: it walks *structure* and
    replaces every [`FileEntry`][recursivist._models.FileEntry] ``path`` with the file's
    canonical blob URL, so the renderers and exporters display GitHub URLs instead of
    temporary filesystem paths.

    Args:
        structure: A scanned structure produced by
            [`recursivist.scanner.get_directory_structure`][recursivist.scanner.get_directory_structure]
            for the checkout's `RepoCheckout.local_root`.
        checkout: The checkout the structure was scanned from, supplying the owner,
            repo, ref, and subpath used to build URLs.

    Returns:
        The same *structure* object, with file paths rewritten.
    """
    target = checkout.target
    base_prefix = target.subpath.strip("/")

    def _walk(node: Directory, rel_dir: str) -> None:
        rewritten: list[FileEntry] = []
        for entry in node.files:
            rel_file = f"{rel_dir}/{entry.name}" if rel_dir else entry.name
            url = target.blob_url(checkout.ref, rel_file)
            rewritten.append(entry._replace(path=url))
        node.files = rewritten
        for name, content in node.subdirectories.items():
            next_dir = f"{rel_dir}/{name}" if rel_dir else name
            _walk(content, next_dir)

    _walk(structure, base_prefix)
    return structure
