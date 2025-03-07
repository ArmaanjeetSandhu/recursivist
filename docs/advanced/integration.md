# Integration with Other Tools

Recursivist can be integrated with other tools and workflows to enhance productivity. This page provides guidance on various integration options.

## Using with Git Repositories

When working with Git repositories, you can use your existing `.gitignore` file to filter the directory structure:

```bash
recursivist visualize \
--ignore-file .gitignore
```

This is particularly useful for quickly visualizing the structure of a Git repository without the noise of ignored files.

## Integration with Shell Scripts

You can use Recursivist in shell scripts to automate directory visualization and export tasks:

```bash
#!/bin/bash

# Generate directory structure visualization for multiple projects
for project in projects/*; do
  if [ -d "$project" ]; then
    echo "Processing $project..."
    recursivist export "$project" --format md --output-dir ./reports --prefix "$(basename $project)"
  fi
done
```

## Processing JSON Exports with jq

The JSON export format is particularly useful for integration with other tools. You can use tools like [jq](https://stedolan.github.io/jq/) to process and analyze the exported JSON:

```bash
# Export to JSON
recursivist export --format json --prefix myproject

# Count the number of files in each directory
cat myproject.json | jq '.structure | to_entries[] | select(.value | type == "object") | .key + ": " + (.value._files | length | tostring) + " files"'

# Find directories with the most files
cat myproject.json | jq '.structure | to_entries[] | select(.value | type == "object" and has("_files")) | {dir: .key, count: (.value._files | length)} | select(.count > 0)' | jq -s 'sort_by(.count) | reverse | .[0:5]'
```

## Programmatic Use with Python

If you need more control or want to integrate Recursivist functionality directly into your Python applications, you can use the underlying Python API:

```python
import recursivist.core as core

# Get directory structure
structure, extensions = core.get_directory_structure(
    "/path/to/directory",
    exclude_dirs=["node_modules", ".git"],
    exclude_extensions=[".pyc", ".log"],
    max_depth=3
)

# Process the structure
def count_files(directory_dict, path=""):
    count = 0
    for name, content in directory_dict.items():
        if name == "_files":
            count += len(content)
        elif isinstance(content, dict) and name != "_max_depth_reached":
            count += count_files(content, f"{path}/{name}")
    return count

total_files = count_files(structure)
print(f"Total files: {total_files}")
```

## Building Dashboards with React Export

The React component export feature allows you to integrate directory structure visualizations into your web applications and dashboards:

1. Export the directory structure as a React component:

   ```bash
   recursivist export \
   --format jsx \
   --output-dir ./components
   ```

2. Import the component into your React application:

   ```jsx
   import DirectoryViewer from "./components/structure.jsx";

   function App() {
     return (
       <div className="Dashboard">
         <header>
           <h1>Project Overview</h1>
         </header>
         <main>
           <section>
             <h2>Directory Structure</h2>
             <DirectoryViewer />
           </section>
           {/* Other dashboard components */}
         </main>
       </div>
     );
   }
   ```

## Continuous Integration Integration

You can incorporate Recursivist into your CI/CD pipelines to document project structure as part of your build process:

### GitHub Actions Example

```yaml
name: Document Project Structure

on:
  push:
    branches: [main]

jobs:
  document:
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
          mkdir -p ./docs/structure
          recursivist export --format md --output-dir ./docs/structure --prefix "project-structure"
          recursivist export --format html --output-dir ./docs/structure --prefix "project-structure"

      - name: Commit and push changes
        uses: stefanzweifel/git-auto-commit-action@v4
        with:
          commit_message: Update project structure documentation
          file_pattern: docs/structure/*
```

## Using with Documentation Tools

You can integrate Recursivist with documentation tools like Sphinx or MkDocs:

### MkDocs Integration

1. Generate a Markdown export of your project structure:

   ```bash
   recursivist export \
   --format md \
   --output-dir ./docs \
   --prefix "project-structure"
   ```

2. Include it in your MkDocs navigation:
   ```yaml
   # mkdocs.yml
   nav:
     - Home: index.md
     - Project Structure: project-structure.md
     # Other pages...
   ```

### Sphinx Integration

1. Generate a JSON export of your project structure:

   ```bash
   recursivist export \
   --format json \
   --output-dir ./docs \
   --prefix "project-structure"
   ```

2. Create a custom Sphinx extension to render the JSON as a directory tree:

   ```python
   # _ext/directory_tree.py
   import json
   from docutils import nodes
   from docutils.parsers.rst import Directive

   class DirectoryTree(Directive):
       def run(self):
           with open('docs/project-structure.json', 'r') as f:
               structure = json.load(f)

           # Render structure as a tree
           # ...

           return [node]

   def setup(app):
       app.add_directive('directory-tree', DirectoryTree)
       return {'version': '0.1'}
   ```

3. Use the directive in your documentation:

   ```rst
   Project Structure
   ================

   .. directory-tree::
   ```

## Command-Line Integration

You can combine Recursivist with other command-line tools:

### Combining with find and grep

```bash
# Find all Python files and visualize their directory structure
find . -name "*.py" | xargs dirname | sort | uniq | xargs recursivist visualize

# Export only directories containing test files
find . -name "*test*.py" | xargs dirname | sort | uniq > test_dirs.txt
cat test_dirs.txt | xargs -I {} recursivist export {} --format md --prefix "test-structure"
```

### Integration with git-ls-files

```bash
# Visualize only tracked files in a Git repository
git ls-files | xargs dirname | sort | uniq | xargs recursivist visualize
```

## API Documentation

For more advanced integrations, refer to the API documentation of the core modules:

- `recursivist.core`: Core functionality for building, filtering, and displaying directory structures
- `recursivist.exports`: Export functionality for various formats
- `recursivist.compare`: Comparison functionality for two directory structures
