import logging
import os
from typing import Any

from rich.console import Console
from rich.tree import Tree

from recursivist.colors import generate_color_for_extension
from recursivist.icons import get_icon
from recursivist.metrics import format_metrics_suffix
from recursivist.tree import build_tree

from .base import BaseExporter

logger = logging.getLogger(__name__)


class SvgExporter(BaseExporter):
    def export(self, output_path: str) -> None:
        def extract_extensions(struct: dict[str, Any]) -> set[str]:
            exts = set()
            for k, v in struct.items():
                if k == "_files":
                    for f in v:
                        name = f[0] if isinstance(f, tuple) else f
                        exts.add(os.path.splitext(name)[1].lower())
                elif isinstance(v, dict):
                    exts.update(extract_extensions(v))
            return exts

        extensions = extract_extensions(self.structure)
        color_map = {ext: generate_color_for_extension(ext) for ext in extensions}

        root_icon = get_icon(self.root_name, is_dir=True, style=self.icon_style)
        root_label = f"{root_icon} {self.root_name}" + format_metrics_suffix(
            self.structure.get("_loc", 0),
            self.structure.get("_size", 0),
            self.structure.get("_mtime", 0.0),
            sort_by_loc=self.sort_by_loc and "_loc" in self.structure,
            sort_by_size=self.sort_by_size and "_size" in self.structure,
            sort_by_mtime=self.sort_by_mtime and "_mtime" in self.structure,
        )

        tree = Tree(root_label)

        build_tree(
            structure=self.structure,
            tree=tree,
            color_map=color_map,
            show_full_path=self.show_full_path,
            sort_by_loc=self.sort_by_loc,
            sort_by_size=self.sort_by_size,
            sort_by_mtime=self.sort_by_mtime,
            show_git_status=self.show_git_status,
            icon_style=self.icon_style,
            sort_by_similarity=self.sort_by_similarity,
        )

        console = Console(record=True, width=120)
        console.print(tree)

        try:
            console.save_svg(
                output_path, title=f"Directory Structure - {self.root_name}"
            )
        except Exception as e:
            logger.exception(f"Error exporting to SVG: {e}")
            raise
