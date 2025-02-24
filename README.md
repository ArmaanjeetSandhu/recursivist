# Phylo-Tree

A beautiful command-line tool for visualizing directory structures with rich formatting, color-coding, and multiple export options.

## Features

- 🎨 **Colorful Visualization**: Each file type is assigned a unique color for easy identification
- 🌳 **Tree Structure**: Displays your directories in an intuitive, hierarchical tree format
- 📁 **Smart Filtering**: Easily exclude directories and file extensions you don't want to see
- 🧩 **Gitignore Support**: Automatically respects your `.gitignore` patterns
- 📊 **Multiple Export Formats**: Export to TXT, JSON, HTML, and Markdown
- 🚀 **Simple Interface**: Intuitive command-line interface with smart defaults

## Installation

### From PyPI

```bash
pip install phylo-tree
```

### From Source

```bash
git clone https://github.com/ArmaanjeetSandhu/phylo-tree.git
cd phylo-tree
pip install .
```

## Usage

### Basic Usage

Just run the command in any directory:

```bash
phylo-tree visualize
```

This will show a colorful tree of the current directory structure in your terminal.

### Advanced Options

```bash
# Visualize a specific directory
phylo-tree visualize /path/to/directory

# Exclude specific directories
phylo-tree visualize --exclude node_modules .git venv

# Exclude file extensions
phylo-tree visualize --exclude-ext .pyc .log .cache

# Use a gitignore-style file
phylo-tree visualize --ignore-file .gitignore

# Export to various formats
phylo-tree visualize --export txt json html md

# Export to a specific directory
phylo-tree visualize --export md --output-dir ./exports

# Custom filename prefix for exports
phylo-tree visualize --export json --prefix my-project

# View the current version
phylo-tree version

# Generate shell completion
phylo-tree completion bash > ~/.bash_completion.d/phylo-tree
```

### Command Overview

| Command      | Description                             |
| ------------ | --------------------------------------- |
| `visualize`  | Display and export directory structures |
| `completion` | Generate shell completion scripts       |
| `version`    | Show the current version                |

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

## Examples

### Basic Directory Visualization

```bash
phylo-tree visualize
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

### Export to Multiple Formats

```bash
phylo-tree visualize --export txt md --output-dir ./docs
```

This exports the directory structure to both text and markdown formats in the `./docs` directory.

### Exclude Unwanted Directories and Files

```bash
phylo-tree visualize --exclude node_modules .git --exclude-ext .pyc .log
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

Phylo-Tree supports shell completion for easier command entry. Generate completion scripts with:

```bash
# For Bash
phylo-tree completion bash > ~/.bash_completion.d/phylo-tree

# For Zsh
phylo-tree completion zsh > ~/.zsh/completion/_phylo-tree

# For Fish
phylo-tree completion fish > ~/.config/fish/completions/phylo-tree.fish

# For PowerShell
phylo-tree completion powershell > phylo-tree.ps1
```

## Advanced Usage

### Using with Git Repositories

When working with Git repositories, you can use your existing `.gitignore` file:

```bash
phylo-tree visualize --ignore-file .gitignore
```

### Integration with Other Tools

The JSON export format allows for easy integration with other tools:

```bash
# Export to JSON
phylo-tree visualize --export json --prefix myproject

# Use with jq for additional processing
cat myproject.json | jq '.structure | keys'
```

## Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/ArmaanjeetSandhu/phylo-tree.git
cd phylo-tree

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
