import os
from collections.abc import Sequence
from typing import Any, Optional, Union


def sort_files_by_type(
    files: Sequence[
        Union[
            str,
            tuple[str, str],
            tuple[str, str, int],
            tuple[str, str, int, int],
            tuple[str, str, int, int, float],
        ]
    ],
    sort_by_loc: bool = False,
    sort_by_size: bool = False,
    sort_by_mtime: bool = False,
) -> list[
    Union[
        str,
        tuple[str, str],
        tuple[str, str, int],
        tuple[str, str, int, int],
        tuple[str, str, int, int, float],
    ]
]:
    """Sort a list of file entries by extension/name or by a requested statistic.

    When one or more sort flags are set, files are ordered by the corresponding
    statistic in descending order (highest first). When multiple flags are set,
    they are applied as a compound sort key in the order LOC > size > mtime.
    When no sort flag is set, files are grouped by extension and then sorted
    alphabetically within each group.

    *files* may contain plain strings (filename only) or tuples whose layout
    depends on which statistics were collected:

    * ``(name, display_path)``
    * ``(name, display_path, loc)``
    * ``(name, display_path, loc, size)``
    * ``(name, display_path, loc, size, mtime)``

    Args:
        files: Sequence of file entries to sort. An empty sequence is
            returned unchanged.
        sort_by_loc: When ``True``, include lines-of-code in the sort key.
        sort_by_size: When ``True``, include file size in the sort key.
        sort_by_mtime: When ``True``, include modification time in the sort
            key (newest first).

    Returns:
        A new sorted list containing the same elements as *files*.
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

    def get_size(item) -> int:
        if not isinstance(item, tuple):
            return 0
        if len(item) > 3:
            if sort_by_size:
                return item[3]
        elif len(item) == 3 and sort_by_size:
            return item[2]
        return 0

    def get_loc(item) -> int:
        if not isinstance(item, tuple) or len(item) <= 2:
            return 0
        return item[2] if sort_by_loc else 0

    def get_mtime(item) -> float:
        if not isinstance(item, tuple):
            return 0
        if len(item) > 4:
            return item[4]
        elif len(item) > 3 and (
            (sort_by_loc and sort_by_mtime and not sort_by_size)
            or (sort_by_size and sort_by_mtime and not sort_by_loc)
        ):
            return item[3]
        elif len(item) > 2 and sort_by_mtime and not sort_by_loc and not sort_by_size:
            return item[2]
        return 0

    if sort_by_loc and sort_by_size and sort_by_mtime and has_mtime:
        return sorted(files, key=lambda f: (-get_loc(f), -get_size(f), -get_mtime(f)))
    elif sort_by_loc and sort_by_size and (has_size or has_simple_size) and has_loc:
        return sorted(files, key=lambda f: (-get_loc(f), -get_size(f)))
    elif sort_by_loc and sort_by_mtime and has_mtime:
        return sorted(files, key=lambda f: (-get_loc(f), -get_mtime(f)))
    elif sort_by_size and sort_by_mtime and has_mtime:
        return sorted(files, key=lambda f: (-get_size(f), -get_mtime(f)))
    elif sort_by_loc and has_loc:
        return sorted(files, key=lambda f: -get_loc(f))
    elif sort_by_size and (has_size or has_simple_size):
        return sorted(files, key=lambda f: -get_size(f))
    elif sort_by_mtime and (has_mtime or has_simple_mtime):
        return sorted(files, key=lambda f: -get_mtime(f))

    def get_filename(item) -> str:
        if isinstance(item, tuple):
            return item[0]
        return item

    return sorted(
        files,
        key=lambda f: (
            os.path.splitext(get_filename(f))[1].lower(),
            get_filename(f).lower(),
        ),
    )


class BaseExporter:
    """Base class for all directory exporters holding shared configuration."""

    def __init__(
        self,
        structure: dict[str, Any],
        root_name: str,
        base_path: Optional[str] = None,
        sort_by_loc: bool = False,
        sort_by_size: bool = False,
        sort_by_mtime: bool = False,
        show_git_status: bool = False,
        icon_style: str = "emoji",
    ):
        self.structure = structure
        self.root_name = root_name
        self.base_path = base_path
        self.show_full_path = base_path is not None
        self.sort_by_loc = sort_by_loc
        self.sort_by_size = sort_by_size
        self.sort_by_mtime = sort_by_mtime
        self.show_git_status = show_git_status
        self.icon_style = icon_style

    def export(self, output_path: str) -> None:
        """Must be implemented by subclasses to perform the actual export."""
        raise NotImplementedError("Subclasses must implement the export method.")
