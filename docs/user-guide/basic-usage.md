# Basic Usage

Recursivist is designed to be intuitive and easy to use. This guide covers the basic concepts and usage patterns.

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
recursivist visualize \
--exclude "node_modules .git"
```

### Excluding File Extensions

To exclude files with specific extensions:

```bash
recursivist visualize \
--exclude-ext ".pyc .log"
```

### Limiting Depth

To limit how deep the directory tree goes:

```bash
recursivist visualize \
--depth 3
```

### Showing Full Paths

To show full file paths instead of just names:

```bash
recursivist visualize \
--full-path
```

### Using Verbose Mode

For more detailed output and logging:

```bash
recursivist visualize \
--verbose
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
