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
| `--sort-by-similarity` | `-S`  | Group files with similar names together                          |
| `--sort-by-loc`        | `-s`  | Sort files by lines of code and display LOC counts               |
| `--sort-by-size`       | `-z`  | Sort files by size and display file sizes                        |
| `--sort-by-mtime`      | `-m`  | Sort files by modification time and display timestamps           |
| `--sort-by-git-status` |       | Sort files by Git status and display status markers              |
| `--loc`                |       | Display lines of code without affecting sort order               |
| `--size`               |       | Display file sizes without affecting sort order                  |
| `--mtime`              |       | Display modification times without affecting sort order          |
| `--git-status`         | `-G`  | Display Git status markers without affecting sort order          |
| `--icon-style`         |       | Icon style: `emoji` or `nerd`                                    |
| `--verbose`            | `-v`  | Enable verbose (DEBUG) logging                                   |

The `--ignore-file` name is matched with or without a leading dot, so `--ignore-file gitignore` and `--ignore-file .gitignore` behave the same when a `.gitignore` is present.

The sorting and annotation flags (`--sort-by-*`, `--loc`, `--size`, `--mtime`, `--git-status`) follow a specific resolution model when several are combined; that model is described in the [Sorting and Display Flags](#sorting-and-display-flags) section below.

!!! note "Pattern scope"
`--exclude-pattern` and `--include-pattern` match against each file's **name**, not its path. For path-based filtering, use `--exclude` (directory names) or `--ignore-file` (gitignore-style). See [Pattern Matching](pattern-matching.md).

## Sorting and Display Flags

Recursivist keeps two concerns separate: **how files are ordered** and **what each file is annotated with**. The flags fall into three families.

| Family           | Flags                                                                                             | Effect                                                          |
| ---------------- | ------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| **Sorting-only** | `--sort-by-similarity` (`-S`)                                                                     | Reorders files; adds no annotation of its own                   |
| **Combined**     | `--sort-by-loc` (`-s`), `--sort-by-size` (`-z`), `--sort-by-mtime` (`-m`), `--sort-by-git-status` | Reorders files by a metric **and** annotates every file with it |
| **Display-only** | `--loc`, `--size`, `--mtime`, `--git-status` (`-G`)                                               | Annotates files with a metric **without** changing the order    |

The combined numeric flags (`--sort-by-loc`, `--sort-by-size`, `--sort-by-mtime`) are shorthand for "sort by this metric and display it too" — equivalent to pairing a sort with the matching display-only flag.

### Resolution by command-line order

When several of these flags are combined, they are resolved strictly by their **left-to-right order on the command line**, not by any fixed precedence:

- **Only the first sorting flag takes effect.** Every later sorting flag — whether sorting-only or combined — is discarded completely, contributing neither ordering nor annotation. So `--sort-by-loc --sort-by-size` sorts by lines of code and shows **only** the LOC annotation; the `--sort-by-size` is dropped.
- **Display-only flags always annotate,** in the exact order they are given.
- **A winning combined numeric metric annotates first,** ahead of any display-only annotations.
- **A Git-status marker always trails last,** after every numeric annotation.

To sort by one metric while displaying others, pair a single sorting flag with display-only flags. For example, `--sort-by-loc --size --mtime` orders files by lines of code and annotates each with its LOC, size, and modification time, in that order.

!!! tip "Migrating from earlier versions"
Earlier releases combined metrics with repeated `--sort-by-*` flags and always displayed them in a fixed LOC → size → mtime order. That no longer works: a second `--sort-by-*` is now ignored. Replace, for example, `--sort-by-loc --sort-by-size` (old: sort by LOC, show both) with `--sort-by-loc --size`.

All three commands (`visualize`, `export`, and `compare`) support every sorting and display flag. In `compare`, Git status is read independently for each directory, so each side is annotated against its own repository.

## `visualize`

Display a directory structure as a tree in the terminal.

```bash
recursivist visualize [OPTIONS] [DIRECTORY]
```

| Argument    | Description                                                |
| ----------- | ---------------------------------------------------------- |
| `DIRECTORY` | Directory to visualize (defaults to the current directory) |

`visualize` supports the [shared options](#shared-options) and the full set of [sorting and display flags](#sorting-and-display-flags).

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
recursivist visualize --sort-by-loc              # sort by and show lines of code
recursivist visualize --sort-by-loc --size       # sort by LOC, show LOC and size
recursivist visualize --mtime --git-status       # annotate only: mtime, then Git status
recursivist visualize --git-status               # Git status markers
recursivist visualize --sort-by-git-status       # sort by and show Git status
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

In addition to the [shared options](#shared-options) and the [sorting and display flags](#sorting-and-display-flags), `export` supports:

| Option         | Short | Description                                                              |
| -------------- | ----- | ------------------------------------------------------------------------ |
| `--format`     | `-f`  | Export formats: `txt`, `json`, `html`, `md`, `svg`, `rst` (default `md`) |
| `--output-dir` | `-o`  | Output directory (created if missing; defaults to current directory)     |
| `--prefix`     | `-n`  | Filename prefix for exports (default `structure`)                        |

Exports default to the `emoji` icon style for cross-platform consistency, regardless of saved configuration.

### Examples

```bash
recursivist export
recursivist export --format html
recursivist export --format "json html md"
recursivist export --format txt --output-dir ./exports
recursivist export --format json --prefix my-project
recursivist export --exclude node_modules --exclude-ext .pyc
recursivist export --format html --sort-by-loc --size   # sort by LOC, show LOC and size
recursivist export --format md --git-status             # Git status markers
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

In addition to the [shared options](#shared-options) and the [sorting and display flags](#sorting-and-display-flags), `compare` supports:

| Option         | Short | Description                                                        |
| -------------- | ----- | ------------------------------------------------------------------ |
| `--save`       | `-f`  | Save the comparison as an HTML file instead of printing it         |
| `--output-dir` | `-o`  | Output directory for the HTML file (defaults to current directory) |
| `--prefix`     | `-n`  | Filename prefix for the HTML file (default `comparison`)           |

!!! note
In `compare`, `-f` is shorthand for `--save`, not `--format`. Items unique to `DIR1` are highlighted in green, items unique to `DIR2` in red. When Git status is enabled, it is read independently for each directory, so each side is annotated against its own repository.

### Examples

```bash
recursivist compare dir1 dir2
recursivist compare dir1 dir2 --exclude "node_modules .git"
recursivist compare dir1 dir2 --depth 2
recursivist compare dir1 dir2 --save --output-dir ./reports
recursivist compare dir1 dir2 --sort-by-loc --size   # sort by LOC, show LOC and size
recursivist compare dir1 dir2 --git-status           # annotate each side with Git status
recursivist compare dir1 dir2 --sort-by-git-status   # sort each side by Git status
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
