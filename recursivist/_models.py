"""Shared data model for scanned directory structures.

This module defines [`Directory`][recursivist._models.Directory], the node type of the
tree a scan produces, and [`FileEntry`][recursivist._models.FileEntry], the fixed-shape
representation of a file stored in a directory's ``files`` list.

[`FileEntry`][recursivist._models.FileEntry] is a `typing.NamedTuple`, so an entry can
be used as a plain tuple — ``entry[0]`` is the name and ``isinstance(entry, tuple)`` is
``True`` — as well as through attribute access (``entry.name``, ``entry.loc``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
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


@dataclass(slots=True)
class Directory:
    """A single directory within a scanned directory structure.

    A scan yields a tree of these nodes: the root directory, with every subdirectory
    nested under its name in ``subdirectories``. Subdirectory names are the only keys of
    that mapping, so a directory may be called anything the filesystem allows.

    Attributes:
        files: The directory's own files.
        subdirectories: The directory's subdirectories, keyed by name.
        loc: Total lines of code in the directory and everything below it, or ``None``
            when lines of code were not counted.
        size: Total size in bytes of the directory and everything below it, or ``None``
            when sizes were not measured.
        mtime: Latest modification time (seconds since epoch) in the directory and
            everything below it, or ``None`` when modification times were not recorded.
        max_depth_reached: Whether traversal stopped at the depth limit, leaving the
            directory's contents unread.
        hidden_contents: Whether a directory cut short by the depth limit is not empty,
            which distinguishes it from one that holds nothing.
        symlink_loop: Whether the directory was not descended into because it resolves
            to one of its own ancestors, i.e. a symlink (or other) cycle back up the
            tree.
        git_markers: ``{filename: status_char}`` Git status markers for the directory's
            files. Empty when Git status was not collected or nothing here has a status.
    """

    files: list[FileEntry] = field(default_factory=list)
    subdirectories: dict[str, Directory] = field(default_factory=dict)
    loc: int | None = None
    size: int | None = None
    mtime: float | None = None
    max_depth_reached: bool = False
    hidden_contents: bool = False
    symlink_loop: bool = False
    git_markers: dict[str, str] = field(default_factory=dict)
