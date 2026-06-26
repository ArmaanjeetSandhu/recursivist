from typing import Any


class BaseExporter:
    """Base class for all directory exporters holding shared configuration."""

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
    ) -> None:
        self.structure = structure
        self.root_name = root_name
        self.base_path = base_path
        self.show_full_path = base_path is not None
        self.sort_by_loc = sort_by_loc
        self.sort_by_size = sort_by_size
        self.sort_by_mtime = sort_by_mtime
        self.show_git_status = show_git_status
        self.icon_style = icon_style

    def export(self, output_path: str) -> None:
        """Must be implemented by subclasses to perform the actual export."""
        raise NotImplementedError("Subclasses must implement the export method.")
