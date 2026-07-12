"""File statistics and metric formatting.

Lines-of-code counting, file size and modification-time retrieval, and the
helpers that format those metrics into the annotation suffixes shown next to
files and directories. Pure standard library.
"""

import datetime
import logging
import os
from collections.abc import Sequence
from datetime import datetime as dt
from typing import Any

logger = logging.getLogger(__name__)


def count_lines_of_code(file_path: str) -> int:
    """Count the number of lines in a text file.

    Detects the encoding well enough to count lines reliably: UTF-16 files are
    recognized by their byte-order mark or by a regular pattern of null bytes,
    while files containing null bytes that are not UTF-16 are treated as binary
    and skipped. Decoding falls back from strict UTF-8 to UTF-16 and finally to
    UTF-8 with replacement so that text is never rejected over a stray byte.

    Args:
        file_path: Path to the file.

    Returns:
        The number of lines, or ``0`` if the file is empty, binary, or cannot
        be read.
    """
    try:
        with open(file_path, "rb") as binary_file:
            sample = binary_file.read(4096)
            if not sample:
                return 0
            utf16_le_bom = sample.startswith(b"\xff\xfe")
            utf16_be_bom = sample.startswith(b"\xfe\xff")
            if utf16_le_bom or utf16_be_bom:
                encoding = "utf-16-le" if utf16_le_bom else "utf-16-be"
                with open(file_path, encoding=encoding, errors="replace") as text_file:
                    return sum(1 for _ in text_file)
            potential_utf16le: bool = False
            potential_utf16be: bool = False
            if len(sample) >= 16:
                potential_utf16le = all(
                    sample[i] == 0 for i in range(1, min(32, len(sample)), 2)
                )
                potential_utf16be = all(
                    sample[i] == 0 for i in range(0, min(32, len(sample)), 2)
                )
                if potential_utf16le or potential_utf16be:
                    encoding = "utf-16-le" if potential_utf16le else "utf-16-be"
                    try:
                        with open(
                            file_path, encoding=encoding, errors="replace"
                        ) as text_file:
                            return sum(1 for _ in text_file)
                    except Exception:
                        pass
            if b"\x00" in sample and not (potential_utf16le or potential_utf16be):
                return 0
    except Exception as e:
        logger.debug(f"Could not analyze file: {file_path}: {e}")
        return 0
    try:
        with open(file_path, encoding="utf-8", errors="strict") as text_file:
            return sum(1 for _ in text_file)
    except UnicodeDecodeError:
        pass
    except Exception as e:
        logger.debug(f"Could not read file as UTF-8: {file_path}: {e}")
        return 0

    try:
        with open(file_path, encoding="utf-8", errors="replace") as text_file:
            return sum(1 for _ in text_file)
    except Exception as e:
        logger.debug(f"Could not analyze file with replacement: {file_path}: {e}")
        return 0


def get_file_size(file_path: str) -> int:
    """Return the size of a file in bytes.

    Args:
        file_path: Path to the file whose size should be retrieved.

    Returns:
        Size of the file in bytes, or ``0`` when the file cannot be
        accessed (e.g., permission error or the path no longer exists).
    """
    try:
        return os.path.getsize(file_path)
    except Exception as e:
        logger.debug(f"Could not get size for {file_path}: {e}")
        return 0


def format_size(size_in_bytes: int) -> str:
    """Format a byte count as a human-readable size string.

    Scales the value to bytes, KB, MB, or GB and formats it with one decimal
    place for every unit above bytes.

    Args:
        size_in_bytes: Size in bytes.

    Returns:
        A human-readable size string (e.g. ``"512 B"`` or ``"4.2 MB"``).
    """
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    elif size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.1f} KB"
    elif size_in_bytes < 1024 * 1024 * 1024:
        return f"{size_in_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_in_bytes / (1024 * 1024 * 1024):.1f} GB"


def get_file_mtime(file_path: str) -> float:
    """Return a file's modification time in seconds since the epoch.

    Args:
        file_path: Path to the file.

    Returns:
        The modification time as a float, or ``0.0`` if the file cannot be
        accessed.
    """
    try:
        return os.path.getmtime(file_path)
    except Exception as e:
        logger.debug(f"Could not get modification time for {file_path}: {e}")
        return 0.0


def format_timestamp(timestamp: float) -> str:
    """Format a Unix timestamp as a human-readable, recency-aware string.

    The representation becomes coarser as the timestamp gets older:

    - Today: ``"Today HH:MM"``
    - Yesterday: ``"Yesterday HH:MM"``
    - Within the last week: abbreviated weekday and time (e.g. ``"Mon 14:30"``)
    - Earlier this year: abbreviated month and day (e.g. ``"Mar 15"``)
    - Older: ``"YYYY-MM-DD"``

    Args:
        timestamp: Seconds since the epoch.

    Returns:
        The formatted date/time string, or ``"-"`` when *timestamp* is zero or
        falls outside the representable range.
    """
    if not timestamp:
        return "-"
    try:
        dt_object = dt.fromtimestamp(timestamp)
    except (OSError, OverflowError, ValueError):
        return "-"
    current_dt = dt.now()
    current_date = current_dt.date()
    if dt_object.date() == current_date:
        return f"Today {dt_object.strftime('%H:%M')}"
    elif dt_object.date() == current_date - datetime.timedelta(days=1):
        return f"Yesterday {dt_object.strftime('%H:%M')}"
    elif current_date - dt_object.date() < datetime.timedelta(days=7):
        return dt_object.strftime("%a %H:%M")
    elif dt_object.year == current_dt.year:
        return dt_object.strftime("%b %d")
    else:
        return dt_object.strftime("%Y-%m-%d")


def format_metrics(
    loc: int = 0,
    size: int = 0,
    mtime: float = 0.0,
    metrics: Sequence[str] = (),
) -> str:
    """Build the parenthetical metrics annotation for a file or directory.

    Includes exactly the metrics named in *metrics*, in that order — e.g.
    ``metrics=("size", "loc")`` yields ``"(4.2 KB, 120 lines)"``. The metric
    names are those defined in :mod:`recursivist.flags`: ``"loc"``, ``"size"``
    and ``"mtime"``.

    Args:
        loc: Lines-of-code count.
        size: Size in bytes.
        mtime: Modification time (seconds since epoch).
        metrics: The metrics to include, in display order.

    Returns:
        The annotation string including the surrounding parentheses, or an
        empty string when *metrics* is empty.
    """
    renderers = {
        "loc": lambda: f"{loc} line" if loc == 1 else f"{loc} lines",
        "size": lambda: format_size(size),
        "mtime": lambda: format_timestamp(mtime),
    }
    parts = [renderers[m]() for m in metrics if m in renderers]
    return f"({', '.join(parts)})" if parts else ""


def format_metrics_suffix(
    loc: int = 0,
    size: int = 0,
    mtime: float = 0.0,
    metrics: Sequence[str] = (),
) -> str:
    """Like :func:`format_metrics` but prefixed with a single space.

    Convenient for appending directly after a file or directory name. Returns
    an empty string (no leading space) when *metrics* is empty.
    """
    annotation = format_metrics(loc, size, mtime, metrics)
    return f" {annotation}" if annotation else ""


def format_dir_metrics(content: Any, metrics: Sequence[str] = ()) -> str:
    """Return the space-prefixed metrics suffix for a directory node.

    Wraps :func:`format_metrics_suffix`, reading the totals from a directory's
    structure dict and keeping only the requested metrics that are actually
    present on that directory — while preserving the requested display order.
    Returns ``""`` for a non-dict node.

    Args:
        content: The directory's structure dict (or any value; non-dicts yield
            an empty string).
        metrics: The metrics to display, in order.

    Returns:
        The metrics suffix (with a leading space) or an empty string.
    """
    if not isinstance(content, dict):
        return ""
    present = [m for m in metrics if f"_{m}" in content]
    return format_metrics_suffix(
        content.get("_loc", 0),
        content.get("_size", 0),
        content.get("_mtime", 0.0),
        present,
    )
