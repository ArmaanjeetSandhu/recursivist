# Filtering Examples

Recursivist provides powerful filtering capabilities to help you focus on exactly the files and directories you need. This guide provides practical examples for common filtering scenarios.

## Basic Exclusion Options

### Excluding Directories

To exclude specific directories from the visualization:

```bash
recursivist visualize --exclude "node_modules .git venv"
```

This excludes `node_modules`, `.git`, and `venv` directories from the output.

You can also provide multiple `--exclude` flags:

```bash
recursivist visualize --exclude node_modules --exclude .git --exclude venv
```

### Excluding File Extensions

To exclude files with specific extensions:

```bash
recursivist visualize --exclude-ext ".pyc .log .cache"
```

This excludes all files with `.pyc`, `.log`, or `.cache` extensions.

Extensions can be specified with or without the leading dot (`.`).

## Pattern-Based Filtering

### Using Glob Patterns (Default)

By default, Recursivist uses glob patterns for filtering:

```bash
# Exclude all JavaScript test files
recursivist visualize --exclude-pattern "*.test.js" "*.spec.js"

# Exclude Python cache files and directories
recursivist visualize --exclude-pattern "__pycache__" "*.pyc"

# Exclude minified and bundled JavaScript
recursivist visualize --exclude-pattern "*.min.js" "*.bundle.js"
```

Glob pattern syntax includes:

- `*`: Matches any number of characters (except `/`)
- `?`: Matches a single character (except `/`)
- `[abc]`: Matches one character in the brackets
- `[!abc]`: Matches one character not in the brackets

### Using Regular Expressions

For more complex patterns, you can use regular expressions with the `--regex` flag:

```bash
# Exclude files starting with "test_" and ending with ".py"
recursivist visualize --exclude-pattern "^test_.*\.py$" --regex

# Exclude both JavaScript and TypeScript test files
recursivist visualize --exclude-pattern ".*\.(spec|test)\.(js|ts)x?$" --regex

# Exclude files in "vendor" or "third_party" directories
recursivist visualize --exclude-pattern "^(vendor|third_party)/.*$" --regex
```

## Include Patterns

Sometimes it's easier to specify what you want to include rather than what to exclude:

```bash
# Show only source code files
recursivist visualize --include-pattern "src/**/*.js" "src/**/*.ts"

# Show only documentation files
recursivist visualize --include-pattern "**/*.md" "docs/**/*"

# Show only Python files in specific directories
recursivist visualize --include-pattern "app/**/*.py" "lib/**/*.py"
```

Include patterns take precedence over exclude patterns, showing only files that match at least one include pattern.

With regex:

```bash
# Show only React components
recursivist visualize --include-pattern "^src/.*\.(jsx|tsx)$" --regex

# Show only Python classes
recursivist visualize --include-pattern "^.*class\s+[A-Z][a-zA-Z0-9]*:" --regex --content-match
```

## Using Gitignore Files

If you have a `.gitignore` file, you can use it to filter the directory structure:

```bash
recursivist visualize --ignore-file .gitignore
```

You can also specify a different ignore file:

```bash
recursivist visualize --ignore-file .recursivist-ignore
```

Example `.recursivist-ignore` file:

```
# Dependencies
node_modules/
venv/
__pycache__/

# Build artifacts
dist/
build/
*.min.js
*.bundle.js

# Logs and caches
*.log
.cache/
.pytest_cache/

# Editor files
.vscode/
.idea/
*.swp
*~
```

## Combining Filtering Methods

You can combine different filtering methods for precise control:

```bash
recursivist visualize \
--exclude "node_modules .git build" \
--exclude-ext ".pyc .log" \
--exclude-pattern "*.test.js" \
--include-pattern "src/*" "*.md" \
--ignore-file .gitignore
```

This powerful combination lets you:

1. Exclude specific directories (`node_modules`, `.git`, `build`)
2. Exclude specific file extensions (`.pyc`, `.log`)
3. Exclude files matching patterns (`*.test.js`)
4. Include only files in `src` and markdown files
5. Also respect patterns from `.gitignore`

## Filter Order of Precedence

When multiple filtering methods are used, Recursivist applies them in this order:

1. Include patterns (if specified, only matching files will be considered)
2. Exclude patterns (matching files are excluded)
3. Excluded extensions (files with matching extensions are excluded)
4. Excluded directories (directories matching these names are excluded)
5. Gitignore patterns (patterns from the ignore file are applied)

This means include patterns have the highest precedence and can override all other exclusions.

## Language-Specific Examples

### Python Project

```bash
recursivist visualize \
--exclude "__pycache__ .pytest_cache .venv venv" \
--exclude-ext ".pyc .pyo .coverage" \
--exclude-pattern "test_*.py" \
--ignore-file .gitignore
```

### JavaScript/TypeScript Project

```bash
recursivist visualize \
--exclude "node_modules .git dist build coverage" \
--exclude-ext ".map .log" \
--exclude-pattern "*.test.js" "*.spec.ts" "*.min.js" \
--ignore-file .gitignore
```

### Java/Maven Project

```bash
recursivist visualize \
--exclude "target .git .idea" \
--exclude-ext ".class .jar" \
--exclude-pattern "*Test.java" \
--ignore-file .gitignore
```

### Ruby on Rails Project

```bash
recursivist visualize \
--exclude ".git vendor tmp log coverage" \
--exclude-ext ".log" \
--exclude-pattern "*_spec.rb" "*_test.rb" \
--ignore-file .gitignore
```

## Task-Specific Filtering

### Code Review Focus

Show only files that changed in a branch:

```bash
# Get changed files
changed_files=$(git diff --name-only main)

# Create include patterns
include_patterns=""
for file in $changed_files; do
    include_patterns+=" \"$file\""
done

# Visualize only changed files
eval "recursivist visualize --include-pattern $include_patterns"
```

### Documentation Overview

Display only documentation files across the project:

```bash
recursivist visualize \
--include-pattern "**/*.md" "**/*.rst" "**/*.txt" "docs/**/*" \
--sort-by-mtime
```

### Security Audit

Focus on configuration and security-related files:

```bash
recursivist visualize \
--include-pattern "**/*.json" "**/*.yml" "**/*.yaml" "**/*.config.*" \
--include-pattern "**/security/**/*" "**/*.env.*" "Dockerfile*" \
--sort-by-mtime
```

### Performance Analysis

Identify large files that might cause performance issues:

```bash
recursivist visualize \
--exclude "node_modules .git dist" \
--sort-by-size
```

## Using Filters with Export

All filtering options work with the `export` command:

```bash
recursivist export \
--format md \
--exclude "node_modules .git" \
--exclude-ext ".log" \
--include-pattern "src/**/*" "docs/**/*" \
--output-dir ./reports \
--prefix filtered-structure
```

## Using Filters with Compare

Filtering also works with the `compare` command:

```bash
recursivist compare dir1 dir2 \
--exclude "node_modules .git" \
--exclude-ext ".log .tmp" \
--exclude-pattern "*.min.js" \
--save \
--output-dir ./reports \
--prefix filtered-comparison
```

## Advanced Pattern Examples

### Frontend Files Only

```bash
recursivist visualize \
--include-pattern "**/*.js" "**/*.ts" "**/*.jsx" "**/*.tsx" "**/*.css" "**/*.scss" "**/*.html"
```

### Backend Files Only

```bash
recursivist visualize \
--include-pattern "**/*.py" "**/*.java" "**/*.go" "**/*.rb" "**/*.php" "**/*.sql"
```

### Configuration Files Only

```bash
recursivist visualize \
--include-pattern "**/*.json" "**/*.yml" "**/*.yaml" "**/*.toml" "**/*.ini" "**/*.xml" "**/*.config.*"
```

### Feature-Specific Files

Focus on files related to a specific feature:

```bash
recursivist visualize \
--include-pattern "**/auth/**/*" "**/login/**/*" "**/security/**/*"
```

### Exclude Generated Code

```bash
recursivist visualize \
--exclude-pattern "**/*.g.dart" "**/*.generated.*" "**/generated/**/*"
```

### Focus on Recently Modified Files

Show only files modified in the last week:

```bash
# Create a temporary file with recently modified paths
find . -type f -mtime -7 | grep -v "node_modules\|.git" > recent_files.txt

# Use these files as include patterns
include_patterns=$(cat recent_files.txt | sed 's/^.//' | xargs -I{} echo -n " \"{}\"")
eval "recursivist visualize --include-pattern $include_patterns --sort-by-mtime"

# Clean up
rm recent_files.txt
```

## Combining with File Statistics

Combining filtering with file statistics provides powerful insights:

```bash
# Find large source files
recursivist visualize \
--include-pattern "src/**/*.js" \
--sort-by-size

# Identify complex modules
recursivist visualize \
--include-pattern "src/**/*.py" \
--exclude-pattern "**/*test*.py" \
--sort-by-loc

# Examine recent changes to specific components
recursivist visualize \
--include-pattern "src/components/**/*.jsx" \
--sort-by-mtime
```

## Shell Script for Filtered Analysis

This script demonstrates how to use filtering for targeted code analysis:

```bash
#!/bin/bash

# Function to analyze specific parts of a codebase
analyze_section() {
    section_name=$1
    include_patterns=$2
    exclude_patterns=$3

    echo "=== Analyzing $section_name ==="
    echo ""

    # Create directory for output
    mkdir -p analysis/$section_name

    # Build the command with appropriate options
    cmd="recursivist export"
    cmd+=" --format json"
    cmd+=" --output-dir ./analysis/$section_name"
    cmd+=" --prefix structure"
    cmd+=" --sort-by-loc --sort-by-size"

    # Add include patterns if provided
    if [ -n "$include_patterns" ]; then
        for pattern in $include_patterns; do
            cmd+=" --include-pattern \"$pattern\""
        done
    fi

    # Add exclude patterns if provided
    if [ -n "$exclude_patterns" ]; then
        for pattern in $exclude_patterns; do
            cmd+=" --exclude-pattern \"$pattern\""
        done
    fi

    # Execute command
    eval $cmd

    echo "Analysis for $section_name complete!"
    echo ""
}

# Create analysis directory
mkdir -p analysis

# Analyze different sections of the codebase
analyze_section "frontend" "src/frontend/**/*" "**/*.test.*"
analyze_section "backend" "src/backend/**/*" "**/*.test.*"
analyze_section "tests" "**/*.test.* **/*_test.* **/test_*.*" ""
analyze_section "documentation" "**/*.md docs/**/*" ""

echo "All analyses complete! Results in ./analysis directory."
```

By mastering Recursivist's filtering capabilities, you can create highly focused views of your project structure, making it easier to understand, document, and analyze specific aspects of your codebase.
