import html
import json
import logging
import os
from typing import Any, Dict, List

from recursivist.jsx_export import generate_jsx_component

logger = logging.getLogger(__name__)


def sort_files_by_type(files: List[str]) -> List[str]:
    """Sort files by extension and then by name.

    Args:
        files: List of filenames to sort

    Returns:
        Sorted list of filenames
    """
    return sorted(files, key=lambda f: (os.path.splitext(f)[1], f.lower()))


class DirectoryExporter:
    """Handles exporting directory structures to various formats."""

    def __init__(self, structure: Dict[str, Any], root_name: str):
        """Initialize the exporter with directory structure and root name.

        Args:
            structure: The directory structure dictionary
            root_name: Name of the root directory
        """
        self.structure = structure
        self.root_name = root_name

    def to_txt(self, output_path: str) -> None:
        """Export directory structure to a text file with ASCII tree representation.

        Args:
            output_path: Path where the txt file will be saved
        """

        def _build_txt_tree(structure: Dict[str, Any], prefix: str = "") -> List[str]:
            lines = []
            items = sorted(structure.items())

            for i, (name, content) in enumerate(items):
                if name == "_files":
                    for file in sort_files_by_type(content):
                        lines.append(f"{prefix}├── 📄 {file}")
                elif name == "_max_depth_reached":
                    continue
                else:
                    lines.append(f"{prefix}├── 📁 {name}")
                    if isinstance(content, dict):
                        if content.get("_max_depth_reached"):
                            lines.append(f"{prefix}│   ├── ⋯ (max depth reached)")
                        else:
                            lines.extend(_build_txt_tree(content, prefix + "│   "))
            return lines

        tree_lines = [f"📂 {self.root_name}"]
        tree_lines.extend(_build_txt_tree(self.structure))

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
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(
                    {"root": self.root_name, "structure": self.structure}, f, indent=2
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

        def _build_html_tree(structure: Dict[str, Any]) -> str:
            html_content = ["<ul>"]

            if "_files" in structure:
                for file in sort_files_by_type(structure["_files"]):
                    html_content.append(f'<li class="file">📄 {html.escape(file)}</li>')

            for name, content in sorted(structure.items()):
                if name == "_files" or name == "_max_depth_reached":
                    continue

                html_content.append(f'<li class="directory">📁 {html.escape(name)}')

                if isinstance(content, dict):
                    if content.get("_max_depth_reached"):
                        html_content.append(
                            '<ul><li class="max-depth">⋯ (max depth reached)</li></ul>'
                        )
                    else:
                        html_content.append(_build_html_tree(content))

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
            </style>
        </head>
        <body>
            <h1>📂 {html.escape(self.root_name)}</h1>
            {_build_html_tree(self.structure)}
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

        def _build_md_tree(structure: Dict[str, Any], level: int = 0) -> List[str]:
            lines = []
            indent = "    " * level

            if "_files" in structure:
                for file in sort_files_by_type(structure["_files"]):
                    lines.append(f"{indent}- 📄 `{file}`")

            for name, content in sorted(structure.items()):
                if name == "_files" or name == "_max_depth_reached":
                    continue

                lines.append(f"{indent}- 📁 **{name}**")

                if isinstance(content, dict):
                    if content.get("_max_depth_reached"):
                        lines.append(f"{indent}    - ⋯ *(max depth reached)*")
                    else:
                        lines.extend(_build_md_tree(content, level + 1))

            return lines

        md_content = [f"# 📂 {self.root_name}", ""]
        md_content.extend(_build_md_tree(self.structure))

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
            generate_jsx_component(self.structure, self.root_name, output_path)
            logger.info(f"Successfully exported React component to {output_path}")
        except Exception as e:
            logger.error(f"Error exporting to React component: {e}")
            raise
