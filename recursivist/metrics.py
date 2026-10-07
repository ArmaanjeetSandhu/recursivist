"""File statistics and metric formatting.

Lines-of-code counting, file size and modification-time retrieval, and the helpers that
format those metrics into the annotation suffixes shown next to files and directories.
Uses only the standard library and the shared data model.
"""

import io
import logging
import os
import stat
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone

from recursivist._models import Directory

logger = logging.getLogger(__name__)

_SIZE_UNITS: dict[str, tuple[int, tuple[str, ...]]] = {
    "iec": (1024, ("KiB", "MiB", "GiB")),
    "si": (1000, ("kB", "MB", "GB")),
}
"""The step between units and the unit labels above bytes, smallest first, for each
size format."""


def _open_nonblocking(path: str, flags: int) -> int:
    """Opener for [`open`][] that never waits for the other end of a named pipe.

    ``O_NONBLOCK`` makes opening a FIFO or a device return at once instead of blocking
    until a writer appears. It has no effect on regular files and does not exist on
    Windows, where it is simply left out.
    """
    return os.open(path, flags | getattr(os, "O_NONBLOCK", 0))


def count_lines_of_code(file_path: str) -> int:
    """Count the number of lines in a text file.

    The encoding is inferred from the first 4 KiB: UTF-16 files are recognized by their
    byte-order mark or by a regular pattern of null bytes, while files containing null
    bytes that are not UTF-16 are treated as binary and skipped. Everything else is read
    as UTF-8. Undecodable bytes are replaced rather than rejected, which never changes
    the line count, so the file is opened once and read in a single pass.

    Only regular files are read. Named pipes, sockets and devices are opened without
    blocking and then skipped, because reading one can wait forever or never end.

    Args:
        file_path: Path to the file.

    Returns:
        The number of lines, or ``0`` if the file is empty, binary, not a regular file,
        or cannot be read.
    """
    try:
        with open(file_path, "rb", opener=_open_nonblocking) as binary_file:
            if not stat.S_ISREG(os.fstat(binary_file.fileno()).st_mode):
                logger.debug("Not a regular file, skipping: %s", file_path)
                return 0
            sample = binary_file.read(4096)
            encoding = _detect_text_encoding(sample)
            if encoding is None:
                return 0
            binary_file.seek(0)
            with io.TextIOWrapper(
                binary_file, encoding=encoding, errors="replace"
            ) as text_file:
                return sum(1 for _ in text_file)
    except (OSError, ValueError) as e:
        logger.debug("Could not read file: %s: %s", file_path, e)
        return 0


def _detect_text_encoding(sample: bytes) -> str | None:
    """Guess the text encoding of a file from its leading bytes.

    Args:
        sample: The first bytes of the file.

    Returns:
        The encoding to decode the file with, or ``None`` if the file is empty or looks
        binary.
    """
    if not sample:
        return None
    if sample.startswith(b"\xff\xfe"):
        return "utf-16-le"
    if sample.startswith(b"\xfe\xff"):
        return "utf-16-be"
    if len(sample) >= 16:
        head = sample[:32]
        odd_bytes_zero = not any(head[1::2])
        even_bytes_zero = not any(head[0::2])
        if odd_bytes_zero and not even_bytes_zero:
            return "utf-16-le"
        if even_bytes_zero and not odd_bytes_zero:
            return "utf-16-be"
    if b"\x00" in sample:
        return None
    return "utf-8"


def get_file_size(file_path: str) -> int:
    """Return the size of a file in bytes.

    Args:
        file_path: Path to the file whose size should be retrieved.

    Returns:
        Size of the file in bytes, or ``0`` when the file cannot be accessed (e.g.,
        permission error or the path no longer exists).
    """
    try:
        return os.path.getsize(file_path)
    except Exception as e:
        logger.debug("Could not get size for %s: %s", file_path, e)
        return 0


def format_size(size_in_bytes: int, size_format: str = "iec") -> str:
    """Format a byte count as a human-readable size string.

    With the ``"iec"`` format the value is scaled by powers of 1024 to bytes, KiB, MiB,
    or GiB. With the ``"si"`` format it is scaled by powers of 1000 to bytes, kB, MB, or
    GB. Either way a size below one step is written as a whole number of bytes, and
    every larger unit with one decimal place.

    The unit is chosen after rounding: a value that rounds up to a full step moves to
    the next unit (``1048575`` is ``"1.0 MiB"``, not ``"1024.0 KiB"``, and ``999950`` is
    ``"1.0 MB"``, not ``"1000.0 kB"``). The largest unit, GiB or GB, is never promoted.

    Args:
        size_in_bytes: Size in bytes.
        size_format: The units to use, either ``"iec"`` or ``"si"``.

    Returns:
        A human-readable size string (e.g. ``"512 B"``, ``"4.2 MiB"`` or ``"4.4 MB"``).
    """
    step, units = _SIZE_UNITS["si" if size_format == "si" else "iec"]
    if size_in_bytes < step:
        return f"{size_in_bytes} B"
    value = size_in_bytes / step
    for unit in units[:-1]:
        text = f"{value:.1f}"
        if float(text) < step:
            return f"{text} {unit}"
        value /= step
    return f"{value:.1f} {units[-1]}"


def get_file_mtime(file_path: str) -> float:
    """Return a file's modification time in seconds since the epoch.

    Args:
        file_path: Path to the file.

    Returns:
        The modification time as a float, or ``0.0`` if the file cannot be accessed.
    """
    try:
        return os.path.getmtime(file_path)
    except Exception as e:
        logger.debug("Could not get modification time for %s: %s", file_path, e)
        return 0.0


def format_timestamp(timestamp: float, date_format: str = "relative") -> str:
    """Format a Unix timestamp as a date/time string.

    With the ``"relative"`` format the result is recency-aware, in local time, and
    becomes coarser as the timestamp gets older:

    - Today: ``"Today HH:MM"``
    - Yesterday: ``"Yesterday HH:MM"``
    - Within the last week: abbreviated weekday and time (e.g. ``"Mon 14:30"``)
    - Earlier this year: abbreviated month and day (e.g. ``"Mar 15"``)
    - Older: ``"YYYY-MM-DD"``

    With the ``"iso"`` format the result is the ISO 8601 date and time in UTC, to the
    second. Unlike the relative form, it does not depend on when or where it is read,
    which suits output that is kept.

    Args:
        timestamp: Seconds since the epoch.
        date_format: The format to use, either ``"relative"`` or ``"iso"``.

    Returns:
        The formatted date/time string, or ``"-"`` when *timestamp* is zero or falls
        outside the representable range.
    """
    if not timestamp:
        return "-"
    if date_format == "iso":
        try:
            utc_dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        except (OSError, OverflowError, ValueError):
            return "-"
        return utc_dt.replace(tzinfo=None).isoformat(timespec="seconds") + "Z"
    try:
        dt_object = datetime.fromtimestamp(timestamp)
    except (OSError, OverflowError, ValueError):
        return "-"
    current_dt = datetime.now()
    current_date = current_dt.date()
    if dt_object.date() == current_date:
        return f"Today {dt_object.strftime('%H:%M')}"
    if dt_object.date() == current_date - timedelta(days=1):
        return f"Yesterday {dt_object.strftime('%H:%M')}"
    if dt_object.date() > current_date:
        return dt_object.strftime("%Y-%m-%d")
    if current_date - dt_object.date() < timedelta(days=7):
        return dt_object.strftime("%a %H:%M")
    if dt_object.year == current_dt.year:
        return dt_object.strftime("%b %d")
    return dt_object.strftime("%Y-%m-%d")


def format_metrics(
    loc: int = 0,
    size: int = 0,
    mtime: float = 0.0,
    metrics: Sequence[str] = (),
    date_format: str = "relative",
    size_format: str = "iec",
) -> str:
    """Build the parenthetical metrics annotation for a file or directory.

    Includes exactly the metrics named in *metrics*, in that order — e.g.
    ``metrics=("size", "loc")`` yields ``"(4.2 KiB, 120 lines)"``. The metric names are
    those defined in [`recursivist.flags`][recursivist.flags]: ``"loc"``, ``"size"`` and
    ``"mtime"``.

    Args:
        loc: Lines-of-code count.
        size: Size in bytes.
        mtime: Modification time (seconds since epoch).
        metrics: The metrics to include, in display order.
        date_format: How the modification time is written, either ``"relative"`` or
            ``"iso"`` (see [`format_timestamp`][recursivist.metrics.format_timestamp]).
        size_format: The units the size is written in, either ``"iec"`` or ``"si"``
            (see [`format_size`][recursivist.metrics.format_size]).

    Returns:
        The annotation string including the surrounding parentheses, or an empty string
        when *metrics* is empty.
    """
    renderers = {
        "loc": lambda: f"{loc} line" if loc == 1 else f"{loc} lines",
        "size": lambda: format_size(size, size_format),
        "mtime": lambda: format_timestamp(mtime, date_format),
    }
    parts = [renderers[m]() for m in metrics if m in renderers]
    return f"({', '.join(parts)})" if parts else ""


def format_metrics_suffix(
    loc: int = 0,
    size: int = 0,
    mtime: float = 0.0,
    metrics: Sequence[str] = (),
    date_format: str = "relative",
    size_format: str = "iec",
) -> str:
    """Like [`format_metrics`][recursivist.metrics.format_metrics] but prefixed with a
    single space.

    Convenient for appending directly after a file or directory name. Returns an empty
    string (no leading space) when *metrics* is empty.
    """
    annotation = format_metrics(loc, size, mtime, metrics, date_format, size_format)
    return f" {annotation}" if annotation else ""


def recorded_dir_metrics(
    directory: Directory, metrics: Sequence[str] = ()
) -> list[str]:
    """Return the entries of *metrics* that *directory* holds a total for.

    A directory carries a total only for the metrics its scan collected, and none at all
    when it was not traversed. The order of *metrics* is preserved.

    Args:
        directory: The directory whose totals are consulted.
        metrics: The metrics to display, in order.

    Returns:
        The displayable subset of *metrics*, in the same order.
    """
    totals: dict[str, int | float | None] = {
        "loc": directory.loc,
        "size": directory.size,
        "mtime": directory.mtime,
    }
    return [m for m in metrics if totals.get(m) is not None]


def format_dir_metrics(
    directory: Directory,
    metrics: Sequence[str] = (),
    date_format: str = "relative",
    size_format: str = "iec",
) -> str:
    """Return the space-prefixed metrics suffix for a directory.

    Wraps [`format_metrics_suffix`][recursivist.metrics.format_metrics_suffix], reading
    the totals from *directory* and keeping only the requested metrics that it actually
    holds a total for (see
    [`recorded_dir_metrics`][recursivist.metrics.recorded_dir_metrics]) — while
    preserving the requested display order.

    Args:
        directory: The directory whose totals are formatted.
        metrics: The metrics to display, in order.
        date_format: How the modification time is written, either ``"relative"`` or
            ``"iso"``.
        size_format: The units the size is written in, either ``"iec"`` or ``"si"``.

    Returns:
        The metrics suffix (with a leading space) or an empty string.
    """
    return format_metrics_suffix(
        directory.loc or 0,
        directory.size or 0,
        directory.mtime or 0.0,
        recorded_dir_metrics(directory, metrics),
        date_format,
        size_format,
    )
