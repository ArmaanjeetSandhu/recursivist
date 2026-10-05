# Quick Start Guide

This guide covers the essentials. After [installing Recursivist](installation.md), you can run it in any directory.

## Visualize a Directory

Display the current directory as a colored tree in the terminal:

```bash
recursivist visualize
```

Output:

<div class="terminal-demo">
  <div class="terminal-header">
    <div class="terminal-buttons">
      <div class="terminal-button red"></div>
      <div class="terminal-button yellow"></div>
      <div class="terminal-button green"></div>
    </div>
    <div class="terminal-title">recursivist-demo ~ bash</div>
  </div>
  <div class="terminal-body">
    <div class="terminal-output">
      <pre>📂 my-project
├── <span style="color: #f1fa8c;">📄 README.md</span>
├── <span style="color: #83e43d;">📄 setup.py</span>
├── <span style="color: #bd93f9;">📄 requirements.txt</span>
└── 📂 src
    ├── <span style="color: #83e43d;">📄 main.py</span>
    ├── <span style="color: #83e43d;">📄 utils.py</span>
    └── 📂 tests
        ├── <span style="color: #83e43d;">📄 test_main.py</span>
        └── <span style="color: #83e43d;">📄 test_utils.py</span></pre>
    </div>
  </div>
</div>

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

With `--sort-by-loc`:

<div class="terminal-demo">
  <div class="terminal-header">
    <div class="terminal-buttons">
      <div class="terminal-button red"></div>
      <div class="terminal-button yellow"></div>
      <div class="terminal-button green"></div>
    </div>
    <div class="terminal-title">recursivist-demo ~ bash</div>
  </div>
  <div class="terminal-body">
    <div class="terminal-output">
      <pre>📂 my-project (1262 lines)
├── <span style="color: #f1fa8c;">📄 README.md</span> (124 lines)
├── <span style="color: #83e43d;">📄 setup.py</span> (65 lines)
├── <span style="color: #bd93f9;">📄 requirements.txt</span> (18 lines)
└── 📂 src (1055 lines)
    ├── <span style="color: #83e43d;">📄 main.py</span> (245 lines)
    ├── <span style="color: #83e43d;">📄 utils.py</span> (157 lines)
    └── 📂 tests (653 lines)
        ├── <span style="color: #83e43d;">📄 test_main.py</span> (412 lines)
        └── <span style="color: #83e43d;">📄 test_utils.py</span> (241 lines)</pre>
    </div>
  </div>
</div>

[Sorting and Statistics](../user-guide/sorting-and-statistics.md) explains how these flags combine.

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

See [GitHub Repositories](../user-guide/github-repositories.md) for pinning a branch or subtree, private repositories, and the options that apply to a GitHub input.

## Common Options

These options work across `visualize`, `export`, and `compare`:

```bash
# Exclude directories
recursivist visualize --exclude node_modules --exclude .git

# Exclude file extensions (leading dot optional)
recursivist visualize --exclude-ext .pyc --exclude-ext .log

# Exclude by glob pattern (default) or regex (--regex)
recursivist visualize --exclude-pattern "*.test.js"
recursivist visualize --exclude-pattern "^test_.*\.py$" --regex

# Include only matching files
recursivist visualize --include-pattern "*.py" --include-pattern "*.md"

# Respect a .gitignore-style file (not read unless you ask)
recursivist visualize --ignore-file .gitignore

# Limit traversal depth
recursivist visualize --depth 2

# Show full paths instead of bare filenames
recursivist visualize --full-path
```

## Save Your Defaults

Options you pass on every run can be saved once:

```bash
recursivist config set ignore-file .gitignore
recursivist config set exclude node_modules .git
```

See [Configuration](../user-guide/configuration.md) for per-project settings and the order of precedence.

## Shell Completion

Recursivist supports tab completion for Bash, Zsh, Fish, and PowerShell. The quickest setup uses Typer's built-in installer:

```bash
recursivist --install-completion
```

See the [Shell Completion guide](../user-guide/shell-completion.md) for per-shell instructions.

## Next Steps

- [User Guide](../user-guide/basic-usage.md) — each command and option explained
- [Recipes](../recipes/index.md) — worked examples for common jobs
- [CLI Reference](../reference/cli-reference.md) — all commands and options
