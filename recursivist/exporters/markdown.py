"""Markdown tree exporter.

Renders the scanned structure as a nested Markdown bullet list — directories in
bold, files as inline code — and writes it to a ``.md`` file.
"""

import html
import logging
import os
from typing import Any

from recursivist.icons import get_icon
from recursivist.metrics import format_dir_metrics, format_metrics_suffix
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
    """Exporter that writes the structure as a nested Markdown list."""

    def export(self, output_path: str) -> None:
        """Write the structure to *output_path* as a Markdown list.

        Directory names are rendered in bold and filenames as inline code,
        with any enabled metric or Git-status suffixes; deleted files are
        struck through.

        Args:
            output_path: Path the ``.md`` file is written to.

        Raises:
            Exception: Re-raised if writing the output file fails (after the
                error is logged).
        """

        def _build_md_tree(
            structure: dict[str, Any],
            level: int = 0,
            path_prefix: str = "",
        ) -> list[str]:
            """Return the Markdown lines for *structure* and its descendants.

            Args:
                structure: Directory-structure dict to render.
                level: Current nesting depth, controlling indentation.
                path_prefix: Accumulated path used when full paths are shown.

            Returns:
                The rendered lines for this subtree, in display order.
            """
            lines = []
            indent = "    " * level
            if "_files" in structure:
                for entry in sort_files_by_type(
                    structure["_files"],
                    self.sort_key,
                    structure.get("_git_markers"),
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
                            entry.loc, entry.size, entry.mtime, self.metrics
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
                    metrics = format_dir_metrics(content, self.metrics)
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
            + format_dir_metrics(self.structure, self.metrics),
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
