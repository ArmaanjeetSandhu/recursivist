"""Nerd Font icon mappings for files and directories.

This module provides icon lookup utilities based on Nerd Font glyph codes.
Icons are resolved in priority order:

1. Exact filename match (e.g., ``Dockerfile``, ``package.json``)
2. File extension match (e.g., ``.py``, ``.ts``)
3. Named folder match (e.g., ``node_modules``, ``.git``)
4. Generic fallback icons for unknown files and directories
"""

import os

DEFAULT_EMOJI_FILE = "📄"
DEFAULT_EMOJI_FOLDER = "📁"

DEFAULT_NERD_FILE = "\uf15b"  # 📄 nf-fa-file
DEFAULT_NERD_FOLDER = "\uf07b"  # 📁 nf-fa-folder

EXACT_MATCH_ICONS = {
    # Git
    ".gitignore": "\ue702",  # nf-dev-git
    ".gitconfig": "\ue702",
    ".gitattributes": "\ue702",
    ".gitmodules": "\ue702",
    # Docker
    "dockerfile": "\uf308",  # nf-linux-docker
    "docker-compose.yml": "\uf308",
    "docker-compose.yaml": "\uf308",
    ".dockerignore": "\uf308",
    # Package & Lock Files
    "package.json": "\ue718",  # nf-dev-npm
    "package-lock.json": "\uf023",  # nf-fa-lock
    "yarn.lock": "\uf023",
    "pnpm-lock.yaml": "\uf023",
    "requirements.txt": "\ue73c",  # nf-dev-python
    "pipfile": "\ue73c",
    "pipfile.lock": "\uf023",
    "pyproject.toml": "\ue73c",
    "uv.lock": "\uf023",  # From your uploaded uv.lock
    "cargo.toml": "\ue7a8",  # nf-dev-rust
    "cargo.lock": "\uf023",
    "go.mod": "\ue624",  # nf-custom-go
    "go.sum": "\uf023",
    "gemfile": "\ue739",  # nf-dev-ruby
    "gemfile.lock": "\uf023",
    # Build & Config
    "makefile": "\ue673",  # nf-seti-makefile
    "cmakelists.txt": "\ue673",
    "license": "\uf48a",  # nf-oct-law
    "license.md": "\uf48a",
    "license.txt": "\uf48a",
    "changelog.md": "\uf48a",
}

EXTENSION_ICONS = {
    # Programming Languages
    ".py": "\ue73c",  # Python
    ".pyc": "\ue73c",
    ".js": "\ue74e",  # JavaScript
    ".mjs": "\ue74e",
    ".ts": "\ue628",  # TypeScript
    ".jsx": "\ue7ba",  # React
    ".tsx": "\ue7ba",
    ".html": "\ue736",  # HTML
    ".htm": "\ue736",
    ".css": "\ue749",  # CSS
    ".scss": "\ue74b",  # Sass
    ".sass": "\ue74b",
    ".less": "\ue758",  # Less
    ".go": "\ue624",  # Go
    ".rs": "\ue7a8",  # Rust
    ".java": "\ue738",  # Java
    ".class": "\ue738",
    ".jar": "\ue738",
    ".c": "\ue61e",  # C
    ".h": "\ue61e",
    ".cpp": "\ue61d",  # C++
    ".hpp": "\ue61d",
    ".cc": "\ue61d",
    ".cs": "\uf81a",  # C#
    ".rb": "\ue739",  # Ruby
    ".php": "\ue73d",  # PHP
    ".swift": "\ue755",  # Swift
    ".kt": "\ue634",  # Kotlin
    ".dart": "\ue798",  # Dart
    ".vue": "\ufd42",  # Vue
    ".svelte": "\ue697",  # Svelte
    ".lua": "\ue620",  # Lua
    # Shell & Scripts
    ".sh": "\uf489",  # Shell
    ".bash": "\uf489",
    ".zsh": "\uf489",
    ".fish": "\uf489",
    ".bat": "\ue70f",  # Windows
    ".ps1": "\ue70f",
    # Data, Config, & Docs
    ".json": "\ue60b",  # JSON
    ".yaml": "\uf481",  # YAML
    ".yml": "\uf481",
    ".toml": "\uf481",
    ".xml": "\ue619",  # XML
    ".csv": "\uf1c6",  # nf-fa-file_excel_o
    ".md": "\ue609",  # Markdown
    ".txt": "\uf15c",  # nf-fa-file_text_o
    ".ini": "\uf415",  # nf-oct-settings
    ".env": "\uf415",
    ".conf": "\uf415",
    ".cfg": "\uf415",
    # Media & Archives
    ".png": "\uf1c5",  # Images
    ".jpg": "\uf1c5",
    ".jpeg": "\uf1c5",
    ".gif": "\uf1c5",
    ".svg": "\uf1c5",
    ".ico": "\uf1c5",
    ".mp4": "\uf1c8",  # Video
    ".mkv": "\uf1c8",
    ".mp3": "\uf1c7",  # Audio
    ".wav": "\uf1c7",
    ".pdf": "\uf1c1",  # PDF
    ".zip": "\uf410",  # Archives
    ".tar": "\uf410",
    ".gz": "\uf410",
    ".rar": "\uf410",
    ".7z": "\uf410",
    # Databases
    ".db": "\uf1c0",  # nf-fa-database
    ".sqlite": "\uf1c0",
    ".sql": "\uf1c0",
}

FOLDER_ICONS = {
    "node_modules": "\ue718",  # npm folder
    ".git": "\ue5fb",  # git folder
    ".github": "\uf408",  # github folder
    "src": "\uf07c",  # open folder
    "tests": "\uf430",  # beaker/test folder
    "docs": "\uf02d",  # book/docs folder
    ".venv": "\ue73c",  # python folder
    "venv": "\ue73c",
}


def get_icon(filename: str, is_dir: bool = False, style: str = "emoji") -> str:
    """Return the icon glyph for a file or directory based on style.

    Resolution order for files:

    1. Exact filename match in ``EXACT_MATCH_ICONS`` (case-insensitive).
    2. File extension match in ``EXTENSION_ICONS``.
    3. ``DEFAULT_NERD_FILE`` fallback.

    For directories, ``FOLDER_ICONS`` is consulted first and
    ``DEFAULT_FOLDER`` is used when no entry matches.

    Args:
        filename: Name of the file or directory (basename only, not a full
            path). Matched case-insensitively.
        is_dir: When ``True``, treat *filename* as a directory name and look
            up folder-specific icons instead of file icons.

    Returns:
        A single Unicode character containing the matching Nerd Font glyph.
    """
    if style == "emoji":
        return DEFAULT_EMOJI_FOLDER if is_dir else DEFAULT_EMOJI_FILE

    filename_lower = filename.lower()

    if is_dir:
        return FOLDER_ICONS.get(filename_lower, DEFAULT_NERD_FOLDER)

    if filename_lower in EXACT_MATCH_ICONS:
        return EXACT_MATCH_ICONS[filename_lower]

    _, ext = os.path.splitext(filename_lower)
    return EXTENSION_ICONS.get(ext, DEFAULT_NERD_FILE)
