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

By default, Recursivist color-codes files based on their extensions. Each file extension gets a unique color, generated deterministically to ensure consistent visualization:

- The same extension always gets the same color in all visualizations
- Colors are generated to be visually distinct between different file types
- The color scheme provides good contrast for readability

### File Statistics

Recursivist can display and sort by various file statistics:

#### Lines of Code

Calculate and display the number of lines in each file and total lines per directory:

```bash
recursivist visualize --sort-by-loc
```

Output:

```
📂 my-project (4328 lines)
├── 📁 src (3851 lines)
│   ├── 📄 main.py (245 lines)
│   ├── 📄 utils.py (157 lines)
...
```

#### File Sizes

Display file sizes with appropriate units (B, KB, MB, GB):

```bash
recursivist visualize --sort-by-size
```

Output:

```
📂 my-project (1.2 MB)
├── 📁 src (850.5 KB)
│   ├── 📄 main.py (12.4 KB)
│   ├── 📄 utils.py (8.2 KB)
...
```

#### Modification Times

Show when files were last modified with smart formatting:

```bash
recursivist visualize --sort-by-mtime
```

Output:

```
📂 my-project (Today 14:30)
├── 📁 src (Today 14:25)
│   ├── 📄 main.py (Today 14:25)
│   ├── 📄 utils.py (Yesterday 18:10)
...
```

#### Combining Statistics

You can combine multiple statistics in a single view:

```bash
recursivist visualize --sort-by-loc --sort-by-size --sort-by-mtime
```

Output:

```
📂 my-project (4328 lines, 1.2 MB, Today 14:30)
├── 📁 src (3851 lines, 850.5 KB, Today 14:25)
│   ├── 📄 main.py (245 lines, 12.4 KB, Today 14:25)
...
```

### Directory Depth Control

For large projects, it can be helpful to limit the directory depth:

```bash
recursivist visualize --depth 2
```

This will display only the top two levels of the directory structure, with indicators showing where the depth limit was reached:

```
📂 my-project
├── 📁 src
│   ├── 📄 main.py
│   ├── 📄 utils.py
│   └── 📁 tests
│       ⋯ (max depth reached)
├── 📄 README.md
...
```

### Full Path Display

By default, Recursivist shows only filenames. For a view with full paths:

```bash
recursivist visualize --full-path
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
recursivist visualize --exclude "node_modules .git"
```

### Excluding File Extensions

To exclude files with specific extensions:

```bash
recursivist visualize --exclude-ext ".pyc .log"
```

### Pattern-Based Filtering

For more precise control, you can use patterns:

```bash
# Exclude with glob patterns (default)
recursivist visualize --exclude-pattern "*.test.js" "*.spec.js"

# Exclude with regex patterns
recursivist visualize --exclude-pattern "^test_.*\.py$" --regex

# Include only specific patterns (overrides exclusions)
recursivist visualize --include-pattern "src/*" "*.md"
```

See the [Pattern Filtering](pattern-filtering.md) guide for more details.

### Using Gitignore Files

If you have a `.gitignore` file, you can use it to filter the directory structure:

```bash
recursivist visualize --ignore-file .gitignore
```

You can also specify a different ignore file:

```bash
recursivist visualize --ignore-file .recursivist-ignore
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

With file statistics enabled:

```
📂 my-project (4328 lines)
├── 📁 src (3851 lines)
│   ├── 📄 main.py (245 lines)
│   ├── 📄 utils.py (157 lines)
│   └── 📁 tests (653 lines)
│       ├── 📄 test_main.py (412 lines)
│       └── 📄 test_utils.py (241 lines)
├── 📄 README.md (124 lines)
├── 📄 requirements.txt (18 lines)
└── 📄 setup.py (65 lines)
```

## Verbose Mode

For detailed information about the visualization process:

```bash
recursivist visualize --verbose
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
4. Avoid using `--sort-by-loc` for very large repositories as line counting can be time-consuming

## Related Commands

- [Export](export.md): Save directory structures to various formats
- [Compare](compare.md): Compare two directory structures side by side

For complete command options, see the [CLI Reference](../reference/cli-reference.md).
