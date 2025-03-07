# Export

The `export` command allows you to save directory structures to various file formats. This guide covers how to use the export features effectively.

## Basic Export Usage

To export the current directory structure:

```bash
recursivist export \
--format FORMAT
```

Replace `FORMAT` with one of: `txt`, `json`, `html`, `md`, or `jsx`.

For a specific directory:

```bash
recursivist export /path/to/directory \
--format FORMAT
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

## Exporting to Multiple Formats

You can export to multiple formats in a single command:

```bash
recursivist export \
--format "txt json html md"
```

Or using multiple flags:

```bash
recursivist export \
--format txt \
--format json \
--format html
```

## Output Directory

By default, exports are saved to the current directory. To specify a different location:

```bash
recursivist export \
--format md \
--output-dir ./exports
```

This will create a file at `./exports/structure.md`.

## Customizing Filenames

By default, all exports use the prefix `structure`. You can specify a different prefix:

```bash
recursivist export \
--format json \
--prefix my-project
```

This will create a file named `my-project.json`.

## Filtering Exports

All of the filtering options available for the `visualize` command also work with `export`:

```bash
recursivist export \
--format md \
--exclude "node_modules .git" \
--exclude-ext .pyc \
--exclude-pattern "*.test.js"
```

See the [Pattern Filtering](pattern-filtering.md) guide for more details on filtering options.

## Depth Control

For large projects, you can limit the export depth:

```bash
recursivist export \
--format html \
--depth 3
```

## Full Path Display

By default, exports show only filenames. To include full paths:

```bash
recursivist export \
--format json \
--full-path
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

This format is ideal for programmatic processing or integration with other tools.

### HTML Format (.html)

The HTML format creates a web page with an interactive directory structure. It includes:

- Proper styling for directories and files
- Expandable/collapsible folders
- Proper indentation and organization

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

### React Component (.jsx)

The JSX format creates an interactive React component with:

- Collapsible folders
- Search functionality
- Path breadcrumbs
- Dark mode support

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
recursivist export \
--format md
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

For more detailed information about export formats, see the [Export Formats](../reference/export-formats.md) reference.
