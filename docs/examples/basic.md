# Basic Examples

Common, everyday Recursivist commands. For deeper dives, see the other example pages.

## Visualization

```bash
# Current directory
recursivist visualize

# A specific directory
recursivist visualize ~/projects/my-app

# Limit depth (useful for large projects)
recursivist visualize --depth 2

# Show full paths instead of bare filenames
recursivist visualize --full-path

# Use Nerd Font icons for this run
recursivist visualize --icon-style nerd
```

A depth-limited tree marks where it was cut off:

```
📁 my-project
├── 📄 README.md
└── 📁 src
    ├── 📄 main.py
    ├── 📄 utils.py
    └── 📁 tests
        ⋯ (max depth reached)
```

## File Statistics

```bash
recursivist visualize --sort-by-loc     # sort by and show lines of code
recursivist visualize --sort-by-size    # sort by and show file sizes
recursivist visualize --sort-by-mtime   # sort by and show modification times
recursivist visualize --loc             # show lines of code, keep default order
recursivist visualize --sort-by-loc --size   # sort by LOC, show LOC and size
```

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

## Git Status

Inside a Git repository, show each file's status (`[U]` untracked, `[M]` modified, `[A]` added, `[D]` deleted):

```bash
recursivist visualize --git-status
```

## Exclusions

```bash
# Exclude directories
recursivist visualize --exclude "node_modules .git"

# Exclude file extensions (leading dot optional)
recursivist visualize --exclude-ext ".pyc .log"

# Combine them
recursivist visualize --exclude "node_modules .git" --exclude-ext ".pyc .log"
```

## Exports

```bash
# Markdown (default), writes structure.md
recursivist export --format md

# Several formats at once
recursivist export --format "txt md json"

# Choose an output directory and filename prefix
recursivist export --format html --output-dir ./docs --prefix project

# Include statistics
recursivist export --format html --sort-by-loc --size
```

## Comparisons

```bash
# Side-by-side in the terminal
recursivist compare dir1 dir2

# Save as HTML (writes comparison.html)
recursivist compare dir1 dir2 --save

# With statistics
recursivist compare dir1 dir2 --sort-by-loc
```

## Configuration and Version

```bash
# Make Nerd Font icons the default
recursivist config set icon-style nerd

# Check the installed version
recursivist version
```

## Next Steps

- [Filtering Examples](filtering.md)
- [Export Examples](export.md)
- [Compare Examples](compare.md)
- [Advanced Examples](advanced.md)
