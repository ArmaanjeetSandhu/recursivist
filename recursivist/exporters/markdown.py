import html
import logging
import os
from typing import Any

from recursivist.icons import get_icon
from recursivist.metrics import format_metrics_suffix
from recursivist.sorting import sort_files_by_type

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
                for entry in sort_files_by_type(
                    structure["_files"],
                    self.sort_by_loc,
                    self.sort_by_size,
                    self.sort_by_mtime,
                    self.sort_by_similarity,
                ):
                    file_icon = get_icon(
                        entry.name, is_dir=False, style=self.icon_style
                    )

                    _git_markers_md = structure.get("_git_markers", {})
                    _git_marker_md = (
                        _git_markers_md.get(entry.name, "")
                        if self.show_git_status
                        else ""
                    )
                    _GIT_MD_BADGE = {
                        "U": "**[U]**",
                        "M": "**[M]**",
                        "A": "**[A]**",
                        "D": "**[D]**",
                    }
                    _md_code = _md_inline_code(entry.path)
                    if _git_marker_md == "D":
                        _md_display = f"~~{_md_code}~~"
                    else:
                        _md_display = _md_code
                    _md_git_suffix = (
                        f" {_GIT_MD_BADGE[_git_marker_md]}"
                        if _git_marker_md in _GIT_MD_BADGE
                        else ""
                    )

                    lines.append(
                        f"{indent}- {file_icon} {_md_display}"
                        + format_metrics_suffix(
                            entry.loc,
                            entry.size,
                            entry.mtime,
                            sort_by_loc=self.sort_by_loc,
                            sort_by_size=self.sort_by_size,
                            sort_by_mtime=self.sort_by_mtime,
                        )
                        + _md_git_suffix
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

                metrics = ""
                if isinstance(content, dict):
                    metrics = format_metrics_suffix(
                        content.get("_loc", 0),
                        content.get("_size", 0),
                        content.get("_mtime", 0.0),
                        sort_by_loc=self.sort_by_loc and "_loc" in content,
                        sort_by_size=self.sort_by_size and "_size" in content,
                        sort_by_mtime=self.sort_by_mtime and "_mtime" in content,
                    )
                lines.append(
                    f"{indent}- {folder_icon} **{_md_escape_text(name)}**{metrics}"
                )
                next_path = os.path.join(path_prefix, name) if path_prefix else name
                if isinstance(content, dict):
                    if content.get("_max_depth_reached"):
                        lines.append(f"{indent}    - ⋯ *(max depth reached)*")
                    else:
                        lines.extend(_build_md_tree(content, level + 1, next_path))
            return lines

        root_icon = get_icon(self.root_name, is_dir=True, style=self.icon_style)

        md_content = [
            f"# {root_icon} {_md_escape_text(self.root_name)}"
            + format_metrics_suffix(
                self.structure.get("_loc", 0),
                self.structure.get("_size", 0),
                self.structure.get("_mtime", 0.0),
                sort_by_loc=self.sort_by_loc and "_loc" in self.structure,
                sort_by_size=self.sort_by_size and "_size" in self.structure,
                sort_by_mtime=self.sort_by_mtime and "_mtime" in self.structure,
            ),
            "",
        ]

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
