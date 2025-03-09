# Basic Usage

Recursivist is designed to be intuitive and easy to use while offering powerful capabilities. This guide covers the basic concepts and usage patterns.

## Command Structure

All Recursivist commands follow a consistent structure:

```bash
recursivist [command] [options] [arguments]
```

Where:

- `command` is one of: `visualize`, `export`, `compare`, `completion`, or `version`
- `options` are optional flags that modify the command's behavior
- `arguments` are typically directory paths or other positional arguments

## Basic Commands

### Checking Version

To check which version of Recursivist you have installed:

```bash
recursivist version
```

### Visualizing the Current Directory

To display a tree representation of the current directory:

```bash
recursivist visualize
```

This will show a colorful tree of all files and directories, with each file type color-coded for easy identification.

### Visualizing a Specific Directory

To visualize a different directory:

```bash
recursivist visualize /path/to/directory
```

### Visualizing with File Statistics

Recursivist can display and sort by various file statistics:

```bash
# Show lines of code
recursivist visualize --sort-by-loc

# Show file sizes
recursivist visualize --sort-by-size

# Show modification times
recursivist visualize --sort-by-mtime

# Combine multiple statistics
recursivist visualize --sort-by-loc --sort-by-size
```

### Getting Help

To see all available commands:

```bash
recursivist --help
```

To get help for a specific command:

```bash
recursivist visualize --help
recursivist export --help
recursivist compare --help
```

## Default Behavior

By default, Recursivist:

- Shows all files and directories in the specified location
- Doesn't limit the depth of the directory tree
- Displays only filenames (not full paths)
- Colors files based on their extensions
- Uses Unicode characters for the tree structure

You can modify this behavior using the various options described in the following sections.

## Common Options

These options work with most Recursivist commands:

### Excluding Directories

To exclude specific directories:

```bash
recursivist visualize --exclude "node_modules .git"
```

### Excluding File Extensions

To exclude files with specific extensions:

```bash
recursivist visualize --exclude-ext ".pyc .log"
```

### Limiting Depth

To limit how deep the directory tree goes:

```bash
recursivist visualize --depth 3
```

### Showing Full Paths

To show full file paths instead of just names:

```bash
recursivist visualize --full-path
```

### Using Verbose Mode

For more detailed output and logging:

```bash
recursivist visualize --verbose
```

## Pattern Filtering

Recursivist offers powerful pattern-based filtering options:

### Glob Patterns (Default)

```bash
# Exclude test files
recursivist visualize --exclude-pattern "*.test.js" "*.spec.js"
```

### Regular Expressions

```bash
# Exclude test files using regex
recursivist visualize --exclude-pattern "^test_.*\.py$" --regex
```

### Include Patterns (Override Exclusions)

```bash
# Only include specific files/directories
recursivist visualize --include-pattern "src/**/*.js" "*.md"
```

### Gitignore Integration

```bash
# Use patterns from a gitignore-style file
recursivist visualize --ignore-file .gitignore
```

## Export Formats

Export directory structures to various formats:

```bash
# Export to Markdown
recursivist export --format md

# Export to JSON
recursivist export --format json

# Export to HTML
recursivist export --format html

# Export to plain text
recursivist export --format txt

# Export to React component
recursivist export --format jsx
```

## Directory Comparison

Compare two directory structures:

```bash
# Basic comparison
recursivist compare dir1 dir2

# Save comparison as HTML
recursivist compare dir1 dir2 --save
```

## Shell Completion

Generate shell completion scripts:

```bash
# For Bash
recursivist completion bash > ~/.bash_completion.d/recursivist

# For Zsh, Fish, or PowerShell
recursivist completion zsh|fish|powershell
```

## Exit Codes

Recursivist uses standard exit codes to indicate success or failure:

- `0`: Success
- `1`: General error (like invalid arguments or directories)
- Other non-zero values: Specific error conditions

These exit codes can be useful when incorporating Recursivist into scripts or automation.

## Next Steps

Now that you're familiar with the basic usage, you can explore:

- [Visualization options](visualization.md) for customizing how directory trees are displayed
- [Export formats](../reference/export-formats.md) for saving directory structures
- [Comparison features](compare.md) for identifying differences between directories
- [Pattern filtering](pattern-filtering.md) for precisely controlling what's included/excluded
