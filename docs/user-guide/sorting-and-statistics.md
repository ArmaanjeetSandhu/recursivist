# Sorting and Statistics

`visualize`, `export`, and `compare` can annotate every file with its lines of code, size, modification time, or Git status, and can order files by any of them. The flags on this page behave the same way in all three commands.

## Sorting and Display Are Separate

Recursivist keeps two things separate: **how files are ordered** and **what each file is annotated with**. That gives three families of flags:

- **Combined** — `--sort-by-loc`, `--sort-by-size`, `--sort-by-mtime`, and `--sort-by-git-status` each sort files by a metric _and_ annotate every file with it.
- **Display-only** — `--loc`, `--size`, `--mtime`, and `--git-status` annotate files without touching the order.
- **Sorting-only** — `--sort-by-similarity` reorders without annotating.

A combined flag is the quickest way to see one metric. To sort by one metric while showing others, see [Combining Statistics](#combining-statistics).

## Lines of Code

Count lines per file and total them per directory, largest first:

```bash
recursivist visualize --sort-by-loc
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
      <pre>📂 my-project (1262 lines)
├── <span style="color: #f1fa8c;">📄 README.md</span> (124 lines)
├── <span style="color: #83e43d;">📄 setup.py</span> (65 lines)
├── <span style="color: #bd93f9;">📄 requirements.txt</span> (18 lines)
└── 📂 src (1055 lines)
    ├── <span style="color: #83e43d;">📄 main.py</span> (245 lines)
    ├── <span style="color: #83e43d;">📄 utils.py</span> (157 lines)
    └── 📂 tests (653 lines)
        ├── <span style="color: #83e43d;">📄 test_main.py</span> (412 lines)
        └── <span style="color: #83e43d;">📄 test_utils.py</span> (241 lines)</pre>
    </div>
  </div>
</div>

Every line of a text file is counted, blank lines and comments included. Files are read as UTF-8, and UTF-16 files are recognized; a file that is empty, binary, or unreadable counts as 0 lines. A directory's figure is the total of the files shown beneath it, so files left out by a filter or a depth limit are not counted.

## File Sizes

Display sizes with units (B, KB, MB, GB), largest first:

```bash
recursivist visualize --sort-by-size
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
      <pre>📂 my-project (57.1 KB)
├── <span style="color: #f1fa8c;">📄 README.md</span> (4.2 KB)
├── <span style="color: #83e43d;">📄 setup.py</span> (3.8 KB)
├── <span style="color: #bd93f9;">📄 requirements.txt</span> (512 B)
└── 📂 src (48.6 KB)
    ├── <span style="color: #83e43d;">📄 main.py</span> (12.4 KB)
    ├── <span style="color: #83e43d;">📄 utils.py</span> (8.2 KB)
    └── 📂 tests (28.0 KB)
        ├── <span style="color: #83e43d;">📄 test_main.py</span> (18.6 KB)
        └── <span style="color: #83e43d;">📄 test_utils.py</span> (9.4 KB)</pre>
    </div>
  </div>
</div>

## Modification Times

Show when files were last modified, newest first, with recency-aware formatting (`Today HH:MM`, `Yesterday HH:MM`, a weekday and time within the last week, `Mon DD` earlier this year, or `YYYY-MM-DD` for older files). A directory shows the time of its most recently modified file:

```bash
recursivist visualize --sort-by-mtime
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
      <pre>📂 my-project (Today 14:30)
├── <span style="color: #f1fa8c;">📄 README.md</span> (Today 10:15)
├── <span style="color: #83e43d;">📄 setup.py</span> (Today 09:00)
├── <span style="color: #bd93f9;">📄 requirements.txt</span> (Yesterday 16:00)
└── 📂 src (Today 14:30)
    ├── <span style="color: #83e43d;">📄 main.py</span> (Today 14:30)
    ├── <span style="color: #83e43d;">📄 utils.py</span> (Today 09:15)
    └── 📂 tests (Today 14:25)
        ├── <span style="color: #83e43d;">📄 test_main.py</span> (Today 14:25)
        └── <span style="color: #83e43d;">📄 test_utils.py</span> (Yesterday 18:10)</pre>
    </div>
  </div>
</div>

## Displaying Without Sorting

Use the display-only flags — `--loc`, `--size`, `--mtime` — to annotate files while keeping the default extension-and-name ordering:

```bash
recursivist visualize --size          # show sizes, don't reorder
recursivist visualize --loc --mtime   # show LOC and mtime, don't reorder
```

Display-only annotations appear in the exact order you list the flags, so `--loc --mtime` and `--mtime --loc` differ only in column order.

## Combining Statistics

You can sort by one metric and annotate with several. Pair a single sorting flag with as many display-only flags as you like:

```bash
recursivist visualize --sort-by-loc --size --mtime
```

<div class="terminal-demo compact">
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
      <pre>📂 my-project (1262 lines, 57.1 KB, Today 14:30)
├── <span style="color: #f1fa8c;">📄 README.md</span> (124 lines, 4.2 KB, Today 10:15)
├── <span style="color: #83e43d;">📄 setup.py</span> (65 lines, 3.8 KB, Today 09:00)
├── <span style="color: #bd93f9;">📄 requirements.txt</span> (18 lines, 512 B, Yesterday 16:00)
└── 📂 src (1055 lines, 48.6 KB, Today 14:30)
    ├── <span style="color: #83e43d;">📄 main.py</span> (245 lines, 12.4 KB, Today 14:30)
    ├── <span style="color: #83e43d;">📄 utils.py</span> (157 lines, 8.2 KB, Today 09:15)
    └── 📂 tests (653 lines, 28.0 KB, Today 14:25)
        ├── <span style="color: #83e43d;">📄 test_main.py</span> (412 lines, 18.6 KB, Today 14:25)
        └── <span style="color: #83e43d;">📄 test_utils.py</span> (241 lines, 9.4 KB, Yesterday 18:10)</pre>
    </div>
  </div>
</div>

Here files are ordered by lines of code, and each is annotated with LOC, size, and modification time.

Flags are resolved by their **left-to-right order on the command line**:

- Only the **first** sorting flag takes effect. A later `--sort-by-*` is discarded entirely — so `--sort-by-loc --sort-by-size` sorts by LOC and shows only LOC, _not_ both. Use `--sort-by-loc --size` to sort by LOC and display size too.
- The winning sort metric is annotated first; display-only annotations follow in the order given.

The [CLI Reference](../reference/cli-reference.md#sorting-and-display-flags) has the complete resolution rules.

## Grouping by Name Similarity

Instead of ordering files by extension and then name, group files with similar names next to each other:

```bash
recursivist visualize --sort-by-similarity
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
      <pre>📂 project
├── <span style="color: #8be9fd;">📄 main.js</span>
├── <span style="color: #83e43d;">📄 main.py</span>
├── <span style="color: #83e43d;">📄 test_api.py</span>
├── <span style="color: #8be9fd;">📄 test_api.js</span>
└── <span style="color: #f1fa8c;">📄 README.md</span></pre>
    </div>
  </div>
</div>

`--sort-by-similarity` is a sorting flag like the others, so it takes effect only when it comes before any other `--sort-by-*` flag on the command line.

## Git Status

Inside a Git repository, annotate files with their status:

```bash
recursivist visualize --git-status
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
├── <span style="color: #bd93f9;">📄 newfile.txt</span> <span style="color: #8b949e;">[U]</span>
└── 📂 src
    ├── <span style="color: #83e43d;">📄 main.py</span>
    └── <span style="color: #83e43d;">📄 utils.py</span> <span style="color: #e3b341;">[M]</span></pre>
    </div>
  </div>
</div>

Markers are `[U]` untracked, `[M]` modified, `[A]` added, and `[D]` deleted. Deleted files are also shown struck through, and a file deleted from disk is still listed so the change is visible. If the directory isn't inside a repository (or has no changes), no markers are added.

`--git-status` is display-only. To also **sort** by Git status (modified, added, deleted, untracked, then clean), use the combined flag:

```bash
recursivist visualize --sort-by-git-status
```

The Git-status marker always trails at the very end of a file's annotations, after any metric parenthetical. For example, `--sort-by-loc --git-status` shows `main.py (245 lines) [M]`.

## In Exports and Comparisons

Every flag above works with `export` and `compare`:

```bash
recursivist export --format md --sort-by-loc --size   # sort by LOC, show LOC and size
recursivist export --format json --mtime              # show mtime, keep default order
recursivist compare dir1 dir2 --sort-by-size
recursivist compare dir1 dir2 --git-status
```

- Each export format writes the annotations in its own way; [Export Formats](../reference/export-formats.md) shows them.
- In `compare`, the legend notes which metrics and ordering are active, and Git status is read independently for each directory, so both sides are annotated correctly even when they belong to different repositories.
- For a GitHub repository URL, lines of code and size apply, while the Git-status and modification-time flags are skipped. See [GitHub Repositories](github-repositories.md#which-options-apply).
