"""Shared base class for directory-structure exporters.

Defines [`BaseExporter`][recursivist.exporters.base.BaseExporter], which stores the
scanned structure and the resolved display options common to every output format.
Concrete exporters subclass it and implement
[`BaseExporter.export`][recursivist.exporters.base.BaseExporter.export].

[`write_text`][recursivist.exporters.base.write_text] is the single place export files
are written: it makes undecodable file names encodable and writes atomically, the same
way for every format.
"""

import contextlib
import errno
import os
import re
import secrets
import shutil

from recursivist._models import Directory
from recursivist.flags import DisplayOptions

_SURROGATES = re.compile("[\ud800-\udfff]")
"""Code points that cannot be encoded as UTF-8.

File names that are not valid in the filesystem encoding reach Python with their
undecodable bytes mapped to lone surrogates (``surrogateescape``).
"""


def write_text(output_path: str, text: str) -> None:
    """Atomically write *text* to *output_path* as UTF-8.

    Lone surrogates, which stand in for the undecodable bytes of a non-UTF-8 file name,
    are replaced with U+FFFD to guarantee that the text encodes.

    The text is written to a temporary file in the destination directory, which is then
    renamed over the destination. A failure at any point leaves an existing file
    untouched and creates no partial one. Symbolic links are followed and the
    permissions of a file being overwritten are kept, as with a plain ``open``. A
    destination that exists but is not a regular file (such as ``/dev/stdout``) cannot
    be replaced, so it is written to directly.

    Args:
        output_path: Path the file is written to.
        text: Content to write.

    Raises:
        OSError: If the file cannot be written.
    """
    text = _SURROGATES.sub("\ufffd", text)
    target = os.path.realpath(output_path)
    if os.path.exists(target):
        if not os.path.isfile(target):
            with open(target, "w", encoding="utf-8") as f:
                f.write(text)
            return
        if not os.access(target, os.W_OK):
            raise PermissionError(errno.EACCES, os.strerror(errno.EACCES), output_path)

    temp_path = os.path.join(
        os.path.dirname(target), f".recursivist-{secrets.token_hex(8)}.tmp"
    )
    try:
        with open(temp_path, "x", encoding="utf-8") as f:
            f.write(text)
        with contextlib.suppress(OSError):
            shutil.copymode(target, temp_path)
        os.replace(temp_path, target)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(temp_path)
        raise


class BaseExporter:
    """Common base for the per-format exporters.

    Holds the scanned structure and the resolved
    [`DisplayOptions`][recursivist.flags.DisplayOptions]; the actual output is produced
    by each subclass's [`export`][recursivist.exporters.base.BaseExporter.export]. For
    convenience, the individual pieces of the spec are also exposed as plain attributes
    (``metrics``, ``sort_key``,
    ``show_loc``/``show_size``/``show_mtime``/``show_git_status``) for exporters to read
    directly.

    Attributes:
        extension: Canonical file extension for this format, without a leading dot (e.g.
            ``"md"``). Set by each concrete subclass and used as the single source of
            truth for output filenames, so format aliases that share an exporter (such
            as ``"md"`` and ``"markdown"``) resolve to the same extension.
    """

    extension: str = ""

    def __init__(
        self,
        structure: Directory,
        root_name: str,
        show_full_path: bool = False,
        spec: DisplayOptions | None = None,
        icon_style: str = "emoji",
    ) -> None:
        """Store the structure and display options for an export.

        Args:
            structure: Scanned directory structure to export.
            root_name: Display name of the root directory.
            show_full_path: Whether *structure* holds absolute paths (or GitHub blob
                URLs) to display instead of bare filenames.
            spec: Resolved sorting and annotation directives. Defaults to a plain
                [`DisplayOptions`][recursivist.flags.DisplayOptions] (no sorting, no
                annotations).
            icon_style: Icon style to use, either ``"emoji"`` or ``"nerd"``.
        """
        self.structure = structure
        self.root_name = root_name
        self.show_full_path = show_full_path
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

        Subclasses must override this method; the base implementation always raises
        `NotImplementedError`.
        """
        raise NotImplementedError("Subclasses must implement the export method.")
