"""File ordering.

Sorts a directory's files by extension/name, by a numeric metric (LOC, size,
mtime), or groups them by name similarity. Operates on :class:`FileEntry`.
"""

import os
from collections.abc import Mapping, Sequence
from difflib import SequenceMatcher
from typing import Any

from recursivist._models import FileEntry
from recursivist.flags import (
    METRIC_GIT,
    METRIC_LOC,
    METRIC_MTIME,
    METRIC_SIMILARITY,
    METRIC_SIZE,
)

_GIT_SORT_RANK: dict[str, int] = {"M": 0, "A": 1, "D": 2, "U": 3}
_GIT_SORT_CLEAN = 4


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
    :meth:`FileEntry.coerce` before ordering. Since only the name is used, the
    metric slots do not affect the result.

    Args:
        files: List of file items (``FileEntry``, tuple, or ``str``).

    Returns:
        Reordered list of :class:`FileEntry` with name-similar files adjacent.
    """
    if not files:
        return []
    entries = [FileEntry.coerce(f) for f in files]
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
    sort_key: str | None = None,
    git_markers: Mapping[str, str] | None = None,
) -> list[FileEntry]:
    """Order files by a single resolved sort key.

    Exactly one ordering is applied, chosen by *sort_key*:

    - ``None``: the default — by extension, then case-insensitive name.
    - ``"loc"`` / ``"size"`` / ``"mtime"``: by that metric, largest/newest
      first (a stable sort keeps the pre-existing order for equal values).
    - ``"git_status"``: grouped by Git status (modified, added, deleted,
      untracked, then clean), and by case-insensitive name within each group.
      Requires *git_markers*.
    - ``"similarity"``: by name similarity, via
      :func:`sort_files_by_similarity`.

    This mirrors the resolution in :mod:`recursivist.flags`, where only the
    first sorting flag on the command line takes effect, so there is never more
    than one active metric to combine.

    Inputs may be :class:`FileEntry` instances, bare filename strings, or
    positional tuples; every item is normalised to a :class:`FileEntry` via
    :meth:`FileEntry.coerce` before sorting.

    Args:
        files: List of file items (``FileEntry``, tuple, or ``str``).
        sort_key: The single metric to order by, or ``None`` for the default.
        git_markers: ``{filename: status_char}`` mapping, required when
            *sort_key* is ``"git_status"``.

    Returns:
        Sorted list of :class:`FileEntry`.
    """
    if not files:
        return []

    entries = [FileEntry.coerce(f) for f in files]

    if sort_key == METRIC_LOC:
        return sorted(entries, key=lambda e: -e.loc)
    if sort_key == METRIC_SIZE:
        return sorted(entries, key=lambda e: -e.size)
    if sort_key == METRIC_MTIME:
        return sorted(entries, key=lambda e: -e.mtime)
    if sort_key == METRIC_GIT:
        markers = git_markers or {}
        return sorted(
            entries,
            key=lambda e: (
                _GIT_SORT_RANK.get(markers.get(e.name, ""), _GIT_SORT_CLEAN),
                e.name.lower(),
            ),
        )
    if sort_key == METRIC_SIMILARITY:
        return sort_files_by_similarity(entries)
    return sorted(
        entries,
        key=lambda e: (os.path.splitext(e.name)[1].lower(), e.name.lower()),
    )
