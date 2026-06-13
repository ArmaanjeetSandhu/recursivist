from typing import Any

from .base import BaseExporter
from .html import HtmlExporter
from .json import JsonExporter
from .jsx import JsxExporter
from .markdown import MarkdownExporter
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
}


def get_exporter(format_type: str, **kwargs: Any) -> BaseExporter:
    """Factory function to get the appropriate exporter instance.

    Args:
        format_type: The desired export format (e.g., 'json', 'txt').
        **kwargs: Configuration arguments passed to the BaseExporter.

    Returns:
        An instantiated exporter ready to call .export()

    Raises:
        ValueError: If the format_type is not supported.
    """
    exporter_class = _EXPORTERS.get(format_type.lower())
    if not exporter_class:
        raise ValueError(
            f"Unsupported export format: {format_type}. "
            f"Supported formats: {', '.join(_EXPORTERS.keys())}"
        )

    return exporter_class(**kwargs)
