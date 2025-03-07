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
recursivist visualize \
--depth 2
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
recursivist visualize \
--full-path
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

## Simple Exclusions

### Excluding Specific Directories

To exclude directories like `node_modules` or `.git`:

```bash
recursivist visualize \
--exclude "node_modules .git"
```

### Excluding File Extensions

To exclude files with specific extensions:

```bash
recursivist visualize \
--exclude-ext ".pyc .log"
```

### Combining Exclusions

You can combine different exclusion methods:

```bash
recursivist visualize \
--exclude "node_modules .git" \
--exclude-ext ".pyc .log"
```

## Basic Exports

### Exporting to Markdown

To export the current directory structure to Markdown:

```bash
recursivist export \
--format md
```

This creates a file named `structure.md` in the current directory.

### Exporting to Multiple Formats

To export to multiple formats at once:

```bash
recursivist export \
--format "txt md json"
```

### Exporting to a Specific Directory

To export to a different directory:

```bash
recursivist export \
--format html \
--output-dir ./docs
```

### Customizing the Filename

To use a custom filename prefix:

```bash
recursivist export \
--format json \
--prefix my-project
```

This creates a file named `my-project.json`.

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
recursivist compare dir1 dir2 \
--save
```

This creates a file named `comparison.html` in the current directory.

## Shell Completion

### Generating Shell Completion for Bash

```bash
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
