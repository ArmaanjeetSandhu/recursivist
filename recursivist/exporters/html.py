"""Standalone HTML tree exporter.

Renders the scanned structure as a self-contained HTML document — a nested,
styled list with extension-colored files and optional metric and Git-status
annotations — and writes it to an ``.html`` file.
"""

import html
import logging
import os
from typing import Any

from recursivist.colors import generate_color_for_extension
from recursivist.icons import get_icon
from recursivist.metrics import (
    format_dir_metrics,
    format_metrics,
    format_metrics_suffix,
)
from recursivist.scanner import iter_subdirectories
from recursivist.sorting import sort_files_by_type

from .base import BaseExporter

logger = logging.getLogger(__name__)

_GIT_STATUS_STYLES: dict[str, tuple[str, str]] = {
    "U": ("#999999", "dim"),
    "M": ("#d4a017", ""),
    "A": ("#28a745", ""),
    "D": ("#dc3545", "line-through"),
}


class HtmlExporter(BaseExporter):
    """Exporter that writes the structure as a standalone HTML page."""

    def export(self, output_path: str) -> None:
        """Write the structure to *output_path* as an HTML document.

        Produces a self-contained page with an embedded stylesheet: a nested
        list of extension-colored files and bold directory names, plus any
        enabled metric or Git-status annotations. All names are HTML-escaped.

        Args:
            output_path: Path the ``.html`` file is written to.

        Raises:
            Exception: Re-raised if writing the output file fails (after the
                error is logged).
        """

        def _build_html_tree(
            structure: dict[str, Any],
            path_prefix: str = "",
        ) -> str:
            """Return the nested ``<ul>`` markup for *structure*.

            Args:
                structure: Directory-structure dict to render.
                path_prefix: Accumulated path used when full paths are shown.

            Returns:
                An HTML fragment representing this subtree.
            """
            html_content = ["<ul>"]
            if "_files" in structure:
                for entry in sort_files_by_type(
                    structure["_files"],
                    self.sort_key,
                    structure.get("_git_markers"),
                ):
                    file_name = entry.name
                    display_path = entry.path

                    ext = os.path.splitext(file_name)[1].lower()
                    color = generate_color_for_extension(ext)

                    file_icon = get_icon(file_name, is_dir=False, style=self.icon_style)

                    _git_markers_here = structure.get("_git_markers", {})
                    _git_marker = (
                        _git_markers_here.get(file_name, "")
                        if self.show_git_status
                        else ""
                    )
                    _file_style = f"color: {color};"
                    if _git_marker and _git_marker in _GIT_STATUS_STYLES:
                        _, _file_style_extra = _GIT_STATUS_STYLES[_git_marker]
                        _git_badge = f' <span class="git-badge git-{_git_marker.lower()}" style="font-size:0.8em;font-weight:bold;">[{_git_marker}]</span>'
                        _name_style = (
                            ' style="text-decoration: line-through;"'
                            if _file_style_extra == "line-through"
                            else ""
                        )
                        _name_open = f"<span{_name_style}>"
                        _name_close = "</span>"
                    else:
                        _git_badge = ""
                        _name_open = ""
                        _name_close = ""

                    html_content.append(
                        f'<li class="file" style="{_file_style}">{file_icon} '
                        f"{_name_open}{html.escape(display_path)}{_name_close}"
                        + format_metrics_suffix(
                            entry.loc, entry.size, entry.mtime, self.metrics
                        )
                        + f"{_git_badge}</li>"
                    )
            for name, content in iter_subdirectories(structure):
                folder_icon = get_icon(name, is_dir=True, style=self.icon_style)

                enabled = []
                if isinstance(content, dict):
                    enabled = [m for m in self.metrics if f"_{m}" in content]
                metric_html = ""
                if enabled:
                    css = "metric-count" if len(enabled) >= 2 else f"{enabled[0]}-count"
                    inner = format_metrics(
                        content.get("_loc", 0),
                        content.get("_size", 0),
                        content.get("_mtime", 0.0),
                        enabled,
                    )
                    metric_html = f' <span class="{css}">{inner}</span>'
                html_content.append(
                    f'<li class="directory">{folder_icon} '
                    f'<span class="dir-name">{html.escape(name)}</span>{metric_html}'
                )
                next_path = os.path.join(path_prefix, name) if path_prefix else name
                if isinstance(content, dict):
                    if content.get("_max_depth_reached"):
                        html_content.append(
                            '<ul><li class="max-depth">⋯ (max depth reached)</li></ul>'
                        )
                    else:
                        html_content.append(_build_html_tree(content, next_path))
                html_content.append("</li>")
            html_content.append("</ul>")
            return "\n".join(html_content)

        root_icon = get_icon(self.root_name, is_dir=True, style=self.icon_style)

        title = f"{root_icon} {html.escape(self.root_name)}" + format_dir_metrics(
            self.structure, self.metrics
        )
        metric_styles = (
            """
            .loc-count,
            .size-count,
            .mtime-count,
            .metric-count {
                color: #666;
                font-size: 0.9em;
                font-weight: normal;
            }
        """
            if self.metrics
            else ""
        )
        git_color_rules = "\n".join(
            f"            .git-{marker.lower()} {{ color: {color}; }}"
            for marker, (color, _decoration) in _GIT_STATUS_STYLES.items()
        )
        git_styles = (
            """
            .git-badge {
                font-size: 0.78em;
                font-weight: bold;
                font-family: monospace;
                margin-left: 4px;
                vertical-align: middle;
            }
"""
            + git_color_rules
            + "\n        "
            if self.show_git_status
            else ""
        )
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Directory Structure - {html.escape(self.root_name)}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                }}
                ul {{
                    list-style-type: none;
                    padding-left: 20px;
                }}
                .directory {{
                    color: #2c3e50;
                }}
                .dir-name {{
                    font-weight: bold;
                }}
                .file {{
                    color: #34495e;
                }}
                .max-depth {{
                    color: #999;
                    font-style: italic;
                }}
                .path-info {{
                    margin-bottom: 20px;
                    font-style: italic;
                    color: #666;
                }}
                {metric_styles}
                {git_styles}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            {_build_html_tree(self.structure, self.root_name if self.show_full_path else "")}
        </body>
        </html>
        """

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_template)
        except Exception as e:
            logger.exception(f"Error exporting to HTML: {e}")
            raise
