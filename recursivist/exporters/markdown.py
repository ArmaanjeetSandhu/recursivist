"""Markdown tree exporter.

Renders the scanned structure as a nested Markdown bullet list — directories in bold,
files as inline code — and writes it to a ``.md`` file.
"""

import html

from recursivist._models import Directory
from recursivist.icons import get_icon
from recursivist.metrics import format_dir_metrics, format_metrics_suffix
from recursivist.scanner import has_contents, iter_subdirectories
from recursivist.sorting import sort_files_by_type

from .base import BaseExporter, write_text


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
    """Escape text used in non-code Markdown contexts (bold dir names, headings).

    Backslash-escapes the characters that can open or close inline markup, including
    ``_`` (emphasis, e.g. ``__pycache__``) and ``~`` (GFM strikethrough). The backslash
    itself is escaped first to avoid double-processing.
    """
    for ch in ("\\", "`", "*", "_", "~", "[", "]"):
        text = text.replace(ch, "\\" + ch)
    return html.escape(text, quote=False)


class MarkdownExporter(BaseExporter):
    """Exporter that writes the structure as a nested Markdown list."""

    extension = "md"

    _GIT_MD_BADGE = {
        "U": "**[U]**",
        "M": "**[M]**",
        "A": "**[A]**",
        "D": "**[D]**",
    }

    def export(self, output_path: str) -> None:
        """Write the structure to *output_path* as a Markdown list.

        Directory names are rendered in bold and filenames as inline code, with any
        enabled metric or Git-status suffixes; deleted files are struck through.

        Args:
            output_path: Path the ``.md`` file is written to.
        """

        def _build_md_tree(
            structure: Directory,
            level: int = 0,
        ) -> list[str]:
            """Return the Markdown lines for *structure* and its descendants.

            Args:
                structure: Directory to render.
                level: Current nesting depth, controlling indentation.

            Returns:
                The rendered lines for this subtree, in display order.
            """
            lines = []
            indent = "    " * level
            for entry in sort_files_by_type(
                structure.files, self.sort_key, structure.git_markers
            ):
                file_icon = get_icon(entry.name, is_dir=False, style=self.icon_style)

                _git_marker_md = (
                    structure.git_markers.get(entry.name, "")
                    if self.show_git_status
                    else ""
                )
                _md_code = _md_inline_code(entry.path)
                if _git_marker_md == "D":
                    _md_display = f"~~{_md_code}~~"
                else:
                    _md_display = _md_code
                _md_git_suffix = (
                    f" {self._GIT_MD_BADGE[_git_marker_md]}"
                    if _git_marker_md in self._GIT_MD_BADGE
                    else ""
                )

                lines.append(
                    f"{indent}- {file_icon} {_md_display}"
                    + format_metrics_suffix(
                        entry.loc, entry.size, entry.mtime, self.metrics
                    )
                    + _md_git_suffix
                )
            for name, content in iter_subdirectories(structure):
                folder_icon = get_icon(
                    name,
                    is_dir=True,
                    style=self.icon_style,
                    is_empty=not has_contents(content),
                )

                metrics = format_dir_metrics(content, self.metrics)
                lines.append(
                    f"{indent}- {folder_icon} **{_md_escape_text(name)}**{metrics}"
                )
                if content.symlink_loop:
                    lines.append(f"{indent}    - ↩ *(symlink loop)*")
                elif not content.max_depth_reached:
                    lines.extend(_build_md_tree(content, level + 1))
            return lines

        root_icon = get_icon(
            self.root_name,
            is_dir=True,
            style=self.icon_style,
            is_empty=not has_contents(self.structure),
        )

        md_content = [
            f"# {root_icon} {_md_escape_text(self.root_name)}"
            + format_dir_metrics(self.structure, self.metrics),
            "",
        ]

        md_content.extend(_build_md_tree(self.structure))
        write_text(output_path, "\n".join(md_content))
