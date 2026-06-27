"""Shared base class for directory-structure exporters.

Defines :class:`BaseExporter`, which stores the scanned structure and the
display options common to every output format. Concrete exporters subclass it
and implement :meth:`BaseExporter.export`.
"""

from typing import Any


class BaseExporter:
    """Common base for the per-format exporters.

    Holds the scanned structure and the shared display configuration; the
    actual output is produced by each subclass's :meth:`export`.
    """

    def __init__(
        self,
        structure: dict[str, Any],
        root_name: str,
        base_path: str | None = None,
        sort_by_loc: bool = False,
        sort_by_size: bool = False,
        sort_by_mtime: bool = False,
        show_git_status: bool = False,
        icon_style: str = "emoji",
        sort_by_similarity: bool = False,
    ) -> None:
        """Store the structure and display options for an export.

        Args:
            structure: Scanned directory structure to export.
            root_name: Display name of the root directory.
            base_path: Base path for full-path display. When provided (not
                ``None``), absolute paths are shown instead of bare filenames.
            sort_by_loc: Whether to sort by and display lines of code.
            sort_by_size: Whether to sort by and display file sizes.
            sort_by_mtime: Whether to sort by and display modification times.
            show_git_status: Whether to annotate files with Git status markers.
            icon_style: Icon style to use, either ``"emoji"`` or ``"nerd"``.
            sort_by_similarity: Whether to group files by name similarity.
        """
        self.structure = structure
        self.root_name = root_name
        self.base_path = base_path
        self.show_full_path = base_path is not None
        self.sort_by_loc = sort_by_loc
        self.sort_by_size = sort_by_size
        self.sort_by_mtime = sort_by_mtime
        self.show_git_status = show_git_status
        self.icon_style = icon_style
        self.sort_by_similarity = sort_by_similarity

    def export(self, output_path: str) -> None:
        """Write the export to *output_path*.

        Args:
            output_path: Path the output file is written to.

        Raises:
            NotImplementedError: Always; subclasses must override this method.
        """
        raise NotImplementedError("Subclasses must implement the export method.")
