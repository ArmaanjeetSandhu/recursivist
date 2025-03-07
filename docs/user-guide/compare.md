# Compare

The `compare` command allows you to compare two directory structures side by side with highlighted differences. This guide explains how to use it effectively.

## Basic Comparison

To compare two directories:

```bash
recursivist compare dir1 dir2
```

This will display both directory trees side by side in the terminal, with highlighted differences between them.

## Understanding the Output

The comparison output uses color highlighting to show differences:

- Items that exist in both directories are displayed normally
- Items unique to directory 1 are highlighted in green
- Items unique to directory 2 are highlighted in red

A legend explains the color coding at the top of the output.

## Exporting Comparison Results

By default, the comparison is displayed in the terminal. To save it as an HTML file:

```bash
recursivist compare dir1 dir2 \
--save
```

This creates an HTML file named `comparison.html` in the current directory.

To specify a different output directory:

```bash
recursivist compare dir1 dir2 \
--save \
--output-dir ./reports
```

To customize the filename prefix:

```bash
recursivist compare dir1 dir2 \
--save \
--prefix project-diff
```

This creates a file named `project-diff.html`.

## Filtering the Comparison

All of the filtering options available for other Recursivist commands also work with `compare`:

### Excluding Directories

```bash
recursivist compare dir1 dir2 \
--exclude "node_modules .git"
```

### Excluding File Extensions

```bash
recursivist compare dir1 dir2 \
--exclude-ext ".pyc .log"
```

### Pattern-Based Filtering

```bash
# Exclude with glob patterns (default)
recursivist compare dir1 dir2 \
--exclude-pattern "*.test.js"

# Exclude with regex patterns
recursivist compare dir1 dir2 \
--exclude-pattern "^test_.*\.py$" \
--regex

# Include only specific patterns
recursivist compare dir1 dir2 \
--include-pattern "src/*" "*.md"
```

See the [Pattern Filtering](pattern-filtering.md) guide for more details.

### Using Gitignore Files

```bash
recursivist compare dir1 dir2 \
--ignore-file .gitignore
```

## Depth Control

For large directories, limit the comparison depth:

```bash
recursivist compare dir1 dir2 \
--depth 3
```

## Full Path Display

To show full paths instead of just filenames:

```bash
recursivist compare dir1 dir2 \
--full-path
```

## Use Cases

The comparison feature is particularly useful for:

### Project Evolution

Compare different versions of a project:

```bash
recursivist compare project-v1.0 project-v2.0
```

### Code Reviews

Compare branches or pull requests:

```bash
# Clone the branches to compare
git clone -b main repo main-branch
git clone -b feature/new-feature repo feature-branch

# Compare directory structures
recursivist compare main-branch feature-branch
```

### Deployment Verification

Compare local development and production environments:

```bash
recursivist compare local-build production-build
```

### Backup Validation

Compare original files with backups:

```bash
recursivist compare original-files backup-files
```

## Examples

### Basic Comparison

```bash
recursivist compare project-v1 project-v2
```

### Compare with Exclusions

```bash
recursivist compare project-v1 project-v2 \
--exclude "node_modules .git" \
--exclude-ext ".pyc .log"
```

### Compare with Depth Limit and HTML Export

```bash
recursivist compare project-v1 project-v2 \
--depth 3 \
--save \
--output-dir ./reports \
--prefix version-comparison
```

### Compare Source Directories Only

```bash
recursivist compare project-v1/src project-v2/src \
--include-pattern "*.js" "*.css" "*.jsx"
```

## HTML Output Features

When exporting to HTML (`--save` option), the generated file includes:

- Interactive, side-by-side comparison
- Responsive layout that works on different screen sizes
- Proper styling for directories and files
- Highlighted differences with a clear legend
- Metadata about the comparison settings

This is useful for sharing comparison results with team members or keeping records of structural changes.

## Terminal Compatibility

The terminal comparison view works best in terminals with:

- Unicode support for special characters
- ANSI color support
- Sufficient width to display side-by-side content

For narrow terminals, the comparison may not display optimally. In these cases, using the HTML export option (`--save`) is recommended.
