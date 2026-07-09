# Quick Start Guide

This guide covers the essentials. After [installing Recursivist](installation.md), you can run it in any directory.

## Visualize a Directory

Display the current directory as a colored tree in the terminal:

```bash
recursivist visualize
```

Output:

```
📁 my-project
├── 📄 README.md
├── 📄 setup.py
├── 📄 requirements.txt
└── 📁 src
    ├── 📄 main.py
    ├── 📄 utils.py
    └── 📁 tests
        ├── 📄 test_main.py
        └── 📄 test_utils.py
```

Files are listed before subdirectories, and each file type is given its own color. To visualize a different directory, pass its path:

```bash
recursivist visualize /path/to/your/directory
```

## Show File Statistics

Display and sort by lines of code, file size, or modification time. The `--sort-by-*` flags both sort and annotate; the bare `--loc`/`--size`/`--mtime` flags annotate without reordering:

```bash
recursivist visualize --sort-by-loc     # sort by and show lines of code
recursivist visualize --sort-by-size    # sort by and show file sizes
recursivist visualize --sort-by-mtime   # sort by and show modification times
recursivist visualize --sort-by-loc --size   # sort by LOC, show LOC and size
```

Flags are read left to right: only the first sorting flag takes effect (a second `--sort-by-*` is ignored), and annotations appear in the order given.

With `--sort-by-loc`:

```
📁 my-project (1262 lines)
├── 📄 README.md (124 lines)
├── 📄 setup.py (65 lines)
├── 📄 requirements.txt (18 lines)
└── 📁 src (1055 lines)
    ├── 📄 main.py (245 lines)
    ├── 📄 utils.py (157 lines)
    └── 📁 tests (653 lines)
        ├── 📄 test_main.py (412 lines)
        └── 📄 test_utils.py (241 lines)
```

## Show Git Status

Annotate files with their Git status when the directory is inside a repository:

```bash
recursivist visualize --git-status
```

Markers are `[U]` untracked, `[M]` modified, `[A]` added, and `[D]` deleted.

## Export a Directory Structure

Export to one or more of `txt`, `json`, `html`, `md`, `svg`, or `rst` (Markdown is the default):

```bash
recursivist export                       # Markdown (structure.md)
recursivist export --format html
recursivist export --format json
recursivist export --format "txt md json"   # multiple at once
```

## Compare Two Directories

Show two structures side by side with differences highlighted:

```bash
recursivist compare dir1 dir2
```

Save the comparison as an HTML file instead of printing it:

```bash
recursivist compare dir1 dir2 --save
```

## Scan a GitHub Repository

`visualize`, `export`, and `compare` accept a GitHub repository URL wherever they accept a directory:

```bash
recursivist visualize https://github.com/owner/repo
recursivist export https://github.com/owner/repo --format md
recursivist compare ./my-fork https://github.com/owner/repo
```

Add a `/tree/<ref>` selector to pin a branch, tag, or commit (optionally followed by a subtree to scan), and set `GITHUB_TOKEN` (or `GH_TOKEN`) to raise rate limits and reach private repositories. See the [CLI Reference](../reference/cli-reference.md#github-repositories) for the accepted URL forms and the options that apply to a GitHub input.

## Common Options

These options work across `visualize`, `export`, and `compare`:

```bash
# Exclude directories
recursivist visualize --exclude "node_modules .git"

# Exclude file extensions (leading dot optional)
recursivist visualize --exclude-ext ".pyc .log"

# Exclude by glob pattern (default) or regex (--regex)
recursivist visualize --exclude-pattern "*.test.js"
recursivist visualize --exclude-pattern "^test_.*\.py$" --regex

# Include only matching files
recursivist visualize --include-pattern "*.py" "*.md"

# Respect a .gitignore-style file
recursivist visualize --ignore-file .gitignore

# Limit traversal depth
recursivist visualize --depth 2

# Show full paths instead of bare filenames
recursivist visualize --full-path
```

## Shell Completion

Recursivist supports tab completion for Bash, Zsh, Fish, and PowerShell. The quickest setup uses Typer's built-in installer:

```bash
recursivist --install-completion
```

See the [Shell Completion guide](../user-guide/shell-completion.md) for per-shell instructions.

## Next Steps

- [Visualization](../user-guide/visualization.md) — customize terminal output
- [Pattern Filtering](../user-guide/pattern-filtering.md) — precise include/exclude control
- [Export Formats](../reference/export-formats.md) — every output format in detail
- [CLI Reference](../reference/cli-reference.md) — all commands and options
