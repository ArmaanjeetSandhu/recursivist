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
recursivist compare dir1 dir2 --save
```

This generates an HTML file named `comparison.html` containing the comparison.

### Custom Output Location

```bash
recursivist compare dir1 dir2 --save --output-dir ./reports
```

This saves the comparison to `./reports/comparison.html`.

### Custom Filename

```bash
recursivist compare dir1 dir2 --save --prefix dir-diff
```

This saves the comparison to `dir-diff.html`.

## Comparison with File Statistics

### Comparing with Lines of Code

```bash
recursivist compare dir1 dir2 --sort-by-loc
```

This compares the directories with line count information, making it easy to identify differences in code volume.

### Comparing with File Sizes

```bash
recursivist compare dir1 dir2 --sort-by-size
```

This compares the directories with file size information, highlighting differences in file sizes.

### Comparing with Modification Times

```bash
recursivist compare dir1 dir2 --sort-by-mtime
```

This compares the directories with file modification times, showing which files are newer in each directory.

### Combining Multiple Statistics

```bash
recursivist compare dir1 dir2 --sort-by-loc --sort-by-size
```

This combines multiple statistics in a single comparison view.

## Filtered Comparisons

### Comparing with Directory Exclusions

```bash
recursivist compare dir1 dir2 --exclude "node_modules .git"
```

This compares the directories while ignoring `node_modules` and `.git` directories.

### Comparing with File Extension Exclusions

```bash
recursivist compare dir1 dir2 --exclude-ext ".pyc .log"
```

This compares the directories while ignoring files with `.pyc` and `.log` extensions.

### Comparing with Pattern Exclusions

```bash
recursivist compare dir1 dir2 --exclude-pattern "*.test.js" "*.spec.js"
```

This compares the directories while ignoring JavaScript test files.

### Focusing on Specific Files

```bash
recursivist compare dir1 dir2 --include-pattern "src/**/*.js" "*.md"
```

This compares only JavaScript files in the `src` directory and markdown files.

### Comparing with Gitignore Patterns

```bash
recursivist compare dir1 dir2 --ignore-file .gitignore
```

This compares the directories while respecting the patterns in `.gitignore`.

## Depth-Limited Comparisons

### Comparing Top-Level Structure

```bash
recursivist compare dir1 dir2 --depth 1
```

This compares only the top level of the directory structures.

### Comparing with Limited Depth

```bash
recursivist compare dir1 dir2 --depth 3
```

This compares the directories up to 3 levels deep.

## Full Path Comparisons

### Comparing with Full Paths

```bash
recursivist compare dir1 dir2 --full-path
```

This displays full file paths in the comparison instead of just filenames.

## Real-World Use Cases

### Project Version Comparison with Statistics

```bash
recursivist compare project-v1.0 project-v2.0 \
  --exclude "node_modules .git" \
  --exclude-ext ".log .tmp" \
  --save \
  --output-dir ./version-reports \
  --prefix v1-vs-v2 \
  --sort-by-loc
```

This compares two versions of a project, excluding common directories and file types, saving the report with lines of code statistics.

### Branch Comparison with Statistics

```bash
# Clone branches to compare
git clone -b main repo main-branch
git clone -b feature/new-feature repo feature-branch

# Compare directory structures with LOC stats
recursivist compare main-branch feature-branch \
  --exclude "node_modules .git" \
  --save \
  --prefix branch-comparison \
  --sort-by-loc
```

This compares the directory structures of two Git branches with line count information.

### Source vs. Build Comparison with File Sizes

```bash
recursivist compare src dist \
  --include-pattern "**/*.js" \
  --save \
  --prefix src-vs-dist \
  --sort-by-size
```

This compares JavaScript files between source and distribution directories with file size information.

### Development vs. Production Configuration Comparison

```bash
recursivist compare dev-config prod-config \
  --save \
  --output-dir ./deployment-validation \
  --prefix dev-vs-prod \
  --sort-by-size
```

This compares development and production configuration directories with file size information.

## Specific Comparison Scenarios

### Code Library Upgrade Analysis

```bash
# Extract old and new versions of a library
mkdir -p old-lib new-lib
tar -xzf library-1.0.tar.gz -C old-lib
tar -xzf library-2.0.tar.gz -C new-lib

# Compare library versions with LOC stats
recursivist compare old-lib new-lib \
  --exclude "tests examples" \
  --save \
  --prefix library-upgrade \
  --sort-by-loc
```

This extracts and compares two versions of a code library with lines of code metrics.

### Project Fork Comparison

```bash
recursivist compare original-project forked-project \
  --exclude "node_modules .git" \
  --save \
  --prefix fork-comparison \
  --sort-by-loc \
  --sort-by-mtime
```

This compares an original project with a forked version, showing both line count differences and when files were modified.

### Backup Verification with File Sizes

```bash
recursivist compare original-files backup-files \
  --full-path \
  --save \
  --prefix backup-verification \
  --sort-by-size
```

This compares original files with their backups, showing full paths and file sizes to verify backup integrity.

### Framework Comparison with Lines of Code

```bash
recursivist compare react-project vue-project \
  --include-pattern "src/**/*" \
  --exclude-pattern "**/*.test.js" \
  --save \
  --prefix framework-comparison \
  --sort-by-loc
```

This compares the source structure of projects built with different frameworks, including lines of code metrics for better comparison.

## Combining with Other Tools

### Comparison and Analysis Script

```bash
#!/bin/bash

# Compare projects with LOC stats
recursivist compare project-v1 project-v2 \
  --save \
  --prefix project-comparison \
  --sort-by-loc

# Generate summary statistics using HTML parsing
echo "Code changes summary:" > comparison-summary.txt
echo "--------------------" >> comparison-summary.txt
echo "Added files:" >> comparison-summary.txt
grep -o "unique to this directory" project-comparison.html | wc -l >> comparison-summary.txt
echo "Removed files:" >> comparison-summary.txt
grep -o "unique to the other directory" project-comparison.html | wc -l >> comparison-summary.txt
echo "Total LOC in v1:" >> comparison-summary.txt
grep -o "Directory 1.*lines" project-comparison.html | sed 's/.*(\([0-9,]*\) lines.*/\1/' | tr -d ',' >> comparison-summary.txt
echo "Total LOC in v2:" >> comparison-summary.txt
grep -o "Directory 2.*lines" project-comparison.html | sed 's/.*(\([0-9,]*\) lines.*/\1/' | tr -d ',' >> comparison-summary.txt

echo "Comparison complete. See project-comparison.html and comparison-summary.txt"
```

This script compares two projects with lines of code statistics and generates a summary of the differences.

### Continuous Integration Comparison with Statistics

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

      - name: Compare branches with statistics
        run: |
          recursivist compare main-branch pr-branch \
            --exclude "node_modules .git" \
            --save \
            --prefix structure-diff \
            --sort-by-loc \
            --sort-by-size

      - name: Upload comparison artifact
        uses: actions/upload-artifact@v3
        with:
          name: structure-comparison
          path: structure-diff.html
```

This GitHub Actions workflow compares the directory structure between the main branch and a pull request branch, including lines of code and file size statistics.

### Weekly Project Evolution Report

```bash
#!/bin/bash

# Get current date for filename
date_str=$(date +%Y-%m-%d)

# Compare current structure with last week's snapshot
if [ -d "snapshots/last_week" ]; then
  echo "Comparing with last week's snapshot..."

  # Create comparison with LOC and modification time stats
  recursivist compare snapshots/last_week . \
    --exclude "node_modules .git snapshots" \
    --save \
    --output-dir ./reports \
    --prefix "weekly-${date_str}" \
    --sort-by-loc \
    --sort-by-mtime

  echo "Weekly comparison saved to reports/weekly-${date_str}.html"
fi

# Create snapshot for next week's comparison
echo "Creating snapshot for next week's comparison..."
mkdir -p snapshots/last_week
cp -a . snapshots/last_week/ 2>/dev/null || true
find snapshots/last_week -name "node_modules" -type d -exec rm -rf {} +
```

This script compares the current project structure with a snapshot from the previous week, highlighting both code volume changes and when files were modified.
