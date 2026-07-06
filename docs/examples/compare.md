# Compare Examples

Practical recipes for comparing directory structures. For an overview, see the [Compare guide](../user-guide/compare.md).

## Basic Comparisons

```bash
# Side-by-side in the terminal
recursivist compare dir1 dir2

# Save as HTML (writes comparison.html)
recursivist compare dir1 dir2 --save

# Choose a location and filename
recursivist compare dir1 dir2 --save --output-dir ./reports --prefix dir-diff
```

Items unique to the first directory are highlighted in green; items unique to the second, in red.

## Comparisons with Statistics

```bash
recursivist compare dir1 dir2 --sort-by-loc
recursivist compare dir1 dir2 --sort-by-size
recursivist compare dir1 dir2 --mtime               # show mtime, keep default order
recursivist compare dir1 dir2 --sort-by-loc --size  # sort by LOC, show LOC and size
```

## Filtered Comparisons

```bash
# Exclude directories and extensions
recursivist compare dir1 dir2 --exclude "node_modules .git" --exclude-ext ".pyc .log"

# Focus on a file type by name
recursivist compare dir1 dir2 --include-pattern "*.js"

# Respect a gitignore-style file
recursivist compare dir1 dir2 --ignore-file .gitignore

# Limit depth
recursivist compare dir1 dir2 --depth 2
```

## Real-World Uses

### Compare Two Versions

```bash
recursivist compare project-v1.0 project-v2.0 \
  --exclude "node_modules .git" \
  --save --prefix v1-vs-v2 --sort-by-loc
```

### Compare Two Git Branches

```bash
git clone -b main repo main-branch
git clone -b feature/new-feature repo feature-branch

recursivist compare main-branch feature-branch \
  --exclude "node_modules .git" \
  --save --prefix branch-comparison --sort-by-loc
```

### Source vs. Build

```bash
recursivist compare src dist --include-pattern "*.js" --save --sort-by-size
```

### Backup Verification

```bash
recursivist compare original-files backup-files --full-path --save --sort-by-size
```

## In Continuous Integration

A GitHub Actions step that compares a pull request against `main` and uploads the result:

```yaml
- name: Compare structures
  run: |
    recursivist compare main-branch pr-branch \
      --exclude "node_modules .git" \
      --save --prefix structure-diff --sort-by-loc

- uses: actions/upload-artifact@v4
  with:
    name: structure-comparison
    path: structure-diff.html
```
