import json
import html
import os


def sort_files_by_type(files):
    """Sort files by extension and then by name."""
    return sorted(files, key=lambda f: (os.path.splitext(f)[1], f.lower()))


class DirectoryExporter:
    def __init__(self, structure, root_name):
        """Initialize the exporter with directory structure and root name.

        Args:
            structure (dict): The directory structure dictionary
            root_name (str): Name of the root directory
        """
        self.structure = structure
        self.root_name = root_name

    def to_txt(self, output_path):
        """Export directory structure to a text file with ASCII tree representation.

        Args:
            output_path (str): Path where the txt file will be saved
        """

        def _build_txt_tree(structure, prefix=""):
            lines = []
            items = sorted(structure.items())

            for i, (name, content) in enumerate(items):
                if name == "_files":
                    for file in sort_files_by_type(content):
                        lines.append(f"{prefix}├── 📄 {file}")
                else:
                    lines.append(f"{prefix}├── 📁 {name}")
                    if isinstance(content, dict):
                        extension = "└── " if i == len(items) - 1 else "├── "
                        lines.extend(_build_txt_tree(content, prefix + "│   "))
            return lines

        tree_lines = [f"📂 {self.root_name}"]
        tree_lines.extend(_build_txt_tree(self.structure))

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(tree_lines))

    def to_json(self, output_path):
        """Export directory structure to a JSON file.

        Args:
            output_path (str): Path where the JSON file will be saved
        """
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(
                {"root": self.root_name, "structure": self.structure}, f, indent=2
            )

    def to_html(self, output_path):
        """Export directory structure to an HTML file.

        Args:
            output_path (str): Path where the HTML file will be saved
        """

        def _build_html_tree(structure):
            html_content = ["<ul>"]

            if "_files" in structure:
                for file in sort_files_by_type(structure["_files"]):
                    html_content.append(f'<li class="file">📄 {html.escape(file)}</li>')

            for name, content in sorted(structure.items()):
                if name != "_files":
                    html_content.append(f'<li class="directory">📁 {html.escape(name)}')
                    if isinstance(content, dict):
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
            </style>
        </head>
        <body>
            <h1>📂 {html.escape(self.root_name)}</h1>
            {_build_html_tree(self.structure)}
        </body>
        </html>
        """

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_template)

    def to_markdown(self, output_path):
        """Export directory structure to a Markdown file.

        Args:
            output_path (str): Path where the Markdown file will be saved
        """

        def _build_md_tree(structure, level=0):
            lines = []
            indent = "    " * level

            if "_files" in structure:
                for file in sort_files_by_type(structure["_files"]):
                    lines.append(f"{indent}- 📄 `{file}`")

            for name, content in sorted(structure.items()):
                if name != "_files":
                    lines.append(f"{indent}- 📁 **{name}**")
                    if isinstance(content, dict):
                        lines.extend(_build_md_tree(content, level + 1))

            return lines

        md_content = [f"# 📂 {self.root_name}", ""]
        md_content.extend(_build_md_tree(self.structure))

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_content))
