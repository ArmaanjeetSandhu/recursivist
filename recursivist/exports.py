import html
import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple, Union

from recursivist.jsx_export import generate_jsx_component

logger = logging.getLogger(__name__)


def sort_files_by_type(
    files: List[Union[str, Tuple[str, str]]]
) -> List[Union[str, Tuple[str, str]]]:
    """Sort files by extension and then by name.

    Args:
        files: List of filenames or (filename, full_path) tuples to sort

    Returns:
        Sorted list of filenames or tuples
    """
    if not files:
        return []

    if files and isinstance(files[0], tuple):
        return sorted(files, key=lambda f: (os.path.splitext(f[0])[1], f[0].lower()))
    else:
        return sorted(files, key=lambda f: (os.path.splitext(f)[1], f.lower()))


class DirectoryExporter:
    """Handles exporting directory structures to various formats."""

    def __init__(
        self, structure: Dict[str, Any], root_name: str, base_path: Optional[str] = None
    ):
        """Initialize the exporter with directory structure and root name.

        Args:
            structure: The directory structure dictionary
            root_name: Name of the root directory
            base_path: Base path for full path display (if None, only show filenames)
        """
        self.structure = structure
        self.root_name = root_name
        self.base_path = base_path
        self.show_full_path = base_path is not None

    def to_txt(self, output_path: str) -> None:
        """Export directory structure to a text file with ASCII tree representation.

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
                    for file_item in sort_files_by_type(content):
                        if self.show_full_path and isinstance(file_item, tuple):
                            file_name, full_path = file_item
                            lines.append(f"{prefix}├── 📄 {full_path}")
                        else:
                            lines.append(f"{prefix}├── 📄 {file_item}")
                elif name == "_max_depth_reached":
                    continue
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

        tree_lines = [f"📂 {self.root_name}"]
        tree_lines.extend(
            _build_txt_tree(
                self.structure, "", self.root_name if self.show_full_path else ""
            )
        )

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(tree_lines))
            logger.info(f"Successfully exported TXT to {output_path}")
        except Exception as e:
            logger.error(f"Error exporting to TXT: {e}")
            raise

    def to_json(self, output_path: str) -> None:
        """Export directory structure to a JSON file.

        Args:
            output_path: Path where the JSON file will be saved
        """
        if self.show_full_path:

            def convert_tuples_to_paths(structure):
                result = {}
                for k, v in structure.items():
                    if k == "_files":
                        result[k] = [full_path for _, full_path in v]
                    elif k == "_max_depth_reached":
                        result[k] = v
                    elif isinstance(v, dict):
                        result[k] = convert_tuples_to_paths(v)
                    else:
                        result[k] = v
                return result

            export_structure = convert_tuples_to_paths(self.structure)
        else:
            export_structure = self.structure

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "root": self.root_name,
                        "structure": export_structure,
                        "show_full_path": self.show_full_path,
                    },
                    f,
                    indent=2,
                )
            logger.info(f"Successfully exported JSON to {output_path}")
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
            raise

    def to_html(self, output_path: str) -> None:
        """Export directory structure to an HTML file.

        Args:
            output_path: Path where the HTML file will be saved
        """

        def _build_html_tree(structure: Dict[str, Any], path_prefix: str = "") -> str:
            html_content = ["<ul>"]

            if "_files" in structure:
                for file_item in sort_files_by_type(structure["_files"]):
                    if self.show_full_path and isinstance(file_item, tuple):
                        file_name, full_path = file_item
                        html_content.append(
                            f'<li class="file">📄 {html.escape(full_path)}</li>'
                        )
                    else:
                        html_content.append(
                            f'<li class="file">📄 {html.escape(file_item)}</li>'
                        )

            for name, content in sorted(structure.items()):
                if name == "_files" or name == "_max_depth_reached":
                    continue

                html_content.append(f'<li class="directory">📁 {html.escape(name)}')
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
            </style>
        </head>
        <body>
            <h1>📂 {html.escape(self.root_name)}</h1>
            {f'<div class="path-info">Showing full file paths from: {html.escape(self.base_path or "")}</div>' if self.show_full_path else ''}
            {_build_html_tree(self.structure, self.root_name if self.show_full_path else "")}
        </body>
        </html>
        """

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_template)
            logger.info(f"Successfully exported HTML to {output_path}")
        except Exception as e:
            logger.error(f"Error exporting to HTML: {e}")
            raise

    def to_markdown(self, output_path: str) -> None:
        """Export directory structure to a Markdown file.

        Args:
            output_path: Path where the Markdown file will be saved
        """

        def _build_md_tree(
            structure: Dict[str, Any], level: int = 0, path_prefix: str = ""
        ) -> List[str]:
            lines = []
            indent = "    " * level

            if "_files" in structure:
                for file_item in sort_files_by_type(structure["_files"]):
                    if self.show_full_path and isinstance(file_item, tuple):
                        file_name, full_path = file_item
                        lines.append(f"{indent}- 📄 `{full_path}`")
                    else:
                        lines.append(f"{indent}- 📄 `{file_item}`")

            for name, content in sorted(structure.items()):
                if name == "_files" or name == "_max_depth_reached":
                    continue

                lines.append(f"{indent}- 📁 **{name}**")
                next_path = os.path.join(path_prefix, name) if path_prefix else name

                if isinstance(content, dict):
                    if content.get("_max_depth_reached"):
                        lines.append(f"{indent}    - ⋯ *(max depth reached)*")
                    else:
                        lines.extend(_build_md_tree(content, level + 1, next_path))

            return lines

        md_content = [f"# 📂 {self.root_name}", ""]
        if self.show_full_path:
            md_content.append(f"> Showing full file paths from: {self.base_path}")
            md_content.append("")

        md_content.extend(
            _build_md_tree(
                self.structure, 0, self.root_name if self.show_full_path else ""
            )
        )

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(md_content))
            logger.info(f"Successfully exported Markdown to {output_path}")
        except Exception as e:
            logger.error(f"Error exporting to Markdown: {e}")
            raise

    def to_jsx(self, output_path: str) -> None:
        """Export directory structure to a React component (JSX file).

        Args:
            output_path: Path where the React component file will be saved
        """
        try:
            generate_jsx_component(
                self.structure,
                self.root_name,
                output_path,
                self.show_full_path,
                self.base_path,
            )
            logger.info(f"Successfully exported React component to {output_path}")
        except Exception as e:
            logger.error(f"Error exporting to React component: {e}")
            raise
