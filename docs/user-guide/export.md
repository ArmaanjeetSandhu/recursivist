# Export

The `export` command allows you to save directory structures to various file formats. This guide covers how to use the export features effectively.

## Basic Export Usage

To export the current directory structure:

```bash
recursivist export --format FORMAT
```

Replace `FORMAT` with one of: `txt`, `json`, `html`, `md`, or `jsx`.

For a specific directory:

```bash
recursivist export /path/to/directory --format FORMAT
```

## Available Export Formats

Recursivist supports multiple export formats, each suitable for different purposes:

| Format   | Extension | Description           | Use Case                                 |
| -------- | --------- | --------------------- | ---------------------------------------- |
| Text     | `.txt`    | Simple ASCII tree     | Quick reference, text-only environments  |
| JSON     | `.json`   | Structured data       | Integration with other tools, processing |
| HTML     | `.html`   | Web-based view        | Sharing, web documentation               |
| Markdown | `.md`     | GitHub-compatible     | Documentation, GitHub readmes            |
| React    | `.jsx`    | Interactive component | Web applications, dashboards             |
| SVG      | `.svg`    | Vector image          | Embedding in READMEs, sharing visuals    |

## Exporting to Multiple Formats

You can export to multiple formats in a single command:

```bash
# Space-separated formats
recursivist export --format "txt json html md"

# Multiple format flags
recursivist export --format txt --format json --format html
```

## Output Directory

By default, exports are saved to the current directory. To specify a different location:

```bash
recursivist export --format md --output-dir ./exports
```

This will create a file at `./exports/structure.md`.

## Customizing Filenames

By default, all exports use the prefix `structure`. You can specify a different prefix:

```bash
recursivist export --format json --prefix my-project
```

This will create a file named `my-project.json`.

## Including File Statistics

You can include statistics in your exports, just like with the `visualize` command:

```bash
# Include lines of code in export
recursivist export --format md --sort-by-loc

# Include file sizes
recursivist export --format html --sort-by-size

# Include modification times
recursivist export --format json --sort-by-mtime

# Combine multiple statistics
recursivist export --format md --sort-by-loc --sort-by-size
```

These statistics will be included in the export file with appropriate formatting for each format.

## Filtering Exports

All of the filtering options available for the `visualize` command also work with `export`:

```bash
recursivist export --format md \
--exclude "node_modules .git" \
--exclude-ext .pyc \
--exclude-pattern "*.test.js"
```

See the [Pattern Filtering](pattern-filtering.md) guide for more details on filtering options.

## Depth Control

For large projects, you can limit the export depth:

```bash
recursivist export --format html --depth 3
```

## Full Path Display

By default, exports show only filenames. To include full paths:

```bash
recursivist export --format json --full-path
```

This is particularly useful for JSON exports that might be processed by other tools.

## Format-Specific Features

### Text Format (.txt)

The text format provides a simple ASCII tree view:

```
📂 my-project
├── 📁 src
│   ├── 📄 main.py
│   └── 📄 utils.py
├── 📄 README.md
└── 📄 setup.py
```

This format works well in environments where Unicode is supported.

### JSON Format (.json)

The JSON format provides a structured representation:

```json
{
  "root": "my-project",
  "structure": {
    "src": {
      "_files": ["main.py", "utils.py"]
    },
    "_files": ["README.md", "setup.py"]
  }
}
```

When file statistics are included:

```json
{
  "root": "my-project",
  "structure": {
    "_loc": 4328,
    "src": {
      "_loc": 3851,
      "_files": [
        { "name": "main.py", "path": "main.py", "loc": 245 },
        { "name": "utils.py", "path": "utils.py", "loc": 157 }
      ]
    },
    "_files": [
      { "name": "README.md", "path": "README.md", "loc": 124 },
      { "name": "setup.py", "path": "setup.py", "loc": 65 }
    ]
  },
  "show_loc": true,
  "show_size": false,
  "show_mtime": false
}
```

This format is ideal for programmatic processing or integration with other tools.

### HTML Format (.html)

The HTML format creates a web page with an interactive directory structure. It includes:

- Proper styling for directories and files
- Color coding based on file types
- Statistics display when enabled
- Responsive design for viewing on different devices

When file statistics are included, they are displayed next to each file and directory with appropriate styling.

### Markdown Format (.md)

The Markdown format creates a representation that renders well on platforms like GitHub:

```markdown
# 📂 my-project

- 📁 **src**
  - 📄 `main.py`
  - 📄 `utils.py`
- 📄 `README.md`
- 📄 `setup.py`
```

With statistics:

```markdown
# 📂 my-project (4328 lines)

- 📁 **src** (3851 lines)
  - 📄 `main.py` (245 lines)
  - 📄 `utils.py` (157 lines)
- 📄 `README.md` (124 lines)
- 📄 `setup.py` (65 lines)
```

### React Component (.jsx)

The JSX format creates an interactive React component with:

- Collapsible folder structure
- Search functionality
- Breadcrumb navigation
- Path copying
- Dark mode toggle
- File statistics display when enabled
- Expand/collapse all buttons
- Mobile-responsive design

This is the most sophisticated export option, designed for integration into web applications.

### SVG Format (.svg)

The SVG format captures an exact image of the terminal visualization, preserving all colors, icons, and tree structures in a scalable vector graphic. This is perfect for embedding your directory structure directly into project READMEs or documentation without losing the beautiful terminal styling.

## Using the React Component

To use the exported React component in your project:

1. Copy the generated `.jsx` file to your React project's components directory
2. Install required dependencies:
   ```
   npm install lucide-react
   ```
3. Import and use the component:

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

The component is designed to work with Tailwind CSS. If your project doesn't use Tailwind, you'll need to adapt the component accordingly.

## Examples

### Basic Export to Markdown

```bash
recursivist export --format md
```

### Export to Multiple Formats with Custom Prefix

```bash
recursivist export \
--format "txt md json" \
--prefix project-structure \
--output-dir ./docs
```

### Export Source Directory Only

```bash
recursivist export src \
--format html \
--prefix source-structure
```

### Export with Depth Control and Exclusions

```bash
recursivist export \
--format jsx \
--depth 3 \
--exclude "node_modules .git" \
--exclude-ext ".log .tmp"
```

### Export with File Statistics

```bash
recursivist export \
--format html \
--sort-by-loc \
--sort-by-size \
--sort-by-mtime
```

For more detailed information about export formats, see the [Export Formats](../reference/export-formats.md) reference.
