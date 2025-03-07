# Compare Examples

This page provides practical examples of how to use Recursivist's directory comparison functionality to identify differences between directory structures.

## Basic Comparison Examples

### Simple Directory Comparison

```bash
recursivist compare dir1 dir2
```

This displays a side-by-side comparison of `dir1` and `dir2` in the terminal, with differences highlighted.

### Saving Comparison as HTML

```bash
recursivist compare dir1 dir2 \
--save
```

This generates an HTML file named `comparison.html` containing the comparison.

### Custom Output Location

```bash
recursivist compare dir1 dir2 \
--save \
--output-dir ./reports
```

This saves the comparison to `./reports/comparison.html`.

### Custom Filename

```bash
recursivist compare dir1 dir2 \
--save \
--prefix dir-diff
```

This saves the comparison to `dir-diff.html`.

## Filtered Comparisons

### Comparing with Directory Exclusions

```bash
recursivist compare dir1 dir2 \
--exclude "node_modules .git"
```

This compares the directories while ignoring `node_modules` and `.git` directories.

### Comparing with File Extension Exclusions

```bash
recursivist compare dir1 dir2 \
--exclude-ext ".pyc .log"
```

This compares the directories while ignoring files with `.pyc` and `.log` extensions.

### Comparing with Pattern Exclusions

```bash
recursivist compare dir1 dir2 \
--exclude-pattern "*.test.js" "*.spec.js"
```

This compares the directories while ignoring JavaScript test files.

### Focusing on Specific Files

```bash
recursivist compare dir1 dir2 \
--include-pattern "src/**/*.js" "*.md"
```

This compares only JavaScript files in the `src` directory and markdown files.

### Comparing with Gitignore Patterns

```bash
recursivist compare dir1 dir2 \
--ignore-file .gitignore
```

This compares the directories while respecting the patterns in `.gitignore`.

## Depth-Limited Comparisons

### Comparing Top-Level Structure

```bash
recursivist compare dir1 dir2 \
--depth 1
```

This compares only the top level of the directory structures.

### Comparing with Limited Depth

```bash
recursivist compare dir1 dir2 \
--depth 3
```

This compares the directories up to 3 levels deep.

## Full Path Comparisons

### Comparing with Full Paths

```bash
recursivist compare dir1 dir2 \
--full-path
```

This displays full file paths in the comparison instead of just filenames.

## Real-World Use Cases

### Project Version Comparison

```bash
recursivist compare project-v1.0 project-v2.0 \
--exclude "node_modules .git" \
--exclude-ext ".log .tmp" \
--save \
--output-dir ./version-reports \
--prefix v1-vs-v2
```

This compares two versions of a project, excluding common directories and file types, and saves the report.

### Branch Comparison

```bash
# Clone branches to compare
git clone -b main repo main-branch
git clone -b feature/new-feature repo feature-branch

# Compare directory structures
recursivist compare main-branch feature-branch \
--exclude "node_modules .git" \
--save \
--prefix branch-comparison
```

This compares the directory structures of two Git branches.

### Source vs. Build Comparison

```bash
recursivist compare src dist \
--include-pattern "**/*.js" \
--save \
--prefix src-vs-dist
```

This compares JavaScript files between source and distribution directories.

### Development vs. Production Comparison

```bash
recursivist compare dev-config prod-config \
--save \
--output-dir ./deployment-validation \
--prefix dev-vs-prod
```

This compares development and production configuration directories.

## Specific Comparison Scenarios

### Code Library Upgrade Analysis

```bash
# Extract old and new versions of a library
mkdir -p old-lib new-lib
tar -xzf library-1.0.tar.gz -C old-lib
tar -xzf library-2.0.tar.gz -C new-lib

# Compare library versions
recursivist compare old-lib new-lib \
--exclude "tests examples" \
--save \
--prefix library-upgrade
```

This extracts and compares two versions of a code library.

### Project Fork Comparison

```bash
recursivist compare original-project forked-project \
--exclude "node_modules .git" \
--save \
--prefix fork-comparison
```

This compares an original project with a forked version.

### Backup Verification

```bash
recursivist compare original-files backup-files \
--full-path \
--save \
--prefix backup-verification
```

This compares original files with their backups, showing full paths.

### Framework Comparison

```bash
recursivist compare react-project vue-project \
--include-pattern "src/**/*" \
--exclude-pattern "**/*.test.js" \
--save \
--prefix framework-comparison
```

This compares the source structure of projects built with different frameworks.

## Combining with Other Tools

### Comparison and Analysis Script

```bash
#!/bin/bash

# Compare projects
recursivist compare project-v1 project-v2 \
--save \
--prefix project-comparison

# Generate summary statistics
echo "Added files:" > comparison-summary.txt
grep -o "unique to this directory" project-comparison.html | wc -l >> comparison-summary.txt
echo "Removed files:" >> comparison-summary.txt
grep -o "unique to the other directory" project-comparison.html | wc -l >> comparison-summary.txt

echo "Comparison complete. See project-comparison.html and comparison-summary.txt"
```

This script compares two projects and generates a simple summary of the differences.

### Continuous Integration Comparison

```yaml
# Example GitHub Actions workflow
name: Structure Comparison

on:
  pull_request:
    branches: [main]

jobs:
  compare:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout main branch
        uses: actions/checkout@v3
        with:
          ref: main
          path: main-branch

      - name: Checkout PR branch
        uses: actions/checkout@v3
        with:
          ref: ${{ github.event.pull_request.head.ref }}
          path: pr-branch

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.10"

      - name: Install Recursivist
        run: pip install recursivist

      - name: Compare branches
        run: |
          recursivist compare main-branch pr-branch \
          --exclude "node_modules .git" \
          --save \
          --prefix structure-diff

      - name: Upload comparison artifact
        uses: actions/upload-artifact@v3
        with:
          name: structure-comparison
          path: structure-diff.html
```

This GitHub Actions workflow compares the directory structure between the main branch and a pull request branch.
