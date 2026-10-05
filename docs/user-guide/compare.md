# Compare

The `compare` command shows two directory structures side by side and highlights the differences between them.

## Basic Comparison

```bash
recursivist compare dir1 dir2
```

Each input must be an existing directory or a [GitHub repository URL](github-repositories.md#comparing-with-a-github-repository). A legend is printed first, followed by the two trees in labeled panels:

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
    <div class="terminal-output boxed">
      <div class="terminal-panel dim"><span style="font-weight: bold;">Legend:</span> <span style="background: #238636; color: #ffffff;">Green</span> = In this directory, <span style="background: #b62324; color: #ffffff;">Red</span> = In the other directory</div>
      <div class="terminal-panels">
        <div class="terminal-panel blue">
          <div class="terminal-panel-title">Directory 1: project-v1</div>
          <pre><span style="font-weight: bold;">📂 project-v1</span>
├── 📄 README.md
├── <span class="terminal-mark green">📄 setup.py</span>
├── 📄 requirements.txt
├── 📂 src
│   ├── 📄 main.py
│   ├── 📄 utils.py
│   └── 📂 tests
│       ├── 📄 test_main.py
│       └── <span class="terminal-mark green">📄 test_utils.py</span>
├── <span class="terminal-mark red">📄 pyproject.toml</span>
└── <span style="color: #ff7b72;">📂 docs</span>
    └── <span class="terminal-mark red">📄 index.md</span></pre>
        </div>
        <div class="terminal-panel green">
          <div class="terminal-panel-title">Directory 2: project-v2</div>
          <pre><span style="font-weight: bold;">📂 project-v2</span>
├── 📄 README.md
├── <span class="terminal-mark green">📄 pyproject.toml</span>
├── 📄 requirements.txt
├── <span style="color: #4ade80;">📂 docs</span>
│   └── <span class="terminal-mark green">📄 index.md</span>
├── 📂 src
│   ├── 📄 main.py
│   ├── 📄 utils.py
│   └── 📂 tests
│       ├── 📄 test_main.py
│       └── <span class="terminal-mark red">📄 test_utils.py</span>
└── <span class="terminal-mark red">📄 setup.py</span></pre>
        </div>
      </div>
    </div>
  </div>
</div>

## Reading the Output

Each panel lists everything found on **either** side, and colors are relative to the panel they appear in:

- Items present in both directories are shown normally.
- Items found only in **that panel's** directory are highlighted in **green**.
- Items found only in the **other** directory are highlighted in **red**, and are listed after the panel's own entries.

In the example above, `project-v2` replaced `setup.py` with `pyproject.toml`, added a `docs` directory, and dropped `test_utils.py`. So `setup.py` and `test_utils.py` are green on the left and red on the right, while `pyproject.toml` and `docs` are red on the left and green on the right. Files are highlighted with a colored background and directories with colored text; file names are not colored by extension here, so that the differences stand out.

The legend also notes any active options, such as metric display, sorting, depth limits, or full paths. Include and exclude patterns are listed in a separate "Applied Patterns" panel.

## Saving as HTML

By default the comparison is printed to the terminal. Save it as a self-contained, two-column HTML document instead with `--save`:

```bash
recursivist compare dir1 dir2 --save
```

This writes `comparison.html` to the current directory. Change the location or filename:

```bash
recursivist compare dir1 dir2 --save --output-dir ./reports --prefix project-diff
```

The document contains the same side-by-side comparison, highlighting, and legend as the terminal view, which makes it convenient for sharing results or keeping a record of structural changes. It uses the `emoji` icon style by default for cross-platform consistency; override it with `--icon-style nerd`.

!!! note

    In `compare`, `-f` is shorthand for `--save`, not for `--format` as it is in `export`.

## Controlling What Is Compared

`compare` takes the same options as `visualize`, and applies them to both directories:

```bash
recursivist compare dir1 dir2 --exclude node_modules --exclude .git
recursivist compare dir1 dir2 --include-pattern "*.py" --include-pattern "*.md"
recursivist compare dir1 dir2 --ignore-file .gitignore
recursivist compare dir1 dir2 --depth 3
recursivist compare dir1 dir2 --sort-by-loc --size
recursivist compare dir1 dir2 --git-status
```

- **Filtering**: see [Pattern Filtering](pattern-filtering.md).
- **Depth and full paths**: see [Visualization](visualization.md#directory-depth-control).
- **Lines of code, sizes, modification times, and Git status**: see [Sorting and Statistics](sorting-and-statistics.md). Metrics surface differences beyond structure — for example, which files grew or were modified more recently. Git status is read independently for each directory, so both sides are annotated correctly even when they belong to different repositories.
- **Saved and project settings**: `compare` uses the project configuration of the first local directory given. See [Configuration](configuration.md#how-commands-use-settings).

## Comparing with a GitHub Repository

Either input may be a GitHub repository URL:

```bash
recursivist compare ./my-fork https://github.com/owner/repo
recursivist compare https://github.com/owner/repo/tree/main https://github.com/owner/repo/tree/develop
```

Some options are skipped for a GitHub side. [GitHub Repositories](github-repositories.md#comparing-with-a-github-repository) explains which, and how a mixed local-and-GitHub comparison behaves.

## Terminal Compatibility

The side-by-side terminal view is best in a terminal with Unicode and ANSI color support and enough width to fit both panels. On narrow terminals, prefer the HTML export (`--save`).

For worked examples — comparing versions, branches, builds, and backups — see the [comparison recipes](../recipes/comparisons.md).
