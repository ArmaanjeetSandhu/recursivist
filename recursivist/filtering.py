"""File and directory filtering: ignore files, glob/regex patterns, and
gitignore-style exclusion rules.

Provides the predicate :func:`should_exclude` used by the scanner. Git-style
ignore matching is delegated to :mod:`pathspec` (its gitignore matcher),
which implements the full gitignore specification: anchoring, ``**`` wildcards,
directory-only (trailing ``/``) patterns, ``!`` negation with last-match-wins,
character classes, backslash escapes, and trailing-whitespace handling. The glob
and regex matching used by ``--exclude-pattern``/``--include-pattern`` is
unrelated and remains pure standard library.
"""

from __future__ import annotations

import fnmatch
import logging
import os
import re
from collections.abc import Sequence
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
    specification. The resulting spec is matched against a path expressed
    relative to the scan root using forward slashes;
    :meth:`~pathspec.PathSpec.match_file` already resolves ``!`` negation with
    last-match-wins.

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
    5. Otherwise apply the gitignore-style patterns from *ignore_context* via
       :mod:`pathspec`, honoring anchoring, ``**`` wildcards, directory-only
       (trailing ``/``) patterns, ``!`` negation, character classes and escapes
       per the gitignore specification.

    Args:
        path: Filesystem path to test.
        ignore_context: Mapping describing the active ignore rules. Recognized
            keys are ``"patterns"`` (gitignore-style patterns), ``"current_dir"``
            (directory the patterns are relative to), and ``"rel_dir"`` (the
            current directory's path relative to the scan root).
        exclude_extensions: Lowercase, dot-prefixed extensions to exclude.
        exclude_patterns: Glob or compiled-regex patterns to exclude.
        include_patterns: Glob or compiled-regex patterns to include, which
            override the gitignore-style exclusions.

    Returns:
        ``True`` if the path should be excluded, ``False`` otherwise.
    """
    patterns = ignore_context.get("patterns", [])
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
    if not patterns:
        return False
    rel_dir = ignore_context.get("rel_dir", "")
    rel_to_root = (f"{rel_dir}/{basename}" if rel_dir else basename).replace("\\", "/")
    rel_to_root = rel_to_root.lstrip("/")
    spec = _build_ignore_spec(tuple(p for p in patterns if isinstance(p, str)))
    if os.path.isdir(path):
        rel_to_root += "/"
    return spec.match_file(rel_to_root)
