import html
import logging
import os
from typing import Any

from recursivist.core import format_size, format_timestamp, sort_files_by_type
from recursivist.icons import get_icon

from .base import BaseExporter

logger = logging.getLogger(__name__)


def _md_inline_code(text: str) -> str:
    """Render arbitrary text as an inline-code span that cannot be broken out of."""
    longest = current = 0
    for ch in text:
        if ch == "`":
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    fence = "`" * (longest + 1)
    if text.startswith("`") or text.endswith("`"):
        return f"{fence} {text} {fence}"
    return f"{fence}{text}{fence}"


def _md_escape_text(text: str) -> str:
    """Escape text used in non-code Markdown contexts (bold dir names, headings)."""
    for ch in ("\\", "`", "*", "[", "]"):
        text = text.replace(ch, "\\" + ch)
    return html.escape(text, quote=False)


class MarkdownExporter(BaseExporter):
    def export(self, output_path: str) -> None:
        def _build_md_tree(
            structure: dict[str, Any],
            level: int = 0,
            path_prefix: str = "",
        ) -> list[str]:
            lines = []
            indent = "    " * level
            if "_files" in structure:
                for file_item in sort_files_by_type(
                    structure["_files"],
                    self.sort_by_loc,
                    self.sort_by_size,
                    self.sort_by_mtime,
                ):
                    loc = 0
                    size = 0
                    mtime = 0

                    if isinstance(file_item, tuple):
                        if len(file_item) <= 0:
                            continue

                        if len(file_item) > 1:
                            display_path = file_item[1]
                        else:
                            display_path = file_item[0]

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
                        display_path = file_item

                    if isinstance(file_item, tuple) and len(file_item) > 0:
                        _fname_md = file_item[0]
                    elif isinstance(file_item, str):
                        _fname_md = file_item
                    else:
                        _fname_md = "unknown"

                    file_icon = get_icon(_fname_md, is_dir=False, style=self.icon_style)

                    _git_markers_md = structure.get("_git_markers", {})
                    _git_marker_md = (
                        _git_markers_md.get(_fname_md, "")
                        if self.show_git_status
                        else ""
                    )
                    _GIT_MD_BADGE = {
                        "U": "**[U]**",
                        "M": "**[M]**",
                        "A": "**[A]**",
                        "D": "**[D]**",
                    }
                    _md_code = _md_inline_code(display_path)
                    if _git_marker_md == "D":
                        _md_display = f"~~{_md_code}~~"
                    else:
                        _md_display = _md_code
                    _md_git_suffix = (
                        f" {_GIT_MD_BADGE[_git_marker_md]}"
                        if _git_marker_md in _GIT_MD_BADGE
                        else ""
                    )

                    if self.sort_by_loc and self.sort_by_size and self.sort_by_mtime:
                        lines.append(
                            f"{indent}- {file_icon} {_md_display} ({loc} lines, {format_size(size)}, {format_timestamp(mtime)}){_md_git_suffix}"
                        )
                    elif self.sort_by_loc and self.sort_by_mtime:
                        lines.append(
                            f"{indent}- {file_icon} {_md_display} ({loc} lines, {format_timestamp(mtime)}){_md_git_suffix}"
                        )
                    elif self.sort_by_size and self.sort_by_mtime:
                        lines.append(
                            f"{indent}- {file_icon} {_md_display} ({format_size(size)}, {format_timestamp(mtime)}){_md_git_suffix}"
                        )
                    elif self.sort_by_loc and self.sort_by_size:
                        lines.append(
                            f"{indent}- {file_icon} {_md_display} ({loc} lines, {format_size(size)}){_md_git_suffix}"
                        )
                    elif self.sort_by_mtime:
                        lines.append(
                            f"{indent}- {file_icon} {_md_display} ({format_timestamp(mtime)}){_md_git_suffix}"
                        )
                    elif self.sort_by_size:
                        lines.append(
                            f"{indent}- {file_icon} {_md_display} ({format_size(size)}){_md_git_suffix}"
                        )
                    elif self.sort_by_loc:
                        lines.append(
                            f"{indent}- {file_icon} {_md_display} ({loc} lines){_md_git_suffix}"
                        )
                    else:
                        lines.append(
                            f"{indent}- {file_icon} {_md_display}{_md_git_suffix}"
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
                    lines.append(
                        f"{indent}- {folder_icon} **{_md_escape_text(name)}** ({loc_count} lines, {format_size(size_count)}, {format_timestamp(mtime_count)})"
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
                    lines.append(
                        f"{indent}- {folder_icon} **{_md_escape_text(name)}** ({loc_count} lines, {format_size(size_count)})"
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
                    lines.append(
                        f"{indent}- {folder_icon} **{_md_escape_text(name)}** ({loc_count} lines, {format_timestamp(mtime_count)})"
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
                    lines.append(
                        f"{indent}- {folder_icon} **{_md_escape_text(name)}** ({format_size(size_count)}, {format_timestamp(mtime_count)})"
                    )
                elif (
                    self.sort_by_loc and isinstance(content, dict) and "_loc" in content
                ):
                    loc_count = content["_loc"]
                    lines.append(
                        f"{indent}- {folder_icon} **{_md_escape_text(name)}** ({loc_count} lines)"
                    )
                elif (
                    self.sort_by_size
                    and isinstance(content, dict)
                    and "_size" in content
                ):
                    size_count = content["_size"]
                    lines.append(
                        f"{indent}- {folder_icon} **{_md_escape_text(name)}** ({format_size(size_count)})"
                    )
                elif (
                    self.sort_by_mtime
                    and isinstance(content, dict)
                    and "_mtime" in content
                ):
                    mtime_count = content["_mtime"]
                    lines.append(
                        f"{indent}- {folder_icon} **{_md_escape_text(name)}** ({format_timestamp(mtime_count)})"
                    )
                else:
                    lines.append(f"{indent}- {folder_icon} **{_md_escape_text(name)}**")
                next_path = os.path.join(path_prefix, name) if path_prefix else name
                if isinstance(content, dict):
                    if content.get("_max_depth_reached"):
                        lines.append(f"{indent}    - ⋯ *(max depth reached)*")
                    else:
                        lines.extend(_build_md_tree(content, level + 1, next_path))
            return lines

        root_icon = get_icon(self.root_name, is_dir=True, style=self.icon_style)

        if (
            self.sort_by_loc
            and self.sort_by_size
            and self.sort_by_mtime
            and "_loc" in self.structure
            and "_size" in self.structure
            and "_mtime" in self.structure
        ):
            md_content = [
                f"# {root_icon} {_md_escape_text(self.root_name)} ({self.structure['_loc']} lines, {format_size(self.structure['_size'])}, {format_timestamp(self.structure['_mtime'])})",
                "",
            ]
        elif (
            self.sort_by_loc
            and self.sort_by_size
            and "_loc" in self.structure
            and "_size" in self.structure
        ):
            md_content = [
                f"# {root_icon} {_md_escape_text(self.root_name)} ({self.structure['_loc']} lines, {format_size(self.structure['_size'])})",
                "",
            ]
        elif (
            self.sort_by_loc
            and self.sort_by_mtime
            and "_loc" in self.structure
            and "_mtime" in self.structure
        ):
            md_content = [
                f"# {root_icon} {_md_escape_text(self.root_name)} ({self.structure['_loc']} lines, {format_timestamp(self.structure['_mtime'])})",
                "",
            ]
        elif (
            self.sort_by_size
            and self.sort_by_mtime
            and "_size" in self.structure
            and "_mtime" in self.structure
        ):
            md_content = [
                f"# {root_icon} {_md_escape_text(self.root_name)} ({format_size(self.structure['_size'])}, {format_timestamp(self.structure['_mtime'])})",
                "",
            ]
        elif self.sort_by_loc and "_loc" in self.structure:
            md_content = [
                f"# {root_icon} {_md_escape_text(self.root_name)} ({self.structure['_loc']} lines)",
                "",
            ]
        elif self.sort_by_size and "_size" in self.structure:
            md_content = [
                f"# {root_icon} {_md_escape_text(self.root_name)} ({format_size(self.structure['_size'])})",
                "",
            ]
        elif self.sort_by_mtime and "_mtime" in self.structure:
            md_content = [
                f"# {root_icon} {_md_escape_text(self.root_name)} ({format_timestamp(self.structure['_mtime'])})",
                "",
            ]
        else:
            md_content = [f"# {root_icon} {_md_escape_text(self.root_name)}", ""]

        md_content.extend(
            _build_md_tree(
                self.structure, 0, self.root_name if self.show_full_path else ""
            )
        )
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(md_content))
        except Exception as e:
            logger.exception(f"Error exporting to Markdown: {e}")
            raise
