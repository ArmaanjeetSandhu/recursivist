"""reStructuredText tree exporter.

Renders the scanned structure as a nested reStructuredText bullet list (directories in bold, files as inline literals) under a section title for the
root, and writes it to a ``.rst`` file. The output is valid reStructuredText
that renders cleanly with docutils and Sphinx.
"""

import logging
import os
import unicodedata
from typing import Any

from recursivist.icons import get_icon
from recursivist.metrics import format_metrics_suffix
from recursivist.sorting import sort_files_by_type

from .base import BaseExporter

logger = logging.getLogger(__name__)

_EAST_ASIAN_WIDTHS = {"W": 2, "F": 2, "Na": 1, "H": 1, "N": 1, "A": 1}

_GIT_RST_BADGE = {
    "U": "**[U]**",
    "M": "**[M]**",
    "A": "**[A]**",
    "D": "**[D]**",
}


def _rst_display_width(text: str) -> int:
    """Return the display column width of *text*.

    Replicates :func:`docutils.utils.column_width`: East Asian wide and
    fullwidth characters count as two columns, combining characters as zero,
    and everything else as one. Used to size section-title underlines so they
    are never reported as too short.
    """
    width = sum(_EAST_ASIAN_WIDTHS[unicodedata.east_asian_width(c)] for c in text)
    width -= sum(1 for c in text if unicodedata.combining(c))
    return width


def _rst_inline_literal(text: str) -> str:
    """Render *text* as a reStructuredText inline literal (``text``).

    Inline literals display their content verbatim, which suits file paths.
    They cannot, however, contain a double back-tick (their end-string), and
    the parser only recognises them when the opening back-ticks are not
    followed by whitespace and the closing back-ticks are not preceded by
    whitespace. When *text* would violate any of these rules (it is empty,
    contains a double back-tick, or starts or ends with whitespace) the
    exporter falls back to escaped plain text so the output stays valid
    reStructuredText.
    """
    if text and "``" not in text and not text[0].isspace() and not text[-1].isspace():
        return f"``{text}``"
    return _rst_escape(text)


def _rst_escape(text: str) -> str:
    """Escape reStructuredText inline-markup characters in *text*.

    Backslash-escapes the characters that can start or end inline markup so the
    text renders literally in interpreted contexts such as bold directory names
    and the section title. The backslash itself is escaped first to avoid
    double-processing.
    """
    for ch in ("\\", "`", "*", "_", "|"):
        text = text.replace(ch, "\\" + ch)
    return text


class RstExporter(BaseExporter):
    """Exporter that writes the structure as a nested reStructuredText list."""

    def export(self, output_path: str) -> None:
        """Write the structure to *output_path* as reStructuredText.

        The root is rendered as a section title (underlined so its length
        matches the title's display width) followed by a nested bullet list.
        Directory names are shown in bold and filenames as inline literals,
        with any enabled metric or Git-status suffixes. A blank line is
        inserted before each nested list, as reStructuredText requires.

        Args:
            output_path: Path the ``.rst`` file is written to.

        Raises:
            Exception: Re-raised if writing the output file fails (after the
                error is logged).
        """

        def _build_rst_tree(
            structure: dict[str, Any],
            level: int = 0,
            path_prefix: str = "",
        ) -> list[str]:
            """Return the reStructuredText lines for *structure* and its descendants.

            Args:
                structure: Directory-structure dict to render.
                level: Current nesting depth, controlling indentation.
                path_prefix: Accumulated path used when full paths are shown.

            Returns:
                The rendered lines for this subtree, in display order. A blank
                line precedes every nested list so the output parses correctly.
            """
            lines: list[str] = []
            indent = "  " * level
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

                    _git_markers = structure.get("_git_markers", {})
                    _git_marker = (
                        _git_markers.get(entry.name, "") if self.show_git_status else ""
                    )
                    _git_suffix = (
                        f" {_GIT_RST_BADGE[_git_marker]}"
                        if _git_marker in _GIT_RST_BADGE
                        else ""
                    )

                    lines.append(
                        f"{indent}- {file_icon} {_rst_inline_literal(entry.path)}"
                        + format_metrics_suffix(
                            entry.loc,
                            entry.size,
                            entry.mtime,
                            sort_by_loc=self.sort_by_loc,
                            sort_by_size=self.sort_by_size,
                            sort_by_mtime=self.sort_by_mtime,
                        )
                        + _git_suffix
                    )
            for name, content in sorted(structure.items()):
                if name in (
                    "_files",
                    "_max_depth_reached",
                    "_loc",
                    "_size",
                    "_mtime",
                    "_git_markers",
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
                    f"{indent}- {folder_icon} **{_rst_escape(name)}**{metrics}"
                )
                next_path = os.path.join(path_prefix, name) if path_prefix else name
                if isinstance(content, dict):
                    if content.get("_max_depth_reached"):
                        lines.append("")
                        lines.append(f"{indent}  - ⋯ *(max depth reached)*")
                    else:
                        sublines = _build_rst_tree(content, level + 1, next_path)
                        if sublines:
                            lines.append("")
                            lines.extend(sublines)
            return lines

        root_icon = get_icon(self.root_name, is_dir=True, style=self.icon_style)
        root_title = f"{root_icon} {self.root_name}" + format_metrics_suffix(
            self.structure.get("_loc", 0),
            self.structure.get("_size", 0),
            self.structure.get("_mtime", 0.0),
            sort_by_loc=self.sort_by_loc and "_loc" in self.structure,
            sort_by_size=self.sort_by_size and "_size" in self.structure,
            sort_by_mtime=self.sort_by_mtime and "_mtime" in self.structure,
        )

        rst_content = [
            root_title,
            "=" * max(_rst_display_width(root_title), 1),
            "",
        ]

        rst_content.extend(
            _build_rst_tree(
                self.structure, 0, self.root_name if self.show_full_path else ""
            )
        )
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(rst_content) + "\n")
        except Exception as e:
            logger.exception(f"Error exporting to reStructuredText: {e}")
            raise
