# Visualization

The `visualize` command renders a directory structure as a color-coded tree in the terminal. This guide covers its display options.

## Basic Visualization

```bash
recursivist visualize                  # current directory
recursivist visualize /path/to/project # a specific directory
```

A progress indicator is shown while the directory is scanned, then the tree is printed:

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

Within each directory, files appear before subdirectories. Files are ordered by extension and then name.

## Color Coding

Each file extension is assigned a unique color, generated deterministically from the extension itself. The same extension always gets the same color, and the algorithm spaces colors apart so different types stay visually distinct.

## Icon Styles

Use file-type-specific Nerd Font glyphs instead of the generic emoji for a single run:

```bash
recursivist visualize --icon-style nerd
```

To make a style the default, see [Basic Usage](basic-usage.md#icon-styles).

## File Statistics

### Lines of Code

Count lines per file and total them per directory:

```bash
recursivist visualize --sort-by-loc
```

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

### File Sizes

Display sizes with units (B, KB, MB, GB):

```bash
recursivist visualize --sort-by-size
```

```
📁 my-project (57.1 KB)
├── 📄 README.md (4.2 KB)
├── 📄 setup.py (3.8 KB)
├── 📄 requirements.txt (512 B)
└── 📁 src (48.6 KB)
    ├── 📄 main.py (12.4 KB)
    ├── 📄 utils.py (8.2 KB)
    └── 📁 tests (28.0 KB)
        ├── 📄 test_main.py (18.6 KB)
        └── 📄 test_utils.py (9.4 KB)
```

### Modification Times

Show when files were last modified, with recency-aware formatting (`Today HH:MM`, `Yesterday HH:MM`, a weekday and time within the last week, `Mon DD` earlier this year, or `YYYY-MM-DD` for older files):

```bash
recursivist visualize --sort-by-mtime
```

```
📁 my-project (Today 14:30)
├── 📄 README.md (Today 10:15)
├── 📄 setup.py (Today 09:00)
├── 📄 requirements.txt (Yesterday 16:00)
└── 📁 src (Today 14:30)
    ├── 📄 main.py (Today 14:30)
    ├── 📄 utils.py (Today 09:15)
    └── 📁 tests (Today 14:25)
        ├── 📄 test_main.py (Today 14:25)
        └── 📄 test_utils.py (Yesterday 18:10)
```

### Combining Statistics

Metrics are combinable and always appear in the order LOC, size, mtime:

```bash
recursivist visualize --sort-by-loc --sort-by-size --sort-by-mtime
```

```
📁 my-project (1262 lines, 57.1 KB, Today 14:30)
├── 📄 README.md (124 lines, 4.2 KB, Today 10:15)
├── 📄 setup.py (65 lines, 3.8 KB, Today 09:00)
├── 📄 requirements.txt (18 lines, 512 B, Yesterday 16:00)
└── 📁 src (1055 lines, 48.6 KB, Today 14:30)
    ├── 📄 main.py (245 lines, 12.4 KB, Today 14:30)
    ├── 📄 utils.py (157 lines, 8.2 KB, Today 09:15)
    └── 📁 tests (653 lines, 28.0 KB, Today 14:25)
        ├── 📄 test_main.py (412 lines, 18.6 KB, Today 14:25)
        └── 📄 test_utils.py (241 lines, 9.4 KB, Yesterday 18:10)
```

When a metric sort is active, files are ordered by that metric (descending) rather than by name.

## Grouping by Name Similarity

```bash
recursivist visualize --sort-by-similarity
```

This groups files with similar names next to each other (for example, `main.py` beside `main.js`). It replaces the default extension-and-name ordering but is overridden by any active metric sort.

## Git Status

Inside a Git repository, annotate files with their status:

```bash
recursivist visualize --git-status
```

```
📁 my-project
├── 📄 README.md
├── 📄 newfile.txt [U]
└── 📁 src
    ├── 📄 main.py
    └── 📄 utils.py [M]
```

Markers are `[U]` untracked, `[M]` modified, `[A]` added, and `[D]` deleted. Deleted files are also shown struck through, and a file deleted from disk is still listed so the change is visible. If the directory isn't inside a repository (or has no changes), no markers are added.

## Directory Depth Control

Limit how deep the tree goes — useful for large projects:

```bash
recursivist visualize --depth 2
```

```
📁 my-project
├── 📄 README.md
└── 📁 src
    ├── 📄 main.py
    ├── 📄 utils.py
    └── 📁 tests
        ⋯ (max depth reached)
```

## Full Path Display

Show absolute paths instead of bare filenames:

```bash
recursivist visualize --full-path
```

```
📁 my-project
├── 📄 /home/user/my-project/README.md
└── 📁 src
    └── 📄 /home/user/my-project/src/main.py
```

## Filtering

All of Recursivist's filtering options apply to `visualize`:

```bash
recursivist visualize --exclude "node_modules .git"
recursivist visualize --exclude-ext ".pyc .log"
recursivist visualize --exclude-pattern "*.test.js" "*.spec.js"
recursivist visualize --exclude-pattern "^test_.*\.py$" --regex
recursivist visualize --include-pattern "*.py" "*.md"
recursivist visualize --ignore-file .gitignore
```

See [Pattern Filtering](pattern-filtering.md) for details.

## Performance Tips

For very large directories:

1. Limit depth with `--depth`.
2. Exclude heavy directories (`node_modules`, `.git`, build output) with `--exclude`.
3. Use include patterns to focus on the part of the tree you care about.
4. Be aware that `--sort-by-loc` reads every file to count lines, which is slower on large repositories.

## Related Commands

- [Export](export.md): save structures to files
- [Compare](compare.md): diff two directories

For every option, see the [CLI Reference](../reference/cli-reference.md).
