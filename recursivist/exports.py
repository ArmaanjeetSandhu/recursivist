"""
Export functionality for the Recursivist directory visualization tool.

This module handles the export of directory structures to various formats including text (ASCII tree), JSON, HTML, Markdown, and JSX (React component).

The DirectoryExporter class provides a unified interface for transforming the directory structure dictionary into different output formats with consistent styling and organization.
"""

import html
import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple, Union, cast

from recursivist.core import format_size, format_timestamp
from recursivist.jsx_export import generate_jsx_component

logger = logging.getLogger(__name__)


def sort_files_by_type(
    files: List[
        Union[
            str,
            Tuple[str, str],
            Tuple[str, str, int],
            Tuple[str, str, int, int],
            Tuple[str, str, int, int, float],
        ]
    ],
    sort_by_loc: bool = False,
    sort_by_size: bool = False,
    sort_by_mtime: bool = False,
) -> List[
    Union[
        str,
        Tuple[str, str],
        Tuple[str, str, int],
        Tuple[str, str, int, int],
        Tuple[str, str, int, int, float],
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

    def get_size(item):
        if not isinstance(item, tuple):
            return 0
        if len(item) > 3:
            if sort_by_loc and sort_by_size:
                return item[3]
            elif sort_by_size and not sort_by_loc:
                return item[2]
        return 0

    def get_loc(item):
        if not isinstance(item, tuple) or len(item) <= 2:
            return 0
        return item[2] if sort_by_loc else 0

    def get_mtime(item):
        if not isinstance(item, tuple):
            return 0
        if len(item) > 4 and sort_by_loc and sort_by_size and sort_by_mtime:
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
        return sorted(files, key=lambda f: (-get_loc(f)))
    elif sort_by_size and (has_size or has_simple_size):
        return sorted(files, key=lambda f: (-get_size(f)))
    elif sort_by_mtime and (has_mtime or has_simple_mtime):
        return sorted(files, key=lambda f: (-get_mtime(f)))
    all_tuples = all(isinstance(item, tuple) for item in files)
    all_strings = all(isinstance(item, str) for item in files)
    if all_strings:
        files_as_strings = cast(List[str], files)
        return cast(
            List[
                Union[
                    str,
                    Tuple[str, str],
                    Tuple[str, str, int],
                    Tuple[str, str, int, int],
                    Tuple[str, str, int, int, float],
                ]
            ],
            sorted(
                files_as_strings,
                key=lambda f: (os.path.splitext(f)[1].lower(), f.lower()),
            ),
        )
    elif all_tuples:
        return sorted(
            files,
            key=lambda t: (os.path.splitext(t[0])[1].lower(), t[0].lower()),
        )
    else:
        str_items: List[str] = []
        tuple_items: List[
            Union[
                Tuple[str, str],
                Tuple[str, str, int],
                Tuple[str, str, int, int],
                Tuple[str, str, int, int, float],
            ]
        ] = []
        for item in files:
            if isinstance(item, tuple):
                tuple_items.append(item)
            else:
                str_items.append(cast(str, item))
        sorted_strings = sorted(
            str_items, key=lambda f: (os.path.splitext(f)[1].lower(), f.lower())
        )
        sorted_tuples = sorted(
            tuple_items, key=lambda t: (os.path.splitext(t[0])[1].lower(), t[0].lower())
        )
        result: List[
            Union[
                str,
                Tuple[str, str],
                Tuple[str, str, int],
                Tuple[str, str, int, int],
                Tuple[str, str, int, int, float],
            ]
        ] = []
        result.extend(sorted_strings)
        result.extend(sorted_tuples)
        return result


class DirectoryExporter:
    """Handles exporting directory structures to various formats.

    Provides a unified interface for transforming directory structures into different output formats with consistent styling and organization. Supports text (ASCII tree), JSON, HTML, Markdown, and JSX (React component).
    """

    def __init__(
        self,
        structure: Dict[str, Any],
        root_name: str,
        base_path: Optional[str] = None,
        sort_by_loc: bool = False,
        sort_by_size: bool = False,
        sort_by_mtime: bool = False,
    ):
        """Initialize the exporter with directory structure and root name.

        Args:
            structure: The directory structure dictionary
            root_name: Name of the root directory
            base_path: Base path for full path display (if None, only show filenames)
            sort_by_loc: Whether to include lines of code counts in exports
            sort_by_size: Whether to include file size information in exports
            sort_by_mtime: Whether to include modification time information in exports
        """
        self.structure = structure
        self.root_name = root_name
        self.base_path = base_path
        self.show_full_path = base_path is not None
        self.sort_by_loc = sort_by_loc
        self.sort_by_size = sort_by_size
        self.sort_by_mtime = sort_by_mtime

    def to_txt(self, output_path: str) -> None:
        """Export directory structure to a text file with ASCII tree representation.

        Creates a text file containing an ASCII tree representation of the directory structure using standard box-drawing characters and indentation.

        Args:
            output_path: Path where the txt file will be saved
        """

        def _build_txt_tree(
            structure: Dict[str, Any],
            prefix: str = "",
            path_prefix: str = "",
        ) -> List[str]:
            lines = []
            items = sorted(structure.items())
            for i, (name, content) in enumerate(items):
                if name == "_files":
                    for file_item in sort_files_by_type(
                        content, self.sort_by_loc, self.sort_by_size, self.sort_by_mtime
                    ):
                        if (
                            self.sort_by_loc
                            and self.sort_by_size
                            and self.sort_by_mtime
                            and isinstance(file_item, tuple)
                            and len(file_item) > 4
                        ):
                            _, display_path, loc, size, mtime = file_item
                            lines.append(
                                f"{prefix}├── 📄 {display_path} ({loc} lines, {format_size(size)}, {format_timestamp(mtime)})"
                            )
                        elif (
                            self.sort_by_loc
                            and self.sort_by_mtime
                            and isinstance(file_item, tuple)
                            and len(file_item) > 3
                        ):
                            if len(file_item) > 4:
                                _, display_path, loc, _, mtime = file_item
                            else:
                                _, display_path, loc, mtime = file_item
                            lines.append(
                                f"{prefix}├── 📄 {display_path} ({loc} lines, {format_timestamp(mtime)})"
                            )
                        elif (
                            self.sort_by_size
                            and self.sort_by_mtime
                            and isinstance(file_item, tuple)
                            and len(file_item) > 3
                        ):
                            if len(file_item) > 4:
                                _, display_path, _, size, mtime = file_item
                            else:
                                _, display_path, size, mtime = file_item
                            lines.append(
                                f"{prefix}├── 📄 {display_path} ({format_size(size)}, {format_timestamp(mtime)})"
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
                                f"{prefix}├── 📄 {display_path} ({loc} lines, {format_size(size)})"
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
                                f"{prefix}├── 📄 {display_path} ({format_timestamp(mtime)})"
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
                                f"{prefix}├── 📄 {display_path} ({format_size(size)})"
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
                            lines.append(f"{prefix}├── 📄 {display_path} ({loc} lines)")
                        elif self.show_full_path and isinstance(file_item, tuple):
                            if len(file_item) > 4:
                                _, full_path, _, _, _ = file_item
                            elif len(file_item) > 3:
                                _, full_path, _, _ = file_item
                            elif len(file_item) > 2:
                                _, full_path, _ = file_item
                            else:
                                _, full_path = file_item
                            lines.append(f"{prefix}├── 📄 {full_path}")
                        else:
                            if isinstance(file_item, tuple):
                                if len(file_item) > 4:
                                    file_name, _, _, _, _ = file_item
                                elif len(file_item) > 3:
                                    file_name, _, _, _ = file_item
                                elif len(file_item) > 2:
                                    file_name, _, _ = file_item
                                else:
                                    file_name, _ = file_item
                            else:
                                file_name = file_item
                            lines.append(f"{prefix}├── 📄 {file_name}")
                elif (
                    name == "_loc"
                    or name == "_size"
                    or name == "_mtime"
                    or name == "_max_depth_reached"
                ):
                    continue
                else:
                    next_path = os.path.join(path_prefix, name) if path_prefix else name
                    if isinstance(content, dict):
                        if content.get("_max_depth_reached"):
                            lines.append(f"{prefix}│   ├── ⋯ (max depth reached)")
                        else:
                            lines.extend(
                                _build_txt_tree(content, prefix + "│   ", next_path)
                            )
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

            def convert_structure_for_json(structure):
                result = {}
                for k, v in structure.items():
                    if k == "_files":
                        result[k] = []
                        for item in v:
                            if (
                                self.sort_by_loc
                                and self.sort_by_size
                                and self.sort_by_mtime
                                and isinstance(item, tuple)
                                and len(item) > 4
                            ):
                                file_name, full_path, loc, size, mtime = item
                                result[k].append(
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
                            elif (
                                self.sort_by_loc
                                and self.sort_by_mtime
                                and isinstance(item, tuple)
                                and len(item) > 4
                            ):
                                file_name, full_path, loc, _, mtime = item
                                result[k].append(
                                    {
                                        "name": file_name,
                                        "path": full_path,
                                        "loc": loc,
                                        "mtime": mtime,
                                        "mtime_formatted": format_timestamp(mtime),
                                    }
                                )
                            elif (
                                self.sort_by_size
                                and self.sort_by_mtime
                                and isinstance(item, tuple)
                                and len(item) > 4
                            ):
                                file_name, full_path, _, size, mtime = item
                                result[k].append(
                                    {
                                        "name": file_name,
                                        "path": full_path,
                                        "size": size,
                                        "size_formatted": format_size(size),
                                        "mtime": mtime,
                                        "mtime_formatted": format_timestamp(mtime),
                                    }
                                )
                            elif (
                                self.sort_by_loc
                                and self.sort_by_size
                                and isinstance(item, tuple)
                                and len(item) > 3
                            ):
                                file_name, full_path, loc, size = item
                                result[k].append(
                                    {
                                        "name": file_name,
                                        "path": full_path,
                                        "loc": loc,
                                        "size": size,
                                        "size_formatted": format_size(size),
                                    }
                                )
                            elif self.sort_by_mtime and isinstance(item, tuple):
                                if len(item) > 4:
                                    file_name, full_path, _, _, mtime = item
                                elif len(item) > 3:
                                    file_name, full_path, _, mtime = item
                                else:
                                    file_name, full_path, mtime = item
                                result[k].append(
                                    {
                                        "name": file_name,
                                        "path": full_path,
                                        "mtime": mtime,
                                        "mtime_formatted": format_timestamp(mtime),
                                    }
                                )
                            elif self.sort_by_size and isinstance(item, tuple):
                                if len(item) > 3:
                                    file_name, full_path, _, size = item
                                    result[k].append(
                                        {
                                            "name": file_name,
                                            "path": full_path,
                                            "size": size,
                                            "size_formatted": format_size(size),
                                        }
                                    )
                                elif len(item) > 2:
                                    file_name, full_path, size = item
                                    result[k].append(
                                        {
                                            "name": file_name,
                                            "path": full_path,
                                            "size": size,
                                            "size_formatted": format_size(size),
                                        }
                                    )
                                else:
                                    file_name, full_path = item
                                    result[k].append(
                                        full_path if self.show_full_path else file_name
                                    )
                            elif (
                                self.sort_by_loc
                                and isinstance(item, tuple)
                                and len(item) > 2
                            ):
                                file_name, full_path, loc = item
                                result[k].append(
                                    {"name": file_name, "path": full_path, "loc": loc}
                                )
                            elif isinstance(item, tuple):
                                if len(item) > 4:
                                    _, full_path, _, _, _ = item
                                elif len(item) > 3:
                                    _, full_path, _, _ = item
                                elif len(item) > 2:
                                    _, full_path, _ = item
                                else:
                                    _, full_path = item
                                result[k].append(full_path)
                            else:
                                result[k].append(item)
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
                    },
                    f,
                    indent=2,
                )
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
            raise

    def to_html(self, output_path: str) -> None:
        """Export directory structure to an HTML file.

        Creates a standalone HTML file with a styled representation of the directory structure using
        nested unordered lists with CSS styling for colors and indentation.

        Args:
            output_path: Path where the HTML file will be saved
        """

        def _build_html_tree(
            structure: Dict[str, Any],
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
                    if (
                        self.sort_by_loc
                        and self.sort_by_size
                        and self.sort_by_mtime
                        and isinstance(file_item, tuple)
                        and len(file_item) > 4
                    ):
                        _, display_path, loc, size, mtime = file_item
                        html_content.append(
                            f'<li class="file">📄 {html.escape(display_path)} ({loc} lines, {format_size(size)}, {format_timestamp(mtime)})</li>'
                        )
                    elif (
                        self.sort_by_loc
                        and self.sort_by_mtime
                        and isinstance(file_item, tuple)
                        and len(file_item) > 3
                    ):
                        if len(file_item) > 4:
                            _, display_path, loc, _, mtime = file_item
                        else:
                            _, display_path, loc, mtime = file_item
                        html_content.append(
                            f'<li class="file">📄 {html.escape(display_path)} ({loc} lines, {format_timestamp(mtime)})</li>'
                        )
                    elif (
                        self.sort_by_size
                        and self.sort_by_mtime
                        and isinstance(file_item, tuple)
                        and len(file_item) > 3
                    ):
                        if len(file_item) > 4:
                            _, display_path, _, size, mtime = file_item
                        else:
                            _, display_path, size, mtime = file_item
                        html_content.append(
                            f'<li class="file">📄 {html.escape(display_path)} ({format_size(size)}, {format_timestamp(mtime)})</li>'
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
                        html_content.append(
                            f'<li class="file">📄 {html.escape(display_path)} ({loc} lines, {format_size(size)})</li>'
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
                        html_content.append(
                            f'<li class="file">📄 {html.escape(display_path)} ({format_timestamp(mtime)})</li>'
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
                        html_content.append(
                            f'<li class="file">📄 {html.escape(display_path)} ({format_size(size)})</li>'
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
                        html_content.append(
                            f'<li class="file">📄 {html.escape(display_path)} ({loc} lines)</li>'
                        )
                    elif self.show_full_path and isinstance(file_item, tuple):
                        if len(file_item) > 4:
                            _, full_path, _, _, _ = file_item
                        elif len(file_item) > 3:
                            _, full_path, _, _ = file_item
                        elif len(file_item) > 2:
                            _, full_path, _ = file_item
                        else:
                            _, full_path = file_item
                        html_content.append(
                            f'<li class="file">📄 {html.escape(full_path)}</li>'
                        )
                    else:
                        if isinstance(file_item, tuple):
                            if len(file_item) > 4:
                                filename_str, _, _, _, _ = file_item
                            elif len(file_item) > 3:
                                filename_str, _, _, _ = file_item
                            elif len(file_item) > 2:
                                filename_str, _, _ = file_item
                            else:
                                filename_str, _ = file_item
                        else:
                            filename_str = cast(str, file_item)
                        html_content.append(
                            f'<li class="file">📄 {html.escape(filename_str)}</li>'
                        )
            for name, content in sorted(structure.items()):
                if (
                    name == "_files"
                    or name == "_max_depth_reached"
                    or name == "_loc"
                    or name == "_size"
                    or name == "_mtime"
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

        Creates a Markdown file with a structured representation of the directory hierarchy using
        headings, lists, and formatting to distinguish between files and directories.

        Args:
            output_path: Path where the Markdown file will be saved
        """

        def _build_md_tree(
            structure: Dict[str, Any],
            level: int = 0,
            path_prefix: str = "",
        ) -> List[str]:
            lines = []
            indent = "    " * level
            if "_files" in structure:
                for file_item in sort_files_by_type(
                    structure["_files"],
                    self.sort_by_loc,
                    self.sort_by_size,
                    self.sort_by_mtime,
                ):
                    if (
                        self.sort_by_loc
                        and self.sort_by_size
                        and self.sort_by_mtime
                        and isinstance(file_item, tuple)
                        and len(file_item) > 4
                    ):
                        _, display_path, loc, size, mtime = file_item
                        lines.append(
                            f"{indent}- 📄 `{display_path}` ({loc} lines, {format_size(size)}, {format_timestamp(mtime)})"
                        )
                    elif (
                        self.sort_by_loc
                        and self.sort_by_mtime
                        and isinstance(file_item, tuple)
                        and len(file_item) > 3
                    ):
                        if len(file_item) > 4:
                            _, display_path, loc, _, mtime = file_item
                        else:
                            _, display_path, loc, mtime = file_item
                        lines.append(
                            f"{indent}- 📄 `{display_path}` ({loc} lines, {format_timestamp(mtime)})"
                        )
                    elif (
                        self.sort_by_size
                        and self.sort_by_mtime
                        and isinstance(file_item, tuple)
                        and len(file_item) > 3
                    ):
                        if len(file_item) > 4:
                            _, display_path, _, size, mtime = file_item
                        else:
                            _, display_path, size, mtime = file_item
                        lines.append(
                            f"{indent}- 📄 `{display_path}` ({format_size(size)}, {format_timestamp(mtime)})"
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
                            f"{indent}- 📄 `{display_path}` ({loc} lines, {format_size(size)})"
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
                            f"{indent}- 📄 `{display_path}` ({format_timestamp(mtime)})"
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
                            f"{indent}- 📄 `{display_path}` ({format_size(size)})"
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
                        lines.append(f"{indent}- 📄 `{display_path}` ({loc} lines)")
                    elif self.show_full_path and isinstance(file_item, tuple):
                        if len(file_item) > 4:
                            _, full_path, _, _, _ = file_item
                        elif len(file_item) > 3:
                            _, full_path, _, _ = file_item
                        elif len(file_item) > 2:
                            _, full_path, _ = file_item
                        else:
                            _, full_path = file_item
                        lines.append(f"{indent}- 📄 `{full_path}`")
                    else:
                        if isinstance(file_item, tuple):
                            if len(file_item) > 4:
                                file_name, _, _, _, _ = file_item
                            elif len(file_item) > 3:
                                file_name, _, _, _ = file_item
                            elif len(file_item) > 2:
                                file_name, _, _ = file_item
                            else:
                                file_name, _ = file_item
                        else:
                            file_name = file_item
                        lines.append(f"{indent}- 📄 `{file_name}`")
            for name, content in sorted(structure.items()):
                if (
                    name == "_files"
                    or name == "_max_depth_reached"
                    or name == "_loc"
                    or name == "_size"
                    or name == "_mtime"
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

        Creates a JSX file containing a React component for interactive visualization
        of the directory structure with collapsible folders and styling.

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
            )
        except Exception as e:
            logger.error(f"Error exporting to React component: {e}")
            raise
