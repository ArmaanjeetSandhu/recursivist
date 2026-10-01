"""Shared data model for directory-structure entries.

This module defines [`FileEntry`][recursivist._models.FileEntry], the fixed-shape
representation of a file stored under ``structure["_files"]``.

[`FileEntry`][recursivist._models.FileEntry] is a `typing.NamedTuple`, so an entry can
be used as a plain tuple — ``entry[0]`` is the name and ``isinstance(entry, tuple)`` is
``True`` — as well as through attribute access (``entry.name``, ``entry.loc``).
"""

from __future__ import annotations

from typing import NamedTuple


class FileEntry(NamedTuple):
    """A single file within a scanned directory structure.

    Attributes:
        name: Bare filename (e.g. ``"main.py"``). Used for icon lookup, extension
            detection and Git-status lookup.
        path: The string to display for this file — an absolute, forward-slash path when
            full-path display is enabled, otherwise just ``name``.
        loc: Lines of code. Populated only when LOC counting is enabled during scanning;
            ``0`` otherwise.
        size: File size in bytes. Populated only when size tracking is enabled; ``0``
            otherwise.
        mtime: Modification time (seconds since epoch). Populated only when mtime
            tracking is enabled; ``0.0`` otherwise.
    """

    name: str
    path: str
    loc: int = 0
    size: int = 0
    mtime: float = 0.0
