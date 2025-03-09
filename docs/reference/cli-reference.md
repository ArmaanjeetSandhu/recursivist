# CLI Reference

This page provides a complete reference for all Recursivist commands and options.

## Command Overview

Recursivist provides several commands for visualizing and exporting directory structures:

| Command      | Description                                    |
| ------------ | ---------------------------------------------- |
| `visualize`  | Display directory structures in the terminal   |
| `export`     | Export directory structures to various formats |
| `compare`    | Compare two directory structures side by side  |
| `completion` | Generate shell completion scripts              |
| `version`    | Show the current version                       |

## Global Options

The following options apply to most Recursivist commands:

| Option              | Short | Description                                                    |
| ------------------- | ----- | -------------------------------------------------------------- |
| `--exclude`         | `-e`  | Directories to exclude (space-separated or multiple flags)     |
| `--exclude-ext`     | `-x`  | File extensions to exclude (space-separated or multiple flags) |
| `--exclude-pattern` | `-p`  | Patterns to exclude (glob by default, regex with --regex flag) |
| `--include-pattern` | `-i`  | Patterns to include (overrides exclusions)                     |
| `--regex`           | `-r`  | Treat patterns as regex instead of glob patterns               |
| `--ignore-file`     | `-g`  | Ignore file to use (e.g., .gitignore)                          |
| `--depth`           | `-d`  | Maximum depth to display (0 for unlimited)                     |
| `--full-path`       | `-l`  | Show full paths instead of just filenames                      |
| `--sort-by-loc`     | `-s`  | Sort files by lines of code and display LOC counts             |
| `--sort-by-size`    | `-z`  | Sort files by size and display file sizes                      |
| `--sort-by-mtime`   | `-m`  | Sort files by modification time and display timestamps         |
| `--verbose`         | `-v`  | Enable verbose output                                          |

## `visualize` Command

The `visualize` command displays a directory structure in the terminal.

### Usage

```bash
recursivist visualize [OPTIONS] [DIRECTORY]
```

### Arguments

| Argument    | Description                                                 |
| ----------- | ----------------------------------------------------------- |
| `DIRECTORY` | Directory path to visualize (defaults to current directory) |

### Options

| Option              | Short | Description                                                    |
| ------------------- | ----- | -------------------------------------------------------------- |
| `--exclude`         | `-e`  | Directories to exclude (space-separated or multiple flags)     |
| `--exclude-ext`     | `-x`  | File extensions to exclude (space-separated or multiple flags) |
| `--exclude-pattern` | `-p`  | Patterns to exclude (glob by default, regex with --regex flag) |
| `--include-pattern` | `-i`  | Patterns to include (overrides exclusions)                     |
| `--regex`           | `-r`  | Treat patterns as regex instead of glob patterns               |
| `--ignore-file`     | `-g`  | Ignore file to use (e.g., .gitignore)                          |
| `--depth`           | `-d`  | Maximum depth to display (0 for unlimited)                     |
| `--full-path`       | `-l`  | Show full paths instead of just filenames                      |
| `--sort-by-loc`     | `-s`  | Sort files by lines of code and display LOC counts             |
| `--sort-by-size`    | `-z`  | Sort files by size and display file sizes                      |
| `--sort-by-mtime`   | `-m`  | Sort files by modification time and display timestamps         |
| `--verbose`         | `-v`  | Enable verbose output                                          |

### Examples

```bash
# Visualize current directory
recursivist visualize

# Visualize specific directory
recursivist visualize /path/to/directory

# Exclude directories
recursivist visualize --exclude "node_modules .git venv"

# Exclude file extensions
recursivist visualize --exclude-ext ".pyc .log .cache"

# Use a gitignore-style file
recursivist visualize --ignore-file .gitignore

# Use glob patterns
recursivist visualize --exclude-pattern "*.test.js" "*.spec.js"

# Use regex patterns
recursivist visualize --exclude-pattern "^test_.*\.py$" ".*_test\.js$" --regex

# Include only specific patterns
recursivist visualize --include-pattern "src/*" "*.md"

# Limit directory depth
recursivist visualize --depth 3

# Show full file paths
recursivist visualize --full-path

# Show lines of code
recursivist visualize --sort-by-loc

# Show file sizes
recursivist visualize --sort-by-size

# Show modification times
recursivist visualize --sort-by-mtime

# Combine statistics
recursivist visualize --sort-by-loc --sort-by-size
```

## `export` Command

The `export` command exports a directory structure to various formats.

### Usage

```bash
recursivist export [OPTIONS] [DIRECTORY]
```

### Arguments

| Argument    | Description                                              |
| ----------- | -------------------------------------------------------- |
| `DIRECTORY` | Directory path to export (defaults to current directory) |

### Options

| Option              | Short | Description                                                    |
| ------------------- | ----- | -------------------------------------------------------------- |
| `--format`          | `-f`  | Export formats: txt, json, html, md, jsx                       |
| `--output-dir`      | `-o`  | Output directory for exports                                   |
| `--prefix`          | `-n`  | Prefix for exported filenames                                  |
| `--exclude`         | `-e`  | Directories to exclude (space-separated or multiple flags)     |
| `--exclude-ext`     | `-x`  | File extensions to exclude (space-separated or multiple flags) |
| `--exclude-pattern` | `-p`  | Patterns to exclude (glob by default, regex with --regex flag) |
| `--include-pattern` | `-i`  | Patterns to include (overrides exclusions)                     |
| `--regex`           | `-r`  | Treat patterns as regex instead of glob patterns               |
| `--ignore-file`     | `-g`  | Ignore file to use (e.g., .gitignore)                          |
| `--depth`           | `-d`  | Maximum depth to display (0 for unlimited)                     |
| `--full-path`       | `-l`  | Show full paths instead of just filenames                      |
| `--sort-by-loc`     | `-s`  | Sort files by lines of code and display LOC counts             |
| `--sort-by-size`    | `-z`  | Sort files by size and display file sizes                      |
| `--sort-by-mtime`   | `-m`  | Sort files by modification time and display timestamps         |
| `--verbose`         | `-v`  | Enable verbose output                                          |

### Examples

```bash
# Export to Markdown format
recursivist export --format md

# Export to multiple formats
recursivist export --format "json html md"

# Export to a specific directory
recursivist export --format txt --output-dir ./exports

# Custom filename prefix
recursivist export --format json --prefix my-project

# Export with exclusions
recursivist export --exclude node_modules --exclude-ext .pyc

# Export with file statistics
recursivist export --format html --sort-by-loc --sort-by-size
```

## `compare` Command

The `compare` command compares two directory structures side by side.

### Usage

```bash
recursivist compare [OPTIONS] DIR1 DIR2
```

### Arguments

| Argument | Description                      |
| -------- | -------------------------------- |
| `DIR1`   | First directory path to compare  |
| `DIR2`   | Second directory path to compare |

### Options

| Option              | Short | Description                                                    |
| ------------------- | ----- | -------------------------------------------------------------- |
| `--exclude`         | `-e`  | Directories to exclude (space-separated or multiple flags)     |
| `--exclude-ext`     | `-x`  | File extensions to exclude (space-separated or multiple flags) |
| `--exclude-pattern` | `-p`  | Patterns to exclude (glob by default, regex with --regex flag) |
| `--include-pattern` | `-i`  | Patterns to include (overrides exclusions)                     |
| `--regex`           | `-r`  | Treat patterns as regex instead of glob patterns               |
| `--ignore-file`     | `-g`  | Ignore file to use (e.g., .gitignore)                          |
| `--depth`           | `-d`  | Maximum depth to display (0 for unlimited)                     |
| `--full-path`       | `-l`  | Show full paths instead of just filenames                      |
| `--save`            | `-f`  | Save comparison result to HTML file                            |
| `--output-dir`      | `-o`  | Output directory for exports                                   |
| `--prefix`          | `-n`  | Prefix for exported filenames                                  |
| `--sort-by-loc`     | `-s`  | Sort files by lines of code and display LOC counts             |
| `--sort-by-size`    | `-z`  | Sort files by size and display file sizes                      |
| `--sort-by-mtime`   | `-m`  | Sort files by modification time and display timestamps         |
| `--verbose`         | `-v`  | Enable verbose output                                          |

### Examples

```bash
# Compare two directories
recursivist compare dir1 dir2

# Compare with exclusions
recursivist compare dir1 dir2 --exclude "node_modules .git"

# Compare with depth limit
recursivist compare dir1 dir2 --depth 2

# Export comparison to HTML
recursivist compare dir1 dir2 --save --output-dir ./reports

# Compare with file statistics
recursivist compare dir1 dir2 --sort-by-loc --sort-by-size
```

## `completion` Command

The `completion` command generates shell completion scripts for different shells.

### Usage

```bash
recursivist completion [SHELL]
```

### Arguments

| Argument | Description                              |
| -------- | ---------------------------------------- |
| `SHELL`  | Shell type (bash, zsh, fish, powershell) |

### Examples

```bash
# Generate Bash completion
recursivist completion bash > ~/.bash_completion.d/recursivist

# Generate Zsh completion
recursivist completion zsh > ~/.zsh/completion/_recursivist

# Generate Fish completion
recursivist completion fish > ~/.config/fish/completions/recursivist.fish

# Generate PowerShell completion
recursivist completion powershell > recursivist.ps1
```

## `version` Command

The `version` command displays the current version of Recursivist.

### Usage

```bash
recursivist version
```
