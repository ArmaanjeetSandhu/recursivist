"""SVG tree exporter.

Renders the scanned structure with the terminal tree builder into a recording ``rich``
console and saves the captured output as an ``.svg`` file.
"""

import io
import os
from typing import Any

from rich.console import Console
from rich.text import Text
from rich.tree import Tree

from recursivist.colors import generate_color_for_extension
from recursivist.icons import get_icon
from recursivist.metrics import format_dir_metrics
from recursivist.scanner import has_contents, iter_subdirectories
from recursivist.tree import build_tree

from .base import BaseExporter


class SvgExporter(BaseExporter):
    """Exporter that captures the rendered tree as an SVG image."""

    extension = "svg"

    def export(self, output_path: str) -> None:
        """Write the structure to *output_path* as an SVG image.

        Builds the same colored tree used for terminal output via
        [`recursivist.tree.build_tree`][recursivist.tree.build_tree], renders it to a
        recording ``rich`` console, and saves that console's output as SVG.

        Args:
            output_path: Path the ``.svg`` file is written to.
        """

        def extract_extensions(struct: dict[str, Any]) -> set[str]:
            """Collect the lowercase file extensions in *struct*, recursively.

            Args:
                struct: Directory-structure dict to scan.

            Returns:
                The set of file extensions (including the leading dot) found in
                this subtree.
            """
            exts = set()
            for entry in struct.get("_files", []):
                exts.add(os.path.splitext(entry.name)[1].lower())
            for _, content in iter_subdirectories(struct):
                if isinstance(content, dict):
                    exts.update(extract_extensions(content))
            return exts

        extensions = extract_extensions(self.structure)
        color_map = {ext: generate_color_for_extension(ext) for ext in extensions}

        root_icon = get_icon(
            self.root_name,
            is_dir=True,
            style=self.icon_style,
            is_empty=not has_contents(self.structure),
        )
        root_label = f"{root_icon} {self.root_name}" + format_dir_metrics(
            self.structure, self.metrics
        )

        tree = Tree(Text(root_label))

        build_tree(
            structure=self.structure,
            tree=tree,
            color_map=color_map,
            spec=self.spec,
            show_full_path=self.show_full_path,
            icon_style=self.icon_style,
        )

        dummy_file = io.StringIO()
        console = Console(record=True, width=120, file=dummy_file, force_terminal=True)
        console.print(tree)

        console.save_svg(output_path, title=f"Directory Structure - {self.root_name}")
