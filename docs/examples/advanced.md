# Advanced Examples

This page provides advanced examples of using Recursivist for more complex scenarios and integrations.

## Combining Commands with Shell Scripts

### Batch Processing Multiple Directories

```bash
#!/bin/bash

# Process all direct subdirectories
for dir in */; do
  if [ -d "$dir" ] && [ "$dir" != "node_modules/" ] && [ "$dir" != ".git/" ]; then
    dir_name=$(basename "$dir")
    echo "Processing $dir_name..."

    # Visualize and export
    recursivist visualize "$dir" \
    --exclude "node_modules .git" \
    --exclude-ext .log

    recursivist export "$dir" \
    --format md \
    --output-dir ./reports \
    --prefix "$dir_name"
  fi
done
```

This script processes all subdirectories, visualizing them in the terminal and exporting them as markdown.

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

# Generate detailed source structure
recursivist export src \
--format md \
--output-dir ./project-report \
--prefix "02-source"

# Generate test structure
recursivist export tests \
--format md \
--output-dir ./project-report \
--prefix "03-tests"

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

This script generates a comprehensive project report by combining multiple exports.

## Integration with Other Tools

### Git Hook for Project Structure Documentation

Create a pre-commit hook (`.git/hooks/pre-commit`) to keep your project structure documentation up-to-date:

```bash
#!/bin/bash

# Check if the structure has changed
if git diff --cached --name-only | grep -q -v "structure.md"; then
  echo "Updating project structure documentation..."

  # Generate updated structure documentation
  recursivist export \
--format md \
--exclude "node_modules .git" \
--prefix "structure"

  # Add the updated file to the commit
  git add structure.md
fi
```

Make the hook executable:

```bash
chmod +x .git/hooks/pre-commit
```

### Using with Continuous Integration

Here's a GitHub Actions workflow to document project structure on each push:

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
          --prefix "structure"

      - name: Commit and push if changed
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add docs/structure.md
          git diff --quiet && git diff --staged --quiet || git commit -m "Update project structure documentation"
          git push
```

### Integration with Documentation Tools

#### MkDocs Integration

Add this to your MkDocs workflow to include project structure:

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
          --prefix "structure"

      - name: Build and deploy docs
        run: mkdocs gh-deploy --force
```

## Using with Git Repositories

### Using with Git Branches

```bash
#!/bin/bash

# Compare structure between current branch and main
current_branch=$(git rev-parse --abbrev-ref HEAD)

# Create temporary directories
mkdir -p .tmp/current .tmp/main

# Copy current branch files (excluding .git)
git ls-files | xargs -I{} cp --parents {} .tmp/current/

# Checkout main branch files
git checkout main -- .
git ls-files | xargs -I{} cp --parents {} .tmp/main/
git checkout $current_branch -- .

# Compare the structures
recursivist compare .tmp/current .tmp/main \
--save \
--prefix "branch-comparison"

# Clean up
rm -rf .tmp

echo "Branch comparison saved to branch-comparison.html"
```

### Analyzing Git Repository Structure

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

# Generate structure reports
recursivist export \
--format md \
--exclude "node_modules .git" \
--prefix "structure"

recursivist export \
--format json \
--exclude "node_modules .git" \
--prefix "structure"

# Analysis using JSON output and jq
echo "Structure Analysis:"
echo "-------------------"
echo "Total files: $(jq '.structure | .. | objects | select(has("_files")) | ._files | length' structure.json | jq -s 'add')"

# Get directory counts
echo "Directory structure:"
jq -r '.structure | to_entries[] | select(.value | type == "object" and has("_files")) | .key + ": " + (.value._files | length | tostring) + " files"' structure.json

# Cleanup
cd ..
echo "Analysis complete. Reports in ./$repo_name/structure.md and ./$repo_name/structure.json"
```

## Limiting Directory Depth

### Visualizing Deep Directories Incrementally

```bash
#!/bin/bash

# Start with a high-level overview
echo "High-level overview (depth=1):"
recursivist visualize --depth 1

# Show more detail for interesting directories
read -p "Enter a directory to explore further: " dir
if [ -d "$dir" ]; then
  echo "Detailed view of $dir:"
  recursivist visualize "$dir" --depth 2

  # Allow exploring subdirectories
  read -p "Enter a subdirectory of $dir to explore fully: " subdir
  full_path="$dir/$subdir"
  if [ -d "$full_path" ]; then
    echo "Full view of $full_path:"
    recursivist visualize "$full_path"
  else
    echo "Directory not found: $full_path"
  fi
else
  echo "Directory not found: $dir"
fi
```

This script allows for interactive exploration of deep directory structures.

### Creating a Multi-Level Project Map

```bash
#!/bin/bash

# Create output directory
mkdir -p project-map

# Generate structure maps at different levels
recursivist export \
--format md \
--depth 1 \
--output-dir ./project-map \
--prefix "L1-overview"

recursivist export \
--format md \
--depth 2 \
--output-dir ./project-map \
--prefix "L2-structure"

recursivist export \
--format md \
--depth 3 \
--output-dir ./project-map \
--prefix "L3-detailed"

recursivist export \
--format md \
--output-dir ./project-map \
--prefix "L4-complete"

echo "Project map generated with multiple detail levels in ./project-map/"
```

This script creates multiple views of the same project at different levels of detail.

## React Component Integration

### Creating a Project Structure Explorer

This example shows how to integrate a Recursivist-generated React component into a web application:

1. First, export the directory structure as a React component:

```bash
recursivist export \
--format jsx \
--exclude "node_modules .git" \
--output-dir ./src/components \
--prefix "DirectoryViewer"
```

2. Create a wrapper component to integrate it into your app:

```jsx
// src/components/ProjectExplorer.jsx
import React from "react";
import DirectoryViewer from "./DirectoryViewer";

const ProjectExplorer = () => {
  return (
    <div className="project-explorer">
      <h2>Project Structure</h2>
      <p>This interactive view shows the structure of our project.</p>
      <div className="explorer-container">
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

## Using Regex Patterns for Complex Filtering

### Finding Files with Specific Naming Conventions

```bash
recursivist visualize \
--include-pattern "^[A-Z][a-zA-Z]+\.(jsx?|tsx?)$" \
--regex
```

This shows only files that start with an uppercase letter followed by lowercase letters, with a `.js`, `.jsx`, `.ts`, or `.tsx` extension (common for React components).

### Complex Exclusion Logic

```bash
recursivist visualize \
--exclude-pattern "^(node_modules|dist|build|coverage)/|.*\.(log|tmp|cache)$|^\..*" \
--regex
```

This excludes:

- Directories: `node_modules`, `dist`, `build`, `coverage`
- File extensions: `.log`, `.tmp`, `.cache`
- All hidden files and directories (starting with a dot)

### Finding Security-Related Files

```bash
recursivist visualize \
--include-pattern "^(security|auth|login|password|credential|cert|key|token|oauth|permission).*\.(js|py|go|rb|java)$|.*security.*\.(js|py|go|rb|java)$" \
--regex
```

This shows files related to security functionality based on common naming patterns.

## Integration with Analysis Tools

### Structure Analysis Script

```bash
#!/bin/bash

# Export JSON structure
recursivist export \
--format json \
--full-path \
--prefix "structure"

echo "Project Structure Analysis:"
echo "=========================="

# Count files by type (extension)
echo "Files by type:"
jq -r '.structure | .. | objects | select(has("_files")) | ._files[] | . | split(".") | select(length > 1) | .[-1] | ascii_downcase' structure.json | sort | uniq -c | sort -nr

# Count directories
echo -e "\nDirectory counts:"
jq -r '.structure | .. | objects | select(has("_files")) | ._files | length' structure.json | jq -s 'length'

# Find deepest nesting
echo -e "\nDeepest nesting level:"
jq -r '.structure | .. | objects | select(has("_files")) | ._files[] | . | split("/") | length' structure.json | sort -nr | head -1

# Clean up
# rm structure.json

echo -e "\nAnalysis complete!"
```

This script exports the directory structure as JSON and then performs various analyses on it.

## Using with Ignore Files

### Custom Ignore File for Documentation

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

Then use it:

```bash
recursivist visualize \
--ignore-file .recursivist-ignore
```

This provides a clean view focusing on the core source code and documentation.
