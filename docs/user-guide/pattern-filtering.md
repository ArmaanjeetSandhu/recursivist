# Pattern Filtering

Recursivist provides powerful pattern-based filtering to help you focus on the files and directories that matter most. This guide explains the different filtering methods available.

## Basic Filtering

### Excluding Directories

To exclude specific directories from the visualization or export, you can specify multiple directories either as space-separated values with a single flag or with multiple flags:

```bash
# Space-separated
recursivist visualize --exclude "node_modules .git venv"

# Multiple flags
recursivist visualize --exclude node_modules --exclude .git --exclude venv
```

### Excluding File Extensions

To exclude files with specific extensions:

```bash
recursivist visualize --exclude-ext ".pyc .log .cache"
```

File extensions can be specified with or without the leading dot (`.`), as Recursivist normalizes them internally.

## Advanced Filtering

### Using Gitignore Files

If you have a `.gitignore` file (or similar), you can use it to filter the directory structure:

```bash
recursivist visualize --ignore-file .gitignore
```

You can also specify a different file:

```bash
recursivist visualize --ignore-file .recursivist-ignore
```

### Glob Pattern Filtering

By default, Recursivist supports glob patterns for filtering:

```bash
# Exclude all JavaScript test files
recursivist visualize --exclude-pattern "*.test.js" "*.spec.js"

# Exclude all Python cache files and directories
recursivist visualize --exclude-pattern "__pycache__" "*.pyc"
```

Glob patterns use simple wildcard characters:

- `*`: Matches any number of characters
- `?`: Matches a single character
- `[abc]`: Matches one character in the brackets
- `[!abc]`: Matches one character not in the brackets
- `**`: Matches directories recursively (e.g., `src/**/*.js` matches all JS files in src and subdirectories)

### Regex Pattern Filtering

For more complex patterns, you can use regular expressions by adding the `--regex` flag:

```bash
# Exclude files starting with "test_" and ending with ".py"
recursivist visualize --exclude-pattern "^test_.*\.py$" --regex

# Exclude both JavaScript and TypeScript test files
recursivist visualize --exclude-pattern ".*\.(spec|test)\.(js|ts)$" --regex
```

Regular expressions provide more powerful matching capabilities but can be more complex to write.

## Include Patterns

Sometimes it's easier to specify what you want to include rather than what you want to exclude. For this, use the `--include-pattern` option:

```bash
# Include only source code files and documentation
recursivist visualize --include-pattern "src/**/*.js" "docs/*.md"
```

When you specify include patterns, they take precedence over exclude patterns. Only files that match at least one include pattern will be shown.

With regex:

```bash
# Include only React components and their tests
recursivist visualize --include-pattern "^src/.*\.(jsx|tsx)$" "^src/.*\.test\.(jsx|tsx)$" --regex
```

## Combining Filters

You can combine different filtering methods for precise control:

```bash
recursivist visualize \
--exclude "node_modules .git" \
--exclude-ext ".pyc .log" \
--exclude-pattern "*.test.js" \
--include-pattern "src/*" "*.md" \
--ignore-file .gitignore
```

## Filter Order of Precedence

When multiple filtering methods are used, Recursivist applies them in the following order:

1. Include patterns (if specified, only matching files will be considered)
2. Exclude patterns (matching files are excluded)
3. Excluded extensions (files with matching extensions are excluded)
4. Excluded directories (directories matching these names are excluded)
5. Gitignore patterns (if specified, patterns from the ignore file are applied)

This means that include patterns have the highest precedence and can override all other exclusions.

## Examples

### Focus on Source Code Only

```bash
recursivist visualize --include-pattern "src/*"
```

### Exclude Generated Files

```bash
recursivist visualize --exclude "dist build coverage" --exclude-ext ".min.js .map"
```

### View Only Documentation

```bash
recursivist visualize --include-pattern "*.md" "*.rst" "docs/*"
```

### Complex Filtering with Regex

```bash
recursivist visualize \
--include-pattern "^src/.*\.(jsx?|tsx?)$" \
--exclude-pattern ".*\.(spec|test)\.(jsx?|tsx?)$" \
--regex
```

This includes only JavaScript and TypeScript source files from the `src` directory, but excludes test files.

### Filtering with File Statistics

You can combine filtering with file statistics to focus on specific aspects of your codebase:

```bash
# Show only source files with more than 100 lines
recursivist visualize \
--include-pattern "src/**/*.py" \
--sort-by-loc

# Find largest files in a specific directory
recursivist visualize \
--include-pattern "assets/**/*" \
--sort-by-size

# See recently modified files
recursivist visualize \
--exclude "node_modules .git" \
--sort-by-mtime
```

While Recursivist doesn't directly filter by the statistics themselves (like "show only files larger than X"), sorting by these metrics helps identify key files of interest.

## Filtering in Export and Compare Commands

All the filtering techniques described above work the same way with the `export` and `compare` commands:

```bash
# Export only source files
recursivist export --format md --include-pattern "src/**/*.js"

# Compare only specific directories
recursivist compare dir1 dir2 --include-pattern "src/*" "config/*"
```

This consistency across commands allows you to apply the same filtering logic regardless of the operation you're performing.
