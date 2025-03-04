# Recursivist

A beautiful command-line tool for visualizing directory structures with rich formatting, color-coding, and multiple export options.

## Features

- 🎨 **Colorful Visualization**: Each file type is assigned a unique color for easy identification
- 🌳 **Tree Structure**: Displays your directories in an intuitive, hierarchical tree format
- 📁 **Smart Filtering**: Easily exclude directories and file extensions you don't want to see
- 🧩 **Gitignore Support**: Automatically respects your `.gitignore` patterns
- 🔍 **Powerful Pattern Matching**: Use glob and regex patterns to precisely include or exclude files
- 🔄 **Directory Comparison**: Compare two directory structures side by side with highlighted differences
- 📊 **Multiple Export Formats**: Export to TXT, JSON, HTML, Markdown, and React components
- 🔎 **Depth Control**: Limit the display depth to focus on higher-level structure
- 🌐 **Full Path Display**: Option to show full paths instead of just filenames
- 🚀 **Simple Interface**: Intuitive command-line interface with smart defaults

## Installation

### From PyPI

```bash
pip install recursivist
```

### From Source

```bash
git clone https://github.com/ArmaanjeetSandhu/recursivist.git
cd recursivist
pip install .
```

## Usage

### Basic Usage

Just run the command in any directory:

```bash
recursivist visualize
```

This will show a colorful tree of the current directory structure in your terminal.

### Command Overview

| Command      | Description                                    |
| ------------ | ---------------------------------------------- |
| `visualize`  | Display directory structures in the terminal   |
| `export`     | Export directory structures to various formats |
| `compare`    | Compare two directory structures side by side  |
| `completion` | Generate shell completion scripts              |
| `version`    | Show the current version                       |

### Advanced Options

#### Visualize Command

```bash
# Visualize a specific directory
recursivist visualize /path/to/directory

# Exclude specific directories
recursivist visualize \
  --exclude node_modules .git venv

# Exclude file extensions
recursivist visualize \
  --exclude-ext .pyc .log .cache

# Use a gitignore-style file
recursivist visualize \
  --ignore-file .gitignore

# Use glob patterns to exclude files
recursivist visualize \
  --exclude-pattern "*.test.js" "*.spec.js"

# Use regex patterns for more precise control
recursivist visualize \
  --exclude-pattern "^test_.*\.py$" ".*_test\.js$" \
  --regex

# Include only specific patterns (overrides exclusions)
recursivist visualize \
  --include-pattern "src/*" "*.md"

# Include with regex patterns
recursivist visualize \
  --include-pattern "^src/.*\.jsx?$" "^docs/.*\.md$" \
  --regex

# Limit directory depth
recursivist visualize \
  --depth 3

# Show full file paths
recursivist visualize \
  --full-path

# Enable verbose output
recursivist visualize \
  --verbose
```

#### Export Command

```bash
# Export to various formats
recursivist export \
  --format txt json html md jsx

# Export a specific directory to a specific output directory
recursivist export /path/to/directory \
  --format md \
  --output-dir ./exports

# Export as a React component
recursivist export \
  --format jsx \
  --output-dir ./components

# Custom filename prefix for exports
recursivist export \
  --format json \
  --prefix my-project

# Export with exclusions and pattern matching
recursivist export \
  --exclude node_modules \
  --exclude-ext .pyc \
  --exclude-pattern "*.test.js"

# Export with depth limit and full paths
recursivist export \
  --depth 2 \
  --full-path
```

#### Compare Command

```bash
# Compare two directories
recursivist compare /path/to/dir1 /path/to/dir2

# Compare with pattern exclusions
recursivist compare dir1 dir2 \
  --exclude-pattern "*.test.js" \
  --regex

# Compare with depth limit
recursivist compare dir1 dir2 \
  --depth 2

# Compare and export the comparison
recursivist compare dir1 dir2 \
  --save \
  --output-dir ./reports

# Compare with full paths
recursivist compare dir1 dir2 \
  --full-path

# Compare with directory exclusions
recursivist compare dir1 dir2 \
  --exclude node_modules .git
```

#### Other Commands

```bash
# View the current version
recursivist version

# Generate shell completion for different shells
recursivist completion bash > ~/.bash_completion.d/recursivist
recursivist completion zsh > ~/.zsh/completion/_recursivist
recursivist completion fish > ~/.config/fish/completions/recursivist.fish
recursivist completion powershell > recursivist.ps1
```

### Command Options

#### `visualize` Command Options

| Option              | Short | Description                                                    |
| ------------------- | ----- | -------------------------------------------------------------- |
| `--exclude`         | `-e`  | Directories to exclude (space-separated or multiple flags)     |
| `--exclude-ext`     | `-x`  | File extensions to exclude (space-separated or multiple flags) |
| `--exclude-pattern` | `-p`  | Patterns to exclude (glob by default, regex with --regex flag) |
| `--include-pattern` | `-i`  | Patterns to include (overrides exclusions)                     |
| `--regex`           | `-r`  | Treat patterns as regex instead of glob patterns               |
| `--ignore-file`     | `-g`  | Ignore file to use (e.g., .gitignore)                          |
| `--depth`           | `-d`  | Maximum depth to display (0 for unlimited)                     |
| `--full-path`       | `-l`  | Show full paths instead of just filenames                      |
| `--verbose`         | `-v`  | Enable verbose output                                          |

#### `export` Command Options

| Option              | Short | Description                                                    |
| ------------------- | ----- | -------------------------------------------------------------- |
| `--format`          | `-f`  | Export formats: txt, json, html, md, jsx                       |
| `--output-dir`      | `-o`  | Output directory for exports                                   |
| `--prefix`          | `-n`  | Prefix for exported filenames                                  |
| `--exclude`         | `-e`  | Directories to exclude (space-separated or multiple flags)     |
| `--exclude-ext`     | `-x`  | File extensions to exclude (space-separated or multiple flags) |
| `--exclude-pattern` | `-p`  | Patterns to exclude (glob by default, regex with --regex flag) |
| `--include-pattern` | `-i`  | Patterns to include (overrides exclusions)                     |
| `--regex`           | `-r`  | Treat patterns as regex instead of glob patterns               |
| `--ignore-file`     | `-g`  | Ignore file to use (e.g., .gitignore)                          |
| `--depth`           | `-d`  | Maximum depth to display (0 for unlimited)                     |
| `--full-path`       | `-l`  | Show full paths instead of just filenames                      |
| `--verbose`         | `-v`  | Enable verbose output                                          |

#### `compare` Command Options

| Option              | Short | Description                                                    |
| ------------------- | ----- | -------------------------------------------------------------- |
| `--exclude`         | `-e`  | Directories to exclude (space-separated or multiple flags)     |
| `--exclude-ext`     | `-x`  | File extensions to exclude (space-separated or multiple flags) |
| `--exclude-pattern` | `-p`  | Patterns to exclude (glob by default, regex with --regex flag) |
| `--include-pattern` | `-i`  | Patterns to include (overrides exclusions)                     |
| `--regex`           | `-r`  | Treat patterns as regex instead of glob patterns               |
| `--ignore-file`     | `-g`  | Ignore file to use (e.g., .gitignore)                          |
| `--depth`           | `-d`  | Maximum depth to display (0 for unlimited)                     |
| `--full-path`       | `-l`  | Show full paths instead of just filenames                      |
| `--save`            | `-f`  | Save comparison result to HTML file                            |
| `--output-dir`      | `-o`  | Output directory for exports                                   |
| `--prefix`          | `-n`  | Prefix for exported filenames                                  |
| `--verbose`         | `-v`  | Enable verbose output                                          |

## Examples

### Basic Directory Visualization

```bash
recursivist visualize
```

This will produce output similar to:

```
📂 my-project
├── 📁 src
│   ├── 📄 main.py
│   ├── 📄 utils.py
│   └── 📁 tests
│       ├── 📄 test_main.py
│       └── 📄 test_utils.py
├── 📄 README.md
├── 📄 requirements.txt
└── 📄 setup.py
```

### Pattern Matching with Glob and Regex

Recursivist supports both glob patterns (default) and regular expressions for precise control over which files and directories to include or exclude.

#### Glob Pattern Examples

Glob patterns use wildcard characters like `*` to match multiple characters:

```bash
# Exclude all JavaScript test files
recursivist visualize \
  --exclude-pattern "*.test.js" "*.spec.js"

# Include only source code and documentation
recursivist visualize \
  --include-pattern "src/*" "docs/*.md"
```

#### Regex Pattern Examples

For more precise control, use the `--regex` flag to enable regular expressions:

```bash
# Exclude files starting with "test_" and ending with ".py"
recursivist visualize \
  --exclude-pattern "^test_.*\.py$" \
  --regex

# Include only React components in the src directory
recursivist visualize \
  --include-pattern "^src/.*\.(jsx|tsx)$" \
  --regex
```

#### Combining Include and Exclude Patterns

When you specify both include and exclude patterns, include patterns take precedence:

```bash
# Include all markdown files, but exclude those containing "draft"
recursivist visualize \
  --include-pattern "*.md" \
  --exclude-pattern "*draft*"

# With regex, include TypeScript files but exclude test files
recursivist visualize \
  --include-pattern "^.*\.ts$" \
  --exclude-pattern ".*\.test\.ts$" \
  --regex
```

### Directory Comparison

```bash
recursivist compare ~/project-v1 ~/project-v2
```

This will display two directory trees side by side with differences highlighted:

- Files and directories unique to each directory are highlighted
- A legend explains the color-coding

You can export the comparison to HTML:

```bash
recursivist compare ~/project-v1 ~/project-v2 \
  --save \
  --output-dir ./reports
```

### Limiting Directory Depth

For large projects, it can be helpful to limit the display depth:

```bash
recursivist visualize \
  --depth 2
```

This will show only the top two levels of the directory structure, with an indicator showing where the depth limit was reached.

### Showing Full Paths

When you need to see the complete path for each file:

```bash
recursivist visualize \
  --full-path
```

This will display the full path for each file rather than just the filename.

### Export to Multiple Formats

```bash
recursivist export \
  --format "txt md jsx" \
  --output-dir ./docs
```

This exports the directory structure to text, markdown, and React component formats in the `./docs` directory.

### Exclude Unwanted Directories and Files

```bash
recursivist visualize \
  --exclude node_modules .git \
  --exclude-ext .pyc .log
```

This shows the directory tree while ignoring the `node_modules` and `.git` directories, as well as any `.pyc` and `.log` files.

## Export Formats

### Text (TXT)

A simple ASCII tree representation that can be viewed in any text editor.

### JSON

A structured JSON format that can be easily parsed by other tools or scripts.

### HTML

An HTML representation with styling that can be viewed in any web browser.

### Markdown (MD)

A markdown representation that renders nicely on platforms like GitHub.

### React Component (JSX)

An interactive React component with a collapsible tree view that can be integrated into your web applications. The component uses Tailwind CSS for styling and includes features like "Expand All" and "Collapse All" buttons.

```bash
recursivist export \
  --format jsx \
  --output-dir ./components
```

This creates a self-contained React component file that you can import directly into your React projects. To use it:

1. Copy the generated `.jsx` file to your React project's components directory
2. Make sure you have the required dependencies:
   ```
   npm install lucide-react
   ```
3. Import and use the component in your application:

   ```jsx
   import DirectoryViewer from "./components/structure.jsx";

   function App() {
     return (
       <div className="App">
         <DirectoryViewer />
       </div>
     );
   }
   ```

**Note:** The component uses Tailwind CSS for styling. If your project doesn't use Tailwind, you'll need to add it or modify the component to use your preferred styling solution.

## Shell Completion

Recursivist supports shell completion for easier command entry. Generate completion scripts with:

```bash
# For Bash
recursivist completion bash > ~/.bash_completion.d/recursivist

# For Zsh
recursivist completion zsh > ~/.zsh/completion/_recursivist

# For Fish
recursivist completion fish > ~/.config/fish/completions/recursivist.fish

# For PowerShell
recursivist completion powershell > recursivist.ps1
```

## Advanced Usage

### Using with Git Repositories

When working with Git repositories, you can use your existing `.gitignore` file:

```bash
recursivist visualize \
  --ignore-file .gitignore
```

### Integration with Other Tools

The JSON export format allows for easy integration with other tools:

```bash
# Export to JSON
recursivist export \
  --format json \
  --prefix myproject

# Use with jq for additional processing
cat myproject.json | jq '.structure | keys'
```

## Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/ArmaanjeetSandhu/recursivist.git
cd recursivist

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run tests
pytest
```

### Building the Package

```bash
# Install build tools
pip install build

# Build the package
python -m build
```

## Testing

The Recursivist project uses pytest for testing. The test suite covers core functionality, CLI interface, export features, comparison functionality, regex pattern matching, and depth limiting.

### Running Tests

To run the tests, first install the development dependencies:

```bash
pip install -e ".[dev]"
```

Then run the tests with:

```bash
pytest
```

You can also run specific test files:

```bash
# Run only core tests
pytest test_core.py

# Run only export tests
pytest test_exports.py

# Run only CLI tests
pytest test_cli.py

# Run only compare tests
pytest test_compare.py

# Run regex pattern tests
pytest test_regex.py

# Run depth limit tests
pytest test_depth.py

# Run integration tests
pytest test_integration.py
```

### Test Coverage

To generate a detailed coverage report:

```bash
pytest \
  --cov=recursivist \
  --cov-report=html
```

This will create an HTML coverage report in the `htmlcov` directory, which you can open in your browser.

### Continuous Integration

The test suite is automatically run on GitHub Actions for every pull request and push to the main branch. This ensures that all changes maintain compatibility and don't introduce regressions.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Acknowledgements

- [Rich](https://github.com/Textualize/rich) - For beautiful terminal formatting
- [Typer](https://github.com/tiangolo/typer) - For the intuitive CLI interface

## Author

**Armaanjeet Singh Sandhu**

- Email: armaanjeetsandhu430@gmail.com
- GitHub: [ArmaanjeetSandhu](https://github.com/ArmaanjeetSandhu)
