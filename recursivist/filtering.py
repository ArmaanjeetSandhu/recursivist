"""File and directory filtering: ignore files, glob/regex patterns, and gitignore-style
exclusion rules.

Provides the predicate [`should_exclude`][recursivist.filtering.should_exclude] used by
the scanner. Git-style ignore matching is delegated to `pathspec` (its gitignore
matcher), which implements the full gitignore specification: anchoring, ``**``
wildcards, directory-only (trailing ``/``) patterns, ``!`` negation with
last-match-wins, character classes, backslash escapes, and trailing-whitespace handling.
The glob and regex matching used by ``--exclude-pattern``/``--include-pattern`` is
unrelated and uses only the standard library.

Like Git, each ignore file is evaluated *relative to the directory that contains it*
rather than relative to the scan root. The active ignore files are kept as a stack
(shallowest first); a path is tested against every level with its own anchoring, and a
deeper file's verdict overrides a shallower one, so an anchored pattern such as
``/build`` in a nested ``.gitignore`` matches only within that subdirectory and does not
leak up to the scan root or down past the anchor.
"""

from __future__ import annotations

import fnmatch
import logging
import os
import re
from collections.abc import Iterable, Mapping, Sequence
from functools import cache
from re import Pattern
from typing import Any, cast

from pathspec import PathSpec
from pathspec.pattern import Pattern as IgnorePattern
from pathspec.util import lookup_pattern

logger = logging.getLogger(__name__)

try:
    _IGNORE_PATTERN_FACTORY = lookup_pattern("gitignore")
except LookupError:
    _IGNORE_PATTERN_FACTORY = lookup_pattern("gitwildmatch")


def parse_ignore_file(ignore_file_path: str) -> list[str]:
    """Read an ignore file and return its lines as gitignore patterns.

    Lines are returned verbatim with only their terminators removed, preserving order
    and every character that is significant to the gitignore grammar (comments, blank
    lines, backslash escapes, and escaped trailing whitespace). Interpretation is left
    entirely to the gitignore matcher, so callers must not strip or filter the returned
    lines.

    Args:
        ignore_file_path: Path to the ignore file (e.g. ``.gitignore``).

    Returns:
        The list of pattern lines, or an empty list when the file does not exist.
    """
    if not os.path.exists(ignore_file_path):
        return []
    with open(ignore_file_path, encoding="utf-8", errors="replace") as f:
        return f.read().splitlines()


def compile_regex_patterns(
    patterns: Sequence[str], is_regex: bool = False
) -> list[str | Pattern[str]]:
    """Compile patterns to regex objects when regex matching is requested.

    When *is_regex* is ``False`` the patterns are returned unchanged for glob matching.
    When ``True`` each pattern is compiled to a `re.Pattern`; any pattern that fails to
    compile is kept as a string and a warning is logged.

    Args:
        patterns: Patterns to process.
        is_regex: Whether to treat the patterns as regular expressions (``True``) or
            glob patterns (``False``).

    Returns:
        A list whose items are plain strings for glob patterns or compiled `re.Pattern`
        objects for successfully compiled regexes.
    """
    if not is_regex:
        return cast(list[str | Pattern[str]], patterns)
    compiled_patterns: list[str | Pattern[str]] = []
    for pattern in patterns:
        try:
            compiled_patterns.append(re.compile(pattern))
        except re.error as e:
            logger.warning(f"Invalid regex pattern '{pattern}': {e}")
            compiled_patterns.append(pattern)
    return compiled_patterns


@cache
def _build_ignore_spec(patterns: tuple[str, ...]) -> PathSpec[IgnorePattern]:
    """Compile gitignore pattern lines into a `PathSpec`.

    Uses pathspec's gitignore implementation, which follows the gitignore specification.
    The resulting spec is matched (by
    [`should_exclude`][recursivist.filtering.should_exclude]) against a path expressed
    relative to the directory of the ignore file the patterns came from, using forward
    slashes; `check_file` resolves ``!`` negation with last-match-wins within the file
    and reports whether any pattern matched.

    Patterns are compiled one at a time so a single malformed line (which pathspec
    rejects with a `ValueError`) is skipped with a warning rather than aborting the
    whole scan. Blank lines and comments compile to inert patterns and are harmless.
    Cached so each unique tuple of patterns is compiled only once per run.
    """
    compiled: list[IgnorePattern] = []
    for line in patterns:
        if not line:
            continue
        try:
            compiled.append(_IGNORE_PATTERN_FACTORY(line))
        except ValueError as exc:
            logger.warning("Ignoring invalid ignore pattern %r: %s", line, exc)
    return PathSpec(compiled)


def _resolve_ignore_levels(
    ignore_context: Mapping[str, Any],
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Return the active ignore levels as ``(base, patterns)`` pairs.

    Each pair is one ignore file: *base* is the file's directory relative to the scan
    root (``""`` for the root ignore file) and *patterns* are its verbatim pattern
    lines. Levels are ordered shallowest-first so a caller can let a deeper file's
    verdict override a shallower one, matching Git's precedence.

    The levels are read from the ``"pattern_stack"`` entry of *ignore_context*; a
    context without one carries no ignore rules.
    """
    stack = ignore_context.get("pattern_stack") or ()
    return tuple(
        (base, tuple(p for p in pats if isinstance(p, str))) for base, pats in stack
    )


def _is_ignored_by_stack(
    target: str, levels: tuple[tuple[str, tuple[str, ...]], ...]
) -> bool:
    """Apply a shallow-to-deep stack of ignore files to a single path.

    *target* is the path relative to the scan root, forward-slashed and with a trailing
    ``/`` when it is a directory. Each level is matched relative to its own *base*
    directory (levels whose base does not contain *target* are skipped), and the last
    level that expresses an opinion wins. A level's opinion is tri-state via
    `check_file`: matched by an ignore pattern, re-included by a ``!`` negation, or
    silent, so a deeper file that says nothing leaves a shallower verdict intact,
    exactly as Git resolves precedence between nested ``.gitignore`` files.
    """
    decision: bool | None = None
    for base, patterns in levels:
        if not patterns:
            continue
        base = base.replace("\\", "/").strip("/")
        if base:
            prefix = f"{base}/"
            if not target.startswith(prefix):
                continue
            rel = target[len(prefix) :]
        else:
            rel = target
        if not rel or rel == "/":
            continue
        verdict = _build_ignore_spec(patterns).check_file(rel).include
        if verdict is not None:
            decision = verdict
    return decision is True


def _pattern_matches(pattern: str | Pattern[str], name: str) -> bool:
    """Return whether a single ``--exclude-pattern``/``--include-pattern`` matches.

    Patterns are tested against an entry's *name* (its basename), never its path. A
    compiled regex matches when it is found anywhere in *name*; a glob matches when
    `fnmatch` accepts it. This is the single definition of pattern matching shared by
    [`should_exclude`][recursivist.filtering.should_exclude] and
    [`PatternMatchTracker`][recursivist.filtering.PatternMatchTracker], so the two can
    never disagree about what a pattern matches.
    """
    if isinstance(pattern, Pattern):
        return bool(pattern.search(name))
    return fnmatch.fnmatch(name, pattern)


def _describe_pattern(pattern: str | Pattern[str]) -> str:
    """Return the text the user typed for *pattern*, whether compiled or not."""
    return pattern.pattern if isinstance(pattern, Pattern) else pattern


class PatternMatchTracker:
    """Record which user-supplied filters matched at least one scanned entry.

    The scanner reports every directory entry it lists to
    [`observe`][recursivist.filtering.PatternMatchTracker.observe] *before* applying the
    exclusion rules, so a filter counts as matched even when an earlier rule already
    removed the entry. Once a filter has matched it is dropped from the pending set, and
    once nothing is pending observation is a no-op, so the bookkeeping costs nothing on
    a scan where every filter is used.

    Matching mirrors the scanner exactly: ``--exclude`` names are compared with the
    entry name, ``--exclude-ext`` applies to files only, ``--exclude-pattern`` applies
    to files and directories, and ``--include-pattern`` applies to files only.

    Entries the scanner never lists — the contents of excluded or ignored directories,
    and anything below ``--depth`` — are not observed, so a filter reported as
    unmatched matched nothing *among the scanned entries*.

    Args:
        exclude_dirs: Names given to ``--exclude``.
        exclude_extensions: Normalized extensions given to ``--exclude-ext``.
        exclude_patterns: Patterns given to ``--exclude-pattern``.
        include_patterns: Patterns given to ``--include-pattern``.
    """

    def __init__(
        self,
        exclude_dirs: Sequence[str] | None = None,
        exclude_extensions: Iterable[str] | None = None,
        exclude_patterns: Sequence[str | Pattern[str]] | None = None,
        include_patterns: Sequence[str | Pattern[str]] | None = None,
    ) -> None:
        self._dirs: dict[str, None] = dict.fromkeys(exclude_dirs or ())
        self._exts: dict[str, None] = dict.fromkeys(exclude_extensions or ())
        self._exclude: list[str | Pattern[str]] = list(
            dict.fromkeys(exclude_patterns or ())
        )
        self._include: list[str | Pattern[str]] = list(
            dict.fromkeys(include_patterns or ())
        )
        self.depth_limited = False

    @property
    def pending(self) -> bool:
        """Whether any filter has not matched an entry yet."""
        return bool(self._dirs or self._exts or self._exclude or self._include)

    def observe(self, path: str, is_dir: bool) -> None:
        """Mark every pending filter that matches the entry at *path* as used.

        Args:
            path: Filesystem path of a directory entry the scanner listed.
            is_dir: Whether *path* is a directory.
        """
        if not self.pending:
            return
        name = os.path.basename(path)
        self._dirs.pop(name, None)
        if not is_dir and self._exts:
            self._exts.pop(os.path.splitext(name)[1].lower(), None)
        if self._exclude:
            self._exclude = [p for p in self._exclude if not _pattern_matches(p, name)]
        if not is_dir and self._include:
            self._include = [p for p in self._include if not _pattern_matches(p, name)]

    def unmatched(self) -> list[tuple[str, str]]:
        """Return ``(flag, value)`` pairs for every filter that matched nothing."""
        return [
            *(("--exclude", d) for d in self._dirs),
            *(("--exclude-ext", e) for e in self._exts),
            *(("--exclude-pattern", _describe_pattern(p)) for p in self._exclude),
            *(("--include-pattern", _describe_pattern(p)) for p in self._include),
        ]

    def report(self, where: str = "") -> None:
        """Log a warning for each filter that matched nothing.

        Args:
            where: Optional phrase naming what was scanned (e.g. ``"in either
                directory"``), appended to each message.
        """
        suffix = f" {where}" if where else ""
        if self.depth_limited:
            suffix += " within the scanned depth"
        for flag, value in self.unmatched():
            logger.warning(f"No files or directories matched {flag} '{value}'{suffix}")


def should_exclude(
    path: str,
    ignore_context: dict[str, Any],
    exclude_extensions: set[str] | None = None,
    exclude_patterns: Sequence[str | Pattern[str]] | None = None,
    include_patterns: Sequence[str | Pattern[str]] | None = None,
    *,
    is_dir: bool | None = None,
) -> bool:
    """Decide whether a path should be excluded from the scan.

    The filtering rules are applied in priority order:

    1. If *include_patterns* are given and none match a file, exclude it.
    2. If any *exclude_patterns* match, exclude the path (this overrides include
       patterns).
    3. If a non-directory's extension is in *exclude_extensions*, exclude it.
    4. If an include pattern matched a file, include it (this overrides the
       gitignore-style patterns below). Directories are never tested against include
       patterns, so they always fall through to the ignore rules.
    5. Otherwise apply the gitignore-style rules from *ignore_context* via `pathspec`,
       honoring anchoring, ``**`` wildcards, directory-only (trailing ``/``) patterns,
       ``!`` negation, character classes and escapes per the gitignore specification.
       Each ignore file in the stack is matched relative to its own directory and deeper
       files override shallower ones, so a nested file's anchored patterns stay scoped
       to its subtree.

    Args:
        path: Filesystem path to test.
        ignore_context: Mapping describing the active ignore rules. Recognized keys are
            ``"pattern_stack"`` (a shallowest-first sequence of
            ``(base_dir_relative_to_root, patterns)`` pairs, one per ignore file; a
            single ignore file at the scan root is ``[("", patterns)]``) and
            ``"rel_dir"`` (the current directory's path relative to the scan root).
        exclude_extensions: Lowercase, dot-prefixed extensions to exclude.
        exclude_patterns: Glob or compiled-regex patterns to exclude, matched against
            the entry's name.
        include_patterns: Glob or compiled-regex patterns to include, matched against
            the entry's name, which override the gitignore-style exclusions.
        is_dir: Whether *path* is a directory, when the caller already knows. Left as
            ``None``, it is looked up with `os.path.isdir`.

    Returns:
        ``True`` if the path should be excluded, ``False`` otherwise.
    """
    basename = os.path.basename(path)
    if is_dir is None:
        is_dir = os.path.isdir(path)
    if (
        include_patterns
        and not is_dir
        and not any(_pattern_matches(pattern, basename) for pattern in include_patterns)
    ):
        return True
    if exclude_patterns and any(
        _pattern_matches(pattern, basename) for pattern in exclude_patterns
    ):
        return True
    if (
        exclude_extensions
        and not is_dir
        and os.path.splitext(basename)[1].lower() in exclude_extensions
    ):
        return True
    if include_patterns and not is_dir:
        return False
    levels = _resolve_ignore_levels(ignore_context)
    if not levels:
        return False
    rel_dir = ignore_context.get("rel_dir", "")
    target = (f"{rel_dir}/{basename}" if rel_dir else basename).replace("\\", "/")
    target = target.lstrip("/")
    if is_dir:
        target += "/"
    return _is_ignored_by_stack(target, levels)
