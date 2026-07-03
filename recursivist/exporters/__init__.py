"""Exporter registry.

Maps each supported export format to its exporter class and exposes
:func:`get_exporter`, the factory used to construct the right exporter for a
requested format.
"""

from typing import Any

from .base import BaseExporter
from .html import HtmlExporter
from .json import JsonExporter
from .jsx import JsxExporter
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
    "jsx": JsxExporter,
    "svg": SvgExporter,
    "rst": RstExporter,
}


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
