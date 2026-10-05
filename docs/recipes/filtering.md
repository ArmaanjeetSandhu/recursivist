# Filtering by Project Type

Ready-made filter sets for common kinds of project. [Pattern Filtering](../user-guide/pattern-filtering.md) explains the rules behind them.

!!! note

    `--exclude-pattern` and `--include-pattern` match a file's **name**, not its path. To filter by location, use `--exclude` (directory names) or `--ignore-file` (gitignore-style, path-aware).

## Python

```bash
recursivist visualize \
  --exclude __pycache__ --exclude .pytest_cache --exclude .venv --exclude venv \
  --exclude-ext .pyc --exclude-ext .pyo \
  --exclude-pattern "test_*.py" \
  --ignore-file .gitignore
```

To show backend source without its tests using regular expressions instead:

```bash
recursivist visualize --include-pattern ".*\.py$" --exclude-pattern "test_.*\.py$" --regex
```

## JavaScript / TypeScript

```bash
recursivist visualize \
  --exclude node_modules --exclude dist --exclude build --exclude coverage \
  --exclude-ext .map --exclude-ext .log \
  --exclude-pattern "*.test.js" --exclude-pattern "*.spec.ts" --exclude-pattern "*.min.js" \
  --ignore-file .gitignore
```

One regular expression covers the JavaScript and TypeScript test files, including `.jsx` and `.tsx`:

```bash
recursivist visualize --exclude-pattern ".*\.(spec|test)\.(js|ts)x?$" --regex
```

## Java / Maven

```bash
recursivist visualize \
  --exclude target --exclude .idea \
  --exclude-ext .class --exclude-ext .jar \
  --exclude-pattern "*Test.java" \
  --ignore-file .gitignore
```

## Documentation Only

```bash
recursivist visualize --include-pattern "*.md" --include-pattern "*.rst" --include-pattern "*.txt"
```

## Without Generated and Minified Assets

```bash
recursivist visualize \
  --exclude dist --exclude build \
  --exclude-ext .map \
  --exclude-pattern "*.min.js" --exclude-pattern "*.bundle.js"
```

## What Matters Most

Pair filters with a metric sort to surface the files worth looking at:

```bash
# Largest source files
recursivist visualize --exclude node_modules --exclude .git --sort-by-size

# Most recently changed files
recursivist visualize --exclude node_modules --exclude .git --exclude dist --sort-by-mtime
```

## A Reusable Ignore File

When the same exclusions apply on every run, keep them in a gitignore-style file of their own instead of on the command line:

```
# .recursivist-ignore

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

```bash
recursivist visualize --ignore-file .recursivist-ignore
```

## Sharing Filters with Your Team

Commit a `.recursivist.toml` to the repository (or add a `[tool.recursivist]` table to `pyproject.toml`) so that everyone gets the same view without passing any options:

```toml
# .recursivist.toml
ignore-file = ".gitignore"
exclude = ["node_modules", ".git", "venv"]
```

See [Configuration](../user-guide/configuration.md#project-configuration).
