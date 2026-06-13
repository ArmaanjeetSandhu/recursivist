import html
import logging
import os
from typing import Any

from recursivist.core import format_size, format_timestamp, generate_color_for_extension
from recursivist.icons import get_icon

from .base import BaseExporter, sort_files_by_type

logger = logging.getLogger(__name__)


class HtmlExporter(BaseExporter):
    def export(self, output_path: str) -> None:
        def _build_html_tree(
            structure: dict[str, Any],
            path_prefix: str = "",
        ) -> str:
            html_content = ["<ul>"]
            if "_files" in structure:
                for file_item in sort_files_by_type(
                    structure["_files"],
                    self.sort_by_loc,
                    self.sort_by_size,
                    self.sort_by_mtime,
                ):
                    file_name = "unknown"
                    loc = 0
                    size = 0
                    mtime = 0

                    if isinstance(file_item, tuple):
                        if len(file_item) > 0:
                            file_name = file_item[0]
                        if len(file_item) > 1:
                            display_path = file_item[1]
                        else:
                            display_path = file_name

                        if (
                            self.sort_by_loc
                            and self.sort_by_size
                            and self.sort_by_mtime
                            and len(file_item) > 4
                        ):
                            loc = file_item[2]
                            size = file_item[3]
                            mtime = int(file_item[4])
                        elif (
                            self.sort_by_loc
                            and self.sort_by_mtime
                            and len(file_item) > 4
                        ):
                            loc = file_item[2]
                            mtime = int(file_item[4])
                        elif (
                            self.sort_by_size
                            and self.sort_by_mtime
                            and len(file_item) > 4
                        ):
                            size = file_item[3]
                            mtime = int(file_item[4])
                        elif (
                            self.sort_by_loc
                            and self.sort_by_size
                            and len(file_item) > 3
                        ):
                            loc = file_item[2]
                            size = file_item[3]
                        elif self.sort_by_loc and len(file_item) > 2:
                            loc = file_item[2]
                        elif self.sort_by_size and len(file_item) > 2:
                            size = file_item[2]
                        elif self.sort_by_mtime and len(file_item) > 2:
                            mtime = file_item[2]
                    else:
                        file_name = file_item
                        display_path = file_name

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

                    if self.sort_by_loc and self.sort_by_size and self.sort_by_mtime:
                        html_content.append(
                            f'<li class="file" style="{_file_style}">{file_icon} {_name_open}{html.escape(display_path)}{_name_close} ({loc} lines, {format_size(size)}, {format_timestamp(mtime)}){_git_badge}</li>'
                        )
                    elif self.sort_by_loc and self.sort_by_mtime:
                        html_content.append(
                            f'<li class="file" style="{_file_style}">{file_icon} {_name_open}{html.escape(display_path)}{_name_close} ({loc} lines, {format_timestamp(mtime)}){_git_badge}</li>'
                        )
                    elif self.sort_by_size and self.sort_by_mtime:
                        html_content.append(
                            f'<li class="file" style="{_file_style}">{file_icon} {_name_open}{html.escape(display_path)}{_name_close} ({format_size(size)}, {format_timestamp(mtime)}){_git_badge}</li>'
                        )
                    elif self.sort_by_loc and self.sort_by_size:
                        html_content.append(
                            f'<li class="file" style="{_file_style}">{file_icon} {_name_open}{html.escape(display_path)}{_name_close} ({loc} lines, {format_size(size)}){_git_badge}</li>'
                        )
                    elif self.sort_by_mtime:
                        html_content.append(
                            f'<li class="file" style="{_file_style}">{file_icon} {_name_open}{html.escape(display_path)}{_name_close} ({format_timestamp(mtime)}){_git_badge}</li>'
                        )
                    elif self.sort_by_size:
                        html_content.append(
                            f'<li class="file" style="{_file_style}">{file_icon} {_name_open}{html.escape(display_path)}{_name_close} ({format_size(size)}){_git_badge}</li>'
                        )
                    elif self.sort_by_loc:
                        html_content.append(
                            f'<li class="file" style="{_file_style}">{file_icon} {_name_open}{html.escape(display_path)}{_name_close} ({loc} lines){_git_badge}</li>'
                        )
                    else:
                        html_content.append(
                            f'<li class="file" style="{_file_style}">{file_icon} {_name_open}{html.escape(display_path)}{_name_close}{_git_badge}</li>'
                        )
            for name, content in sorted(structure.items()):
                if (
                    name == "_files"
                    or name == "_max_depth_reached"
                    or name == "_loc"
                    or name == "_size"
                    or name == "_mtime"
                    or name == "_git_markers"
                ):
                    continue

                folder_icon = get_icon(name, is_dir=True, style=self.icon_style)

                if (
                    self.sort_by_loc
                    and self.sort_by_size
                    and self.sort_by_mtime
                    and isinstance(content, dict)
                    and "_loc" in content
                    and "_size" in content
                    and "_mtime" in content
                ):
                    loc_count = content["_loc"]
                    size_count = content["_size"]
                    mtime_count = content["_mtime"]
                    html_content.append(
                        f'<li class="directory">{folder_icon} <span class="dir-name">{html.escape(name)}</span> '
                        f'<span class="metric-count">({loc_count} lines, {format_size(size_count)}, {format_timestamp(mtime_count)})</span>'
                    )
                elif (
                    self.sort_by_loc
                    and self.sort_by_size
                    and isinstance(content, dict)
                    and "_loc" in content
                    and "_size" in content
                ):
                    loc_count = content["_loc"]
                    size_count = content["_size"]
                    html_content.append(
                        f'<li class="directory">{folder_icon} <span class="dir-name">{html.escape(name)}</span> '
                        f'<span class="metric-count">({loc_count} lines, {format_size(size_count)})</span>'
                    )
                elif (
                    self.sort_by_loc
                    and self.sort_by_mtime
                    and isinstance(content, dict)
                    and "_loc" in content
                    and "_mtime" in content
                ):
                    loc_count = content["_loc"]
                    mtime_count = content["_mtime"]
                    html_content.append(
                        f'<li class="directory">{folder_icon} <span class="dir-name">{html.escape(name)}</span> '
                        f'<span class="metric-count">({loc_count} lines, {format_timestamp(mtime_count)})</span>'
                    )
                elif (
                    self.sort_by_size
                    and self.sort_by_mtime
                    and isinstance(content, dict)
                    and "_size" in content
                    and "_mtime" in content
                ):
                    size_count = content["_size"]
                    mtime_count = content["_mtime"]
                    html_content.append(
                        f'<li class="directory">{folder_icon} <span class="dir-name">{html.escape(name)}</span> '
                        f'<span class="metric-count">({format_size(size_count)}, {format_timestamp(mtime_count)})</span>'
                    )
                elif (
                    self.sort_by_loc and isinstance(content, dict) and "_loc" in content
                ):
                    loc_count = content["_loc"]
                    html_content.append(
                        f'<li class="directory">{folder_icon} <span class="dir-name">{html.escape(name)}</span> '
                        f'<span class="loc-count">({loc_count} lines)</span>'
                    )
                elif (
                    self.sort_by_size
                    and isinstance(content, dict)
                    and "_size" in content
                ):
                    size_count = content["_size"]
                    html_content.append(
                        f'<li class="directory">{folder_icon} <span class="dir-name">{html.escape(name)}</span> '
                        f'<span class="size-count">({format_size(size_count)})</span>'
                    )
                elif (
                    self.sort_by_mtime
                    and isinstance(content, dict)
                    and "_mtime" in content
                ):
                    mtime_count = content["_mtime"]
                    html_content.append(
                        f'<li class="directory">{folder_icon} <span class="dir-name">{html.escape(name)}</span> '
                        f'<span class="mtime-count">({format_timestamp(mtime_count)})</span>'
                    )
                else:
                    html_content.append(
                        f'<li class="directory">{folder_icon} <span class="dir-name">{html.escape(name)}</span>'
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

        title = f"{root_icon} {html.escape(self.root_name)}"
        if (
            self.sort_by_loc
            and self.sort_by_size
            and self.sort_by_mtime
            and "_loc" in self.structure
            and "_size" in self.structure
            and "_mtime" in self.structure
        ):
            title = f"{root_icon} {html.escape(self.root_name)} ({self.structure['_loc']} lines, {format_size(self.structure['_size'])}, {format_timestamp(self.structure['_mtime'])})"
        elif (
            self.sort_by_loc
            and self.sort_by_size
            and "_loc" in self.structure
            and "_size" in self.structure
        ):
            title = f"{root_icon} {html.escape(self.root_name)} ({self.structure['_loc']} lines, {format_size(self.structure['_size'])})"
        elif (
            self.sort_by_loc
            and self.sort_by_mtime
            and "_loc" in self.structure
            and "_mtime" in self.structure
        ):
            title = f"{root_icon} {html.escape(self.root_name)} ({self.structure['_loc']} lines, {format_timestamp(self.structure['_mtime'])})"
        elif (
            self.sort_by_size
            and self.sort_by_mtime
            and "_size" in self.structure
            and "_mtime" in self.structure
        ):
            title = f"{root_icon} {html.escape(self.root_name)} ({format_size(self.structure['_size'])}, {format_timestamp(self.structure['_mtime'])})"
        elif self.sort_by_loc and "_loc" in self.structure:
            title = f"{root_icon} {html.escape(self.root_name)} ({self.structure['_loc']} lines)"
        elif self.sort_by_size and "_size" in self.structure:
            title = f"{root_icon} {html.escape(self.root_name)} ({format_size(self.structure['_size'])})"
        elif self.sort_by_mtime and "_mtime" in self.structure:
            title = f"{root_icon} {html.escape(self.root_name)} ({format_timestamp(self.structure['_mtime'])})"
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
