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

from recursivist.jsx_export import generate_jsx_component

logger = logging.getLogger(__name__)


def sort_files_by_type(
    files: List[Union[str, Tuple[str, str], Tuple[str, str, int]]],
    sort_by_loc: bool = False,
) -> List[Union[str, Tuple[str, str], Tuple[str, str, int]]]:
    """Sort files by extension and then by name, or by LOC if requested.

    Handles mixed input of both strings and tuples, ensuring correct sorting in either case. When sort_by_loc is True, files are sorted by lines of code (descending).

    Args:
        files: List of filenames or tuples to sort
        sort_by_loc: Whether to sort by lines of code instead of file type

    Returns:
        Sorted list of filenames or tuples
    """
    if not files:
        return []
    has_loc = any(isinstance(item, tuple) and len(item) > 2 for item in files)
    if sort_by_loc and has_loc:
        return sorted(
            files, key=lambda f: (-(f[2] if isinstance(f, tuple) and len(f) > 2 else 0))
        )
    all_tuples = all(isinstance(item, tuple) for item in files)
    all_strings = all(isinstance(item, str) for item in files)
    if all_strings:
        files_as_strings = cast(List[str], files)
        return cast(
            List[Union[str, Tuple[str, str], Tuple[str, str, int]]],
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
        tuple_items: List[Union[Tuple[str, str], Tuple[str, str, int]]] = []
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
        result: List[Union[str, Tuple[str, str], Tuple[str, str, int]]] = []
        result.extend(sorted_strings)
        result.extend(sorted_tuples)
        return result


class DirectoryExporter:
    """Handles exporting directory structures to various formats.

    Provides a unified interface for transforming directory structures into different output formats
    with consistent styling and organization. Supports text (ASCII tree), JSON, HTML, Markdown,
    and JSX (React component).
    """

    def __init__(
        self,
        structure: Dict[str, Any],
        root_name: str,
        base_path: Optional[str] = None,
        sort_by_loc: bool = False,
    ):
        """Initialize the exporter with directory structure and root name.

        Args:
            structure: The directory structure dictionary
            root_name: Name of the root directory
            base_path: Base path for full path display (if None, only show filenames)
            sort_by_loc: Whether to include lines of code counts in exports
        """
        self.structure = structure
        self.root_name = root_name
        self.base_path = base_path
        self.show_full_path = base_path is not None
        self.sort_by_loc = sort_by_loc

    def to_txt(self, output_path: str) -> None:
        """Export directory structure to a text file with ASCII tree representation.

        Creates a text file containing an ASCII tree representation of the directory structure
        using standard box-drawing characters and indentation.

        Args:
            output_path: Path where the txt file will be saved
        """

        def _build_txt_tree(
            structure: Dict[str, Any], prefix: str = "", path_prefix: str = ""
        ) -> List[str]:
            lines = []
            items = sorted(structure.items())
            for i, (name, content) in enumerate(items):
                if name == "_files":
                    for file_item in sort_files_by_type(content, self.sort_by_loc):
                        if (
                            self.sort_by_loc
                            and isinstance(file_item, tuple)
                            and len(file_item) > 2
                        ):
                            _, display_path, loc = file_item
                            lines.append(f"{prefix}├── 📄 {display_path} ({loc} lines)")
                        elif self.show_full_path and isinstance(file_item, tuple):
                            if len(file_item) > 2:
                                _, full_path, _ = file_item
                            else:
                                _, full_path = file_item
                            lines.append(f"{prefix}├── 📄 {full_path}")
                        else:
                            if isinstance(file_item, tuple):
                                if len(file_item) > 2:
                                    file_name, _, _ = file_item
                                else:
                                    file_name, _ = file_item
                            else:
                                file_name = file_item
                            lines.append(f"{prefix}├── 📄 {file_name}")
                elif name == "_loc" or name == "_max_depth_reached":
                    continue
                else:
                    if (
                        self.sort_by_loc
                        and isinstance(content, dict)
                        and "_loc" in content
                    ):
                        loc_count = content["_loc"]
                        lines.append(f"{prefix}├── 📁 {name} ({loc_count} lines)")
                    else:
                        lines.append(f"{prefix}├── 📁 {name}")
                    next_path = os.path.join(path_prefix, name) if path_prefix else name
                    if isinstance(content, dict):
                        if content.get("_max_depth_reached"):
                            lines.append(f"{prefix}│   ├── ⋯ (max depth reached)")
                        else:
                            lines.extend(
                                _build_txt_tree(content, prefix + "│   ", next_path)
                            )
            return lines

        if self.sort_by_loc and "_loc" in self.structure:
            tree_lines = [f"📂 {self.root_name} ({self.structure['_loc']} lines)"]
        else:
            tree_lines = [f"📂 {self.root_name}"]
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

        Creates a JSON file containing the directory structure with options for including full paths. The JSON structure includes a root name and the hierarchical structure of directories and files.

        Args:
            output_path: Path where the JSON file will be saved
        """
        if self.show_full_path or self.sort_by_loc:

            def convert_structure_for_json(structure):
                result = {}
                for k, v in structure.items():
                    if k == "_files":
                        if self.sort_by_loc:
                            result[k] = []
                            for item in v:
                                if isinstance(item, tuple):
                                    if len(item) > 2:
                                        file_name, full_path, loc = item
                                        result[k].append(
                                            {
                                                "name": file_name,
                                                "path": full_path,
                                                "loc": loc,
                                            }
                                        )
                                    else:
                                        file_name, full_path = item
                                        result[k].append(
                                            full_path
                                            if self.show_full_path
                                            else file_name
                                        )
                                else:
                                    result[k].append(item)
                        else:
                            result[k] = []
                            for item in v:
                                if isinstance(item, tuple):
                                    if len(item) > 2:
                                        _, full_path, _ = item
                                    else:
                                        _, full_path = item
                                    result[k].append(full_path)
                                else:
                                    result[k].append(item)
                    elif k == "_loc":
                        if self.sort_by_loc:
                            result[k] = v
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

        def _build_html_tree(structure: Dict[str, Any], path_prefix: str = "") -> str:
            html_content = ["<ul>"]
            if "_files" in structure:
                for file_item in sort_files_by_type(
                    structure["_files"], self.sort_by_loc
                ):
                    if (
                        self.sort_by_loc
                        and isinstance(file_item, tuple)
                        and len(file_item) > 2
                    ):
                        _, display_path, loc = file_item
                        html_content.append(
                            f'<li class="file">📄 {html.escape(display_path)} ({loc} lines)</li>'
                        )
                    elif self.show_full_path and isinstance(file_item, tuple):
                        if len(file_item) > 2:
                            _, full_path, _ = file_item
                        else:
                            _, full_path = file_item
                        html_content.append(
                            f'<li class="file">📄 {html.escape(full_path)}</li>'
                        )
                    else:
                        if isinstance(file_item, tuple):
                            if len(file_item) > 2:
                                filename_str, _, _ = file_item
                            else:
                                filename_str, _ = file_item
                        else:
                            filename_str = cast(str, file_item)
                        html_content.append(
                            f'<li class="file">📄 {html.escape(filename_str)}</li>'
                        )
            for name, content in sorted(structure.items()):
                if name == "_files" or name == "_max_depth_reached" or name == "_loc":
                    continue
                if self.sort_by_loc and isinstance(content, dict) and "_loc" in content:
                    loc_count = content["_loc"]
                    html_content.append(
                        f'<li class="directory">📁 <span class="dir-name">{html.escape(name)}</span> '
                        f'<span class="loc-count">({loc_count} lines)</span>'
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

        if self.sort_by_loc and "_loc" in self.structure:
            title_with_loc = (
                f"📂 {html.escape(self.root_name)} ({self.structure['_loc']} lines)"
            )
        else:
            title_with_loc = f"📂 {html.escape(self.root_name)}"
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
            </style>
        </head>
        <body>
            <h1>{title_with_loc}</h1>
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
            structure: Dict[str, Any], level: int = 0, path_prefix: str = ""
        ) -> List[str]:
            lines = []
            indent = "    " * level
            if "_files" in structure:
                for file_item in sort_files_by_type(
                    structure["_files"], self.sort_by_loc
                ):
                    if (
                        self.sort_by_loc
                        and isinstance(file_item, tuple)
                        and len(file_item) > 2
                    ):
                        _, display_path, loc = file_item
                        lines.append(f"{indent}- 📄 `{display_path}` ({loc} lines)")
                    elif self.show_full_path and isinstance(file_item, tuple):
                        if len(file_item) > 2:
                            _, full_path, _ = file_item
                        else:
                            _, full_path = file_item
                        lines.append(f"{indent}- 📄 `{full_path}`")
                    else:
                        if isinstance(file_item, tuple):
                            if len(file_item) > 2:
                                file_name, _, _ = file_item
                            else:
                                file_name, _ = file_item
                        else:
                            file_name = file_item
                        lines.append(f"{indent}- 📄 `{file_name}`")
            for name, content in sorted(structure.items()):
                if name == "_files" or name == "_max_depth_reached" or name == "_loc":
                    continue
                if self.sort_by_loc and isinstance(content, dict) and "_loc" in content:
                    loc_count = content["_loc"]
                    lines.append(f"{indent}- 📁 **{name}** ({loc_count} lines)")
                else:
                    lines.append(f"{indent}- 📁 **{name}**")
                next_path = os.path.join(path_prefix, name) if path_prefix else name
                if isinstance(content, dict):
                    if content.get("_max_depth_reached"):
                        lines.append(f"{indent}    - ⋯ *(max depth reached)*")
                    else:
                        lines.extend(_build_md_tree(content, level + 1, next_path))
            return lines

        if self.sort_by_loc and "_loc" in self.structure:
            md_content = [f"# 📂 {self.root_name} ({self.structure['_loc']} lines)", ""]
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
            )
        except Exception as e:
            logger.error(f"Error exporting to React component: {e}")
            raise
