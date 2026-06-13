import json
import logging
from typing import Any

from recursivist.core import format_size, format_timestamp

from .base import BaseExporter

logger = logging.getLogger(__name__)


class JsonExporter(BaseExporter):
    def export(self, output_path: str) -> None:
        if (
            self.show_full_path
            or self.sort_by_loc
            or self.sort_by_size
            or self.sort_by_mtime
        ):

            def convert_structure_for_json(structure: dict[str, Any]) -> dict[str, Any]:
                result: dict[str, Any] = {}
                _git_markers_here = structure.get("_git_markers", {})
                for k, v in structure.items():
                    if k == "_files":
                        result[k] = []
                        for item in v:
                            if not isinstance(item, tuple):
                                if self.show_git_status:
                                    _gs = _git_markers_here.get(item, "")
                                    entry: Any = {"name": item}
                                    if _gs:
                                        entry["git_status"] = _gs
                                    result[k].append(entry)
                                else:
                                    result[k].append(item)
                                continue

                            file_name = "unknown"
                            full_path = ""
                            loc = 0
                            size = 0
                            mtime = 0

                            if len(item) > 0:
                                file_name = item[0]
                            if len(item) > 1:
                                full_path = item[1]

                            _git_status = (
                                _git_markers_here.get(file_name, "")
                                if self.show_git_status
                                else ""
                            )

                            def _maybe_git(
                                d: dict[str, Any], _gs: str = _git_status
                            ) -> dict[str, Any]:
                                if _gs:
                                    d["git_status"] = _gs
                                return d

                            if (
                                self.sort_by_loc
                                and self.sort_by_size
                                and self.sort_by_mtime
                                and len(item) > 4
                            ):
                                loc = item[2]
                                size = item[3]
                                mtime = item[4]
                                result[k].append(
                                    _maybe_git(
                                        {
                                            "name": file_name,
                                            "path": full_path,
                                            "loc": loc,
                                            "size": size,
                                            "size_formatted": format_size(size),
                                            "mtime": mtime,
                                            "mtime_formatted": format_timestamp(mtime),
                                        }
                                    )
                                )
                            elif (
                                self.sort_by_loc
                                and self.sort_by_mtime
                                and len(item) > 4
                            ):
                                loc = item[2]
                                mtime = item[4]
                                result[k].append(
                                    _maybe_git(
                                        {
                                            "name": file_name,
                                            "path": full_path,
                                            "loc": loc,
                                            "mtime": mtime,
                                            "mtime_formatted": format_timestamp(mtime),
                                        }
                                    )
                                )
                            elif (
                                self.sort_by_size
                                and self.sort_by_mtime
                                and len(item) > 4
                            ):
                                size = item[3]
                                mtime = item[4]
                                result[k].append(
                                    _maybe_git(
                                        {
                                            "name": file_name,
                                            "path": full_path,
                                            "size": size,
                                            "size_formatted": format_size(size),
                                            "mtime": mtime,
                                            "mtime_formatted": format_timestamp(mtime),
                                        }
                                    )
                                )
                            elif (
                                self.sort_by_loc and self.sort_by_size and len(item) > 3
                            ):
                                loc = item[2] if len(item) > 2 else 0
                                size = item[3] if len(item) > 3 else 0
                                result[k].append(
                                    _maybe_git(
                                        {
                                            "name": file_name,
                                            "path": full_path,
                                            "loc": loc,
                                            "size": size,
                                            "size_formatted": format_size(size),
                                        }
                                    )
                                )
                            elif self.sort_by_mtime and len(item) > 2:
                                mtime = item[2] if len(item) > 2 else 0
                                result[k].append(
                                    _maybe_git(
                                        {
                                            "name": file_name,
                                            "path": full_path,
                                            "mtime": mtime,
                                            "mtime_formatted": format_timestamp(mtime),
                                        }
                                    )
                                )
                            elif self.sort_by_size and len(item) > 2:
                                size = item[2] if len(item) > 2 else 0
                                result[k].append(
                                    _maybe_git(
                                        {
                                            "name": file_name,
                                            "path": full_path,
                                            "size": size,
                                            "size_formatted": format_size(size),
                                        }
                                    )
                                )
                            elif self.sort_by_loc and len(item) > 2:
                                loc = item[2] if len(item) > 2 else 0
                                result[k].append(
                                    _maybe_git(
                                        {
                                            "name": file_name,
                                            "path": full_path,
                                            "loc": loc,
                                        }
                                    )
                                )
                            elif self.show_full_path and len(item) > 1:
                                result[k].append(
                                    _maybe_git({"name": file_name, "path": full_path})
                                )
                            else:
                                if _git_status:
                                    result[k].append(
                                        {"name": file_name, "git_status": _git_status}
                                    )
                                else:
                                    result[k].append(file_name)
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

            export_structure = convert_structure_for_json(self.structure)
        else:
            export_structure = self.structure

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
