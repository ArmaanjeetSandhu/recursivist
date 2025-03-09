# Advanced Examples

This page provides advanced examples of using Recursivist for more complex scenarios and integrations.

## Working with File Statistics

### Finding Large Files Across Projects

```bash
#!/bin/bash

# Process multiple projects to find largest files
echo "Finding largest files across projects..."
echo "----------------------------------------"

for dir in projects/*/; do
  if [ -d "$dir" ]; then
    project_name=$(basename "$dir")
    echo "Exporting size data for $project_name..."

    # Export project with size data
    recursivist export "$dir" \
      --format json \
      --prefix "${project_name}_sizes" \
      --output-dir ./analysis \
      --sort-by-size \
      --exclude "node_modules .git"
  fi
done

# Find largest files using jq
echo "Top 10 largest files across all projects:"
cat analysis/*_sizes.json | \
  jq -r '.structure | .. | objects | select(has("_files")) | ._files[] |
      select(type=="object" and has("size")) |
      "\(.size) \(.path)"' | \
  sort -nr | head -10 | \
  awk '{printf "%.2f MB: %s\n", $1/(1024*1024), substr($0, length($1)+2)}'
```

### Lines of Code Analysis with Filtering

```bash
#!/bin/bash

# Analyze code density by file type
echo "Code density by file type in project:"

# Export with LOC data
recursivist export \
  --format json \
  --prefix code_stats \
  --sort-by-loc \
  --sort-by-size \
  --exclude "node_modules .git build dist"

# Analyze with jq
jq -r '.structure | .. | objects | select(has("_files")) | ._files[] |
    select(type=="object" and has("loc") and has("size") and .loc > 0) |
    {path: .path, ext: (.path | split(".") | .[-1]), loc: .loc, size: .size,
     density: (.loc / (.size/1024))} |
    .ext + "," + (.density | tostring)' code_stats.json | \
  awk -F, '{sum[$1] += $2; count[$1]++}
    END {for (ext in sum)
      printf "%s files: %.2f lines per KB (avg of %d files)\n",
      ext, sum[ext]/count[ext], count[ext]}' | \
  sort -k3 -nr
```

### Finding Recently Modified Code

```bash
#!/bin/bash

# Show files modified in the last day
echo "Recent code changes:"

# Use sort-by-mtime to prioritize recent changes
recursivist visualize \
  --sort-by-mtime \
  --exclude "node_modules .git dist" \
  --exclude-ext ".log .tmp" | \
  grep "Today\|Yesterday" | head -20

# Alternative script to export recent changes to HTML
recursivist export \
  --format html \
  --prefix recent_changes \
  --sort-by-mtime \
  --exclude "node_modules .git" \
  --include-pattern "src/**/*" \
  --output-dir ./reports

echo "Recent changes exported to reports/recent_changes.html"
```

## Combining Commands with Shell Scripts

### Batch Processing Multiple Directories

```bash
#!/bin/bash

# Process all direct subdirectories with file statistics
for dir in */; do
  if [ -d "$dir" ] && [ "$dir" != "node_modules/" ] && [ "$dir" != ".git/" ]; then
    dir_name=$(basename "$dir")
    echo "Processing $dir_name..."

    # Visualize and export with lines of code statistics
    recursivist visualize "$dir" \
      --exclude "node_modules .git" \
      --exclude-ext .log \
      --sort-by-loc

    recursivist export "$dir" \
      --format md \
      --output-dir ./reports \
      --prefix "$dir_name" \
      --sort-by-loc \
      --sort-by-size
  fi
done
```

### Project Report Generator

```bash
#!/bin/bash

# Create report directory
mkdir -p project-report

# Generate project overview
recursivist export \
  --format md \
  --depth 2 \
  --exclude "node_modules .git" \
  --output-dir ./project-report \
  --prefix "01-overview"

# Generate detailed source structure with statistics
recursivist export src \
  --format md \
  --output-dir ./project-report \
  --prefix "02-source" \
  --sort-by-loc \
  --sort-by-size

# Generate test structure
recursivist export tests \
  --format md \
  --output-dir ./project-report \
  --prefix "03-tests" \
  --sort-by-loc

# Generate documentation structure
recursivist export docs \
  --format md \
  --output-dir ./project-report \
  --prefix "04-documentation"

# Combine into a single report
cat ./project-report/01-overview.md > ./project-report/project-structure.md
echo "" >> ./project-report/project-structure.md
cat ./project-report/02-source.md >> ./project-report/project-structure.md
echo "" >> ./project-report/project-structure.md
cat ./project-report/03-tests.md >> ./project-report/project-structure.md
echo "" >> ./project-report/project-structure.md
cat ./project-report/04-documentation.md >> ./project-report/project-structure.md

echo "Project report generated at ./project-report/project-structure.md"
```

## Integration with Other Tools

### Git Hook for Project Structure Documentation

Create a pre-commit hook (`.git/hooks/pre-commit`) to keep your project structure documentation up-to-date:

```bash
#!/bin/bash

# Check if the structure has changed
if git diff --cached --name-only | grep -q -v "structure.md"; then
  echo "Updating project structure documentation..."

  # Generate updated structure documentation with LOC statistics
  recursivist export \
    --format md \
    --exclude "node_modules .git" \
    --prefix "structure" \
    --sort-by-loc

  # Add the updated file to the commit
  git add structure.md
fi
```

Make the hook executable:

```bash
chmod +x .git/hooks/pre-commit
```

### Using with Continuous Integration

Here's a GitHub Actions workflow to document project structure with statistics on each push:

```yaml
name: Update Structure Documentation

on:
  push:
    branches: [main]
    paths-ignore:
      - "docs/structure.md"

jobs:
  update-structure:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.10"

      - name: Install Recursivist
        run: pip install recursivist

      - name: Generate structure documentation
        run: |
          mkdir -p docs
          recursivist export \
            --format md \
            --exclude "node_modules .git" \
            --output-dir ./docs \
            --prefix "structure" \
            --sort-by-loc \
            --sort-by-size

      - name: Commit and push if changed
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add docs/structure.md
          git diff --quiet && git diff --staged --quiet || git commit -m "Update project structure documentation"
          git push
```

### MkDocs Integration with Statistics

Add this to your MkDocs workflow to include project structure with LOC metrics:

```yaml
name: Build Documentation

on:
  push:
    branches: [main]

jobs:
  build-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.10"

      - name: Install dependencies
        run: |
          pip install mkdocs mkdocs-material recursivist

      - name: Generate structure documentation
        run: |
          recursivist export \
            --format md \
            --exclude "node_modules .git" \
            --output-dir ./docs \
            --prefix "structure" \
            --sort-by-loc

      - name: Build and deploy docs
        run: mkdocs gh-deploy --force
```

## Using with Git Repositories

### Comparing Git Branches with Statistics

```bash
#!/bin/bash

# Compare structure between current branch and main with file statistics
current_branch=$(git rev-parse --abbrev-ref HEAD)

# Create temporary directories
mkdir -p .tmp/current .tmp/main

# Copy current branch files (excluding .git)
git ls-files | xargs -I{} cp --parents {} .tmp/current/

# Checkout main branch files
git checkout main -- .
git ls-files | xargs -I{} cp --parents {} .tmp/main/
git checkout $current_branch -- .

# Compare the structures with LOC stats
recursivist compare .tmp/current .tmp/main \
  --save \
  --prefix "branch-comparison" \
  --sort-by-loc

# Clean up
rm -rf .tmp

echo "Branch comparison saved to branch-comparison.html"
```

### Analyzing Git Repository Structure with Statistics

```bash
#!/bin/bash

# Clone repository to analyze
if [ $# -ne 1 ]; then
  echo "Usage: $0 <repository-url>"
  exit 1
fi

repo_url=$1
repo_name=$(basename $repo_url .git)

echo "Analyzing repository: $repo_url"
git clone $repo_url --depth 1
cd $repo_name

# Generate structure reports with file statistics
recursivist export \
  --format md \
  --exclude "node_modules .git" \
  --prefix "structure" \
  --sort-by-loc

recursivist export \
  --format json \
  --exclude "node_modules .git" \
  --prefix "structure" \
  --sort-by-loc \
  --sort-by-size

# Analysis using JSON output and jq
echo "Structure Analysis:"
echo "-------------------"
echo "Total files: $(jq '.structure | .. | objects | select(has("_files")) | ._files | length' structure.json | jq -s 'add')"
echo "Total lines of code: $(jq '.structure._loc // 0' structure.json)"

# Get directory counts and LOC by directory
echo "Directory structure with LOC counts:"
jq -r '.structure | to_entries[] |
    select(.value | type == "object" and has("_files") and has("_loc")) |
    .key + ": " + (.value._loc | tostring) + " lines in " +
    (.value._files | length | tostring) + " files"' structure.json | sort -t: -k2 -nr

# Cleanup
cd ..
echo "Analysis complete. Reports in ./$repo_name/structure.md and ./$repo_name/structure.json"
```

## Limiting Directory Depth with File Statistics

### Visualizing Deep Directories Incrementally with Statistics

```bash
#!/bin/bash

# Start with a high-level overview including LOC counts
echo "High-level overview (depth=1):"
recursivist visualize --depth 1 --sort-by-loc

# Show more detail for interesting directories
read -p "Enter a directory to explore further: " dir
if [ -d "$dir" ]; then
  echo "Detailed view of $dir with LOC statistics:"
  recursivist visualize "$dir" --depth 2 --sort-by-loc

  # Allow exploring subdirectories
  read -p "Enter a subdirectory of $dir to explore fully: " subdir
  full_path="$dir/$subdir"
  if [ -d "$full_path" ]; then
    echo "Full view of $full_path with LOC statistics:"
    recursivist visualize "$full_path" --sort-by-loc
  else
    echo "Directory not found: $full_path"
  fi
else
  echo "Directory not found: $dir"
fi
```

### Creating a Multi-Level Project Map with Statistics

```bash
#!/bin/bash

# Create output directory
mkdir -p project-map

# Generate structure maps at different levels with file statistics
recursivist export \
  --format md \
  --depth 1 \
  --output-dir ./project-map \
  --prefix "L1-overview" \
  --sort-by-size

recursivist export \
  --format md \
  --depth 2 \
  --output-dir ./project-map \
  --prefix "L2-structure" \
  --sort-by-loc

recursivist export \
  --format md \
  --depth 3 \
  --output-dir ./project-map \
  --prefix "L3-detailed" \
  --sort-by-loc \
  --sort-by-size

recursivist export \
  --format md \
  --output-dir ./project-map \
  --prefix "L4-complete" \
  --sort-by-loc \
  --sort-by-size \
  --sort-by-mtime

echo "Project map generated with multiple detail levels in ./project-map/"
```

## React Component Integration with Statistics

### Creating a Project Explorer with File Statistics

This example shows how to integrate a Recursivist-generated React component with file statistics into a web application:

1. First, export the directory structure as a React component with file statistics:

```bash
recursivist export \
  --format jsx \
  --exclude "node_modules .git" \
  --output-dir ./src/components \
  --prefix "DirectoryViewer" \
  --sort-by-loc \
  --sort-by-size \
  --sort-by-mtime
```

2. Create a wrapper component to integrate it into your app:

```jsx
// src/components/ProjectExplorer.jsx
import React, { useState } from "react";
import DirectoryViewer from "./DirectoryViewer";

const ProjectExplorer = () => {
  const [activeTab, setActiveTab] = useState("structure");

  return (
    <div className="project-explorer">
      <h2>Project Structure</h2>
      <p>
        This interactive view shows the structure of our project with file
        statistics.
      </p>
      <div className="explorer-container p-4 bg-white rounded-lg shadow">
        <DirectoryViewer />
      </div>
    </div>
  );
};

export default ProjectExplorer;
```

3. Use the component in your application:

```jsx
// src/App.jsx
import React from "react";
import ProjectExplorer from "./components/ProjectExplorer";

function App() {
  return (
    <div className="App">
      <header>
        <h1>Project Documentation</h1>
      </header>
      <main>
        <section>
          <ProjectExplorer />
        </section>
        {/* Other sections */}
      </main>
    </div>
  );
}

export default App;
```

## Using Regex Patterns with File Statistics

### Finding Complex Files by Size

```bash
# Find large JavaScript files with specific naming patterns
recursivist visualize \
  --include-pattern "^src/.*\.(jsx?|tsx?)$" \
  --exclude-pattern ".*\.(spec|test)\.(jsx?|tsx?)$" \
  --regex \
  --sort-by-size
```

### Finding Files by LOC and Type

```bash
# Identify React components with high line counts
recursivist visualize \
  --include-pattern "^src/components/.*\.jsx$" \
  --regex \
  --sort-by-loc
```

## Integration with Analysis Tools

### Structure Analysis with LOC Statistics

```bash
#!/bin/bash

# Export JSON structure with file statistics
recursivist export \
  --format json \
  --full-path \
  --prefix "structure" \
  --sort-by-loc \
  --sort-by-size

echo "Project Structure Analysis:"
echo "=========================="

# Count total lines
total_loc=$(jq '.structure._loc // 0' structure.json)
echo "Total lines of code: $total_loc"

# Lines of code by file type
echo -e "\nLines of code by file type:"
jq -r '.structure | .. | objects | select(has("_files")) | ._files[] |
    select(type=="object" and has("loc")) |
    {ext: (.path | split(".") | .[-1]), loc: .loc} |
    .ext + "," + (.loc | tostring)' structure.json | \
  awk -F, '{sum[$1] += $2; count[$1]++}
    END {for (ext in sum)
      printf "%s: %d lines (%.1f%% of codebase) in %d files\n",
      ext, sum[$1], sum[$1]*100/'$total_loc', count[$1]}' | \
  sort -t: -k2 -nr

# Count files by type
echo -e "\nFiles by type:"
jq -r '.structure | .. | objects | select(has("_files")) | ._files[] |
    select(type=="object") |
    .path | split(".") | .[-1] | ascii_downcase' structure.json | \
  sort | uniq -c | sort -nr

# Find largest files
echo -e "\nTop 10 largest files by lines of code:"
jq -r '.structure | .. | objects | select(has("_files")) | ._files[] |
    select(type=="object" and has("loc")) |
    [.loc, .path] | @tsv' structure.json | \
  sort -nr | head -10

echo -e "\nAnalysis complete!"
```

## Using with Ignore Files and File Statistics

### Custom Ignore File for Documentation with Statistics

Create a `.recursivist-ignore` file:

```
# Ignore build artifacts and dependencies
node_modules/
dist/
build/
*.min.js
*.bundle.js

# Ignore temporary files
*.log
*.tmp
*.cache
.DS_Store

# Ignore test files
*.test.js
*.spec.js
__tests__/
test/
tests/

# Ignore configuration files
.*rc
*.config.js
*.config.ts
```

Then use it with file statistics:

```bash
recursivist visualize \
  --ignore-file .recursivist-ignore \
  --sort-by-loc \
  --sort-by-size
```

This provides a clean view focusing on the core source code and documentation, with additional insights from the file statistics.
