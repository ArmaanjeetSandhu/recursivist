# Visualization

The `visualize` command is the primary way to display directory structures in the terminal with Recursivist. This guide explains how to use it effectively and customize the output.

## Basic Visualization

To visualize the current directory structure:

```bash
recursivist visualize
```

For a specific directory:

```bash
recursivist visualize /path/to/directory
```

## Customizing the Visualization

### Color Coding

By default, Recursivist color-codes files based on their extensions. Each file extension gets a unique color, making it easier to identify different file types at a glance.

The colors are:

- Generated consistently based on file extensions
- Visually distinct for different types of files
- Maintained throughout a single visualization session

### Directory Depth Control

For large projects, it can be helpful to limit the directory depth:

```bash
recursivist visualize \
--depth 2
```

This will display only the top two levels of the directory structure, with indicators showing where the depth limit was reached.

### Full Path Display

By default, Recursivist shows only filenames. For a view with full paths:

```bash
recursivist visualize \
--full-path
```

Example:

```
📂 project
├── 📄 /home/user/project/README.md
├── 📁 src
│   ├── 📄 /home/user/project/src/main.py
│   └── 📄 /home/user/project/src/utils.py
```

## Filtering the Visualization

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

### Pattern-Based Filtering

For more precise control, you can use patterns:

```bash
# Exclude with glob patterns (default)
recursivist visualize \
--exclude-pattern "*.test.js" "*.spec.js"

# Exclude with regex patterns
recursivist visualize \
--exclude-pattern "^test_.*\.py$" \
--regex

# Include only specific patterns (overrides exclusions)
recursivist visualize \
--include-pattern "src/*" "*.md"
```

See the [Pattern Filtering](pattern-filtering.md) guide for more details.

### Using Gitignore Files

If you have a `.gitignore` file, you can use it to filter the directory structure:

```bash
recursivist visualize \
--ignore-file .gitignore
```

You can also specify a different ignore file:

```bash
recursivist visualize \
--ignore-file .recursivist-ignore
```

## Output Example

The visualization output looks like this:

```
📂 my-project
├── 📁 src
│   ├── 📄 main.py
│   ├── 📄 utils.py
│   └── 📁 tests
│       ├── 📄 test_main.py
│       └── 📄 test_utils.py
├── 📄 README.md
├── 📄 requirements.txt
└── 📄 setup.py
```

With depth limits, you might see:

```
📂 my-project
├── 📁 src
│   ├── 📄 main.py
│   ├── 📄 utils.py
│   └── 📁 tests
│       ⋯ (max depth reached)
├── 📄 README.md
├── 📄 requirements.txt
└── 📄 setup.py
```

## Verbose Mode

For detailed information about the visualization process:

```bash
recursivist visualize \
--verbose
```

This is useful for debugging or understanding how patterns are applied.

## Terminal Compatibility

Recursivist works in most modern terminals with:

- Unicode support for special characters (📁, 📄, etc.)
- ANSI color support

If your terminal doesn't support these features, you might see different characters or no colors.

## Performance Tips

For large directories:

1. Use the `--depth` option to limit the directory depth
2. Exclude large directories you don't need with `--exclude`
3. Use pattern matching to focus on specific parts of the directory tree

## Related Commands

- [Export](export.md): Save directory structures to various formats
- [Compare](compare.md): Compare two directory structures side by side

For complete command options, see the [CLI Reference](../reference/cli-reference.md).
