# Export Examples

Practical recipes for exporting directory structures. For a per-format reference, see [Export Formats](../reference/export-formats.md).

## Exporting to Each Format

```bash
recursivist export --format md     # structure.md
recursivist export --format json   # structure.json
recursivist export --format html   # structure.html
recursivist export --format txt    # structure.txt
recursivist export --format svg    # structure.svg
recursivist export --format rst    # structure.rst
```

Several at once:

```bash
recursivist export --format "md json html"
```

## Statistics in Exports

```bash
recursivist export --format md --sort-by-loc
recursivist export --format html --sort-by-size
recursivist export --format json --mtime                         # show mtime, keep order
recursivist export --format txt --sort-by-loc --size --mtime     # sort by LOC, show all three
```

A Markdown export with `--sort-by-loc`:

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

## Output Location and Filename

```bash
recursivist export --format md --output-dir ./docs                 # ./docs/structure.md
recursivist export --format json --prefix my-project                # my-project.json
recursivist export --format html --output-dir ./docs --prefix tree  # ./docs/tree.html
```

## Filtered and Depth-Limited Exports

```bash
# Exclude directories and extensions
recursivist export --format md --exclude "node_modules .git build" --exclude-ext ".pyc .log"

# Top-level overview only
recursivist export --format md --depth 1

# Export a subdirectory directly
recursivist export src --format html --prefix source-structure

# Full paths (handy for JSON consumed by other tools)
recursivist export --format json --full-path
```

## Processing JSON with jq

Export to JSON with metrics, then analyze with [jq](https://jqlang.org). With a detail flag, each file is an object carrying `path`, `loc`, and/or `size`:

```bash
recursivist export --format json --prefix structure --sort-by-loc --size
```

```bash
# Ten files with the most lines of code
jq -r '.structure | .. | objects | select(has("_files")) | ._files[]
       | select(type=="object" and has("loc")) | [.loc, .path] | @tsv' \
  structure.json | sort -nr | head -10

# Count files by extension
jq -r '.structure | .. | objects | select(has("_files")) | ._files[]
       | select(type=="object") | (.path | split(".") | .[-1]) | ascii_downcase' \
  structure.json | sort | uniq -c | sort -nr
```

## Including a Structure in Documentation

```bash
# Generate a Markdown tree and prepend it to a README section
recursivist export --format md --exclude "node_modules .git" --prefix structure --sort-by-loc

{
  echo "# Project Structure"
  echo
  cat structure.md
} > STRUCTURE.md
```
