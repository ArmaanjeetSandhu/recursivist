"""JSON tree exporter.

Serializes the scanned structure to JSON. Without any detail flags, files
collapse to bare names; with LOC, size, mtime, or Git status enabled, each file
becomes an object carrying the requested fields.
"""

import json
import logging
from typing import Any

from recursivist._models import FileEntry
from recursivist.metrics import format_size, format_timestamp

from .base import BaseExporter

logger = logging.getLogger(__name__)


class JsonExporter(BaseExporter):
    """Exporter that serializes the structure to JSON."""

    def export(self, output_path: str) -> None:
        """Write the structure to *output_path* as JSON.

        The payload records the root name, the (possibly detailed) structure,
        and which detail flags were active. File entries are emitted as bare
        names unless a detail flag (full path, LOC, size, mtime, or Git status)
        requires the richer object form.

        Args:
            output_path: Path the ``.json`` file is written to.

        Raises:
            Exception: Re-raised if writing the output file fails (after the
                error is logged).
        """
        has_detail = (
            self.show_full_path
            or self.sort_by_loc
            or self.sort_by_size
            or self.sort_by_mtime
        )

        def file_to_json(
            item: Any, git_markers_here: dict[str, str]
        ) -> str | dict[str, Any]:
            """Encode a single ``_files`` entry for the detail JSON form.

            Bare-string entries are emitted as plain names, optionally wrapped
            with their Git status. Every other entry is normalised through
            :meth:`FileEntry.from_raw` and rendered with exactly the keys the
            active flags call for.
            """
            if not isinstance(item, tuple):
                name = str(item)
                git_status = (
                    git_markers_here.get(name, "") if self.show_git_status else ""
                )
                if git_status:
                    return {"name": name, "git_status": git_status}
                return name
            entry = FileEntry.from_raw(
                item, self.sort_by_loc, self.sort_by_size, self.sort_by_mtime
            )
            git_status = (
                git_markers_here.get(entry.name, "") if self.show_git_status else ""
            )
            result: dict[str, Any] = {"name": entry.name, "path": entry.path}
            if self.sort_by_loc:
                result["loc"] = entry.loc
            if self.sort_by_size:
                result["size"] = entry.size
                result["size_formatted"] = format_size(entry.size)
            if self.sort_by_mtime:
                result["mtime"] = entry.mtime
                result["mtime_formatted"] = format_timestamp(entry.mtime)
            if git_status:
                result["git_status"] = git_status
            return result

        def convert_structure_for_json(structure: dict[str, Any]) -> dict[str, Any]:
            """Recursively convert *structure* to its detailed JSON form.

            Encodes each file via :func:`file_to_json` and carries through the
            enabled aggregate metrics (adding their formatted variants), while
            dropping the internal ``_git_markers`` bookkeeping key.

            Args:
                structure: Directory-structure dict to convert.

            Returns:
                The JSON-serializable mapping for this subtree.
            """
            result: dict[str, Any] = {}
            git_markers_here = structure.get("_git_markers", {})
            for k, v in structure.items():
                if k == "_files":
                    result[k] = [file_to_json(item, git_markers_here) for item in v]
                elif k == "_loc":
                    if self.sort_by_loc:
                        result[k] = v
                elif k == "_size":
                    if self.sort_by_size:
                        result[k] = v
                        result["_size_formatted"] = format_size(v)
                elif k == "_mtime":
                    if self.sort_by_mtime:
                        result[k] = v
                        result["_mtime_formatted"] = format_timestamp(v)
                elif k == "_git_markers":
                    continue
                elif k == "_max_depth_reached":
                    result[k] = v
                elif isinstance(v, dict):
                    result[k] = convert_structure_for_json(v)
                else:
                    result[k] = v
            return result

        def names_only(structure: dict[str, Any]) -> dict[str, Any]:
            """Copy ``structure``, collapsing ``_files`` to bare names.

            Used when no detail flags are active: each file is reduced to its
            name while every other key (including ``_git_markers``) is left
            intact.
            """
            result: dict[str, Any] = {}
            for k, v in structure.items():
                if k == "_files":
                    result[k] = [
                        FileEntry.from_raw(item).name
                        if isinstance(item, tuple)
                        else item
                        for item in v
                    ]
                elif isinstance(v, dict):
                    result[k] = names_only(v)
                else:
                    result[k] = v
            return result

        if has_detail:
            export_structure = convert_structure_for_json(self.structure)
        else:
            export_structure = names_only(self.structure)

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "root": self.root_name,
                        "structure": export_structure,
                        "show_loc": self.sort_by_loc,
                        "show_size": self.sort_by_size,
                        "show_mtime": self.sort_by_mtime,
                        "show_git_status": self.show_git_status,
                    },
                    f,
                    indent=2,
                )
        except Exception as e:
            logger.exception(f"Error exporting to JSON: {e}")
            raise
