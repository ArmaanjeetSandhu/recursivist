"""
Export functionality for the Recursivist directory visualization tool.

This module handles the export of directory structures to various formats through the DirectoryExporter class, which provides a unified interface for transforming directory structures into different output formats.

Supported export formats:
- TXT: ASCII tree representation
- JSON: Structured data for programmatic use
- HTML: Interactive web page with styling
- Markdown: Clean representation for documentation
- JSX: React component for web integration

Each format maintains consistent styling and organization, with support for
showing lines of code, file sizes, and modification times.
"""

import html
import json
import logging
import os
from collections.abc import Sequence
from typing import Any, Optional, Union

from recursivist.core import format_size, format_timestamp, generate_color_for_extension
from recursivist.jsx_export import generate_jsx_component

logger = logging.getLogger(__name__)


def sort_files_by_type(
    files: Sequence[
        Union[
            str,
            tuple[str, str],
            tuple[str, str, int],
            tuple[str, str, int, int],
            tuple[str, str, int, int, float],
        ]
    ],
    sort_by_loc: bool = False,
    sort_by_size: bool = False,
    sort_by_mtime: bool = False,
) -> list[
    Union[
        str,
        tuple[str, str],
        tuple[str, str, int],
        tuple[str, str, int, int],
        tuple[str, str, int, int, float],
    ]
]:
    """Sort files by extension and then by name, or by LOC/size/mtime if requested."""
    if not files:
        return []
    has_loc = any(isinstance(item, tuple) and len(item) > 2 for item in files)
    has_size = any(isinstance(item, tuple) and len(item) > 3 for item in files)
    has_mtime = any(isinstance(item, tuple) and len(item) > 4 for item in files)
    has_simple_size = sort_by_size and not sort_by_loc and has_loc
    has_simple_mtime = (
        sort_by_mtime and not sort_by_loc and not sort_by_size and (has_loc or has_size)
    )

    def get_size(
        item: Union[
            str,
            tuple[str, str],
            tuple[str, str, int],
            tuple[str, str, int, int],
            tuple[str, str, int, int, float],
        ],
    ) -> int:
        if not isinstance(item, tuple):
            return 0
        if len(item) > 3:
            if sort_by_loc and sort_by_size:
                return item[3]
            elif sort_by_size and not sort_by_loc:
                return item[3]
        elif len(item) == 3 and sort_by_size:
            return item[2]
        return 0

    def get_loc(
        item: Union[
            str,
            tuple[str, str],
            tuple[str, str, int],
            tuple[str, str, int, int],
            tuple[str, str, int, int, float],
        ],
    ) -> int:
        if not isinstance(item, tuple) or len(item) <= 2:
            return 0
        return item[2] if sort_by_loc else 0

    def get_mtime(
        item: Union[
            str,
            tuple[str, str],
            tuple[str, str, int],
            tuple[str, str, int, int],
            tuple[str, str, int, int, float],
        ],
    ) -> float:
        if not isinstance(item, tuple):
            return 0
        if len(item) > 4:
            return item[4]
        elif len(item) > 3 and (
            (sort_by_loc and sort_by_mtime and not sort_by_size)
            or (sort_by_size and sort_by_mtime and not sort_by_loc)
        ):
            return item[3]
        elif len(item) > 2 and sort_by_mtime and not sort_by_loc and not sort_by_size:
            return item[2]
        return 0

    if sort_by_loc and sort_by_size and sort_by_mtime and has_mtime:
        return sorted(files, key=lambda f: (-get_loc(f), -get_size(f), -get_mtime(f)))
    elif sort_by_loc and sort_by_size and (has_size or has_simple_size) and has_loc:
        return sorted(files, key=lambda f: (-get_loc(f), -get_size(f)))
    elif sort_by_loc and sort_by_mtime and has_mtime:
        return sorted(files, key=lambda f: (-get_loc(f), -get_mtime(f)))
    elif sort_by_size and sort_by_mtime and has_mtime:
        return sorted(files, key=lambda f: (-get_size(f), -get_mtime(f)))
    elif sort_by_loc and has_loc:
        return sorted(files, key=lambda f: -get_loc(f))
    elif sort_by_size and (has_size or has_simple_size):
        return sorted(files, key=lambda f: -get_size(f))
    elif sort_by_mtime and (has_mtime or has_simple_mtime):
        return sorted(files, key=lambda f: -get_mtime(f))

    def get_filename(
        item: Union[
            str,
            tuple[str, str],
            tuple[str, str, int],
            tuple[str, str, int, int],
            tuple[str, str, int, int, float],
        ],
    ) -> str:
        if isinstance(item, tuple):
            return item[0]
        return item

    return sorted(
        files,
        key=lambda f: (
            os.path.splitext(get_filename(f))[1].lower(),
            get_filename(f).lower(),
        ),
    )


class DirectoryExporter:
    """Export directory structures to various formats.

    Provides a unified interface for transforming directory structures into different output formats with consistent styling and organization.

    Supported formats:
    - TXT: ASCII tree representation
    - JSON: Structured data for programmatic use
    - HTML: Interactive web page with styling
    - Markdown: Clean representation for documentation
    - JSX: React component for web integration

    Each format maintains consistent features for:
    - Directory and file hierarchical representation
    - Optional statistics (lines of code, sizes, modification times)
    - Path display options (full or relative paths)
    """

    def __init__(
        self,
        structure: dict[str, Any],
        root_name: str,
        base_path: Optional[str] = None,
        sort_by_loc: bool = False,
        sort_by_size: bool = False,
        sort_by_mtime: bool = False,
        show_git_status: bool = False,
    ):
        """Initialize the exporter with directory structure and root name.

        Args:
            structure: The directory structure dictionary
            root_name: Name of the root directory
            base_path: Base path for full path display (if None, only show filenames)
            sort_by_loc: Whether to include lines of code counts in exports
            sort_by_size: Whether to include file size information in exports
            sort_by_mtime: Whether to include modification time information in exports
            show_git_status: Whether to annotate files with Git status markers
        """

        self.structure = structure
        self.root_name = root_name
        self.base_path = base_path
        self.show_full_path = base_path is not None
        self.sort_by_loc = sort_by_loc
        self.sort_by_size = sort_by_size
        self.sort_by_mtime = sort_by_mtime
        self.show_git_status = show_git_status

    _GIT_MARKER_LABELS = {"U": "[U]", "M": "[M]", "A": "[A]", "D": "[D]"}
    _GIT_TXT_SUFFIX = {"U": " [U]", "M": " [M]", "A": " [A]", "D": " [D]"}

    def to_txt(self, output_path: str) -> None:
        """Export directory structure to a text file with ASCII tree representation.

        Creates a text file containing an ASCII tree representation of the directory structure using standard box-drawing characters and indentation.

        Args:
            output_path: Path where the txt file will be saved
        """

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

                        _fname = (
                            file_item[0]
                            if isinstance(file_item, tuple) and len(file_item) > 0
                            else (
                                file_item if isinstance(file_item, str) else "unknown"
                            )
                        )
                        _git_markers = structure.get("_git_markers", {})
                        _git_marker = (
                            _git_markers.get(_fname, "") if self.show_git_status else ""
                        )
                        _git_suffix = (
                            f" {self._GIT_TXT_SUFFIX.get(_git_marker, _git_marker)}"
                            if _git_marker
                            else ""
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
                                f"{item_prefix}📄 {display_path} ({loc} lines, {format_size(size)}, {format_timestamp(mtime)}){_git_suffix}"
                            )
                        elif (
                            self.sort_by_loc
                            and self.sort_by_mtime
                            and isinstance(file_item, tuple)
                            and len(file_item) > 4
                        ):
                            _, display_path, loc, _, mtime = file_item
                            lines.append(
                                f"{item_prefix}📄 {display_path} ({loc} lines, {format_timestamp(mtime)}){_git_suffix}"
                            )
                        elif (
                            self.sort_by_size
                            and self.sort_by_mtime
                            and isinstance(file_item, tuple)
                            and len(file_item) > 4
                        ):
                            _, display_path, _, size, mtime = file_item
                            lines.append(
                                f"{item_prefix}📄 {display_path} ({format_size(size)}, {format_timestamp(mtime)}){_git_suffix}"
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
                                f"{item_prefix}📄 {display_path} ({loc} lines, {format_size(size)}){_git_suffix}"
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
                                f"{item_prefix}📄 {display_path} ({format_timestamp(mtime)}){_git_suffix}"
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
                                f"{item_prefix}📄 {display_path} ({format_size(size)}){_git_suffix}"
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
                                f"{item_prefix}📄 {display_path} ({loc} lines){_git_suffix}"
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
                            lines.append(f"{item_prefix}📄 {full_path}{_git_suffix}")
                        else:
                            if isinstance(file_item, tuple):
                                file_name = (
                                    file_item[0] if len(file_item) > 0 else "unknown"
                                )
                            else:
                                file_name = file_item
                            lines.append(f"{item_prefix}📄 {file_name}{_git_suffix}")
                        if not is_last_item:
                            next_prefix = prefix + "│   "
                        else:
                            next_prefix = prefix + "    "
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
                                f"{item_prefix}📁 {name} ({folder_loc} lines, {format_size(folder_size)}, {format_timestamp(folder_mtime)})"
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
                                f"{item_prefix}📁 {name} ({folder_loc} lines, {format_size(folder_size)})"
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
                                f"{item_prefix}📁 {name} ({folder_loc} lines, {format_timestamp(folder_mtime)})"
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
                                f"{item_prefix}📁 {name} ({format_size(folder_size)}, {format_timestamp(folder_mtime)})"
                            )
                        elif self.sort_by_loc and "_loc" in content:
                            folder_loc = content["_loc"]
                            lines.append(f"{item_prefix}📁 {name} ({folder_loc} lines)")
                        elif self.sort_by_size and "_size" in content:
                            folder_size = content["_size"]
                            lines.append(
                                f"{item_prefix}📁 {name} ({format_size(folder_size)})"
                            )
                        elif self.sort_by_mtime and "_mtime" in content:
                            folder_mtime = content["_mtime"]
                            lines.append(
                                f"{item_prefix}📁 {name} ({format_timestamp(folder_mtime)})"
                            )
                        else:
                            lines.append(f"{item_prefix}📁 {name}")
                        if content.get("_max_depth_reached"):
                            next_prefix = prefix + ("    " if is_last_item else "│   ")
                            lines.append(f"{next_prefix}└── ⋯ (max depth reached)")
                        else:
                            next_prefix = prefix + ("    " if is_last_item else "│   ")
                            sublines = _build_txt_tree(content, next_prefix, next_path)
                            lines.extend(sublines)
                    else:
                        lines.append(f"{item_prefix}📁 {name}")
            return lines

        root_label = f"📂 {self.root_name}"
        if (
            self.sort_by_loc
            and self.sort_by_size
            and self.sort_by_mtime
            and "_loc" in self.structure
            and "_size" in self.structure
            and "_mtime" in self.structure
        ):
            root_label = f"📂 {self.root_name} ({self.structure['_loc']} lines, {format_size(self.structure['_size'])}, {format_timestamp(self.structure['_mtime'])})"
        elif (
            self.sort_by_loc
            and self.sort_by_size
            and "_loc" in self.structure
            and "_size" in self.structure
        ):
            root_label = f"📂 {self.root_name} ({self.structure['_loc']} lines, {format_size(self.structure['_size'])})"
        elif (
            self.sort_by_loc
            and self.sort_by_mtime
            and "_loc" in self.structure
            and "_mtime" in self.structure
        ):
            root_label = f"📂 {self.root_name} ({self.structure['_loc']} lines, {format_timestamp(self.structure['_mtime'])})"
        elif (
            self.sort_by_size
            and self.sort_by_mtime
            and "_size" in self.structure
            and "_mtime" in self.structure
        ):
            root_label = f"📂 {self.root_name} ({format_size(self.structure['_size'])}, {format_timestamp(self.structure['_mtime'])})"
        elif self.sort_by_loc and "_loc" in self.structure:
            root_label = f"📂 {self.root_name} ({self.structure['_loc']} lines)"
        elif self.sort_by_size and "_size" in self.structure:
            root_label = f"📂 {self.root_name} ({format_size(self.structure['_size'])})"
        elif self.sort_by_mtime and "_mtime" in self.structure:
            root_label = (
                f"📂 {self.root_name} ({format_timestamp(self.structure['_mtime'])})"
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
            logger.error(f"Error exporting to TXT: {e}")
            raise

    def to_json(self, output_path: str) -> None:
        """Export directory structure to a JSON file.

        Creates a JSON file containing the directory structure with options for including full paths, LOC counts, file sizes, and modification times. The JSON structure includes a root name and the hierarchical structure of directories and files.

        Args:
            output_path: Path where the JSON file will be saved
        """

        if (
            self.show_full_path
            or self.sort_by_loc
            or self.sort_by_size
            or self.sort_by_mtime
        ):

            def convert_structure_for_json(structure: dict[str, Any]) -> dict[str, Any]:
                result: dict[str, Any] = {}
                _git_markers_here = structure.get("_git_markers", {})
                for k, v in structure.items():
                    if k == "_files":
                        result[k] = []
                        for item in v:
                            if not isinstance(item, tuple):
                                if self.show_git_status:
                                    _gs = _git_markers_here.get(item, "")
                                    entry: Any = {"name": item}
                                    if _gs:
                                        entry["git_status"] = _gs
                                    result[k].append(entry)
                                else:
                                    result[k].append(item)
                                continue

                            file_name = "unknown"
                            full_path = ""
                            loc = 0
                            size = 0
                            mtime = 0

                            if len(item) > 0:
                                file_name = item[0]
                            if len(item) > 1:
                                full_path = item[1]

                            _git_status = (
                                _git_markers_here.get(file_name, "")
                                if self.show_git_status
                                else ""
                            )

                            def _maybe_git(
                                d: dict[str, Any], _gs: str = _git_status
                            ) -> dict[str, Any]:
                                if _gs:
                                    d["git_status"] = _gs
                                return d

                            if (
                                self.sort_by_loc
                                and self.sort_by_size
                                and self.sort_by_mtime
                                and len(item) > 4
                            ):
                                loc = item[2]
                                size = item[3]
                                mtime = item[4]
                                result[k].append(
                                    _maybe_git(
                                        {
                                            "name": file_name,
                                            "path": full_path,
                                            "loc": loc,
                                            "size": size,
                                            "size_formatted": format_size(size),
                                            "mtime": mtime,
                                            "mtime_formatted": format_timestamp(mtime),
                                        }
                                    )
                                )
                            elif (
                                self.sort_by_loc
                                and self.sort_by_mtime
                                and len(item) > 4
                            ):
                                loc = item[2]
                                mtime = item[4]
                                result[k].append(
                                    _maybe_git(
                                        {
                                            "name": file_name,
                                            "path": full_path,
                                            "loc": loc,
                                            "mtime": mtime,
                                            "mtime_formatted": format_timestamp(mtime),
                                        }
                                    )
                                )
                            elif (
                                self.sort_by_size
                                and self.sort_by_mtime
                                and len(item) > 4
                            ):
                                size = item[3]
                                mtime = item[4]
                                result[k].append(
                                    _maybe_git(
                                        {
                                            "name": file_name,
                                            "path": full_path,
                                            "size": size,
                                            "size_formatted": format_size(size),
                                            "mtime": mtime,
                                            "mtime_formatted": format_timestamp(mtime),
                                        }
                                    )
                                )
                            elif (
                                self.sort_by_loc and self.sort_by_size and len(item) > 3
                            ):
                                loc = item[2] if len(item) > 2 else 0
                                size = item[3] if len(item) > 3 else 0
                                result[k].append(
                                    _maybe_git(
                                        {
                                            "name": file_name,
                                            "path": full_path,
                                            "loc": loc,
                                            "size": size,
                                            "size_formatted": format_size(size),
                                        }
                                    )
                                )
                            elif self.sort_by_mtime and len(item) > 2:
                                mtime = item[2] if len(item) > 2 else 0
                                result[k].append(
                                    _maybe_git(
                                        {
                                            "name": file_name,
                                            "path": full_path,
                                            "mtime": mtime,
                                            "mtime_formatted": format_timestamp(mtime),
                                        }
                                    )
                                )
                            elif self.sort_by_size and len(item) > 2:
                                size = item[2] if len(item) > 2 else 0
                                result[k].append(
                                    _maybe_git(
                                        {
                                            "name": file_name,
                                            "path": full_path,
                                            "size": size,
                                            "size_formatted": format_size(size),
                                        }
                                    )
                                )
                            elif self.sort_by_loc and len(item) > 2:
                                loc = item[2] if len(item) > 2 else 0
                                result[k].append(
                                    _maybe_git(
                                        {
                                            "name": file_name,
                                            "path": full_path,
                                            "loc": loc,
                                        }
                                    )
                                )
                            elif self.show_full_path and len(item) > 1:
                                result[k].append(
                                    _maybe_git({"name": file_name, "path": full_path})
                                )
                            else:
                                if _git_status:
                                    result[k].append(
                                        {"name": file_name, "git_status": _git_status}
                                    )
                                else:
                                    result[k].append(file_name)
                    elif k == "_loc":
                        if self.sort_by_loc:
                            result[k] = v
                    elif k == "_size":
                        if self.sort_by_size:
                            result[k] = v
                            result["_size_formatted"] = format_size(v)
                    elif k == "_mtime":
                        if self.sort_by_mtime:
                            result[k] = v
                            result["_mtime_formatted"] = format_timestamp(v)
                    elif k == "_git_markers":
                        pass
                    elif k == "_max_depth_reached":
                        result[k] = v
                    elif isinstance(v, dict):
                        result[k] = convert_structure_for_json(v)
                    else:
                        result[k] = v
                return result

            export_structure = convert_structure_for_json(self.structure)
        else:
            export_structure = self.structure
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "root": self.root_name,
                        "structure": export_structure,
                        "show_loc": self.sort_by_loc,
                        "show_size": self.sort_by_size,
                        "show_mtime": self.sort_by_mtime,
                        "show_git_status": self.show_git_status,
                    },
                    f,
                    indent=2,
                )
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
            raise

    def to_html(self, output_path: str) -> None:
        """Export directory structure to an HTML file.

        Creates a standalone HTML file with a styled representation of the directory structure using nested unordered lists with CSS styling for colors and indentation.

        Args:
            output_path: Path where the HTML file will be saved
        """

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
                    display_path = "unknown"
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
                            f'<li class="file" style="{_file_style}">📄 {_name_open}{html.escape(display_path)}{_name_close} ({loc} lines, {format_size(size)}, {format_timestamp(mtime)}){_git_badge}</li>'
                        )
                    elif self.sort_by_loc and self.sort_by_mtime:
                        html_content.append(
                            f'<li class="file" style="{_file_style}">📄 {_name_open}{html.escape(display_path)}{_name_close} ({loc} lines, {format_timestamp(mtime)}){_git_badge}</li>'
                        )
                    elif self.sort_by_size and self.sort_by_mtime:
                        html_content.append(
                            f'<li class="file" style="{_file_style}">📄 {_name_open}{html.escape(display_path)}{_name_close} ({format_size(size)}, {format_timestamp(mtime)}){_git_badge}</li>'
                        )
                    elif self.sort_by_loc and self.sort_by_size:
                        html_content.append(
                            f'<li class="file" style="{_file_style}">📄 {_name_open}{html.escape(display_path)}{_name_close} ({loc} lines, {format_size(size)}){_git_badge}</li>'
                        )
                    elif self.sort_by_mtime:
                        html_content.append(
                            f'<li class="file" style="{_file_style}">📄 {_name_open}{html.escape(display_path)}{_name_close} ({format_timestamp(mtime)}){_git_badge}</li>'
                        )
                    elif self.sort_by_size:
                        html_content.append(
                            f'<li class="file" style="{_file_style}">📄 {_name_open}{html.escape(display_path)}{_name_close} ({format_size(size)}){_git_badge}</li>'
                        )
                    elif self.sort_by_loc:
                        html_content.append(
                            f'<li class="file" style="{_file_style}">📄 {_name_open}{html.escape(display_path)}{_name_close} ({loc} lines){_git_badge}</li>'
                        )
                    else:
                        html_content.append(
                            f'<li class="file" style="{_file_style}">📄 {_name_open}{html.escape(display_path)}{_name_close}{_git_badge}</li>'
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
                        f'<li class="directory">📁 <span class="dir-name">{html.escape(name)}</span> '
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
                        f'<li class="directory">📁 <span class="dir-name">{html.escape(name)}</span> '
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
                        f'<li class="directory">📁 <span class="dir-name">{html.escape(name)}</span> '
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
                        f'<li class="directory">📁 <span class="dir-name">{html.escape(name)}</span> '
                        f'<span class="metric-count">({format_size(size_count)}, {format_timestamp(mtime_count)})</span>'
                    )
                elif (
                    self.sort_by_loc and isinstance(content, dict) and "_loc" in content
                ):
                    loc_count = content["_loc"]
                    html_content.append(
                        f'<li class="directory">📁 <span class="dir-name">{html.escape(name)}</span> '
                        f'<span class="loc-count">({loc_count} lines)</span>'
                    )
                elif (
                    self.sort_by_size
                    and isinstance(content, dict)
                    and "_size" in content
                ):
                    size_count = content["_size"]
                    html_content.append(
                        f'<li class="directory">📁 <span class="dir-name">{html.escape(name)}</span> '
                        f'<span class="size-count">({format_size(size_count)})</span>'
                    )
                elif (
                    self.sort_by_mtime
                    and isinstance(content, dict)
                    and "_mtime" in content
                ):
                    mtime_count = content["_mtime"]
                    html_content.append(
                        f'<li class="directory">📁 <span class="dir-name">{html.escape(name)}</span> '
                        f'<span class="mtime-count">({format_timestamp(mtime_count)})</span>'
                    )
                else:
                    html_content.append(
                        f'<li class="directory">📁 <span class="dir-name">{html.escape(name)}</span>'
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

        title = f"📂 {html.escape(self.root_name)}"
        if (
            self.sort_by_loc
            and self.sort_by_size
            and self.sort_by_mtime
            and "_loc" in self.structure
            and "_size" in self.structure
            and "_mtime" in self.structure
        ):
            title = f"📂 {html.escape(self.root_name)} ({self.structure['_loc']} lines, {format_size(self.structure['_size'])}, {format_timestamp(self.structure['_mtime'])})"
        elif (
            self.sort_by_loc
            and self.sort_by_size
            and "_loc" in self.structure
            and "_size" in self.structure
        ):
            title = f"📂 {html.escape(self.root_name)} ({self.structure['_loc']} lines, {format_size(self.structure['_size'])})"
        elif (
            self.sort_by_loc
            and self.sort_by_mtime
            and "_loc" in self.structure
            and "_mtime" in self.structure
        ):
            title = f"📂 {html.escape(self.root_name)} ({self.structure['_loc']} lines, {format_timestamp(self.structure['_mtime'])})"
        elif (
            self.sort_by_size
            and self.sort_by_mtime
            and "_size" in self.structure
            and "_mtime" in self.structure
        ):
            title = f"📂 {html.escape(self.root_name)} ({format_size(self.structure['_size'])}, {format_timestamp(self.structure['_mtime'])})"
        elif self.sort_by_loc and "_loc" in self.structure:
            title = f"📂 {html.escape(self.root_name)} ({self.structure['_loc']} lines)"
        elif self.sort_by_size and "_size" in self.structure:
            title = f"📂 {html.escape(self.root_name)} ({format_size(self.structure['_size'])})"
        elif self.sort_by_mtime and "_mtime" in self.structure:
            title = f"📂 {html.escape(self.root_name)} ({format_timestamp(self.structure['_mtime'])})"
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
            logger.error(f"Error exporting to HTML: {e}")
            raise

    def to_markdown(self, output_path: str) -> None:
        """Export directory structure to a Markdown file.

        Creates a Markdown file with a structured representation of the directory hierarchy using headings, lists, and formatting to distinguish between files and directories.

        Args:
            output_path: Path where the Markdown file will be saved
        """

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
                    display_path = ""
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

                    _fname_md = (
                        file_item[0]
                        if isinstance(file_item, tuple) and len(file_item) > 0
                        else (file_item if isinstance(file_item, str) else "unknown")
                    )
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
                    if _git_marker_md == "D":
                        _md_display = f"~~`{display_path}`~~"
                    else:
                        _md_display = f"`{display_path}`"
                    _md_git_suffix = (
                        f" {_GIT_MD_BADGE[_git_marker_md]}"
                        if _git_marker_md in _GIT_MD_BADGE
                        else ""
                    )

                    if self.sort_by_loc and self.sort_by_size and self.sort_by_mtime:
                        lines.append(
                            f"{indent}- 📄 {_md_display} ({loc} lines, {format_size(size)}, {format_timestamp(mtime)}){_md_git_suffix}"
                        )
                    elif self.sort_by_loc and self.sort_by_mtime:
                        lines.append(
                            f"{indent}- 📄 {_md_display} ({loc} lines, {format_timestamp(mtime)}){_md_git_suffix}"
                        )
                    elif self.sort_by_size and self.sort_by_mtime:
                        lines.append(
                            f"{indent}- 📄 {_md_display} ({format_size(size)}, {format_timestamp(mtime)}){_md_git_suffix}"
                        )
                    elif self.sort_by_loc and self.sort_by_size:
                        lines.append(
                            f"{indent}- 📄 {_md_display} ({loc} lines, {format_size(size)}){_md_git_suffix}"
                        )
                    elif self.sort_by_mtime:
                        lines.append(
                            f"{indent}- 📄 {_md_display} ({format_timestamp(mtime)}){_md_git_suffix}"
                        )
                    elif self.sort_by_size:
                        lines.append(
                            f"{indent}- 📄 {_md_display} ({format_size(size)}){_md_git_suffix}"
                        )
                    elif self.sort_by_loc:
                        lines.append(
                            f"{indent}- 📄 {_md_display} ({loc} lines){_md_git_suffix}"
                        )
                    else:
                        lines.append(f"{indent}- 📄 {_md_display}{_md_git_suffix}")
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
                        f"{indent}- 📁 **{name}** ({loc_count} lines, {format_size(size_count)}, {format_timestamp(mtime_count)})"
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
                        f"{indent}- 📁 **{name}** ({loc_count} lines, {format_size(size_count)})"
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
                        f"{indent}- 📁 **{name}** ({loc_count} lines, {format_timestamp(mtime_count)})"
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
                        f"{indent}- 📁 **{name}** ({format_size(size_count)}, {format_timestamp(mtime_count)})"
                    )
                elif (
                    self.sort_by_loc and isinstance(content, dict) and "_loc" in content
                ):
                    loc_count = content["_loc"]
                    lines.append(f"{indent}- 📁 **{name}** ({loc_count} lines)")
                elif (
                    self.sort_by_size
                    and isinstance(content, dict)
                    and "_size" in content
                ):
                    size_count = content["_size"]
                    lines.append(f"{indent}- 📁 **{name}** ({format_size(size_count)})")
                elif (
                    self.sort_by_mtime
                    and isinstance(content, dict)
                    and "_mtime" in content
                ):
                    mtime_count = content["_mtime"]
                    lines.append(
                        f"{indent}- 📁 **{name}** ({format_timestamp(mtime_count)})"
                    )
                else:
                    lines.append(f"{indent}- 📁 **{name}**")
                next_path = os.path.join(path_prefix, name) if path_prefix else name
                if isinstance(content, dict):
                    if content.get("_max_depth_reached"):
                        lines.append(f"{indent}    - ⋯ *(max depth reached)*")
                    else:
                        lines.extend(_build_md_tree(content, level + 1, next_path))
            return lines

        if (
            self.sort_by_loc
            and self.sort_by_size
            and self.sort_by_mtime
            and "_loc" in self.structure
            and "_size" in self.structure
            and "_mtime" in self.structure
        ):
            md_content = [
                f"# 📂 {self.root_name} ({self.structure['_loc']} lines, {format_size(self.structure['_size'])}, {format_timestamp(self.structure['_mtime'])})",
                "",
            ]
        elif (
            self.sort_by_loc
            and self.sort_by_size
            and "_loc" in self.structure
            and "_size" in self.structure
        ):
            md_content = [
                f"# 📂 {self.root_name} ({self.structure['_loc']} lines, {format_size(self.structure['_size'])})",
                "",
            ]
        elif (
            self.sort_by_loc
            and self.sort_by_mtime
            and "_loc" in self.structure
            and "_mtime" in self.structure
        ):
            md_content = [
                f"# 📂 {self.root_name} ({self.structure['_loc']} lines, {format_timestamp(self.structure['_mtime'])})",
                "",
            ]
        elif (
            self.sort_by_size
            and self.sort_by_mtime
            and "_size" in self.structure
            and "_mtime" in self.structure
        ):
            md_content = [
                f"# 📂 {self.root_name} ({format_size(self.structure['_size'])}, {format_timestamp(self.structure['_mtime'])})",
                "",
            ]
        elif self.sort_by_loc and "_loc" in self.structure:
            md_content = [f"# 📂 {self.root_name} ({self.structure['_loc']} lines)", ""]
        elif self.sort_by_size and "_size" in self.structure:
            md_content = [
                f"# 📂 {self.root_name} ({format_size(self.structure['_size'])})",
                "",
            ]
        elif self.sort_by_mtime and "_mtime" in self.structure:
            md_content = [
                f"# 📂 {self.root_name} ({format_timestamp(self.structure['_mtime'])})",
                "",
            ]
        else:
            md_content = [f"# 📂 {self.root_name}", ""]
        md_content.extend(
            _build_md_tree(
                self.structure, 0, self.root_name if self.show_full_path else ""
            )
        )
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(md_content))
        except Exception as e:
            logger.error(f"Error exporting to Markdown: {e}")
            raise

    def to_jsx(self, output_path: str) -> None:
        """Export directory structure to a React component (JSX file).

        Creates a JSX file containing a React component for interactive visualization of the directory structure with collapsible folders and styling.

        Args:
            output_path: Path where the React component file will be saved
        """

        try:
            generate_jsx_component(
                self.structure,
                self.root_name,
                output_path,
                self.show_full_path,
                self.sort_by_loc,
                self.sort_by_size,
                self.sort_by_mtime,
                self.show_git_status,
            )
        except Exception as e:
            logger.error(f"Error exporting to React component: {e}")
            raise
