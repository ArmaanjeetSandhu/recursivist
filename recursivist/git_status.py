"""Git status lookup.

Wraps ``git status --porcelain`` and maps changed/untracked paths back to a location
relative to the directory being visualised. Pure standard library.
"""

import os
import sys


class GitStatusError(Exception):
    """Raised when Git status cannot be read for a directory.

    The message names the cause: Git's own error output when a Git command fails, or the
    operating-system error when Git cannot be executed.
    """


def _decode_path(raw: bytes) -> str:
    """Decode path bytes emitted by Git the way the OS decodes filenames.

    Bytes that are invalid in the filesystem encoding become surrogate escapes, so every
    path decodes and matches the name the filesystem APIs report for the same file.

    Args:
        raw: Path bytes from Git's output.

    Returns:
        The decoded path.
    """
    return raw.decode(sys.getfilesystemencoding(), errors="surrogateescape")


def _run_git(args: list[str], cwd: str) -> bytes:
    """Run a Git command and return its standard output.

    Args:
        args: Arguments to pass to ``git``.
        cwd: Directory to run the command in.

    Returns:
        The command's raw standard output.

    Raises:
        GitStatusError: If Git cannot be executed or exits with a non-zero status.
    """
    import subprocess

    try:
        result = subprocess.run(["git", *args], cwd=cwd, capture_output=True)
    except OSError as e:
        raise GitStatusError(f"could not run git: {e}") from e
    if result.returncode != 0:
        detail = result.stderr.decode(errors="replace").strip()
        raise GitStatusError(
            detail or f"git {args[0]} exited with status {result.returncode}"
        )
    return result.stdout


def get_git_status(directory: str) -> dict[str, str]:
    """Get Git status for files relative to a given directory.

    Runs ``git status --porcelain -z --untracked-files=all`` from the repository root
    and maps every changed/untracked path back to a path relative to *directory*,
    filtering out files that live outside of it.

    Status characters returned:

    - ``'U'``: Untracked (``??`` in porcelain output)
    - ``'M'``: Modified (working-tree or staged modification)
    - ``'A'``: Added / staged for the first time (includes renames)
    - ``'D'``: Deleted (working-tree or staged deletion)

    Args:
        directory: Absolute path to the directory being visualised. Must be inside a Git
            repository.

    Returns:
        ``{relative_path: status_char}`` where *relative_path* uses forward slashes
        regardless of OS. The mapping is empty when nothing under *directory* is changed
        or untracked.

    Raises:
        GitStatusError: If Git is not installed, *directory* is not inside a Git work
            tree, or a Git command fails.
    """
    git_root = os.path.realpath(
        _decode_path(_run_git(["rev-parse", "--show-toplevel"], directory)).strip()
    )
    directory = os.path.realpath(directory)
    porcelain = _decode_path(
        _run_git(["status", "--porcelain", "-z", "--untracked-files=all"], git_root)
    )

    status_map: dict[str, str] = {}
    records = porcelain.split("\0")
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

        abs_file = os.path.normpath(os.path.join(git_root, path.replace("/", os.sep)))
        try:
            rel = os.path.relpath(abs_file, directory)
            outside = rel == os.pardir or rel.startswith(os.pardir + os.sep)
            if not outside:
                status_map[rel.replace(os.sep, "/")] = status
        except ValueError:
            pass

    return status_map
