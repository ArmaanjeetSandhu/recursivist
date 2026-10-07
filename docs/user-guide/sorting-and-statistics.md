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

Display sizes with units (B, KiB, MiB, GiB), largest first. A directory shows the total size of the files beneath it:

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
      <pre>📂 my-project (57.1 KiB)
├── <span style="color: #f1fa8c;">📄 README.md</span> (4.2 KiB)
├── <span style="color: #83e43d;">📄 setup.py</span> (3.8 KiB)
├── <span style="color: #bd93f9;">📄 requirements.txt</span> (512 B)
└── 📂 src (48.6 KiB)
    ├── <span style="color: #83e43d;">📄 main.py</span> (12.4 KiB)
    ├── <span style="color: #83e43d;">📄 utils.py</span> (8.2 KiB)
    └── 📂 tests (28.0 KiB)
        ├── <span style="color: #83e43d;">📄 test_main.py</span> (18.6 KiB)
        └── <span style="color: #83e43d;">📄 test_utils.py</span> (9.4 KiB)</pre>
    </div>
  </div>
</div>

### Size Format

A size is written in one of two formats, chosen with `--size-format`:

| Format | Example   | Units         | Description                                                   |
| ------ | --------- | ------------- | ------------------------------------------------------------- |
| `iec`  | `4.2 MiB` | KiB, MiB, GiB | Binary units, each 1024 times the one before it (the default) |
| `si`   | `4.4 MB`  | kB, MB, GB    | Decimal units, each 1000 times the one before it              |

Both examples are the same file of 4,400,000 bytes. In either format, a size below the first unit is written as a whole number of bytes (`512 B`), and anything larger with one decimal place.

```bash
recursivist visualize --sort-by-size --size-format si
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
      <pre>📂 my-project (58.5 kB)
├── <span style="color: #f1fa8c;">📄 README.md</span> (4.3 kB)
├── <span style="color: #83e43d;">📄 setup.py</span> (3.9 kB)
├── <span style="color: #bd93f9;">📄 requirements.txt</span> (512 B)
└── 📂 src (49.8 kB)
    ├── <span style="color: #83e43d;">📄 main.py</span> (12.7 kB)
    ├── <span style="color: #83e43d;">📄 utils.py</span> (8.4 kB)
    └── 📂 tests (28.7 kB)
        ├── <span style="color: #83e43d;">📄 test_main.py</span> (19.0 kB)
        └── <span style="color: #83e43d;">📄 test_utils.py</span> (9.6 kB)</pre>
    </div>
  </div>
</div>

The default is `iec` everywhere: in `visualize`, in `export`, and in `compare`, in the terminal and saved with `--save`. To change the format for every run, save it as the `size-format` [setting](configuration.md#settings), which applies to all of them:

```bash
recursivist config set size-format si
```

The option only changes _how_ a size is written, not the order files are sorted in. It has no effect unless `--size` or `--sort-by-size` is given.

## Modification Times

Show when files were last modified, newest first. A directory shows the time of its most recently modified file:

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

### Date Format

A modification time is written in one of two formats, chosen with `--date-format`:

| Format     | Example                | Description                                                                                                                                                                                    |
| ---------- | ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `relative` | `Today 14:30`          | Recency-aware, in your local time: `Today HH:MM`, `Yesterday HH:MM`, a weekday and time within the last week, `Mon DD` earlier this year, or `YYYY-MM-DD` for older and for future-dated files |
| `iso`      | `2026-10-07T12:30:41Z` | ISO 8601, in UTC, to the second                                                                                                                                                                |

Both examples are the same moment, on a machine two hours ahead of UTC: the `relative` form is in local time and drops the seconds.

```bash
recursivist visualize --sort-by-mtime --date-format iso
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
      <pre>📂 my-project (2026-10-07T12:30:41Z)
├── <span style="color: #f1fa8c;">📄 README.md</span> (2026-10-07T08:15:02Z)
├── <span style="color: #83e43d;">📄 setup.py</span> (2026-10-07T07:00:19Z)
├── <span style="color: #bd93f9;">📄 requirements.txt</span> (2026-10-06T14:00:55Z)
└── 📂 src (2026-10-07T12:30:41Z)
    ├── <span style="color: #83e43d;">📄 main.py</span> (2026-10-07T12:30:41Z)
    ├── <span style="color: #83e43d;">📄 utils.py</span> (2026-10-07T07:15:33Z)
    └── 📂 tests (2026-10-07T12:25:07Z)
        ├── <span style="color: #83e43d;">📄 test_main.py</span> (2026-10-07T12:25:07Z)
        └── <span style="color: #83e43d;">📄 test_utils.py</span> (2026-10-06T16:10:48Z)</pre>
    </div>
  </div>
</div>

The default depends on where the times end up:

| Output                                 | Default    |
| -------------------------------------- | ---------- |
| `visualize`                            | `relative` |
| `compare` in the terminal              | `relative` |
| `export`, in every format              | `iso`      |
| `compare --save` (the comparison HTML) | `iso`      |

A relative time is read at a glance in the terminal, but `Today 14:30` stops being true once a file is read on another day, which is why everything written to a file defaults to `iso`. `--date-format` overrides the default of any command. To change the format used in the terminal for every run, save it as the `date-format` [setting](configuration.md#settings):

```bash
recursivist config set date-format iso
```

The option only changes _how_ a time is written. It has no effect unless `--mtime` or `--sort-by-mtime` is given.

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
      <pre>📂 my-project (1262 lines, 57.1 KiB, Today 14:30)
├── <span style="color: #f1fa8c;">📄 README.md</span> (124 lines, 4.2 KiB, Today 10:15)
├── <span style="color: #83e43d;">📄 setup.py</span> (65 lines, 3.8 KiB, Today 09:00)
├── <span style="color: #bd93f9;">📄 requirements.txt</span> (18 lines, 512 B, Yesterday 16:00)
└── 📂 src (1055 lines, 48.6 KiB, Today 14:30)
    ├── <span style="color: #83e43d;">📄 main.py</span> (245 lines, 12.4 KiB, Today 14:30)
    ├── <span style="color: #83e43d;">📄 utils.py</span> (157 lines, 8.2 KiB, Today 09:15)
    └── 📂 tests (653 lines, 28.0 KiB, Today 14:25)
        ├── <span style="color: #83e43d;">📄 test_main.py</span> (412 lines, 18.6 KiB, Today 14:25)
        └── <span style="color: #83e43d;">📄 test_utils.py</span> (241 lines, 9.4 KiB, Yesterday 18:10)</pre>
    </div>
  </div>
</div>

Here files are ordered by lines of code, and each is annotated with LOC, size, and modification time.

Flags are resolved by their **left-to-right order on the command line**:

- Only the **first** sorting flag takes effect. A later `--sort-by-*` is discarded entirely: `--sort-by-loc --sort-by-size` sorts by LOC and shows only LOC, _not_ both. Use `--sort-by-loc --size` to sort by LOC and display size too.
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

Markers are `[U]` untracked, `[M]` modified, `[A]` added, and `[D]` deleted. Deleted files are also shown struck through, and a file deleted from disk is still listed to keep the change visible, along with its directory if that is gone too. A directory with no changes gets no markers.

When Git status can't be read (because the directory isn't inside a repository, `git` isn't installed, or Git reports an error), a warning naming the cause is logged and the tree is shown without markers.

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
- Exports, and a comparison saved with `--save`, write modification times in the `iso` [date format](#date-format) unless `--date-format relative` is given.
- Sizes are written in the `iec` [size format](#size-format) in every output unless `--size-format si` is given or the `size-format` setting says otherwise.
- In `compare`, the legend notes which metrics and ordering are active, and Git status is read independently for each directory. This way, both sides are annotated correctly even when they belong to different repositories.
- In `compare`, two files of the same name are highlighted as different when their annotations read differently. With `--mtime`, that follows the date format: `iso` tells apart files modified a second apart, while `relative` only tells them apart when the coarser text differs. With `--size`, it follows the size format in the same way: two sizes that round to the same text in one format can differ in the other.
- For a GitHub repository URL, lines of code and size apply, while the Git-status and modification-time flags are skipped. See [GitHub Repositories](github-repositories.md#which-options-apply).
