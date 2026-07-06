# Export

The `export` command writes a directory structure to one or more files. Nothing is printed to the terminal — each requested format produces its own file.

## Basic Usage

```bash
recursivist export                       # Markdown (the default), writes structure.md
recursivist export --format html         # a specific format
recursivist export /path/to/project --format json
```

The format flag accepts `txt`, `json`, `html`, `md`, `jsx`, `svg`, and `rst`. When omitted, it defaults to `md`.

## Available Formats

| Format           | Extension | Description                       | Best For                              |
| ---------------- | --------- | --------------------------------- | ------------------------------------- |
| Text             | `.txt`    | Plain ASCII tree                  | Quick reference, text-only contexts   |
| JSON             | `.json`   | Structured data                   | Programmatic processing, integrations |
| HTML             | `.html`   | Self-contained styled web page    | Sharing, web documentation            |
| Markdown         | `.md`     | GitHub-compatible nested list     | READMEs, project documentation        |
| React            | `.jsx`    | Interactive React component       | Web applications, dashboards          |
| SVG              | `.svg`    | Vector image of the terminal tree | Embedding visuals in docs and READMEs |
| reStructuredText | `.rst`    | Sphinx-compatible nested list     | Sphinx/docutils documentation         |

## Multiple Formats at Once

```bash
recursivist export --format "txt json html md"     # space-separated
recursivist export --format txt --format json      # repeated flags
```

## Output Location and Filename

Exports are written to the current directory by default, using the prefix `structure`. Change either:

```bash
recursivist export --format md --output-dir ./exports   # ./exports/structure.md
recursivist export --format json --prefix my-project     # my-project.json
```

The output directory is created automatically if it doesn't exist.

## File Statistics

Every format can include lines of code, file sizes, and modification times. As in the terminal, sorting and display are separate: `--sort-by-loc`/`-size`/`-mtime` sort by and show a metric, while `--loc`/`--size`/`--mtime` show a metric without reordering.

```bash
recursivist export --format md --sort-by-loc          # sort by and show LOC
recursivist export --format html --sort-by-size       # sort by and show size
recursivist export --format json --mtime              # show mtime, keep default order
recursivist export --format md --sort-by-loc --size   # sort by LOC, show LOC and size
```

Flags are resolved by command-line order — only the first sorting flag takes effect, and a second `--sort-by-*` is ignored. See the [CLI Reference](../reference/cli-reference.md#sorting-and-display-flags).

## Git Status

Annotate exported files with their Git status (`[U]`, `[M]`, `[A]`, `[D]`):

```bash
recursivist export --format md --git-status
```

`--git-status` annotates without reordering; use `--sort-by-git-status` to also sort by status. The status marker always trails after any metric annotations.

## Icon Style

Exports use the `emoji` icon style by default — independent of your saved configuration — so files render consistently anywhere. Switch to Nerd Font glyphs with:

```bash
recursivist export --format md --icon-style nerd
```

## Filtering and Depth

All filtering options, plus depth limiting and full paths, work exactly as they do for `visualize`:

```bash
recursivist export --format md \
  --exclude "node_modules .git" \
  --exclude-ext .pyc \
  --exclude-pattern "*.test.js" \
  --depth 3 \
  --full-path
```

See [Pattern Filtering](pattern-filtering.md).

## Format Details

### Text (`.txt`)

A plain ASCII tree using `├──` and `└──` connectors:

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

### JSON (`.json`)

A structured representation. Without detail flags, files collapse to bare names:

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

With a detail flag (full path, LOC, size, mtime, or Git status), each file becomes an object carrying the requested fields, and directories gain aggregate totals:

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

Size and mtime entries also include human-readable variants (`size_formatted`, `mtime_formatted`). This format is ideal for processing with tools like [jq](https://jqlang.org).

### HTML (`.html`)

A self-contained HTML document with an embedded stylesheet: a nested list with extension-colored files, bold directory names, and any enabled metric or Git-status annotations. It opens in any browser and needs no external assets — well suited to sharing or embedding in documentation.

### Markdown (`.md`)

A nested bullet list that renders cleanly on GitHub and other Markdown viewers — directories in bold, files as inline code:

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

### React Component (`.jsx`)

A standalone `DirectoryViewer` React component with an interactive tree:

- Collapsible folders with expand-all and collapse-all controls
- File and path search
- Breadcrumb navigation and path copying
- Dark/light mode toggle
- File-statistics display when the corresponding flags are set

See [Using the React Component](#using-the-react-component) below.

### SVG (`.svg`)

A scalable vector image of the tree exactly as it appears in the terminal, preserving the `rich` colors, icons, and connectors. Perfect for embedding a directory structure in a README without losing the styling.

```bash
recursivist export --format svg
```

### reStructuredText (`.rst`)

A nested bullet list that renders cleanly with docutils and Sphinx — the reStructuredText counterpart to the Markdown export. The root is a section title, directories are shown in bold, and files as inline literals:

```rst
📁 my-project
=============

- 📄 ``README.md``
- 📁 **src**

  - 📄 ``main.py``
```

```bash
recursivist export --format rst
```

Drop the file into a Sphinx project directly, or pull it into an existing page with the `.. include::` directive.

## Using the React Component

The `.jsx` export imports `react`, [`lucide-react`](https://lucide.dev/) for icons, and `prop-types`, and is styled with [Tailwind CSS](https://tailwindcss.com/) utility classes.

1. Copy the generated file into your project's components directory.
2. Install the dependencies:

   ```bash
   npm install lucide-react prop-types
   ```

3. Import and render it:

   ```jsx
   import DirectoryViewer from "./components/structure.jsx";

   function App() {
     return (
       <div className="App">
         <DirectoryViewer />
       </div>
     );
   }
   ```

If your project doesn't use Tailwind, adapt the component's class names to your styling solution.

## Examples

```bash
# Markdown overview for a README, two levels deep
recursivist export --format md --depth 2 --exclude "node_modules .git" --prefix project-overview

# Detailed JSON of the source tree with full paths and metrics
recursivist export src --format json --full-path --sort-by-loc --size --prefix source-structure

# A filtered React component focused on source files
recursivist export --format jsx \
  --include-pattern "*.py" "*.md" \
  --output-dir ./src/components \
  --prefix DirectoryViewer \
  --sort-by-loc
```

For a per-format reference, see [Export Formats](../reference/export-formats.md).
