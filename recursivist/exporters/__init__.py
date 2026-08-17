"""Exporter registry.

Maps each supported export format to its exporter class and exposes
:func:`get_exporter`, the factory used to construct the right exporter for a
requested format.
"""

from typing import Any

from .base import BaseExporter
from .html import HtmlExporter
from .json import JsonExporter
from .markdown import MarkdownExporter
from .rst import RstExporter
from .svg import SvgExporter
from .txt import TxtExporter

_EXPORTERS: dict[str, type[BaseExporter]] = {
    "txt": TxtExporter,
    "json": JsonExporter,
    "html": HtmlExporter,
    "markdown": MarkdownExporter,
    "md": MarkdownExporter,
    "svg": SvgExporter,
    "rst": RstExporter,
}


def supported_formats() -> list[str]:
    """Return the export format identifiers accepted by :func:`get_exporter`.

    This is the single source of truth for which formats are valid; callers
    (e.g. the CLI) should derive their validation from it rather than
    hard-coding a list.

    Returns:
        The supported format identifiers, sorted for stable presentation.
        Alias keys are included, so both ``"md"`` and ``"markdown"`` appear.
    """
    return sorted(_EXPORTERS)


def canonical_extension(format_type: str) -> str:
    """Return the canonical output file extension for a format identifier.

    The extension is read from the exporter class, so aliases that share an
    exporter collapse to a single extension.

    Args:
        format_type: Export format identifier (e.g. ``"json"`` or
            ``"markdown"``). Matched case-insensitively.

    Returns:
        The exporter's canonical file extension, without a leading dot (e.g.
        ``"md"`` for both ``"md"`` and ``"markdown"``). Falls back to the
        lowercased *format_type* for unknown formats, mirroring
        :func:`get_exporter`'s lookup.
    """
    exporter_class = _EXPORTERS.get(format_type.lower())
    if exporter_class is not None and exporter_class.extension:
        return exporter_class.extension
    return format_type.lower()


def get_exporter(format_type: str, **kwargs: Any) -> BaseExporter:
    """Construct the exporter for a given format.

    Args:
        format_type: Export format identifier (e.g. ``"json"`` or ``"txt"``).
            Matched case-insensitively; ``"md"`` and ``"markdown"`` are
            equivalent.
        **kwargs: Keyword arguments forwarded to the exporter's constructor
            (see :class:`BaseExporter`).

    Returns:
        A ready-to-use exporter instance; call its ``export`` method to write
        the output file.

    Raises:
        ValueError: If *format_type* is not a supported format.
    """
    exporter_class = _EXPORTERS.get(format_type.lower())
    if not exporter_class:
        raise ValueError(
            f"Unsupported export format: {format_type}. "
            f"Supported formats: {', '.join(_EXPORTERS.keys())}"
        )

    return exporter_class(**kwargs)
