# Export Formats

Recursivist can export directory structures to several different formats to suit different needs. This page explains each format and provides examples.

## Available Formats

| Format   | Extension | Description                                 | Best For                                 |
| -------- | --------- | ------------------------------------------- | ---------------------------------------- |
| Text     | `.txt`    | Simple ASCII tree representation            | Quick reference, text-only environments  |
| JSON     | `.json`   | Structured data format for programmatic use | Data processing, integration with tools  |
| HTML     | `.html`   | Interactive web-based visualization         | Sharing, documentation, web presentation |
| Markdown | `.md`     | GitHub-compatible Markdown representation   | Project documentation, README files      |
| React    | `.jsx`    | Interactive React component                 | Web applications, interactive interfaces |

## Basic Export Command

To export the current directory structure:

```bash
recursivist export --format FORMAT
```

Replace `FORMAT` with one of: `txt`, `json`, `html`, `md`, or `jsx`.

## Exporting to Multiple Formats

You can export to multiple formats in a single command:

```bash
recursivist export --format "txt json html md jsx"
```

## Specifying Output Directory

By default, exports are saved to the current directory. You can specify a different output directory:

```bash
recursivist export --format md --output-dir ./exports
```

## Customizing Filename Prefix

By default, all exports use the prefix `structure`. You can specify a different prefix:

```bash
recursivist export --format json --prefix my-project
```

This will create a file named `my-project.json`.

## Including File Statistics

All export formats support including file statistics:

```bash
# Include lines of code
recursivist export --format html --sort-by-loc

# Include file sizes
recursivist export --format json --sort-by-size

# Include modification times
recursivist export --format md --sort-by-mtime

# Combine multiple statistics
recursivist export --format txt --sort-by-loc --sort-by-size
```

## Format Details

### Text Format (TXT)

The text format provides a simple ASCII tree representation that can be viewed in any text editor:

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

With file statistics:

```
📂 my-project (4328 lines)
├── 📁 src (3851 lines)
│   ├── 📄 main.py (245 lines)
│   ├── 📄 utils.py (157 lines)
│   └── 📁 tests (653 lines)
│       ├── 📄 test_main.py (412 lines)
│       └── 📄 test_utils.py (241 lines)
├── 📄 README.md (124 lines)
├── 📄 requirements.txt (18 lines)
└── 📄 setup.py (65 lines)
```

Export to text format with:

```bash
recursivist export --format txt
```

### JSON Format

The JSON format provides a structured representation that can be easily parsed by other tools or scripts:

```json
{
  "root": "my-project",
  "structure": {
    "_files": ["README.md", "requirements.txt", "setup.py"],
    "src": {
      "_files": ["main.py", "utils.py"],
      "tests": {
        "_files": ["test_main.py", "test_utils.py"]
      }
    }
  }
}
```

With file statistics:

```json
{
  "root": "my-project",
  "structure": {
    "_loc": 4328,
    "_files": [
      { "name": "README.md", "path": "README.md", "loc": 124 },
      { "name": "requirements.txt", "path": "requirements.txt", "loc": 18 },
      { "name": "setup.py", "path": "setup.py", "loc": 65 }
    ],
    "src": {
      "_loc": 3851,
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
  "show_mtime": false
}
```

Export to JSON format with:

```bash
recursivist export --format json
```

### HTML Format

The HTML format provides an interactive web-based visualization that includes:

- Proper styling for directories and files
- Color-coding based on file extensions
- File statistics display when enabled
- Mobile-friendly responsive design
- Clean, modern styling

Export to HTML format with:

```bash
recursivist export --format html
```

The generated HTML file can be opened in any web browser and includes appropriate styling and formatting.

### Markdown Format (MD)

The Markdown format creates a representation that renders nicely on platforms like GitHub:

```markdown
# 📂 my-project

- 📁 **src**
  - 📄 `main.py`
  - 📄 `utils.py`
  - 📁 **tests**
    - 📄 `test_main.py`
    - 📄 `test_utils.py`
- 📄 `README.md`
- 📄 `requirements.txt`
- 📄 `setup.py`
```

With file statistics:

```markdown
# 📂 my-project (4328 lines)

- 📁 **src** (3851 lines)
  - 📄 `main.py` (245 lines)
  - 📄 `utils.py` (157 lines)
  - 📁 **tests** (653 lines)
    - 📄 `test_main.py` (412 lines)
    - 📄 `test_utils.py` (241 lines)
- 📄 `README.md` (124 lines)
- 📄 `requirements.txt` (18 lines)
- 📄 `setup.py` (65 lines)
```

Export to Markdown format with:

```bash
recursivist export --format md
```

### React Component (JSX)

The JSX format creates a self-contained React component with an interactive directory tree viewer:

Features include:

- Collapsible folder structure
- Breadcrumb navigation
- File and path search functionality
- Path copying
- Dark/light mode toggle
- Tree navigation with keyboard shortcuts
- File statistics display when enabled
- Expand/collapse all buttons
- Mobile-responsive design
- Smooth animations and transitions

Export to React component format with:

```bash
recursivist export --format jsx
```

## Using the React Component

To use the exported React component in your project:

1. Copy the generated `.jsx` file to your React project's components directory
2. Install the required dependencies:
   ```
   npm install lucide-react prop-types
   ```
3. Import and use the component in your application:

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

The component is designed to be used with Tailwind CSS. If your project doesn't use Tailwind, you may need to adapt the component to use your preferred styling solution.

## Export with Filtering

All of the filtering options available for the `visualize` command also work with the `export` command:

```bash
recursivist export \
--format md \
--exclude "node_modules .git" \
--exclude-ext .pyc \
--depth 3
```

This exports a Markdown representation of the directory structure, excluding `node_modules` and `.git` directories, as well as `.pyc` files, and limiting the depth to 3 levels.

## Exporting Full Paths

By default, exports show only filenames. You can include full paths with the `--full-path` option:

```bash
recursivist export --format json --full-path
```

This is particularly useful for JSON exports that might be processed by other tools.

## Comparison of Export Formats

| Feature                     | TXT | JSON | HTML | MD  | JSX |
| --------------------------- | --- | ---- | ---- | --- | --- |
| Human-readable              | ✅  | ⚠️   | ✅   | ✅  | ⚠️  |
| Machine-readable            | ⚠️  | ✅   | ⚠️   | ⚠️  | ⚠️  |
| Interactive                 | ❌  | ❌   | ✅   | ❌  | ✅  |
| Search functionality        | ❌  | ❌   | ❌   | ❌  | ✅  |
| File statistics support     | ✅  | ✅   | ✅   | ✅  | ✅  |
| Color-coding                | ✅  | ❌   | ✅   | ⚠️  | ✅  |
| Collapsible structure       | ❌  | ❌   | ❌   | ❌  | ✅  |
| Requires external libraries | ❌  | ❌   | ❌   | ❌  | ✅  |

Legend:

- ✅ Fully supported
- ⚠️ Partially supported
- ❌ Not supported
