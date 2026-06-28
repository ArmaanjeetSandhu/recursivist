# Filtering Examples

Practical recipes for narrowing what Recursivist shows. For the rules behind these, see [Pattern Filtering](../user-guide/pattern-filtering.md).

!!! note
`--exclude-pattern` and `--include-pattern` match a file's **name**, not its path. To filter by location, use `--exclude` (directory names) or `--ignore-file` (gitignore-style, path-aware).

## Excluding Directories and Extensions

```bash
# Directories
recursivist visualize --exclude "node_modules .git venv"

# Extensions (leading dot optional)
recursivist visualize --exclude-ext ".pyc .log .cache"
```

## Glob Patterns

```bash
# Exclude test files anywhere in the tree
recursivist visualize --exclude-pattern "*.test.js" "*.spec.js"

# Exclude Python bytecode
recursivist visualize --exclude-pattern "*.pyc"

# Exclude minified and bundled assets
recursivist visualize --exclude-pattern "*.min.js" "*.bundle.js"
```

## Regular Expressions

```bash
# Files named test_*.py
recursivist visualize --exclude-pattern "^test_.*\.py$" --regex

# JavaScript and TypeScript test files
recursivist visualize --exclude-pattern ".*\.(spec|test)\.(js|ts)x?$" --regex
```

## Include Patterns

Include patterns restrict the view to files whose names match. A file must match at least one include pattern to appear (unless removed by an exclude pattern or excluded extension, which take priority):

```bash
# Source and docs by extension
recursivist visualize --include-pattern "*.js" "*.ts" "*.md"

# Only Python files (regex)
recursivist visualize --include-pattern ".*\.py$" --regex
```

## Ignore Files

For path-aware, gitignore-style filtering, use an ignore file:

```bash
recursivist visualize --ignore-file .gitignore
recursivist visualize --ignore-file .recursivist-ignore
```

Example `.recursivist-ignore`:

```
# Dependencies and build output
node_modules/
venv/
dist/
build/

# Logs and caches
*.log
.cache/

# Editor files
.vscode/
.idea/
*.swp
```

## Combining Filters

```bash
recursivist visualize \
  --exclude "node_modules .git build" \
  --exclude-ext ".pyc .log" \
  --exclude-pattern "*.test.js" \
  --include-pattern "*.js" "*.md" \
  --ignore-file .gitignore
```

This keeps `.js` and `.md` files, drops `.test.js` files and excluded extensions, prunes the listed directories, and also applies the ignore file.

## Language-Specific Recipes

### Python

```bash
recursivist visualize \
  --exclude "__pycache__ .pytest_cache .venv venv" \
  --exclude-ext ".pyc .pyo" \
  --exclude-pattern "test_*.py" \
  --ignore-file .gitignore
```

### JavaScript / TypeScript

```bash
recursivist visualize \
  --exclude "node_modules dist build coverage" \
  --exclude-ext ".map .log" \
  --exclude-pattern "*.test.js" "*.spec.ts" "*.min.js" \
  --ignore-file .gitignore
```

### Java / Maven

```bash
recursivist visualize \
  --exclude "target .idea" \
  --exclude-ext ".class .jar" \
  --exclude-pattern "*Test.java" \
  --ignore-file .gitignore
```

## Filtering with Statistics

Pair filters with a metric sort to surface what matters:

```bash
# Largest source files
recursivist visualize --exclude "node_modules .git" --sort-by-size

# Most recently changed files
recursivist visualize --exclude "node_modules .git" --sort-by-mtime
```

## Filtering in Export and Compare

Every filtering option works the same way with `export` and `compare`:

```bash
recursivist export --format md \
  --exclude "node_modules .git" \
  --exclude-ext ".log" \
  --include-pattern "*.py" "*.md"

recursivist compare dir1 dir2 \
  --exclude "node_modules .git" \
  --exclude-pattern "*.min.js" \
  --save
```
