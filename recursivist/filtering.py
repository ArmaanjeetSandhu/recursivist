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
    """Parse an ignore file (like .gitignore) and return patterns.

    Reads an ignore file and extracts patterns for excluding files and directories. Handles comments and trailing slashes in directories.

    Args:
        ignore_file_path: Path to the ignore file

    Returns:
        List of patterns to ignore
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
    """Convert patterns to compiled regex objects when appropriate.

    When is_regex is True, compiles string patterns into regex pattern objects for efficient matching. For invalid regex patterns, logs a warning and keeps them as strings.

    Args:
        patterns: List of patterns to compile
        is_regex: Whether the patterns should be treated as regex (True) or glob patterns (False)

    Returns:
        List of patterns (strings for glob patterns or compiled regex objects)
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
    """Determine if a path should be excluded based on filtering rules.

    Logic to handle priority between include and exclude patterns:
    1. If include_patterns exist and NONE match, EXCLUDE the path
    2. If exclude_patterns match, EXCLUDE the path (overrides include patterns)
    3. If file extension is in exclude_extensions, EXCLUDE the path
    4. If a matching include pattern exists, INCLUDE the path (overrides gitignore patterns)
    5. If gitignore-style patterns match, follow their rules (including negations)

    Args:
        path: Path to check for exclusion
        ignore_context: Dictionary with 'patterns' and 'current_dir' keys
        exclude_extensions: Set of file extensions to exclude
        exclude_patterns: List of patterns (glob or regex) to exclude
        include_patterns: List of patterns (glob or regex) to include (overrides gitignore exclusions)
    Returns:
        True if path should be excluded, False otherwise
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
