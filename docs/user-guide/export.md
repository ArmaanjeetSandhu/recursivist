# Export

The `export` command writes a directory structure to one or more files. Nothing is printed to the terminal — each requested format produces its own file.

## Basic Usage

```bash
recursivist export                       # Markdown (the default), writes structure.md
recursivist export --format html         # a specific format
recursivist export /path/to/project --format json
```

The format flag accepts `txt`, `json`, `html`, `md`, `svg`, and `rst`. When omitted, it defaults to `md`.

## Choosing a Format

| Format           | `--format` | Description                       | Best For                              |
| ---------------- | ---------- | --------------------------------- | ------------------------------------- |
| Text             | `txt`      | Plain-text tree                   | Quick reference, text-only contexts   |
| JSON             | `json`     | Structured data                   | Programmatic processing, integrations |
| HTML             | `html`     | Self-contained styled web page    | Sharing, web documentation            |
| Markdown         | `md`       | GitHub-compatible nested list     | READMEs, project documentation        |
| SVG              | `svg`      | Vector image of the terminal tree | Embedding visuals in docs and READMEs |
| reStructuredText | `rst`      | Sphinx-compatible nested list     | Sphinx/docutils documentation         |

[Export Formats](../reference/export-formats.md) shows exactly what each format produces.

## Multiple Formats at Once

```bash
recursivist export --format "txt json html md"     # space-separated
recursivist export --format txt --format json      # repeated flags
```

## Output Location and Filename

Exports are written to the current directory by default, using the prefix `structure`. Change either:

```bash
recursivist export --format md --output-dir ./exports   # ./exports/structure.md
recursivist export --format json --prefix my-project     # my-project.json
```

The output directory is created automatically if it doesn't exist.

## Controlling What Is Exported

`export` takes the same options as `visualize`, and they work the same way:

```bash
recursivist export \
  --format md \
  --exclude node_modules --exclude .git \
  --exclude-ext .pyc \
  --exclude-pattern "*.test.js" \
  --depth 3 \
  --sort-by-loc --size \
  --git-status
```

- **Filtering**: see [Pattern Filtering](pattern-filtering.md).
- **Depth and full paths**: see [Visualization](visualization.md#directory-depth-control).
- **Lines of code, sizes, modification times, and Git status**: see [Sorting and Statistics](sorting-and-statistics.md).
- **A GitHub repository instead of a local directory**: see [GitHub Repositories](github-repositories.md).

## Icon Style

Exports use the `emoji` icon style by default, independent of your saved and project [configuration](configuration.md). This enables files to render consistently anywhere. Switch to Nerd Font glyphs with:

```bash
recursivist export --format md --icon-style nerd
```

## Date Format

Exports write modification times (`--mtime`, `--sort-by-mtime`) as ISO 8601 in UTC, such as `2026-10-07T12:30:41Z`, independent of your saved and project [configuration](configuration.md). Unlike the relative form shown in the terminal (`Today 14:30`), it stays accurate however long the file is kept. Switch to the relative form with:

```bash
recursivist export --format md --mtime --date-format relative
```

See [Date Format](sorting-and-statistics.md#date-format) for both formats.

## Examples

```bash
# Markdown overview for a README, two levels deep
recursivist export --format md --depth 2 --exclude node_modules --exclude .git --prefix project-overview

# Detailed JSON of the source tree with full paths and metrics
recursivist export src --format json --full-path --sort-by-loc --size --prefix source-structure

# A filtered SVG focused on source files
recursivist export \
  --format svg \
  --include-pattern "*.py" --include-pattern "*.md" \
  --output-dir ./assets \
  --prefix directory-structure \
  --sort-by-loc
```

For longer workflows, see the recipes on [keeping structure docs up to date](../recipes/documentation.md) and [analyzing a JSON export](../recipes/json.md).
