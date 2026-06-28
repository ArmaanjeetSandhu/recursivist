# CLI Reference

A complete reference for every Recursivist command and option.

## Commands

| Command      | Description                                   |
| ------------ | --------------------------------------------- |
| `visualize`  | Display a directory structure in the terminal |
| `export`     | Export a directory structure to files         |
| `compare`    | Compare two directory structures side by side |
| `config`     | Manage persistent user preferences            |
| `completion` | Generate a shell completion snippet           |
| `version`    | Show the installed version                    |

## Shared Options

The following options are common to `visualize`, `export`, and `compare`. Repeatable options accept either space-separated values in one flag or several flags.

| Option                 | Short | Description                                                      |
| ---------------------- | ----- | ---------------------------------------------------------------- |
| `--exclude`            | `-e`  | Directory names to exclude                                       |
| `--exclude-ext`        | `-x`  | File extensions to exclude (leading dot optional)                |
| `--exclude-pattern`    | `-p`  | File-name patterns to exclude (glob by default, regex with `-r`) |
| `--include-pattern`    | `-i`  | File-name patterns to include                                    |
| `--regex`              | `-r`  | Treat patterns as regular expressions instead of globs           |
| `--ignore-file`        | `-g`  | Gitignore-style ignore file to honor (e.g. `.gitignore`)         |
| `--depth`              | `-d`  | Maximum depth to traverse (`0` for unlimited)                    |
| `--full-path`          | `-l`  | Show full paths instead of bare filenames                        |
| `--sort-by-loc`        | `-s`  | Sort by and display lines of code                                |
| `--sort-by-size`       | `-z`  | Sort by and display file sizes                                   |
| `--sort-by-mtime`      | `-m`  | Sort by and display modification times                           |
| `--sort-by-similarity` | `-S`  | Group files by name similarity (overridden by a metric sort)     |
| `--icon-style`         |       | Icon style: `emoji` or `nerd`                                    |
| `--verbose`            | `-v`  | Enable verbose (DEBUG) logging                                   |

!!! note "Pattern scope"
`--exclude-pattern` and `--include-pattern` match against each file's **name**, not its path. For path-based filtering, use `--exclude` (directory names) or `--ignore-file` (gitignore-style). See [Pattern Matching](pattern-matching.md).

## `visualize`

Display a directory structure as a tree in the terminal.

```bash
recursivist visualize [OPTIONS] [DIRECTORY]
```

| Argument    | Description                                                |
| ----------- | ---------------------------------------------------------- |
| `DIRECTORY` | Directory to visualize (defaults to the current directory) |

In addition to the [shared options](#shared-options), `visualize` supports:

| Option         | Short | Description                                                                                 |
| -------------- | ----- | ------------------------------------------------------------------------------------------- |
| `--git-status` | `-G`  | Annotate files with Git status: `[U]` untracked, `[M]` modified, `[A]` added, `[D]` deleted |

### Examples

```bash
recursivist visualize
recursivist visualize /path/to/project
recursivist visualize --exclude "node_modules .git"
recursivist visualize --exclude-ext ".pyc .log"
recursivist visualize --exclude-pattern "*.test.js" "*.spec.js"
recursivist visualize --exclude-pattern "^test_.*\.py$" --regex
recursivist visualize --include-pattern "*.md" "*.py"
recursivist visualize --ignore-file .gitignore
recursivist visualize --depth 3
recursivist visualize --full-path
recursivist visualize --sort-by-loc
recursivist visualize --git-status
recursivist visualize --icon-style nerd
```

## `export`

Export a directory structure to one or more files.

```bash
recursivist export [OPTIONS] [DIRECTORY]
```

| Argument    | Description                                             |
| ----------- | ------------------------------------------------------- |
| `DIRECTORY` | Directory to export (defaults to the current directory) |

In addition to the [shared options](#shared-options), `export` supports:

| Option         | Short | Description                                                              |
| -------------- | ----- | ------------------------------------------------------------------------ |
| `--format`     | `-f`  | Export formats: `txt`, `json`, `html`, `md`, `jsx`, `svg` (default `md`) |
| `--output-dir` | `-o`  | Output directory (created if missing; defaults to current directory)     |
| `--prefix`     | `-n`  | Filename prefix for exports (default `structure`)                        |
| `--git-status` | `-G`  | Annotate exported files with Git status markers                          |

Exports default to the `emoji` icon style for cross-platform consistency, regardless of saved configuration.

### Examples

```bash
recursivist export
recursivist export --format html
recursivist export --format "json html md"
recursivist export --format txt --output-dir ./exports
recursivist export --format json --prefix my-project
recursivist export --exclude node_modules --exclude-ext .pyc
recursivist export --format html --sort-by-loc --sort-by-size
recursivist export --format md --icon-style nerd
```

## `compare`

Compare two directory structures side by side.

```bash
recursivist compare [OPTIONS] DIR1 DIR2
```

| Argument | Description                 |
| -------- | --------------------------- |
| `DIR1`   | First directory to compare  |
| `DIR2`   | Second directory to compare |

In addition to the [shared options](#shared-options), `compare` supports:

| Option         | Short | Description                                                        |
| -------------- | ----- | ------------------------------------------------------------------ |
| `--save`       | `-f`  | Save the comparison as an HTML file instead of printing it         |
| `--output-dir` | `-o`  | Output directory for the HTML file (defaults to current directory) |
| `--prefix`     | `-n`  | Filename prefix for the HTML file (default `comparison`)           |

!!! note
`compare` does not support `--git-status`. Its `-f` is shorthand for `--save`, not `--format`. Items unique to `DIR1` are highlighted in green, items unique to `DIR2` in red.

### Examples

```bash
recursivist compare dir1 dir2
recursivist compare dir1 dir2 --exclude "node_modules .git"
recursivist compare dir1 dir2 --depth 2
recursivist compare dir1 dir2 --save --output-dir ./reports
recursivist compare dir1 dir2 --sort-by-loc --sort-by-size
```

## `config`

Manage persistent user preferences, stored as JSON in your platform's application-data directory (for example, `~/.config/recursivist/config.json` on Linux).

```bash
recursivist config set KEY VALUE
```

| Argument | Description                                       |
| -------- | ------------------------------------------------- |
| `KEY`    | Configuration key (currently `icon-style`)        |
| `VALUE`  | Value to set (`emoji` or `nerd` for `icon-style`) |

### Examples

```bash
recursivist config set icon-style nerd
recursivist config set icon-style emoji
```

## `completion`

Print a shell completion activation snippet to add to your shell's startup file.

```bash
recursivist completion SHELL
```

| Argument | Description                                       |
| -------- | ------------------------------------------------- |
| `SHELL`  | Target shell: `bash`, `zsh`, `fish`, `powershell` |

For most users, the built-in `recursivist --install-completion` is the simplest way to enable completion. See [Shell Completion](../user-guide/shell-completion.md).

## `version`

Print the installed version.

```bash
recursivist version
```
