# Export Formats

Recursivist exports directory structures to six formats. This page describes each one in detail. For task-oriented examples, see [Export Examples](../examples/export.md).

## Available Formats

| Format   | Extension | Description                       | Best For                              |
| -------- | --------- | --------------------------------- | ------------------------------------- |
| Text     | `.txt`    | Plain ASCII tree                  | Quick reference, text-only contexts   |
| JSON     | `.json`   | Structured data                   | Programmatic processing, integrations |
| HTML     | `.html`   | Self-contained styled web page    | Sharing, web documentation            |
| Markdown | `.md`     | GitHub-compatible nested list     | READMEs, project documentation        |
| SVG      | `.svg`    | Vector image of the terminal tree | Embedding visuals in docs and READMEs |
| reStructuredText | `.rst` | Sphinx-compatible nested list  | Sphinx/docutils documentation         |

## Basic Usage

```bash
recursivist export --format FORMAT
```

`FORMAT` is one of `txt`, `json`, `html`, `md`, `svg`, or `rst`. Markdown is used when `--format` is omitted. Multiple formats can be requested at once:

```bash
recursivist export --format "txt json html md svg rst"
```

Outputs are written to the current directory with the prefix `structure` unless `--output-dir` and `--prefix` say otherwise. Every format honors the filtering, depth, full-path, file-statistics, Git-status, and icon-style options. Exports use the `emoji` icon style by default for cross-platform consistency.

## Text (`.txt`)

A plain ASCII tree with `├──` and `└──` connectors:

```
📁 my-project
├── 📄 README.md
├── 📄 setup.py
├── 📄 requirements.txt
└── 📁 src
    ├── 📄 main.py
    ├── 📄 utils.py
    └── 📁 tests
        ├── 📄 test_main.py
        └── 📄 test_utils.py
```

With statistics, each entry gains a parenthetical suffix:

```
📁 my-project (1262 lines)
├── 📄 README.md (124 lines)
├── 📄 setup.py (65 lines)
├── 📄 requirements.txt (18 lines)
└── 📁 src (1055 lines)
    ├── 📄 main.py (245 lines)
    ├── 📄 utils.py (157 lines)
    └── 📁 tests (653 lines)
        ├── 📄 test_main.py (412 lines)
        └── 📄 test_utils.py (241 lines)
```

## JSON (`.json`)

A structured representation. The payload records the root name, the structure, and which detail flags were active. Without detail flags, files collapse to bare names:

```json
{
  "root": "my-project",
  "structure": {
    "_files": ["README.md", "setup.py", "requirements.txt"],
    "src": {
      "_files": ["main.py", "utils.py"],
      "tests": {
        "_files": ["test_main.py", "test_utils.py"]
      }
    }
  },
  "show_loc": false,
  "show_size": false,
  "show_mtime": false,
  "show_git_status": false
}
```

With a detail flag (full path, LOC, size, mtime, or Git status), each file becomes an object and directories carry aggregate totals:

```json
{
  "root": "my-project",
  "structure": {
    "_loc": 1262,
    "_files": [
      { "name": "README.md", "path": "README.md", "loc": 124 },
      { "name": "setup.py", "path": "setup.py", "loc": 65 },
      { "name": "requirements.txt", "path": "requirements.txt", "loc": 18 }
    ],
    "src": {
      "_loc": 1055,
      "_files": [
        { "name": "main.py", "path": "main.py", "loc": 245 },
        { "name": "utils.py", "path": "utils.py", "loc": 157 }
      ],
      "tests": {
        "_loc": 653,
        "_files": [
          { "name": "test_main.py", "path": "test_main.py", "loc": 412 },
          { "name": "test_utils.py", "path": "test_utils.py", "loc": 241 }
        ]
      }
    }
  },
  "show_loc": true,
  "show_size": false,
  "show_mtime": false,
  "show_git_status": false
}
```

Size and mtime fields are accompanied by human-readable variants (`size_formatted`, `mtime_formatted`), and the same applies to the directory aggregates (`_size_formatted`, `_mtime_formatted`). This format pairs well with [jq](https://jqlang.org).

## HTML (`.html`)

A self-contained HTML document with an embedded stylesheet — no external assets required. It renders the structure as a nested list with:

- Extension-based color coding for files
- Bold directory names
- Metric annotations when statistics are enabled
- Git-status badges when `--git-status` is used

Open it in any browser, or embed it in documentation. The output is a static page.

## Markdown (`.md`)

A nested bullet list that renders cleanly on GitHub and other Markdown viewers, with directories in bold and files as inline code:

```markdown
# 📁 my-project

- 📄 `README.md`
- 📄 `setup.py`
- 📄 `requirements.txt`
- 📁 **src**
  - 📄 `main.py`
  - 📄 `utils.py`
  - 📁 **tests**
    - 📄 `test_main.py`
    - 📄 `test_utils.py`
```

With statistics:

```markdown
# 📁 my-project (1262 lines)

- 📄 `README.md` (124 lines)
- 📄 `setup.py` (65 lines)
- 📄 `requirements.txt` (18 lines)
- 📁 **src** (1055 lines)
  - 📄 `main.py` (245 lines)
  - 📄 `utils.py` (157 lines)
  - 📁 **tests** (653 lines)
    - 📄 `test_main.py` (412 lines)
    - 📄 `test_utils.py` (241 lines)
```

## reStructuredText (`.rst`)

A nested bullet list that renders cleanly with [docutils](https://docutils.sourceforge.io/) and [Sphinx](https://www.sphinx-doc.org/), the reStructuredText counterpart to the Markdown export. The root becomes a section title, directories are shown in bold, and files as inline literals:

```rst
📁 my-project
=============

- 📄 ``README.md``
- 📄 ``setup.py``
- 📄 ``requirements.txt``
- 📁 **src**

  - 📄 ``main.py``
  - 📄 ``utils.py``
  - 📁 **tests**

    - 📄 ``test_main.py``
    - 📄 ``test_utils.py``
```

With statistics:

```rst
📁 my-project (1262 lines)
==========================

- 📄 ``README.md`` (124 lines)
- 📄 ``setup.py`` (65 lines)
- 📄 ``requirements.txt`` (18 lines)
- 📁 **src** (1055 lines)

  - 📄 ``main.py`` (245 lines)
  - 📄 ``utils.py`` (157 lines)
  - 📁 **tests** (653 lines)

    - 📄 ``test_main.py`` (412 lines)
    - 📄 ``test_utils.py`` (241 lines)
```

The section-title underline is sized to the title's display width, so emoji icons don't trigger a "Title underline too short" warning. Directory names have rST markup characters escaped, and Git status is shown with bold `[U]`/`[M]`/`[A]`/`[D]` badges (reStructuredText has no standard strike-through, so deleted files carry the `[D]` badge rather than being struck through). Drop the file straight into a Sphinx project or include it with the [`.. include::`](https://docutils.sourceforge.io/docs/ref/rst/directives.html#include) directive.

## SVG (`.svg`)

A scalable vector image of the tree exactly as it appears in the terminal, preserving the `rich` colors, icons, and connectors. Ideal for embedding a styled directory tree in a README without a screenshot.
