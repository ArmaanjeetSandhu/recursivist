"""Shared data model for directory-structure entries.

This module defines :class:`FileEntry`, the fixed-shape representation of a
file stored under ``structure["_files"]``.

:class:`FileEntry` is a :class:`typing.NamedTuple`, so an entry can be used as
a plain tuple — ``entry[0]`` is the name and ``isinstance(entry, tuple)`` is
``True`` — as well as through attribute access (``entry.name``, ``entry.loc``).
"""

from typing import Any, NamedTuple, Union


class FileEntry(NamedTuple):
    """A single file within a scanned directory structure.

    Attributes:
        name: Bare filename (e.g. ``"main.py"``). Used for icon lookup,
            extension detection and Git-status lookup.
        path: The string to display for this file — an absolute, forward-slash
            path when full-path display is enabled, otherwise just ``name``.
        loc: Lines of code. Populated only when LOC counting is enabled during
            scanning; ``0`` otherwise.
        size: File size in bytes. Populated only when size tracking is enabled;
            ``0`` otherwise.
        mtime: Modification time (seconds since epoch). Populated only when
            mtime tracking is enabled; ``0.0`` otherwise.
    """

    name: str
    path: str
    loc: int = 0
    size: int = 0
    mtime: float = 0.0

    @classmethod
    def from_raw(
        cls,
        item: Union["FileEntry", tuple[Any, ...], str],
        sort_by_loc: bool = False,
        sort_by_size: bool = False,
        sort_by_mtime: bool = False,
    ) -> "FileEntry":
        """Build a :class:`FileEntry` from a raw ``_files`` entry.

        An entry may be a :class:`FileEntry`, a positional tuple, or a bare
        filename string. For tuples, the ``sort_by_*`` flags determine which
        positional slots carry which metric:

        - ``(name, path, loc, size, mtime)`` when LOC + size + mtime are on
        - ``(name, path, loc, size)`` when LOC + size are on
        - ``(name, path, loc, 0, mtime)`` when LOC + mtime are on
        - ``(name, path, 0, size, mtime)`` when size + mtime are on
        - ``(name, path, <metric>)`` for a single metric
        - ``(name, path)`` or a bare ``str`` when no metric is on

        A :class:`FileEntry` is returned unchanged, and a bare string becomes a
        name-only entry.

        Args:
            item: A :class:`FileEntry`, a positional tuple, or a bare filename
                string.
            sort_by_loc: Whether LOC is tracked for this entry.
            sort_by_size: Whether size is tracked for this entry.
            sort_by_mtime: Whether mtime is tracked for this entry.

        Returns:
            The equivalent :class:`FileEntry`.
        """
        if isinstance(item, cls):
            return item
        if not isinstance(item, tuple):
            name = str(item)
            return cls(name=name, path=name)

        n = len(item)
        if n == 0:
            return cls(name="unknown", path="unknown")
        name = item[0]
        path = item[1] if n > 1 else name

        loc = item[2] if (sort_by_loc and n > 2) else 0
        if sort_by_size and n > 3:
            size = item[3]
        elif sort_by_size and n == 3:
            size = item[2]
        else:
            size = 0
        mtime: float = 0.0
        if n > 4:
            mtime = item[4]
        elif n > 3 and (
            (sort_by_loc and sort_by_mtime and not sort_by_size)
            or (sort_by_size and sort_by_mtime and not sort_by_loc)
        ):
            mtime = item[3]
        elif n > 2 and sort_by_mtime and not sort_by_loc and not sort_by_size:
            mtime = item[2]
        return cls(name=name, path=path, loc=loc, size=size, mtime=float(mtime))

    @classmethod
    def coerce(cls, item: Union["FileEntry", tuple[Any, ...], str]) -> "FileEntry":
        """Normalize any raw ``_files`` entry to a :class:`FileEntry` by position.

        Unlike :meth:`from_raw`, this makes no assumptions about which metric
        flags were active: it simply reads the canonical
        ``(name, path, loc, size, mtime)`` slots by index, defaulting any
        missing trailing field. This matches how the scanner always emits
        entries (as full :class:`FileEntry` values) and lets callers that need
        the metric values — such as sorting — read them unconditionally.

        Args:
            item: A :class:`FileEntry`, a positional tuple, or a bare filename
                string.

        Returns:
            The equivalent :class:`FileEntry`.
        """
        if isinstance(item, cls):
            return item
        if not isinstance(item, tuple):
            name = str(item)
            return cls(name=name, path=name)
        n = len(item)
        if n == 0:
            return cls(name="unknown", path="unknown")
        name = item[0]
        path = item[1] if n > 1 else name
        loc = item[2] if n > 2 else 0
        size = item[3] if n > 3 else 0
        mtime = item[4] if n > 4 else 0.0
        return cls(name=name, path=path, loc=loc, size=size, mtime=float(mtime))
