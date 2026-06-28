# Pattern Filtering

Recursivist offers several complementary ways to control which files and directories appear. This guide explains each one and, importantly, how they interact.

## The Four Filtering Mechanisms

| Mechanism                | Option                                    | Matches against                |
| ------------------------ | ----------------------------------------- | ------------------------------ |
| Directory exclusion      | `--exclude`                               | Directory **name**             |
| Extension exclusion      | `--exclude-ext`                           | File **extension**             |
| Include/exclude patterns | `--include-pattern` / `--exclude-pattern` | File **name** (glob or regex)  |
| Ignore file              | `--ignore-file`                           | File **path**, gitignore-style |

The distinction in the last column matters: **include and exclude patterns test a file's name, not its path**, whereas an ignore file matches paths. This determines which tool to reach for, as explained below.

## Directory Exclusion

Exclude directories by name. Matching directories are pruned entirely and never descended into:

```bash
recursivist visualize --exclude "node_modules .git venv"
# or with repeated flags:
recursivist visualize --exclude node_modules --exclude .git
```

## Extension Exclusion

Exclude files by extension. The leading dot is optional:

```bash
recursivist visualize --exclude-ext ".pyc .log .cache"
```

## Include and Exclude Patterns

These options accept either glob patterns (the default) or regular expressions (with `--regex`), and **match against each file's name** — the basename, evaluated at every level of the tree.

```bash
# Exclude every JavaScript test file, anywhere in the tree
recursivist visualize --exclude-pattern "*.test.js" "*.spec.js"

# Exclude Python cache files
recursivist visualize --exclude-pattern "*.pyc"

# Keep only Markdown and Python files
recursivist visualize --include-pattern "*.md" "*.py"
```

!!! warning "Patterns match file names, not paths"
Because patterns are tested against the file name only, a path-style pattern such as `src/*` or `src/**/*.js` will not match anything — file names never contain a `/`. A pattern like `*.js`, by contrast, matches `.js` files at **any** depth. To filter by location rather than by name, use a directory exclusion (`--exclude src`) or an ignore file (see below).

Glob syntax: `*` matches any run of characters, `?` matches a single character, `[abc]` matches one listed character, and `[!abc]` matches one character not listed. With `--regex`, patterns follow Python's regular-expression syntax and are searched within the file name (anchor with `^` and `$` for a full-name match):

```bash
recursivist visualize --exclude-pattern "^test_.*\.py$" --regex
recursivist visualize --exclude-pattern ".*\.(spec|test)\.(js|ts)$" --regex
```

## Ignore Files

The `--ignore-file` option reads a gitignore-style file and applies its patterns to each file's **path relative to the scan root**. This is the path-aware mechanism, supporting anchoring, the `**` wildcard, directory-only patterns (a trailing `/`), and negation (a leading `!`):

```bash
recursivist visualize --ignore-file .gitignore
recursivist visualize --ignore-file .recursivist-ignore
```

An example `.recursivist-ignore`:

```
# Dependencies and build output
node_modules/
dist/
build/

# Logs and caches
*.log
.cache/

# But keep an important generated file
!build/manifest.json
```

## Order of Precedence

When several mechanisms are combined, Recursivist resolves them per file as follows:

1. **Directory exclusions** (`--exclude`) prune matching directories before anything else.
2. **Include patterns** (`--include-pattern`): if any are set, a file must match at least one, or it is dropped.
3. **Exclude patterns** (`--exclude-pattern`): a matching file is removed — **this overrides include patterns**.
4. **Excluded extensions** (`--exclude-ext`): a matching file is removed — **this also overrides include patterns**.
5. **Include match wins over ignore files**: a file that matched an include pattern is kept even if an ignore-file pattern would exclude it.
6. **Ignore-file patterns** (`--ignore-file`) are applied last to anything still undecided.

!!! note
This means include patterns do **not** override everything. Explicit exclude patterns and excluded extensions take priority over includes; include patterns only take priority over ignore-file patterns.

## Combining Filters

The mechanisms compose cleanly:

```bash
recursivist visualize \
  --exclude "node_modules .git build" \
  --exclude-ext ".pyc .log" \
  --exclude-pattern "*.test.js" \
  --include-pattern "*.js" "*.md" \
  --ignore-file .gitignore
```

## Same Behavior Across Commands

Every filtering option works identically with `visualize`, `export`, and `compare`:

```bash
recursivist export --format md --include-pattern "*.py" --exclude-pattern "test_*.py"
recursivist compare dir1 dir2 --exclude "node_modules .git" --exclude-ext ".log"
```

## Examples

```bash
# Documentation files only
recursivist visualize --include-pattern "*.md" "*.rst" "*.txt"

# Exclude generated and minified assets
recursivist visualize --exclude "dist build" --exclude-ext ".min.js .map"

# Backend source, excluding tests (regex)
recursivist visualize --include-pattern ".*\.py$" --exclude-pattern "test_.*\.py$" --regex
```

For a focused reference on glob and regex syntax, see [Pattern Matching](../reference/pattern-matching.md).
