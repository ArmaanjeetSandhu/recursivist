import html
import logging
import os
from typing import Any

from recursivist.core import (
    format_metrics,
    format_metrics_suffix,
    generate_color_for_extension,
    iter_subdirectories,
    sort_files_by_type,
)
from recursivist.icons import get_icon

from .base import BaseExporter

logger = logging.getLogger(__name__)


class HtmlExporter(BaseExporter):
    def export(self, output_path: str) -> None:
        def _build_html_tree(
            structure: dict[str, Any],
            path_prefix: str = "",
        ) -> str:
            html_content = ["<ul>"]
            if "_files" in structure:
                for entry in sort_files_by_type(
                    structure["_files"],
                    self.sort_by_loc,
                    self.sort_by_size,
                    self.sort_by_mtime,
                    self.sort_by_similarity,
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
                    _GIT_HTML_STYLES = {
                        "U": ("#999999", "dim"),
                        "M": ("#d4a017", ""),
                        "A": ("#28a745", ""),
                        "D": ("#dc3545", "line-through"),
                    }
                    if _git_marker and _git_marker in _GIT_HTML_STYLES:
                        _badge_color, _file_style_extra = _GIT_HTML_STYLES[_git_marker]
                        _git_badge = f' <span class="git-badge git-{_git_marker.lower()}" style="color:{_badge_color};font-size:0.8em;font-weight:bold;">[{_git_marker}]</span>'
                        _name_style = (
                            ' style="text-decoration: line-through;"'
                            if _file_style_extra == "line-through"
                            else ""
                        )
                        _name_open = f"<span{_name_style}>"
                        _name_close = "</span>"
                        _file_style = f"color: {color};"
                    else:
                        _git_badge = ""
                        _name_open = ""
                        _name_close = ""
                        _file_style = f"color: {color};"

                    html_content.append(
                        f'<li class="file" style="{_file_style}">{file_icon} '
                        f"{_name_open}{html.escape(display_path)}{_name_close}"
                        + format_metrics_suffix(
                            entry.loc,
                            entry.size,
                            entry.mtime,
                            sort_by_loc=self.sort_by_loc,
                            sort_by_size=self.sort_by_size,
                            sort_by_mtime=self.sort_by_mtime,
                        )
                        + f"{_git_badge}</li>"
                    )
            for name, content in iter_subdirectories(structure):
                folder_icon = get_icon(name, is_dir=True, style=self.icon_style)

                enabled = []
                if isinstance(content, dict):
                    if self.sort_by_loc and "_loc" in content:
                        enabled.append("loc")
                    if self.sort_by_size and "_size" in content:
                        enabled.append("size")
                    if self.sort_by_mtime and "_mtime" in content:
                        enabled.append("mtime")
                metric_html = ""
                if enabled:
                    css = "metric-count" if len(enabled) >= 2 else f"{enabled[0]}-count"
                    inner = format_metrics(
                        content.get("_loc", 0),
                        content.get("_size", 0),
                        content.get("_mtime", 0.0),
                        sort_by_loc=self.sort_by_loc and "_loc" in content,
                        sort_by_size=self.sort_by_size and "_size" in content,
                        sort_by_mtime=self.sort_by_mtime and "_mtime" in content,
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

        title = f"{root_icon} {html.escape(self.root_name)}" + format_metrics_suffix(
            self.structure.get("_loc", 0),
            self.structure.get("_size", 0),
            self.structure.get("_mtime", 0.0),
            sort_by_loc=self.sort_by_loc and "_loc" in self.structure,
            sort_by_size=self.sort_by_size and "_size" in self.structure,
            sort_by_mtime=self.sort_by_mtime and "_mtime" in self.structure,
        )
        loc_styles = (
            """
            .loc-count {
                color: #666;
                font-size: 0.9em;
                font-weight: normal;
            }
        """
            if self.sort_by_loc
            else ""
        )
        size_styles = (
            """
            .size-count {
                color: #666;
                font-size: 0.9em;
                font-weight: normal;
            }
        """
            if self.sort_by_size
            else ""
        )
        mtime_styles = (
            """
            .mtime-count {
                color: #666;
                font-size: 0.9em;
                font-weight: normal;
            }
        """
            if self.sort_by_mtime
            else ""
        )
        metric_styles = (
            """
            .metric-count {
                color: #666;
                font-size: 0.9em;
                font-weight: normal;
            }
        """
            if (self.sort_by_size and self.sort_by_loc)
            or (self.sort_by_mtime and (self.sort_by_loc or self.sort_by_size))
            else ""
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
            .git-u { color: #999999; }
            .git-m { color: #d4a017; }
            .git-a { color: #28a745; }
            .git-d { color: #dc3545; }
        """
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
                {loc_styles}
                {size_styles}
                {mtime_styles}
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
