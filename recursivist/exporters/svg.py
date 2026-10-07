"""SVG tree exporter.

Renders the scanned structure with the terminal tree builder into a recording ``rich``
console and saves the captured output as an ``.svg`` file.
"""

import io

from rich.console import Console
from rich.text import Text
from rich.tree import Tree

from recursivist.colors import build_color_map
from recursivist.icons import get_icon
from recursivist.metrics import format_dir_metrics
from recursivist.scanner import collect_extensions, has_contents
from recursivist.tree import build_tree

from .base import BaseExporter, write_text


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
        color_map = build_color_map(collect_extensions(self.structure))

        root_icon = get_icon(
            self.root_name,
            is_dir=True,
            style=self.icon_style,
            is_empty=not has_contents(self.structure),
        )
        root_label = f"{root_icon} {self.root_name}" + format_dir_metrics(
            self.structure, self.metrics, self.date_format
        )

        tree = Tree(Text(root_label))

        build_tree(
            structure=self.structure,
            tree=tree,
            color_map=color_map,
            spec=self.spec,
            icon_style=self.icon_style,
        )

        dummy_file = io.StringIO()
        console = Console(record=True, width=120, file=dummy_file, force_terminal=True)
        console.print(tree)

        write_text(
            output_path,
            console.export_svg(title=f"Directory Structure - {self.root_name}"),
        )
