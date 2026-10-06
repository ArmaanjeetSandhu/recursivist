"""Plain-text tree exporter.

Renders the scanned structure as an indented ASCII tree (``├──``/``└──`` connectors) and
writes it to a ``.txt`` file.
"""

from typing import ClassVar

from recursivist._models import Directory
from recursivist.icons import get_icon
from recursivist.metrics import format_dir_metrics, format_metrics_suffix
from recursivist.scanner import has_contents, iter_subdirectories
from recursivist.sorting import sort_files_by_type

from .base import BaseExporter, write_text


class TxtExporter(BaseExporter):
    """Exporter that writes the structure as a plain-text tree."""

    extension = "txt"

    _GIT_TXT_SUFFIX: ClassVar[dict[str, str]] = {
        "U": " [U]",
        "M": " [M]",
        "A": " [A]",
        "D": " [D]",
    }

    def export(self, output_path: str) -> None:
        """Write the structure to *output_path* as a plain-text tree.

        Each entry is drawn with ``├──``/``└──`` branch connectors plus any enabled
        metric or Git-status suffixes.

        Args:
            output_path: Path the ``.txt`` file is written to.
        """

        def _build_txt_tree(
            structure: Directory,
            prefix: str = "",
        ) -> list[str]:
            """Return the text lines for *structure* and its descendants.

            Args:
                structure: Directory to render.
                prefix: Branch-connector prefix carried down from parent levels.

            Returns:
                The rendered lines for this subtree, in display order.
            """
            lines = []
            dir_items = list(iter_subdirectories(structure))
            has_dirs = bool(dir_items)
            file_items = sort_files_by_type(
                structure.files, self.sort_key, structure.git_markers
            )
            for j, entry in enumerate(file_items):
                is_last_file = j == len(file_items) - 1
                is_last_item = is_last_file and not has_dirs
                item_prefix = prefix + ("└── " if is_last_item else "├── ")

                _git_marker = (
                    structure.git_markers.get(entry.name, "")
                    if self.show_git_status
                    else ""
                )
                _git_suffix = (
                    self._GIT_TXT_SUFFIX.get(_git_marker, f" {_git_marker}")
                    if _git_marker
                    else ""
                )

                file_icon = get_icon(entry.name, is_dir=False, style=self.icon_style)
                lines.append(
                    f"{item_prefix}{file_icon} {entry.path}"
                    + format_metrics_suffix(
                        entry.loc, entry.size, entry.mtime, self.metrics
                    )
                    + _git_suffix
                )

            for i, (name, content) in enumerate(dir_items):
                is_last_item = i == len(dir_items) - 1
                item_prefix = prefix + ("└── " if is_last_item else "├── ")
                folder_icon = get_icon(
                    name,
                    is_dir=True,
                    style=self.icon_style,
                    is_empty=not has_contents(content),
                )
                lines.append(
                    f"{item_prefix}{folder_icon} {name}"
                    + format_dir_metrics(content, self.metrics)
                )
                if content.symlink_loop:
                    next_prefix = prefix + ("    " if is_last_item else "│   ")
                    lines.append(f"{next_prefix}└── ↩ (symlink loop)")
                elif not content.max_depth_reached:
                    next_prefix = prefix + ("    " if is_last_item else "│   ")
                    sublines = _build_txt_tree(content, next_prefix)
                    lines.extend(sublines)
            return lines

        root_icon = get_icon(
            self.root_name,
            is_dir=True,
            style=self.icon_style,
            is_empty=not has_contents(self.structure),
        )
        root_label = f"{root_icon} {self.root_name}" + format_dir_metrics(
            self.structure, self.metrics
        )

        tree_lines = [root_label]
        tree_lines.extend(_build_txt_tree(self.structure))
        write_text(output_path, "\n".join(tree_lines))
