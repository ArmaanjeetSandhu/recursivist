"""File ordering.

Sorts a directory's files by extension/name, by a numeric metric (LOC, size,
mtime), or groups them by name similarity. Operates on :class:`FileEntry`.
"""

import os
from collections.abc import Sequence
from difflib import SequenceMatcher
from typing import Any

from recursivist._models import FileEntry


def sort_files_by_similarity(files: Sequence[Any]) -> list[FileEntry]:
    """Order files so that similarly named files sit next to each other.

    Unlike the LOC/size/mtime metrics, name similarity is *relational*: it
    depends on how a file's name compares to the others rather than on any
    single measured value, so it cannot be expressed as a ``sorted`` key.
    Instead this builds a greedy nearest-neighbour chain:

    1. Entries are seeded in case-insensitive name order and the
       alphabetically-first name becomes the start of the chain. Using a
       fixed, name-derived anchor makes the result deterministic and stable
       across runs (the same directory always yields the same order).
    2. Repeatedly, the not-yet-placed entry whose name is most similar to the
       most recently placed name is appended. Similarity is the
       :class:`difflib.SequenceMatcher` ratio computed case-insensitively on
       the full filename (extension included), so ``main.py``/``main.js`` and
       ``test_api.py``/``test_api.js`` naturally cluster.
    3. Ratio ties are broken by case-insensitive name order: because the
       candidates are kept alphabetically sorted and the best match is only
       replaced on a strictly greater ratio, the alphabetically-first of any
       tied group wins.

    This is a heuristic (locally greedy) ordering rather than a globally
    optimal grouping, which is the appropriate trade-off for a directory
    listing: each directory holds relatively few files, so the ``O(n^2)``
    pairwise comparisons are cheap, and the result reliably places obvious
    name-siblings adjacent to one another.

    Inputs may be :class:`FileEntry` instances, bare filename strings, or
    positional tuples; every item is normalised to a :class:`FileEntry` via
    :meth:`FileEntry.from_raw` before ordering. Since only the name is used,
    no metric flags are needed.

    Args:
        files: List of file items (``FileEntry``, tuple, or ``str``).

    Returns:
        Reordered list of :class:`FileEntry` with name-similar files adjacent.
    """
    if not files:
        return []
    entries = [FileEntry.from_raw(f) for f in files]
    if len(entries) < 2:
        return entries
    remaining = sorted(entries, key=lambda e: e.name.lower())
    ordered: list[FileEntry] = [remaining.pop(0)]
    matcher = SequenceMatcher(autojunk=False)
    while remaining:
        matcher.set_seq2(ordered[-1].name.lower())
        best_idx = 0
        best_ratio = -1.0
        for idx, candidate in enumerate(remaining):
            matcher.set_seq1(candidate.name.lower())
            ratio = matcher.ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_idx = idx
        ordered.append(remaining.pop(best_idx))
    return ordered


def sort_files_by_type(
    files: Sequence[Any],
    sort_by_loc: bool = False,
    sort_by_size: bool = False,
    sort_by_mtime: bool = False,
    sort_by_similarity: bool = False,
) -> list[FileEntry]:
    """Sort files by extension and then by name, or by LOC/size/mtime/similarity if requested.

    The sort precedence follows: LOC > size > mtime > similarity >
    extension/name. The numeric metrics are mutually combinable and take
    priority; name-similarity grouping replaces the default extension/name
    ordering when requested but is itself overridden by any active numeric
    sort (a value-based ordering is treated as the stronger intent, exactly
    as it already overrides the plain alphabetical fallback).

    Inputs may be :class:`FileEntry` instances, bare filename strings, or
    positional tuples; every item is normalised to a :class:`FileEntry` via
    :meth:`FileEntry.from_raw` before sorting.

    Args:
        files: List of file items (``FileEntry``, tuple, or ``str``).
        sort_by_loc: Whether to sort by lines of code.
        sort_by_size: Whether to sort by file size.
        sort_by_mtime: Whether to sort by modification time.
        sort_by_similarity: Whether to group files by name similarity (used
            only when no numeric sort is active).

    Returns:
        Sorted list of :class:`FileEntry`.
    """
    if not files:
        return []

    has_loc = any(isinstance(item, tuple) and len(item) > 2 for item in files)
    has_size = any(isinstance(item, tuple) and len(item) > 3 for item in files)
    has_mtime = any(isinstance(item, tuple) and len(item) > 4 for item in files)
    has_simple_size = sort_by_size and not sort_by_loc and has_loc
    has_simple_mtime = (
        sort_by_mtime and not sort_by_loc and not sort_by_size and (has_loc or has_size)
    )

    entries = [
        FileEntry.from_raw(f, sort_by_loc, sort_by_size, sort_by_mtime) for f in files
    ]

    if sort_by_loc and sort_by_size and sort_by_mtime and has_mtime:
        return sorted(entries, key=lambda e: (-e.loc, -e.size, -e.mtime))
    if sort_by_loc and sort_by_size and (has_size or has_simple_size) and has_loc:
        return sorted(entries, key=lambda e: (-e.loc, -e.size))
    if sort_by_loc and sort_by_mtime and has_mtime:
        return sorted(entries, key=lambda e: (-e.loc, -e.mtime))
    if sort_by_size and sort_by_mtime and has_mtime:
        return sorted(entries, key=lambda e: (-e.size, -e.mtime))
    if sort_by_loc and has_loc:
        return sorted(entries, key=lambda e: -e.loc)
    if sort_by_size and (has_size or has_simple_size):
        return sorted(entries, key=lambda e: -e.size)
    if sort_by_mtime and (has_mtime or has_simple_mtime):
        return sorted(entries, key=lambda e: -e.mtime)
    if sort_by_similarity:
        return sort_files_by_similarity(entries)
    return sorted(
        entries,
        key=lambda e: (os.path.splitext(e.name)[1].lower(), e.name.lower()),
    )
