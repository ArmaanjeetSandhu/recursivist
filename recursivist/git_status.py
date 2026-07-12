"""Git status lookup.

Wraps ``git status --porcelain`` and maps changed/untracked paths back to a
location relative to the directory being visualised. Pure standard library.
"""

import logging
import os

logger = logging.getLogger(__name__)


def get_git_status(directory: str) -> dict[str, str]:
    """Get Git status for files relative to a given directory.

    Runs ``git status --porcelain -z`` from the repository root and maps every
    changed/untracked path back to a path relative to *directory*, filtering
    out files that live outside of it.

    Status characters returned:
    - ``'U'``: Untracked (``??`` in porcelain output)
    - ``'M'``: Modified (working-tree or staged modification)
    - ``'A'``: Added / staged for the first time (includes renames)
    - ``'D'``: Deleted (working-tree or staged deletion)

    Args:
        directory: Absolute path to the directory being visualised. Must be
            inside a Git repository.

    Returns:
        ``{relative_path: status_char}`` where *relative_path* uses forward
        slashes regardless of OS, or an empty dict when Git is unavailable or
        the directory is not tracked.
    """
    import subprocess

    try:
        root_result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=directory,
            capture_output=True,
            text=True,
        )
        if root_result.returncode != 0:
            return {}
        git_root = root_result.stdout.strip()

        status_result = subprocess.run(
            ["git", "status", "--porcelain", "-z"],
            cwd=git_root,
            capture_output=True,
            text=True,
        )
        if status_result.returncode != 0:
            return {}

        status_map: dict[str, str] = {}
        records = status_result.stdout.split("\0")
        i = 0
        while i < len(records):
            entry = records[i]
            i += 1
            if len(entry) < 4:
                continue
            xy = entry[:2]
            path = entry[3:]

            x, y = xy[0], xy[1]
            if x == "R" or x == "C":
                i += 1
            if x == "?" and y == "?":
                status = "U"
            elif x == "D" or y == "D":
                status = "D"
            elif x == "A" or x == "R":
                status = "A"
            else:
                status = "M"

            abs_file = os.path.normpath(
                os.path.join(git_root, path.replace("/", os.sep))
            )
            try:
                rel = os.path.relpath(abs_file, directory)
                if not rel.startswith(".."):
                    status_map[rel.replace(os.sep, "/")] = status
            except ValueError:
                pass

        return status_map
    except Exception as e:
        logger.debug(f"Could not get git status for {directory}: {e}")
        return {}
