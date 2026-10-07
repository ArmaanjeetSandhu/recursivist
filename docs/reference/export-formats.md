# Export Formats

`recursivist export` writes a directory structure in six formats. This page shows exactly what each one produces; for how to run an export, choose an output location, or control what is included, see the [Export guide](../user-guide/export.md).

| `--format` | File written (default prefix) | Contents                                              |
| ---------- | ----------------------------- | ----------------------------------------------------- |
| `txt`      | `structure.txt`               | [Plain-text tree](#text-txt)                          |
| `json`     | `structure.json`              | [Structured data](#json-json)                         |
| `html`     | `structure.html`              | [Self-contained web page](#html-html)                 |
| `md`       | `structure.md`                | [Markdown nested list](#markdown-md)                  |
| `rst`      | `structure.rst`               | [reStructuredText nested list](#restructuredtext-rst) |
| `svg`      | `structure.svg`               | [Image of the terminal tree](#svg-svg)                |

Every format honors the filtering, depth, full-path, file-statistics, Git-status, icon-style, date-format, and size-format options. Exports use the `emoji` icon style unless `--icon-style nerd` is given, and write modification times as ISO 8601 in UTC unless [`--date-format relative`](../user-guide/sorting-and-statistics.md#date-format) is given. A directory that was not descended into because it is a [symbolic link back to an ancestor](../user-guide/visualization.md#symbolic-links) is marked `↩ (symlink loop)`, or carries a `symlink_loop` key in JSON.

The examples below all describe the same project, first as a plain export and then with `--sort-by-loc`.

## Text (`.txt`)

A plain-text tree with `├──` and `└──` connectors:

```
📂 my-project
├── 📄 README.md
├── 📄 setup.py
├── 📄 requirements.txt
└── 📂 src
    ├── 📄 main.py
    ├── 📄 utils.py
    └── 📂 tests
        ├── 📄 test_main.py
        └── 📄 test_utils.py
```

With statistics, each entry gains a parenthetical suffix:

```
📂 my-project (1262 lines)
├── 📄 README.md (124 lines)
├── 📄 setup.py (65 lines)
├── 📄 requirements.txt (18 lines)
└── 📂 src (1055 lines)
    ├── 📄 main.py (245 lines)
    ├── 📄 utils.py (157 lines)
    └── 📂 tests (653 lines)
        ├── 📄 test_main.py (412 lines)
        └── 📄 test_utils.py (241 lines)
```

## JSON (`.json`)

A structured representation. The payload has these top-level keys:

| Key                                                      | Value                                                                                     |
| -------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| `root`                                                   | Name of the exported directory                                                            |
| `structure`                                              | The tree: the root directory as an object, with its subdirectories nested inside it       |
| `sort_key`                                               | The active sort (`"loc"`, `"size"`, `"mtime"`, `"git_status"`, `"similarity"`), or `null` |
| `metric_order`                                           | The numeric metrics displayed, in display order                                           |
| `show_loc`, `show_size`, `show_mtime`, `show_git_status` | Whether each annotation was enabled                                                       |

Every directory, the root included, is an object with the same set of keys: its own files are listed under `files`, and its subdirectories are nested under `subdirectories`, keyed by name. A key that does not apply is left out, so a directory without subdirectories has no `subdirectories` key. Without detail flags, files collapse to bare names:

```json
{
    "root": "my-project",
    "structure": {
        "files": ["README.md", "setup.py", "requirements.txt"],
        "subdirectories": {
            "src": {
                "files": ["main.py", "utils.py"],
                "subdirectories": {
                    "tests": {
                        "files": ["test_main.py", "test_utils.py"]
                    }
                }
            }
        }
    },
    "sort_key": null,
    "metric_order": [],
    "show_loc": false,
    "show_size": false,
    "show_mtime": false,
    "show_git_status": false
}
```

With a detail flag (full path, LOC, size, mtime, or Git status), each file becomes an object carrying the requested fields, and directories gain aggregate totals:

```json
{
    "root": "my-project",
    "structure": {
        "files": [
            {
                "name": "README.md",
                "path": "README.md",
                "loc": 124
            },
            {
                "name": "setup.py",
                "path": "setup.py",
                "loc": 65
            },
            {
                "name": "requirements.txt",
                "path": "requirements.txt",
                "loc": 18
            }
        ],
        "loc": 1262,
        "subdirectories": {
            "src": {
                "files": [
                    {
                        "name": "main.py",
                        "path": "main.py",
                        "loc": 245
                    },
                    {
                        "name": "utils.py",
                        "path": "utils.py",
                        "loc": 157
                    }
                ],
                "loc": 1055,
                "subdirectories": {
                    "tests": {
                        "files": [
                            {
                                "name": "test_main.py",
                                "path": "test_main.py",
                                "loc": 412
                            },
                            {
                                "name": "test_utils.py",
                                "path": "test_utils.py",
                                "loc": 241
                            }
                        ],
                        "loc": 653
                    }
                }
            }
        }
    },
    "sort_key": "loc",
    "metric_order": ["loc"],
    "show_loc": true,
    "show_size": false,
    "show_mtime": false,
    "show_git_status": false
}
```

The fields that can appear:

| On a file                  | On a directory                         | Present with                                                                                                  |
| -------------------------- | -------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
|                            | `files`                                | A directory that has files                                                                                    |
|                            | `subdirectories`                       | A directory that has subdirectories                                                                           |
| `name`, `path`             |                                        | Any detail flag; `path` is the full path (or GitHub blob URL) with `--full-path`, and the file name otherwise |
| `loc`                      | `loc`                                  | `--loc` or `--sort-by-loc`                                                                                    |
| `size`, `size_formatted`   | `size`, `size_formatted`               | `--size` or `--sort-by-size`                                                                                  |
| `mtime`, `mtime_formatted` | `mtime`, `mtime_formatted`             | `--mtime` or `--sort-by-mtime`                                                                                |
| `git_status`               |                                        | `--git-status` or `--sort-by-git-status`, on files that have a status                                         |
|                            | `max_depth_reached`, `hidden_contents` | `--depth`, on a directory cut off by the limit (`hidden_contents` when it is not empty)                       |
|                            | `symlink_loop`                         | A directory that links back to an ancestor                                                                    |

Sizes are in bytes and modification times are Unix timestamps; the `_formatted` variants hold the human-readable text shown by the other formats. `mtime_formatted` follows `--date-format`, so it is an ISO 8601 time in UTC by default; `mtime` is the same number either way. Likewise `size_formatted` follows [`--size-format`](../user-guide/sorting-and-statistics.md#size-format), while `size` is always the number of bytes. A directory that was cut off by the depth limit or links back to an ancestor was not read, so it carries no totals. This format pairs well with [jq](https://jqlang.org) — see [Analyzing a Codebase with JSON](../recipes/json.md).

## HTML (`.html`)

A self-contained HTML document with an embedded stylesheet — no external assets required. It renders the structure as a nested list with:

- Extension-based color coding for files
- Bold directory names
- Metric annotations when statistics are enabled
- Git-status badges when `--git-status` is used

The document pins a white background, and every extension color is darkened as needed until all text meets the WCAG 2.1 level AAA contrast ratio (7:1) for normal-sized text. Hues are preserved: extensions stay visually distinct, and each one keeps the hue it has in the terminal tree.

Open it in any browser, or embed it in documentation. The output is a static page.

## Markdown (`.md`)

A nested bullet list that renders cleanly on GitHub and other Markdown viewers, with directories in bold and files as inline code:

```markdown
# 📂 my-project

- 📄 `README.md`
- 📄 `setup.py`
- 📄 `requirements.txt`
- 📂 **src**
    - 📄 `main.py`
    - 📄 `utils.py`
    - 📂 **tests**
        - 📄 `test_main.py`
        - 📄 `test_utils.py`
```

With statistics:

```markdown
# 📂 my-project (1262 lines)

- 📄 `README.md` (124 lines)
- 📄 `setup.py` (65 lines)
- 📄 `requirements.txt` (18 lines)
- 📂 **src** (1055 lines)
    - 📄 `main.py` (245 lines)
    - 📄 `utils.py` (157 lines)
    - 📂 **tests** (653 lines)
        - 📄 `test_main.py` (412 lines)
        - 📄 `test_utils.py` (241 lines)
```

## reStructuredText (`.rst`)

A nested bullet list that renders cleanly with [docutils](https://docutils.sourceforge.io/) and [Sphinx](https://www.sphinx-doc.org/), the reStructuredText counterpart to the Markdown export. The root becomes a section title, directories are shown in bold, and files as inline literals:

```rst
📂 my-project
=============

- 📄 ``README.md``
- 📄 ``setup.py``
- 📄 ``requirements.txt``
- 📂 **src**

  - 📄 ``main.py``
  - 📄 ``utils.py``
  - 📂 **tests**

    - 📄 ``test_main.py``
    - 📄 ``test_utils.py``
```

With statistics:

```rst
📂 my-project (1262 lines)
==========================

- 📄 ``README.md`` (124 lines)
- 📄 ``setup.py`` (65 lines)
- 📄 ``requirements.txt`` (18 lines)
- 📂 **src** (1055 lines)

  - 📄 ``main.py`` (245 lines)
  - 📄 ``utils.py`` (157 lines)
  - 📂 **tests** (653 lines)

    - 📄 ``test_main.py`` (412 lines)
    - 📄 ``test_utils.py`` (241 lines)
```

The section-title underline is sized to the title's display width, which keeps emoji icons from triggering a "Title underline too short" warning. Directory names have rST markup characters escaped, and Git status is shown with bold `[U]`/`[M]`/`[A]`/`[D]` badges (reStructuredText has no standard strike-through; deleted files carry the `[D]` badge instead). Drop the file straight into a Sphinx project or include it with the [`.. include::`](https://docutils.sourceforge.io/docs/ref/rst/directives.html#include) directive.

## SVG (`.svg`)

A scalable vector image of the tree exactly as it appears in the terminal, preserving the `rich` colors, icons, and connectors. Ideal for embedding a styled directory tree in a README without a screenshot.

The image is drawn as a terminal window titled with the directory's name, on a canvas that is always 120 columns wide, whatever the size of the tree. With `--sort-by-loc`, the example project looks like this:

<div class="terminal-demo">
  <div class="terminal-header">
    <div class="terminal-buttons">
      <div class="terminal-button red"></div>
      <div class="terminal-button yellow"></div>
      <div class="terminal-button green"></div>
    </div>
    <div class="terminal-title">Directory Structure - my-project</div>
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
