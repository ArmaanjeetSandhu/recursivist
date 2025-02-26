# Recursivist

A beautiful command-line tool for visualizing directory structures with rich formatting, color-coding, and multiple export options.

## Features

- 🎨 **Colorful Visualization**: Each file type is assigned a unique color for easy identification
- 🌳 **Tree Structure**: Displays your directories in an intuitive, hierarchical tree format
- 📁 **Smart Filtering**: Easily exclude directories and file extensions you don't want to see
- 🧩 **Gitignore Support**: Automatically respects your `.gitignore` patterns
- 📊 **Multiple Export Formats**: Export to TXT, JSON, HTML, and Markdown
- 🔄 **Directory Comparison**: Compare two directory structures side by side with highlighted differences
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

### Advanced Options

```bash
# Visualize a specific directory
recursivist visualize /path/to/directory

# Exclude specific directories
recursivist visualize --exclude node_modules .git venv

# Exclude file extensions
recursivist visualize --exclude-ext .pyc .log .cache

# Use a gitignore-style file
recursivist visualize --ignore-file .gitignore

# Export to various formats
recursivist visualize --export txt json html md

# Export to a specific directory
recursivist visualize --export md --output-dir ./exports

# Custom filename prefix for exports
recursivist visualize --export json --prefix my-project

# Compare two directories
recursivist compare /path/to/dir1 /path/to/dir2

# Compare and export the comparison
recursivist compare dir1 dir2 --export html --output-dir ./reports

# View the current version
recursivist version

# Generate shell completion
recursivist completion bash > ~/.bash_completion.d/recursivist
```

### Command Overview

| Command      | Description                                   |
| ------------ | --------------------------------------------- |
| `visualize`  | Display and export directory structures       |
| `compare`    | Compare two directory structures side by side |
| `completion` | Generate shell completion scripts             |
| `version`    | Show the current version                      |

### Command Options for `visualize`

| Option          | Short | Description                                                    |
| --------------- | ----- | -------------------------------------------------------------- |
| `--exclude`     | `-e`  | Directories to exclude (space-separated or multiple flags)     |
| `--exclude-ext` | `-x`  | File extensions to exclude (space-separated or multiple flags) |
| `--ignore-file` | `-i`  | Ignore file to use (e.g., .gitignore)                          |
| `--export`      | `-f`  | Export formats: txt, json, html, md                            |
| `--output-dir`  | `-o`  | Output directory for exports                                   |
| `--prefix`      | `-p`  | Prefix for exported filenames                                  |
| `--verbose`     | `-v`  | Enable verbose output                                          |

### Command Options for `compare`

| Option          | Short | Description                                                    |
| --------------- | ----- | -------------------------------------------------------------- |
| `--exclude`     | `-e`  | Directories to exclude (space-separated or multiple flags)     |
| `--exclude-ext` | `-x`  | File extensions to exclude (space-separated or multiple flags) |
| `--ignore-file` | `-i`  | Ignore file to use (e.g., .gitignore)                          |
| `--export`      | `-f`  | Export formats: txt, json, html, md                            |
| `--output-dir`  | `-o`  | Output directory for exports                                   |
| `--prefix`      | `-p`  | Prefix for exported filenames                                  |
| `--verbose`     | `-v`  | Enable verbose output                                          |

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

### Directory Comparison

```bash
recursivist compare ~/project-v1 ~/project-v2
```

This will display two directory trees side by side with differences highlighted:

- Files and directories present only in the first directory are highlighted in green
- Files and directories present only in the second directory are highlighted in red

You can export the comparison to various formats:

```bash
recursivist compare ~/project-v1 ~/project-v2 --export html --output-dir ./reports
```

### Export to Multiple Formats

```bash
recursivist visualize --export txt md --output-dir ./docs
```

This exports the directory structure to both text and markdown formats in the `./docs` directory.

### Exclude Unwanted Directories and Files

```bash
recursivist visualize --exclude node_modules .git --exclude-ext .pyc .log
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
recursivist visualize --ignore-file .gitignore
```

### Integration with Other Tools

The JSON export format allows for easy integration with other tools:

```bash
# Export to JSON
recursivist visualize --export json --prefix myproject

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

The Recursivist project uses pytest for testing. The test suite covers core functionality, CLI interface, and export features.

### Running Tests

To run the tests, first install the development dependencies:

```bash
pip install -e ".[dev]"
```

Then run the tests with coverage reporting:

```bash
pytest
```

You can also run specific test files:

```bash
# Run only core tests
pytest tests/test_core.py

# Run only export tests
pytest tests/test_exports.py

# Run only CLI tests
pytest tests/test_cli.py

# Run only compare tests
pytest tests/test_compare.py
```

### Test Coverage

To generate a detailed coverage report:

```bash
pytest --cov=recursivist --cov-report=html
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
- [Typer](https://github.com/fastapi/typer) - For the intuitive CLI interface

## Author

**Armaanjeet Singh Sandhu**

- Email: armaanjeetsandhu430@gmail.com
- GitHub: [ArmaanjeetSandhu](https://github.com/ArmaanjeetSandhu)
