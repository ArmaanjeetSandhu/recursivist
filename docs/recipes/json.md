# Analyzing a Codebase with JSON

The JSON export pairs well with [jq](https://jqlang.org). Export with the detail flags you need; each file then becomes an object carrying `path`, `loc`, and/or `size`, and each directory carries aggregate totals. The [JSON format reference](../reference/export-formats.md#json-json) describes the full layout.

```bash
recursivist export \
  --format json --full-path \
  --exclude node_modules --exclude .git \
  --prefix structure --sort-by-loc --size
```

This writes `structure.json`. `--full-path` makes each `path` unique, which is what you want when listing files from several directories.

## Totals

```bash
# Total lines of code
jq '.structure._loc // 0' structure.json

# Lines of code per top-level directory
jq -r '.structure | to_entries[]
       | select(.value | type == "object" and has("_loc"))
       | [.key, (.value._loc | tostring)] | @tsv' structure.json | sort -k2 -nr
```

## Largest Files

```bash
# Ten files with the most lines of code
jq -r '.structure | .. | objects | select(has("_files")) | ._files[]
       | select(type=="object" and has("loc")) | [.loc, .path] | @tsv' \
  structure.json | sort -nr | head -10

# Ten largest files by size
jq -r '.structure | .. | objects | select(has("_files")) | ._files[]
       | select(type=="object" and has("size")) | [.size, .path] | @tsv' \
  structure.json | sort -nr | head -10
```

## By Extension

```bash
# Count files by extension
jq -r '.structure | .. | objects | select(has("_files")) | ._files[]
       | select(type=="object") | (.path | split(".") | .[-1]) | ascii_downcase' \
  structure.json | sort | uniq -c | sort -nr

# Lines of code by extension
jq -r '.structure | .. | objects | select(has("_files")) | ._files[]
       | select(type=="object" and has("loc"))
       | "\(.path | split(".") | .[-1])\t\(.loc)"' structure.json \
  | awk -F'\t' '{loc[$1]+=$2; n[$1]++}
      END {for (e in loc) printf "%-6s %8d lines in %d files\n", e, loc[e], n[e]}' \
  | sort -k2 -nr
```
