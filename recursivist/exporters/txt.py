"""Plain-text tree exporter.

Renders the scanned structure as an indented ASCII tree (``├──``/``└──``
connectors) and writes it to a ``.txt`` file.
"""

import logging
import os
from typing import Any

from recursivist.icons import get_icon
from recursivist.metrics import format_metrics_suffix
from recursivist.sorting import sort_files_by_type

from .base import BaseExporter

logger = logging.getLogger(__name__)


class TxtExporter(BaseExporter):
    """Exporter that writes the structure as a plain-text tree."""

    _GIT_MARKER_LABELS = {"U": "[U]", "M": "[M]", "A": "[A]", "D": "[D]"}
    _GIT_TXT_SUFFIX = {"U": " [U]", "M": " [M]", "A": " [A]", "D": " [D]"}

    def export(self, output_path: str) -> None:
        """Write the structure to *output_path* as a plain-text tree.

        Each entry is drawn with ``├──``/``└──`` branch connectors plus any
        enabled metric or Git-status suffixes.

        Args:
            output_path: Path the ``.txt`` file is written to.

        Raises:
            Exception: Re-raised if writing the output file fails (after the
                error is logged).
        """

        def _build_txt_tree(
            structure: dict[str, Any],
            prefix: str = "",
            path_prefix: str = "",
        ) -> list[str]:
            """Return the text lines for *structure* and its descendants.

            Args:
                structure: Directory-structure dict to render.
                prefix: Branch-connector prefix carried down from parent
                    levels.
                path_prefix: Accumulated path used when full paths are shown.

            Returns:
                The rendered lines for this subtree, in display order.
            """
            lines = []
            special_keys = {
                "_files",
                "_max_depth_reached",
                "_loc",
                "_size",
                "_mtime",
                "_git_markers",
            }
            dir_items = sorted(
                (name, content)
                for name, content in structure.items()
                if name not in special_keys
            )
            has_dirs = bool(dir_items)
            if "_files" in structure:
                file_items = sort_files_by_type(
                    structure["_files"],
                    self.sort_by_loc,
                    self.sort_by_size,
                    self.sort_by_mtime,
                    self.sort_by_similarity,
                )
                for j, entry in enumerate(file_items):
                    is_last_file = j == len(file_items) - 1
                    is_last_item = is_last_file and not has_dirs
                    item_prefix = prefix + ("└── " if is_last_item else "├── ")

                    _git_markers = structure.get("_git_markers", {})
                    _git_marker = (
                        _git_markers.get(entry.name, "") if self.show_git_status else ""
                    )
                    _git_suffix = (
                        self._GIT_TXT_SUFFIX.get(_git_marker, f" {_git_marker}")
                        if _git_marker
                        else ""
                    )

                    file_icon = get_icon(
                        entry.name, is_dir=False, style=self.icon_style
                    )
                    display_path = (
                        entry.path
                        if (
                            self.show_full_path
                            or self.sort_by_loc
                            or self.sort_by_size
                            or self.sort_by_mtime
                        )
                        else entry.name
                    )
                    lines.append(
                        f"{item_prefix}{file_icon} {display_path}"
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

            for i, (name, content) in enumerate(dir_items):
                is_last_item = i == len(dir_items) - 1
                item_prefix = prefix + ("└── " if is_last_item else "├── ")
                next_path = os.path.join(path_prefix, name) if path_prefix else name
                folder_icon = get_icon(name, is_dir=True, style=self.icon_style)
                if isinstance(content, dict):
                    lines.append(
                        f"{item_prefix}{folder_icon} {name}"
                        + format_metrics_suffix(
                            content.get("_loc", 0),
                            content.get("_size", 0),
                            content.get("_mtime", 0.0),
                            sort_by_loc=self.sort_by_loc and "_loc" in content,
                            sort_by_size=self.sort_by_size and "_size" in content,
                            sort_by_mtime=self.sort_by_mtime and "_mtime" in content,
                        )
                    )
                    if content.get("_max_depth_reached"):
                        next_prefix = prefix + ("    " if is_last_item else "│   ")
                        lines.append(f"{next_prefix}└── ⋯ (max depth reached)")
                    else:
                        next_prefix = prefix + ("    " if is_last_item else "│   ")
                        sublines = _build_txt_tree(content, next_prefix, next_path)
                        lines.extend(sublines)
                else:
                    lines.append(f"{item_prefix}{folder_icon} {name}")
            return lines

        root_icon = get_icon(self.root_name, is_dir=True, style=self.icon_style)
        root_label = f"{root_icon} {self.root_name}" + format_metrics_suffix(
            self.structure.get("_loc", 0),
            self.structure.get("_size", 0),
            self.structure.get("_mtime", 0.0),
            sort_by_loc=self.sort_by_loc and "_loc" in self.structure,
            sort_by_size=self.sort_by_size and "_size" in self.structure,
            sort_by_mtime=self.sort_by_mtime and "_mtime" in self.structure,
        )

        tree_lines = [root_label]
        tree_lines.extend(
            _build_txt_tree(
                self.structure, "", self.root_name if self.show_full_path else ""
            )
        )
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(tree_lines))
        except Exception as e:
            logger.exception(f"Error exporting to TXT: {e}")
            raise
