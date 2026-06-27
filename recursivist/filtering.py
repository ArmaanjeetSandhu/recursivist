"""File and directory filtering: ignore files, glob/regex patterns, and
gitignore-style exclusion rules.

Provides the predicate :func:`should_exclude` used by the scanner, plus the
gitignore glob-to-regex translation that backs it. Pure standard library; no
dependency on the rest of the package.
"""

import fnmatch
import logging
import os
import re
from collections.abc import Sequence
from functools import cache
from re import Pattern
from typing import Any, cast

logger = logging.getLogger(__name__)


def parse_ignore_file(ignore_file_path: str) -> list[str]:
    """Read an ignore file and return its patterns.

    Blank lines and ``#`` comment lines are skipped; every other line is
    returned stripped of surrounding whitespace, preserving the order in
    which the patterns appear.

    Args:
        ignore_file_path: Path to the ignore file (e.g. ``.gitignore``).

    Returns:
        The list of pattern strings, or an empty list when the file does not
        exist.
    """
    if not os.path.exists(ignore_file_path):
        return []
    patterns = []
    with open(ignore_file_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.append(line)
    return patterns


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


def _gitignore_glob_to_regex(glob: str, anchored: bool) -> str:
    """Translate a gitignore glob (no leading '!'/'/' and no trailing '/') into
    a regex for a forward-slash path.

    '*' matches anything but '/', '**' crosses '/', '?' is one non-'/' char, and
    '[...]' is a character class. Anchored patterns must match from the start of
    the path; floating patterns may match at any directory depth.
    """
    i, n = 0, len(glob)
    out: list[str] = []
    while i < n:
        c = glob[i]
        if c == "*":
            star = 0
            while i < n and glob[i] == "*":
                star += 1
                i += 1
            if star >= 2:
                if i < n and glob[i] == "/":
                    out.append("(?:.*/)?")
                    i += 1
                else:
                    out.append(".*")
            else:
                out.append("[^/]*")
        elif c == "?":
            out.append("[^/]")
            i += 1
        elif c == "[":
            j = i + 1
            if j < n and glob[j] in ("!", "^"):
                j += 1
            if j < n and glob[j] == "]":
                j += 1
            while j < n and glob[j] != "]":
                j += 1
            if j >= n:
                out.append(re.escape("["))
                i += 1
            else:
                cls = glob[i + 1 : j]
                if cls.startswith("!"):
                    cls = "^" + cls[1:]
                out.append("[" + cls + "]")
                i = j + 1
        elif c == "/":
            out.append("/")
            i += 1
        else:
            out.append(re.escape(c))
            i += 1
    body = "".join(out)
    prefix = r"\A" if anchored else r"(?:\A|.*/)"
    return prefix + body + r"(?:/|\Z)"


@cache
def _compile_ignore_pattern(body: str) -> tuple[Pattern[str], bool] | None:
    """Compile a gitignore pattern body (the part after any leading '!').

    Returns ``(regex, dir_only)`` or ``None`` for an empty pattern. The regex is
    searched against a path relative to the ignore file's directory, expressed
    with forward slashes and no leading slash. ``dir_only`` patterns (trailing
    '/') match directories only. Cached so each unique pattern compiles once.
    """
    if body.startswith(("\\#", "\\!")):
        body = body[1:]
    dir_only = body.endswith("/")
    if dir_only:
        body = body[:-1]
    anchored = "/" in body
    if body.startswith("/"):
        body = body[1:]
    if not body:
        return None
    try:
        return re.compile(_gitignore_glob_to_regex(body, anchored)), dir_only
    except re.error:
        return None


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
    5. Otherwise apply the gitignore-style patterns from *ignore_context*,
       honoring negations (``!``) and directory-only (trailing ``/``) rules.

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
    is_dir = os.path.isdir(path)
    excluded = False
    for pattern in patterns:
        if not isinstance(pattern, str) or not pattern:
            continue
        negated = pattern.startswith("!")
        compiled = _compile_ignore_pattern(pattern[1:] if negated else pattern)
        if compiled is None:
            continue
        regex, dir_only = compiled
        if dir_only and not is_dir:
            continue
        if regex.search(rel_to_root):
            excluded = not negated
    return excluded
