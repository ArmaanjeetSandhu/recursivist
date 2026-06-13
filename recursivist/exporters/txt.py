import logging
import os
from typing import Any

from recursivist.core import format_size, format_timestamp
from recursivist.icons import get_icon

from .base import BaseExporter, sort_files_by_type

logger = logging.getLogger(__name__)


class TxtExporter(BaseExporter):
    _GIT_MARKER_LABELS = {"U": "[U]", "M": "[M]", "A": "[A]", "D": "[D]"}
    _GIT_TXT_SUFFIX = {"U": " [U]", "M": " [M]", "A": " [A]", "D": " [D]"}

    def export(self, output_path: str) -> None:
        def _build_txt_tree(
            structure: dict[str, Any],
            prefix: str = "",
            path_prefix: str = "",
        ) -> list[str]:
            lines = []
            items = sorted(structure.items())
            for i, (name, content) in enumerate(items):
                if name == "_files":
                    file_items = sort_files_by_type(
                        content, self.sort_by_loc, self.sort_by_size, self.sort_by_mtime
                    )
                    for j, file_item in enumerate(file_items):
                        is_last_file = j == len(file_items) - 1
                        is_last_item = is_last_file and i == len(items) - 1
                        item_prefix = prefix + ("└── " if is_last_item else "├── ")

                        if isinstance(file_item, tuple) and len(file_item) > 0:
                            _fname = file_item[0]
                        elif isinstance(file_item, str):
                            _fname = file_item
                        else:
                            _fname = "unknown"
                        _git_markers = structure.get("_git_markers", {})
                        _git_marker = (
                            _git_markers.get(_fname, "") if self.show_git_status else ""
                        )
                        _git_suffix = (
                            f" {self._GIT_TXT_SUFFIX.get(_git_marker, _git_marker)}"
                            if _git_marker
                            else ""
                        )

                        file_icon = get_icon(
                            _fname, is_dir=False, style=self.icon_style
                        )

                        if (
                            self.sort_by_loc
                            and self.sort_by_size
                            and self.sort_by_mtime
                            and isinstance(file_item, tuple)
                            and len(file_item) > 4
                        ):
                            _, display_path, loc, size, mtime = file_item
                            lines.append(
                                f"{item_prefix}{file_icon} {display_path} ({loc} lines, {format_size(size)}, {format_timestamp(mtime)}){_git_suffix}"
                            )
                        elif (
                            self.sort_by_loc
                            and self.sort_by_mtime
                            and isinstance(file_item, tuple)
                            and len(file_item) > 4
                        ):
                            _, display_path, loc, _, mtime = file_item
                            lines.append(
                                f"{item_prefix}{file_icon} {display_path} ({loc} lines, {format_timestamp(mtime)}){_git_suffix}"
                            )
                        elif (
                            self.sort_by_size
                            and self.sort_by_mtime
                            and isinstance(file_item, tuple)
                            and len(file_item) > 4
                        ):
                            _, display_path, _, size, mtime = file_item
                            lines.append(
                                f"{item_prefix}{file_icon} {display_path} ({format_size(size)}, {format_timestamp(mtime)}){_git_suffix}"
                            )
                        elif (
                            self.sort_by_loc
                            and self.sort_by_size
                            and isinstance(file_item, tuple)
                            and len(file_item) > 3
                        ):
                            if len(file_item) > 4:
                                _, display_path, loc, size, _ = file_item
                            else:
                                _, display_path, loc, size = file_item
                            lines.append(
                                f"{item_prefix}{file_icon} {display_path} ({loc} lines, {format_size(size)}){_git_suffix}"
                            )
                        elif (
                            self.sort_by_mtime
                            and isinstance(file_item, tuple)
                            and len(file_item) > 2
                        ):
                            if len(file_item) > 4:
                                _, display_path, _, _, mtime = file_item
                            elif len(file_item) > 3:
                                _, display_path, _, mtime = file_item
                            else:
                                _, display_path, mtime = file_item
                            lines.append(
                                f"{item_prefix}{file_icon} {display_path} ({format_timestamp(mtime)}){_git_suffix}"
                            )
                        elif (
                            self.sort_by_size
                            and isinstance(file_item, tuple)
                            and len(file_item) > 2
                        ):
                            if len(file_item) > 4:
                                _, display_path, _, size, _ = file_item
                            elif len(file_item) > 3:
                                _, display_path, _, size = file_item
                            else:
                                _, display_path, size = file_item
                            lines.append(
                                f"{item_prefix}{file_icon} {display_path} ({format_size(size)}){_git_suffix}"
                            )
                        elif (
                            self.sort_by_loc
                            and isinstance(file_item, tuple)
                            and len(file_item) > 2
                        ):
                            if len(file_item) > 4:
                                _, display_path, loc, _, _ = file_item
                            elif len(file_item) > 3:
                                _, display_path, loc, _ = file_item
                            else:
                                _, display_path, loc = file_item
                            lines.append(
                                f"{item_prefix}{file_icon} {display_path} ({loc} lines){_git_suffix}"
                            )
                        elif self.show_full_path and isinstance(file_item, tuple):
                            if len(file_item) > 4:
                                _, full_path, _, _, _ = file_item
                            elif len(file_item) > 3:
                                _, full_path, _, _ = file_item
                            elif len(file_item) > 2:
                                _, full_path, _ = file_item
                            elif len(file_item) > 1:
                                _, full_path = file_item
                            else:
                                full_path = (
                                    file_item[0] if len(file_item) > 0 else "unknown"
                                )
                            lines.append(
                                f"{item_prefix}{file_icon} {full_path}{_git_suffix}"
                            )
                        else:
                            if isinstance(file_item, tuple):
                                file_name = (
                                    file_item[0] if len(file_item) > 0 else "unknown"
                                )
                            else:
                                file_name = file_item
                            lines.append(
                                f"{item_prefix}{file_icon} {file_name}{_git_suffix}"
                            )
                elif (
                    name == "_loc"
                    or name == "_size"
                    or name == "_mtime"
                    or name == "_max_depth_reached"
                    or name == "_git_markers"
                ):
                    continue
                else:
                    is_last_dir = True
                    for j in range(i + 1, len(items)):
                        next_name, _ = items[j]
                        if next_name not in [
                            "_files",
                            "_max_depth_reached",
                            "_loc",
                            "_size",
                            "_mtime",
                            "_git_markers",
                        ]:
                            is_last_dir = False
                            break
                    is_last_item = is_last_dir and (
                        i == len(items) - 1
                        or all(
                            key
                            in [
                                "_files",
                                "_max_depth_reached",
                                "_loc",
                                "_size",
                                "_mtime",
                                "_git_markers",
                            ]
                            for key, _ in items[i + 1 :]
                        )
                    )
                    item_prefix = prefix + ("└── " if is_last_item else "├── ")
                    next_path = os.path.join(path_prefix, name) if path_prefix else name
                    folder_icon = get_icon(name, is_dir=True, style=self.icon_style)
                    if isinstance(content, dict):
                        if (
                            self.sort_by_loc
                            and self.sort_by_size
                            and self.sort_by_mtime
                            and "_loc" in content
                            and "_size" in content
                            and "_mtime" in content
                        ):
                            folder_loc = content["_loc"]
                            folder_size = content["_size"]
                            folder_mtime = content["_mtime"]
                            lines.append(
                                f"{item_prefix}{folder_icon} {name} ({folder_loc} lines, {format_size(folder_size)}, {format_timestamp(folder_mtime)})"
                            )
                        elif (
                            self.sort_by_loc
                            and self.sort_by_size
                            and "_loc" in content
                            and "_size" in content
                        ):
                            folder_loc = content["_loc"]
                            folder_size = content["_size"]
                            lines.append(
                                f"{item_prefix}{folder_icon} {name} ({folder_loc} lines, {format_size(folder_size)})"
                            )
                        elif (
                            self.sort_by_loc
                            and self.sort_by_mtime
                            and "_loc" in content
                            and "_mtime" in content
                        ):
                            folder_loc = content["_loc"]
                            folder_mtime = content["_mtime"]
                            lines.append(
                                f"{item_prefix}{folder_icon} {name} ({folder_loc} lines, {format_timestamp(folder_mtime)})"
                            )
                        elif (
                            self.sort_by_size
                            and self.sort_by_mtime
                            and "_size" in content
                            and "_mtime" in content
                        ):
                            folder_size = content["_size"]
                            folder_mtime = content["_mtime"]
                            lines.append(
                                f"{item_prefix}{folder_icon} {name} ({format_size(folder_size)}, {format_timestamp(folder_mtime)})"
                            )
                        elif self.sort_by_loc and "_loc" in content:
                            folder_loc = content["_loc"]
                            lines.append(
                                f"{item_prefix}{folder_icon} {name} ({folder_loc} lines)"
                            )
                        elif self.sort_by_size and "_size" in content:
                            folder_size = content["_size"]
                            lines.append(
                                f"{item_prefix}{folder_icon} {name} ({format_size(folder_size)})"
                            )
                        elif self.sort_by_mtime and "_mtime" in content:
                            folder_mtime = content["_mtime"]
                            lines.append(
                                f"{item_prefix}{folder_icon} {name} ({format_timestamp(folder_mtime)})"
                            )
                        else:
                            lines.append(f"{item_prefix}{folder_icon} {name}")
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
        root_label = f"{root_icon} {self.root_name}"
        if (
            self.sort_by_loc
            and self.sort_by_size
            and self.sort_by_mtime
            and "_loc" in self.structure
            and "_size" in self.structure
            and "_mtime" in self.structure
        ):
            root_label = f"{root_icon} {self.root_name} ({self.structure['_loc']} lines, {format_size(self.structure['_size'])}, {format_timestamp(self.structure['_mtime'])})"
        elif (
            self.sort_by_loc
            and self.sort_by_size
            and "_loc" in self.structure
            and "_size" in self.structure
        ):
            root_label = f"{root_icon} {self.root_name} ({self.structure['_loc']} lines, {format_size(self.structure['_size'])})"
        elif (
            self.sort_by_loc
            and self.sort_by_mtime
            and "_loc" in self.structure
            and "_mtime" in self.structure
        ):
            root_label = f"{root_icon} {self.root_name} ({self.structure['_loc']} lines, {format_timestamp(self.structure['_mtime'])})"
        elif (
            self.sort_by_size
            and self.sort_by_mtime
            and "_size" in self.structure
            and "_mtime" in self.structure
        ):
            root_label = f"{root_icon} {self.root_name} ({format_size(self.structure['_size'])}, {format_timestamp(self.structure['_mtime'])})"
        elif self.sort_by_loc and "_loc" in self.structure:
            root_label = (
                f"{root_icon} {self.root_name} ({self.structure['_loc']} lines)"
            )
        elif self.sort_by_size and "_size" in self.structure:
            root_label = (
                f"{root_icon} {self.root_name} ({format_size(self.structure['_size'])})"
            )
        elif self.sort_by_mtime and "_mtime" in self.structure:
            root_label = f"{root_icon} {self.root_name} ({format_timestamp(self.structure['_mtime'])})"

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
