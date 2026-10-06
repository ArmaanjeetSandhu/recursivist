# Visualization

The `visualize` command renders a directory structure as a color-coded tree in the terminal. This guide covers its display options, which `export` and `compare` share.

## Basic Visualization

```bash
recursivist visualize                  # current directory
recursivist visualize /path/to/project # a specific directory
```

A progress indicator is shown while the directory is scanned, then the tree is printed, with each file type in its own color:

<div class="terminal-demo">
  <div class="terminal-header">
    <div class="terminal-buttons">
      <div class="terminal-button red"></div>
      <div class="terminal-button yellow"></div>
      <div class="terminal-button green"></div>
    </div>
    <div class="terminal-title">recursivist-demo ~ bash</div>
  </div>
  <div class="terminal-body">
    <div class="terminal-output">
      <pre>📂 my-project
├── <span style="color: #f1fa8c;">📄 README.md</span>
├── <span style="color: #83e43d;">📄 setup.py</span>
├── <span style="color: #bd93f9;">📄 requirements.txt</span>
└── 📂 src
    ├── <span style="color: #83e43d;">📄 main.py</span>
    ├── <span style="color: #83e43d;">📄 utils.py</span>
    └── 📂 tests
        ├── <span style="color: #83e43d;">📄 test_main.py</span>
        └── <span style="color: #83e43d;">📄 test_utils.py</span></pre>
    </div>
  </div>
</div>

Within each directory, files appear before subdirectories. Files are ordered by extension and then name; [Sorting and Statistics](sorting-and-statistics.md) covers the other orderings and the metrics each file can be annotated with.

## Color Coding

Each file extension is assigned its own color. A color starts from a hash of the extension and is then spaced apart from the colors of the other extensions in the tree to keep different types visually distinct.

Colors are deterministic: a given set of file types always produces the same colors. A directory is colored the same way on every run, and the SVG and HTML exports use the same colors as the terminal (the HTML export darkens them for contrast on its white page). Because colors are spaced relative to one another, an extension's color can differ between directories that contain different mixes of file types.

## Icon Styles

Recursivist ships with two icon styles:

- **`emoji`** (default): the generic 📄, 📂, and 📁 glyphs, which render in virtually any terminal.
- **`nerd`**: file-type-specific [Nerd Font](https://www.nerdfonts.com/) glyphs (a distinct icon for Python, JavaScript, folders like `.git` or `node_modules`, and so on). This requires a Nerd Font installed and selected in your terminal; without one, the glyphs appear as boxes or question marks.

Choose a style for a single run with `--icon-style`:

```bash
recursivist visualize --icon-style nerd
```

To make a style the default, save it as a preference or set it for a project:

```bash
recursivist config set icon-style nerd
```

See [Configuration](configuration.md) for how saved and project settings work. Exported files (and a comparison saved as HTML) use the `emoji` style regardless of your configuration, so that they render consistently on any machine; pass `--icon-style nerd` to override this.

## Directory Depth Control

Limit how deep the tree goes — useful for large projects:

```bash
recursivist visualize --depth 2
```

<div class="terminal-demo">
  <div class="terminal-header">
    <div class="terminal-buttons">
      <div class="terminal-button red"></div>
      <div class="terminal-button yellow"></div>
      <div class="terminal-button green"></div>
    </div>
    <div class="terminal-title">recursivist-demo ~ bash</div>
  </div>
  <div class="terminal-body">
    <div class="terminal-output">
      <pre>📂 my-project
├── <span style="color: #f1fa8c;">📄 README.md</span>
└── 📂 src
    ├── <span style="color: #83e43d;">📄 main.py</span>
    ├── <span style="color: #83e43d;">📄 utils.py</span>
    └── 📂 tests</pre>
    </div>
  </div>
</div>

Subtrees cut off by the limit are left unexpanded. Their folder icon still distinguishes the two cases: 📂 means contents were hidden by the limit (as for `tests` above), while 📁 means the directory is genuinely empty.

## Full Path Display

Show absolute paths instead of bare filenames:

```bash
recursivist visualize --full-path
```

<div class="terminal-demo">
  <div class="terminal-header">
    <div class="terminal-buttons">
      <div class="terminal-button red"></div>
      <div class="terminal-button yellow"></div>
      <div class="terminal-button green"></div>
    </div>
    <div class="terminal-title">recursivist-demo ~ bash</div>
  </div>
  <div class="terminal-body">
    <div class="terminal-output">
      <pre>📂 my-project
├── <span style="color: #f1fa8c;">📄 /home/user/my-project/README.md</span>
└── 📂 src
    └── <span style="color: #83e43d;">📄 /home/user/my-project/src/main.py</span></pre>
    </div>
  </div>
</div>

For a [GitHub repository](github-repositories.md), `--full-path` shows each file's canonical blob URL instead of a filesystem path.

## Symbolic Links

A symbolic link to a directory is followed and listed like any other directory, and a link to a file is listed as a file. A link that leads back to one of its own ancestors is not descended into again; it is shown with a marker instead, and a warning names the link:

<div class="terminal-demo">
  <div class="terminal-header">
    <div class="terminal-buttons">
      <div class="terminal-button red"></div>
      <div class="terminal-button yellow"></div>
      <div class="terminal-button green"></div>
    </div>
    <div class="terminal-title">recursivist-demo ~ bash</div>
  </div>
  <div class="terminal-body">
    <div class="terminal-output">
      <pre>📂 my-project
└── 📂 latest
    └── <span style="color: #8b949e;">↩ (symlink loop)</span></pre>
    </div>
  </div>
</div>

## Filtering

All of Recursivist's filtering options apply to `visualize`:

```bash
recursivist visualize --exclude node_modules --exclude .git
recursivist visualize --include-pattern "*.py" --include-pattern "*.md"
recursivist visualize --ignore-file .gitignore
```

See [Pattern Filtering](pattern-filtering.md) for each mechanism and how they combine.

## Performance Tips

For very large directories:

1. Limit depth with `--depth`.
2. Exclude heavy directories (`node_modules`, `.git`, build output) with `--exclude`.
3. Use include patterns to focus on the part of the tree you care about.
4. Be aware that `--loc` and `--sort-by-loc` read every file to count lines, which is slower on large repositories.

## Related Guides

- [Sorting and Statistics](sorting-and-statistics.md): order files and annotate them with metrics or Git status
- [Export](export.md): save structures to files
- [Compare](compare.md): diff two directories

For every option, see the [CLI Reference](../reference/cli-reference.md).
