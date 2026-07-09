# Compare

The `compare` command shows two directory structures side by side and highlights the differences between them.

## Basic Comparison

```bash
recursivist compare dir1 dir2
```

Both directories must exist. The two trees are printed in labeled, color-coded panels with a legend.

## Reading the Output

Highlighting marks what is unique to each side:

- Items present in both directories are shown normally.
- Items unique to the first directory (`dir1`) are highlighted with a **green** background.
- Items unique to the second directory (`dir2`) are highlighted with a **red** background.

A legend at the bottom explains the scheme, and notes any active options such as metric display, depth limits, or applied patterns.

## File Statistics

Include metrics in the comparison to surface differences beyond structure — for example, which files grew or were modified more recently. As elsewhere, `--sort-by-loc`/`-size`/`-mtime` sort by and show a metric, `--loc`/`--size`/`--mtime` show one without reordering, and only the first sorting flag takes effect:

```bash
recursivist compare dir1 dir2 --sort-by-loc
recursivist compare dir1 dir2 --sort-by-size
recursivist compare dir1 dir2 --mtime               # show mtime, keep default order
recursivist compare dir1 dir2 --sort-by-loc --size  # sort by LOC, show LOC and size
```

## Saving as HTML

By default the comparison is printed to the terminal. Save it as a self-contained, two-column HTML document instead with `--save`:

```bash
recursivist compare dir1 dir2 --save
```

This writes `comparison.html` to the current directory. Change the location or filename:

```bash
recursivist compare dir1 dir2 --save --output-dir ./reports --prefix project-diff
```

When saving to HTML, the `emoji` icon style is used by default for cross-platform consistency; override it with `--icon-style nerd`.

## Filtering and Depth

The same filtering, depth, and full-path options as the other commands apply to both directories:

```bash
recursivist compare dir1 dir2 --exclude "node_modules .git"
recursivist compare dir1 dir2 --exclude-ext ".pyc .log"
recursivist compare dir1 dir2 --exclude-pattern "*.test.js"
recursivist compare dir1 dir2 --include-pattern "*.py" "*.md"
recursivist compare dir1 dir2 --ignore-file .gitignore
recursivist compare dir1 dir2 --depth 3
recursivist compare dir1 dir2 --full-path
recursivist compare dir1 dir2 --git-status
recursivist compare dir1 dir2 --sort-by-git-status
```

See [Pattern Filtering](pattern-filtering.md) for details.

!!! note
`compare` supports every sorting and display flag, including the Git-status flags (`--git-status` and `--sort-by-git-status`), the metric sorts, the display-only `--loc`/`--size`/`--mtime`, and `--sort-by-similarity`. When Git status is enabled, each directory's status is read independently against its own repository, so both sides are annotated correctly even when they belong to different repos. Also note that `-f` here is shorthand for `--save`, not `--format`.

## Use Cases

Comparing structures is useful for tracking how a project changes over time:

```bash
# Two versions of a project
recursivist compare project-v1.0 project-v2.0 --exclude "node_modules .git"

# Two Git branches (checked out into separate directories)
git clone -b main repo main-branch
git clone -b feature/x repo feature-branch
recursivist compare main-branch feature-branch

# Source against a build, focusing on JavaScript
recursivist compare src dist --include-pattern "*.js" --sort-by-size

# Original files against a backup
recursivist compare original-files backup-files --full-path
```

## HTML Output

The saved HTML document contains:

- A side-by-side, two-column comparison
- Color-coded highlighting of the differences
- A legend explaining the scheme and any active options

This is convenient for sharing results or keeping a record of structural changes.

## Terminal Compatibility

The side-by-side terminal view is best in a terminal with Unicode and ANSI color support and enough width to fit both panels. On narrow terminals, prefer the HTML export (`--save`).
