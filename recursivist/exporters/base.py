"""Shared base class for directory-structure exporters.

Defines :class:`BaseExporter`, which stores the scanned structure and the
resolved display options common to every output format. Concrete exporters
subclass it and implement :meth:`BaseExporter.export`.
"""

from typing import Any

from recursivist.flags import DisplayOptions


class BaseExporter:
    """Common base for the per-format exporters.

    Holds the scanned structure and the resolved :class:`DisplayOptions`; the
    actual output is produced by each subclass's :meth:`export`. For
    convenience, the individual pieces of the spec are also exposed as plain
    attributes (``metrics``, ``sort_key``, ``show_loc``/``show_size``/
    ``show_mtime``/``show_git_status``) so exporters can read them directly.
    """

    def __init__(
        self,
        structure: dict[str, Any],
        root_name: str,
        base_path: str | None = None,
        spec: DisplayOptions | None = None,
        icon_style: str = "emoji",
    ) -> None:
        """Store the structure and display options for an export.

        Args:
            structure: Scanned directory structure to export.
            root_name: Display name of the root directory.
            base_path: Base path for full-path display. When provided (not
                ``None``), absolute paths are shown instead of bare filenames.
            spec: Resolved sorting and annotation directives. Defaults to a
                plain :class:`DisplayOptions` (no sorting, no annotations).
            icon_style: Icon style to use, either ``"emoji"`` or ``"nerd"``.
        """
        self.structure = structure
        self.root_name = root_name
        self.base_path = base_path
        self.show_full_path = base_path is not None
        self.spec = spec if spec is not None else DisplayOptions()
        self.metrics = self.spec.metrics
        self.sort_key = self.spec.sort_key
        self.show_loc = self.spec.show_loc
        self.show_size = self.spec.show_size
        self.show_mtime = self.spec.show_mtime
        self.show_git_status = self.spec.show_git_status
        self.icon_style = icon_style

    def export(self, output_path: str) -> None:
        """Write the export to *output_path*.

        Args:
            output_path: Path the output file is written to.

        Raises:
            NotImplementedError: Always; subclasses must override this method.
        """
        raise NotImplementedError("Subclasses must implement the export method.")
