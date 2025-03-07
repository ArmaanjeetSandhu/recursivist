# Filtering Examples

This page provides practical examples of how to use Recursivist's powerful filtering capabilities to focus on exactly the files and directories you care about.

## Basic Filtering

### Excluding Common Development Directories

Exclude directories typically not needed in visualization:

```bash
recursivist visualize \
--exclude "node_modules .git .venv __pycache__ build dist"
```

### Excluding Temporary and Generated Files

Exclude common temporary and generated file extensions:

```bash
recursivist visualize \
--exclude-ext ".pyc .pyo .class .o .obj .log .tmp .cache"
```

### Combining Directory and Extension Exclusions

Exclude both directories and file extensions:

```bash
recursivist visualize \
--exclude "node_modules .git build" \
--exclude-ext ".pyc .log .map"
```

## Glob Pattern Examples

### Excluding Test Files

Exclude test files using glob patterns:

```bash
recursivist visualize \
--exclude-pattern "*.test.js" "*.spec.js" "*_test.py" "test_*.py"
```

### Focusing on Source Code

Include only source code files:

```bash
recursivist visualize \
--include-pattern "src/**/*.js" "src/**/*.ts" "src/**/*.jsx" "src/**/*.tsx"
```

### Excluding Generated Code

Exclude generated or minified code:

```bash
recursivist visualize \
--exclude-pattern "*.min.js" "*.bundle.js" "*.generated.*"
```

### Including Only Documentation

Show only documentation files:

```bash
recursivist visualize \
--include-pattern "**/*.md" "**/*.rst" "docs/**/*"
```

### Excluding Hidden Files and Directories

Exclude hidden files and directories:

```bash
recursivist visualize \
--exclude-pattern ".*" ".*/.*"
```

## Regex Pattern Examples

### Excluding Test Files with Regex

Exclude test files using regex patterns:

```bash
recursivist visualize \
--exclude-pattern "^test_.*\.py$" ".*_test\.py$" ".*\.(test|spec)\.(js|ts)x?$" \
--regex
```

### Including Only Specific File Types

Include only specific file types using regex:

```bash
recursivist visualize \
--include-pattern ".*\.(jsx?|tsx?|css|scss|html)$" \
--regex
```

### Complex File Selection

Include source files but exclude test files:

```bash
recursivist visualize \
--include-pattern "^src/.*\.(jsx?|tsx?)$" \
--exclude-pattern ".*\.(test|spec)\.(jsx?|tsx?)$" \
--regex
```

### Excluding Based on File Location

Exclude files based on their location:

```bash
recursivist visualize \
--exclude-pattern "^(vendor|third_party)/.*$" "^dist/.*$" \
--regex
```

### Including Files by Naming Pattern

Include files that follow a specific naming convention:

```bash
recursivist visualize \
--include-pattern "^[A-Z][a-zA-Z]+\.(jsx?|tsx?)$" \
--regex
```

This includes files that start with an uppercase letter followed by letters (like React components).

## Using Gitignore Files

### Using an Existing Gitignore

Use patterns from an existing `.gitignore` file:

```bash
recursivist visualize \
--ignore-file .gitignore
```

### Using a Custom Ignore File

Create a custom ignore file (`.recursivist-ignore`):

```
# Example .recursivist-ignore file
*.log
node_modules/
build/
*.min.js
```

Then use it:

```bash
recursivist visualize \
--ignore-file .recursivist-ignore
```

## Combining Different Filtering Methods

### Comprehensive Web Project Filtering

A comprehensive example for a web project:

```bash
recursivist visualize \
--exclude "node_modules .git dist coverage" \
--exclude-ext ".map .log .tmp" \
--exclude-pattern "*.min.js" "*.bundle.js" \
--ignore-file .gitignore
```

### Full-Stack Project Filtering

For a full-stack project with different file types:

```bash
recursivist visualize \
--exclude "node_modules .git __pycache__ venv .pytest_cache" \
--exclude-ext ".pyc .pyo .log .coverage" \
--exclude-pattern "*.test.js" "*_test.py" "*.min.js" \
--ignore-file .gitignore
```

### Documentation-Only View

Show only documentation files across different formats:

```bash
recursivist visualize \
--include-pattern "**/*.md" "**/*.rst" "**/*.txt" "**/*.pdf" "docs/**/*"
```

## Project-Specific Examples

### Python Project

Typical filtering for a Python project:

```bash
recursivist visualize \
--exclude "__pycache__ .pytest_cache .venv venv" \
--exclude-ext ".pyc .pyo .coverage" \
--exclude-pattern "test_*.py" \
--ignore-file .gitignore
```

### JavaScript/TypeScript Project

Typical filtering for a JS/TS project:

```bash
recursivist visualize \
--exclude "node_modules .git dist build coverage" \
--exclude-ext ".map .log" \
--exclude-pattern "*.test.js" "*.spec.ts" "*.min.js" \
--ignore-file .gitignore
```

### Java/Maven Project

Typical filtering for a Java project:

```bash
recursivist visualize \
--exclude "target .git .idea" \
--exclude-ext ".class .jar" \
--exclude-pattern "*Test.java" \
--ignore-file .gitignore
```

### Ruby on Rails Project

Typical filtering for a Rails project:

```bash
recursivist visualize \
--exclude ".git vendor tmp log coverage" \
--exclude-ext .log \
--exclude-pattern "*_spec.rb" "*_test.rb" \
--ignore-file .gitignore
```

## Using Filters with Exports and Comparisons

### Filtered Export

Export with filtering:

```bash
recursivist export \
--format md \
--exclude "node_modules .git" \
--exclude-ext .log \
--include-pattern "src/**/*" "docs/**/*"
```

### Filtered Comparison

Compare with filtering:

```bash
recursivist compare dir1 dir2 \
--exclude "node_modules .git" \
--exclude-ext ".log .tmp" \
--exclude-pattern "*.min.js"
```

## Advanced Pattern Combinations

### Complex Include/Exclude Logic

Include certain files but exclude specific subsets:

```bash
recursivist visualize \
--include-pattern "src/**/*.js" "src/**/*.ts" \
--exclude-pattern "src/**/*.test.js" "src/**/*.spec.ts"
```

### Filtering with Depth Control

Combine filtering with depth control:

```bash
recursivist visualize \
--include-pattern "src/**/*" \
--exclude-pattern "src/test/**/*" \
--depth 3
```

This focuses on the `src` directory but excludes test files, and limits the depth to 3 levels.
