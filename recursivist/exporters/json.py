"""JSON tree exporter.

Serializes the scanned structure to JSON. Without any detail flags, files collapse to
bare names; with LOC, size, mtime, or Git status enabled, each file becomes an object
carrying the requested fields.

Every directory is written as an object with a fixed set of keys, of which only the ones
that apply are present. Its subdirectories are nested under ``subdirectories``, keyed by
name, which keeps a directory's own fields and the names of its subdirectories in
separate namespaces.
"""

import json
from collections.abc import Callable
from typing import Any

from recursivist._models import Directory, FileEntry
from recursivist.metrics import format_size, format_timestamp
from recursivist.scanner import iter_subdirectories
from recursivist.sorting import sort_files_by_type

from .base import BaseExporter, write_text


def _traversal_flags(directory: Directory) -> dict[str, Any]:
    """Return the keys recording why *directory* was not fully traversed.

    Holds ``max_depth_reached`` (with ``hidden_contents`` when the directory is not
    empty) for a directory cut off by the depth limit and ``symlink_loop`` for one that
    links back to an ancestor. Empty for a directory that was read in full.
    """
    flags: dict[str, Any] = {}
    if directory.max_depth_reached:
        flags["max_depth_reached"] = True
    if directory.hidden_contents:
        flags["hidden_contents"] = True
    if directory.symlink_loop:
        flags["symlink_loop"] = True
    return flags


def _subdirectories_to_json(
    directory: Directory, convert: Callable[[Directory], dict[str, Any]]
) -> dict[str, Any]:
    """Return the ``subdirectories`` key for *directory*, or nothing if it has none.

    Each subdirectory is converted with *convert* and stored under its name, in the
    order the other formats list them.
    """
    subdirectories = {
        name: convert(content) for name, content in iter_subdirectories(directory)
    }
    return {"subdirectories": subdirectories} if subdirectories else {}


class JsonExporter(BaseExporter):
    """Exporter that serializes the structure to JSON."""

    extension = "json"

    def export(self, output_path: str) -> None:
        """Write the structure to *output_path* as JSON.

        The payload records the root name, the (possibly detailed) structure, the
        resolved sort key, and which detail flags were active. File entries are emitted
        as bare names unless a detail flag (full path, LOC, size, mtime, or Git status)
        requires the richer object form. When present, the per-file metric fields are
        emitted in the resolved display order, with the Git status always last.

        Args:
            output_path: Path the ``.json`` file is written to.
        """
        has_detail = self.show_full_path or bool(self.metrics) or self.show_git_status

        def file_to_json(
            entry: FileEntry, git_markers: dict[str, str]
        ) -> dict[str, Any]:
            """Encode a single file for the detail JSON form.

            The entry is rendered with exactly the keys the active flags call for, with
            metric fields following the resolved display order.
            """
            git_status = git_markers.get(entry.name, "") if self.show_git_status else ""
            result: dict[str, Any] = {"name": entry.name, "path": entry.path}
            for metric in self.metrics:
                if metric == "loc":
                    result["loc"] = entry.loc
                elif metric == "size":
                    result["size"] = entry.size
                    result["size_formatted"] = format_size(entry.size)
                elif metric == "mtime":
                    result["mtime"] = entry.mtime
                    result["mtime_formatted"] = format_timestamp(
                        entry.mtime, self.date_format
                    )
            if git_status:
                result["git_status"] = git_status
            return result

        def detailed(directory: Directory) -> dict[str, Any]:
            """Recursively convert *directory* to its detailed JSON form.

            Encodes each file via `file_to_json` and carries through the enabled
            aggregate metrics (adding their formatted variants). Git status is reported
            on the files themselves, so the directory's marker map is not written.

            Args:
                directory: Directory to convert.

            Returns:
                The JSON-serializable mapping for this subtree.
            """
            result: dict[str, Any] = {}
            if directory.files:
                sorted_files = sort_files_by_type(
                    directory.files, self.sort_key, directory.git_markers
                )
                result["files"] = [
                    file_to_json(item, directory.git_markers) for item in sorted_files
                ]
            if self.show_loc and directory.loc is not None:
                result["loc"] = directory.loc
            if self.show_size and directory.size is not None:
                result["size"] = directory.size
                result["size_formatted"] = format_size(directory.size)
            if self.show_mtime and directory.mtime is not None:
                result["mtime"] = directory.mtime
                result["mtime_formatted"] = format_timestamp(
                    directory.mtime, self.date_format
                )
            result.update(_traversal_flags(directory))
            result.update(_subdirectories_to_json(directory, detailed))
            return result

        def names_only(directory: Directory) -> dict[str, Any]:
            """Recursively convert *directory*, collapsing its files to bare names.

            Used when no detail flags are active: each file is reduced to its name, and
            any Git status markers the directory carries are written as a
            ``git_markers`` map.

            Args:
                directory: Directory to convert.

            Returns:
                The JSON-serializable mapping for this subtree.
            """
            result: dict[str, Any] = {}
            if directory.files:
                sorted_files = sort_files_by_type(
                    directory.files, self.sort_key, directory.git_markers
                )
                result["files"] = [entry.name for entry in sorted_files]
            result.update(_traversal_flags(directory))
            if directory.git_markers:
                result["git_markers"] = directory.git_markers
            result.update(_subdirectories_to_json(directory, names_only))
            return result

        convert = detailed if has_detail else names_only

        write_text(
            output_path,
            json.dumps(
                {
                    "root": self.root_name,
                    "structure": convert(self.structure),
                    "sort_key": self.sort_key,
                    "metric_order": list(self.metrics),
                    "show_loc": self.show_loc,
                    "show_size": self.show_size,
                    "show_mtime": self.show_mtime,
                    "show_git_status": self.show_git_status,
                },
                indent=2,
            ),
        )
