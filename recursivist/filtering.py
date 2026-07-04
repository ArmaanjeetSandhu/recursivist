"""File and directory filtering: ignore files, glob/regex patterns, and
gitignore-style exclusion rules.

Provides the predicate :func:`should_exclude` used by the scanner. Git-style
ignore matching is delegated to :mod:`pathspec` (its gitignore matcher),
which implements the full gitignore specification: anchoring, ``**`` wildcards,
directory-only (trailing ``/``) patterns, ``!`` negation with last-match-wins,
character classes, backslash escapes, and trailing-whitespace handling. The glob
and regex matching used by ``--exclude-pattern``/``--include-pattern`` is
unrelated and remains pure standard library.

Like Git, each ignore file is evaluated *relative to the directory that
contains it* rather than relative to the scan root. The active ignore files are
kept as a stack (shallowest first); a path is tested against every level with
its own anchoring, and a deeper file's verdict overrides a shallower one, so an
anchored pattern such as ``/build`` in a nested ``.gitignore`` matches only
within that subdirectory and does not leak up to the scan root or down past the
anchor.
"""

from __future__ import annotations

import fnmatch
import logging
import os
import re
from collections.abc import Mapping, Sequence
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

    Lines are returned verbatim with only their terminators removed, preserving
    order and every character that is significant to the gitignore grammar
    (comments, blank lines, backslash escapes, and escaped trailing
    whitespace). Interpretation is left entirely to the gitignore matcher, so
    callers must not strip or filter the returned lines.

    Args:
        ignore_file_path: Path to the ignore file (e.g. ``.gitignore``).

    Returns:
        The list of pattern lines, or an empty list when the file does not
        exist.
    """
    if not os.path.exists(ignore_file_path):
        return []
    with open(ignore_file_path, encoding="utf-8", errors="replace") as f:
        return f.read().splitlines()


def compile_regex_patterns(
    patterns: Sequence[str], is_regex: bool = False
) -> list[str | Pattern[str]]:
    """Compile patterns to regex objects when regex matching is requested.

    When *is_regex* is ``False`` the patterns are returned unchanged for glob
    matching. When ``True`` each pattern is compiled to a
    :class:`re.Pattern`; any pattern that fails to compile is kept as a string
    and a warning is logged.

    Args:
        patterns: Patterns to process.
        is_regex: Whether to treat the patterns as regular expressions
            (``True``) or glob patterns (``False``).

    Returns:
        A list whose items are plain strings for glob patterns or compiled
        :class:`re.Pattern` objects for successfully compiled regexes.
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
    """Compile gitignore pattern lines into a :class:`~pathspec.PathSpec`.

    Uses pathspec's gitignore implementation, which follows the gitignore
    specification. The resulting spec is matched (by :func:`should_exclude`)
    against a path expressed relative to the directory of the ignore file the
    patterns came from, using forward slashes;
    :meth:`~pathspec.PathSpec.check_file` resolves ``!`` negation with
    last-match-wins within the file and reports whether any pattern matched.

    Patterns are compiled one at a time so a single malformed line (which
    pathspec rejects with a :class:`ValueError`) is skipped with a warning
    rather than aborting the whole scan. Blank lines and comments compile to
    inert patterns and are harmless. Cached so each unique tuple of patterns is
    compiled only once per run.
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

    Each pair is one ignore file: *base* is the file's directory relative to the
    scan root (``""`` for the root ignore file) and *patterns* are its verbatim
    pattern lines. Levels are ordered shallowest-first so a caller can let a
    deeper file's verdict override a shallower one, matching Git's precedence.

    The explicit ``"pattern_stack"`` produced by the scanner is preferred. When
    it is absent the legacy flat ``"patterns"`` list is used and treated as a
    single ignore file rooted at the scan root.
    """
    stack = ignore_context.get("pattern_stack")
    if stack is not None:
        return tuple(
            (base, tuple(p for p in pats if isinstance(p, str))) for base, pats in stack
        )
    patterns = ignore_context.get("patterns", [])
    root_patterns = tuple(p for p in patterns if isinstance(p, str))
    return (("", root_patterns),) if root_patterns else ()


def _is_ignored_by_stack(
    target: str, levels: tuple[tuple[str, tuple[str, ...]], ...]
) -> bool:
    """Apply a shallow-to-deep stack of ignore files to a single path.

    *target* is the path relative to the scan root, forward-slashed and with a
    trailing ``/`` when it is a directory. Each level is matched relative to its
    own *base* directory (levels whose base does not contain *target* are
    skipped), and the last level that expresses an opinion wins. A level's
    opinion is tri-state via :meth:`~pathspec.PathSpec.check_file`: matched by an
    ignore pattern, re-included by a ``!`` negation, or silent -- so a deeper
    file that says nothing leaves a shallower verdict intact, exactly as Git
    resolves precedence between nested ``.gitignore`` files.
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


def should_exclude(
    path: str,
    ignore_context: dict[str, Any],
    exclude_extensions: set[str] | None = None,
    exclude_patterns: Sequence[str | Pattern[str]] | None = None,
    include_patterns: Sequence[str | Pattern[str]] | None = None,
) -> bool:
    """Decide whether a path should be excluded from the scan.

    The filtering rules are applied in priority order:

    1. If *include_patterns* are given and none match a file, exclude it.
    2. If any *exclude_patterns* match, exclude the path (this overrides
       include patterns).
    3. If the file's extension is in *exclude_extensions*, exclude it.
    4. If an include pattern matched, include the path (this overrides the
       gitignore-style patterns below).
    5. Otherwise apply the gitignore-style rules from *ignore_context* via
       :mod:`pathspec`, honoring anchoring, ``**`` wildcards, directory-only
       (trailing ``/``) patterns, ``!`` negation, character classes and escapes
       per the gitignore specification. Each ignore file in the stack is matched
       relative to its own directory and deeper files override shallower ones,
       so a nested file's anchored patterns stay scoped to its subtree.

    Args:
        path: Filesystem path to test.
        ignore_context: Mapping describing the active ignore rules. Recognized
            keys are ``"pattern_stack"`` (a shallowest-first sequence of
            ``(base_dir_relative_to_root, patterns)`` pairs, one per ignore
            file), ``"patterns"`` (a legacy flat pattern list, treated as a
            single ignore file at the scan root when ``"pattern_stack"`` is
            absent), ``"current_dir"`` (directory used to anchor the
            ``--exclude-pattern``/``--include-pattern`` globs), and ``"rel_dir"``
            (the current directory's path relative to the scan root).
        exclude_extensions: Lowercase, dot-prefixed extensions to exclude.
        exclude_patterns: Glob or compiled-regex patterns to exclude.
        include_patterns: Glob or compiled-regex patterns to include, which
            override the gitignore-style exclusions.

    Returns:
        ``True`` if the path should be excluded, ``False`` otherwise.
    """
    current_dir = ignore_context.get("current_dir", os.path.dirname(path))
    rel_path = os.path.relpath(path, current_dir)
    if os.name == "nt":
        rel_path = rel_path.replace("\\", "/")
    basename = os.path.basename(path)
    if include_patterns and not os.path.isdir(path):
        included = False
        for pattern in include_patterns:
            if isinstance(pattern, Pattern):
                if pattern.search(rel_path) or pattern.search(basename):
                    included = True
                    break
            else:
                if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(
                    basename, pattern
                ):
                    included = True
                    break
        if not included:
            return True
    if exclude_patterns:
        for pattern in exclude_patterns:
            if isinstance(pattern, Pattern):
                if pattern.search(rel_path) or pattern.search(basename):
                    return True
            else:
                if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(
                    basename, pattern
                ):
                    return True
    if exclude_extensions and os.path.isfile(path):
        _, ext = os.path.splitext(path)
        if ext.lower() in exclude_extensions:
            return True
    if include_patterns:
        return False
    levels = _resolve_ignore_levels(ignore_context)
    if not levels:
        return False
    rel_dir = ignore_context.get("rel_dir", "")
    target = (f"{rel_dir}/{basename}" if rel_dir else basename).replace("\\", "/")
    target = target.lstrip("/")
    if os.path.isdir(path):
        target += "/"
    return _is_ignored_by_stack(target, levels)
