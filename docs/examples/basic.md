# Basic Examples

This page provides simple examples of common Recursivist usage patterns. These examples are designed to help you get familiar with the basic capabilities of the tool.

## Simple Visualization

### Viewing the Current Directory

To visualize the current directory structure:

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

### Viewing a Specific Directory

To visualize a different directory:

```bash
recursivist visualize ~/projects/my-app
```

### Limiting Directory Depth

To limit the depth of the directory tree (useful for large projects):

```bash
recursivist visualize --depth 2
```

Output:

```
📂 my-project
├── 📁 src
│   ├── 📄 main.py
│   ├── 📄 utils.py
│   └── 📁 tests
│       ⋯ (max depth reached)
├── 📄 README.md
├── 📄 requirements.txt
└── 📄 setup.py
```

### Showing Full Paths

To show full file paths instead of just filenames:

```bash
recursivist visualize --full-path
```

Output:

```
📂 my-project
├── 📁 src
│   ├── 📄 /home/user/my-project/src/main.py
│   ├── 📄 /home/user/my-project/src/utils.py
│   └── 📁 tests
│       ├── 📄 /home/user/my-project/src/tests/test_main.py
│       └── 📄 /home/user/my-project/src/tests/test_utils.py
├── 📄 /home/user/my-project/README.md
├── 📄 /home/user/my-project/requirements.txt
└── 📄 /home/user/my-project/setup.py
```

## File Statistics

### Showing Lines of Code

To display and sort by lines of code:

```bash
recursivist visualize --sort-by-loc
```

Output:

```
📂 my-project (4328 lines)
├── 📁 src (3851 lines)
│   ├── 📄 main.py (245 lines)
│   ├── 📄 utils.py (157 lines)
│   └── 📁 tests (653 lines)
│       ├── 📄 test_main.py (412 lines)
│       └── 📄 test_utils.py (241 lines)
├── 📄 README.md (124 lines)
├── 📄 requirements.txt (18 lines)
└── 📄 setup.py (65 lines)
```

### Showing File Sizes

To display and sort by file sizes:

```bash
recursivist visualize --sort-by-size
```

Output:

```
📂 my-project (1.2 MB)
├── 📁 src (850.5 KB)
│   ├── 📄 main.py (12.4 KB)
│   ├── 📄 utils.py (8.2 KB)
│   └── 📁 tests (45.7 KB)
│       ├── 📄 test_main.py (28.9 KB)
│       └── 📄 test_utils.py (16.8 KB)
├── 📄 README.md (4.2 KB)
├── 📄 requirements.txt (512 B)
└── 📄 setup.py (3.8 KB)
```

### Showing Modification Times

To display and sort by modification times:

```bash
recursivist visualize --sort-by-mtime
```

Output:

```
📂 my-project (Today 14:30)
├── 📁 src (Today 14:25)
│   ├── 📄 main.py (Today 14:25)
│   ├── 📄 utils.py (Yesterday 18:10)
│   └── 📁 tests (Feb 15)
│       ├── 📄 test_main.py (Feb 15)
│       └── 📄 test_utils.py (Feb 10)
├── 📄 README.md (Today 10:15)
├── 📄 requirements.txt (Jan 20)
└── 📄 setup.py (Jan 15)
```

### Combining Statistics

To show multiple statistics at once:

```bash
recursivist visualize --sort-by-loc --sort-by-size
```

Output:

```
📂 my-project (4328 lines, 1.2 MB)
├── 📁 src (3851 lines, 850.5 KB)
│   ├── 📄 main.py (245 lines, 12.4 KB)
...
```

## Simple Exclusions

### Excluding Specific Directories

To exclude directories like `node_modules` or `.git`:

```bash
recursivist visualize --exclude "node_modules .git"
```

### Excluding File Extensions

To exclude files with specific extensions:

```bash
recursivist visualize --exclude-ext ".pyc .log"
```

### Combining Exclusions

You can combine different exclusion methods:

```bash
recursivist visualize --exclude "node_modules .git" --exclude-ext ".pyc .log"
```

## Basic Exports

### Exporting to Markdown

To export the current directory structure to Markdown:

```bash
recursivist export --format md
```

This creates a file named `structure.md` in the current directory.

### Exporting to Multiple Formats

To export to multiple formats at once:

```bash
recursivist export --format "txt md json"
```

### Exporting to a Specific Directory

To export to a different directory:

```bash
recursivist export --format html --output-dir ./docs
```

### Customizing the Filename

To use a custom filename prefix:

```bash
recursivist export --format json --prefix my-project
```

This creates a file named `my-project.json`.

### Exporting with Statistics

To include file statistics in the export:

```bash
recursivist export --format html --sort-by-loc --sort-by-size
```

## Simple Comparisons

### Comparing Two Directories

To compare two directories:

```bash
recursivist compare dir1 dir2
```

This displays a side-by-side comparison in the terminal.

### Exporting a Comparison

To save the comparison as an HTML file:

```bash
recursivist compare dir1 dir2 --save
```

This creates a file named `comparison.html` in the current directory.

### Comparing with Statistics

To include file statistics in the comparison:

```bash
recursivist compare dir1 dir2 --sort-by-loc
```

This makes it easy to see not just structural differences but also differences in code volume.

## Shell Completion

### Generating Shell Completion for Bash

```bash
mkdir -p ~/.bash_completion.d
recursivist completion bash > ~/.bash_completion.d/recursivist
source ~/.bash_completion.d/recursivist
```

### Generating Shell Completion for Zsh

```bash
mkdir -p ~/.zsh/completion
recursivist completion zsh > ~/.zsh/completion/_recursivist
```

Then add to your `.zshrc`:

```bash
fpath=(~/.zsh/completion $fpath)
autoload -U compinit; compinit
```

## Version Information

To check the version of Recursivist:

```bash
recursivist version
```

## Next Steps

These basic examples should help you get started with Recursivist. For more advanced examples, check out:

- [Filtering Examples](filtering.md) - More complex pattern matching
- [Export Examples](export.md) - Advanced export options
- [Compare Examples](compare.md) - In-depth comparison examples
- [Advanced Examples](advanced.md) - Advanced usage patterns
