# Keeping Structure Docs Up to Date

A directory tree in a README or a docs site goes stale the moment a file moves. These recipes regenerate it automatically. [Export](../user-guide/export.md) covers the options used here.

## A One-Off Export

Generate a Markdown tree and wrap it in a page of its own:

```bash
recursivist export --format md --exclude node_modules --exclude .git --prefix structure --sort-by-loc

{
  echo "# Project Structure"
  echo
  cat structure.md
} > STRUCTURE.md
```

For a README, an SVG keeps the terminal's colors and icons:

```bash
recursivist export --format svg --depth 2 --output-dir ./assets --prefix directory-structure
```

```markdown
![Project structure](assets/directory-structure.svg)
```

## Pre-commit Framework

Recursivist ships an official [pre-commit](https://pre-commit.com) hook (id `recursivist-export`) that regenerates an export before every commit. Add it to `.pre-commit-config.yaml`:

```yaml
repos:
    - repo: https://github.com/ArmaanjeetSandhu/recursivist
      rev: v2.1.0 # use the latest release tag
      hooks:
          - id: recursivist-export
            args:
                - "."
                - "--format"
                - "md"
                - "--output-dir"
                - "docs"
                - "--prefix"
                - "structure"
                - "--exclude"
                - "node_modules"
                - "--exclude"
                - ".git"
                - "--exclude"
                - "venv"
```

Then enable it:

```bash
pre-commit install
```

## Manual Git Hook

Without the framework, a `.git/hooks/pre-commit` script works too:

```bash
#!/bin/bash
recursivist export --format md --exclude node_modules --exclude .git --prefix STRUCTURE --sort-by-loc
git add STRUCTURE.md
```

Make it executable with `chmod +x .git/hooks/pre-commit`.

## GitHub Actions

A workflow that regenerates the structure page on every push to `main`:

```yaml
name: Generate Project Structure Documentation

on:
    push:
        branches: [main]
        paths-ignore:
            - "docs/structure.md"

jobs:
    update-structure:
        runs-on: ubuntu-latest
        steps:
            - uses: actions/checkout@v4
            - uses: actions/setup-python@v5
              with:
                  python-version: "3.12"
            - run: pip install recursivist
            - run: |
                  mkdir -p docs
                  recursivist export \
                    --format md \
                    --exclude node_modules --exclude .git \
                    --output-dir ./docs --prefix structure --sort-by-loc
            - run: |
                  git config user.email "action@github.com"
                  git config user.name "GitHub Action"
                  git add docs/structure.md
                  git diff --quiet && git diff --staged --quiet || git commit -m "Update structure docs"
                  git push
```

## GitLab CI

```yaml
generate-structure:
    image: python:3.12-slim
    script:
        - pip install recursivist
        - mkdir -p docs
        - recursivist export --format md --exclude node_modules --exclude .git --output-dir ./docs --prefix structure --sort-by-loc
    artifacts:
        paths:
            - docs/structure.md
```

## Documentation Sites

For MkDocs, or any Markdown-based site, generate a Markdown export into the docs directory and reference it from your navigation like any other page:

```bash
recursivist export --format md --output-dir ./docs --prefix structure
```

For Sphinx, export reStructuredText instead, then add the file to a toctree or pull it into an existing page with the [`.. include::`](https://docutils.sourceforge.io/docs/ref/rst/directives.html#include) directive:

```bash
recursivist export --format rst --output-dir ./docs --prefix structure
```

## A Multi-Level Project Map

Generate overviews at several depths, from a top-level summary to the complete tree:

```bash
mkdir -p project-map
recursivist export --format md --depth 1 --output-dir project-map --prefix L1-overview --sort-by-size
recursivist export --format md --depth 2 --output-dir project-map --prefix L2-structure --sort-by-loc
recursivist export --format md --output-dir project-map --prefix L3-complete --sort-by-loc --mtime
```

## Documenting a Repository You Haven't Cloned

`export` takes a GitHub repository URL in place of a local path, so a structure page can be generated for another repository without cloning it:

```bash
recursivist export https://github.com/owner/repo --format md --output-dir ./docs
```

In CI or against private repositories, set `GITHUB_TOKEN` (or `GH_TOKEN`) to raise rate limits and authenticate. See [GitHub Repositories](../user-guide/github-repositories.md).
