# Basic Usage

Recursivist is built around a small set of commands that share a consistent collection of filtering and display options. This guide covers the fundamentals; later guides go deeper into each command.

## Command Structure

```bash
recursivist [COMMAND] [OPTIONS] [ARGUMENTS]
```

The available commands are:

| Command      | Purpose                                       |
| ------------ | --------------------------------------------- |
| `visualize`  | Display a directory structure in the terminal |
| `export`     | Export a directory structure to files         |
| `compare`    | Compare two directory structures side by side |
| `config`     | Manage persistent user preferences            |
| `completion` | Generate a shell completion script            |
| `version`    | Show the installed version                    |

## Getting Help

Every command has built-in help:

```bash
recursivist --help            # list all commands
recursivist visualize --help  # options for a specific command
```

## Default Behavior

By default, `visualize` and `export`:

- Include every file and directory in the target location.
- Apply no depth limit.
- Show bare filenames rather than full paths.
- Color files by extension (colors are derived deterministically, so a given extension always maps to the same color).
- List files before subdirectories, ordering files by extension and then name.
- Label entries with generic emoji icons (📄 for files, 📁 for directories).

## Icon Styles

Recursivist ships with two icon styles:

- **`emoji`** (default): the generic 📄 and 📁 glyphs, which render in virtually any terminal.
- **`nerd`**: file-type-specific [Nerd Font](https://www.nerdfonts.com/) glyphs (a distinct icon for Python, JavaScript, folders like `.git` or `node_modules`, and so on). This requires a Nerd Font installed and selected in your terminal.

Set the default style persistently with the `config` command:

```bash
recursivist config set icon-style nerd
recursivist config set icon-style emoji
```

The preference is stored in a JSON config file in your platform's application-data directory (for example, `~/.config/recursivist/config.json` on Linux). Override it for a single run with `--icon-style`:

```bash
recursivist visualize --icon-style nerd
```

Exports default to the `emoji` style regardless of your configuration, so exported files render consistently on any machine. Pass `--icon-style nerd` to override this.

## Common Options

The following options are shared by `visualize`, `export`, and `compare`.

### Excluding Directories

```bash
recursivist visualize --exclude "node_modules .git"
```

### Excluding File Extensions

Extensions may be given with or without the leading dot:

```bash
recursivist visualize --exclude-ext ".pyc .log"
```

### Limiting Depth

```bash
recursivist visualize --depth 2
```

Subtrees cut off by the limit are marked `⋯ (max depth reached)`.

### Showing Full Paths

```bash
recursivist visualize --full-path
```

### Verbose Output

```bash
recursivist visualize --verbose
```

Verbose mode lowers the log level to `DEBUG`, printing details about how patterns and filters are applied — useful when a filter isn't behaving as expected.

## File Statistics

All three primary commands can display file metrics, and can sort by them. Sorting and display are separate concerns:

```bash
recursivist visualize --sort-by-loc     # sort by AND show lines of code
recursivist visualize --sort-by-size    # sort by AND show file sizes
recursivist visualize --sort-by-mtime   # sort by AND show modification times

recursivist visualize --loc             # show lines of code, keep default order
recursivist visualize --size            # show file sizes, keep default order
recursivist visualize --mtime           # show modification times, keep default order
```

The `--sort-by-*` forms both sort and annotate; the bare `--loc`/`--size`/`--mtime` forms annotate only. Flags are resolved by their order on the command line: only the first sorting flag takes effect, and annotations appear in the order requested. So to sort by lines of code while also showing size, write `--sort-by-loc --size` — note that a second `--sort-by-*` (as in `--sort-by-loc --sort-by-size`) is ignored. See [Visualization](visualization.md#file-statistics) and the [CLI Reference](../reference/cli-reference.md#sorting-and-display-flags) for details.

## Grouping by Name Similarity

Instead of the default extension-and-name ordering, files can be grouped so that similarly named files sit next to each other:

```bash
recursivist visualize --sort-by-similarity
```

Like the metric sorts, this is a sorting flag, so only the first sorting flag on the command line takes effect: an earlier `--sort-by-*` (metric or Git status) wins and the similarity flag is ignored.

## Pattern Filtering

Glob patterns (default) and regular expressions (`--regex`) give finer control than directory or extension exclusions, and include patterns can override exclusions:

```bash
recursivist visualize --exclude-pattern "*.test.js"
recursivist visualize --exclude-pattern "^test_.*\.py$" --regex
recursivist visualize --include-pattern "*.py" "*.md"
recursivist visualize --ignore-file .gitignore
```

See [Pattern Filtering](pattern-filtering.md) for the full picture, including the order of precedence.

## Exit Codes

Recursivist uses standard exit codes:

- `0`: Success
- `1`: An error occurred (for example, an invalid directory, an unsupported export format, or a failure during scanning or writing)

These make Recursivist easy to use in scripts and automation.

## Next Steps

- [Visualization](visualization.md) — terminal output options in depth
- [Export](export.md) — saving structures to files
- [Compare](compare.md) — diffing two directories
- [Pattern Filtering](pattern-filtering.md) — precise include/exclude control
