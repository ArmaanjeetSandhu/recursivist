# Export Formats

Recursivist can export directory structures to several different formats to suit different needs. This page explains each format and provides examples.

## Available Formats

| Format   | Extension | Description                                 |
| -------- | --------- | ------------------------------------------- |
| Text     | `.txt`    | Simple ASCII tree representation            |
| JSON     | `.json`   | Structured data format for programmatic use |
| HTML     | `.html`   | Interactive web-based visualization         |
| Markdown | `.md`     | GitHub-compatible Markdown representation   |
| React    | `.jsx`    | Interactive React component                 |

## Basic Export Command

To export the current directory structure:

```bash
recursivist export \
--format FORMAT
```

Replace `FORMAT` with one of: `txt`, `json`, `html`, `md`, or `jsx`.

## Exporting to Multiple Formats

You can export to multiple formats in a single command:

```bash
recursivist export \
--format "txt json html md jsx"
```

## Specifying Output Directory

By default, exports are saved to the current directory. You can specify a different output directory:

```bash
recursivist export \
--format md \
--output-dir ./exports
```

## Customizing Filename Prefix

By default, all exports use the prefix `structure`. You can specify a different prefix:

```bash
recursivist export \
--format json \
--prefix my-project
```

This will create a file named `my-project.json`.

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

Export to text format with:

```bash
recursivist export \
--format txt
```

### JSON Format

The JSON format provides a structured representation that can be easily parsed by other tools or scripts:

```json
{
  "root": "my-project",
  "structure": {
    "src": {
      "main.py": null,
      "utils.py": null,
      "tests": {
        "test_main.py": null,
        "test_utils.py": null
      }
    },
    "README.md": null,
    "requirements.txt": null,
    "setup.py": null
  }
}
```

Export to JSON format with:

```bash
recursivist export \
--format json
```

### HTML Format

The HTML format provides a web-based visualization that can be viewed in any browser. It includes styling to make the directory structure easier to read.

Export to HTML format with:

```bash
recursivist export \
--format html
```

The generated HTML file can be opened in any web browser and includes proper styling for directories and files.

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

Export to Markdown format with:

```bash
recursivist export \
--format md
```

### React Component (JSX)

The JSX format creates an interactive React component with a collapsible tree view:

```bash
recursivist export \
--format jsx
```

This creates a self-contained React component file that you can import directly into your React projects. The component includes:

- Collapsible folders
- Search functionality
- Expandable/collapsible tree view
- Smooth animations
- Dark mode support

## Using the React Component

To use the exported React component in your project:

1. Copy the generated `.jsx` file to your React project's components directory
2. Make sure you have the required dependencies:
   ```
   npm install lucide-react
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

The component uses Tailwind CSS for styling. If your project doesn't use Tailwind, you'll need to add it or modify the component to use your preferred styling solution.

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
recursivist export \
--format json \
--full-path
```

This is particularly useful for JSON exports that might be processed by other tools.
